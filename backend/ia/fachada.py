"""
PADRÃO DE DESENHO: FACADE (Fachada)

Problema: analisar um anúncio envolve vários módulos de IA (preço justo,
verificação de imagens, detecção de fraude) e várias tabelas (Anuncio,
ImagemImovel, AlertaFraude, ParametroSistema). Se cada vista da API tivesse
de coordenar tudo isto, o código ficaria repetido e frágil.

Solução: a classe ServicosIA oferece uma interface simples com poucos
métodos (analisar_anuncio, estimar_preco, recomendar, responder_pergunta).
As vistas só conhecem a fachada; os pormenores ficam escondidos atrás dela.
"""
from django.db import transaction

from administracao.configuracao import Configuracao
from administracao.models import AlertaFraude, EstadoAlerta, gravidade_da_pontuacao
from anuncios.models import Anuncio, EstadoAnuncio

from . import assistente, imagens
from .preco import DadosImovel, EstimadorPreco, dados_de_anuncio
from .recomendacao import MotorRecomendacao, PerfilPreferencias
from .risco import (
    ContextoAnalise,
    DetectorFraude,
    RegraImagemDuplicada,
    RegraIsolationForest,
    RegraPrecoAtipico,
    RegraTextoSuspeito,
)


def _publicados():
    return (Anuncio.objects.filter(estado=EstadoAnuncio.PUBLICADO)
            .select_related("imovel"))


def _contexto(anuncio, preco_justo, duplicadas=0):
    i = anuncio.imovel
    return ContextoAnalise(
        preco=float(anuncio.preco), preco_justo=preco_justo, finalidade=anuncio.finalidade,
        titulo=anuncio.titulo, descricao=anuncio.descricao, area=float(i.area),
        num_divisoes=i.num_divisoes, latitude=float(i.latitude), longitude=float(i.longitude),
        imagens_duplicadas=duplicadas)


class ServicosIA:

    # --- Preço justo (CT01) ---------------------------------------------------

    def _estimador(self, excluir_id=None):
        exemplos = [(dados_de_anuncio(a), float(a.preco))
                    for a in _publicados().exclude(id=excluir_id)]
        return EstimadorPreco(exemplos)

    def estimar_preco(self, finalidade, tipo, cidade, bairro, area, num_divisoes):
        """Pré-visualização no formulário de publicação (antes de submeter)."""
        dados = DadosImovel(finalidade, tipo, cidade, bairro.strip().lower(),
                            float(area), int(num_divisoes))
        return self._estimador().estimar(dados)

    # --- Análise completa de um anúncio (UC01, UC02) --------------------------

    @transaction.atomic
    def analisar_anuncio(self, anuncio):
        """Submetido/Publicado/Rejeitado > Em análise de IA > Pendente de moderação.
        Devolve a lista de alertas criados."""
        config = Configuracao.instancia()
        anuncio.mudar_estado(EstadoAnuncio.EM_ANALISE)

        # 1. Preço justo
        estimativa = self._estimador(excluir_id=anuncio.id).estimar(dados_de_anuncio(anuncio))
        anuncio.preco_justo = estimativa.valor
        anuncio.preco_justo_min = estimativa.minimo
        anuncio.preco_justo_max = estimativa.maximo

        # 2. Verificação de imagens
        duplicadas = imagens.contar_duplicadas(anuncio)

        # 3. Detecção de fraude (todas as estratégias)
        exemplos = [_contexto(a, None) for a in _publicados().exclude(id=anuncio.id)]
        detector = DetectorFraude([
            RegraPrecoAtipico(config.obter("desvio_preco_atipico")),
            RegraTextoSuspeito(config.lista_palavras_suspeitas()),
            RegraImagemDuplicada(),
            RegraIsolationForest(exemplos, config.obter("contaminacao_isolation_forest")),
        ])
        sinais = detector.analisar(_contexto(anuncio, estimativa.valor, duplicadas))

        # Alertas antigos ainda por decidir deixam de fazer sentido após a edição
        anuncio.alertas.filter(estado__in=[EstadoAlerta.PENDENTE, EstadoAlerta.ESCALADO]).delete()

        limiar = config.obter("limiar_risco_fraude")
        alertas = []
        for sinal in sinais:
            if sinal.pontuacao >= limiar:
                # Criar o alerta dispara o sinal post_save (padrão Observer)
                alertas.append(AlertaFraude.objects.create(
                    anuncio=anuncio, tipo_alerta=sinal.tipo, pontuacao_risco=sinal.pontuacao,
                    justificacao=sinal.justificacao,
                    gravidade=gravidade_da_pontuacao(sinal.pontuacao)))

        anuncio.pontuacao_risco = max((s.pontuacao for s in sinais), default=0.0)
        anuncio.mudar_estado(EstadoAnuncio.PENDENTE)   # também grava os campos acima
        return alertas

    # --- Recomendações (CT03, UC08) ------------------------------------------

    def recomendar(self, utilizador, quantidade=None):
        from administracao.models import HistoricoInteracao, TipoAccao

        quantidade = quantidade or Configuracao.instancia().obter("max_recomendacoes")
        perfil = PerfilPreferencias()
        vistos = set()

        historico = HistoricoInteracao.objects.filter(
            utilizador=utilizador,
            tipo_accao__in=[TipoAccao.VISUALIZACAO, TipoAccao.FAVORITO, TipoAccao.PESQUISA],
        )[:200]
        ids = {h.dados_contexto.get("anuncio") for h in historico} - {None}
        anuncios_hist = {a.id: a for a in Anuncio.objects.filter(id__in=ids).select_related("imovel")}

        for h in historico:
            if h.tipo_accao == TipoAccao.PESQUISA:
                perfil.juntar_pesquisa(h.dados_contexto.get("filtros", {}))
            elif h.dados_contexto.get("anuncio") in anuncios_hist:
                peso = 3 if h.tipo_accao == TipoAccao.FAVORITO else 1
                perfil.juntar_anuncio(anuncios_hist[h.dados_contexto["anuncio"]], peso)
                vistos.add(h.dados_contexto["anuncio"])

        favoritos = set(utilizador.favoritos.values_list("anuncio_id", flat=True))
        candidatos = [a for a in _publicados().prefetch_related("imagens")
                      if a.id not in favoritos and a.anunciante_id != utilizador.id]
        # Dar prioridade a anúncios ainda não vistos, se houver suficientes
        nao_vistos = [a for a in candidatos if a.id not in vistos]
        if len(nao_vistos) >= quantidade:
            candidatos = nao_vistos
        return MotorRecomendacao().sugerir_imoveis(perfil, candidatos, quantidade)

    def semelhantes(self, anuncio, quantidade=4):
        """Imóveis semelhantes a um anúncio (página de detalhe)."""
        perfil = PerfilPreferencias()
        perfil.juntar_anuncio(anuncio)
        candidatos = [a for a in _publicados().prefetch_related("imagens") if a.id != anuncio.id]
        return MotorRecomendacao().sugerir_imoveis(perfil, candidatos, quantidade)

    # --- Assistente virtual (UC09) -------------------------------------------

    def responder_pergunta(self, pergunta, topico_anterior=None):
        return assistente.responder(pergunta, topico_anterior)
