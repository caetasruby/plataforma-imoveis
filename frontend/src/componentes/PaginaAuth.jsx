// Moldura dos ecrãs de entrada e registo: fundo azul e cartão branco ao centro (ecrã do documento)
import { Link } from "react-router-dom";

export default function PaginaAuth({ legenda, children }) {
  return (
    <div className="pagina-auth">
      <div className="cartao-auth">
        <Link to="/" className="marca-auth" aria-label="Kaya Justa, página inicial">Kaya Justa</Link>
        {legenda && <p className="legenda">{legenda}</p>}
        {children}
      </div>
    </div>
  );
}
