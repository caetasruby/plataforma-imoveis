// Listas de opções partilhadas pelos formulários e filtros (iguais às do servidor)
export const CIDADES = [
  { valor: "MAPUTO", nome: "Maputo" },
  { valor: "MATOLA", nome: "Matola" },
  { valor: "BEIRA", nome: "Beira" },
];
export const TIPOS = [
  { valor: "APARTAMENTO", nome: "Apartamento" },
  { valor: "MORADIA", nome: "Moradia" },
  { valor: "ESCRITORIO", nome: "Escritório" },
  { valor: "TERRENO", nome: "Terreno" },
];
export const FINALIDADES = [
  { valor: "ARRENDAMENTO", nome: "Arrendar" },
  { valor: "VENDA", nome: "Comprar" },
];
export const LIMITES_PRECO = {
  ARRENDAMENTO: [1000, 2000000],
  VENDA: [100000, 500000000],
};

// Bairros conhecidos e coordenadas aproximadas do centro (preenchem o mapa)
export const BAIRROS = {
  MAPUTO: {
    "Polana Cimento": [-25.9655, 32.5952], Sommerschield: [-25.956, 32.599], Coop: [-25.953, 32.585],
    Malhangalene: [-25.956, 32.578], "Alto Maé": [-25.964, 32.57], Baixa: [-25.97, 32.576],
    "Costa do Sol": [-25.905, 32.625], Triunfo: [-25.918, 32.617], "Polana Caniço": [-25.93, 32.6],
    Zimpeto: [-25.84, 32.56],
  },
  MATOLA: {
    Fomento: [-25.958, 32.472], "Matola C": [-25.96, 32.455], Machava: [-25.92, 32.49],
    Liberdade: [-25.94, 32.465], "Matola Rio": [-26.04, 32.45],
  },
  BEIRA: {
    "Ponta Gêa": [-19.84, 34.835], Macuti: [-19.82, 34.87], Palmeiras: [-19.83, 34.85],
    Esturro: [-19.835, 34.845], Manga: [-19.78, 34.89],
  },
};
export const CENTRO_CIDADE = { MAPUTO: [-25.9692, 32.5732], MATOLA: [-25.9622, 32.4589], BEIRA: [-19.8436, 34.8389] };
