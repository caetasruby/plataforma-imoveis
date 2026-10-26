// Cartão de anúncio usado na pesquisa, favoritos e recomendações (ecrã "Início" do documento)
import { Link } from "react-router-dom";
import { meticais, resumoDivisoes, sufixoPreco } from "../formato";
import Icone from "./Icone";
import { seloPreco } from "./ReguaPreco";
import BotaoFavorito from "./BotaoFavorito";

// Selo que aparece sobre a fotografia: alerta de fraude tem prioridade sobre o preço
function SeloFoto({ anuncio }) {
  if (anuncio.tem_alerta) return <span className="selo selo-perigo"><Icone nome="alerta" tamanho={14} /> Alerta de fraude</span>;
  const selo = seloPreco(anuncio.diferenca_percentual);
  if (!selo) return null;
  const icone = selo.classe === "selo-ok" ? "certo" : selo.classe === "selo-aviso" ? "cima" : "baixo";
  return <span className={`selo ${selo.classe}`}><Icone nome={icone} tamanho={14} /> {selo.curto}</span>;
}

export default function CartaoAnuncio({ anuncio, motivo, aoMudarFavorito, ligacao, extra, indice = 0 }) {
  const destino = ligacao || `/anuncios/${anuncio.id}`;
  return (
    <article className="cartao cartao-anuncio aparecer" style={{ animationDelay: `${Math.min(indice, 8) * 40}ms` }}>
      <div className="foto">
        {anuncio.capa ? <img src={anuncio.capa} alt={`Fotografia de ${anuncio.titulo}`} loading="lazy" width="600" height="320" /> :
          <div style={{ display: "grid", placeItems: "center", height: "100%", color: "var(--tinta-2)" }}><Icone nome="predio" tamanho={40} /></div>}
        <div className="selos-foto"><SeloFoto anuncio={anuncio} /></div>
        {aoMudarFavorito !== undefined && <BotaoFavorito anuncio={anuncio} aoMudar={aoMudarFavorito} />}
      </div>
      <div className="cartao-corpo" style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600 }}>
          <Link className="ligacao" to={destino}>{anuncio.titulo}</Link>
        </h3>
        <div className="preco">{meticais(anuncio.preco)}<small>{sufixoPreco(anuncio.finalidade)}</small></div>
        <p className="meta">{resumoDivisoes(anuncio.imovel)} • {anuncio.imovel.bairro}, {anuncio.imovel.cidade_nome}</p>
        {motivo && <p className="motivo"><Icone nome="estrela" tamanho={14} /> {motivo}</p>}
        {extra}
      </div>
    </article>
  );
}
