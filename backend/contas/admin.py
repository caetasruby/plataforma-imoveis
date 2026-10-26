from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilizador


@admin.register(Utilizador)
class UtilizadorAdmin(UserAdmin):
    list_display = ("email", "nome", "perfil", "estado")
    list_filter = ("perfil", "estado")
    fieldsets = UserAdmin.fieldsets + (("Plataforma", {"fields": ("nome", "contacto", "perfil", "estado", "nome_agencia")}),)
