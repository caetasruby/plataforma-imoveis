// Avisos flutuantes de confirmação ou erro (feedback de usabilidade)
import { createContext, useCallback, useContext, useState } from "react";
import Icone from "../componentes/Icone";

const Avisos = createContext(() => {});

export function FornecedorAvisos({ children }) {
  const [lista, setLista] = useState([]);
  const avisar = useCallback((texto, tipo = "ok") => {
    const id = Math.random();
    setLista((l) => [...l, { id, texto, tipo }]);
    setTimeout(() => setLista((l) => l.filter((a) => a.id !== id)), 4500);
  }, []);
  return (
    <Avisos.Provider value={avisar}>
      {children}
      <div className="avisos" role="status" aria-live="polite">
        {lista.map((a) => (
          <div key={a.id} className={`aviso ${a.tipo}`}>
            <Icone nome={a.tipo === "erro" ? "alerta" : "certo"} />
            <span>{a.texto}</span>
          </div>
        ))}
      </div>
    </Avisos.Provider>
  );
}

export const useAvisos = () => useContext(Avisos);
