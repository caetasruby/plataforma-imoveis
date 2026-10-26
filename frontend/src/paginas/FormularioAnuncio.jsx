// UC01 Publicar anúncio e UC02 Editar anúncio (o mesmo formulário).
// Validação em duas camadas: aqui no navegador e depois no servidor.
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import Campo, { ResumoErros } from "../componentes/Campo";
import { Erro, EsqueletoLinhas, Rodar } from "../componentes/Estados";
import Icone from "../componentes/Icone";
import Mapa from "../componentes/Mapa";
import { useAvisos } from "../contexto/Avisos";
import { BAIRROS, CENTRO_CIDADE, CIDADES, FINALIDADES, TIPOS } from "../dados/opcoes";
import { meticais } from "../formato";
import { errosDoServidor, regras, validar, validarPreco } from "../validacao";

const MAX_FOTOS = 8;
const MAX_MB = 5;
const NOMES = { tipo: "Tipo", finalidade: "Finalidade", cidade: "Cidade", bairro: "Bairro", endereco: "Endereço",
  latitude: "Localização", area: "Área", num_divisoes: "Divisões", preco: "Preço", titulo: "Título",
  descricao: "Descrição", imagens: "Fotografias" };

const VAZIO = { tipo: "APARTAMENTO", finalidade: "ARRENDAMENTO", cidade: "MAPUTO", bairro: "", endereco: "",
  latitude: CENTRO_CIDADE.MAPUTO[0], longitude: CENTRO_CIDADE.MAPUTO[1], area: "", num_divisoes: "",
  preco: "", titulo: "", descricao: "" };

function validarFormulario(v, totalFotos) {
  const erros = validar(v, {
    bairro: [regras.obrigatorio("Indique o bairro.")],
    endereco: [regras.obrigatorio("Indique o endereço (avenida ou rua e número).")],
    area: [regras.numeroEntre(10, 100000, "A área deve estar entre 10 e 100 000 m².")],
    titulo: [regras.minimo(10, "O título deve ter pelo menos 10 caracteres.")],
    descricao: [regras.minimo(30, "A descrição deve ter pelo menos 30 caracteres.")],
  });
  const divisoes = Number(v.num_divisoes);
  if (v.num_divisoes === "" || !Number.isInteger(divisoes) || divisoes < 0 || divisoes > 30) erros.num_divisoes = "Indique um número inteiro entre 0 e 30.";
  else if (v.tipo !== "TERRENO" && divisoes < 1) erros.num_divisoes = "Indique pelo menos 1 divisão.";
  const erroPreco = validarPreco(v.preco, v.finalidade);
  if (erroPreco) erros.preco = erroPreco;
  if (totalFotos < 1) erros.imagens = "Adicione pelo menos uma fotografia.";
  if (totalFotos > MAX_FOTOS) erros.imagens = `No máximo ${MAX_FOTOS} fotografias.`;
  return erros;
}

function EstimativaPreco({ v }) {
  // Pré-visualização do preço justo enquanto o proprietário preenche o formulário
  const [estimativa, setEstimativa] = useState(null);
  const [ocupado, setOcupado] = useState(false);
  const pronto = v.bairro && Number(v.area) >= 10 && v.num_divisoes !== "";
  useEffect(() => {
    if (!pronto) { setEstimativa(null); return; }
    setOcupado(true);
    const t = setTimeout(() => {
      api.post("/estimativa-preco/", { finalidade: v.finalidade, tipo: v.tipo, cidade: v.cidade, bairro: v.bairro, area: v.area, num_divisoes: v.num_divisoes })
        .then(setEstimativa).catch(() => setEstimativa(null)).finally(() => setOcupado(false));
    }, 500);
    return () => clearTimeout(t);
  }, [pronto, v.finalidade, v.tipo, v.cidade, v.bairro, v.area, v.num_divisoes]);

  if (!pronto) return <span className="selo selo-info" title="Preencha o bairro, a área e as divisões para ver já a estimativa">Resultado disponível após submissão</span>;
  if (ocupado || !estimativa) return <div className="esqueleto" style={{ height: 64 }} />;
  const preco = Number(v.preco);
  const fora = preco && (preco < estimativa.minimo || preco > estimativa.maximo);
  return (
    <div className={fora ? "aviso-bloco" : "info-bloco"} aria-live="polite">
      <Icone nome="balanca" />
      <div>
        <strong>Preço justo estimado: {meticais(estimativa.valor)}</strong>
        <p className="pequeno">Intervalo normal na zona: {meticais(estimativa.minimo)} a {meticais(estimativa.maximo)} ({estimativa.metodo.toLowerCase()}).
          {fora && " O seu preço está fora deste intervalo: o anúncio pode ser sinalizado para revisão."}</p>
      </div>
    </div>
  );
}

export default function FormularioAnuncio() {
  const { id } = useParams();
  const edicao = Boolean(id);
  const navegar = useNavigate();
  const avisar = useAvisos();
  const [v, setV] = useState(VAZIO);
  const [existentes, setExistentes] = useState([]);   // fotografias já guardadas (edição)
  const [remover, setRemover] = useState([]);
  const [novas, setNovas] = useState([]);             // {ficheiro, url}
  const [erros, setErros] = useState({});
  const [ocupado, setOcupado] = useState(false);
  const [aCarregar, setACarregar] = useState(edicao);
  const [erroCarregar, setErroCarregar] = useState(null);
  const [arrastar, setArrastar] = useState(false);
  const entradaFicheiros = useRef(null);
  const topo = useRef(null);

  useEffect(() => {
    if (!edicao) return;
    api.get(`/meus-anuncios/${id}/`).then((a) => {
      const i = a.imovel;
      setV({ tipo: i.tipo, finalidade: a.finalidade, cidade: i.cidade, bairro: i.bairro, endereco: i.endereco,
        latitude: Number(i.latitude), longitude: Number(i.longitude), area: String(Number(i.area)),
        num_divisoes: String(i.num_divisoes), preco: String(Number(a.preco)), titulo: a.titulo, descricao: a.descricao });
      setExistentes(a.imagens);
    }).catch(setErroCarregar).finally(() => setACarregar(false));
  }, [edicao, id]);

  useEffect(() => () => novas.forEach((n) => URL.revokeObjectURL(n.url)), [novas]);

  const mudar = (campo, valor) => { setV((x) => ({ ...x, [campo]: valor })); setErros((e) => ({ ...e, [campo]: null })); };
  const aoMudar = (e) => mudar(e.target.name, e.target.value);

  function mudarCidade(cidade) {
    const [lat, lon] = CENTRO_CIDADE[cidade];
    setV((x) => ({ ...x, cidade, bairro: "", latitude: lat, longitude: lon }));
  }
  function mudarBairro(bairro) {
    const coords = BAIRROS[v.cidade]?.[bairro];
    setV((x) => ({ ...x, bairro, ...(coords ? { latitude: coords[0], longitude: coords[1] } : {}) }));
    setErros((e) => ({ ...e, bairro: null }));
  }

  function juntarFicheiros(lista) {
    const aceites = [];
    for (const f of lista) {
      if (!["image/jpeg", "image/png", "image/webp"].includes(f.type)) { setErros((e) => ({ ...e, imagens: `«${f.name}»: use JPEG, PNG ou WEBP.` })); continue; }
      if (f.size > MAX_MB * 1024 * 1024) { setErros((e) => ({ ...e, imagens: `«${f.name}» ultrapassa ${MAX_MB} MB.` })); continue; }
      aceites.push({ ficheiro: f, url: URL.createObjectURL(f) });
    }
    if (aceites.length) { setNovas((n) => [...n, ...aceites]); setErros((e) => ({ ...e, imagens: null })); }
  }

  const totalFotos = existentes.length - remover.length + novas.length;

  async function submeter(e) {
    e.preventDefault();
    const encontrados = validarFormulario(v, totalFotos);
    setErros(encontrados);
    if (Object.keys(encontrados).length) { topo.current?.scrollIntoView({ behavior: "smooth" }); return; }

    const dados = new FormData();
    Object.entries(v).forEach(([k, valor]) => dados.append(k, k === "latitude" || k === "longitude" ? Number(valor).toFixed(6) : valor));
    novas.forEach((n) => dados.append("imagens", n.ficheiro));
    remover.forEach((r) => dados.append("remover_imagens", r));
    setOcupado(true);
    try {
      const r = await api.enviar(edicao ? `/meus-anuncios/${id}/` : "/meus-anuncios/", dados, edicao ? "PUT" : "POST");
      avisar(r.mensagem || "Anúncio guardado.");
      navegar("/meus-anuncios");
    } catch (erro) {
      setErros(Object.keys(erro.campos).length ? errosDoServidor(erro.campos) : { geral: erro.message });
      topo.current?.scrollIntoView({ behavior: "smooth" });
    } finally {
      setOcupado(false);
    }
  }

  if (aCarregar) return <div className="conteudo"><EsqueletoLinhas linhas={8} /></div>;
  if (erroCarregar) return <div className="conteudo"><Erro erro={erroCarregar} /></div>;

  const bairros = Object.keys(BAIRROS[v.cidade] || {});

  return (
    <div className="conteudo">
      <div className="cabecalho-pagina" ref={topo}>
        <h1 className="titulo-pagina">{edicao ? "Editar anúncio" : "Publicar anúncio"}</h1>
      </div>

      <div className="layout-formulario">
        <form onSubmit={submeter} noValidate className="cartao bloco-form pilha" style={{ minWidth: 0 }}>
          <ResumoErros erros={erros} nomes={NOMES} />

          <div className="grelha-form">
            <Campo rotulo="Cidade" erro={erros.cidade}>
              {(p) => <select {...p} value={v.cidade} onChange={(e) => mudarCidade(e.target.value)}>{CIDADES.map((o) => <option key={o.valor} value={o.valor}>{o.nome}</option>)}</select>}
            </Campo>
            <Campo rotulo="Bairro" erro={erros.bairro}>
              {(p) => <><input {...p} list="lista-bairros" value={v.bairro} onChange={(e) => mudarBairro(e.target.value)} autoComplete="off" placeholder="Bairro" />
                <datalist id="lista-bairros">{bairros.map((b) => <option key={b} value={b} />)}</datalist></>}
            </Campo>
            <Campo rotulo="Endereço" erro={erros.endereco} className="inteira">
              {(p) => <input {...p} name="endereco" value={v.endereco} onChange={aoMudar} placeholder="ex.: Av. Julius Nyerere, n.º 450" />}
            </Campo>
            <div className="inteira pilha">
              <Mapa latitude={Number(v.latitude)} longitude={Number(v.longitude)} zoom={14} altura={240}
                    endereco={v.bairro ? `Será usada a localização aproximada do bairro ${v.bairro}. Toque no mapa para marcar o local exacto.` : "Escolha o bairro para definir a localização."} aoClicar={(p) => setV((x) => ({ ...x, latitude: p.lat, longitude: p.lng }))} />
              {erros.latitude && <span className="erro-campo" role="alert">{erros.latitude}</span>}
            </div>

            <div className="campo inteira">
              <span className="rotulo">Pretende</span>
              <div className="escolhas" role="radiogroup" aria-label="Finalidade">
                {FINALIDADES.map((o) => (
                  <label key={o.valor} className="escolha">
                    <input type="radio" name="finalidade" value={o.valor} checked={v.finalidade === o.valor} onChange={aoMudar} />
                    <span>{o.valor === "ARRENDAMENTO" ? "Arrendar" : "Vender"}</span>
                  </label>
                ))}
              </div>
            </div>
            <Campo rotulo="Tipo de imóvel" erro={erros.tipo}>
              {(p) => <select {...p} name="tipo" value={v.tipo} onChange={aoMudar}>{TIPOS.map((o) => <option key={o.valor} value={o.valor}>{o.nome}</option>)}</select>}
            </Campo>
            <Campo rotulo="Preço (MT)" erro={erros.preco} ajuda={v.finalidade === "ARRENDAMENTO" ? "Renda mensal." : "Preço de venda."}>
              {(p) => <input {...p} name="preco" type="number" min="0" inputMode="numeric" value={v.preco} onChange={aoMudar} placeholder="0,00 MT" />}
            </Campo>
            <Campo rotulo="Número de divisões" erro={erros.num_divisoes} ajuda={v.tipo === "TERRENO" ? "Num terreno indique 0." : v.tipo === "ESCRITORIO" ? "Conte as salas." : "T2 = 2 quartos."}>
              {(p) => <input {...p} name="num_divisoes" type="number" min="0" max="30" inputMode="numeric" value={v.num_divisoes} onChange={aoMudar} placeholder="Ex.: 3" />}
            </Campo>
            <Campo rotulo="Área (m²)" erro={erros.area}>
              {(p) => <input {...p} name="area" type="number" min="10" inputMode="decimal" value={v.area} onChange={aoMudar} placeholder="Ex.: 140" />}
            </Campo>

            <Campo rotulo="Título" erro={erros.titulo} ajuda={`${v.titulo.length}/120 caracteres`} className="inteira">
              {(p) => <input {...p} name="titulo" maxLength={120} value={v.titulo} onChange={aoMudar} placeholder="ex.: Apartamento T3 com varanda na Polana" />}
            </Campo>
            <Campo rotulo="Descrição" erro={erros.descricao} ajuda={`${v.descricao.length} caracteres (mínimo 30). Não peça pagamentos antecipados.`} className="inteira">
              {(p) => <textarea {...p} name="descricao" value={v.descricao} onChange={aoMudar} placeholder="Descreva o imóvel: estado, equipamento, proximidades..." />}
            </Campo>
          </div>

          <div>
            <span className="rotulo" id="rotulo-fotos">Fotografias</span>
            <div className="caixas-fotos" style={{ marginTop: 6 }} aria-labelledby="rotulo-fotos">
              {["Carregar fotografias", "Adicionar mais"].map((titulo) => (
                <div key={titulo} className={`zona-ficheiros ${arrastar ? "arrastar" : ""}`} role="button" tabIndex={0}
                     aria-describedby={erros.imagens ? "erro-imagens" : undefined}
                     onClick={() => entradaFicheiros.current.click()}
                     onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), entradaFicheiros.current.click())}
                     onDragOver={(e) => { e.preventDefault(); setArrastar(true); }} onDragLeave={() => setArrastar(false)}
                     onDrop={(e) => { e.preventDefault(); setArrastar(false); juntarFicheiros(e.dataTransfer.files); }}>
                  <span className="mais"><Icone nome="mais" /></span>
                  <strong>{titulo}</strong>
                  <span className="dica">JPG ou PNG · mínimo 1 fotografia (máx. {MAX_FOTOS}, {MAX_MB} MB cada)</span>
                </div>
              ))}
            </div>
            <input ref={entradaFicheiros} type="file" accept="image/jpeg,image/png,image/webp" multiple hidden aria-label="Escolher fotografias"
                   onChange={(e) => { juntarFicheiros(e.target.files); e.target.value = ""; }} />
            {erros.imagens && <span id="erro-imagens" className="erro-campo" role="alert" style={{ marginTop: 8 }}>{erros.imagens}</span>}
            <div className="miniaturas">
              {existentes.filter((f) => !remover.includes(f.id)).map((f) => (
                <div key={f.id} className="miniatura"><img src={f.ficheiro} alt="" />
                  <button type="button" onClick={() => setRemover((r) => [...r, f.id])} aria-label="Retirar fotografia"><Icone nome="fechar" tamanho={14} /></button></div>
              ))}
              {novas.map((n, i) => (
                <div key={n.url} className="miniatura"><img src={n.url} alt="" />
                  <button type="button" onClick={() => setNovas((l) => l.filter((_, j) => j !== i))} aria-label="Retirar fotografia"><Icone nome="fechar" tamanho={14} /></button></div>
              ))}
            </div>
          </div>

          <div className="linha" style={{ marginTop: 28 }}>
            <Link to="/meus-anuncios" className="botao botao-neutro">Cancelar</Link>
            <button className="botao botao-primario" disabled={ocupado}>{ocupado ? <><Rodar /> A analisar...</> : edicao ? "Guardar e ressubmeter" : "Publicar Anúncio"}</button>
          </div>
        </form>

        <aside className="pilha">
          <section className="cartao cartao-corpo" aria-label="Módulos de inteligência artificial">
            <h2 style={{ fontSize: 17 }}>Pré-visualização dos módulos de IA</h2>
            <p className="subtil pequeno" style={{ marginTop: 6 }}>Ao submeter, o sistema calcula:</p>
            <ul className="lista-modulos">
              {[["Estimativa de preço justo", "CT01"], ["Detecção de preço atípico / texto suspeito", "CT02"], ["Verificação de imagens duplicadas", "CT02, RNF02"]].map(([nome, ref]) => (
                <li key={nome}><span className="tique"><Icone nome="certo" tamanho={16} /></span><span>{nome}<small>{ref}</small></span></li>
              ))}
            </ul>
            <EstimativaPreco v={v} />
          </section>
          <section className="cartao cartao-corpo" aria-label="Estado após submissão">
            <h2 style={{ fontSize: 17, marginBottom: 12 }}>Estado após submissão</h2>
            <div className="linha">
              <span className="selo selo-aviso">Pendente de moderação</span>
              <span className="subtil pequeno">{edicao ? "Volta a ser analisado e moderado" : "Aguarda validação do Administrador"}</span>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
