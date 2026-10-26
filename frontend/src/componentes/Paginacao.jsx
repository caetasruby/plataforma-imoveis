// Paginação numerada: setas, números das páginas e "Página X de Y" (ecrã Início do documento)
export default function Paginacao({ pagina, total, porPagina = 12, aoMudar }) {
  const paginas = Math.ceil(total / porPagina);
  if (paginas <= 1) return null;
  // Mostra no máximo 5 números à volta da página actual
  const inicio = Math.max(1, Math.min(pagina - 2, paginas - 4));
  const numeros = Array.from({ length: Math.min(5, paginas) }, (_, i) => inicio + i);
  return (
    <>
      <nav className="paginacao" aria-label="Paginação">
        <button aria-label="Página anterior" disabled={pagina <= 1} onClick={() => aoMudar(pagina - 1)}>&larr;</button>
        {numeros.map((n) => (
          <button key={n} aria-current={n === pagina ? "page" : undefined} aria-label={`Página ${n}`} onClick={() => aoMudar(n)}>{n}</button>
        ))}
        <button aria-label="Página seguinte" disabled={pagina >= paginas} onClick={() => aoMudar(pagina + 1)}>&rarr;</button>
      </nav>
      <p className="paginacao-nota">Página {pagina} de {paginas}</p>
    </>
  );
}
