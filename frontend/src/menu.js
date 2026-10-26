// Menu da aplicação por perfil, organizado pela ordem de utilização.
// O servidor aplica as mesmas regras nas classes de permissão (contas/permissoes.py).

export const MENU = {
  VISITANTE: [
    { para: "/", texto: "Início", uc: "UC04", exacto: true },
    { para: "/assistente", texto: "Assistente", uc: "UC09" },
  ],
  INQUILINO: [
    { para: "/", texto: "Início", uc: "UC04", exacto: true },
    { para: "/para-si", texto: "Para si", uc: "UC08" },
    { para: "/favoritos", texto: "Favoritos", uc: "UC18" },
    { para: "/assistente", texto: "Assistente", uc: "UC09" },
  ],
  PROPRIETARIO: [
    { para: "/", texto: "Início", uc: "UC04", exacto: true },
    { para: "/meus-anuncios", texto: "Os meus anúncios", uc: "UC02, UC03", exacto: true },
    { para: "/meus-anuncios/novo", texto: "Publicar anúncio", uc: "UC01" },
    { para: "/assistente", texto: "Assistente", uc: "UC09" },
  ],
};

// Menu do administrador, agrupado por tarefa: decidir, gerir e acompanhar.
// Aparece no cabeçalho (como nas telas do documento), com um traço entre grupos.
export const MENU_ADMIN = [
  { grupo: "Decidir", itens: [
    { para: "/admin/moderacao", texto: "Moderação", uc: "UC10", contador: "pendentes" },
    { para: "/admin/alertas", texto: "Alertas de IA", uc: "UC12", contador: "alertas" },
  ] },
  { grupo: "Gerir", itens: [
    { para: "/admin/utilizadores", texto: "Utilizadores", uc: "UC11" },
    { para: "/admin/parametros", texto: "Parâmetros", uc: "UC16" },
  ] },
  { grupo: "Acompanhar", itens: [
    { para: "/admin/indicadores", texto: "Indicadores", uc: "UC13" },
    { para: "/admin/registos", texto: "Registos", uc: "RNF08" },
  ] },
];
