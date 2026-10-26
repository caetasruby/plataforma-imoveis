"""
Serializers do módulo de contas: convertem JSON em objectos e validam os
dados do lado do servidor (segunda camada de validação; a primeira está nos
formulários do React).
"""
import re

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .fabrica import FabricaUtilizador
from .models import EstadoConta, Perfil, Utilizador

# Números moçambicanos: 82 a 87 seguidos de 7 dígitos, com ou sem +258
PADRAO_CONTACTO = re.compile(r"^(\+258)?8[2-7]\d{7}$")


def validar_contacto(valor):
    limpo = valor.replace(" ", "")
    if limpo and not PADRAO_CONTACTO.match(limpo):
        raise serializers.ValidationError(
            "Indique um número moçambicano válido, por exemplo 84 123 4567."
        )
    return limpo


class UtilizadorSerializer(serializers.ModelSerializer):
    """Dados públicos do utilizador devolvidos ao cliente."""
    perfil_nome = serializers.CharField(source="get_perfil_display", read_only=True)
    estado_nome = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Utilizador
        fields = ["id", "email", "nome", "contacto", "perfil", "perfil_nome",
                  "estado", "estado_nome", "nome_agencia", "date_joined"]
        read_only_fields = ["id", "email", "perfil", "estado", "date_joined"]


class RegistoSerializer(serializers.Serializer):
    """UC14 Registar conta."""
    nome = serializers.CharField(max_length=120, error_messages={
        "blank": "Indique o seu nome completo."})
    email = serializers.EmailField(error_messages={
        "invalid": "Indique um endereço de e-mail válido.",
        "blank": "Indique o seu e-mail."})
    contacto = serializers.CharField(max_length=20, required=False, allow_blank=True)
    perfil = serializers.ChoiceField(
        # No registo público não é possível escolher o perfil de administrador
        choices=[Perfil.INQUILINO, Perfil.PROPRIETARIO],
        error_messages={"invalid_choice": "Escolha Inquilino/Comprador ou Proprietário/Agência."})
    nome_agencia = serializers.CharField(max_length=120, required=False, allow_blank=True)
    palavra_passe = serializers.CharField(write_only=True)
    confirmar_palavra_passe = serializers.CharField(write_only=True)

    def validate_nome(self, valor):
        valor = valor.strip()
        if len(valor) < 3 or " " not in valor:
            raise serializers.ValidationError("Indique o nome e o apelido.")
        return valor

    def validate_email(self, valor):
        if Utilizador.objects.filter(email__iexact=valor).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return valor.lower()

    def validate_contacto(self, valor):
        return validar_contacto(valor)

    def validate(self, dados):
        if dados["palavra_passe"] != dados["confirmar_palavra_passe"]:
            raise serializers.ValidationError(
                {"confirmar_palavra_passe": "As palavras-passe não coincidem."})
        # Regras do Django: mínimo 8 caracteres, não só números, não comum
        candidato = Utilizador(email=dados["email"], nome=dados["nome"])
        try:
            validate_password(dados["palavra_passe"], candidato)
        except Exception as erro:
            raise serializers.ValidationError({"palavra_passe": list(erro.messages)})
        return dados

    def create(self, dados):
        return FabricaUtilizador.criar(
            perfil=dados["perfil"],
            email=dados["email"],
            palavra_passe=dados["palavra_passe"],
            nome=dados["nome"],
            contacto=dados.get("contacto", ""),
            nome_agencia=dados.get("nome_agencia", ""),
        )


class EntrarSerializer(serializers.Serializer):
    """UC15 Iniciar sessão."""
    email = serializers.EmailField(error_messages={"invalid": "Indique um e-mail válido."})
    palavra_passe = serializers.CharField(write_only=True)

    def validate(self, dados):
        try:
            conta = Utilizador.objects.get(email__iexact=dados["email"])
        except Utilizador.DoesNotExist:
            conta = None

        # Mensagens específicas para contas que existem mas estão restringidas
        if conta and conta.check_password(dados["palavra_passe"]):
            if conta.estado == EstadoConta.BLOQUEADO:
                raise serializers.ValidationError(
                    "A sua conta foi bloqueada pelo administrador.")
            if conta.estado == EstadoConta.DESACTIVADO:
                raise serializers.ValidationError(
                    "A sua conta está desactivada. Contacte o administrador.")

        utilizador = authenticate(username=dados["email"].lower(),
                                  password=dados["palavra_passe"])
        if utilizador is None:
            raise serializers.ValidationError("E-mail ou palavra-passe incorrectos.")
        dados["utilizador"] = utilizador
        return dados


class PerfilSerializer(serializers.ModelSerializer):
    """UC17 Gerir perfil pessoal (o e-mail e o perfil não se alteram)."""

    class Meta:
        model = Utilizador
        fields = ["nome", "contacto", "nome_agencia"]

    def validate_nome(self, valor):
        return RegistoSerializer().validate_nome(valor)

    def validate_contacto(self, valor):
        return validar_contacto(valor)


class MudarPalavraPasseSerializer(serializers.Serializer):
    actual = serializers.CharField(write_only=True)
    nova = serializers.CharField(write_only=True)

    def validate_actual(self, valor):
        if not self.context["request"].user.check_password(valor):
            raise serializers.ValidationError("A palavra-passe actual está incorrecta.")
        return valor

    def validate_nova(self, valor):
        try:
            validate_password(valor, self.context["request"].user)
        except Exception as erro:
            raise serializers.ValidationError(list(erro.messages))
        return valor
