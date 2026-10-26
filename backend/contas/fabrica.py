"""
PADRÃO DE DESENHO: FACTORY (Fábrica)

Problema: criar um utilizador exige passos diferentes conforme o perfil
(classe proxy correcta, permissões do Django, valores por omissão). Se essa
lógica estivesse espalhada pelas vistas de registo, pelo comando de dados de
demonstração e pelos testes, qualquer mudança teria de ser feita em vários
sítios.

Solução: uma única classe, FabricaUtilizador, recebe o perfil e devolve o
objecto já configurado. Quem chama não precisa de saber os pormenores.
"""
from django.db import transaction

from .models import (
    Administrador,
    EstadoConta,
    InquilinoComprador,
    Perfil,
    ProprietarioAgencia,
)


class FabricaUtilizador:
    # Correspondência entre o perfil e a classe do diagrama de classes
    CLASSES = {
        Perfil.INQUILINO: InquilinoComprador,
        Perfil.PROPRIETARIO: ProprietarioAgencia,
        Perfil.ADMINISTRADOR: Administrador,
    }

    @classmethod
    @transaction.atomic
    def criar(cls, perfil, email, palavra_passe, nome, **outros_dados):
        """Cria e devolve um utilizador do perfil indicado."""
        if perfil not in cls.CLASSES:
            raise ValueError(f"Perfil desconhecido: {perfil}")

        classe = cls.CLASSES[perfil]
        utilizador = classe(
            username=email.lower(),       # o Django exige username; usamos o e-mail
            email=email.lower(),
            nome=nome,
            perfil=perfil,
            estado=EstadoConta.ACTIVO,
            **outros_dados,
        )
        # Só o administrador pode entrar no painel interno do Django
        if perfil == Perfil.ADMINISTRADOR:
            utilizador.is_staff = True
        # Só o proprietário/agência usa o campo nome_agencia
        if perfil != Perfil.PROPRIETARIO:
            utilizador.nome_agencia = ""

        utilizador.set_password(palavra_passe)   # guarda a palavra-passe cifrada
        utilizador.save()
        return utilizador
