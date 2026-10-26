// UC12 Acompanhar alertas gerados pelo sistema
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api";
import Confirmar from "../../componentes/Confirmar";
import Campo from "../../componentes/Campo";
import { Erro, EsqueletoLinhas, Vazio } from "../../componentes/Estados";
import Paginacao from "../../componentes/Paginacao";
import usarDados from "../../componentes/usarDados";
import { useAvisos } from "../../contexto/Avisos";
import { dataHora } from "../../formato";
import { SeloGravidade } from "./Moderacao";
import { useContadores } from "./PainelAdmin";

const ESTADOS = [["PENDENTE", "Pendente"], ["ESCALADO", "Escalado"], ["EM_REVISAO", "Em revisão"], ["CONFIRMADO", "Confirmado"], ["FALSO_POSITIVO", "Falso positivo"], ["RESOLVIDO", "Resolvido"]];
const TIPOS = [["PRECO_ATIPICO", "Preço atípico"], ["TEXTO_SUSPEITO", "Texto suspeito"], ["IMAGEM_DUPLICADA", "Imagem duplicada"], ["ANOMALIA", "Anomalia estatística"]];
const SELO_ESTADO = { PENDENTE: "selo-info", ESCALADO: "selo-perigo", EM_REVISAO: "selo-aviso", CONFIRMADO: "selo-perigo", FALSO_POSITIVO: "selo-neutro", RESOLVIDO: "selo-ok" };
const DECISOES = {
  CONFIRMADO: "Confirmar risco",
  FALSO_POSITIVO: "Marcar como falso positivo",
  RESOLVIDO: "Marcar como resolvido",
};

export default function Alertas() {
  const avisar = useAvisos();
  const { recarregar: recarregarContadores } = useContadores();
  const [f, setF] = useState({ abertos: "1", gravidade: "", tipo_alerta: "", estado: "", inicio: "", fim: "", ordenar: "-pontuacao_risco", page: 1 });
  const { dados, aCarregar, erro, recarregar } = usarDados(() => api.get("/admin/alertas/", f), [JSON.stringify(f)]);
  const [decidir, setDecidir] = useState(null);   // { alerta, decisao }
  const [nota, setNota] = useState("");
  const mudar = (e) => setF({ ...f, [e.target.name]: e.target.value, page: 1 });

  async function confirmar() {
    try {
      await api.post(`/admin/alertas/${decidir.alerta.id}/classificar/`, { decisao: decidir.decisao, nota });
      avisar("Decisão registada.");
      setDecidir(null);
      recarregar();
      recarregarContadores();
    } catch (e) { avisar(e.message, "erro"); }
  }

  const accoes = (a) => {
    if (a.estado === "RESOLVIDO") return [];
    if (a.estado === "CONFIRMADO") return ["RESOLVIDO"];
    if (a.estado === "FALSO_POSITIVO") return ["CONFIRMADO"];
    return ["CONFIRMADO", "FALSO_POSITIVO", "RESOLVIDO"];
  };

  return (
    <div className="pilha">
      <div className="cabecalho-pagina">
        <div><h1 className="titulo-pagina">Alertas de IA</h1><p className="subtil">Sinais de risco detectados pelos módulos de inteligência artificial. Alertas pendentes há mais de 24 horas passam a «Escalado».</p></div>
      </div>
      <div className="cartao cartao-corpo grelha-form" role="search" aria-label="Filtros de alertas">
        <div className="campo"><label htmlFor="abertos">Mostrar</label>
          <select id="abertos" name="abertos" value={f.abertos} onChange={mudar}><option value="1">Só por decidir</option><option value="">Todos</option></select></div>
        <div className="campo"><label htmlFor="gravidade">Gravidade</label>
          <select id="gravidade" name="gravidade" value={f.gravidade} onChange={mudar}><option value="">Todas</option><option value="ALTA">Alta</option><option value="MEDIA">Média</option><option value="BAIXA">Baixa</option></select></div>
        <div className="campo"><label htmlFor="tipo_alerta">Tipo</label>
          <select id="tipo_alerta" name="tipo_alerta" value={f.tipo_alerta} onChange={mudar}><option value="">Todos</option>{TIPOS.map(([v, n]) => <option key={v} value={v}>{n}</option>)}</select></div>
        <div className="campo"><label htmlFor="estado">Estado</label>
          <select id="estado" name="estado" value={f.estado} onChange={mudar}><option value="">Todos</option>{ESTADOS.map(([v, n]) => <option key={v} value={v}>{n}</option>)}</select></div>
        <div className="campo"><label htmlFor="inicio">Desde</label><input id="inicio" name="inicio" type="date" value={f.inicio} onChange={mudar} /></div>
        <div className="campo"><label htmlFor="ordenar">Ordenar</label>
          <select id="ordenar" name="ordenar" value={f.ordenar} onChange={mudar}><option value="-pontuacao_risco">Maior risco</option><option value="-data_criacao">Mais recentes</option><option value="data_criacao">Mais antigos</option></select></div>
      </div>
      <Erro erro={erro} tentar={recarregar} />
      {aCarregar ? <EsqueletoLinhas /> : dados?.count === 0 ? <Vazio icone="escudo" titulo="Sem alertas" texto="Nenhum alerta corresponde aos filtros escolhidos." /> : (
        <>
          <div className="tabela-envolvente">
            <table>
              <thead><tr><th>Gravidade</th><th>Anúncio</th><th>Justificação</th><th>Estado</th><th>Data</th><th>Decisão</th></tr></thead>
              <tbody>{dados?.results.map((a) => (
                <tr key={a.id}>
                  <td><SeloGravidade g={a.gravidade} nome={`${a.gravidade_nome} · ${Math.round(a.pontuacao_risco * 100)}`} /></td>
                  <td><Link to={`/anuncios/${a.anuncio}`}>{a.anuncio_titulo}</Link><div className="subtil pequeno">{a.tipo_nome} · {a.anuncio_estado}</div></td>
                  <td style={{ minWidth: 240 }}>{a.justificacao}{a.nota_decisao && <div className="subtil pequeno">Nota: {a.nota_decisao}</div>}</td>
                  <td><span className={`selo ${SELO_ESTADO[a.estado]}`}>{a.estado_nome}</span>{a.decidido_por_nome && <div className="subtil pequeno">{a.decidido_por_nome}</div>}</td>
                  <td className="pequeno">{dataHora(a.data_criacao)}</td>
                  <td><div className="pilha" style={{ gap: 6 }}>{accoes(a).map((d) => (
                    <button key={d} className="botao botao-secundario botao-pequeno" onClick={() => { setDecidir({ alerta: a, decisao: d }); setNota(""); }}>{DECISOES[d]}</button>
                  ))}</div></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          <Paginacao pagina={f.page} total={dados?.count || 0} aoMudar={(p) => setF({ ...f, page: p })} />
        </>
      )}
      <Confirmar aberto={!!decidir} titulo={decidir ? DECISOES[decidir.decisao] : ""} confirmar="Registar decisão"
                 texto={decidir ? `Alerta «${decidir.alerta.tipo_nome}» do anúncio «${decidir.alerta.anuncio_titulo}».` : ""}
                 aoConfirmar={confirmar} aoCancelar={() => setDecidir(null)}>
        <Campo rotulo="Nota (opcional)" ajuda="Fica registada no log de auditoria.">
          {(p) => <textarea {...p} value={nota} maxLength={500} onChange={(e) => setNota(e.target.value)} style={{ minHeight: 90 }} />}
        </Campo>
      </Confirmar>
    </div>
  );
}
