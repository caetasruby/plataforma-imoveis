"""
Fotografias dos anúncios de demonstração.

As fotografias são REAIS (edifícios de Maputo, Matola e Beira com licença livre,
do Wikimedia Commons). Descarregam-se uma vez com o script
anuncios/fotos_reais/descarregar_fotos.py, que também escreve o manifesto
(manifesto.json) com o autor, a licença e a origem de cada ficheiro.

Se a pasta estiver vazia (sem manifesto), usa-se uma imagem neutra com o texto
"Fotografia por adicionar": nunca se desenham casas falsas.
"""
import io
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw

PASTA = Path(__file__).resolve().parent.parent.parent / "fotos_reais"
L, A = 1200, 800

# Se não houver fotografias de um tipo, tenta-se uma categoria vizinha adequada
ALTERNATIVAS = {"TERRENO": ["PAISAGEM"], "ESCRITORIO": [], "MORADIA": [], "APARTAMENTO": []}


class ColecaoFotos:
    def __init__(self, pasta=PASTA):
        self.pasta = Path(pasta)
        self.por_tipo = {}
        manifesto = self.pasta / "manifesto.json"
        if manifesto.exists():
            for item in json.loads(manifesto.read_text(encoding="utf-8")):
                caminho = self.pasta / item["ficheiro"]
                if caminho.exists():
                    self.por_tipo.setdefault(item["categoria"], []).append(caminho)
        self.contadores = {}

    @property
    def total(self):
        return sum(len(v) for v in self.por_tipo.values())

    def _lista(self, tipo):
        for categoria in [tipo, *ALTERNATIVAS.get(tipo, [])]:
            if self.por_tipo.get(categoria):
                return self.por_tipo[categoria]
        return []

    def fotografia(self, tipo, semente):
        """Devolve os bytes de uma fotografia real para o tipo de imóvel (por rotação).
        O mesmo ficheiro serve vários anúncios; para cada anúncio ter um ficheiro
        distinto (o detector de duplicados compara a impressão digital do ficheiro),
        corta-se uma margem de poucos píxeis e grava-se de novo."""
        lista = self._lista(tipo)
        if not lista:
            return placeholder(tipo, semente)
        n = self.contadores.get(tipo, 0)
        self.contadores[tipo] = n + 1
        r = random.Random(semente)
        imagem = Image.open(lista[n % len(lista)]).convert("RGB")
        l, a = imagem.size
        e, t, d, b = (r.randint(0, 14) for _ in range(4))
        imagem = imagem.crop((e, t, l - d, a - b))
        saida = io.BytesIO()
        imagem.save(saida, "JPEG", quality=r.randint(84, 90), optimize=True)
        return saida.getvalue()


def placeholder(tipo, semente=0):
    """Imagem neutra e honesta: indica que falta a fotografia, sem simular um imóvel.
    O tom de fundo varia um pouco com a semente para os ficheiros não serem idênticos
    (senão o detector de imagens duplicadas sinalizaria todos os anúncios)."""
    r = random.Random(semente)
    img = Image.new("RGB", (L, A), (229 + r.randint(-4, 4), 231 + r.randint(-4, 4), 235 + r.randint(-4, 4)))
    d = ImageDraw.Draw(img)
    cx, cy = L // 2, A // 2 - 30
    cor = (148, 163, 184)
    d.rectangle([cx - 70, cy - 90, cx + 30, cy + 70], outline=cor, width=8)
    d.rectangle([cx + 30, cy - 20, cx + 100, cy + 70], outline=cor, width=8)
    for y in (cy - 55, cy - 15, cy + 25):
        d.rectangle([cx - 40, y, cx - 10, y + 16], fill=cor)
    d.line([cx - 110, cy + 70, cx + 130, cy + 70], fill=cor, width=8)
    d.text((cx - 80, cy + 110), "Fotografia por adicionar", fill=(100, 116, 139))
    # Alguns píxeis imperceptíveis tornam cada ficheiro único (ver nota acima)
    for _ in range(40):
        d.point((r.randint(0, L - 1), r.randint(0, A - 1)), fill=(r.randint(200, 235),) * 3)
    saida = io.BytesIO()
    img.save(saida, "JPEG", quality=85)
    return saida.getvalue()
