from django.core.exceptions import ValidationError as ErroDjango
from rest_framework import serializers

from anuncios.serializers import AnuncioListaSerializer

from .models import AlertaFraude, HistoricoInteracao, ParametroSistema


class AlertaSerializer(serializers.ModelSerializer):
    tipo_nome = serializers.CharField(source="get_tipo_alerta_display", read_only=True)
    gravidade_nome = serializers.CharField(source="get_gravidade_display", read_only=True)
    estado_nome = serializers.CharField(source="get_estado_display", read_only=True)
    anuncio_titulo = serializers.CharField(source="anuncio.titulo", read_only=True)
    anuncio_estado = serializers.CharField(source="anuncio.get_estado_display", read_only=True)
    decidido_por_nome = serializers.CharField(source="decidido_por.nome", read_only=True,
                                              default=None)

    class Meta:
        model = AlertaFraude
        fields = ["id", "anuncio", "anuncio_titulo", "anuncio_estado", "tipo_alerta",
                  "tipo_nome", "pontuacao_risco", "justificacao", "gravidade", "gravidade_nome",
                  "estado", "estado_nome", "nota_decisao", "decidido_por_nome",
                  "data_criacao", "data_decisao"]


class AnuncioModeracaoSerializer(AnuncioListaSerializer):
    alertas = AlertaSerializer(many=True, read_only=True)
    anunciante_nome = serializers.CharField(source="anunciante.nome", read_only=True)

    class Meta(AnuncioListaSerializer.Meta):
        fields = AnuncioListaSerializer.Meta.fields + [
            "descricao", "pontuacao_risco", "preco_justo_min", "preco_justo_max",
            "alertas", "anunciante_nome"]


class RejeitarSerializer(serializers.Serializer):
    motivo = serializers.CharField(error_messages={"blank": "Indique o motivo da rejeição.",
                                                   "required": "Indique o motivo da rejeição."})

    def validate_motivo(self, valor):
        if len(valor.strip()) < 10:
            raise serializers.ValidationError("Explique o motivo em pelo menos 10 caracteres.")
        return valor.strip()


class ClassificarAlertaSerializer(serializers.Serializer):
    decisao = serializers.ChoiceField(
        choices=["EM_REVISAO", "CONFIRMADO", "FALSO_POSITIVO", "RESOLVIDO"],
        error_messages={"invalid_choice": "Escolha uma decisão válida."})
    nota = serializers.CharField(required=False, allow_blank=True, max_length=500)


class ParametroSerializer(serializers.ModelSerializer):
    actualizado_por_nome = serializers.CharField(source="actualizado_por.nome", read_only=True,
                                                 default=None)

    class Meta:
        model = ParametroSistema
        fields = ["id", "chave", "nome", "descricao", "valor", "tipo", "minimo", "maximo",
                  "ultima_actualizacao", "actualizado_por_nome"]
        read_only_fields = ["chave", "nome", "descricao", "tipo", "minimo", "maximo"]

    def validate_valor(self, valor):
        try:
            return self.instance.validar_valor(valor)
        except ErroDjango as erro:
            raise serializers.ValidationError(erro.messages)


class HistoricoSerializer(serializers.ModelSerializer):
    utilizador_nome = serializers.CharField(source="utilizador.nome", read_only=True,
                                            default="Sistema")
    tipo_nome = serializers.CharField(source="get_tipo_accao_display", read_only=True)

    class Meta:
        model = HistoricoInteracao
        fields = ["id", "utilizador_nome", "tipo_accao", "tipo_nome", "descricao",
                  "dados_contexto", "data_hora"]
