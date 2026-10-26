"""
Modelos do módulo Autenticação e Perfis (UC14, UC15, UC17 e UC11).

No diagrama de classes, Utilizador é uma classe abstracta com três
especializações. No Django guardamos todos os utilizadores numa só tabela
(campo "perfil") e criamos três modelos "proxy", um por especialização.
Um modelo proxy usa a mesma tabela mas pode ter comportamento próprio.
"""
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models


class Perfil(models.TextChoices):
    INQUILINO = "INQUILINO", "Inquilino/Comprador"
    PROPRIETARIO = "PROPRIETARIO", "Proprietário/Agência"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"


class EstadoConta(models.TextChoices):
    """Estados do diagrama de estados da conta de utilizador (secção 13)."""
    PENDENTE = "PENDENTE", "Pendente de verificação"
    ACTIVO = "ACTIVO", "Activo"
    BLOQUEADO = "BLOQUEADO", "Bloqueado"
    DESACTIVADO = "DESACTIVADO", "Desactivado"


# Transições permitidas pelo diagrama de estados. Qualquer outra é recusada (TC23).
TRANSICOES_CONTA = {
    EstadoConta.PENDENTE: {EstadoConta.ACTIVO},
    EstadoConta.ACTIVO: {EstadoConta.BLOQUEADO, EstadoConta.DESACTIVADO},
    EstadoConta.BLOQUEADO: {EstadoConta.ACTIVO},
    EstadoConta.DESACTIVADO: {EstadoConta.ACTIVO},
}


class GestorUtilizadores(UserManager):
    """Permite criar o superutilizador com o comando createsuperuser."""

    def create_superuser(self, username, email=None, password=None, **extra):
        extra.setdefault("perfil", Perfil.ADMINISTRADOR)
        extra.setdefault("estado", EstadoConta.ACTIVO)
        return super().create_superuser(username, email, password, **extra)


class Utilizador(AbstractUser):
    """Utilizador da plataforma. O e-mail é usado para iniciar sessão."""

    email = models.EmailField("e-mail", unique=True)
    nome = models.CharField("nome completo", max_length=120)
    contacto = models.CharField("contacto telefónico", max_length=20, blank=True)
    perfil = models.CharField(max_length=20, choices=Perfil.choices, default=Perfil.INQUILINO)
    estado = models.CharField(max_length=20, choices=EstadoConta.choices, default=EstadoConta.ACTIVO)
    # Só para Proprietário/Agência: nome da agência, se existir
    nome_agencia = models.CharField("nome da agência", max_length=120, blank=True)

    objects = GestorUtilizadores()

    class Meta:
        verbose_name = "utilizador"
        verbose_name_plural = "utilizadores"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.get_perfil_display()})"

    @property
    def eh_administrador(self):
        return self.perfil == Perfil.ADMINISTRADOR

    @property
    def eh_proprietario(self):
        return self.perfil == Perfil.PROPRIETARIO

    @property
    def eh_inquilino(self):
        return self.perfil == Perfil.INQUILINO

    def mudar_estado(self, novo_estado):
        """Aplica uma transição do diagrama de estados ou lança erro."""
        if novo_estado not in TRANSICOES_CONTA.get(self.estado, set()):
            raise ValidationError(
                f"Não é possível passar a conta de «{self.get_estado_display()}» "
                f"para «{EstadoConta(novo_estado).label}»."
            )
        self.estado = novo_estado
        # Uma conta que não está activa não pode iniciar sessão
        self.is_active = novo_estado == EstadoConta.ACTIVO
        self.save(update_fields=["estado", "is_active"])


# --- Especializações do diagrama de classes (modelos proxy) -----------------

class _GestorPorPerfil(models.Manager):
    def __init__(self, perfil):
        super().__init__()
        self.perfil = perfil

    def get_queryset(self):
        return super().get_queryset().filter(perfil=self.perfil)


class InquilinoComprador(Utilizador):
    objects = _GestorPorPerfil(Perfil.INQUILINO)

    class Meta:
        proxy = True
        verbose_name = "inquilino/comprador"


class ProprietarioAgencia(Utilizador):
    objects = _GestorPorPerfil(Perfil.PROPRIETARIO)

    class Meta:
        proxy = True
        verbose_name = "proprietário/agência"


class Administrador(Utilizador):
    objects = _GestorPorPerfil(Perfil.ADMINISTRADOR)

    class Meta:
        proxy = True
        verbose_name = "administrador"
