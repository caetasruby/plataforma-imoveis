"""
Motor de Recomendação (CT03, UC08).

Método: filtragem baseada em conteúdo. A partir do histórico do utilizador
(anúncios vistos, favoritos e pesquisas, CT05) constrói-se um perfil de
preferências: cidades, bairros, tipos e finalidades mais frequentes e o
preço médio. Cada anúncio publicado recebe uma pontuação de semelhança com
esse perfil e devolvem-se os de maior pontuação.
"""
from collections import Counter
from dataclasses import dataclass, field

PESOS = {"bairro": 3, "cidade": 2, "tipo": 2, "finalidade": 2, "preco": 2, "divisoes": 1}


@dataclass
class PerfilPreferencias:
    cidades: Counter = field(default_factory=Counter)
    bairros: Counter = field(default_factory=Counter)
    tipos: Counter = field(default_factory=Counter)
    finalidades: Counter = field(default_factory=Counter)
    precos: dict = field(default_factory=dict)      # finalidade -> lista de preços
    divisoes: list = field(default_factory=list)

    @property
    def vazio(self):
        return not (self.cidades or self.tipos or self.finalidades)

    def juntar_anuncio(self, anuncio, peso=1):
        i = anuncio.imovel
        self.cidades[i.cidade] += peso
        self.bairros[i.bairro.lower()] += peso
        self.tipos[i.tipo] += peso
        self.finalidades[anuncio.finalidade] += peso
        self.precos.setdefault(anuncio.finalidade, []).append(float(anuncio.preco))
        self.divisoes.append(i.num_divisoes)

    def juntar_pesquisa(self, filtros):
        for chave, contador in (("cidade", self.cidades), ("tipo", self.tipos),
                                ("finalidade", self.finalidades)):
            if filtros.get(chave):
                contador[filtros[chave]] += 1


def _proporcao(contador, valor):
    total = sum(contador.values())
    return contador[valor] / total if total else 0


def pontuar(anuncio, perfil):
    """Devolve (pontuação, motivo) para um anúncio face ao perfil."""
    i = anuncio.imovel
    partes = {
        "bairro": _proporcao(perfil.bairros, i.bairro.lower()),
        "cidade": _proporcao(perfil.cidades, i.cidade),
        "tipo": _proporcao(perfil.tipos, i.tipo),
        "finalidade": _proporcao(perfil.finalidades, anuncio.finalidade),
    }
    precos = perfil.precos.get(anuncio.finalidade)
    if precos:
        medio = sum(precos) / len(precos)
        partes["preco"] = max(0.0, 1 - abs(float(anuncio.preco) - medio) / medio)
    if perfil.divisoes:
        media = sum(perfil.divisoes) / len(perfil.divisoes)
        partes["divisoes"] = max(0.0, 1 - abs(i.num_divisoes - media) / 3)

    pontuacao = sum(PESOS[k] * v for k, v in partes.items())

    # Motivo legível para o utilizador
    if partes["bairro"] >= 0.3:
        motivo = f"Porque procurou imóveis em {i.bairro}"
    elif partes["cidade"] >= 0.5 and partes["tipo"] >= 0.5:
        motivo = f"{i.get_tipo_display()} em {i.get_cidade_display()}, como os que viu"
    elif partes.get("preco", 0) >= 0.8:
        motivo = "Dentro da faixa de preço que costuma ver"
    else:
        motivo = "Semelhante às suas pesquisas"
    return pontuacao, motivo


class MotorRecomendacao:
    def sugerir_imoveis(self, perfil, candidatos, quantidade):
        """Método surgirImoveis() do diagrama de classes."""
        if perfil.vazio:
            # Sem histórico: mostra os mais vistos (arranque a frio)
            mais_vistos = sorted(candidatos, key=lambda a: -a.visualizacoes)[:quantidade]
            return [(a, "Em destaque na plataforma") for a in mais_vistos]
        pontuados = [(a, *pontuar(a, perfil)) for a in candidatos]
        pontuados.sort(key=lambda t: -t[1])
        return [(a, motivo) for a, _, motivo in pontuados[:quantidade]]
