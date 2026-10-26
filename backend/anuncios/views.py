"""
Vistas dos anúncios.

Público / Inquilino:  UC04 Pesquisar, UC05 Preço justo, UC06 Alertas de fraude,
                      UC07 Mapa, UC08 Recomendações, UC09 Assistente, UC18 Favoritos.
Proprietário:         UC01 Publicar, UC02 Editar, UC03 Remover.
"""
from django.core.exceptions import ValidationError as ErroDjango
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from administracao.models import HistoricoInteracao, Notificacao, TipoAccao
from contas.permissoes import ContaActiva, EhInquilino, EhProprietario, EhTitularDoAnuncio
from ia.fachada import ServicosIA
from ia.imagens import calcular_hash

from .models import Anuncio, EstadoAnuncio, Favorito, ImagemImovel, Imovel
from .serializers import (
    AnuncioDetalheSerializer,
    AnuncioEscritaSerializer,
    AnuncioListaSerializer,
    FavoritoSerializer,
    erro_django_para_drf,
)

FILTROS_PESQUISA = ["cidade", "tipo", "finalidade", "preco_min", "preco_max",
                    "divisoes_min", "area_min", "q", "apenas_preco_justo"]


def _ids_favoritos(request):
    if request.user.is_authenticated:
        return set(request.user.favoritos.values_list("anuncio_id", flat=True))
    return None


def _base():
    return (Anuncio.objects.select_related("imovel", "anunciante")
            .prefetch_related("imagens", "alertas"))


# --- UC04 a UC07: pesquisa e detalhe (público) ------------------------------

class AnuncioPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    throttle_scope = None   # só a acção "mapa" tem limite de pedidos (RNF09)

    def get_queryset(self):
        qs = _base().filter(estado=EstadoAnuncio.PUBLICADO)
        if self.action != "list":
            # O titular e o administrador também podem abrir anúncios não publicados
            u = self.request.user
            if u.is_authenticated:
                if u.eh_administrador:
                    qs = _base()
                else:
                    qs = _base().filter(Q(estado=EstadoAnuncio.PUBLICADO) | Q(anunciante=u))
            return qs
        return self._filtrar(qs)

    def _filtrar(self, qs):
        p = self.request.query_params
        if p.get("cidade"):
            qs = qs.filter(imovel__cidade=p["cidade"])
        if p.get("tipo"):
            qs = qs.filter(imovel__tipo=p["tipo"])
        if p.get("finalidade"):
            qs = qs.filter(finalidade=p["finalidade"])
        if p.get("preco_min"):
            qs = qs.filter(preco__gte=p["preco_min"])
        if p.get("preco_max"):
            qs = qs.filter(preco__lte=p["preco_max"])
        if p.get("divisoes_min"):
            qs = qs.filter(imovel__num_divisoes__gte=p["divisoes_min"])
        if p.get("area_min"):
            qs = qs.filter(imovel__area__gte=p["area_min"])
        if p.get("apenas_preco_justo") in ("1", "true", "sim"):
            # Só anúncios cujo preço está dentro do intervalo justo estimado pela IA
            qs = qs.filter(preco_justo_min__lte=F("preco"), preco_justo_max__gte=F("preco"))
        if p.get("q"):
            termo = p["q"].strip()
            qs = qs.filter(Q(titulo__icontains=termo) | Q(imovel__bairro__icontains=termo)
                           | Q(descricao__icontains=termo))

        # Ordenação (TC03): relevância, preço ou data
        ordem = p.get("ordenar", "relevancia")
        if ordem == "preco":
            qs = qs.order_by("preco")
        elif ordem == "-preco":
            qs = qs.order_by("-preco")
        elif ordem == "data":
            qs = qs.order_by("-data_publicacao")
        else:
            # Relevância: primeiro os de menor risco e mais vistos, depois os mais recentes
            qs = qs.order_by("pontuacao_risco", "-visualizacoes", "-data_publicacao")
        return qs

    def get_serializer_class(self):
        return AnuncioDetalheSerializer if self.action == "retrieve" else AnuncioListaSerializer

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        contexto["favoritos"] = _ids_favoritos(self.request)
        return contexto

    def list(self, request, *args, **kwargs):
        # Guarda a pesquisa no histórico (CT05), só na primeira página
        filtros = {k: v for k, v in request.query_params.items() if k in FILTROS_PESQUISA and v}
        if filtros and request.user.is_authenticated and request.query_params.get("page", "1") == "1":
            HistoricoInteracao.registar(request.user, TipoAccao.PESQUISA, "Pesquisa de imóveis",
                                        filtros=filtros)
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        anuncio = self.get_object()
        if anuncio.estado == EstadoAnuncio.PUBLICADO:
            Anuncio.objects.filter(id=anuncio.id).update(visualizacoes=F("visualizacoes") + 1)
            if request.user.is_authenticated:
                HistoricoInteracao.registar(request.user, TipoAccao.VISUALIZACAO,
                                            f"Viu o anúncio #{anuncio.id}", anuncio=anuncio.id)
        return Response(self.get_serializer(anuncio).data)

    @action(detail=True, throttle_classes=[ScopedRateThrottle], throttle_scope="mapa")
    def mapa(self, request, pk=None):
        """UC07: localização e distâncias a pontos de interesse (CT04)."""
        imovel = self.get_object().imovel
        return Response({
            "latitude": float(imovel.latitude), "longitude": float(imovel.longitude),
            "endereco": f"{imovel.endereco}, {imovel.bairro}, {imovel.get_cidade_display()}",
            "pontos_interesse": imovel.calcular_distancias_poi(),
        })

    @action(detail=True)
    def semelhantes(self, request, pk=None):
        sugestoes = ServicosIA().semelhantes(self.get_object())
        dados = AnuncioListaSerializer([a for a, _ in sugestoes], many=True,
                                       context=self.get_serializer_context()).data
        return Response(dados)


# --- UC01 a UC03: anúncios do proprietário -----------------------------------

class MeusAnunciosViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    permission_classes = [EhProprietario, EhTitularDoAnuncio]
    pagination_class = None

    def get_queryset(self):
        return _base().filter(anunciante=self.request.user).exclude(estado=EstadoAnuncio.REMOVIDO)

    def get_serializer_class(self):
        return AnuncioDetalheSerializer if self.action == "retrieve" else AnuncioListaSerializer

    def _guardar_imagens(self, anuncio, ficheiros, a_remover=()):
        if a_remover:
            anuncio.imagens.filter(id__in=a_remover).delete()
        inicio = anuncio.imagens.count()
        for ordem, ficheiro in enumerate(ficheiros, start=inicio):
            ImagemImovel.objects.create(anuncio=anuncio, ficheiro=ficheiro, ordem=ordem,
                                        checksum_hash=calcular_hash(ficheiro))

    def _resposta_analise(self, anuncio, alertas, codigo):
        dados = AnuncioDetalheSerializer(anuncio, context={"request": self.request}).data
        dados["mensagem"] = ("Anúncio submetido. Está pendente de moderação e ficará visível "
                             "depois de aprovado pelo administrador.")
        dados["alertas_gerados"] = len(alertas)
        return Response(dados, status=codigo)

    def create(self, request):
        """UC01 Publicar anúncio."""
        serializer = AnuncioEscritaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        with transaction.atomic():
            imovel = Imovel.objects.create(
                tipo=d["tipo"], area=d["area"], num_divisoes=d["num_divisoes"],
                cidade=d["cidade"], bairro=d["bairro"].strip(), endereco=d["endereco"].strip(),
                latitude=d["latitude"], longitude=d["longitude"])
            anuncio = Anuncio.objects.create(
                imovel=imovel, anunciante=request.user, titulo=d["titulo"],
                descricao=d["descricao"], preco=d["preco"], finalidade=d["finalidade"])
            self._guardar_imagens(anuncio, d.get("imagens", []))
            alertas = ServicosIA().analisar_anuncio(anuncio)   # Fachada
        HistoricoInteracao.registar(request.user, TipoAccao.ANUNCIO,
                                    f"Publicou o anúncio #{anuncio.id}", anuncio=anuncio.id)
        return self._resposta_analise(anuncio, alertas, status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """UC02 Editar anúncio: revalida, reanalisa e volta à moderação."""
        anuncio = self.get_object()
        if anuncio.estado in (EstadoAnuncio.SUBMETIDO, EstadoAnuncio.EM_ANALISE):
            return Response({"detail": "O anúncio ainda está a ser analisado."},
                            status=status.HTTP_409_CONFLICT)
        serializer = AnuncioEscritaSerializer(anuncio, data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        try:
            with transaction.atomic():
                imovel = anuncio.imovel
                for campo in ["tipo", "area", "num_divisoes", "cidade", "bairro", "endereco",
                              "latitude", "longitude"]:
                    setattr(imovel, campo, d[campo])
                imovel.save()
                for campo in ["titulo", "descricao", "preco", "finalidade"]:
                    setattr(anuncio, campo, d[campo])
                anuncio.save()
                self._guardar_imagens(anuncio, d.get("imagens", []), d.get("remover_imagens", []))
                alertas = ServicosIA().analisar_anuncio(anuncio)
        except ErroDjango as erro:
            raise erro_django_para_drf(erro)
        HistoricoInteracao.registar(request.user, TipoAccao.ANUNCIO,
                                    f"Editou o anúncio #{anuncio.id}", anuncio=anuncio.id)
        return self._resposta_analise(anuncio, alertas, status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        """UC03 Remover anúncio (fica no estado Removido, não é apagado)."""
        anuncio = self.get_object()
        try:
            anuncio.mudar_estado(EstadoAnuncio.REMOVIDO)
        except ErroDjango as erro:
            raise erro_django_para_drf(erro)
        HistoricoInteracao.registar(request.user, TipoAccao.ANUNCIO,
                                    f"Removeu o anúncio #{anuncio.id}", anuncio=anuncio.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EstimativaPrecoView(APIView):
    """Pré-visualização do preço justo no formulário de publicação."""
    permission_classes = [EhProprietario]

    def post(self, request):
        campos = ["finalidade", "tipo", "cidade", "bairro", "area", "num_divisoes"]
        em_falta = [c for c in campos if not str(request.data.get(c, "")).strip()]
        if em_falta:
            return Response({"detail": "Preencha tipo, cidade, bairro, área e divisões."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            e = ServicosIA().estimar_preco(*(request.data[c] for c in campos))
        except (ValueError, TypeError):
            return Response({"detail": "Valores inválidos."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"valor": e.valor, "minimo": e.minimo, "maximo": e.maximo,
                         "metodo": e.metodo})


# --- UC18 Favoritos -----------------------------------------------------------

class FavoritosView(APIView):
    permission_classes = [EhInquilino]

    def get(self, request):
        favoritos = (Favorito.objects.filter(utilizador=request.user,
                                             anuncio__estado=EstadoAnuncio.PUBLICADO)
                     .select_related("anuncio__imovel").prefetch_related("anuncio__imagens",
                                                                         "anuncio__alertas"))
        contexto = {"request": request, "favoritos": _ids_favoritos(request)}
        return Response(FavoritoSerializer(favoritos, many=True, context=contexto).data)

    def post(self, request):
        anuncio = get_object_or_404(Anuncio, id=request.data.get("anuncio"),
                                    estado=EstadoAnuncio.PUBLICADO)
        _, criado = Favorito.objects.get_or_create(utilizador=request.user, anuncio=anuncio)
        if criado:
            HistoricoInteracao.registar(request.user, TipoAccao.FAVORITO,
                                        f"Guardou o anúncio #{anuncio.id}", anuncio=anuncio.id)
        return Response({"favorito": True},
                        status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK)


class FavoritoDetalheView(APIView):
    permission_classes = [EhInquilino]

    def delete(self, request, anuncio_id):
        Favorito.objects.filter(utilizador=request.user, anuncio_id=anuncio_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- UC08 Recomendações e UC09 Assistente --------------------------------------

class RecomendacoesView(APIView):
    permission_classes = [EhInquilino]

    def get(self, request):
        sugestoes = ServicosIA().recomendar(request.user)
        contexto = {"request": request, "favoritos": _ids_favoritos(request)}
        resultado = []
        for anuncio, motivo in sugestoes:
            dados = AnuncioListaSerializer(anuncio, context=contexto).data
            dados["motivo"] = motivo
            resultado.append(dados)
        return Response(resultado)


class AssistenteView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "assistente"

    def post(self, request):
        pergunta = str(request.data.get("pergunta", "")).strip()
        if not pergunta:
            return Response({"pergunta": ["Escreva uma pergunta."]},
                            status=status.HTTP_400_BAD_REQUEST)
        if len(pergunta) > 500:
            return Response({"pergunta": ["A pergunta deve ter no máximo 500 caracteres."]},
                            status=status.HTTP_400_BAD_REQUEST)
        resposta = ServicosIA().responder_pergunta(pergunta, request.data.get("topico_anterior"))
        HistoricoInteracao.registar(request.user, TipoAccao.CHAT, pergunta[:200],
                                    topico=resposta["topico"])
        return Response(resposta)


# --- Notificações -------------------------------------------------------------

class NotificacoesView(APIView):
    permission_classes = [ContaActiva]

    def get(self, request):
        notificacoes = request.user.notificacoes.all()[:30]
        return Response({
            "nao_lidas": request.user.notificacoes.filter(lida=False).count(),
            "lista": [{"id": n.id, "mensagem": n.mensagem, "ligacao": n.ligacao,
                       "lida": n.lida, "data": n.data} for n in notificacoes],
        })

    def post(self, request):
        """Marca todas como lidas."""
        Notificacao.objects.filter(utilizador=request.user, lida=False).update(lida=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
