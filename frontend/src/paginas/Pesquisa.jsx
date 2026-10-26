// Ecrã "Início" do Inquilino/Comprador e UC04 Pesquisar imóveis: filtros laterais,
// ordenação e paginação. Os filtros ficam no endereço (URL), por isso a pesquisa pode ser partilhada.
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import CartaoAnuncio from "../componentes/CartaoAnuncio";
import { Erro, EsqueletoCartoes, Vazio } from "../componentes/Estados";
import Icone from "../componentes/Icone";
import Paginacao from "../componentes/Paginacao";
import usarDados from "../componentes/usarDados";
import { useSessao } from "../contexto/Sessao";
import { CIDADES, FINALIDADES, TIPOS } from "../dados/opcoes";

const FILTROS = ["finalidade", "cidade", "tipo", "preco_min", "preco_max", "divisoes_min", "q", "apenas_preco_justo"];

export default function Pesquisa() {
  const { utilizador } = useSessao();
  const [url, setUrl] = useSearchParams();
  const [filtrosAbertos, setFiltrosAbertos] = useState(false);
  const parametros = Object.fromEntries(url.entries());
  const pagina = Number(parametros.page || 1);
  const chave = url.toString();

  const { dados, setDados, aCarregar, erro, recarregar } = usarDados(() => api.get("/anuncios/", parametros), [chave]);

  // Formulário local; só é aplicado ao carregar em "Pesquisar"
  const [f, setF] = useState(() => Object.fromEntries(FILTROS.map((k) => [k, parametros[k] || ""])));
  const mudar = (e) => setF({ ...f, [e.target.name]: e.target.type === "checkbox" ? (e.target.checked ? "1" : "") : e.target.value });
  const erroPreco = f.preco_min && f.preco_max && Number(f.preco_min) > Number(f.preco_max)
    ? "O preço mínimo não pode ser maior do que o máximo." : null;

  function aplicar(e) {
    e?.preventDefault();
    if (erroPreco) return;
    const novo = Object.fromEntries(Object.entries(f).filter(([, v]) => v !== ""));
    if (parametros.ordenar) novo.ordenar = parametros.ordenar;
    setUrl(novo);
    setFiltrosAbertos(false);
  }
  function limpar() {
    setF(Object.fromEntries(FILTROS.map((k) => [k, ""])));
    setUrl({});
  }
  const definir = (chaveP, valor) => {
    const novo = { ...parametros, [chaveP]: valor };
    if (chaveP !== "page") delete novo.page;
    setUrl(novo);
  };
  const activos = FILTROS.filter((k) => parametros[k]).length;

  function mudarFavorito(id, valor) {
    setDados((d) => ({ ...d, results: d.results.map((a) => (a.id === id ? { ...a, favorito: valor } : a)) }));
  }

  const total = dados?.count ?? 0;

  return (
    <div className="conteudo">
      {!utilizador && (
        <section className="faixa-boas-vindas" aria-label="Apresentação">
          <div>
            <h2>Arrende ou compre com confiança, ao preço certo.</h2>
            <p>Cada anúncio mostra o preço justo estimado por inteligência artificial e os alertas de fraude, para decidir com dados.</p>
          </div>
          <Link to="/registo" className="botao">Criar conta gratuita</Link>
        </section>
      )}

      <div className="layout-pesquisa">
        <aside className={`cartao filtros ${filtrosAbertos ? "aberto" : ""}`} aria-label="Filtros">
          <form className="cartao-corpo" onSubmit={aplicar}>
            <h2>Filtros</h2>
            <div className="campo">
              <span className="rotulo">Pretende</span>
              <div className="escolhas escolhas-grelha" role="radiogroup" aria-label="Pretende">
                {[{ valor: "", nome: "Tudo" }, ...FINALIDADES].map((o) => (
                  <label key={o.valor} className="escolha">
                    <input type="radio" name="finalidade" value={o.valor} checked={f.finalidade === o.valor} onChange={mudar} />
                    <span>{o.nome}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="campo">
              <label htmlFor="cidade">Cidade</label>
              <select id="cidade" name="cidade" value={f.cidade} onChange={mudar}>
                <option value="">Todas</option>
                {CIDADES.map((o) => <option key={o.valor} value={o.valor}>{o.nome}</option>)}
              </select>
            </div>
            <div className="campo">
              <label htmlFor="q">Localização (bairro)</label>
              <input id="q" name="q" value={f.q} onChange={mudar} placeholder="ex.: Sommerschield" />
            </div>
            <div className="campo">
              <label htmlFor="tipo">Tipo de imóvel</label>
              <select id="tipo" name="tipo" value={f.tipo} onChange={mudar}>
                <option value="">Todos</option>
                {TIPOS.map((o) => <option key={o.valor} value={o.valor}>{o.nome}</option>)}
              </select>
            </div>
            <div className="campo">
              <span className="rotulo">Preço mínimo / máximo (MT)</span>
              <div className="linha" style={{ flexWrap: "nowrap" }}>
                <input name="preco_min" type="number" min="0" inputMode="numeric" value={f.preco_min} onChange={mudar} placeholder="Mínimo" aria-label="Preço mínimo" aria-invalid={erroPreco ? "true" : undefined} />
                <input name="preco_max" type="number" min="0" inputMode="numeric" value={f.preco_max} onChange={mudar} placeholder="Máximo" aria-label="Preço máximo" aria-invalid={erroPreco ? "true" : undefined} />
              </div>
              {erroPreco && <span className="erro-campo" role="alert">{erroPreco}</span>}
            </div>
            <div className="campo">
              <label htmlFor="divisoes_min">Número de divisões</label>
              <select id="divisoes_min" name="divisoes_min" value={f.divisoes_min} onChange={mudar}>
                <option value="">Qualquer</option>
                {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>T{n} ou mais</option>)}
              </select>
            </div>
            <label className="caixa-opcao">
              <input type="checkbox" name="apenas_preco_justo" checked={f.apenas_preco_justo === "1"} onChange={mudar} />
              Apenas com preço justo
            </label>
            <button type="submit" className="botao botao-primario botao-largo" disabled={!!erroPreco}>Pesquisar</button>
            <button type="button" className="botao botao-texto botao-largo" onClick={limpar}>Limpar filtros</button>
          </form>
        </aside>

        <section aria-label="Resultados">
          <div className="cabecalho-pagina" style={{ marginBottom: 20 }}>
            <h1 style={{ fontSize: 18 }} aria-live="polite">
              {aCarregar ? "A procurar..." : `Resultados (${total} ${total === 1 ? "imóvel" : "imóveis"})`}
            </h1>
            <div className="linha">
              <button className="botao botao-secundario botao-pequeno alternar-filtros" onClick={() => setFiltrosAbertos(!filtrosAbertos)} aria-expanded={filtrosAbertos}>
                <Icone nome="filtro" /> Filtros {activos > 0 && <span className="contador">{activos}</span>}
              </button>
              <select aria-label="Ordenar por" value={parametros.ordenar || "relevancia"} onChange={(e) => definir("ordenar", e.target.value)} style={{ width: "auto", fontWeight: 600, fontSize: 14 }}>
                <option value="relevancia">Ordenar: Relevância</option>
                <option value="preco">Ordenar: Preço mais baixo</option>
                <option value="-preco">Ordenar: Preço mais alto</option>
                <option value="data">Ordenar: Mais recentes</option>
              </select>
            </div>
          </div>
          <Erro erro={erro} tentar={recarregar} />
          {aCarregar ? <EsqueletoCartoes /> : total === 0 ? (
            // TC02: mensagem de ausência de resultados e sugestão
            <Vazio icone="pesquisa" titulo="Sem resultados"
                   texto="Nenhum imóvel corresponde a todos os filtros. Experimente retirar alguns filtros ou alargar o intervalo de preço.">
              <button className="botao botao-secundario" onClick={limpar}>Limpar filtros</button>
            </Vazio>
          ) : (
            <>
              <div className="grelha-cartoes" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 270px), 1fr))" }}>
                {dados?.results.map((a, i) => <CartaoAnuncio key={a.id} anuncio={a} indice={i} aoMudarFavorito={mudarFavorito} />)}
              </div>
              <Paginacao pagina={pagina} total={total} aoMudar={(p) => { definir("page", p); window.scrollTo(0, 0); }} />
            </>
          )}
        </section>
      </div>
    </div>
  );
}
