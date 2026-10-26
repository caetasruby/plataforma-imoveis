// Janela de confirmação acessível (usa o elemento <dialog> do navegador)
import { useEffect, useRef } from "react";

export default function Confirmar({ aberto, titulo, texto, confirmar = "Confirmar", perigo, aoConfirmar, aoCancelar, children }) {
  const ref = useRef(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (aberto && !d.open) d.showModal();
    if (!aberto && d.open) d.close();
  }, [aberto]);
  return (
    <dialog ref={ref} onCancel={aoCancelar} className="cartao" style={{ border: 0, padding: 0, maxWidth: 460, width: "calc(100% - 32px)" }}>
      <form method="dialog" className="cartao-corpo pilha" onSubmit={(e) => { e.preventDefault(); aoConfirmar(); }}>
        <h3>{titulo}</h3>
        {texto && <p className="subtil">{texto}</p>}
        {children}
        <div className="linha" style={{ justifyContent: "flex-end" }}>
          <button type="button" className="botao botao-texto" onClick={aoCancelar}>Cancelar</button>
          <button type="submit" className={`botao ${perigo ? "botao-perigo" : "botao-primario"}`}>{confirmar}</button>
        </div>
      </form>
    </dialog>
  );
}
