"""Rotas da API REST."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
