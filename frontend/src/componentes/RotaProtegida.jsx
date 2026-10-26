// Controlo de acesso no cliente: só mostra a página aos perfis autorizados.
// (O servidor volta a verificar em cada pedido; isto é só para a interface.)
import { Navigate, useLocation } from "react-router-dom";
import { useSessao } from "../contexto/Sessao";
import { EsqueletoLinhas, Vazio } from "./Estados";

export default function RotaProtegida({ perfis, children }) {
  const { utilizador, aCarregar } = useSessao();
  const local = useLocation();
  if (aCarregar) return <div className="conteudo"><EsqueletoLinhas /></div>;
  if (!utilizador) return <Navigate to="/entrar" replace state={{ voltar: local.pathname }} />;
  if (perfis && !perfis.includes(utilizador.perfil))
    return (
      <div className="conteudo">
        <Vazio icone="escudo" titulo="Acesso reservado"
               texto="Esta página não está disponível para o seu perfil de utilizador." />
      </div>
    );
  return children;
}
