// Formatação de valores para português de Moçambique (ponto nos milhares, como nas telas do documento)
const separarMilhares = (n) => String(Math.round(Number(n))).replace(/\B(?=(\d{3})+(?!\d))/g, ".");

export const meticais = (v) => (v == null || v === "" ? "-" : `${separarMilhares(v)} MT`);
export const numeroCurto = (v) => separarMilhares(v);
export const data = (v) => (v ? new Date(v).toLocaleDateString("pt-PT", { day: "2-digit", month: "short", year: "numeric" }) : "-");
export const dataHora = (v) => (v ? new Date(v).toLocaleString("pt-PT", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) : "-");
// Arrendamento: "45.000 MT/mês"; venda: "58.000 MT (Venda)"
export const sufixoPreco = (finalidade) => (finalidade === "ARRENDAMENTO" ? "/mês" : " (Venda)");

export function tipologia(imovel) {
  if (imovel.tipo === "TERRENO") return `Terreno · ${numeroCurto(imovel.area)} m²`;
  const d = imovel.tipo === "ESCRITORIO" ? `${imovel.num_divisoes} salas` : `T${imovel.num_divisoes}`;
  return `${imovel.tipo_nome} ${d} · ${numeroCurto(imovel.area)} m²`;
}

// Resumo curto usado nos cartões: "3 quartos", "4 salas" ou "Terreno 600 m²"
export function resumoDivisoes(imovel) {
  if (imovel.tipo === "TERRENO") return `Terreno ${numeroCurto(imovel.area)} m²`;
  const n = Number(imovel.num_divisoes);
  if (imovel.tipo === "ESCRITORIO") return `${n} ${n === 1 ? "sala" : "salas"}`;
  return `${n} ${n === 1 ? "quarto" : "quartos"}`;
}
