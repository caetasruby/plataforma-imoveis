// UC13 Visualizar indicadores gerais de actividade (ecrã "Painel de Indicadores" do documento)
import { useState } from "react";
import { api, descarregar } from "../../api";
import { Erro, EsqueletoLinhas } from "../../componentes/Estados";
import GraficoBarras from "../../componentes/GraficoBarras";
import Icone from "../../componentes/Icone";
import usarDados from "../../componentes/usarDados";
import { useAvisos } from "../../contexto/Avisos";
import { meticais, numeroCurto } from "../../formato";

const PERIODOS = [
  { valor: "30d", nome: "Últimos 30 dias", dias: 29, meses: false },
  { valor: "3m", nome: "Últimos 3 meses", meses: 3 },
  { valor: "6m", nome: "Últimos 6 meses", meses: 6 },
  { valor: "12m", nome: "Últimos 12 meses", meses: 12 },
];
const isoLocal = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

// Início e fim do período: os meses contam desde o dia 1 do mês mais antigo
function limites(valor) {
  const p = PERIODOS.find((x) => x.valor === valor);
  const fim = new Date();
  const inicio = p.meses ? new Date(fim.getFullYear(), fim.getMonth() - (p.meses - 1), 1) : new Date(Date.now() - p.dias * 864e5);
  return { inicio: isoLocal(inicio), fim: isoLocal(fim), mensal: Boolean(p.meses) };
}

const nomeMes = (chave) => {
  const [a, m] = chave.split("-").map(Number);
  const t = new Date(a, m - 1, 1).toLocaleDateString("pt-PT", { month: "short" }).replace(".", "");
  return t.charAt(0).toUpperCase() + t.slice(1);
};
const diaCurto = (d) => new Date(`${d}T12:00`).toLocaleDateString("pt-PT", { day: "2-digit", month: "short" });

// Agrupa a série diária por mês (ou mantém por dia nos períodos curtos), sem deixar meses em falta
function agrupar(serie, inicio, fim, campo, mensal) {
  if (!mensal) {
    const mapa = Object.fromEntries(serie.map((s) => [s.dia, s[campo]]));
    const r = [];
    for (let d = new Date(`${inicio}T12:00`); d <= new Date(`${fim}T12:00`); d = new Date(d.getTime() + 864e5)) {
      const k = isoLocal(d);
      r.push({ rotulo: k, valor: mapa[k] || 0 });
    }
    return r;
  }
  const meses = {};
  for (let d = new Date(`${inicio}T12:00`); d <= new Date(`${fim}T12:00`); d = new Date(d.getFullYear(), d.getMonth() + 1, 1, 12)) {
    meses[isoLocal(d).slice(0, 7)] = 0;
  }
  serie.forEach((s) => { const k = s.dia.slice(0, 7); if (k in meses) meses[k] += s[campo] || 0; });
  return Object.entries(meses).map(([rotulo, valor]) => ({ rotulo, valor }));
}

export default function Indicadores() {
  const avisar = useAvisos();
  const [periodo, setPeriodo] = useState("6m");
  const lim = limites(periodo);
  const { dados, aCarregar, erro, recarregar } = usarDados(() => api.get("/admin/indicadores/", { inicio: lim.inicio, fim: lim.fim }), [periodo]);

  async function exportar() {
    try { await descarregar("/admin/indicadores/exportar/", { inicio: lim.inicio, fim: lim.fim }, `indicadores_${lim.inicio}_${lim.fim}.csv`); avisar("Relatório exportado."); }
    catch (e) { avisar(e.message, "erro"); }
  }

  const horas = dados?.totais.tempo_medio_moderacao_horas;

  return (
    <div className="pilha">
      <div className="cabecalho-pagina" style={{ marginBottom: 28 }}>
        <h1 className="titulo-pagina">Painel de Indicadores</h1>
        <div className="linha">
          <label className="so-leitor" htmlFor="periodo">Período</label>
          <span className="seleccao-periodo">
            <select id="periodo" value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
              {PERIODOS.map((p) => <option key={p.valor} value={p.valor}>{p.nome}</option>)}
            </select>
          </span>
          <button type="button" className="botao botao-secundario botao-pequeno" onClick={exportar}><Icone nome="transferir" tamanho={17} /> Exportar relatório</button>
        </div>
      </div>
      <Erro erro={erro} tentar={recarregar} />
      {aCarregar || !dados ? <EsqueletoLinhas linhas={8} /> : (
        <>
          <div className="kpis">
            <div className="cartao kpi" style={{ "--cor": "var(--teal)" }}><b>{numeroCurto(dados.totais.anuncios_publicados)}</b><span>Nº de Anúncios Activos</span></div>
            <div className="cartao kpi" style={{ "--cor": "var(--azul)" }}><b>{numeroCurto(dados.totais.utilizadores_activos)}</b><span>Utilizadores Activos</span></div>
            <div className="cartao kpi" style={{ "--cor": "var(--perigo)" }}><b>{dados.totais.alertas_abertos}</b><span>Alertas de Fraude Abertos</span></div>
            <div className="cartao kpi" style={{ "--cor": "var(--ambar)" }}><b>{horas == null ? "-" : `${String(horas).replace(".", ",")} h`}</b><span>Tempo Médio de Moderação</span></div>
          </div>

          <div className="graficos" style={{ marginTop: 28 }}>
            <GraficoBarras titulo={lim.mensal ? "Anúncios publicados por mês" : "Anúncios publicados por dia"} cor="var(--teal)"
                           formatarRotulo={lim.mensal ? nomeMes : diaCurto} colunaRotulo={lim.mensal ? "Mês" : "Dia"}
                           dados={agrupar(dados.serie_diaria, dados.periodo.inicio, dados.periodo.fim, "publicados", lim.mensal)} />
            <GraficoBarras titulo="Alertas de fraude por tipo" cor="var(--ambar)" colunaRotulo="Tipo"
                           dados={dados.alertas_por_tipo.map((a) => ({ rotulo: a.tipo, valor: a.total }))} />
          </div>

          <h2 style={{ fontSize: 18, marginTop: 36 }}>Actividade no período</h2>
          <div className="kpis" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 170px), 1fr))" }}>
            {[["novos_anuncios", "Novos anúncios"], ["novos_utilizadores", "Novos utilizadores"], ["pesquisas", "Pesquisas"],
              ["visualizacoes", "Visualizações"], ["aprovados", "Aprovados"], ["rejeitados", "Rejeitados"],
              ["alertas_gerados", "Alertas gerados"], ["perguntas_assistente", "Perguntas ao assistente"]].map(([k, nome]) => (
              <div key={k} className="cartao kpi pequeno-kpi" style={{ "--cor": "var(--indico)" }}><b>{dados.no_periodo[k]}</b><span>{nome}</span></div>
            ))}
          </div>

          <div className="tabela-envolvente" style={{ marginTop: 24 }}>
            <table>
              <caption className="so-leitor">Mercado por cidade</caption>
              <thead><tr><th>Cidade</th><th>Publicados</th><th>Renda média</th><th>Venda média</th></tr></thead>
              <tbody>{dados.por_cidade.map((c) => (
                <tr key={c.cidade}><td><strong>{c.cidade}</strong></td><td>{c.total}</td><td>{meticais(c.renda_media)}</td><td>{meticais(c.venda_media)}</td></tr>
              ))}</tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
