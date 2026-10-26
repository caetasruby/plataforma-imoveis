// Rotas da aplicação. Cada rota indica os perfis que a podem abrir.
import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import Cabecalho from "./componentes/Cabecalho";
import { Vazio } from "./componentes/Estados";
import RotaProtegida from "./componentes/RotaProtegida";
import Assistente from "./paginas/Assistente";
import Detalhe from "./paginas/Detalhe";
import Entrar from "./paginas/Entrar";
import Favoritos from "./paginas/Favoritos";
import FormularioAnuncio from "./paginas/FormularioAnuncio";
import MeusAnuncios from "./paginas/MeusAnuncios";
import ParaSi from "./paginas/ParaSi";
import Perfil from "./paginas/Perfil";
import Pesquisa from "./paginas/Pesquisa";
import Registo from "./paginas/Registo";
import PainelAdmin from "./paginas/admin/PainelAdmin";

const INQ = ["INQUILINO"];
const PROP = ["PROPRIETARIO"];
const ADM = ["ADMINISTRADOR"];

export default function App() {
  const local = useLocation();
  useEffect(() => window.scrollTo(0, 0), [local.pathname]);

  // Entrar e Registo ocupam o ecrã todo (fundo azul), como no documento
  const ecraInteiro = ["/entrar", "/registo"].includes(local.pathname);

  return (
    <>
      {!ecraInteiro && <Cabecalho />}
      <main id="principal">
        <Routes>
          <Route path="/" element={<Pesquisa />} />
          <Route path="/pesquisa" element={<Pesquisa />} />
          <Route path="/anuncios/:id" element={<Detalhe />} />
          <Route path="/assistente" element={<Assistente />} />
          <Route path="/entrar" element={<Entrar />} />
          <Route path="/registo" element={<Registo />} />
          <Route path="/perfil" element={<RotaProtegida><Perfil /></RotaProtegida>} />
          <Route path="/para-si" element={<RotaProtegida perfis={INQ}><ParaSi /></RotaProtegida>} />
          <Route path="/favoritos" element={<RotaProtegida perfis={INQ}><Favoritos /></RotaProtegida>} />
          <Route path="/meus-anuncios" element={<RotaProtegida perfis={PROP}><MeusAnuncios /></RotaProtegida>} />
          <Route path="/meus-anuncios/novo" element={<RotaProtegida perfis={PROP}><FormularioAnuncio /></RotaProtegida>} />
          <Route path="/meus-anuncios/:id" element={<RotaProtegida perfis={PROP}><FormularioAnuncio /></RotaProtegida>} />
          <Route path="/admin/*" element={<RotaProtegida perfis={ADM}><PainelAdmin /></RotaProtegida>} />
          <Route path="*" element={<div className="conteudo"><Vazio titulo="Página não encontrada" texto="O endereço que abriu não existe." /></div>} />
        </Routes>
      </main>
      {!ecraInteiro && (
        <footer className="rodape">
          <div>
            <span>Casa Certa · Plataforma Inteligente de Apoio à Decisão para Arrendamento e Compra de Imóveis</span>
            <span>UJC · Laboratório de Engenharia de Software · 2026</span>
            <span style={{ flexBasis: "100%" }}>Dados de demonstração: os anúncios, preços e anunciantes são fictícios. As fotografias mostram edifícios reais de Moçambique, com licença livre (autores e licenças no ficheiro CREDITOS_FOTOGRAFIAS.md).</span>
          </div>
        </footer>
      )}
    </>
  );
}
