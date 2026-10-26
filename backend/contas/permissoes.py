"""
Controlo de permissões por perfil (exigência da Fase III).

Cada classe responde a uma pergunta simples: "este pedido pode continuar?".
As vistas da API indicam quais destas classes se aplicam. O menu do React
usa a mesma regra para mostrar só as opções de cada perfil.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import EstadoConta, Perfil


class ContaActiva(BasePermission):
    message = "A sua conta não está activa. Contacte o administrador."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.estado == EstadoConta.ACTIVO)


class EhInquilino(ContaActiva):
    message = "Esta funcionalidade é exclusiva do perfil Inquilino/Comprador."

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.perfil == Perfil.INQUILINO


class EhProprietario(ContaActiva):
    message = "Esta funcionalidade é exclusiva do perfil Proprietário/Agência."

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.perfil == Perfil.PROPRIETARIO


class EhAdministrador(ContaActiva):
    message = "Acesso reservado ao administrador."

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.perfil == Perfil.ADMINISTRADOR


class EhTitularDoAnuncio(BasePermission):
    """Permissão ao nível do objecto: só o dono altera ou remove o anúncio (TC17)."""
    message = "Só o titular do anúncio pode alterá-lo ou removê-lo."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.anunciante_id == request.user.id
