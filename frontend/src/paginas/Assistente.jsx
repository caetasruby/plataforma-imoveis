// UC09 Obter esclarecimentos através do assistente virtual
import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import Icone from "../componentes/Icone";
import { Rodar } from "../componentes/Estados";

const INICIAIS = ["O que é o DUAT?", "Quanto é a caução?", "Quanto se paga de SISA?", "Como evitar burlas?"];

export default function Assistente() {
  const [mensagens, setMensagens] = useState([
    { de: "assistente", texto: "Olá! Sou o assistente da Casa Certa. Pergunte-me sobre DUAT, caução, SISA, contratos ou como evitar burlas." },
  ]);
  const [sugestoes, setSugestoes] = useState(INICIAIS);
  const [texto, setTexto] = useState("");
  const [topico, setTopico] = useState(null);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState(null);
  const fim = useRef(null);

  useEffect(() => fim.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), [mensagens]);

  async function perguntar(pergunta) {
    const limpa = pergunta.trim();
    if (!limpa) { setErro("Escreva uma pergunta."); return; }
    if (limpa.length > 500) { setErro("A pergunta deve ter no máximo 500 caracteres."); return; }
    setErro(null);
    setMensagens((m) => [...m, { de: "utilizador", texto: limpa }]);
    setTexto("");
    setOcupado(true);
    try {
      const r = await api.post("/assistente/", { pergunta: limpa, topico_anterior: topico });
      setMensagens((m) => [...m, { de: "assistente", texto: r.resposta }]);
      setSugestoes(r.sugestoes || []);
      if (r.topico) setTopico(r.topico);
    } catch (e) {
      setMensagens((m) => [...m, { de: "assistente", texto: e.message }]);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="conteudo" style={{ maxWidth: 820 }}>
      <div className="cabecalho-pagina">
        <div><h1>Assistente</h1><p className="subtil">Informação geral sobre arrendamento e compra. Não substitui aconselhamento jurídico.</p></div>
      </div>
      <section className="cartao" aria-label="Conversa">
        <div className="conversa" aria-live="polite">
          {mensagens.map((m, i) => <div key={i} className={`mensagem ${m.de}`}>{m.texto}</div>)}
          {ocupado && <div className="mensagem assistente"><Rodar /></div>}
          <div ref={fim} />
        </div>
        <div className="cartao-corpo pilha" style={{ borderTop: "1px solid var(--linha)" }}>
          <div className="sugestoes" aria-label="Sugestões">
            {sugestoes.map((s) => <button key={s} className="sugestao" onClick={() => perguntar(s)} disabled={ocupado}>{s}</button>)}
          </div>
          <form className="linha" style={{ flexWrap: "nowrap" }} onSubmit={(e) => { e.preventDefault(); perguntar(texto); }}>
            <label htmlFor="pergunta" className="so-leitor">A sua pergunta</label>
            <input id="pergunta" value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Escreva a sua pergunta..."
                   maxLength={500} aria-invalid={erro ? "true" : undefined} aria-describedby={erro ? "erro-pergunta" : undefined} />
            <button className="botao botao-primario" disabled={ocupado} aria-label="Enviar"><Icone nome="seta" /></button>
          </form>
          {erro && <span id="erro-pergunta" className="erro-campo" role="alert">{erro}</span>}
        </div>
      </section>
    </div>
  );
}
