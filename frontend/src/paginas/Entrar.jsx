// UC15 Iniciar sessão
import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import Campo from "../componentes/Campo";
import { Rodar } from "../componentes/Estados";
import Icone from "../componentes/Icone";
import PaginaAuth from "../componentes/PaginaAuth";
import { inicioDoPerfil, useSessao } from "../contexto/Sessao";
import { regras, validar } from "../validacao";

const DEMO = [
  ["Inquilino/Comprador", "inquilino@imoveis.co.mz"],
  ["Proprietário/Agência", "agencia@imoveis.co.mz"],
  ["Administrador", "admin@imoveis.co.mz"],
];

export default function Entrar() {
  const { entrar, utilizador } = useSessao();
  const navegar = useNavigate();
  const local = useLocation();
  const [v, setV] = useState({ email: "", palavra_passe: "" });
  const [erros, setErros] = useState({});
  const [erroGeral, setErroGeral] = useState(null);
  const [ocupado, setOcupado] = useState(false);

  if (utilizador) return <Navigate to={inicioDoPerfil(utilizador)} replace />;

  const mudar = (e) => { setV({ ...v, [e.target.name]: e.target.value }); setErros({ ...erros, [e.target.name]: null }); };

  async function submeter(e) {
    e.preventDefault();
    const encontrados = validar(v, {
      email: [regras.obrigatorio("Indique o seu e-mail."), regras.email],
      palavra_passe: [regras.obrigatorio("Indique a palavra-passe.")],
    });
    setErros(encontrados);
    if (Object.keys(encontrados).length) return;
    setOcupado(true);
    setErroGeral(null);
    try {
      const u = await entrar(v.email.trim(), v.palavra_passe);
      navegar(local.state?.voltar || inicioDoPerfil(u), { replace: true });
    } catch (erro) {
      setErroGeral(erro.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <PaginaAuth legenda="Entre para guardar favoritos, receber recomendações ou gerir os seus anúncios.">
      <form onSubmit={submeter} noValidate className="pilha">
        <h1 className="so-leitor">Entrar</h1>
        {erroGeral && <div className="erro-bloco" role="alert"><Icone nome="alerta" /> {erroGeral}</div>}
        <Campo rotulo="E-mail" erro={erros.email}>
          {(p) => <input {...p} name="email" type="email" autoComplete="email" value={v.email} onChange={mudar} placeholder="Email" />}
        </Campo>
        <Campo rotulo="Palavra-passe" erro={erros.palavra_passe}>
          {(p) => <input {...p} name="palavra_passe" type="password" autoComplete="current-password" value={v.palavra_passe} onChange={mudar} placeholder="Palavra-passe" />}
        </Campo>
        <button className="botao botao-primario botao-largo" disabled={ocupado}>{ocupado && <Rodar />} Entrar</button>
        <p className="subtil pequeno" style={{ textAlign: "center" }}>Ainda não tem conta? <Link to="/registo">Criar conta</Link></p>
        <div className="contas-demo">
          <strong>Contas de demonstração</strong> (palavra-passe <code>Demo@2026</code>):
          <div style={{ marginTop: 4 }}>
            {DEMO.map(([perfil, email]) => (
              <div key={email}>{perfil}:<br /><button type="button" onClick={() => setV({ email, palavra_passe: "Demo@2026" })}>{email}</button></div>
            ))}
          </div>
        </div>
        <p className="termos">Ao registar-se aceita os Termos de Utilização</p>
      </form>
    </PaginaAuth>
  );
}
