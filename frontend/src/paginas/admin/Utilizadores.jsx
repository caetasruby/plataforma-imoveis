// UC11 Gerir utilizadores (ecrã "Gestão de Utilizadores" do documento)
import { useEffect, useState } from "react";
import { api } from "../../api";
import Confirmar from "../../componentes/Confirmar";
import { Erro, EsqueletoLinhas, Vazio } from "../../componentes/Estados";
import Icone from "../../componentes/Icone";
import Paginacao from "../../componentes/Paginacao";
import usarDados from "../../componentes/usarDados";
import { useAvisos } from "../../contexto/Avisos";
import { useSessao } from "../../contexto/Sessao";

const SELO = { ACTIVO: "selo-ok", BLOQUEADO: "selo-perigo", DESACTIVADO: "selo-neutro", PENDENTE: "selo-info" };
// Acções permitidas em cada estado (iguais ao diagrama de estados da conta)
const ACCOES = {
  ACTIVO: [["bloquear", "Bloquear", "botao-perigo"], ["desactivar", "Desactivar", "botao-neutro"]],
  BLOQUEADO: [["reactivar", "Reactivar", "botao-secundario"]],
  DESACTIVADO: [["reactivar", "Reactivar", "botao-secundario"]],
  PENDENTE: [],
};
const TEXTOS = {
  bloquear: "A conta fica bloqueada por risco de segurança e a sessão termina de imediato.",
  desactivar: "A conta fica desactivada (por pedido do utilizador ou inactividade).",
  reactivar: "A conta volta ao estado Activo e o utilizador pode entrar de novo.",
};
const iniciais = (nome) => nome.split(/\s+/).filter(Boolean).map((p) => p[0]).slice(0, 2).join("").toUpperCase();

export default function Utilizadores() {
  const avisar = useAvisos();
  const { utilizador: eu } = useSessao();
  const [f, setF] = useState({ q: "", perfil: "", estado: "", page: 1 });
  const [pesquisa, setPesquisa] = useState("");
  const { dados, setDados, aCarregar, erro, recarregar } = usarDados(() => api.get("/admin/utilizadores/", f), [JSON.stringify(f)]);
  const [accao, setAccao] = useState(null);
  const mudar = (e) => setF({ ...f, [e.target.name]: e.target.value, page: 1 });

  // A pesquisa por nome ou e-mail actualiza a lista meio segundo depois de parar de escrever
  useEffect(() => {
    const t = setTimeout(() => setF((x) => (x.q === pesquisa ? x : { ...x, q: pesquisa, page: 1 })), 450);
    return () => clearTimeout(t);
  }, [pesquisa]);

  async function confirmar() {
    const { conta, tipo } = accao;
    setAccao(null);
    try {
      const actualizada = await api.post(`/admin/utilizadores/${conta.id}/${tipo}/`);
      setDados((d) => ({ ...d, results: d.results.map((u) => (u.id === conta.id ? actualizada : u)) }));
      avisar(`Conta de ${conta.nome}: ${actualizada.estado_nome.toLowerCase()}.`);
    } catch (e) { avisar(e.message, "erro"); }
  }

  return (
    <div>
      <div className="cabecalho-pagina">
        <h1 className="titulo-pagina">Gestão de Utilizadores</h1>
        <div className="linha" role="search" aria-label="Filtros de utilizadores">
          <label className="so-leitor" htmlFor="perfil">Perfil</label>
          <select id="perfil" name="perfil" value={f.perfil} onChange={mudar} style={{ width: "auto" }}>
            <option value="">Todos os perfis</option><option value="INQUILINO">Inquilino/Comprador</option><option value="PROPRIETARIO">Proprietário/Agência</option><option value="ADMINISTRADOR">Administrador</option>
          </select>
          <label className="so-leitor" htmlFor="estado">Estado</label>
          <select id="estado" name="estado" value={f.estado} onChange={mudar} style={{ width: "auto" }}>
            <option value="">Todos os estados</option><option value="ACTIVO">Activo</option><option value="BLOQUEADO">Bloqueado</option><option value="DESACTIVADO">Desactivado</option>
          </select>
          <div style={{ position: "relative", minWidth: 240 }}>
            <label className="so-leitor" htmlFor="q">Pesquisar utilizador</label>
            <Icone nome="pesquisa" tamanho={18} style={{ position: "absolute", left: 14, top: 14, color: "var(--tinta-2)" }} />
            <input id="q" type="search" value={pesquisa} onChange={(e) => setPesquisa(e.target.value)} placeholder="Pesquisar utilizador" style={{ paddingLeft: 42 }} />
          </div>
        </div>
      </div>
      <Erro erro={erro} tentar={recarregar} />
      {aCarregar ? <EsqueletoLinhas /> : dados?.count === 0 ? <Vazio icone="utilizador" titulo="Nenhum utilizador encontrado" /> : (
        <>
          <div className="tabela-envolvente tabela-resp">
            <table>
              <thead><tr><th>Nome</th><th>Perfil</th><th>Estado</th><th>Acções</th></tr></thead>
              <tbody>{dados?.results.map((u) => (
                <tr key={u.id}>
                  <td data-rotulo="Nome">
                    <div className="celula-utilizador">
                      <span className="avatar" aria-hidden="true">{iniciais(u.nome)}</span>
                      <div><strong>{u.nome}</strong><div className="subtil pequeno">{u.email}{u.nome_agencia ? ` · ${u.nome_agencia}` : ""}</div></div>
                    </div>
                  </td>
                  <td data-rotulo="Perfil">{u.perfil_nome}</td>
                  <td data-rotulo="Estado"><span className={`selo ${SELO[u.estado]}`}>{u.estado_nome}</span></td>
                  <td data-rotulo="Acções">{u.id === eu.id ? <span className="subtil pequeno">A sua conta</span> : (
                    <div className="linha" style={{ gap: 8 }}>{ACCOES[u.estado].map(([tipo, nome, classe]) => (
                      <button key={tipo} className={`botao botao-pequeno ${classe}`} onClick={() => setAccao({ conta: u, tipo, nome })} aria-label={`${nome} ${u.nome}`}>{nome}</button>
                    ))}</div>
                  )}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          <Paginacao pagina={f.page} total={dados?.count || 0} aoMudar={(p) => setF({ ...f, page: p })} />
        </>
      )}
      <p className="nota-tabela">As alterações ao estado das contas ficam registadas.</p>
      <Confirmar aberto={!!accao} perigo={accao?.tipo !== "reactivar"} titulo={accao ? `${accao.nome} ${accao.conta.nome}?` : ""}
                 texto={accao ? TEXTOS[accao.tipo] : ""} confirmar={accao?.nome} aoConfirmar={confirmar} aoCancelar={() => setAccao(null)} />
    </div>
  );
}
