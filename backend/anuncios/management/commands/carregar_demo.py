"""
Carrega dados de demonstração: utilizadores, pontos de interesse e anúncios
realistas em Maputo, Matola e Beira, incluindo anúncios suspeitos para
mostrar os alertas de fraude.

Uso:  python manage.py carregar_demo          (só carrega se a base estiver vazia)
      python manage.py carregar_demo --limpar (apaga e volta a carregar)
"""
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from administracao.models import (
    AlertaFraude,
    EstadoAlerta,
    HistoricoInteracao,
    Notificacao,
    TipoAccao,
)
from anuncios.models import (
    Anuncio,
    EstadoAnuncio,
    Favorito,
    ImagemImovel,
    Imovel,
    PontoInteresse,
)
from contas.fabrica import FabricaUtilizador
from contas.models import EstadoConta, Perfil, Utilizador
from ia.fachada import ServicosIA
from ia.imagens import calcular_hash

from ._fotos import ColecaoFotos

PALAVRA_PASSE = "Demo@2026"

# bairro: (cidade, latitude, longitude, renda em MZN por m² por mês)
BAIRROS = {
    "Polana Cimento": ("MAPUTO", -25.9655, 32.5952, 1000),
    "Sommerschield": ("MAPUTO", -25.9560, 32.5990, 1100),
    "Coop": ("MAPUTO", -25.9530, 32.5850, 650),
    "Malhangalene": ("MAPUTO", -25.9560, 32.5780, 560),
    "Alto Maé": ("MAPUTO", -25.9640, 32.5700, 480),
    "Baixa": ("MAPUTO", -25.9700, 32.5760, 520),
    "Costa do Sol": ("MAPUTO", -25.9050, 32.6250, 850),
    "Triunfo": ("MAPUTO", -25.9180, 32.6170, 780),
    "Polana Caniço": ("MAPUTO", -25.9300, 32.6000, 300),
    "Zimpeto": ("MAPUTO", -25.8400, 32.5600, 230),
    "Fomento": ("MATOLA", -25.9580, 32.4720, 360),
    "Matola C": ("MATOLA", -25.9600, 32.4550, 340),
    "Machava": ("MATOLA", -25.9200, 32.4900, 250),
    "Liberdade": ("MATOLA", -25.9400, 32.4650, 260),
    "Matola Rio": ("MATOLA", -26.0400, 32.4500, 190),
    "Ponta Gêa": ("BEIRA", -19.8400, 34.8350, 520),
    "Macuti": ("BEIRA", -19.8200, 34.8700, 560),
    "Palmeiras": ("BEIRA", -19.8300, 34.8500, 400),
    "Esturro": ("BEIRA", -19.8350, 34.8450, 300),
    "Manga": ("BEIRA", -19.7800, 34.8900, 210),
}

RUAS = {
    "MAPUTO": ["Av. Julius Nyerere", "Av. Kenneth Kaunda", "Av. 24 de Julho", "Av. Eduardo Mondlane",
               "Av. Mao Tsé Tung", "Av. Vladimir Lenine", "Rua da Argélia", "Av. Marginal"],
    "MATOLA": ["Av. União Africana", "Av. Samora Machel", "Rua da Liberdade", "Av. das Indústrias"],
    "BEIRA": ["Av. Eduardo Mondlane", "Av. das FPLM", "Rua Major Serpa Pinto", "Av. Poder Popular"],
}

POIS = [
    ("Escola Secundária Josina Machel", "ESCOLA", "MAPUTO", -25.9663, 32.5826),
    ("Escola Secundária da Polana", "ESCOLA", "MAPUTO", -25.9585, 32.5935),
    ("Escola Primária do Triunfo", "ESCOLA", "MAPUTO", -25.9200, 32.6120),
    ("Mercado Central", "MERCADO", "MAPUTO", -25.9714, 32.5725),
    ("Mercado do Peixe", "MERCADO", "MAPUTO", -25.9330, 32.6150),
    ("Mercado do Povo", "MERCADO", "MAPUTO", -25.9590, 32.5720),
    ("Estação Central dos CFM", "TRANSPORTE", "MAPUTO", -25.9744, 32.5650),
    ("Terminal do Museu", "TRANSPORTE", "MAPUTO", -25.9705, 32.5890),
    ("Terminal da Praça dos Combatentes", "TRANSPORTE", "MAPUTO", -25.9300, 32.5770),
    ("Hospital Central de Maputo", "SAUDE", "MAPUTO", -25.9667, 32.5867),
    ("Escola Secundária da Matola", "ESCOLA", "MATOLA", -25.9650, 32.4600),
    ("Mercado da Machava", "MERCADO", "MATOLA", -25.9220, 32.4880),
    ("Mercado do Fomento", "MERCADO", "MATOLA", -25.9560, 32.4750),
    ("Terminal da Matola Gare", "TRANSPORTE", "MATOLA", -25.9300, 32.4600),
    ("Hospital Provincial da Matola", "SAUDE", "MATOLA", -25.9600, 32.4650),
    ("Escola Secundária Samora Machel", "ESCOLA", "BEIRA", -19.8380, 34.8420),
    ("Mercado Central da Beira", "MERCADO", "BEIRA", -19.8430, 34.8380),
    ("Mercado do Goto", "MERCADO", "BEIRA", -19.8200, 34.8600),
    ("Estação dos CFM da Beira", "TRANSPORTE", "BEIRA", -19.8360, 34.8440),
    ("Hospital Central da Beira", "SAUDE", "BEIRA", -19.8320, 34.8480),
]

CARACTERISTICAS = [
    "cozinha equipada", "ar condicionado em todas as divisões", "segurança 24 horas",
    "parqueamento para dois carros", "gerador de reserva", "tanque de água", "varanda ampla",
    "roupeiros embutidos", "acabamentos recentes", "boa iluminação natural",
    "perto de escolas e supermercados", "acesso fácil a transportes", "condomínio fechado",
    "quintal com jardim", "suite com casa de banho privativa",
]


class Command(BaseCommand):
    help = "Carrega dados de demonstração (utilizadores, imóveis e anúncios)."

    def add_arguments(self, parser):
        parser.add_argument("--limpar", action="store_true", help="Apaga os dados existentes.")

    def handle(self, *args, **opcoes):
        if opcoes["limpar"]:
            self._limpar()
        elif Anuncio.objects.exists():
            self.stdout.write("Já existem dados; nada a fazer (use --limpar para recarregar).")
            return
        self.r = random.Random(2026)
        self.fotos = ColecaoFotos()
        if not self.fotos.total:
            self.stdout.write(self.style.WARNING(
                "Sem fotografias reais em anuncios/fotos_reais/: serão usadas imagens neutras. "
                "Execute descarregar_fotos.py num computador com internet."))
        with transaction.atomic():
            self._utilizadores()
            self._pois()
            self._publicados()
            self._analisar_publicados()
            self._pendentes_e_suspeitos()
            self._historico()
        self.stdout.write(self.style.SUCCESS(
            f"Dados carregados: {Utilizador.objects.count()} utilizadores, "
            f"{Anuncio.objects.count()} anúncios, {AlertaFraude.objects.count()} alertas."))

    # ------------------------------------------------------------------
    def _limpar(self):
        Anuncio.objects.all().delete()
        Imovel.objects.all().delete()
        PontoInteresse.objects.all().delete()
        HistoricoInteracao.objects.all().delete()
        Notificacao.objects.all().delete()
        Utilizador.objects.all().delete()

    def _utilizadores(self):
        f = FabricaUtilizador.criar
        self.admin = f(Perfil.ADMINISTRADOR, "admin@imoveis.co.mz", PALAVRA_PASSE,
                       "Marta Sitoe", contacto="841234567")
        self.agencia = f(Perfil.PROPRIETARIO, "agencia@imoveis.co.mz", PALAVRA_PASSE,
                         "Rui Tembe", contacto="823456789", nome_agencia="Imobiliária Polana")
        self.agencia_beira = f(Perfil.PROPRIETARIO, "beira@imoveis.co.mz", PALAVRA_PASSE,
                               "Helena Muchanga", contacto="864567890", nome_agencia="Beira Casas")
        self.proprietario = f(Perfil.PROPRIETARIO, "proprietario@imoveis.co.mz", PALAVRA_PASSE,
                              "Carlos Mondlane", contacto="845678901")
        self.suspeito = f(Perfil.PROPRIETARIO, "oportunidades@imoveis.co.mz", PALAVRA_PASSE,
                          "Jorge Fumo", contacto="876789012")
        self.inquilino = f(Perfil.INQUILINO, "inquilino@imoveis.co.mz", PALAVRA_PASSE,
                           "Ana Macuácua", contacto="847890123")
        f(Perfil.INQUILINO, "paulo@imoveis.co.mz", PALAVRA_PASSE, "Paulo Nhantumbo",
          contacto="828901234")
        bloqueado = f(Perfil.INQUILINO, "lucia@imoveis.co.mz", PALAVRA_PASSE, "Lúcia Cossa",
                      contacto="849012345")
        bloqueado.mudar_estado(EstadoConta.BLOQUEADO)
        # Datas de registo espalhadas pelos últimos meses (para os indicadores)
        for u in Utilizador.objects.all():
            Utilizador.objects.filter(id=u.id).update(
                date_joined=timezone.now() - timedelta(days=self.r.randint(5, 170)))

    def _pois(self):
        for nome, cat, cidade, lat, lon in POIS:
            PontoInteresse.objects.create(nome=nome, categoria=cat, cidade=cidade,
                                          latitude=lat, longitude=lon)

    # ------------------------------------------------------------------
    def _criar(self, anunciante, bairro, tipo, finalidade, divisoes, area, preco,
               titulo=None, descricao=None, estado=EstadoAnuncio.PUBLICADO, dias=None,
               imagens_bytes=None):
        cidade, lat, lon, _ = BAIRROS[bairro]
        imovel = Imovel.objects.create(
            tipo=tipo, area=area, num_divisoes=divisoes, cidade=cidade, bairro=bairro,
            endereco=f"{self.r.choice(RUAS[cidade])}, n.º {self.r.randint(10, 1500)}",
            latitude=round(lat + self.r.uniform(-0.006, 0.006), 6),
            longitude=round(lon + self.r.uniform(-0.006, 0.006), 6))
        anuncio = Anuncio.objects.create(
            imovel=imovel, anunciante=anunciante, finalidade=finalidade, preco=preco,
            titulo=titulo or self._titulo(tipo, divisoes, bairro, area, finalidade),
            descricao=descricao or self._descricao(tipo, divisoes, bairro, area),
            estado=estado)
        if imagens_bytes is None:
            # Uma fotografia real do tipo de imóvel (ver _fotos.py)
            imagens_bytes = [self.fotos.fotografia(tipo, anuncio.id * 7)]
        for ordem, conteudo in enumerate(imagens_bytes):
            ficheiro = ContentFile(conteudo, name=f"anuncio_{anuncio.id}_{ordem}.jpg")
            ImagemImovel.objects.create(anuncio=anuncio, ficheiro=ficheiro, ordem=ordem,
                                        checksum_hash=calcular_hash(ficheiro))
        dias = self.r.randint(1, 175) if dias is None else dias
        quando = timezone.now() - timedelta(days=dias, hours=self.r.randint(0, 20))
        Anuncio.objects.filter(id=anuncio.id).update(
            data_criacao=quando,
            data_publicacao=quando + timedelta(hours=self.r.uniform(2, 11)) if estado == EstadoAnuncio.PUBLICADO else None,
            visualizacoes=self.r.randint(5, 240) if estado == EstadoAnuncio.PUBLICADO else 0)
        anuncio.refresh_from_db()
        return anuncio

    def _titulo(self, tipo, divisoes, bairro, area, finalidade):
        acao = "para arrendar" if finalidade == "ARRENDAMENTO" else "à venda"
        if tipo == "APARTAMENTO":
            extra = self.r.choice(["com vista para a baía", "renovado", "mobilado",
                                   "com varanda", "perto da avenida", "luminoso"])
            return f"Apartamento T{divisoes} {extra} em {bairro}"
        if tipo == "MORADIA":
            extra = self.r.choice(["com quintal", "com piscina", "em condomínio",
                                   "com anexo", "independente"])
            return f"Moradia T{divisoes} {extra} em {bairro}"
        if tipo == "ESCRITORIO":
            return f"Escritório de {int(area)} m² {acao} em {bairro}"
        return f"Terreno de {int(area)} m² {acao} em {bairro}"

    def _descricao(self, tipo, divisoes, bairro, area):
        itens = self.r.sample(CARACTERISTICAS, 4)
        if tipo == "TERRENO":
            return (f"Terreno plano com {int(area)} m² em {bairro}, com DUAT em dia, vedado e "
                    f"com acesso a água e energia. Ideal para construção de moradia.")
        divisao = f"{divisoes} quartos" if tipo != "ESCRITORIO" else f"{divisoes} salas"
        return (f"Imóvel com {divisao} e {int(area)} m², situado numa zona tranquila de {bairro}. "
                f"Inclui {', '.join(itens[:3])} e {itens[3]}. Visitas por marcação com o anunciante.")

    def _publicados(self):
        self.publicados = []
        donos = [self.agencia, self.agencia, self.proprietario, self.agencia_beira]
        bairros = list(BAIRROS)
        for n in range(78):
            bairro = bairros[n % len(bairros)]
            cidade, _, _, renda_m2 = BAIRROS[bairro]
            dono = self.agencia_beira if cidade == "BEIRA" else self.r.choice(donos[:3])
            finalidade = "ARRENDAMENTO" if n % 3 else "VENDA"
            tipo = self.r.choices(["APARTAMENTO", "MORADIA", "ESCRITORIO", "TERRENO"],
                                  weights=[5, 3, 1, 1])[0]
            if tipo == "TERRENO":
                finalidade = "VENDA"
            divisoes = {"APARTAMENTO": self.r.randint(1, 4), "MORADIA": self.r.randint(2, 5),
                        "ESCRITORIO": self.r.randint(2, 8), "TERRENO": 0}[tipo]
            area = {"APARTAMENTO": 45 + divisoes * 28, "MORADIA": 90 + divisoes * 45,
                    "ESCRITORIO": 60 + divisoes * 25, "TERRENO": self.r.choice([450, 600, 800, 1000])}[tipo]
            area = round(area * self.r.uniform(0.85, 1.2))
            # Preço = área x preço por m² da zona, com variação natural
            fator_tipo = {"APARTAMENTO": 1.0, "MORADIA": 0.95, "ESCRITORIO": 1.15, "TERRENO": 0.12}[tipo]
            preco_m2 = renda_m2 * fator_tipo * self.r.uniform(0.85, 1.15)
            preco = area * preco_m2 * (115 if finalidade == "VENDA" else 1)
            passo = 1000 if finalidade == "ARRENDAMENTO" else 50_000
            preco = max(passo, round(preco / passo) * passo)
            self.publicados.append(self._criar(dono, bairro, tipo, finalidade, divisoes, area, preco))

    def _analisar_publicados(self):
        """Corre a análise de IA nos anúncios publicados e repõe o estado
        Publicado (simula que já foram aprovados no passado)."""
        servicos = ServicosIA()
        for anuncio in self.publicados:
            publicado_em = anuncio.data_publicacao   # data simulada no passado
            servicos.analisar_anuncio(anuncio)
            anuncio.mudar_estado(EstadoAnuncio.PUBLICADO)
            # mudar_estado grava a hora actual; repomos a data simulada
            Anuncio.objects.filter(id=anuncio.id).update(data_publicacao=publicado_em)
        # Alguns alertas antigos já foram decididos pelo administrador
        for i, alerta in enumerate(AlertaFraude.objects.all()):
            if i % 2 == 0:
                alerta.classificar(EstadoAlerta.FALSO_POSITIVO, self.admin,
                                   "Preço confirmado com o anunciante.")

    def _pendentes_e_suspeitos(self):
        servicos = ServicosIA()
        foto_repetida = self.publicados[4].imagens.first().ficheiro.read()
        casos = [
            # Normais, à espera de moderação
            dict(anunciante=self.agencia, bairro="Coop", tipo="APARTAMENTO",
                 finalidade="ARRENDAMENTO", divisoes=2, area=95, preco=62_000, dias=1),
            dict(anunciante=self.proprietario, bairro="Fomento", tipo="MORADIA",
                 finalidade="VENDA", divisoes=3, area=210, preco=8_500_000, dias=0),
            dict(anunciante=self.agencia_beira, bairro="Macuti", tipo="APARTAMENTO",
                 finalidade="ARRENDAMENTO", divisoes=3, area=120, preco=66_000, dias=0),
            # Suspeito 1: preço muito abaixo e texto típico de burla
            dict(anunciante=self.suspeito, bairro="Polana Cimento", tipo="APARTAMENTO",
                 finalidade="ARRENDAMENTO", divisoes=3, area=140, preco=18_000, dias=0,
                 titulo="Apartamento T3 mobilado na Polana, oportunidade única",
                 descricao=("Apartamento T3 totalmente mobilado na Polana. Estou fora do país, "
                            "por isso não é possível visitar antes. Para reservar faça o "
                            "pagamento antecipado de 3 meses por M-Pesa e envio as chaves por "
                            "transportadora. Oferta relâmpago, só hoje!")),
            # Suspeito 2: fotografia já usada noutro anúncio
            dict(anunciante=self.suspeito, bairro="Matola C", tipo="MORADIA",
                 finalidade="ARRENDAMENTO", divisoes=3, area=180, preco=58_000, dias=1,
                 titulo="Moradia T3 com quintal na Matola C",
                 imagens_bytes=[foto_repetida]),
            # Suspeito 3: preço de venda muito acima do mercado
            dict(anunciante=self.suspeito, bairro="Alto Maé", tipo="APARTAMENTO",
                 finalidade="VENDA", divisoes=2, area=90, preco=48_000_000, dias=2,
                 titulo="Apartamento T2 de luxo no Alto Maé"),
        ]
        for caso in casos:
            anuncio = self._criar(estado=EstadoAnuncio.SUBMETIDO, **caso)
            servicos.analisar_anuncio(anuncio)

        # Um anúncio rejeitado, para o proprietário ver o motivo
        rejeitado = self._criar(self.proprietario, "Malhangalene", "APARTAMENTO", "ARRENDAMENTO",
                                1, 55, 30_000, estado=EstadoAnuncio.SUBMETIDO, dias=6)
        servicos.analisar_anuncio(rejeitado)
        rejeitado.motivo_rejeicao = "As fotografias não mostram o interior do imóvel."
        rejeitado.mudar_estado(EstadoAnuncio.REJEITADO)
        Notificacao.objects.create(utilizador=self.proprietario, ligacao=f"/meus-anuncios/{rejeitado.id}",
                                   mensagem=f"O seu anúncio «{rejeitado.titulo}» foi rejeitado. "
                                            f"Motivo: {rejeitado.motivo_rejeicao}")

    def _historico(self):
        """Histórico da inquilina de demonstração: prefere apartamentos para
        arrendar na zona da Polana e Sommerschield (alimenta as recomendações)."""
        preferidos = [a for a in self.publicados if a.imovel.bairro in
                      ("Polana Cimento", "Sommerschield", "Coop") and a.finalidade == "ARRENDAMENTO"]
        for a in preferidos[:5]:
            HistoricoInteracao.registar(self.inquilino, TipoAccao.VISUALIZACAO,
                                        f"Viu o anúncio #{a.id}", anuncio=a.id)
        for a in preferidos[:2]:
            Favorito.objects.create(utilizador=self.inquilino, anuncio=a)
            HistoricoInteracao.registar(self.inquilino, TipoAccao.FAVORITO,
                                        f"Guardou o anúncio #{a.id}", anuncio=a.id)
        HistoricoInteracao.registar(self.inquilino, TipoAccao.PESQUISA, "Pesquisa de imóveis",
                                    filtros={"cidade": "MAPUTO", "tipo": "APARTAMENTO",
                                             "finalidade": "ARRENDAMENTO"})
        # Pesquisas de vários dias, para o gráfico dos indicadores
        for _ in range(60):
            h = HistoricoInteracao.registar(self.r.choice([self.inquilino, None]), TipoAccao.PESQUISA,
                                            "Pesquisa de imóveis",
                                            filtros={"cidade": self.r.choice(["MAPUTO", "MATOLA", "BEIRA"])})
            HistoricoInteracao.objects.filter(id=h.id).update(
                data_hora=timezone.now() - timedelta(days=self.r.randint(0, 170),
                                                     hours=self.r.randint(0, 23)))
