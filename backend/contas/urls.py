from django.urls import path

from . import views

urlpatterns = [
    path("registo/", views.RegistoView.as_view()),
    path("entrar/", views.EntrarView.as_view()),
    path("sair/", views.SairView.as_view()),
    path("perfil/", views.PerfilView.as_view()),
    path("palavra-passe/", views.MudarPalavraPasseView.as_view()),
]
