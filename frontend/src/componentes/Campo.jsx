// Campo de formulário com etiqueta, ajuda e mensagem de erro ligada ao campo
// (o leitor de ecrã anuncia o erro através de aria-describedby).
import { useId } from "react";
import Icone from "./Icone";

export default function Campo({ rotulo, erro, ajuda, children, className = "" }) {
  const id = useId();
  const idErro = `${id}-erro`;
  const idAjuda = `${id}-ajuda`;
  const descricao = [erro && idErro, ajuda && idAjuda].filter(Boolean).join(" ") || undefined;
  return (
    <div className={`campo ${className}`}>
      <label htmlFor={id}>{rotulo}</label>
      {children({ id, "aria-invalid": erro ? "true" : undefined, "aria-describedby": descricao })}
      {ajuda && !erro && <span id={idAjuda} className="ajuda">{ajuda}</span>}
      {erro && (
        <span id={idErro} className="erro-campo">
          <Icone nome="alerta" tamanho={16} style={{ flexShrink: 0, marginTop: 2 }} />
          {erro}
        </span>
      )}
    </div>
  );
}

export function ResumoErros({ erros, nomes }) {
  const lista = Object.entries(erros).filter(([, v]) => v);
  if (!lista.length) return null;
  return (
    <div className="resumo-erros" role="alert">
      <strong>Corrija {lista.length === 1 ? "o campo assinalado" : `os ${lista.length} campos assinalados`}:</strong>
      <ul>{lista.map(([k, v]) => <li key={k}>{nomes?.[k] ? `${nomes[k]}: ` : ""}{v}</li>)}</ul>
    </div>
  );
}
