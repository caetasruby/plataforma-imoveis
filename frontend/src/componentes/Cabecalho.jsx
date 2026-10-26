// Cabeçalho com o menu do perfil activo, notificações e conta do utilizador
import { Fragment, useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useSessao } from "../contexto/Sessao";
import { dataHora } from "../formato";
import { MENU, MENU_ADMIN } from "../menu";
import Icone from "./Icone";

function useFecharFora(aberto, fechar) {
  const ref = useRef(null);
  useEffect(() => {
    if (!aberto) return;
    const clique = (e) => ref.current && !ref.current.contains(e.target) && fechar();
    const tecla = (e) => e.key === "Escape" && fechar();
    document.addEventListener("mousedown", clique);
    document.addEventListener("keydown", tecla);
    return () => { document.removeEventListener("mousedown", clique); document.removeEventListener("keydown", tecla); };
  }, [aberto, fechar]);
  return ref;
}

function Notificacoes() {
  const [aberto, setAberto] = useState(false);
  const [dados, setDados] = useState({ nao_lidas: 0, lista: [] });
  const ref = useFecharFora(aberto, () => setAberto(false));
  const local = useLocation();

  useEffect(() => {
    api.get("/notificacoes/").then(setDados).catch(() => {});
  }, [local.pathname]);

  async function abrir() {
    setAberto(!aberto);
    if (!aberto && dados.nao_lidas) {
      await api.post("/notificacoes/").catch(() => {});
      setDados((d) => ({ ...d, nao_lidas: 0 }));
    }
  }

  return (
    <div className="suspenso" ref={ref}>
      <button className="item-menu" onClick={abrir} aria-expanded={aberto}
              aria-label={`Notificações${dados.nao_lidas ? `, ${dados.nao_lidas} por ler` : ""}`}>
        <Icone nome="sino" />
        {dados.nao_lidas > 0 && <span className="contador">{dados.nao_lidas}</span>}
      </button>
      {aberto && (
        <div className="painel-suspenso lista-notificacoes">
          <div className="cabeca"><strong>Notificações</strong></div>
          {dados.lista.length === 0 && <p className="subtil pequeno" style={{ padding: 12 }}>Não tem notificações.</p>}
          {dados.lista.map((n) => (
            <div key={n.id} className={`notificacao ${n.lida ? "" : "nova"}`}>
              {n.ligacao ? <Link to={n.ligacao} onClick={() => setAberto(false)} style={{ padding: 0 }}>{n.mensagem}</Link> : n.mensagem}
              <div className="subtil" style={{ fontSize: 12, marginTop: 4 }}>{dataHora(n.data)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MenuConta({ utilizador, sair }) {
  const [aberto, setAberto] = useState(false);
  const ref = useFecharFora(aberto, () => setAberto(false));
  return (
    <div className="suspenso" ref={ref}>
      <button className="item-menu" onClick={() => setAberto(!aberto)} aria-expanded={aberto} aria-haspopup="menu">
        <Icone nome="utilizador" /> {utilizador.nome.split(" ")[0]}
      </button>
      {aberto && (
        <div className="painel-suspenso" role="menu">
          <div className="cabeca">
            <strong>{utilizador.nome}</strong>
            <div className="subtil pequeno">{utilizador.perfil_nome}</div>
          </div>
          <Link role="menuitem" to="/perfil" onClick={() => setAberto(false)}>A minha conta</Link>
          <button role="menuitem" onClick={sair}>Terminar sessão</button>
        </div>
      )}
    </div>
  );
}

// Contadores do administrador (pendentes de moderação e alertas abertos).
// As páginas de moderação e de alertas avisam o cabeçalho com o evento "contadores".
function useContadoresAdmin(activo) {
  const [c, setC] = useState({});
  const local = useLocation();
  useEffect(() => {
    if (!activo) return undefined;
    const carregar = () => api.get("/admin/indicadores/").then((d) => setC({ pendentes: d.totais.anuncios_pendentes, alertas: d.totais.alertas_abertos })).catch(() => {});
    carregar();
    window.addEventListener("contadores", carregar);
    return () => window.removeEventListener("contadores", carregar);
  }, [activo, local.pathname]);
  return c;
}

export default function Cabecalho() {
  const { utilizador, sair } = useSessao();
  const [aberto, setAberto] = useState(false);
  const navegar = useNavigate();
  const local = useLocation();
  useEffect(() => setAberto(false), [local.pathname]);

  const eAdmin = utilizador?.perfil === "ADMINISTRADOR";
  const contadores = useContadoresAdmin(eAdmin);

  async function terminar() {
    await sair();
    navegar("/");
  }

  const ligacao = (i) => (
    <NavLink key={i.para} to={i.para} end={i.exacto} className={({ isActive }) => (isActive ? "activo" : "")}>
      {i.texto}
      {i.contador && contadores[i.contador] > 0 && <span className="contador" aria-label={`${contadores[i.contador]} pendentes`}>{contadores[i.contador]}</span>}
    </NavLink>
  );

  return (
    <header className="topo">
      <a className="saltar" href="#principal">Saltar para o conteúdo</a>
      <div className="topo-interior">
        <Link to={eAdmin ? "/admin/moderacao" : "/"} className="marca" aria-label="Casa Certa, página inicial">
          Casa Certa {eAdmin && <small>Admin</small>}
        </Link>
        <button className="botao-menu" onClick={() => setAberto(!aberto)} aria-expanded={aberto} aria-controls="menu-principal" aria-label="Abrir menu">
          <Icone nome={aberto ? "fechar" : "menu"} tamanho={26} />
        </button>
        <nav id="menu-principal" className={`menu ${aberto ? "aberto" : ""}`} aria-label="Menu principal">
          <div className="ligacoes">
            {eAdmin
              ? MENU_ADMIN.map((g, n) => (
                <Fragment key={g.grupo}>
                  {n > 0 && <span className="separador" aria-hidden="true" />}
                  {g.itens.map(ligacao)}
                </Fragment>
              ))
              : MENU[utilizador?.perfil || "VISITANTE"].map(ligacao)}
          </div>
          <div className="direita">
            {utilizador ? (
              <>
                <Notificacoes />
                <MenuConta utilizador={utilizador} sair={terminar} />
              </>
            ) : (
              <>
                <NavLink to="/entrar">Entrar</NavLink>
                <Link to="/registo" className="botao botao-primario botao-pequeno">Criar conta</Link>
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
