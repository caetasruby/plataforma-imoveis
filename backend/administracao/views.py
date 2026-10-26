"""
Painel de Administração (todas as vistas exigem o perfil Administrador).
UC10 Moderar anúncios, UC11 Gerir utilizadores, UC12 Acompanhar alertas,
UC13 Indicadores, UC16 Gerir parâmetros e consulta dos logs (RNF08).
"""
import csv
from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError as ErroDjango
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from anuncios.models import Anuncio, EstadoAnuncio
from anuncios.serializers import erro_django_para_drf
from contas.models import EstadoConta, Utilizador
from contas.permissoes import EhAdministrador
from contas.serializers import UtilizadorSerializer

from .configuracao import Configuracao
from .models import (
    AlertaFraude,
    EstadoAlerta,
    HistoricoInteracao,
    ParametroSistema,
    TipoAccao,
)
from .serializers import (
    AlertaSerializer,
    AnuncioModeracaoSerializer,
    ClassificarAlertaSerializer,
    HistoricoSerializer,
    ParametroSerializer,
    RejeitarSerializer,
)
from .sinais import anuncio_moderado, estado_conta_alterado, parametro_alterado


# --- UC10 Moderar anúncios -----------------------------------------------------

class ModeracaoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    permission_classes = [EhAdministrador]
    serializer_class = AnuncioModeracaoSerializer

    def get_queryset(self):
        qs = (Anuncio.objects.select_related("imovel", "anunciante")
              .prefetch_related("imagens", "alertas__decidido_por"))
        if self.action == "list":
            # Fila: pendentes, os de maior risco primeiro (TC18)
            qs = qs.filter(estado=EstadoAnuncio.PENDENTE).order_by("-pontuacao_risco",
                                                                   "data_criacao")
        return qs

    def _decidir(self, anuncio, aprovado, motivo=""):
        try:
            if aprovado:
                anuncio.mudar_estado(EstadoAnuncio.PUBLICADO)
            else:
                anuncio.motivo_rejeicao = motivo
                anuncio.mudar_estado(EstadoAnuncio.REJEITADO)
        except ErroDjango as erro:
            raise erro_django_para_drf(erro)
        # Padrão Observer: os receptores gravam o log e notificam o anunciante
        anuncio_moderado.send(sender=self.__class__, anuncio=anuncio,
                              administrador=self.request.user, aprovado=aprovado, motivo=motivo)
        return Response(self.get_serializer(anuncio).data)

    @action(detail=True, methods=["post"])
    def aprovar(self, request, pk=None):
        return self._decidir(self.get_object(), aprovado=True)

    @action(detail=True, methods=["post"])
    def rejeitar(self, request, pk=None):
        serializer = RejeitarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._decidir(self.get_object(), aprovado=False,
                             motivo=serializer.validated_data["motivo"])


# --- UC11 Gerir utilizadores ----------------------------------------------------

class UtilizadoresViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    permission_classes = [EhAdministrador]
    serializer_class = UtilizadorSerializer

    def get_queryset(self):
        qs = Utilizador.objects.annotate(num_anuncios=Count("anuncios")).order_by("nome")
        p = self.request.query_params
        if p.get("perfil"):
            qs = qs.filter(perfil=p["perfil"])
        if p.get("estado"):
            qs = qs.filter(estado=p["estado"])
        if p.get("q"):
            qs = qs.filter(Q(nome__icontains=p["q"]) | Q(email__icontains=p["q"]))
        return qs

    def _mudar(self, conta, novo_estado):
        if conta.id == self.request.user.id:
            return Response({"detail": "Não pode alterar o estado da sua própria conta."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            conta.mudar_estado(novo_estado)
        except ErroDjango as erro:
            raise erro_django_para_drf(erro)
        if novo_estado != EstadoConta.ACTIVO:
            Token.objects.filter(user=conta).delete()   # termina a sessão imediatamente
        estado_conta_alterado.send(sender=self.__class__, conta=conta,
                                   administrador=self.request.user, novo_estado=novo_estado)
        return Response(UtilizadorSerializer(conta).data)

    @action(detail=True, methods=["post"])
    def bloquear(self, request, pk=None):
        return self._mudar(self.get_object(), EstadoConta.BLOQUEADO)

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        return self._mudar(self.get_object(), EstadoConta.DESACTIVADO)

    @action(detail=True, methods=["post"])
    def reactivar(self, request, pk=None):
        return self._mudar(self.get_object(), EstadoConta.ACTIVO)


# --- UC12 Acompanhar alertas ----------------------------------------------------

class AlertasViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    permission_classes = [EhAdministrador]
    serializer_class = AlertaSerializer

    def get_queryset(self):
        qs = AlertaFraude.objects.select_related("anuncio", "decidido_por")
        p = self.request.query_params
        for campo in ("gravidade", "tipo_alerta", "estado"):
            if p.get(campo):
                qs = qs.filter(**{campo: p[campo]})
        if p.get("abertos") == "1":
            qs = qs.filter(estado__in=[EstadoAlerta.PENDENTE, EstadoAlerta.ESCALADO,
                                       EstadoAlerta.EM_REVISAO, EstadoAlerta.CONFIRMADO])
        if p.get("inicio"):
            qs = qs.filter(data_criacao__date__gte=p["inicio"])
        if p.get("fim"):
            qs = qs.filter(data_criacao__date__lte=p["fim"])
        ordem = p.get("ordenar", "-data_criacao")
        if ordem in ("-data_criacao", "data_criacao", "-pontuacao_risco", "pontuacao_risco"):
            qs = qs.order_by(ordem)
        return qs

    def list(self, request, *args, **kwargs):
        # Antes de listar, escala os alertas esquecidos (diagrama de estados)
        AlertaFraude.escalar_antigos(Configuracao.instancia().obter("horas_escalamento_alerta"))
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def classificar(self, request, pk=None):
        serializer = ClassificarAlertaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alerta = self.get_object()
        try:
            alerta.classificar(serializer.validated_data["decisao"], request.user,
                               serializer.validated_data.get("nota", ""))
        except ErroDjango as erro:
            raise erro_django_para_drf(erro)
        return Response(self.get_serializer(alerta).data)


# --- UC13 Indicadores -------------------------------------------------------------

def _periodo(request):
    hoje = timezone.localdate()
    try:
        inicio = datetime.strptime(request.query_params.get("inicio", ""), "%Y-%m-%d").date()
    except ValueError:
        inicio = hoje - timedelta(days=29)
    try:
        fim = datetime.strptime(request.query_params.get("fim", ""), "%Y-%m-%d").date()
    except ValueError:
        fim = hoje
    if inicio > fim:
        inicio, fim = fim, inicio
    tz = timezone.get_current_timezone()
    return (inicio, fim, timezone.make_aware(datetime.combine(inicio, time.min), tz),
            timezone.make_aware(datetime.combine(fim, time.max), tz))


def calcular_indicadores(request):
    inicio, fim, desde, ate = _periodo(request)
    anuncios_periodo = Anuncio.objects.filter(data_criacao__range=(desde, ate))
    historico = HistoricoInteracao.objects.filter(data_hora__range=(desde, ate))
    moderacoes = historico.filter(tipo_accao=TipoAccao.MODERACAO)

    serie = {}

    def contar(dia, campo, n):
        serie.setdefault(str(dia), {"anuncios": 0, "publicados": 0, "pesquisas": 0})[campo] = n

    for linha in (anuncios_periodo.annotate(dia=TruncDate("data_criacao")).values("dia")
                  .annotate(n=Count("id"))):
        contar(linha["dia"], "anuncios", linha["n"])
    for linha in (Anuncio.objects.filter(data_publicacao__range=(desde, ate))
                  .annotate(dia=TruncDate("data_publicacao")).values("dia").annotate(n=Count("id"))):
        contar(linha["dia"], "publicados", linha["n"])
    for linha in (historico.filter(tipo_accao=TipoAccao.PESQUISA)
                  .annotate(dia=TruncDate("data_hora")).values("dia").annotate(n=Count("id"))):
        contar(linha["dia"], "pesquisas", linha["n"])

    publicados = Anuncio.objects.filter(estado=EstadoAnuncio.PUBLICADO)
    por_cidade = []
    for linha in (publicados.values("imovel__cidade").annotate(
            total=Count("id"),
            renda_media=Avg("preco", filter=Q(finalidade="ARRENDAMENTO")),
            venda_media=Avg("preco", filter=Q(finalidade="VENDA"))).order_by("-total")):
        por_cidade.append({"cidade": linha["imovel__cidade"].title(), "total": linha["total"],
                           "renda_media": round(float(linha["renda_media"] or 0)),
                           "venda_media": round(float(linha["venda_media"] or 0))})

    alertas_periodo = AlertaFraude.objects.filter(data_criacao__range=(desde, ate))

    # Tempo médio entre a submissão e a publicação (decisão do administrador), em horas
    media = (publicados.exclude(data_publicacao=None)
             .aggregate(m=Avg(ExpressionWrapper(F("data_publicacao") - F("data_criacao"),
                                                output_field=DurationField())))["m"])
    tempo_medio = round(media.total_seconds() / 3600, 1) if media is not None else None
    return {
        "periodo": {"inicio": str(inicio), "fim": str(fim)},
        "totais": {
            "anuncios_publicados": publicados.count(),
            "anuncios_pendentes": Anuncio.objects.filter(estado=EstadoAnuncio.PENDENTE).count(),
            "utilizadores_activos": Utilizador.objects.filter(estado=EstadoConta.ACTIVO).count(),
            "tempo_medio_moderacao_horas": tempo_medio,
            "alertas_abertos": AlertaFraude.objects.filter(estado__in=[
                EstadoAlerta.PENDENTE, EstadoAlerta.ESCALADO, EstadoAlerta.EM_REVISAO]).count(),
        },
        "no_periodo": {
            "novos_anuncios": anuncios_periodo.count(),
            "novos_utilizadores": Utilizador.objects.filter(date_joined__range=(desde, ate)).count(),
            "pesquisas": historico.filter(tipo_accao=TipoAccao.PESQUISA).count(),
            "visualizacoes": historico.filter(tipo_accao=TipoAccao.VISUALIZACAO).count(),
            "perguntas_assistente": historico.filter(tipo_accao=TipoAccao.CHAT).count(),
            "alertas_gerados": alertas_periodo.count(),
            "aprovados": moderacoes.filter(dados_contexto__decisao="aprovado").count(),
            "rejeitados": moderacoes.filter(dados_contexto__decisao="rejeitado").count(),
        },
        "serie_diaria": [{"dia": d, **v} for d, v in sorted(serie.items())],
        "por_cidade": por_cidade,
        "alertas_por_tipo": [
            {"tipo": AlertaFraude(tipo_alerta=l["tipo_alerta"]).get_tipo_alerta_display(),
             "total": l["n"]}
            for l in alertas_periodo.values("tipo_alerta").annotate(n=Count("id")).order_by("-n")],
    }


class IndicadoresView(APIView):
    permission_classes = [EhAdministrador]

    def get(self, request):
        return Response(calcular_indicadores(request))


class ExportarIndicadoresView(APIView):
    """Exporta o relatório em CSV (abre no Excel), TC26."""
    permission_classes = [EhAdministrador]

    def get(self, request):
        dados = calcular_indicadores(request)
        resposta = HttpResponse(content_type="text/csv; charset=utf-8")
        nome = f"indicadores_{dados['periodo']['inicio']}_{dados['periodo']['fim']}.csv"
        resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
        resposta.write("﻿")   # BOM: o Excel reconhece os acentos
        w = csv.writer(resposta, delimiter=";")
        w.writerow(["Relatório de indicadores", dados["periodo"]["inicio"], dados["periodo"]["fim"]])
        w.writerow([])
        w.writerow(["Indicador", "Valor"])
        for chave, valor in {**dados["totais"], **dados["no_periodo"]}.items():
            w.writerow([chave.replace("_", " ").capitalize(), "" if valor is None else valor])
        w.writerow([])
        w.writerow(["Cidade", "Anúncios publicados", "Renda média (MT)", "Venda média (MT)"])
        for c in dados["por_cidade"]:
            w.writerow([c["cidade"], c["total"], c["renda_media"], c["venda_media"]])
        w.writerow([])
        w.writerow(["Dia", "Novos anúncios", "Anúncios publicados", "Pesquisas"])
        for d in dados["serie_diaria"]:
            w.writerow([d["dia"], d["anuncios"], d["publicados"], d["pesquisas"]])
        return resposta


# --- UC16 Gerir parâmetros do sistema -------------------------------------------------

class ParametrosViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    permission_classes = [EhAdministrador]
    serializer_class = ParametroSerializer
    queryset = ParametroSistema.objects.all()
    pagination_class = None
    http_method_names = ["get", "patch"]

    def perform_update(self, serializer):
        anterior = serializer.instance.valor
        parametro = serializer.save(actualizado_por=self.request.user)
        if anterior != parametro.valor:
            parametro_alterado.send(sender=self.__class__, parametro=parametro,
                                    administrador=self.request.user, valor_anterior=anterior)


# --- Logs de auditoria (RNF08) -------------------------------------------------------

class RegistosView(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [EhAdministrador]
    serializer_class = HistoricoSerializer

    def get_queryset(self):
        qs = HistoricoInteracao.objects.select_related("utilizador")
        tipo = self.request.query_params.get("tipo")
        if tipo:
            qs = qs.filter(tipo_accao=tipo)
        else:
            # Por omissão mostra apenas as acções relevantes para auditoria
            qs = qs.filter(tipo_accao__in=[TipoAccao.MODERACAO, TipoAccao.UTILIZADOR,
                                           TipoAccao.ALERTA, TipoAccao.PARAMETRO,
                                           TipoAccao.ANUNCIO])
        return qs
