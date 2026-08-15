/**
 * Catálogo das luas dos demais planetas.
 *
 * Espelha o `dados/luas.py` do desktop. Estava dentro de `dados/planetas.js`,
 * junto com os 9 corpos principais; saiu para cá quando a ficha da lua passou a
 * exigir massa e composição: o arquivo misturava duas coisas com ciclos de vida
 * diferentes — os 9 corpos são fixos e têm gesto próprio, as luas são um
 * catálogo que cresce.
 *
 * Os corpos principais continuam lá; `planetas.js` importa daqui e faz a fusão
 * (a Lua da Terra vive em CORPOS, porque tem gesto próprio, mas precisa
 * aparecer também na listagem de luas). O sentido do import é este de
 * propósito: `luas.js` não conhece `planetas.js`, então não há ciclo.
 *
 * Dados astronômicos: NASA Planetary Fact Sheet e JPL Solar System Dynamics.
 *
 * ATENÇÃO à escala: `raioOrbitaPx` é VISUAL, não proporcional. Em escala real
 * Calisto ficaria a 26 raios de Júpiter e Fobos a 1,4 raios de Marte — as luas
 * internas sumiriam dentro do planeta. O que preservamos é a ordem e o
 * espaçamento relativo dentro de cada sistema.
 */

/**
 * Satélite secundário: aparece na cena e tem ficha, mas não tem gesto próprio.
 *
 * Os gestos vão de 0 a 10 e todos já estão ocupados (0-8 Sol e planetas, 9 Lua,
 * 10 visão geral). Estas luas são alcançadas pelo MODO LUA: uma mão em "L" mais
 * o número da outra mão.
 */
export const LUAS_MENORES = [
  // --- Marte ---
  { nome: "Fobos", planeta: "Marte", diametroKm: 22.5, distanciaKm: 9376, periodoOrbitalDias: 0.319, raioOrbitaPx: 2.2, cor: [150, 140, 130], faseInicial: 0, fatoCurioso: "Está tão perto de Marte que nasce a oeste e se põe a leste.", massaKg: 1.0659e+16, composicao: "Rocha carbonácea porosa, coberta por poeira e sulcos" },
  { nome: "Deimos", planeta: "Marte", diametroKm: 12.4, distanciaKm: 23463, periodoOrbitalDias: 1.263, raioOrbitaPx: 3.2, cor: [170, 158, 145], faseInicial: 2.1, fatoCurioso: "A menor lua do Sistema Solar entre as bem conhecidas.", massaKg: 1.4762e+15, composicao: "Rocha carbonácea sob um manto espesso de regolito" },
  // --- Júpiter ---
  { nome: "Amalteia", planeta: "Júpiter", diametroKm: 167, distanciaKm: 181366, periodoOrbitalDias: 0.498, raioOrbitaPx: 1.7, cor: [196, 120, 96], faseInicial: 1.1, fatoCurioso: "É avermelhada e tem formato irregular, como uma batata.", massaKg: 2.08e+18, composicao: "Gelo poroso tingido de enxofre vindo de Io" },
  { nome: "Io", planeta: "Júpiter", diametroKm: 3643, distanciaKm: 421700, periodoOrbitalDias: 1.769, raioOrbitaPx: 2.1, cor: [232, 214, 120], faseInicial: 0.4, fatoCurioso: "O corpo com mais atividade vulcânica do Sistema Solar.", massaKg: 8.9319e+22, composicao: "Silicatos e enxofre; núcleo de ferro, sem gelo" },
  { nome: "Europa", planeta: "Júpiter", diametroKm: 3122, distanciaKm: 671034, periodoOrbitalDias: 3.551, raioOrbitaPx: 2.6, cor: [216, 206, 190], faseInicial: 2, fatoCurioso: "Sob a crosta de gelo há um oceano de água líquida.", massaKg: 4.7998e+22, composicao: "Crosta de gelo de água sobre oceano salgado e manto rochoso" },
  { nome: "Ganimedes", planeta: "Júpiter", diametroKm: 5268, distanciaKm: 1070412, periodoOrbitalDias: 7.155, raioOrbitaPx: 3.2, cor: [168, 156, 140], faseInicial: 3.7, fatoCurioso: "É a maior lua do Sistema Solar — maior que Mercúrio.", massaKg: 1.4819e+23, composicao: "Gelo e silicatos; núcleo de ferro com campo magnético próprio" },
  { nome: "Calisto", planeta: "Júpiter", diametroKm: 4821, distanciaKm: 1882709, periodoOrbitalDias: 16.689, raioOrbitaPx: 4, cor: [128, 118, 108], faseInicial: 5.2, fatoCurioso: "A superfície mais craterada que se conhece.", massaKg: 1.0759e+23, composicao: "Mistura homogênea de gelo e rocha, sem diferenciação" },
  // --- Saturno ---
  { nome: "Encélado", planeta: "Saturno", diametroKm: 504, distanciaKm: 237948, periodoOrbitalDias: 1.37, raioOrbitaPx: 1.8, cor: [236, 240, 244], faseInicial: 4.4, fatoCurioso: "Lança gêiseres de água pelo polo sul.", massaKg: 1.0802e+20, composicao: "Gelo de água quase puro sobre oceano subsuperficial" },
  { nome: "Dione", planeta: "Saturno", diametroKm: 1123, distanciaKm: 377396, periodoOrbitalDias: 2.737, raioOrbitaPx: 2.2, cor: [206, 204, 198], faseInicial: 1.9, fatoCurioso: "Tem penhascos de gelo que chegam a centenas de metros.", massaKg: 1.0955e+21, composicao: "Gelo de água com núcleo de silicatos" },
  { nome: "Reia", planeta: "Saturno", diametroKm: 1527, distanciaKm: 527108, periodoOrbitalDias: 4.518, raioOrbitaPx: 2.7, cor: [194, 192, 186], faseInicial: 3.1, fatoCurioso: "A segunda maior lua de Saturno, feita quase toda de gelo.", massaKg: 2.3065e+21, composicao: "Cerca de três quartos de gelo de água e um quarto de rocha" },
  { nome: "Titã", planeta: "Saturno", diametroKm: 5150, distanciaKm: 1221870, periodoOrbitalDias: 15.945, raioOrbitaPx: 3.3, cor: [214, 168, 92], faseInicial: 1.2, fatoCurioso: "Tem atmosfera densa e rios de metano líquido.", massaKg: 1.3452e+23, composicao: "Gelo e rocha sob atmosfera espessa de nitrogênio e metano" },
  { nome: "Jápeto", planeta: "Saturno", diametroKm: 1469, distanciaKm: 3560820, periodoOrbitalDias: 79.33, raioOrbitaPx: 4.1, cor: [150, 140, 126], faseInicial: 5.6, fatoCurioso: "Um hemisfério é escuro como carvão e o outro, branco como neve.", massaKg: 1.8056e+21, composicao: "Gelo de água com depósito escuro de compostos orgânicos" },
  // --- Urano ---
  { nome: "Miranda", planeta: "Urano", diametroKm: 472, distanciaKm: 129900, periodoOrbitalDias: 1.413, raioOrbitaPx: 1.8, cor: [188, 190, 192], faseInicial: 2.7, fatoCurioso: "Tem um penhasco de 20 km, o mais alto conhecido.", massaKg: 6.59e+19, composicao: "Gelo de água e silicatos, com terreno remendado" },
  { nome: "Ariel", planeta: "Urano", diametroKm: 1158, distanciaKm: 190900, periodoOrbitalDias: 2.52, raioOrbitaPx: 2.2, cor: [198, 196, 190], faseInicial: 0.5, fatoCurioso: "A superfície mais clara e jovem entre as luas de Urano.", massaKg: 1.353e+21, composicao: "Gelo de água e dióxido de carbono sobre rocha" },
  { nome: "Umbriel", planeta: "Urano", diametroKm: 1169, distanciaKm: 266000, periodoOrbitalDias: 4.144, raioOrbitaPx: 2.6, cor: [132, 130, 128], faseInicial: 4, fatoCurioso: "A mais escura das grandes luas de Urano.", massaKg: 1.172e+21, composicao: "Gelo escurecido por material carbonáceo antigo" },
  { nome: "Titânia", planeta: "Urano", diametroKm: 1578, distanciaKm: 435910, periodoOrbitalDias: 8.706, raioOrbitaPx: 3.1, cor: [176, 166, 158], faseInicial: 0.9, fatoCurioso: "A maior lua de Urano, com cânions de centenas de quilômetros.", massaKg: 3.527e+21, composicao: "Metade gelo de água, metade rocha; traços de CO2" },
  { nome: "Oberon", planeta: "Urano", diametroKm: 1523, distanciaKm: 583520, periodoOrbitalDias: 13.463, raioOrbitaPx: 3.7, cor: [150, 142, 136], faseInicial: 3.4, fatoCurioso: "A mais externa das grandes luas de Urano.", massaKg: 3.014e+21, composicao: "Gelo de água e rocha, com crateras de fundo escuro" },
  // --- Netuno ---
  { nome: "Galateia", planeta: "Netuno", diametroKm: 176, distanciaKm: 61953, periodoOrbitalDias: 0.429, raioOrbitaPx: 1.7, cor: [160, 168, 176], faseInicial: 3, fatoCurioso: "Sua gravidade mantém um dos anéis de Netuno agrupado.", massaKg: 2.12e+18, composicao: "Gelo escuro e poroso, de formato irregular" },
  { nome: "Larissa", planeta: "Netuno", diametroKm: 194, distanciaKm: 73548, periodoOrbitalDias: 0.555, raioOrbitaPx: 2, cor: [172, 178, 184], faseInicial: 5, fatoCurioso: "Tem forma irregular e superfície muito craterada.", massaKg: 4.2e+18, composicao: "Gelo de água misturado a material rochoso escuro" },
  { nome: "Proteu", planeta: "Netuno", diametroKm: 420, distanciaKm: 117647, periodoOrbitalDias: 1.122, raioOrbitaPx: 2.4, cor: [150, 156, 162], faseInicial: 0.7, fatoCurioso: "É quase o maior corpo que a gravidade não conseguiu arredondar.", massaKg: 4.4e+19, composicao: "Gelo de água sob superfície muito escura e porosa" },
  { nome: "Tritão", planeta: "Netuno", diametroKm: 2707, distanciaKm: 354759, periodoOrbitalDias: -5.877, raioOrbitaPx: 2.9, cor: [198, 206, 210], faseInicial: 1.7, fatoCurioso: "Orbita ao contrário: foi capturado, não se formou ali.", massaKg: 2.14e+22, composicao: "Gelo de nitrogênio e metano sobre manto de água e rocha" },
  { nome: "Nereida", planeta: "Netuno", diametroKm: 340, distanciaKm: 5513400, periodoOrbitalDias: 360.13, raioOrbitaPx: 3.8, cor: [166, 170, 174], faseInicial: 4.2, fatoCurioso: "Tem a órbita mais alongada entre as luas conhecidas.", massaKg: 3.1e+19, composicao: "Gelo de água com superfície irregular e pouco refletiva" },
];

/** Raio médio em km. A ficha mostra raio; o catálogo guarda diâmetro. */
export function raioKm(lua) {
  return lua.diametroKm / 2;
}

/** True quando a lua orbita no sentido contrário ao giro do planeta. */
export function retrograda(lua) {
  return lua.periodoOrbitalDias < 0;
}

/**
 * Agrupa as luas por nome do planeta-pai, preservando a ordem do catálogo.
 *
 * A ordem importa: é ela que numera as luas no HUD e no gesto. As entradas de
 * cada planeta já estão listadas da mais interna para a mais externa, que é a
 * ordem que o usuário vê na tela.
 */
export function indexarPorPlaneta(luas) {
  return luas.reduce((mapa, lua) => {
    (mapa[lua.planeta] ??= []).push(lua);
    return mapa;
  }, {});
}
