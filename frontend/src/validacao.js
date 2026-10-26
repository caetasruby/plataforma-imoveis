// Primeira camada de validação (no navegador). Usa as mesmas regras do
// servidor para que o utilizador veja o erro antes de enviar o formulário.
import { LIMITES_PRECO } from "./dados/opcoes";

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const CONTACTO = /^(\+258)?8[2-7]\d{7}$/;

export const regras = {
  obrigatorio: (msg) => (v) => (String(v ?? "").trim() ? null : msg),
  email: (v) => (EMAIL.test(String(v).trim()) ? null : "Indique um endereço de e-mail válido."),
  nomeCompleto: (v) => (String(v).trim().split(/\s+/).length >= 2 ? null : "Indique o nome e o apelido."),
  contacto: (v) => (!v || CONTACTO.test(String(v).replace(/\s/g, "")) ? null : "Indique um número moçambicano válido, por exemplo 84 123 4567."),
  palavraPasse: (v) => {
    if (String(v).length < 8) return "A palavra-passe deve ter pelo menos 8 caracteres.";
    if (/^\d+$/.test(v)) return "A palavra-passe não pode ter só números.";
    return null;
  },
  minimo: (n, msg) => (v) => (String(v ?? "").trim().length >= n ? null : msg),
  numeroEntre: (min, max, msg) => (v) => {
    const n = Number(String(v).replace(",", "."));
    return v !== "" && !Number.isNaN(n) && n >= min && n <= max ? null : msg;
  },
};

export function validarPreco(preco, finalidade) {
  const [min, max] = LIMITES_PRECO[finalidade] || [0, Infinity];
  const n = Number(preco);
  if (!preco || Number.isNaN(n)) return "Indique o preço em meticais.";
  if (n < min || n > max)
    return `Para ${finalidade === "VENDA" ? "venda" : "arrendamento"} o preço deve estar entre ${min.toLocaleString("pt-PT")} e ${max.toLocaleString("pt-PT")} MT.`;
  return null;
}

// Aplica um conjunto de regras {campo: [regra, ...]} e devolve {campo: mensagem}
export function validar(valores, esquema) {
  const erros = {};
  for (const [campo, lista] of Object.entries(esquema)) {
    for (const regra of lista) {
      const msg = regra(valores[campo] ?? "", valores);
      if (msg) { erros[campo] = msg; break; }
    }
  }
  return erros;
}

// Junta os erros do servidor (listas) num texto por campo
export function errosDoServidor(campos) {
  const r = {};
  for (const [k, v] of Object.entries(campos || {})) r[k] = Array.isArray(v) ? v.join(" ") : String(v);
  return r;
}
