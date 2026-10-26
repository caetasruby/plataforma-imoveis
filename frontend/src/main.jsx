import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "./estilos.css";
import App from "./App";
import { FornecedorAvisos } from "./contexto/Avisos";
import { FornecedorSessao } from "./contexto/Sessao";

createRoot(document.getElementById("raiz")).render(
  <StrictMode>
    <BrowserRouter>
      <FornecedorSessao>
        <FornecedorAvisos>
          <App />
        </FornecedorAvisos>
      </FornecedorSessao>
    </BrowserRouter>
  </StrictMode>
);
