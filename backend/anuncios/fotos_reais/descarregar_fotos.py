#!/usr/bin/env python3
"""
Descarrega fotografias REAIS de edifícios de Maputo, Matola e Beira do Wikimedia
Commons (só ficheiros com licença livre) e guarda, ao lado de cada uma, o autor,
a licença e a página de origem. Esses dados ficam em manifesto.json e em
CREDITOS_FOTOGRAFIAS.md (obrigatórios pelas licenças CC BY e CC BY-SA).

Uso (num computador com internet; só usa a biblioteca padrão do Python):
    python descarregar_fotos.py                 descarrega para esta pasta
    python descarregar_fotos.py --listar        só mostra os candidatos, sem descarregar
    python descarregar_fotos.py --por-categoria 6    número de fotografias por categoria

Depois de descarregar, ABRA a pasta, veja as fotografias e apague as que não
servirem (também pode apagar a linha correspondente no manifesto.json; o
carregamento dos dados de demonstração ignora ficheiros que já não existem).
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

PASTA = Path(__file__).resolve().parent
API = "https://commons.wikimedia.org/w/api.php"
# A Wikimedia exige que o programa se identifique
AGENTE = "KayaJustaLES/1.0 (projecto academico UJC; fotografias de demonstracao)"

# categoria de imóvel -> pesquisas no Commons (em inglês e português)
PESQUISAS = {
    "APARTAMENTO": ["Maputo apartment building", "Maputo residential building", "Sommerschield Maputo",
                    "Polana Maputo building", "Edifício Maputo prédio", "Matola apartment building",
                    "Beira Mozambique apartment building"],
    "MORADIA": ["Maputo house villa", "Maputo residence", "Matola house", "Beira Mozambique house",
                "Costa do Sol Maputo house"],
    "ESCRITORIO": ["Maputo office building", "Maputo skyscraper", "Maputo business tower",
                   "Avenida 25 de Setembro Maputo", "Baixa de Maputo building"],
    "PAISAGEM": ["Maputo Costa do Sol", "Maputo bay waterfront", "Maputo street"],
}
LICENCAS_ACEITES = re.compile(r"^(CC0|Public domain|PD|CC[ -]BY(-SA)?[ -]\d(\.\d)?)", re.I)
EXCLUIR = re.compile(r"map|mapa|logo|flag|bandeira|plan|diagram|coat of arms|stamp|postcard|poster|"
                     r"satellite|aerial|drone|demolition|ruin|cyclone|idai|protest|election|portrait", re.I)


def pedir_json(parametros):
    url = API + "?" + urllib.parse.urlencode(parametros)
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(pedido, timeout=40) as resposta:
        return json.load(resposta)


def descarregar(url, destino):
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(pedido, timeout=90) as resposta:
        destino.write_bytes(resposta.read())


def texto_simples(valor):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", valor or ""))).strip()


def candidatos(pesquisa):
    """Ficheiros JPEG largos, com licença livre, para uma pesquisa do Commons."""
    dados = pedir_json({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": pesquisa,
        "gsrnamespace": 6, "gsrlimit": 30, "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280,
    })
    for pagina in sorted(dados.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
        info = (pagina.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        licenca = meta.get("LicenseShortName", {}).get("value", "")
        titulo = pagina["title"]
        largura, altura = info.get("width", 0), info.get("height", 0)
        if (info.get("mime") != "image/jpeg" or largura < 1000 or altura < 600
                or not 1.25 <= largura / max(altura, 1) <= 2.2
                or not LICENCAS_ACEITES.match(licenca) or EXCLUIR.search(titulo)):
            continue
        yield {
            "id": pagina["pageid"], "titulo": titulo, "url": info.get("thumburl") or info["url"],
            "pagina": info.get("descriptionurl", ""), "licenca": licenca,
            "url_licenca": meta.get("LicenseUrl", {}).get("value", ""),
            "autor": texto_simples(meta.get("Artist", {}).get("value", "")) or "Autor não indicado",
        }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--listar", action="store_true", help="só mostra os candidatos")
    ap.add_argument("--por-categoria", type=int, default=6, help="fotografias por categoria (por omissão 6)")
    args = ap.parse_args()

    manifesto, vistos = [], set()
    for categoria, pesquisas in PESQUISAS.items():
        escolhidas = []
        for pesquisa in pesquisas:
            if len(escolhidas) >= args.por_categoria:
                break
            try:
                for c in candidatos(pesquisa):
                    if c["id"] in vistos:
                        continue
                    vistos.add(c["id"])
                    escolhidas.append(c)
                    if len(escolhidas) >= args.por_categoria:
                        break
            except Exception as erro:   # noqa: BLE001  (sem internet, limite de pedidos...)
                print(f"  Falhou a pesquisa «{pesquisa}»: {erro}", file=sys.stderr)
            time.sleep(1)
        print(f"{categoria}: {len(escolhidas)} fotografias")
        for n, c in enumerate(escolhidas, 1):
            ficheiro = f"{categoria.lower()}_{n:02d}.jpg"
            print(f"  {ficheiro}  {c['titulo']}  [{c['licenca']}]  {c['autor'][:40]}")
            if not args.listar:
                try:
                    descarregar(c["url"], PASTA / ficheiro)
                except Exception as erro:   # noqa: BLE001
                    print(f"    Falhou o descarregamento: {erro}", file=sys.stderr)
                    continue
                time.sleep(1)
            manifesto.append({"ficheiro": ficheiro, "categoria": categoria, **c})

    if args.listar:
        return 0
    if not manifesto:
        print("Nenhuma fotografia descarregada. Verifique a ligação à internet.", file=sys.stderr)
        return 1
    (PASTA / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    linhas = ["# Créditos das fotografias", "",
              "Fotografias de edifícios reais, do Wikimedia Commons, usadas nos anúncios de demonstração. "
              "Os anúncios, preços e anunciantes são fictícios.", "",
              "| Ficheiro | Título no Commons | Autor | Licença | Origem |", "|---|---|---|---|---|"]
    for m in manifesto:
        licenca = f"[{m['licenca']}]({m['url_licenca']})" if m["url_licenca"] else m["licenca"]
        linhas.append(f"| {m['ficheiro']} | {m['titulo'].replace('File:', '')} | {m['autor'].replace('|', '/')} | {licenca} | [página]({m['pagina']}) |")
    (PASTA / "CREDITOS_FOTOGRAFIAS.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\n{len(manifesto)} fotografias guardadas em {PASTA}. Reveja-as e apague as que não servirem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
