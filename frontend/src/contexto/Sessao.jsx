// Contexto da sessão: quem está autenticado e com que perfil (UC14, UC15, UC17)
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, guardarToken, lerToken } from "../api";

const Sessao = createContext(null);

export function FornecedorSessao({ children }) {
  const [utilizador, setUtilizador] = useState(null);
  const [aCarregar, setACarregar] = useState(Boolean(lerToken()));

  // Ao abrir a aplicação, recupera o utilizador a partir do token guardado
  useEffect(() => {
    if (!lerToken()) return;
    api.get("/auth/perfil/")
      .then(setUtilizador)
      .catch(() => guardarToken(null))
      .finally(() => setACarregar(false));
  }, []);

  // O servidor respondeu 401: a sessão foi invalidada (ex.: conta bloqueada)
  useEffect(() => {
    const terminar = () => setUtilizador(null);
    window.addEventListener("sessao-expirada", terminar);
    return () => window.removeEventListener("sessao-expirada", terminar);
  }, []);

  const iniciar = useCallback((resposta) => {
    guardarToken(resposta.token);
    setUtilizador(resposta.utilizador);
    return resposta.utilizador;
  }, []);

  const entrar = useCallback(async (email, palavra_passe) =>
    iniciar(await api.post("/auth/entrar/", { email, palavra_passe })), [iniciar]);

  const registar = useCallback(async (dados) => iniciar(await api.post("/auth/registo/", dados)), [iniciar]);

  const sair = useCallback(async () => {
    try { await api.post("/auth/sair/"); } catch { /* o token pode já ter expirado */ }
    guardarToken(null);
    setUtilizador(null);
  }, []);

  return (
    <Sessao.Provider value={{ utilizador, setUtilizador, aCarregar, entrar, registar, sair }}>
      {children}
    </Sessao.Provider>
  );
}

export const useSessao = () => useContext(Sessao);

// Página inicial de cada perfil depois de entrar
export function inicioDoPerfil(utilizador) {
  if (!utilizador) return "/";
  if (utilizador.perfil === "ADMINISTRADOR") return "/admin";
  if (utilizador.perfil === "PROPRIETARIO") return "/meus-anuncios";
  return "/";
}
