// Moldura dos ecrãs de entrada e registo: fundo azul e cartão branco ao centro (ecrã do documento)
import { Link } from "react-router-dom";
import Simbolo from "./Simbolo";

export default function PaginaAuth({ legenda, children }) {
  return (
    <div className="pagina-auth" style={{ "--foto-hero": "url(/hero-maputo.jpg)" }}>
      <div className="cartao-auth">
        <Link to="/" className="marca-auth" aria-label="Kaya Justa, página inicial"><Simbolo />Kaya Justa</Link>
        {legenda && <p className="legenda">{legenda}</p>}
        {children}
      </div>
    </div>
  );
}
