"""
Serializers dos anúncios. A validação do lado do servidor está aqui
(segunda camada; a primeira está no formulário do React).
"""
from django.conf import settings
from django.core.exceptions import ValidationError as ErroDjango
from rest_framework import serializers

from administracao.models import EstadoAlerta

from .models import (
    LIMITES_PRECO,
    Anuncio,
    Cidade,
    Favorito,
    Finalidade,
    ImagemImovel,
    Imovel,
    TipoImovel,
    distancia_km,
)

# Centro aproximado de cada cidade e raio máximo aceite (km)
CENTRO_CIDADE = {
    Cidade.MAPUTO: (-25.9692, 32.5732, 25),
    Cidade.MATOLA: (-25.9622, 32.4589, 25),
    Cidade.BEIRA: (-19.8436, 34.8389, 25),
}
FORMATOS_IMAGEM = {"JPEG", "PNG", "WEBP"}


class ImagemSerializer(serializers.ModelSerializer):
    # Caminho relativo (/media/...): funciona atrás de qualquer servidor ou proxy
    ficheiro = serializers.SerializerMethodField()

    def get_ficheiro(self, obj):
        return obj.ficheiro.url

    class Meta:
        model = ImagemImovel
        fields = ["id", "ficheiro", "eh_duplicada"]


class ImovelSerializer(serializers.ModelSerializer):
    tipo_nome = serializers.CharField(source="get_tipo_display", read_only=True)
    cidade_nome = serializers.CharField(source="get_cidade_display", read_only=True)

    class Meta:
        model = Imovel
        fields = ["tipo", "tipo_nome", "area", "num_divisoes", "cidade", "cidade_nome",
                  "bairro", "endereco", "latitude", "longitude"]


def alertas_visiveis(anuncio):
    """UC06: alertas mostrados ao inquilino (os falsos positivos não aparecem)."""
    return [a for a in anuncio.alertas.all() if a.estado != EstadoAlerta.FALSO_POSITIVO]


class AnuncioListaSerializer(serializers.ModelSerializer):
    imovel = ImovelSerializer(read_only=True)
    finalidade_nome = serializers.CharField(source="get_finalidade_display", read_only=True)
    estado_nome = serializers.CharField(source="get_estado_display", read_only=True)
    capa = serializers.SerializerMethodField()
    tem_alerta = serializers.SerializerMethodField()
    favorito = serializers.SerializerMethodField()
    diferenca_percentual = serializers.FloatField(read_only=True)

    class Meta:
        model = Anuncio
        fields = ["id", "titulo", "preco", "finalidade", "finalidade_nome", "estado",
                  "estado_nome", "imovel", "capa", "preco_justo", "diferenca_percentual",
                  "tem_alerta", "favorito", "data_publicacao", "data_criacao", "visualizacoes",
                  "motivo_rejeicao"]

    def get_capa(self, obj):
        primeira = next(iter(obj.imagens.all()), None)
        return primeira.ficheiro.url if primeira else None

    def get_tem_alerta(self, obj):
        return bool(alertas_visiveis(obj))

    def get_favorito(self, obj):
        ids = self.context.get("favoritos")
        return obj.id in ids if ids is not None else False


class AlertaPublicoSerializer(serializers.Serializer):
    tipo = serializers.CharField(source="get_tipo_alerta_display")
    gravidade = serializers.CharField()
    gravidade_nome = serializers.CharField(source="get_gravidade_display")
    pontuacao_risco = serializers.FloatField()
    justificacao = serializers.CharField()


class AnuncioDetalheSerializer(AnuncioListaSerializer):
    imagens = ImagemSerializer(many=True, read_only=True)
    alertas = serializers.SerializerMethodField()
    anunciante = serializers.SerializerMethodField()

    class Meta(AnuncioListaSerializer.Meta):
        fields = AnuncioListaSerializer.Meta.fields + [
            "descricao", "imagens", "preco_justo_min", "preco_justo_max", "pontuacao_risco",
            "alertas", "anunciante", "data_actualizacao"]

    def get_alertas(self, obj):
        return AlertaPublicoSerializer(alertas_visiveis(obj), many=True).data

    def get_anunciante(self, obj):
        a = obj.anunciante
        return {"nome": a.nome, "agencia": a.nome_agencia, "contacto": a.contacto,
                "email": a.email}


class AnuncioEscritaSerializer(serializers.Serializer):
    """UC01 Publicar e UC02 Editar. Recebe os dados do imóvel e do anúncio
    num só formulário (multipart, por causa das fotografias)."""
    # Dados do imóvel
    tipo = serializers.ChoiceField(choices=TipoImovel.choices, error_messages={
        "invalid_choice": "Escolha o tipo de imóvel."})
    area = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=10,
                                    max_value=100_000, error_messages={
        "min_value": "A área mínima é 10 m².", "max_value": "A área máxima é 100 000 m².",
        "invalid": "Indique a área em m²."})
    num_divisoes = serializers.IntegerField(min_value=0, max_value=30, error_messages={
        "max_value": "No máximo 30 divisões.", "invalid": "Indique um número inteiro."})
    cidade = serializers.ChoiceField(choices=Cidade.choices, error_messages={
        "invalid_choice": "Escolha a cidade."})
    bairro = serializers.CharField(max_length=80, error_messages={"blank": "Indique o bairro."})
    endereco = serializers.CharField(max_length=200, error_messages={
        "blank": "Indique o endereço (avenida ou rua e número)."})
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    # Dados do anúncio
    titulo = serializers.CharField(max_length=120, error_messages={"blank": "Indique um título."})
    descricao = serializers.CharField(error_messages={"blank": "Descreva o imóvel."})
    preco = serializers.DecimalField(max_digits=14, decimal_places=2, error_messages={
        "invalid": "Indique o preço em meticais."})
    finalidade = serializers.ChoiceField(choices=Finalidade.choices, error_messages={
        "invalid_choice": "Escolha arrendamento ou venda."})
    # Fotografias novas e fotografias a retirar (na edição)
    imagens = serializers.ListField(child=serializers.ImageField(), required=False,
                                    error_messages={"invalid": "Ficheiro de imagem inválido."})
    remover_imagens = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate_titulo(self, valor):
        valor = valor.strip()
        if len(valor) < 10:
            raise serializers.ValidationError("O título deve ter pelo menos 10 caracteres.")
        return valor

    def validate_descricao(self, valor):
        valor = valor.strip()
        if len(valor) < 30:
            raise serializers.ValidationError("A descrição deve ter pelo menos 30 caracteres.")
        return valor

    def validate_imagens(self, ficheiros):
        for f in ficheiros:
            if f.size > settings.TAMANHO_MAXIMO_IMAGEM:
                raise serializers.ValidationError(f"«{f.name}» ultrapassa 5 MB.")
            formato = getattr(getattr(f, "image", None), "format", None)
            if formato and formato.upper() not in FORMATOS_IMAGEM:
                raise serializers.ValidationError(f"«{f.name}»: use JPEG, PNG ou WEBP.")
        return ficheiros

    def validate(self, dados):
        erros = {}
        # Divisões: só o terreno pode ter 0
        if dados["tipo"] != TipoImovel.TERRENO and dados["num_divisoes"] < 1:
            erros["num_divisoes"] = "Indique pelo menos 1 divisão."
        # Preço dentro dos limites da finalidade
        minimo, maximo = LIMITES_PRECO[dados["finalidade"]]
        if not (minimo <= dados["preco"] <= maximo):
            erros["preco"] = (f"Para {Finalidade(dados['finalidade']).label.lower()} o preço deve "
                              f"estar entre {minimo:,} e {maximo:,} MT.".replace(",", " "))
        # Coordenadas próximas da cidade escolhida
        lat, lon, raio = CENTRO_CIDADE[dados["cidade"]]
        if distancia_km(dados["latitude"], dados["longitude"], lat, lon) > raio:
            erros["latitude"] = (f"A localização marcada no mapa não fica em "
                                 f"{Cidade(dados['cidade']).label}.")
        # Fotografias: pelo menos 1 e no máximo 8 no total
        existentes = self.instance.imagens.count() if self.instance else 0
        a_remover = len(dados.get("remover_imagens", []))
        total = existentes - a_remover + len(dados.get("imagens", []))
        if total < 1:
            erros["imagens"] = "Adicione pelo menos uma fotografia."
        elif total > settings.MAXIMO_IMAGENS_POR_ANUNCIO:
            erros["imagens"] = f"No máximo {settings.MAXIMO_IMAGENS_POR_ANUNCIO} fotografias."
        if erros:
            raise serializers.ValidationError(erros)
        return dados


class FavoritoSerializer(serializers.ModelSerializer):
    anuncio = AnuncioListaSerializer(read_only=True)

    class Meta:
        model = Favorito
        fields = ["id", "anuncio", "criado_em"]


def erro_django_para_drf(erro: ErroDjango):
    """Converte um erro de validação do modelo num erro da API."""
    if hasattr(erro, "message_dict"):
        return serializers.ValidationError(erro.message_dict)
    return serializers.ValidationError({"detail": erro.messages})
