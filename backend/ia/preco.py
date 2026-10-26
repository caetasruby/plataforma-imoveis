"""
Módulo Preço Justo (CT01, UC05).

PADRÃO DE DESENHO: STRATEGY (Estratégia)

Problema: há mais de uma forma de estimar o preço justo. A regressão linear
é melhor quando há muitos anúncios publicados, mas falha quando há poucos
dados (por exemplo, numa cidade nova). Escrever "if/else" dentro de uma só
função tornaria o código difícil de ler e de testar.

Solução: cada forma de cálculo é uma classe com o mesmo método estimar().
A classe EstimadorPreco escolhe a estratégia adequada e usa-a sem saber
como ela funciona por dentro. Acrescentar outra estratégia no futuro não
obriga a mudar o resto do código.
"""
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from statistics import median

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Abaixo deste número de exemplos a regressão não é fiável
MINIMO_EXEMPLOS_REGRESSAO = 15


@dataclass
class DadosImovel:
    """Dados de entrada da estimativa (vêm do formulário ou da base de dados)."""
    finalidade: str
    tipo: str
    cidade: str
    bairro: str
    area: float
    num_divisoes: int


@dataclass
class Estimativa:
    valor: float
    minimo: float
    maximo: float
    metodo: str


def dados_de_anuncio(anuncio):
    i = anuncio.imovel
    return DadosImovel(anuncio.finalidade, i.tipo, i.cidade, i.bairro.strip().lower(),
                       float(i.area), int(i.num_divisoes))


def arredondar(valor):
    """Arredonda para valores "humanos" (milhares ou dezenas de milhares)."""
    passo = 1000 if valor < 1_000_000 else 10_000
    return round(valor / passo) * passo


class EstrategiaPreco(ABC):
    """Interface comum a todas as estratégias de cálculo."""

    @abstractmethod
    def estimar(self, dados: DadosImovel) -> Estimativa:
        ...


class EstrategiaRegressaoLinear(EstrategiaPreco):
    """Regressão linear (Ridge) sobre o logaritmo do preço.
    Variáveis: tipo, cidade, bairro (categóricas) e log(área), divisões (numéricas).
    O intervalo de confiança de 95% usa o desvio-padrão dos resíduos."""

    def __init__(self, exemplos):
        # exemplos: lista de (DadosImovel, preco)
        linhas = [self._linha(d) for d, _ in exemplos]
        precos = np.log([p for _, p in exemplos])

        self.modelo = Pipeline([
            ("preparar", ColumnTransformer([
                ("categorias", OneHotEncoder(handle_unknown="ignore"), [0, 1, 2]),
                ("numeros", StandardScaler(), [3, 4]),
            ])),
            ("regressao", Ridge(alpha=1.0)),
        ])
        self.modelo.fit(np.array(linhas, dtype=object), precos)
        residuos = precos - self.modelo.predict(np.array(linhas, dtype=object))
        self.desvio = float(np.std(residuos)) or 0.1

    @staticmethod
    def _linha(d):
        return [d.tipo, d.cidade, d.bairro, math.log(d.area), d.num_divisoes]

    def estimar(self, dados):
        log_preco = float(self.modelo.predict(np.array([self._linha(dados)], dtype=object))[0])
        margem = 1.96 * self.desvio
        return Estimativa(
            valor=arredondar(math.exp(log_preco)),
            minimo=arredondar(math.exp(log_preco - margem)),
            maximo=arredondar(math.exp(log_preco + margem)),
            metodo="Regressão linear",
        )


class EstrategiaMediaZona(EstrategiaPreco):
    """Alternativa simples quando há poucos dados: mediana do preço por m²
    do bairro (ou, se não houver, da cidade) multiplicada pela área."""

    PRECO_M2_REFERENCIA = {"ARRENDAMENTO": 500.0, "VENDA": 60_000.0}   # MZN por m²

    def __init__(self, exemplos):
        self.exemplos = exemplos

    def estimar(self, dados):
        mesmos = [(d, p) for d, p in self.exemplos if d.finalidade == dados.finalidade]
        grupos = [
            [p / d.area for d, p in mesmos if d.bairro == dados.bairro and d.tipo == dados.tipo],
            [p / d.area for d, p in mesmos if d.cidade == dados.cidade and d.tipo == dados.tipo],
            [p / d.area for d, p in mesmos if d.cidade == dados.cidade],
        ]
        precos_m2 = next((g for g in grupos if len(g) >= 3), None)
        preco_m2 = median(precos_m2) if precos_m2 else self.PRECO_M2_REFERENCIA[dados.finalidade]
        valor = preco_m2 * dados.area
        return Estimativa(arredondar(valor), arredondar(valor * 0.75), arredondar(valor * 1.25),
                          "Mediana da zona")


class EstimadorPreco:
    """Contexto do padrão Strategy: escolhe e usa a estratégia adequada."""

    def __init__(self, exemplos):
        self.exemplos = exemplos
        self._cache = {}

    def _estrategia_para(self, finalidade):
        if finalidade not in self._cache:
            da_finalidade = [(d, p) for d, p in self.exemplos if d.finalidade == finalidade]
            if len(da_finalidade) >= MINIMO_EXEMPLOS_REGRESSAO:
                self._cache[finalidade] = EstrategiaRegressaoLinear(da_finalidade)
            else:
                self._cache[finalidade] = EstrategiaMediaZona(self.exemplos)
        return self._cache[finalidade]

    def estimar(self, dados: DadosImovel) -> Estimativa:
        return self._estrategia_para(dados.finalidade).estimar(dados)
