// UC18 Guardar imóveis favoritos
import { Link } from "react-router-dom";
import { api } from "../api";
import CartaoAnuncio from "../componentes/CartaoAnuncio";
import { Erro, EsqueletoCartoes, Vazio } from "../componentes/Estados";
import usarDados from "../componentes/usarDados";

export default function Favoritos() {
  const { dados, setDados, aCarregar, erro, recarregar } = usarDados(() => api.get("/favoritos/"), []);
  const retirar = (id, valor) => !valor && setDados((l) => l.filter((f) => f.anuncio.id !== id));
  return (
    <div className="conteudo">
      <div className="cabecalho-pagina">
        <div><h1>Favoritos</h1><p className="subtil">Os imóveis que guardou para comparar mais tarde.</p></div>
      </div>
      <Erro erro={erro} tentar={recarregar} />
      {aCarregar ? <EsqueletoCartoes quantidade={3} /> : dados?.length === 0 ? (
        <Vazio icone="coracao" titulo="Ainda não guardou imóveis" texto="Toque no coração de um anúncio para o guardar aqui.">
          <Link to="/pesquisa" className="botao botao-primario">Pesquisar imóveis</Link>
        </Vazio>
      ) : (
        <div className="grelha-cartoes">
          {dados?.map((f, i) => <CartaoAnuncio key={f.id} anuncio={f.anuncio} indice={i} aoMudarFavorito={retirar} />)}
        </div>
      )}
    </div>
  );
}
