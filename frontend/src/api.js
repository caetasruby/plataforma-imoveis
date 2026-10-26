// Comunicação com a API REST do Django.
// O token de sessão fica guardado no navegador e é enviado em cada pedido.

const CHAVE_TOKEN = "casacerta.token";

export function lerToken() {
  try { return localStorage.getItem(CHAVE_TOKEN); } catch { return null; }
}
export function guardarToken(token) {
  try { token ? localStorage.setItem(CHAVE_TOKEN, token) : localStorage.removeItem(CHAVE_TOKEN); } catch { /* sem armazenamento */ }
}

// Erro da API com os erros por campo (para mostrar junto de cada campo)
export class ErroApi extends Error {
  constructor(estado, dados) {
    super(mensagemGeral(estado, dados));
    this.estado = estado;
    this.campos = dados && typeof dados === "object" && !Array.isArray(dados) ? dados : {};
  }
}

function mensagemGeral(estado, dados) {
  if (estado === 0) return "Sem ligação ao servidor. Verifique a internet e tente novamente.";
  if (estado === 401) return "A sua sessão terminou. Entre novamente.";
  if (estado === 403) return dados?.detail || "Não tem permissão para esta operação.";
  if (estado === 404) return "O recurso pedido não existe ou já não está disponível.";
  if (estado === 429) return "Demasiados pedidos seguidos. Aguarde um momento.";
  if (estado >= 500) return "Ocorreu um erro no servidor. Tente novamente mais tarde.";
  if (dados?.detail) return Array.isArray(dados.detail) ? dados.detail.join(" ") : dados.detail;
  if (dados?.non_field_errors) return dados.non_field_errors.join(" ");
  return "Verifique os campos assinalados.";
}

export async function pedido(caminho, { metodo = "GET", dados, parametros, formulario } = {}) {
  let url = `/api${caminho}`;
  if (parametros) {
    const limpos = Object.fromEntries(Object.entries(parametros).filter(([, v]) => v !== "" && v != null));
    const qs = new URLSearchParams(limpos).toString();
    if (qs) url += `?${qs}`;
  }
  const cabecalhos = {};
  const token = lerToken();
  if (token) cabecalhos.Authorization = `Token ${token}`;
  let corpo;
  if (formulario) corpo = formulario;               // multipart (fotografias)
  else if (dados !== undefined) {
    cabecalhos["Content-Type"] = "application/json";
    corpo = JSON.stringify(dados);
  }

  let resposta;
  try {
    resposta = await fetch(url, { method: metodo, headers: cabecalhos, body: corpo });
  } catch {
    throw new ErroApi(0, null);
  }
  if (resposta.status === 401 && token) {
    guardarToken(null);
    window.dispatchEvent(new Event("sessao-expirada"));
  }
  if (resposta.status === 204) return null;
  const tipo = resposta.headers.get("Content-Type") || "";
  const conteudo = tipo.includes("application/json") ? await resposta.json() : await resposta.text();
  if (!resposta.ok) throw new ErroApi(resposta.status, conteudo);
  return conteudo;
}

// Atalhos
export const api = {
  get: (c, parametros) => pedido(c, { parametros }),
  post: (c, dados) => pedido(c, { metodo: "POST", dados }),
  patch: (c, dados) => pedido(c, { metodo: "PATCH", dados }),
  delete: (c) => pedido(c, { metodo: "DELETE" }),
  enviar: (c, formulario, metodo = "POST") => pedido(c, { metodo, formulario }),
};

// Descarrega um ficheiro protegido (ex.: relatório CSV)
export async function descarregar(caminho, parametros, nome) {
  const qs = new URLSearchParams(parametros).toString();
  const r = await fetch(`/api${caminho}?${qs}`, { headers: { Authorization: `Token ${lerToken()}` } });
  if (!r.ok) throw new ErroApi(r.status, null);
  const ligacao = document.createElement("a");
  ligacao.href = URL.createObjectURL(await r.blob());
  ligacao.download = nome;
  ligacao.click();
  URL.revokeObjectURL(ligacao.href);
}
