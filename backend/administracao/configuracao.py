"""
PADRÃO DE DESENHO: SINGLETON

Problema: os módulos de IA consultam os parâmetros do sistema (limiar de
risco, palavras suspeitas, etc.) muitas vezes em cada pedido. Ir à base de
dados de cada vez é lento, e ter várias cópias dos valores em memória pode
dar resultados diferentes conforme a cópia usada.

Solução: existe uma única instância da classe Configuracao em todo o
processo. Ela carrega os parâmetros uma vez e guarda-os. Quando o
administrador altera um parâmetro (UC16), a instância é recarregada.
"""
from threading import Lock

# Valores por omissão e regras de cada parâmetro (usados também para criar
# os registos na base de dados na primeira execução).
PARAMETROS_POR_OMISSAO = [
    {"chave": "limiar_risco_fraude", "nome": "Limiar de risco de fraude",
     "descricao": "Pontuação (0 a 1) a partir da qual um sinal de risco gera um AlertaFraude.",
     "valor": "0.6", "tipo": "DECIMAL", "minimo": 0.1, "maximo": 0.95},
    {"chave": "desvio_preco_atipico", "nome": "Desvio de preço atípico (%)",
     "descricao": "Diferença percentual em relação ao preço justo a partir da qual o preço é considerado atípico.",
     "valor": "45", "tipo": "INTEIRO", "minimo": 10, "maximo": 90},
    {"chave": "palavras_suspeitas", "nome": "Expressões suspeitas",
     "descricao": "Expressões, separadas por vírgulas, que indicam possível burla no texto do anúncio.",
     "valor": ("pagamento antecipado, transferência antecipada, pague antes da visita, "
               "m-pesa antes, sem visita, não é possível visitar, envie o sinal, "
               "estou fora do país, depósito imediato, só hoje, oferta relâmpago"),
     "tipo": "TEXTO", "minimo": None, "maximo": None},
    {"chave": "contaminacao_isolation_forest", "nome": "Contaminação do Isolation Forest",
     "descricao": "Proporção esperada de anúncios anómalos usada pelo modelo de detecção de anomalias.",
     "valor": "0.08", "tipo": "DECIMAL", "minimo": 0.01, "maximo": 0.4},
    {"chave": "horas_escalamento_alerta", "nome": "Horas até escalar um alerta",
     "descricao": "Um alerta pendente há mais horas do que este valor passa ao estado Escalado.",
     "valor": "24", "tipo": "INTEIRO", "minimo": 1, "maximo": 168},
    {"chave": "retencao_logs_meses", "nome": "Retenção dos logs (meses)",
     "descricao": "Tempo mínimo de conservação dos registos de auditoria (RNF08 exige 12 meses).",
     "valor": "12", "tipo": "INTEIRO", "minimo": 12, "maximo": 120},
    {"chave": "max_recomendacoes", "nome": "Número de recomendações",
     "descricao": "Quantidade máxima de imóveis sugeridos na página inicial.",
     "valor": "6", "tipo": "INTEIRO", "minimo": 1, "maximo": 20},
]


class Configuracao:
    _instancia = None
    _trinco = Lock()   # evita que dois pedidos criem duas instâncias ao mesmo tempo

    def __new__(cls):
        with cls._trinco:
            if cls._instancia is None:
                cls._instancia = super().__new__(cls)
                cls._instancia._valores = None
        return cls._instancia

    @classmethod
    def instancia(cls):
        return cls()

    def _carregar(self):
        from .models import ParametroSistema   # importação tardia: evita ciclos

        valores = {p["chave"]: _converter(p["valor"], p["tipo"]) for p in PARAMETROS_POR_OMISSAO}
        for parametro in ParametroSistema.objects.all():
            valores[parametro.chave] = parametro.valor_convertido()
        self._valores = valores

    def obter(self, chave):
        if self._valores is None:
            self._carregar()
        return self._valores[chave]

    def recarregar(self):
        """Chamado depois de o administrador alterar um parâmetro."""
        self._valores = None

    def lista_palavras_suspeitas(self):
        return [p.strip().lower() for p in self.obter("palavras_suspeitas").split(",") if p.strip()]


def _converter(valor, tipo):
    if tipo == "DECIMAL":
        return float(valor)
    if tipo == "INTEIRO":
        return int(valor)
    return valor
