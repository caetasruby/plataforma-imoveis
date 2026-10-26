// UC08 Receber recomendações personalizadas
import { Link } from "react-router-dom";
import { api } from "../api";
import CartaoAnuncio from "../componentes/CartaoAnuncio";
import { Erro, EsqueletoCartoes, Vazio } from "../componentes/Estados";
import usarDados from "../componentes/usarDados";

export default function ParaSi() {
  const { dados, setDados, aCarregar, erro, recarregar } = usarDados(() => api.get("/recomendacoes/"), []);
  const mudar = (id, v) => setDados((l) => l.map((a) => (a.id === id ? { ...a, favorito: v } : a)));
  return (
    <div className="conteudo">
      <div className="cabecalho-pagina">
        <div>
          <h1>Para si</h1>
          <p className="subtil">Sugestões calculadas a partir dos imóveis que viu, guardou e pesquisou.</p>
        </div>
        <button className="botao botao-secundario" onClick={recarregar}>Actualizar</button>
      </div>
      <Erro erro={erro} tentar={recarregar} />
      {aCarregar ? <EsqueletoCartoes /> : dados?.length === 0 ? (
        <Vazio titulo="Ainda sem sugestões" texto="Explore alguns anúncios e voltaremos com recomendações à sua medida.">
          <Link to="/pesquisa" className="botao botao-primario">Começar a pesquisar</Link>
        </Vazio>
      ) : (
        <div className="grelha-cartoes">
          {dados?.map((a, i) => <CartaoAnuncio key={a.id} anuncio={a} motivo={a.motivo} indice={i} aoMudarFavorito={mudar} />)}
        </div>
      )}
    </div>
  );
}
