"""
Módulo Detecção de Fraude (CT02, UC06, UC12).

PADRÃO DE DESENHO: STRATEGY (Estratégia), aplicado à pontuação de risco.

Cada regra de detecção é uma estratégia independente com o método avaliar().
O DetectorFraude percorre a lista de estratégias e junta os sinais. Para
acrescentar uma regra nova basta criar uma classe e juntá-la à lista.

Regras implementadas:
  1. Preço atípico em relação ao preço justo.
  2. Texto suspeito (NLP simples: procura de expressões típicas de burla).
  3. Imagem duplicada noutro anúncio (hash SHA-256).
  4. Anomalia estatística (Isolation Forest, scikit-learn).
"""
import math
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

MINIMO_EXEMPLOS_ANOMALIA = 20


@dataclass
class Sinal:
    tipo: str            # um dos valores de TipoAlerta
    pontuacao: float     # entre 0 e 1
    justificacao: str


@dataclass
class ContextoAnalise:
    """Tudo o que as regras precisam para avaliar um anúncio."""
    preco: float
    preco_justo: float | None
    finalidade: str
    titulo: str
    descricao: str
    area: float
    num_divisoes: int
    latitude: float
    longitude: float
    imagens_duplicadas: int        # quantas fotografias já existem noutros anúncios


def sem_acentos(texto):
    normal = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in normal if unicodedata.category(c) != "Mn")


class EstrategiaRisco(ABC):
    @abstractmethod
    def avaliar(self, contexto: ContextoAnalise) -> list[Sinal]:
        ...


class RegraPrecoAtipico(EstrategiaRisco):
    def __init__(self, desvio_percentual):
        self.desvio = desvio_percentual

    def avaliar(self, c):
        if not c.preco_justo:
            return []
        diferenca = (c.preco - c.preco_justo) / c.preco_justo * 100
        if abs(diferenca) < self.desvio:
            return []
        # No limite vale 0,6; cada 10 pontos acima soma 0,1; máximo 0,95
        pontuacao = min(0.95, 0.6 + (abs(diferenca) - self.desvio) / 100)
        sentido = "abaixo" if diferenca < 0 else "acima"
        texto = (f"O preço pedido está {abs(diferenca):.0f}% {sentido} do preço justo estimado "
                 f"({c.preco_justo:,.0f} MT).".replace(",", " "))
        if diferenca < 0:
            texto += " Preços muito baixos são usados como isco em burlas."
        return [Sinal("PRECO_ATIPICO", round(pontuacao, 2), texto)]


class RegraTextoSuspeito(EstrategiaRisco):
    def __init__(self, expressoes):
        # Compara sem acentos, mas guarda a expressão original para a justificação
        self.expressoes = {sem_acentos(e): e for e in expressoes}

    def avaliar(self, c):
        texto = sem_acentos(f"{c.titulo} {c.descricao}")
        encontradas = [original for normal, original in self.expressoes.items() if normal in texto]
        if not encontradas:
            return []
        pontuacao = min(0.95, 0.5 + 0.2 * len(encontradas))
        lista = ", ".join(f"«{e}»" for e in encontradas)
        return [Sinal("TEXTO_SUSPEITO", round(pontuacao, 2),
                      f"A descrição contém expressões associadas a burlas: {lista}.")]


class RegraImagemDuplicada(EstrategiaRisco):
    def avaliar(self, c):
        if c.imagens_duplicadas == 0:
            return []
        return [Sinal("IMAGEM_DUPLICADA", 0.85,
                      f"{c.imagens_duplicadas} fotografia(s) já foram usadas noutro anúncio.")]


class RegraIsolationForest(EstrategiaRisco):
    """Treina um Isolation Forest com os anúncios publicados da mesma
    finalidade e verifica se o novo anúncio é um ponto isolado."""

    def __init__(self, exemplos, contaminacao):
        # exemplos: lista de ContextoAnalise de anúncios publicados
        self.modelos = {}
        for finalidade in {e.finalidade for e in exemplos}:
            dados = [self._vector(e) for e in exemplos if e.finalidade == finalidade]
            if len(dados) >= MINIMO_EXEMPLOS_ANOMALIA:
                modelo = IsolationForest(contamination=contaminacao, random_state=42)
                modelo.fit(np.array(dados))
                self.modelos[finalidade] = modelo

    @staticmethod
    def _vector(c):
        return [math.log(c.preco / c.area), math.log(c.area), c.num_divisoes,
                c.latitude, c.longitude]

    def avaliar(self, c):
        modelo = self.modelos.get(c.finalidade)
        if modelo is None:
            return []
        vector = np.array([self._vector(c)])
        if modelo.predict(vector)[0] != -1:
            return []
        # decision_function: quanto mais negativo, mais anómalo
        grau = -float(modelo.decision_function(vector)[0])
        pontuacao = min(0.9, 0.6 + grau * 2)
        return [Sinal("ANOMALIA", round(pontuacao, 2),
                      "A combinação de preço, área, divisões e localização é rara entre os "
                      "anúncios publicados (detecção de anomalias).")]


class DetectorFraude:
    """Corre todas as estratégias e devolve os sinais encontrados."""

    def __init__(self, estrategias):
        self.estrategias = estrategias

    def analisar(self, contexto):
        sinais = []
        for estrategia in self.estrategias:
            sinais.extend(estrategia.avaliar(contexto))
        return sinais
