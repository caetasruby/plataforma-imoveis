// Detalhe do anúncio (ecrã do documento): UC05 Preço justo, UC06 Alertas de fraude,
// UC07 Mapa, favoritos (UC18) e imóveis semelhantes.
import { useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import BotaoFavorito from "../componentes/BotaoFavorito";
import CartaoAnuncio from "../componentes/CartaoAnuncio";
import { Erro, EsqueletoLinhas } from "../componentes/Estados";
import Icone from "../componentes/Icone";
import Mapa from "../componentes/Mapa";
import ReguaPreco, { seloPreco } from "../componentes/ReguaPreco";
import usarDados from "../componentes/usarDados";
import { data, meticais, numeroCurto, resumoDivisoes, sufixoPreco } from "../formato";

function Galeria({ imagens, titulo }) {
  const [actual, setActual] = useState(0);
  if (!imagens.length) {
    return <div className="galeria"><div className="principal" style={{ display: "grid", placeItems: "center", color: "var(--tinta-2)" }}><Icone nome="predio" tamanho={56} /></div></div>;
  }
  return (
    <div className="galeria">
      <div className="principal"><img src={imagens[actual].ficheiro} alt={`${titulo}, fotografia ${actual + 1} de ${imagens.length}`} width="900" height="600" /></div>
      {imagens.length > 1 && (
        <div className="miniaturas-galeria">
          {imagens.map((img, i) => (
            <button key={img.id} onClick={() => setActual(i)} aria-current={i === actual ? "true" : undefined} aria-label={`Ver fotografia ${i + 1}`}>
              <img src={img.ficheiro} alt="" loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function AlertasRisco({ alertas }) {
  // TC05: indicador de risco com justificação resumida; ao expandir mostra o pormenor
  const maior = alertas.length ? alertas.reduce((a, b) => (b.pontuacao_risco > a.pontuacao_risco ? b : a)) : null;
  return (
    <section className={`cartao cartao-corpo ${alertas.length ? "alerta-risco" : ""}`} aria-label="Alertas de fraude">
      <h3 style={{ fontSize: 16, marginBottom: 10 }}>Alertas de fraude</h3>
      {!alertas.length ? <span className="selo selo-neutro">Nenhum alerta activo</span> : (
        <details className="alerta-risco" style={{ border: 0 }}>
          <summary>
            <span className="selo selo-perigo"><Icone nome="alerta" tamanho={14} /> Risco {maior.gravidade_nome.toLowerCase()}</span>
            <span>Este anúncio tem {alertas.length === 1 ? "um sinal" : `${alertas.length} sinais`} de risco. Ver porquê</span>
          </summary>
          <ul style={{ margin: "14px 0 0", paddingLeft: 20 }} className="pilha">
            {alertas.map((a, i) => (
              <li key={i}><strong>{a.tipo}</strong> (pontuação {Math.round(a.pontuacao_risco * 100)}/100): {a.justificacao}</li>
            ))}
          </ul>
          <p className="subtil pequeno" style={{ marginTop: 12 }}>
            Recomendação: não faça pagamentos antes de visitar o imóvel e confirmar a identidade do proprietário.
          </p>
        </details>
      )}
    </section>
  );
}

function SeccaoMapa({ id }) {
  const { dados, aCarregar, erro } = usarDados(() => api.get(`/anuncios/${id}/mapa/`), [id]);
  if (aCarregar) return <div className="esqueleto" style={{ height: 340 }} />;
  if (erro) return <div className="aviso-bloco"><Icone nome="mapa" /> Não foi possível obter a localização. {erro.message}</div>;
  return (
    <div className="pilha">
      <Mapa latitude={dados.latitude} longitude={dados.longitude} endereco={dados.endereco} pontos={dados.pontos_interesse} zoom={14} />
      <p className="subtil pequeno"><Icone nome="mapa" tamanho={15} style={{ verticalAlign: -2 }} /> {dados.endereco}</p>
      {dados.pontos_interesse.length > 0 && (
        <ul className="lista-poi" aria-label="Distâncias a pontos de interesse">
          {dados.pontos_interesse.map((p) => (
            <li key={p.nome}><strong>{p.categoria}</strong> · {p.nome}<br /><span className="subtil">{p.distancia_km.toLocaleString("pt-PT")} km em linha recta</span></li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Detalhe() {
  const { id } = useParams();
  const { dados: a, setDados, aCarregar, erro, recarregar } = usarDados(() => api.get(`/anuncios/${id}/`), [id]);
  const semelhantes = usarDados(() => api.get(`/anuncios/${id}/semelhantes/`), [id]);
  const [contactar, setContactar] = useState(false);
  const secaoSemelhantes = useRef(null);

  if (aCarregar) return <div className="conteudo"><div className="esqueleto" style={{ height: 360 }} /><div style={{ marginTop: 20 }}><EsqueletoLinhas /></div></div>;
  if (erro) return <div className="conteudo"><Erro erro={erro} tentar={recarregar} /></div>;

  const selo = seloPreco(a.diferenca_percentual);
  const i = a.imovel;

  return (
    <div className="conteudo">
      <Link to="/" className="botao botao-texto" style={{ marginBottom: 12, paddingLeft: 0 }}><Icone nome="voltar" /> Voltar para resultados</Link>
      {a.estado !== "PUBLICADO" && (
        <div className="info-bloco" style={{ marginBottom: 16 }}><Icone nome="olho" /> Pré-visualização: este anúncio está «{a.estado_nome}» e não aparece na pesquisa pública.</div>
      )}

      <div className="detalhe-topo">
        <Galeria imagens={a.imagens} titulo={a.titulo} />

        <div className="pilha">
          <section className="cartao cartao-corpo pilha" aria-label="Preço">
            <div className="linha-valor"><span>Preço anunciado:</span><b>{meticais(a.preco)}{sufixoPreco(a.finalidade)}</b></div>
            {a.preco_justo ? (
              <>
                <div className="linha-valor">
                  <span>Preço justo estimado (IA):</span>
                  <span>{numeroCurto(a.preco_justo_min)} - {numeroCurto(a.preco_justo_max)} MT</span>
                </div>
                {selo && <div><span className={`selo ${selo.classe}`}>{selo.classe === "selo-ok" && <Icone nome="certo" tamanho={14} />}{selo.texto}</span></div>}
                <ReguaPreco preco={a.preco} minimo={a.preco_justo_min} maximo={a.preco_justo_max} />
                <p className="subtil pequeno">
                  Estimativa central de {meticais(a.preco_justo)}; diferença de {a.diferenca_percentual > 0 ? "+" : ""}{a.diferenca_percentual}%. Calculado com anúncios semelhantes na mesma zona (intervalo de confiança de 95%).
                </p>
              </>
            ) : <p className="subtil pequeno">Estimativa de preço ainda não disponível.</p>}
          </section>

          <AlertasRisco alertas={a.alertas} />

          <div className="linha" style={{ alignItems: "stretch" }}>
            <button className="botao botao-primario" style={{ flex: 1 }} aria-expanded={contactar} aria-controls="contacto" onClick={() => setContactar(!contactar)}>
              Contactar Proprietário
            </button>
            <button className="botao botao-primario" style={{ flex: 1 }}
                    onClick={() => secaoSemelhantes.current?.scrollIntoView({ behavior: "smooth", block: "start" })}>
              Ver imóveis semelhantes
            </button>
          </div>
          {contactar && (
            <div id="contacto" className="painel-contacto pilha">
              <p><strong>{a.anunciante.agencia || a.anunciante.nome}</strong>{a.anunciante.agencia && <span> · {a.anunciante.nome}</span>}</p>
              <div className="linha">
                {a.anunciante.contacto && <a className="botao botao-secundario botao-pequeno" href={`tel:${a.anunciante.contacto}`}>Ligar {a.anunciante.contacto}</a>}
                <a className="botao botao-secundario botao-pequeno" href={`mailto:${a.anunciante.email}?subject=${encodeURIComponent(a.titulo)}`}>Enviar e-mail</a>
              </div>
              <p className="pequeno">Marque sempre uma visita antes de qualquer pagamento.</p>
            </div>
          )}
          <BotaoFavorito anuncio={a} comTexto aoMudar={(_, v) => setDados({ ...a, favorito: v })} />
        </div>
      </div>

      <div className="detalhe-topo" style={{ marginTop: 36 }}>
        <div className="pilha" style={{ minWidth: 0 }}>
          <div>
            <div className="linha" style={{ marginBottom: 10 }}>
              <span className="selo selo-info">{a.finalidade_nome}</span>
              <span className="selo selo-neutro">{i.tipo_nome}</span>
            </div>
            <h1>{a.titulo}</h1>
            <p className="factos-linha" style={{ marginTop: 8 }}>
              {resumoDivisoes(i)} • {numeroCurto(i.area)} m² • {numeroCurto(Number(a.preco) / Number(i.area))} MT/m²
            </p>
            <p className="subtil pequeno" style={{ marginTop: 4 }}>
              {i.bairro}, {i.cidade_nome} • Publicado em {data(a.data_publicacao || a.data_criacao)} • {a.visualizacoes} visualizações
            </p>
          </div>
          <section>
            <h2 style={{ fontSize: 18, marginBottom: 8 }}>Descrição</h2>
            <p style={{ whiteSpace: "pre-line", maxWidth: "70ch" }}>{a.descricao}</p>
          </section>
        </div>
        <section className="pilha" style={{ minWidth: 0 }}>
          <h2 style={{ fontSize: 18 }}>Localização e pontos de interesse</h2>
          <SeccaoMapa id={a.id} />
        </section>
      </div>

      <section className="seccao" ref={secaoSemelhantes} id="semelhantes" style={{ marginTop: 44, scrollMarginTop: 90 }}>
        <h2 style={{ marginBottom: 16 }}>Imóveis semelhantes</h2>
        {semelhantes.dados?.length > 0 ? (
          <div className="grelha-cartoes">
            {semelhantes.dados.map((s, n) => <CartaoAnuncio key={s.id} anuncio={s} indice={n} />)}
          </div>
        ) : <p className="subtil">{semelhantes.aCarregar ? "A procurar imóveis semelhantes..." : "Ainda não há imóveis semelhantes a este."}</p>}
      </section>
    </div>
  );
}
