// Gráfico de barras simples em SVG (uma só série, um só eixo), como nos indicadores do documento.
// Com poucas barras mostra o valor por cima de cada uma; com muitas, mostra-o ao passar o rato
// ou ao receber foco pelo teclado. Existe sempre a alternativa em tabela (acessibilidade).
import { useState } from "react";

export default function GraficoBarras({ titulo, dados, cor = "var(--teal)", formatarRotulo = (x) => x, altura = 260, colunaRotulo = "Data" }) {
  const [activo, setActivo] = useState(null);
  const [tabela, setTabela] = useState(false);
  const max = Math.max(1, ...dados.map((d) => d.valor));
  const largura = 640;
  const margem = { esq: 30, dir: 8, topo: 26, base: 30 };
  const util = largura - margem.esq - margem.dir;
  const passo = util / Math.max(1, dados.length);
  const poucas = dados.length <= 12;
  const barra = poucas ? Math.min(72, passo * 0.7) : Math.max(3, Math.min(28, passo - 2));
  const escala = (v) => ((altura - margem.topo - margem.base) * v) / max;
  const marcas = max % 2 === 0 ? [0, max / 2, max] : [0, max];   // só marcas inteiras
  const indicesRotulos = poucas ? dados.map((_, i) => i) : [0, dados.length - 1];
  const resumo = `${titulo}: ${dados.map((d) => `${formatarRotulo(d.rotulo)} ${d.valor}`).join(", ")}`;

  return (
    <figure className="cartao cartao-corpo" style={{ margin: 0 }}>
      <figcaption className="linha entre" style={{ marginBottom: 10 }}>
        <strong>{titulo}</strong>
        <button className="botao botao-texto botao-pequeno" onClick={() => setTabela(!tabela)} aria-pressed={tabela}>
          {tabela ? "Ver gráfico" : "Ver tabela"}
        </button>
      </figcaption>
      {tabela ? (
        <div style={{ maxHeight: 260, overflow: "auto" }}>
          <table><thead><tr><th>{colunaRotulo}</th><th>Valor</th></tr></thead>
            <tbody>{dados.map((d) => <tr key={d.rotulo}><td style={{ padding: "10px 16px" }}>{formatarRotulo(d.rotulo)}</td><td style={{ padding: "10px 16px" }}>{d.valor}</td></tr>)}</tbody></table>
        </div>
      ) : dados.length === 0 ? <p className="subtil pequeno">Sem dados no período.</p> : (
        <div style={{ position: "relative" }}>
          <svg viewBox={`0 0 ${largura} ${altura}`} width="100%" role="img" aria-label={resumo}>
            {marcas.map((m) => {
              const y = altura - margem.base - escala(m);
              return (
                <g key={m}>
                  <line x1={margem.esq} x2={largura - margem.dir} y1={y} y2={y} stroke="#E5E7EB" strokeWidth="1" />
                  <text x={margem.esq - 6} y={y + 4} textAnchor="end" fontSize="12" fill="var(--tinta-2)">{m}</text>
                </g>
              );
            })}
            {dados.map((d, i) => {
              const h = escala(d.valor);
              const x = margem.esq + i * passo + (passo - barra) / 2;
              const y = altura - margem.base - h;
              const r = Math.min(6, barra / 2, h);
              return (
                <g key={d.rotulo} tabIndex={0} onMouseEnter={() => setActivo(i)} onMouseLeave={() => setActivo(null)}
                   onFocus={() => setActivo(i)} onBlur={() => setActivo(null)} aria-label={`${formatarRotulo(d.rotulo)}: ${d.valor}`}>
                  <rect x={margem.esq + i * passo} y={margem.topo} width={passo} height={altura - margem.topo - margem.base} fill="transparent" />
                  {/* barra com cantos arredondados só no topo */}
                  {h > 0 && <path d={`M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + barra - r} Q${x + barra},${y} ${x + barra},${y + r} V${y + h} Z`}
                                    fill={cor} opacity={activo === null || activo === i ? 1 : 0.5} />}
                  {poucas && <text x={x + barra / 2} y={y - 8} textAnchor="middle" fontSize="14" fontWeight="700" fill="var(--tinta)">{d.valor}</text>}
                </g>
              );
            })}
            {indicesRotulos.filter((i, n, a) => a.indexOf(i) === n).map((i) => (
              <text key={i} x={margem.esq + i * passo + (poucas ? passo / 2 : i === 0 ? 0 : passo)} y={altura - 8}
                    textAnchor={poucas ? "middle" : i === 0 ? "start" : "end"} fontSize={poucas && dados.length > 4 ? 12 : 13} fill="var(--tinta-2)">
                {formatarRotulo(dados[i].rotulo)}
              </text>
            ))}
          </svg>
          {!poucas && activo !== null && (
            <div role="status" style={{ position: "absolute", top: 0, left: `${Math.min(80, ((margem.esq + activo * passo) / largura) * 100)}%`,
              background: "var(--tinta)", color: "#fff", borderRadius: 8, padding: "4px 10px", fontSize: 13, pointerEvents: "none" }}>
              {formatarRotulo(dados[activo].rotulo)}: <strong>{dados[activo].valor}</strong>
            </div>
          )}
        </div>
      )}
    </figure>
  );
}
