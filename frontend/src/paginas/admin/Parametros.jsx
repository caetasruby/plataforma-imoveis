// UC16 Gerir parâmetros do sistema (limiares dos módulos de IA, retenção de logs, etc.)
import { useState } from "react";
import { api } from "../../api";
import Campo from "../../componentes/Campo";
import { Erro, EsqueletoLinhas } from "../../componentes/Estados";
import usarDados from "../../componentes/usarDados";
import { useAvisos } from "../../contexto/Avisos";
import { dataHora } from "../../formato";

function validarLocal(p, valor) {
  const texto = String(valor).trim();
  if (!texto) return "O valor não pode ficar vazio.";
  if (p.tipo === "TEXTO") return null;
  const n = Number(texto.replace(",", "."));
  if (Number.isNaN(n)) return "Indique um número.";
  if (p.tipo === "INTEIRO" && !Number.isInteger(n)) return "Indique um número inteiro.";
  if (p.minimo != null && n < p.minimo) return `O valor mínimo é ${p.minimo}.`;
  if (p.maximo != null && n > p.maximo) return `O valor máximo é ${p.maximo}.`;
  return null;
}

function Parametro({ p, aoGuardar }) {
  const [valor, setValor] = useState(p.valor);
  const [erro, setErro] = useState(null);
  const [ocupado, setOcupado] = useState(false);
  const alterado = valor !== p.valor;

  async function guardar(e) {
    e.preventDefault();
    const msg = validarLocal(p, valor);
    if (msg) { setErro(msg); return; }
    setOcupado(true);
    try {
      const novo = await api.patch(`/admin/parametros/${p.id}/`, { valor });
      setValor(novo.valor);
      aoGuardar(novo);
    } catch (er) { setErro(er.campos?.valor?.join(" ") || er.message); }
    finally { setOcupado(false); }
  }

  const limites = p.tipo !== "TEXTO" && p.minimo != null ? `Entre ${p.minimo} e ${p.maximo}.` : "";
  return (
    <form className="cartao cartao-corpo pilha" onSubmit={guardar} noValidate>
      <div className="linha entre"><h3 style={{ fontSize: 18 }}>{p.nome}</h3><code className="subtil pequeno">{p.chave}</code></div>
      <p className="subtil pequeno">{p.descricao}</p>
      <Campo rotulo="Valor" erro={erro} ajuda={limites || undefined}>
        {(a) => p.tipo === "TEXTO"
          ? <textarea {...a} value={valor} onChange={(e) => { setValor(e.target.value); setErro(null); }} style={{ minHeight: 90 }} />
          : <input {...a} value={valor} inputMode="decimal" onChange={(e) => { setValor(e.target.value); setErro(null); }} style={{ maxWidth: 200 }} />}
      </Campo>
      <div className="linha entre">
        <span className="subtil pequeno">Última alteração: {dataHora(p.ultima_actualizacao)}{p.actualizado_por_nome && ` por ${p.actualizado_por_nome}`}</span>
        <div className="linha">
          {alterado && <button type="button" className="botao botao-texto botao-pequeno" onClick={() => { setValor(p.valor); setErro(null); }}>Repor</button>}
          <button className="botao botao-primario botao-pequeno" disabled={!alterado || ocupado}>Guardar</button>
        </div>
      </div>
    </form>
  );
}

export default function Parametros() {
  const avisar = useAvisos();
  const { dados, setDados, aCarregar, erro, recarregar } = usarDados(() => api.get("/admin/parametros/"), []);
  return (
    <div className="pilha">
      <div className="cabecalho-pagina"><div><h1 className="titulo-pagina">Parâmetros do sistema</h1><p className="subtil">As alterações aplicam-se de imediato às próximas análises e ficam registadas na auditoria.</p></div></div>
      <Erro erro={erro} tentar={recarregar} />
      {aCarregar ? <EsqueletoLinhas /> : dados?.map((p) => (
        <Parametro key={p.id} p={p} aoGuardar={(novo) => { setDados((l) => l.map((x) => (x.id === novo.id ? novo : x))); avisar(`«${novo.nome}» actualizado.`); }} />
      ))}
    </div>
  );
}
