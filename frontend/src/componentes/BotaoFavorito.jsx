// Guardar ou retirar dos favoritos (UC18). Visitantes são levados a entrar.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAvisos } from "../contexto/Avisos";
import { useSessao } from "../contexto/Sessao";
import Icone from "./Icone";

export default function BotaoFavorito({ anuncio, aoMudar, comTexto = false }) {
  const { utilizador } = useSessao();
  const avisar = useAvisos();
  const navegar = useNavigate();
  const [ocupado, setOcupado] = useState(false);

  if (utilizador && utilizador.perfil !== "INQUILINO") return null;

  async function alternar(e) {
    e.preventDefault();
    if (!utilizador) { navegar("/entrar", { state: { voltar: `/anuncios/${anuncio.id}` } }); return; }
    setOcupado(true);
    try {
      if (anuncio.favorito) await api.delete(`/favoritos/${anuncio.id}/`);
      else await api.post("/favoritos/", { anuncio: anuncio.id });
      avisar(anuncio.favorito ? "Retirado dos favoritos." : "Guardado nos favoritos.");
      aoMudar?.(anuncio.id, !anuncio.favorito);
    } catch (erro) {
      avisar(erro.message, "erro");
    } finally {
      setOcupado(false);
    }
  }

  const rotulo = anuncio.favorito ? "Retirar dos favoritos" : "Guardar nos favoritos";
  if (comTexto)
    return (
      <button className="botao botao-secundario botao-largo" onClick={alternar} disabled={ocupado} aria-pressed={!!anuncio.favorito}>
        <Icone nome={anuncio.favorito ? "coracaoCheio" : "coracao"} /> {anuncio.favorito ? "Guardado" : "Guardar"}
      </button>
    );
  return (
    <button className="botao-favorito" onClick={alternar} disabled={ocupado} aria-label={rotulo} title={rotulo} aria-pressed={!!anuncio.favorito}>
      <Icone nome={anuncio.favorito ? "coracaoCheio" : "coracao"} />
    </button>
  );
}
