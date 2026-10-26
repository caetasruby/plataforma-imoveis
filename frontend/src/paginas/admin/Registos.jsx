// Consulta dos registos de auditoria (RNF08)
import { useState } from "react";
import { api } from "../../api";
import { Erro, EsqueletoLinhas, Vazio } from "../../componentes/Estados";
import Paginacao from "../../componentes/Paginacao";
import usarDados from "../../componentes/usarDados";
import { dataHora } from "../../formato";

const TIPOS = [["", "Acções de auditoria"], ["MODERACAO", "Moderação"], ["UTILIZADOR", "Gestão de utilizadores"], ["ALERTA", "Alertas"],
  ["PARAMETRO", "Parâmetros"], ["ANUNCIO", "Anúncios"], ["SESSAO", "Sessões"], ["PESQUISA", "Pesquisas"], ["CHAT", "Assistente"]];

export default function Registos() {
  const [f, setF] = useState({ tipo: "", page: 1 });
  const { dados, aCarregar, erro, recarregar } = usarDados(() => api.get("/admin/registos/", { ...f, tamanho: 25 }), [f.tipo, f.page]);
  return (
    <div className="pilha">
      <div className="cabecalho-pagina">
        <div><h1 className="titulo-pagina">Registos de auditoria</h1><p className="subtil">Quem fez o quê e quando. Conservados pelo menos 12 meses.</p></div>
        <div className="campo"><label htmlFor="tipo" className="so-leitor">Tipo</label>
          <select id="tipo" value={f.tipo} onChange={(e) => setF({ tipo: e.target.value, page: 1 })} style={{ width: "auto" }}>
            {TIPOS.map(([v, n]) => <option key={v} value={v}>{n}</option>)}</select></div>
      </div>
      <Erro erro={erro} tentar={recarregar} />
      {aCarregar ? <EsqueletoLinhas /> : dados?.count === 0 ? <Vazio titulo="Sem registos" /> : (
        <>
          <div className="tabela-envolvente">
            <table>
              <thead><tr><th>Data</th><th>Autor</th><th>Tipo</th><th>Descrição</th></tr></thead>
              <tbody>{dados?.results.map((r) => (
                <tr key={r.id}><td className="pequeno" style={{ whiteSpace: "nowrap" }}>{dataHora(r.data_hora)}</td><td>{r.utilizador_nome}</td>
                  <td><span className="selo selo-neutro">{r.tipo_nome}</span></td><td>{r.descricao}</td></tr>
              ))}</tbody>
            </table>
          </div>
          <Paginacao pagina={f.page} total={dados?.count || 0} porPagina={25} aoMudar={(p) => setF({ ...f, page: p })} />
        </>
      )}
    </div>
  );
}
