// UC10 Moderar anúncios (ecrã "Moderação de Anúncios" do documento):
// tabela com o alerta da IA de cada anúncio, os sinalizados em destaque, e acções de aprovar ou rejeitar.
import { Fragment, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api";
import Campo from "../../componentes/Campo";
import Confirmar from "../../componentes/Confirmar";
import { Erro, EsqueletoLinhas, Vazio } from "../../componentes/Estados";
import Icone from "../../componentes/Icone";
import ReguaPreco from "../../componentes/ReguaPreco";
import usarDados from "../../componentes/usarDados";
import { useAvisos } from "../../contexto/Avisos";
import { dataHora, meticais, sufixoPreco, tipologia } from "../../formato";
import { useContadores } from "./PainelAdmin";

export function SeloGravidade({ g, nome }) {
  const classe = { ALTA: "selo-perigo", MEDIA: "selo-aviso", BAIXA: "selo-neutro" }[g];
  return <span className={`selo ${classe}`}><Icone nome="alerta" tamanho={13} /> {nome}</span>;
}

export default function Moderacao() {
  const avisar = useAvisos();
  const { recarregar: recarregarContadores } = useContadores();
  const { dados, setDados, aCarregar, erro, recarregar } = usarDados(() => api.get("/admin/moderacao/", { tamanho: 50 }), []);
  const [rejeitar, setRejeitar] = useState(null);
  const [motivo, setMotivo] = useState("");
  const [erroMotivo, setErroMotivo] = useState(null);
  const [ocupado, setOcupado] = useState(null);
  const [abertos, setAbertos] = useState([]);   // linhas com os detalhes expandidos

  function retirar(id) {
    setDados((d) => ({ ...d, count: d.count - 1, results: d.results.filter((a) => a.id !== id) }));
    recarregarContadores();
  }

  async function aprovar(a) {
    setOcupado(a.id);
    try { await api.post(`/admin/moderacao/${a.id}/aprovar/`); retirar(a.id); avisar(`«${a.titulo}» publicado. O anunciante foi notificado.`); }
    catch (e) { avisar(e.message, "erro"); } finally { setOcupado(null); }
  }

  async function confirmarRejeicao() {
    if (motivo.trim().length < 10) { setErroMotivo("Explique o motivo em pelo menos 10 caracteres."); return; }
    const a = rejeitar;
    try {
      await api.post(`/admin/moderacao/${a.id}/rejeitar/`, { motivo });
      retirar(a.id);
      setRejeitar(null);
      avisar(`«${a.titulo}» rejeitado. O anunciante foi notificado do motivo.`);
    } catch (e) { setErroMotivo(e.campos?.motivo?.join(" ") || e.message); }
  }

  const alternar = (id) => setAbertos((l) => (l.includes(id) ? l.filter((x) => x !== id) : [...l, id]));
  const lista = dados?.results || [];
  const sinalizados = lista.filter((a) => a.alertas.length > 0).length;

  return (
    <div>
      <div className="cabecalho-pagina">
        <h1 className="titulo-pagina">Moderação de Anúncios</h1>
        <p className="subtil pequeno" style={{ margin: 0 }}>
          {sinalizados} {sinalizados === 1 ? "anúncio sinalizado" : "anúncios sinalizados"} · revisão prioritária
        </p>
      </div>
      <Erro erro={erro} tentar={recarregar} />
      {aCarregar ? <EsqueletoLinhas linhas={6} /> : lista.length === 0 ? (
        <Vazio icone="certo" titulo="Fila vazia" texto="Não há anúncios à espera de moderação." />
      ) : (
        <div className="tabela-envolvente tabela-resp">
          <table>
            <thead><tr><th>Anúncio</th><th>Proprietário</th><th>Alerta da IA</th><th>Acções</th></tr></thead>
            <tbody>
              {lista.map((a) => (
                <Fragment key={a.id}>
                  <tr className={a.alertas.length ? "sinalizada" : ""}>
                    <td data-rotulo="Anúncio">
                      <strong>{a.titulo}</strong>
                      <div className="subtil pequeno">{tipologia(a.imovel)} · {a.imovel.bairro}, {a.imovel.cidade_nome} · {meticais(a.preco)}{sufixoPreco(a.finalidade)}</div>
                      <button type="button" className="accao-texto" style={{ minHeight: 44 }} aria-expanded={abertos.includes(a.id)} onClick={() => alternar(a.id)}>
                        {abertos.includes(a.id) ? "Ocultar detalhes" : "Ver detalhes"}
                      </button>
                    </td>
                    <td data-rotulo="Proprietário">{a.anunciante_nome}<div className="subtil pequeno">{dataHora(a.data_criacao)}</div></td>
                    <td data-rotulo="Alerta da IA">
                      {a.alertas.length === 0 ? <span className="selo selo-ok">Sem alertas</span> : (
                        <div className="linha" style={{ gap: 6 }}>
                          {a.alertas.map((al) => (
                            <SeloGravidade key={al.id} g={al.gravidade} nome={`${al.tipo_nome} (CT02)`} />
                          ))}
                        </div>
                      )}
                    </td>
                    <td data-rotulo="Acções">
                      <div className="linha" style={{ gap: 8 }}>
                        <button className="botao botao-ok botao-pequeno" onClick={() => aprovar(a)} disabled={ocupado === a.id} aria-label={`Aprovar ${a.titulo}`}>Aprovar</button>
                        <button className="botao botao-perigo botao-pequeno" onClick={() => { setRejeitar(a); setMotivo(""); setErroMotivo(null); }} aria-label={`Rejeitar ${a.titulo}`}>Rejeitar</button>
                      </div>
                    </td>
                  </tr>
                  {abertos.includes(a.id) && (
                    <tr className="detalhe-linha">
                      <td colSpan={4} className="sem-rotulo">
                        <div className="linha" style={{ alignItems: "flex-start", gap: 24, flexWrap: "wrap" }}>
                          {a.capa && <img src={a.capa} alt={`Fotografia de ${a.titulo}`} style={{ width: 220, aspectRatio: "3/2", objectFit: "cover", borderRadius: 10 }} />}
                          <div className="pilha" style={{ flex: 1, minWidth: 240 }}>
                            <p style={{ maxWidth: "70ch" }}>{a.descricao}</p>
                            <div style={{ maxWidth: 420 }}><ReguaPreco preco={a.preco} minimo={a.preco_justo_min} maximo={a.preco_justo_max} /></div>
                            {a.alertas.map((al) => (
                              <p key={al.id} className="pequeno"><strong>{al.tipo_nome}:</strong> {al.justificacao}</p>
                            ))}
                            <Link className="accao-texto" to={`/anuncios/${a.id}`} target="_blank" style={{ padding: 0 }}>Ver como o público vê</Link>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="nota-tabela">Os anúncios sinalizados pelos módulos de IA aparecem em destaque. Verifique se o DUAT está correctamente indicado antes de aprovar.</p>
      <Confirmar aberto={!!rejeitar} perigo titulo="Rejeitar anúncio" confirmar="Rejeitar e notificar"
                 texto={rejeitar ? `O anunciante de «${rejeitar.titulo}» recebe o motivo e pode corrigir o anúncio.` : ""}
                 aoConfirmar={confirmarRejeicao} aoCancelar={() => setRejeitar(null)}>
        <Campo rotulo="Motivo da rejeição" erro={erroMotivo}>
          {(p) => <textarea {...p} value={motivo} onChange={(e) => { setMotivo(e.target.value); setErroMotivo(null); }} style={{ minHeight: 100 }} />}
        </Campo>
      </Confirmar>
    </div>
  );
}
