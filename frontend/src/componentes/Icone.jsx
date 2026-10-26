// Ícones simples em SVG (traço), sem bibliotecas externas
const CAMINHOS = {
  casa: <><path d="M3 11 12 4l9 7" /><path d="M5 10v10h14V10" /></>,
  pesquisa: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
  coracao: <path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />,
  coracaoCheio: <path fill="currentColor" d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />,
  sino: <><path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z" /><path d="M10 20a2 2 0 0 0 4 0" /></>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  fechar: <path d="M6 6l12 12M18 6 6 18" />,
  alerta: <><path d="M12 3 2 20h20z" /><path d="M12 10v4M12 17v.5" /></>,
  certo: <path d="m5 12 4 4 10-10" />,
  escudo: <><path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z" /><path d="m9 12 2 2 4-4" /></>,
  balanca: <><path d="M12 4v16M6 20h12M4 9h16" /><path d="m6 9-3 6h6zM18 9l-3 6h6z" /></>,
  mapa: <><path d="M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" /></>,
  chat: <><path d="M4 5h16v11H9l-5 4z" /></>,
  estrela: <path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" />,
  mais: <path d="M12 5v14M5 12h14" />,
  lapis: <><path d="M4 20h4L19 9l-4-4L4 16z" /></>,
  lixo: <><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" /></>,
  olho: <><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></>,
  foto: <><rect x="3" y="5" width="18" height="14" rx="2" /><circle cx="9" cy="10" r="2" /><path d="m21 16-5-5-8 8" /></>,
  seta: <path d="m9 6 6 6-6 6" />,
  voltar: <path d="m15 6-6 6 6 6" />,
  utilizador: <><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></>,
  sair: <><path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10" /></>,
  filtro: <path d="M4 5h16l-6 8v6l-4-2v-4z" />,
  transferir: <><path d="M12 4v11M7 10l5 5 5-5M5 20h14" /></>,
  cima: <path d="M12 19V5M5 12l7-7 7 7" />,
  baixo: <path d="M12 5v14M5 12l7 7 7-7" />,
  predio: <><path d="M5 21V4h10v17M15 9h4v12M3 21h18" /><path d="M9 8h2M9 12h2M9 16h2" /></>,
};

export default function Icone({ nome, tamanho = 20, ...resto }) {
  return (
    <svg width={tamanho} height={tamanho} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...resto}>
      {CAMINHOS[nome]}
    </svg>
  );
}
