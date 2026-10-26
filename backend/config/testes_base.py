"""
Utilitários comuns aos testes automáticos (casos TC do plano de testes, secção 20.8).
Cada teste cria os seus próprios dados numa base de dados temporária.
"""
import io
import random
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from anuncios.models import Anuncio, EstadoAnuncio, ImagemImovel, Imovel, PontoInteresse
from contas.fabrica import FabricaUtilizador
from contas.models import Perfil
from ia.imagens import calcular_hash

PASSE = "Teste@2026"
PASTA_MEDIA = tempfile.mkdtemp(prefix="media_testes_")


def imagem_teste(nome="foto.jpg", cor=None, tamanho=(64, 48)):
    cor = cor or tuple(random.randint(0, 255) for _ in range(3))
    tampao = io.BytesIO()
    Image.new("RGB", tamanho, cor).save(tampao, "JPEG")
    return SimpleUploadedFile(nome, tampao.getvalue(), content_type="image/jpeg")


@override_settings(MEDIA_ROOT=PASTA_MEDIA)
class TesteBase(APITestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PASTA_MEDIA, ignore_errors=True)

    def setUp(self):
        self.admin = FabricaUtilizador.criar(Perfil.ADMINISTRADOR, "admin@t.mz", PASSE, "Admin Teste")
        self.dono = FabricaUtilizador.criar(Perfil.PROPRIETARIO, "dono@t.mz", PASSE, "Dono Teste")
        self.outro_dono = FabricaUtilizador.criar(Perfil.PROPRIETARIO, "outro@t.mz", PASSE, "Outro Dono")
        self.inquilino = FabricaUtilizador.criar(Perfil.INQUILINO, "inq@t.mz", PASSE, "Inquilino Teste")
        PontoInteresse.objects.create(nome="Escola X", categoria="ESCOLA", cidade="MAPUTO",
                                      latitude=-25.960, longitude=32.590)
        PontoInteresse.objects.create(nome="Mercado Y", categoria="MERCADO", cidade="MAPUTO",
                                      latitude=-25.970, longitude=32.572)

    def entrar(self, utilizador):
        self.client.force_authenticate(user=utilizador)

    def sair(self):
        self.client.force_authenticate(user=None)

    def criar_publicado(self, bairro="Polana Cimento", tipo="APARTAMENTO", finalidade="ARRENDAMENTO",
                        divisoes=2, area=100, preco=60000, cidade="MAPUTO", dono=None, **extra):
        """Cria um anúncio já publicado, sem passar pela API (dados de contexto)."""
        imovel = Imovel.objects.create(tipo=tipo, area=area, num_divisoes=divisoes, cidade=cidade,
                                       bairro=bairro, endereco="Av. Teste, 1",
                                       latitude=-25.965, longitude=32.595)
        anuncio = Anuncio.objects.create(
            imovel=imovel, anunciante=dono or self.dono, titulo=extra.get("titulo", f"{tipo} em {bairro}"),
            descricao="Descrição de teste com comprimento suficiente para validar.",
            preco=preco, finalidade=finalidade, estado=EstadoAnuncio.PUBLICADO,
            preco_justo=extra.get("preco_justo"))
        foto = imagem_teste()
        ImagemImovel.objects.create(anuncio=anuncio, ficheiro=foto, checksum_hash=calcular_hash(foto))
        return anuncio

    def criar_mercado(self, n=20):
        """Cria um conjunto de anúncios publicados coerentes, para treinar os modelos."""
        r = random.Random(1)
        for i in range(n):
            area = r.randint(60, 180)
            self.criar_publicado(bairro=r.choice(["Polana Cimento", "Sommerschield"]),
                                 divisoes=max(1, area // 45), area=area,
                                 preco=round(area * 1000 * r.uniform(0.9, 1.1), -3))

    def dados_formulario(self, **alteracoes):
        dados = {
            "tipo": "APARTAMENTO", "area": "110", "num_divisoes": "2", "cidade": "MAPUTO",
            "bairro": "Polana Cimento", "endereco": "Av. Julius Nyerere, 100",
            "latitude": "-25.965500", "longitude": "32.595200",
            "titulo": "Apartamento T2 luminoso na Polana",
            "descricao": "Apartamento com dois quartos, cozinha equipada e varanda ampla.",
            "preco": "110000", "finalidade": "ARRENDAMENTO",
            "imagens": [imagem_teste("a.jpg")],
        }
        dados.update(alteracoes)
        return dados
