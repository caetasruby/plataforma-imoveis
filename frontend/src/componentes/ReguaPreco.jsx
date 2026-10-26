// Régua do preço justo (UC05): mostra onde fica o preço pedido no intervalo estimado
import { numeroCurto } from "../formato";

export function seloPreco(diferenca) {
  if (diferenca == null) return null;
  const d = Math.round(diferenca);
  // "texto" é o selo completo (detalhe) e "curto" o das fotografias dos cartões
  if (Math.abs(d) <= 15) return { classe: "selo-ok", texto: "Dentro do preço justo", curto: "Preço justo" };
  if (d > 0) return { classe: "selo-aviso", texto: `${d}% acima do justo`, curto: "Preço acima da média" };
  return { classe: Math.abs(d) >= 40 ? "selo-perigo" : "selo-info", texto: `${Math.abs(d)}% abaixo do justo`, curto: `${Math.abs(d)}% abaixo do justo` };
}

export default function ReguaPreco({ preco, minimo, maximo }) {
  if (!minimo || !maximo) return null;
  const min = Number(minimo) * 0.7;
  const max = Number(maximo) * 1.3;
  const posicao = Math.min(100, Math.max(0, ((Number(preco) - min) / (max - min)) * 100));
  return (
    <div>
      <div className="regua" role="img"
           aria-label={`Preço pedido ${numeroCurto(preco)}; intervalo justo entre ${numeroCurto(minimo)} e ${numeroCurto(maximo)} meticais`}>
        <span className="marcador" style={{ left: `${posicao}%` }} />
      </div>
      <div className="regua-legenda"><span>{numeroCurto(minimo)}</span><span>Intervalo justo</span><span>{numeroCurto(maximo)}</span></div>
    </div>
  );
}
