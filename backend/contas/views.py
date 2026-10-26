"""
Vistas do módulo Autenticação e Perfis.
UC14 Registar conta, UC15 Iniciar e terminar sessão, UC17 Gerir perfil pessoal.
"""
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from administracao.models import HistoricoInteracao, TipoAccao

from .permissoes import ContaActiva
from .serializers import (
    EntrarSerializer,
    MudarPalavraPasseSerializer,
    PerfilSerializer,
    RegistoSerializer,
    UtilizadorSerializer,
)


class RegistoView(APIView):
    """POST /api/auth/registo/ (UC14)"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        utilizador = serializer.save()
        token, _ = Token.objects.get_or_create(user=utilizador)
        HistoricoInteracao.registar(utilizador, TipoAccao.REGISTO, "Conta criada")
        return Response(
            {"token": token.key, "utilizador": UtilizadorSerializer(utilizador).data},
            status=status.HTTP_201_CREATED,
        )


class EntrarView(APIView):
    """POST /api/auth/entrar/ (UC15). Devolve o token que o cliente envia em
    cada pedido seguinte. O servidor não guarda sessão (RNF04)."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EntrarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        utilizador = serializer.validated_data["utilizador"]
        token, _ = Token.objects.get_or_create(user=utilizador)
        HistoricoInteracao.registar(utilizador, TipoAccao.SESSAO, "Início de sessão")
        return Response({"token": token.key, "utilizador": UtilizadorSerializer(utilizador).data})


class SairView(APIView):
    """POST /api/auth/sair/ (UC15). Apagar o token invalida a sessão."""
    permission_classes = [ContaActiva]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PerfilView(APIView):
    """GET e PATCH /api/auth/perfil/ (UC17)"""
    permission_classes = [ContaActiva]

    def get(self, request):
        return Response(UtilizadorSerializer(request.user).data)

    def patch(self, request):
        serializer = PerfilSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UtilizadorSerializer(request.user).data)


class MudarPalavraPasseView(APIView):
    """POST /api/auth/palavra-passe/ (UC17)"""
    permission_classes = [ContaActiva]

    def post(self, request):
        serializer = MudarPalavraPasseSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["nova"])
        request.user.save()
        # Novo token: as sessões antigas deixam de ser válidas
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({"token": token.key})
