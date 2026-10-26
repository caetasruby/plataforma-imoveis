"""
Modelos dos módulos Gestão de Anúncios e Pesquisa e Filtros.
Seguem o diagrama de classes da Fase II: Imovel, Anuncio e ImagemImovel.
Acrescentam-se Favorito (UC18) e PontoInteresse (distâncias do UC07, CT04).
"""
import math

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Cidade(models.TextChoices):
    MAPUTO = "MAPUTO", "Maputo"
    MATOLA = "MATOLA", "Matola"
    BEIRA = "BEIRA", "Beira"


class TipoImovel(models.TextChoices):
    APARTAMENTO = "APARTAMENTO", "Apartamento"
    MORADIA = "MORADIA", "Moradia"
    ESCRITORIO = "ESCRITORIO", "Escritório"
    TERRENO = "TERRENO", "Terreno"


class Finalidade(models.TextChoices):
    ARRENDAMENTO = "ARRENDAMENTO", "Arrendamento"
    VENDA = "VENDA", "Venda"


class EstadoAnuncio(models.TextChoices):
    """Estados do diagrama de estados do Anúncio (secção 13)."""
    SUBMETIDO = "SUBMETIDO", "Submetido"
    EM_ANALISE = "EM_ANALISE", "Em análise de IA"
    PENDENTE = "PENDENTE", "Pendente de moderação"
    PUBLICADO = "PUBLICADO", "Publicado"
    REJEITADO = "REJEITADO", "Rejeitado"
    REMOVIDO = "REMOVIDO", "Removido"


E = EstadoAnuncio
TRANSICOES_ANUNCIO = {
    E.SUBMETIDO: {E.EM_ANALISE},
    E.EM_ANALISE: {E.PENDENTE},
    E.PENDENTE: {E.PUBLICADO, E.REJEITADO, E.REMOVIDO, E.EM_ANALISE},
    E.PUBLICADO: {E.EM_ANALISE, E.REMOVIDO},   # editar volta à análise
    E.REJEITADO: {E.EM_ANALISE, E.REMOVIDO},   # ressubmeter volta à análise
    E.REMOVIDO: set(),
}

# Limites usados na validação (servidor e cliente usam os mesmos valores)
LIMITES_PRECO = {
    Finalidade.ARRENDAMENTO: (1_000, 2_000_000),        # MZN por mês
    Finalidade.VENDA: (100_000, 500_000_000),            # MZN
}


class Imovel(models.Model):
    tipo = models.CharField(max_length=20, choices=TipoImovel.choices)
    area = models.DecimalField("área (m²)", max_digits=10, decimal_places=2,
                               validators=[MinValueValidator(10), MaxValueValidator(100_000)])
    num_divisoes = models.PositiveSmallIntegerField(
        "número de divisões (quartos)", validators=[MaxValueValidator(30)])
    cidade = models.CharField(max_length=20, choices=Cidade.choices)
    bairro = models.CharField(max_length=80)
    endereco = models.CharField("endereço", max_length=200)
    # Coordenadas dentro dos limites de Moçambique
    latitude = models.DecimalField(max_digits=9, decimal_places=6,
                                   validators=[MinValueValidator(-27), MaxValueValidator(-10)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6,
                                    validators=[MinValueValidator(30), MaxValueValidator(41)])

    class Meta:
        verbose_name = "imóvel"
        verbose_name_plural = "imóveis"

    def __str__(self):
        return f"{self.get_tipo_display()} T{self.num_divisoes}, {self.bairro}, {self.get_cidade_display()}"

    def calcular_distancias_poi(self):
        """Método do diagrama de classes (CT04): distância em km ao ponto de
        interesse mais próximo de cada categoria, na mesma cidade."""
        resultado = {}
        for poi in PontoInteresse.objects.filter(cidade=self.cidade):
            km = distancia_km(self.latitude, self.longitude, poi.latitude, poi.longitude)
            actual = resultado.get(poi.categoria)
            if actual is None or km < actual["distancia_km"]:
                resultado[poi.categoria] = {
                    "categoria": poi.get_categoria_display(),
                    "nome": poi.nome,
                    "distancia_km": round(km, 2),
                    "latitude": float(poi.latitude),
                    "longitude": float(poi.longitude),
                }
        return list(resultado.values())


def distancia_km(lat1, lon1, lat2, lon2):
    """Fórmula de Haversine: distância em linha recta entre duas coordenadas."""
    raio_terra = 6371
    lat1, lon1, lat2, lon2 = map(lambda v: math.radians(float(v)), (lat1, lon1, lat2, lon2))
    a = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * raio_terra * math.asin(math.sqrt(a))


class Anuncio(models.Model):
    imovel = models.ForeignKey(Imovel, on_delete=models.CASCADE, related_name="anuncios")
    anunciante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="anuncios")
    titulo = models.CharField("título", max_length=120)
    descricao = models.TextField("descrição")
    preco = models.DecimalField("preço (MZN)", max_digits=14, decimal_places=2)
    finalidade = models.CharField(max_length=20, choices=Finalidade.choices)
    estado = models.CharField(max_length=20, choices=EstadoAnuncio.choices,
                              default=EstadoAnuncio.SUBMETIDO)
    motivo_rejeicao = models.TextField(blank=True)

    # Resultados dos módulos de IA (CT01 e CT02)
    preco_justo = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    preco_justo_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    preco_justo_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    pontuacao_risco = models.FloatField(default=0)

    visualizacoes = models.PositiveIntegerField(default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_actualizacao = models.DateTimeField(auto_now=True)
    data_publicacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "anúncio"
        ordering = ["-data_criacao"]

    def __str__(self):
        return self.titulo

    # --- Regras de negócio ---------------------------------------------------

    def mudar_estado(self, novo_estado):
        """Aplica uma transição do diagrama de estados ou lança erro."""
        if novo_estado not in TRANSICOES_ANUNCIO[self.estado]:
            raise ValidationError(
                f"Não é possível passar o anúncio de «{self.get_estado_display()}» "
                f"para «{EstadoAnuncio(novo_estado).label}»."
            )
        self.estado = novo_estado
        if novo_estado == EstadoAnuncio.PUBLICADO:
            self.data_publicacao = timezone.now()
            self.motivo_rejeicao = ""
        self.save()

    @property
    def diferenca_percentual(self):
        """Diferença entre o preço pedido e o preço justo (TC04)."""
        if not self.preco_justo:
            return None
        return round(float((self.preco - self.preco_justo) / self.preco_justo * 100), 1)

    def validar_anuncio(self):
        """Método do diagrama de classes: confirma as regras que não dependem
        de um só campo (o preço depende da finalidade)."""
        minimo, maximo = LIMITES_PRECO[self.finalidade]
        if not (minimo <= self.preco <= maximo):
            raise ValidationError({"preco": (
                f"Para {self.get_finalidade_display().lower()} o preço deve estar entre "
                f"{minimo:,} e {maximo:,} MT.".replace(",", " "))})


class ImagemImovel(models.Model):
    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name="imagens")
    ficheiro = models.ImageField(upload_to="anuncios/%Y/%m/")
    checksum_hash = models.CharField(max_length=64, db_index=True)
    eh_duplicada = models.BooleanField(default=False)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "imagem do imóvel"
        verbose_name_plural = "imagens do imóvel"
        ordering = ["ordem", "id"]


class Favorito(models.Model):
    """UC18 Guardar imóveis favoritos."""
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name="favoritos")
    anuncio = models.ForeignKey(Anuncio, on_delete=models.CASCADE, related_name="favoritos")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("utilizador", "anuncio")
        ordering = ["-criado_em"]


class CategoriaPOI(models.TextChoices):
    ESCOLA = "ESCOLA", "Escola"
    MERCADO = "MERCADO", "Mercado"
    TRANSPORTE = "TRANSPORTE", "Transporte"
    SAUDE = "SAUDE", "Saúde"


class PontoInteresse(models.Model):
    """Pontos de interesse usados no cálculo de distâncias (UC07)."""
    nome = models.CharField(max_length=120)
    categoria = models.CharField(max_length=20, choices=CategoriaPOI.choices)
    cidade = models.CharField(max_length=20, choices=Cidade.choices)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        verbose_name = "ponto de interesse"
        verbose_name_plural = "pontos de interesse"

    def __str__(self):
        return self.nome
