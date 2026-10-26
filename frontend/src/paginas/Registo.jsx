// UC14 Registar conta
import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import Campo, { ResumoErros } from "../componentes/Campo";
import { Rodar } from "../componentes/Estados";
import { useAvisos } from "../contexto/Avisos";
import { inicioDoPerfil, useSessao } from "../contexto/Sessao";
import { errosDoServidor, regras, validar } from "../validacao";
import PaginaAuth from "../componentes/PaginaAuth";

const NOMES = { nome: "Nome", email: "E-mail", contacto: "Contacto", perfil: "Perfil",
  palavra_passe: "Palavra-passe", confirmar_palavra_passe: "Confirmação" };

export default function Registo() {
  const { registar, utilizador } = useSessao();
  const avisar = useAvisos();
  const navegar = useNavigate();
  const [url] = useSearchParams();
  const [v, setV] = useState({ nome: "", email: "", contacto: "", perfil: url.get("perfil") || "INQUILINO",
    nome_agencia: "", palavra_passe: "", confirmar_palavra_passe: "" });
  const [erros, setErros] = useState({});
  const [ocupado, setOcupado] = useState(false);

  if (utilizador) return <Navigate to={inicioDoPerfil(utilizador)} replace />;
  const mudar = (e) => { setV({ ...v, [e.target.name]: e.target.value }); setErros({ ...erros, [e.target.name]: null }); };

  async function submeter(e) {
    e.preventDefault();
    const encontrados = validar(v, {
      nome: [regras.obrigatorio("Indique o seu nome completo."), regras.nomeCompleto],
      email: [regras.obrigatorio("Indique o seu e-mail."), regras.email],
      contacto: [regras.contacto],
      palavra_passe: [regras.palavraPasse],
      confirmar_palavra_passe: [(c, todos) => (c === todos.palavra_passe ? null : "As palavras-passe não coincidem.")],
    });
    setErros(encontrados);
    if (Object.keys(encontrados).length) return;
    setOcupado(true);
    try {
      const u = await registar(v);
      avisar(`Conta criada. Bem-vindo, ${u.nome.split(" ")[0]}!`);
      navegar(inicioDoPerfil(u), { replace: true });
    } catch (erro) {
      setErros(Object.keys(erro.campos).length ? errosDoServidor(erro.campos) : { geral: erro.message });
    } finally {
      setOcupado(false);
    }
  }

  return (
    <PaginaAuth legenda="Decida com dados, não com palpites. Crie a sua conta gratuita.">
      <form onSubmit={submeter} noValidate className="pilha">
        <h1 style={{ fontSize: 20, textAlign: "center" }}>Criar conta</h1>
        <ResumoErros erros={erros} nomes={NOMES} />
        <div className="campo">
          <span className="rotulo">Vou usar a plataforma para</span>
          <div className="escolhas" role="radiogroup" aria-label="Perfil">
            {[["INQUILINO", "Arrendar ou comprar"], ["PROPRIETARIO", "Publicar imóveis"]].map(([valor, nome]) => (
              <label key={valor} className="escolha">
                <input type="radio" name="perfil" value={valor} checked={v.perfil === valor} onChange={mudar} />
                <span>{nome}</span>
              </label>
            ))}
          </div>
        </div>
        <Campo rotulo="Nome completo" erro={erros.nome}>
          {(p) => <input {...p} name="nome" autoComplete="name" value={v.nome} onChange={mudar} />}
        </Campo>
        {v.perfil === "PROPRIETARIO" && (
          <Campo rotulo="Nome da agência (opcional)" ajuda="Deixe vazio se for proprietário particular.">
            {(p) => <input {...p} name="nome_agencia" value={v.nome_agencia} onChange={mudar} />}
          </Campo>
        )}
        <Campo rotulo="E-mail" erro={erros.email}>
          {(p) => <input {...p} name="email" type="email" autoComplete="email" value={v.email} onChange={mudar} />}
        </Campo>
        <Campo rotulo="Contacto telefónico (opcional)" erro={erros.contacto} ajuda="Por exemplo 84 123 4567.">
          {(p) => <input {...p} name="contacto" type="tel" autoComplete="tel" value={v.contacto} onChange={mudar} />}
        </Campo>
        <Campo rotulo="Palavra-passe" erro={erros.palavra_passe} ajuda="Pelo menos 8 caracteres, não só números.">
          {(p) => <input {...p} name="palavra_passe" type="password" autoComplete="new-password" value={v.palavra_passe} onChange={mudar} />}
        </Campo>
        <Campo rotulo="Confirmar palavra-passe" erro={erros.confirmar_palavra_passe}>
          {(p) => <input {...p} name="confirmar_palavra_passe" type="password" autoComplete="new-password" value={v.confirmar_palavra_passe} onChange={mudar} />}
        </Campo>
        <button className="botao botao-primario botao-largo" disabled={ocupado}>{ocupado && <Rodar />} Criar conta</button>
        <p className="subtil pequeno">Já tem conta? <Link to="/entrar">Entrar</Link></p>
      </form>
    </PaginaAuth>
  );
}
