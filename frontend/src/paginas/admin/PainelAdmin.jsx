// Painel de administração: as páginas partilham o menu do cabeçalho (agrupado por tarefa)
import { createContext, useContext } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Alertas from "./Alertas";
import Indicadores from "./Indicadores";
import Moderacao from "./Moderacao";
import Parametros from "./Parametros";
import Registos from "./Registos";
import Utilizadores from "./Utilizadores";

// As páginas chamam recarregar() depois de decidir; o cabeçalho actualiza os contadores
const Contadores = createContext({ recarregar: () => window.dispatchEvent(new Event("contadores")) });
export const useContadores = () => useContext(Contadores);

export default function PainelAdmin() {
  return (
    <div className="conteudo">
      <Routes>
        <Route index element={<Navigate to="moderacao" replace />} />
        <Route path="moderacao" element={<Moderacao />} />
        <Route path="alertas" element={<Alertas />} />
        <Route path="utilizadores" element={<Utilizadores />} />
        <Route path="parametros" element={<Parametros />} />
        <Route path="indicadores" element={<Indicadores />} />
        <Route path="registos" element={<Registos />} />
      </Routes>
    </div>
  );
}
