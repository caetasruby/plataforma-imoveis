// UC02 Editar e UC03 Remover anúncios (ecrã "Os Meus Anúncios" do documento)
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import Confirmar from "../componentes/Confirmar";
import { Erro, EsqueletoLinhas, Vazio } from "../componentes/Estados";
import Icone from "../componentes/Icone";
import usarDados from "../componentes/usarDados";
import { useAvisos } from "../contexto/Avisos";
import { meticais, sufixoPreco, tipologia } from "../formato";

const SELO_ESTADO = { PUBLICADO: "selo-ok", PENDENTE: "selo-aviso", EM_ANALISE: "selo-info", REJEITADO: "selo-perigo", SUBMETIDO: "selo-neutro" };
const RESUMOS = [
  { estado: "PUBLICADO", nome: "Publicados", cor: "var(--ok)" },
  { estado: "PENDENTE", nome: "Pendentes de moderação", cor: "var(--ambar)" },
  { estado: "REJEITADO", nome: "Rejeitados", cor: "var(--perigo)" },
];

export default function MeusAnuncios() {
  const avisar = useAvisos();
  const { dados, setDados, aCarregar, erro, recarregar } = usarDados(() => api.get("/meus-anuncios/"), []);
  const [aRemover, setARemover] = useState(null);
  const [filtro, setFiltro] = useState("");

  async function remover() {
    const alvo = aRemover;
    setARemover(null);
    try {
      await api.delete(`/meus-anuncios/${alvo.id}/`);
      setDados((l) => l.filter((a) => a.id !== alvo.id));
      avisar("Anúncio removido. Já não aparece na pesquisa.");
    } catch (e) { avisar(e.message, "erro"); }
  }

  const contagem = (estado) => (dados || []).filter((a) => a.estado === estado).length;
  const lista = (dados || []).filter((a) => !filtro || a.estado === filtro);

  return (
    <div className="conteudo">
      <div className="cabecalho-pagina">
        <h1 className="titulo-pagina">Os meus anúncios</h1>
        <Link to="/meus-anuncios/novo" className="botao botao-primario"><Icone nome="mais" tamanho={16} /> Novo anúncio</Link>
      </div>

      <div className="estatisticas" role="group" aria-label="Filtrar por estado">
        {RESUMOS.map((r) => (
          <button key={r.estado} type="button" className="cartao estatistica" style={{ "--cor": r.cor, cursor: "pointer", font: "inherit", textAlign: "left", outline: filtro === r.estado ? "2px solid var(--indico)" : undefined }}
                  aria-pressed={filtro === r.estado} onClick={() => setFiltro(filtro === r.estado ? "" : r.estado)}>
            <b>{contagem(r.estado)}</b><span>{r.nome}</span>
          </button>
        ))}
      </div>

      <Erro erro={erro} tentar={recarregar} />
      {aCarregar ? <EsqueletoLinhas linhas={5} /> : dados?.length === 0 ? (
        <Vazio titulo="Ainda não publicou anúncios" texto="Publique o primeiro imóvel e veja logo a estimativa de preço justo.">
          <Link to="/meus-anuncios/novo" className="botao botao-primario">Publicar anúncio</Link>
        </Vazio>
      ) : (
        <>
          <div className="tabela-envolvente tabela-resp">
            <table>
              <thead><tr><th>Título</th><th>Preço</th><th>Estado</th><th>Acções</th></tr></thead>
              <tbody>
                {lista.map((a) => (
                  <tr key={a.id}>
                    <td data-rotulo="Título">
                      <Link to={`/anuncios/${a.id}`} style={{ color: "var(--tinta)", textDecoration: "none", fontWeight: 600 }}>{a.titulo}</Link>
                      <div className="subtil pequeno">{tipologia(a.imovel)} · {a.imovel.bairro} · {a.visualizacoes} visualizações</div>
                      {a.estado === "REJEITADO" && a.motivo_rejeicao && (
                        <div className="pequeno" style={{ color: "var(--perigo)", marginTop: 4 }}><strong>Motivo:</strong> {a.motivo_rejeicao}</div>
                      )}
                    </td>
                    <td data-rotulo="Preço" style={{ whiteSpace: "nowrap" }}>{meticais(a.preco)}{sufixoPreco(a.finalidade)}</td>
                    <td data-rotulo="Estado"><span className={`selo ${SELO_ESTADO[a.estado] || "selo-neutro"}`}>{a.estado_nome}</span></td>
                    <td data-rotulo="Acções">
                      <span className="barra-accoes">
                        <Link to={`/meus-anuncios/${a.id}`} className="accao-texto" aria-label={`Editar ${a.titulo}`}>Editar</Link>
                        <span className="divisor" aria-hidden="true">/</span>
                        <button className="accao-texto perigo" onClick={() => setARemover(a)} aria-label={`Remover ${a.titulo}`}>Remover</button>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="nota-tabela">A mostrar {lista.length} {lista.length === 1 ? "anúncio" : "anúncios"} · Os anúncios rejeitados podem ser editados e submetidos novamente.</p>
        </>
      )}

      <Confirmar aberto={!!aRemover} perigo titulo="Remover anúncio?" confirmar="Remover"
                 texto={aRemover ? `«${aRemover.titulo}» deixa de aparecer na pesquisa. Esta acção não pode ser anulada.` : ""}
                 aoConfirmar={remover} aoCancelar={() => setARemover(null)} />
    </div>
  );
}
