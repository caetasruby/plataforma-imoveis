"""
Testes de interface (ponta a ponta) com Playwright.
Percorrem os fluxos principais no navegador, como um utilizador real.

Uso:  python fluxos.py [endereço]     (por omissão http://127.0.0.1:3000)
Requer o sistema a correr com os dados de demonstração.
"""
import io
import sys
import time

from PIL import Image
from playwright.sync_api import expect, sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000"
PASSE = "Demo@2026"
TITULO = f"Apartamento T3 de teste n.º {int(time.time()) % 100000}"
resultados = []


def caso(nome):
    def decorador(funcao):
        def executar(pagina):
            inicio = time.time()
            try:
                funcao(pagina)
                resultados.append((nome, "Passou", f"{time.time() - inicio:.1f}s"))
            except Exception as erro:   # noqa: BLE001
                resultados.append((nome, "FALHOU", str(erro).splitlines()[0][:120]))
            finally:
                sair(pagina)   # cada caso começa sem sessão
        return executar
    return decorador


def entrar(p, email):
    p.goto(f"{BASE}/entrar")
    p.get_by_label("E-mail").fill(email)
    p.get_by_label("Palavra-passe").fill(PASSE)
    p.get_by_role("button", name="Entrar").click()
    p.wait_for_url(lambda url: "/entrar" not in url)


def sair(p):
    if p.url.startswith(BASE):
        p.evaluate("localStorage.clear()")


def fotografia():
    tampao = io.BytesIO()
    Image.new("RGB", (640, 480), (int(time.time()) % 255, 120, 90)).save(tampao, "JPEG")
    return {"name": "fachada.jpg", "mimeType": "image/jpeg", "buffer": tampao.getvalue()}


@caso("TC01/TC02 Pesquisa com filtros e sem resultados")
def pesquisa(p):
    p.goto(f"{BASE}/pesquisa?cidade=MAPUTO&finalidade=ARRENDAMENTO")
    expect(p.locator(".cartao-anuncio").first).to_be_visible()
    p.goto(f"{BASE}/pesquisa?cidade=BEIRA&tipo=TERRENO&finalidade=ARRENDAMENTO")
    expect(p.get_by_text("Sem resultados")).to_be_visible()
    p.get_by_role("button", name="Limpar filtros").last.click()
    expect(p.locator(".cartao-anuncio").first).to_be_visible()


@caso("TC12 Formulário recusa dados inválidos (validação no cliente)")
def formulario_invalido(p):
    entrar(p, "proprietario@imoveis.co.mz")
    p.goto(f"{BASE}/meus-anuncios/novo")
    p.get_by_label("Preço (MT)").fill("10")
    p.get_by_role("button", name="Publicar Anúncio").click()
    expect(p.get_by_role("alert").filter(has_text="Corrija")).to_be_visible()
    expect(p.get_by_text("Adicione pelo menos uma fotografia.").first).to_be_visible()
    expect(p.get_by_text("o preço deve estar entre").first).to_be_visible()
    assert "/novo" in p.url
    sair(p)


@caso("TC11 Publicar anúncio válido fica pendente de moderação")
def publicar(p):
    entrar(p, "proprietario@imoveis.co.mz")
    p.goto(f"{BASE}/meus-anuncios/novo")
    p.get_by_label("Área (m²)").fill("120")
    p.get_by_label("Número de divisões").fill("3")
    p.get_by_label("Bairro").fill("Sommerschield")
    p.get_by_label("Endereço").fill("Rua da Argélia, n.º 210")
    p.get_by_label("Preço (MT)").fill("115000")
    expect(p.get_by_text("Preço justo estimado:")).to_be_visible(timeout=8000)
    p.get_by_label("Título").fill(TITULO)
    p.get_by_label("Descrição").fill("Apartamento com três quartos, cozinha equipada, varanda e parqueamento.")
    p.locator("input[type=file]").set_input_files(fotografia())
    expect(p.locator(".miniatura")).to_have_count(1)
    p.get_by_role("button", name="Publicar Anúncio").click()
    p.wait_for_url(f"{BASE}/meus-anuncios")
    expect(p.get_by_text("pendente de moderação").first).to_be_visible()
    expect(p.get_by_text(TITULO)).to_be_visible()
    sair(p)


@caso("TC19 Administrador aprova e o anúncio fica público")
def aprovar(p):
    entrar(p, "admin@imoveis.co.mz")
    p.goto(f"{BASE}/admin/moderacao")
    cartao = p.locator("tbody tr").filter(has_text=TITULO)
    cartao.get_by_role("button", name="Aprovar").click()
    expect(p.get_by_text("O anunciante foi notificado")).to_be_visible()
    sair(p)
    p.goto(f"{BASE}/pesquisa?q={TITULO}")
    expect(p.get_by_text(TITULO)).to_be_visible()


@caso("TC20 Rejeitar exige motivo")
def rejeitar(p):
    entrar(p, "admin@imoveis.co.mz")
    p.goto(f"{BASE}/admin/moderacao")
    p.locator("tbody tr").first.get_by_role("button", name="Rejeitar").click()
    p.get_by_role("button", name="Rejeitar e notificar").click()
    expect(p.get_by_text("pelo menos 10 caracteres")).to_be_visible()
    p.get_by_role("button", name="Cancelar").click()
    sair(p)


@caso("TC05 Anúncio com risco mostra o alerta ao inquilino")
def alerta_visivel(p):
    # Procura pela API um anúncio publicado com alerta visível e abre-o na interface
    lista = p.request.get(f"{BASE}/api/anuncios/?tamanho=100&ordenar=-preco").json()["results"]
    com_risco = next(a for a in lista if a["tem_alerta"])
    p.goto(f"{BASE}/anuncios/{com_risco['id']}")
    resumo = p.locator("details.alerta-risco summary")
    expect(resumo).to_contain_text("Risco")
    resumo.click()
    expect(p.locator("details.alerta-risco li").first).to_be_visible()


@caso("TC42 Inquilino guarda e retira favorito")
def favorito(p):
    entrar(p, "paulo@imoveis.co.mz")
    p.goto(f"{BASE}/pesquisa")
    p.locator(".botao-favorito").first.click()
    expect(p.get_by_text("Guardado nos favoritos.")).to_be_visible()
    p.goto(f"{BASE}/favoritos")
    expect(p.locator(".cartao-anuncio")).to_have_count(1)
    p.locator(".botao-favorito").first.click()
    expect(p.get_by_text("Ainda não guardou imóveis")).to_be_visible()
    sair(p)


@caso("TC10 Assistente responde e segue o tema")
def assistente(p):
    p.goto(f"{BASE}/assistente")
    p.get_by_role("button", name="Quanto se paga de SISA?").click()
    expect(p.locator(".mensagem.assistente").last).to_contain_text("2%")
    p.get_by_label("A sua pergunta").fill("E quem paga?")
    p.get_by_role("button", name="Enviar").click()
    expect(p.locator(".mensagem.assistente").last).to_contain_text("comprador")


@caso("TC27 Inquilino não acede ao painel de administração")
def acesso_recusado(p):
    entrar(p, "inquilino@imoveis.co.mz")
    p.goto(f"{BASE}/admin")
    expect(p.get_by_text("Acesso reservado")).to_be_visible()
    sair(p)


@caso("TC31 Sem deslocamento horizontal a 320 píxeis")
def largura_320(p):
    p.set_viewport_size({"width": 320, "height": 800})
    for rota in ["/", "/pesquisa", "/anuncios/2", "/entrar", "/registo", "/assistente"]:
        p.goto(BASE + rota)
        p.wait_for_timeout(600)
        largura = p.evaluate("document.documentElement.scrollWidth")
        assert largura <= 320, f"{rota}: largura {largura}px"
    p.set_viewport_size({"width": 1280, "height": 900})


@caso("UC14/UC15 Registo, sessão e saída")
def registo(p):
    p.goto(f"{BASE}/registo")
    p.get_by_label("Nome completo").fill("Teste")
    p.get_by_role("button", name="Criar conta").click()
    expect(p.get_by_text("Indique o nome e o apelido.").first).to_be_visible()
    p.get_by_label("Nome completo").fill("Rosa Matsinhe")
    p.get_by_label("E-mail").fill(f"rosa{int(time.time())}@exemplo.co.mz")
    p.get_by_label("Palavra-passe", exact=True).fill("Casa@Beira26")
    p.get_by_label("Confirmar palavra-passe").fill("Casa@Beira26")
    p.get_by_role("button", name="Criar conta").click()
    expect(p.get_by_text("Conta criada")).to_be_visible()
    p.get_by_role("button", name="Rosa").click()
    p.get_by_role("menuitem", name="Terminar sessão").click()
    expect(p.get_by_role("link", name="Entrar")).to_be_visible()


if __name__ == "__main__":
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1280, "height": 900})
        pagina.set_default_timeout(10000)
        for teste in [pesquisa, formulario_invalido, publicar, aprovar, rejeitar, alerta_visivel,
                      favorito, assistente, acesso_recusado, largura_320, registo]:
            teste(pagina)
        navegador.close()
    for nome, estado, detalhe in resultados:
        print(f"{estado:7} {nome}  ({detalhe})")
    sys.exit(0 if all(e == "Passou" for _, e, _ in resultados) else 1)
