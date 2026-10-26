from django.contrib import admin

from .models import Anuncio, Favorito, ImagemImovel, Imovel, PontoInteresse

admin.site.register([Imovel, Favorito, PontoInteresse, ImagemImovel])


@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display = ("titulo", "finalidade", "preco", "estado", "pontuacao_risco")
    list_filter = ("estado", "finalidade")
