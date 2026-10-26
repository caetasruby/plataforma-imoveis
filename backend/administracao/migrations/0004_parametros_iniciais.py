"""Cria os parâmetros do sistema com os valores por omissão (UC16)."""
from django.db import migrations


def criar_parametros(apps, schema_editor):
    from administracao.configuracao import PARAMETROS_POR_OMISSAO

    ParametroSistema = apps.get_model("administracao", "ParametroSistema")
    for p in PARAMETROS_POR_OMISSAO:
        ParametroSistema.objects.get_or_create(chave=p["chave"], defaults=p)


class Migration(migrations.Migration):
    dependencies = [("administracao", "0003_initial")]
    operations = [migrations.RunPython(criar_parametros, migrations.RunPython.noop)]
