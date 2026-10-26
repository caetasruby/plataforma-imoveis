// UC17 Gerir perfil pessoal
import { useState } from "react";
import { api, guardarToken } from "../api";
import Campo from "../componentes/Campo";
import { Rodar } from "../componentes/Estados";
import { useAvisos } from "../contexto/Avisos";
import { useSessao } from "../contexto/Sessao";
import { data } from "../formato";
import { errosDoServidor, regras, validar } from "../validacao";

export default function Perfil() {
  const { utilizador, setUtilizador } = useSessao();
  const avisar = useAvisos();
  const [v, setV] = useState({ nome: utilizador.nome, contacto: utilizador.contacto, nome_agencia: utilizador.nome_agencia });
  const [erros, setErros] = useState({});
  const [ocupado, setOcupado] = useState(false);
  const [pp, setPp] = useState({ actual: "", nova: "" });
  const [errosPp, setErrosPp] = useState({});

  async function guardar(e) {
    e.preventDefault();
    const encontrados = validar(v, { nome: [regras.nomeCompleto], contacto: [regras.contacto] });
    setErros(encontrados);
    if (Object.keys(encontrados).length) return;
    setOcupado(true);
    try {
      setUtilizador(await api.patch("/auth/perfil/", v));
      avisar("Perfil actualizado.");
    } catch (erro) {
      setErros(errosDoServidor(erro.campos));
    } finally { setOcupado(false); }
  }

  async function mudarPalavraPasse(e) {
    e.preventDefault();
    const encontrados = validar(pp, { actual: [regras.obrigatorio("Indique a palavra-passe actual.")], nova: [regras.palavraPasse] });
    setErrosPp(encontrados);
    if (Object.keys(encontrados).length) return;
    try {
      const r = await api.post("/auth/palavra-passe/", pp);
      guardarToken(r.token);
      setPp({ actual: "", nova: "" });
      avisar("Palavra-passe alterada.");
    } catch (erro) {
      setErrosPp(errosDoServidor(erro.campos));
    }
  }

  return (
    <div className="conteudo" style={{ maxWidth: 760 }}>
      <div className="cabecalho-pagina">
        <div><h1>O meu perfil</h1><p className="subtil">{utilizador.perfil_nome} · conta criada em {data(utilizador.date_joined)}</p></div>
      </div>
      <form className="bloco-form pilha" onSubmit={guardar} noValidate>
        <h3>Dados pessoais</h3>
        <Campo rotulo="E-mail" ajuda="O e-mail identifica a conta e não pode ser alterado.">
          {(p) => <input {...p} value={utilizador.email} disabled />}
        </Campo>
        <Campo rotulo="Nome completo" erro={erros.nome}>
          {(p) => <input {...p} value={v.nome} onChange={(e) => setV({ ...v, nome: e.target.value })} />}
        </Campo>
        <Campo rotulo="Contacto telefónico" erro={erros.contacto}>
          {(p) => <input {...p} type="tel" value={v.contacto} onChange={(e) => setV({ ...v, contacto: e.target.value })} />}
        </Campo>
        {utilizador.perfil === "PROPRIETARIO" && (
          <Campo rotulo="Nome da agência">
            {(p) => <input {...p} value={v.nome_agencia} onChange={(e) => setV({ ...v, nome_agencia: e.target.value })} />}
          </Campo>
        )}
        <div><button className="botao botao-primario" disabled={ocupado}>{ocupado && <Rodar />} Guardar alterações</button></div>
      </form>

      <form className="bloco-form pilha" style={{ marginTop: 20 }} onSubmit={mudarPalavraPasse} noValidate>
        <h3>Alterar palavra-passe</h3>
        <Campo rotulo="Palavra-passe actual" erro={errosPp.actual}>
          {(p) => <input {...p} type="password" autoComplete="current-password" value={pp.actual} onChange={(e) => setPp({ ...pp, actual: e.target.value })} />}
        </Campo>
        <Campo rotulo="Nova palavra-passe" erro={errosPp.nova} ajuda="Pelo menos 8 caracteres, não só números.">
          {(p) => <input {...p} type="password" autoComplete="new-password" value={pp.nova} onChange={(e) => setPp({ ...pp, nova: e.target.value })} />}
        </Campo>
        <div><button className="botao botao-secundario">Alterar palavra-passe</button></div>
      </form>
    </div>
  );
}
