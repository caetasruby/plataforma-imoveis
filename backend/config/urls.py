"""Rotas da API REST."""
from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from administracao import views as adm
from anuncios import views as anu

router = DefaultRouter()
router.register("anuncios", anu.AnuncioPublicoViewSet, basename="anuncios")
router.register("meus-anuncios", anu.MeusAnunciosViewSet, basename="meus-anuncios")
router.register("admin/moderacao", adm.ModeracaoViewSet, basename="moderacao")
router.register("admin/utilizadores", adm.UtilizadoresViewSet, basename="utilizadores")
router.register("admin/alertas", adm.AlertasViewSet, basename="alertas")
router.register("admin/parametros", adm.ParametrosViewSet, basename="parametros")
router.register("admin/registos", adm.RegistosView, basename="registos")

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/auth/", include("contas.urls")),
    path("api/estimativa-preco/", anu.EstimativaPrecoView.as_view()),
    path("api/favoritos/", anu.FavoritosView.as_view()),
    path("api/favoritos/<int:anuncio_id>/", anu.FavoritoDetalheView.as_view()),
    path("api/recomendacoes/", anu.RecomendacoesView.as_view()),
    path("api/assistente/", anu.AssistenteView.as_view()),
    path("api/notificacoes/", anu.NotificacoesView.as_view()),
    path("api/admin/indicadores/", adm.IndicadoresView.as_view()),
    path("api/admin/indicadores/exportar/", adm.ExportarIndicadoresView.as_view()),
    path("api/", include(router.urls)),
    # Fotografias enviadas (no Docker é o nginx que as serve; aqui serve o Django)
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]


def cliente_react(pedido):
    """Qualquer outra rota devolve o index.html do React (SPA), como o nginx no Docker."""
    if not settings.FRONTEND_DIST:
        raise Http404
    return FileResponse(open(f"{settings.FRONTEND_DIST}/index.html", "rb"), content_type="text/html")


urlpatterns.append(re_path(r"^(?!api/|django-admin/|static/|media/).*$", cliente_react))
