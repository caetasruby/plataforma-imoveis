// Estados de carregamento, vazio e erro (usados em todas as páginas)
import Icone from "./Icone";

export function EsqueletoCartoes({ quantidade = 6 }) {
  return (
    <div className="grelha-cartoes" aria-busy="true" aria-label="A carregar">
      {Array.from({ length: quantidade }).map((_, i) => (
        <div key={i} className="cartao" style={{ overflow: "hidden" }}>
          <div className="esqueleto" style={{ aspectRatio: "3/2", borderRadius: 0 }} />
          <div className="cartao-corpo">
            <div className="esqueleto" style={{ height: 24, width: "55%" }} />
            <div className="esqueleto" style={{ height: 14, marginTop: 12 }} />
            <div className="esqueleto" style={{ height: 14, marginTop: 8, width: "70%" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function EsqueletoLinhas({ linhas = 5 }) {
  return (
    <div className="cartao cartao-corpo pilha" aria-busy="true" aria-label="A carregar">
      {Array.from({ length: linhas }).map((_, i) => <div key={i} className="esqueleto" style={{ height: 18 }} />)}
    </div>
  );
}

export function Vazio({ titulo, texto, children, icone = "casa" }) {
  return (
    <div className="vazio">
      <Icone nome={icone} tamanho={54} />
      <h3>{titulo}</h3>
      {texto && <p className="subtil">{texto}</p>}
      {children}
    </div>
  );
}

export function Erro({ erro, tentar }) {
  if (!erro) return null;
  return (
    <div className="erro-bloco" role="alert">
      <Icone nome="alerta" />
      <div className="pilha" style={{ flex: 1 }}>
        <p>{erro.message || String(erro)}</p>
        {tentar && <button className="botao botao-perigo botao-pequeno" onClick={tentar}>Tentar novamente</button>}
      </div>
    </div>
  );
}

export function Rodar() {
  return <span className="rodar" aria-hidden="true" />;
}
