"""
Modelos do Painel de Administração: AlertaFraude, ParametroSistema,
HistoricoInteracao (logs de auditoria, RNF08 e CT05) e Notificacao.
"""
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# --- AlertaFraude (UC06, UC12) ----------------------------------------------

class TipoAlerta(models.TextChoices):
    PRECO_ATIPICO = "PRECO_ATIPICO", "Preço atípico"
    TEXTO_SUSPEITO = "TEXTO_SUSPEITO", "Texto suspeito"
    IMAGEM_DUPLICADA = "IMAGEM_DUPLICADA", "Imagem duplicada"
    ANOMALIA = "ANOMALIA", "Anomalia estatística"


class Gravidade(models.TextChoices):
    BAIXA = "BAIXA", "Baixa"
    MEDIA = "MEDIA", "Média"
    ALTA = "ALTA", "Alta"


class EstadoAlerta(models.TextChoices):
    """Estados do diagrama de estados do AlertaFraude (secção 13)."""
    PENDENTE = "PENDENTE", "Pendente"
    ESCALADO = "ESCALADO", "Escalado"
    EM_REVISAO = "EM_REVISAO", "Em revisão"
    CONFIRMADO = "CONFIRMADO", "Confirmado"
    FALSO_POSITIVO = "FALSO_POSITIVO", "Falso positivo"
    RESOLVIDO = "RESOLVIDO", "Resolvido"


A = EstadoAlerta
TRANSICOES_ALERTA = {
    A.PENDENTE: {A.EM_REVISAO, A.ESCALADO},
    A.ESCALADO: {A.EM_REVISAO},
    A.EM_REVISAO: {A.CONFIRMADO, A.FALSO_POSITIVO},
    A.CONFIRMADO: {A.RESOLVIDO},
    A.FALSO_POSITIVO: {A.EM_REVISAO},   # reabrir com nova evidência
    A.RESOLVIDO: set(),
}


def gravidade_da_pontuacao(pontuacao):
    if pontuacao >= 0.8:
        return Gravidade.ALTA
    if pontuacao >= 0.6:
        return Gravidade.MEDIA
    return Gravidade.BAIXA


class AlertaFraude(models.Model):
    anuncio = models.ForeignKey("anuncios.Anuncio", on_delete=models.CASCADE,
                                related_name="alertas")
    tipo_alerta = models.CharField(max_length=20, choices=TipoAlerta.choices)
    pontuacao_risco = models.FloatField()
    justificacao = models.TextField()
    gravidade = models.CharField(max_length=10, choices=Gravidade.choices)
    estado = models.CharField(max_length=20, choices=EstadoAlerta.choices,
                              default=EstadoAlerta.PENDENTE)
    nota_decisao = models.TextField(blank=True)
    decidido_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="+")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_decisao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "alerta de fraude"
        verbose_name_plural = "alertas de fraude"
        ordering = ["-data_criacao"]

    def __str__(self):
        return f"{self.get_tipo_alerta_display()} ({self.pontuacao_risco:.2f})"

    def _transitar(self, novo):
        if novo not in TRANSICOES_ALERTA[self.estado]:
            raise ValidationError(
                f"Não é possível passar o alerta de «{self.get_estado_display()}» "
                f"para «{EstadoAlerta(novo).label}».")
        self.estado = novo

    def caminho_ate(self, destino):
        """Procura (em largura) o caminho mais curto no diagrama de estados
        entre o estado actual e o destino. Devolve None se não existir."""
        fila = [[self.estado]]
        visitados = {self.estado}
        while fila:
            caminho = fila.pop(0)
            if caminho[-1] == destino:
                return caminho[1:]
            for seguinte in TRANSICOES_ALERTA[caminho[-1]]:
                if seguinte not in visitados:
                    visitados.add(seguinte)
                    fila.append(caminho + [seguinte])
        return None

    def classificar(self, decisao, administrador, nota=""):
        """UC12: o administrador decide (Confirmado, Falso positivo ou Resolvido).
        Percorre os estados intermédios do diagrama, por exemplo
        Pendente > Em revisão > Confirmado > Resolvido, para que nenhuma
        transição ilegal seja gravada."""
        if decisao not in (A.EM_REVISAO, A.CONFIRMADO, A.FALSO_POSITIVO, A.RESOLVIDO):
            raise ValidationError("Decisão inválida.")
        caminho = self.caminho_ate(decisao)
        if not caminho:
            raise ValidationError(
                f"O alerta já está em «{self.get_estado_display()}» e não pode passar "
                f"para «{EstadoAlerta(decisao).label}».")
        for passo in caminho:
            self._transitar(passo)
        self.decidido_por = administrador
        self.nota_decisao = nota
        self.data_decisao = timezone.now()
        self.save()

    @classmethod
    def escalar_antigos(cls, horas):
        """Alertas pendentes há mais de N horas passam a Escalado."""
        limite = timezone.now() - timedelta(hours=horas)
        return cls.objects.filter(estado=A.PENDENTE, data_criacao__lt=limite).update(
            estado=A.ESCALADO)


# --- ParametroSistema (UC16) ------------------------------------------------

class TipoParametro(models.TextChoices):
    DECIMAL = "DECIMAL", "Decimal"
    INTEIRO = "INTEIRO", "Inteiro"
    TEXTO = "TEXTO", "Texto"


class ParametroSistema(models.Model):
    chave = models.CharField(max_length=60, unique=True)
    nome = models.CharField(max_length=120)
    descricao = models.TextField()
    valor = models.CharField(max_length=500)
    tipo = models.CharField(max_length=10, choices=TipoParametro.choices)
    minimo = models.FloatField(null=True, blank=True)
    maximo = models.FloatField(null=True, blank=True)
    ultima_actualizacao = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name="+")

    class Meta:
        verbose_name = "parâmetro do sistema"
        verbose_name_plural = "parâmetros do sistema"
        ordering = ["chave"]

    def __str__(self):
        return f"{self.chave} = {self.valor}"

    def valor_convertido(self):
        if self.tipo == TipoParametro.DECIMAL:
            return float(self.valor)
        if self.tipo == TipoParametro.INTEIRO:
            return int(self.valor)
        return self.valor

    def validar_valor(self, valor):
        """Devolve o valor normalizado ou lança erro em português (UC16)."""
        texto = str(valor).strip()
        if not texto:
            raise ValidationError("O valor não pode ficar vazio.")
        if self.tipo in (TipoParametro.DECIMAL, TipoParametro.INTEIRO):
            try:
                numero = float(texto.replace(",", "."))
            except ValueError:
                raise ValidationError("Indique um número.")
            if self.tipo == TipoParametro.INTEIRO and not numero.is_integer():
                raise ValidationError("Indique um número inteiro.")
            if self.minimo is not None and numero < self.minimo:
                raise ValidationError(f"O valor mínimo é {self.minimo:g}.")
            if self.maximo is not None and numero > self.maximo:
                raise ValidationError(f"O valor máximo é {self.maximo:g}.")
            return str(int(numero)) if self.tipo == TipoParametro.INTEIRO else f"{numero:g}"
        return texto


# --- HistoricoInteracao (CT05, RNF08) ---------------------------------------

class TipoAccao(models.TextChoices):
    REGISTO = "REGISTO", "Registo de conta"
    SESSAO = "SESSAO", "Sessão"
    PESQUISA = "PESQUISA", "Pesquisa"
    VISUALIZACAO = "VISUALIZACAO", "Visualização de anúncio"
    FAVORITO = "FAVORITO", "Favorito"
    CHAT = "CHAT", "Assistente virtual"
    ANUNCIO = "ANUNCIO", "Gestão de anúncio"
    MODERACAO = "MODERACAO", "Decisão de moderação"
    UTILIZADOR = "UTILIZADOR", "Gestão de utilizador"
    ALERTA = "ALERTA", "Alerta de fraude"
    PARAMETRO = "PARAMETRO", "Parâmetro do sistema"


class HistoricoInteracao(models.Model):
    """Registo de acções. Serve dois fins: auditoria (RNF08, retenção mínima
    de 12 meses) e dados para as recomendações (CT05)."""
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="historico")
    tipo_accao = models.CharField(max_length=20, choices=TipoAccao.choices)
    descricao = models.CharField(max_length=255)
    dados_contexto = models.JSONField(default=dict, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "histórico de interacção"
        verbose_name_plural = "histórico de interacções"
        ordering = ["-data_hora"]

    @classmethod
    def registar(cls, utilizador, tipo_accao, descricao, **contexto):
        """Método registarLog() do diagrama de classes."""
        if utilizador is not None and not utilizador.is_authenticated:
            utilizador = None
        return cls.objects.create(utilizador=utilizador, tipo_accao=tipo_accao,
                                  descricao=descricao[:255], dados_contexto=contexto)


# --- Notificacao ------------------------------------------------------------

class Notificacao(models.Model):
    """Avisos ao utilizador (por exemplo, anúncio aprovado ou rejeitado, TC19/TC20)."""
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="notificacoes")
    mensagem = models.CharField(max_length=255)
    ligacao = models.CharField(max_length=200, blank=True)
    lida = models.BooleanField(default=False)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data"]
