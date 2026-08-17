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
 *
 * `corClara` e `corEscura` formam a paleta de SUPERFÍCIE usada pelo sprite
 * esférico do renderizador — `cor` sozinha só rendia um disco chapado. Com o
 * terreno claro e o escuro a lua ganha manchas, e é isso que separa Jápeto
 * (hemisférios opostos) de Reia (gelo uniforme), que na cor média são quase o
 * mesmo cinza. As duas são OPCIONAIS: sem elas o renderizador deriva um par
 * plausível clareando/escurecendo a base.
 *
 * As cores saem da aparência REAL de cada lua (mosaicos Voyager/Galileo/Cassini
 * em cor aproximadamente natural), não de um cinza genérico com variação: antes
 * 14 das 22 luas caíam na mesma faixa de cinza claro e a cena não distinguia
 * Encélado (o corpo mais refletivo do Sistema Solar, albedo ~0,99) de Umbriel
 * (o mais escuro das grandes luas de Urano, albedo ~0,21).
 */
export const LUAS_MENORES = [
  // --- Marte ---
  { nome: "Fobos", planeta: "Marte", diametroKm: 22.5, distanciaKm: 9376, periodoOrbitalDias: 0.319, raioOrbitaPx: 2.2, cor: [124, 114, 106], corClara: [166, 154, 142], corEscura: [78, 71, 65], faseInicial: 0, fatoCurioso: "Está tão perto de Marte que nasce a oeste e se põe a leste.", massaKg: 1.0659e+16, composicao: "Rocha carbonácea porosa, coberta por poeira e sulcos" },
  { nome: "Deimos", planeta: "Marte", diametroKm: 12.4, distanciaKm: 23463, periodoOrbitalDias: 1.263, raioOrbitaPx: 3.2, cor: [146, 134, 122], corClara: [186, 173, 158], corEscura: [96, 88, 80], faseInicial: 2.1, fatoCurioso: "A menor lua do Sistema Solar entre as bem conhecidas.", massaKg: 1.4762e+15, composicao: "Rocha carbonácea sob um manto espesso de regolito" },
  // --- Júpiter ---
  { nome: "Amalteia", planeta: "Júpiter", diametroKm: 167, distanciaKm: 181366, periodoOrbitalDias: 0.498, raioOrbitaPx: 1.7, cor: [186, 102, 82], corClara: [228, 150, 120], corEscura: [118, 56, 44], faseInicial: 1.1, fatoCurioso: "É avermelhada e tem formato irregular, como uma batata.", massaKg: 2.08e+18, composicao: "Gelo poroso tingido de enxofre vindo de Io" },
  // Enxofre: amarelo pálido nas planícies, laranja nos depósitos vulcânicos frescos.
  { nome: "Io", planeta: "Júpiter", diametroKm: 3643, distanciaKm: 421700, periodoOrbitalDias: 1.769, raioOrbitaPx: 2.1, cor: [234, 202, 104], corClara: [252, 240, 190], corEscura: [188, 124, 44], faseInicial: 0.4, fatoCurioso: "O corpo com mais atividade vulcânica do Sistema Solar.", massaKg: 8.9319e+22, composicao: "Silicatos e enxofre; núcleo de ferro, sem gelo" },
  // Gelo quase branco riscado pelas lineae avermelhadas.
  { nome: "Europa", planeta: "Júpiter", diametroKm: 3122, distanciaKm: 671034, periodoOrbitalDias: 3.551, raioOrbitaPx: 2.6, cor: [226, 216, 198], corClara: [248, 246, 240], corEscura: [170, 146, 124], faseInicial: 2, fatoCurioso: "Sob a crosta de gelo há um oceano de água líquida.", massaKg: 4.7998e+22, composicao: "Crosta de gelo de água sobre oceano salgado e manto rochoso" },
  { nome: "Ganimedes", planeta: "Júpiter", diametroKm: 5268, distanciaKm: 1070412, periodoOrbitalDias: 7.155, raioOrbitaPx: 3.2, cor: [162, 152, 140], corClara: [204, 196, 186], corEscura: [104, 96, 90], faseInicial: 3.7, fatoCurioso: "É a maior lua do Sistema Solar — maior que Mercúrio.", massaKg: 1.4819e+23, composicao: "Gelo e silicatos; núcleo de ferro com campo magnético próprio" },
  { nome: "Calisto", planeta: "Júpiter", diametroKm: 4821, distanciaKm: 1882709, periodoOrbitalDias: 16.689, raioOrbitaPx: 4, cor: [116, 106, 98], corClara: [158, 148, 138], corEscura: [70, 63, 58], faseInicial: 5.2, fatoCurioso: "A superfície mais craterada que se conhece.", massaKg: 1.0759e+23, composicao: "Mistura homogênea de gelo e rocha, sem diferenciação" },
  // --- Saturno ---
  // Albedo ~0,99: a lua tem de sair da tela como a mais branca de todas.
  { nome: "Encélado", planeta: "Saturno", diametroKm: 504, distanciaKm: 237948, periodoOrbitalDias: 1.37, raioOrbitaPx: 1.8, cor: [240, 246, 250], corClara: [255, 255, 255], corEscura: [192, 206, 220], faseInicial: 4.4, fatoCurioso: "Lança gêiseres de água pelo polo sul.", massaKg: 1.0802e+20, composicao: "Gelo de água quase puro sobre oceano subsuperficial" },
  { nome: "Dione", planeta: "Saturno", diametroKm: 1123, distanciaKm: 377396, periodoOrbitalDias: 2.737, raioOrbitaPx: 2.2, cor: [204, 202, 196], corClara: [240, 240, 238], corEscura: [146, 144, 140], faseInicial: 1.9, fatoCurioso: "Tem penhascos de gelo que chegam a centenas de metros.", massaKg: 1.0955e+21, composicao: "Gelo de água com núcleo de silicatos" },
  { nome: "Reia", planeta: "Saturno", diametroKm: 1527, distanciaKm: 527108, periodoOrbitalDias: 4.518, raioOrbitaPx: 2.7, cor: [196, 194, 188], corClara: [234, 234, 232], corEscura: [140, 138, 134], faseInicial: 3.1, fatoCurioso: "A segunda maior lua de Saturno, feita quase toda de gelo.", massaKg: 2.3065e+21, composicao: "Cerca de três quartos de gelo de água e um quarto de rocha" },
  // A névoa de tholins fecha a superfície: laranja em todo o disco.
  { nome: "Titã", planeta: "Saturno", diametroKm: 5150, distanciaKm: 1221870, periodoOrbitalDias: 15.945, raioOrbitaPx: 3.3, cor: [222, 166, 78], corClara: [248, 210, 138], corEscura: [168, 104, 36], faseInicial: 1.2, fatoCurioso: "Tem atmosfera densa e rios de metano líquido.", massaKg: 1.3452e+23, composicao: "Gelo e rocha sob atmosfera espessa de nitrogênio e metano" },
  // O contraste extremo do par é o ponto: é a única lua em que os dois tons são
  // material diferente, não relevo.
  { nome: "Jápeto", planeta: "Saturno", diametroKm: 1469, distanciaKm: 3560820, periodoOrbitalDias: 79.33, raioOrbitaPx: 4.1, cor: [152, 142, 128], corClara: [228, 222, 212], corEscura: [58, 48, 40], faseInicial: 5.6, fatoCurioso: "Um hemisfério é escuro como carvão e o outro, branco como neve.", massaKg: 1.8056e+21, composicao: "Gelo de água com depósito escuro de compostos orgânicos" },
  // --- Urano ---
  { nome: "Miranda", planeta: "Urano", diametroKm: 472, distanciaKm: 129900, periodoOrbitalDias: 1.413, raioOrbitaPx: 1.8, cor: [186, 188, 192], corClara: [226, 228, 232], corEscura: [128, 130, 136], faseInicial: 2.7, fatoCurioso: "Tem um penhasco de 20 km, o mais alto conhecido.", massaKg: 6.59e+19, composicao: "Gelo de água e silicatos, com terreno remendado" },
  { nome: "Ariel", planeta: "Urano", diametroKm: 1158, distanciaKm: 190900, periodoOrbitalDias: 2.52, raioOrbitaPx: 2.2, cor: [204, 204, 200], corClara: [240, 242, 240], corEscura: [148, 150, 150], faseInicial: 0.5, fatoCurioso: "A superfície mais clara e jovem entre as luas de Urano.", massaKg: 1.353e+21, composicao: "Gelo de água e dióxido de carbono sobre rocha" },
  // Quase sem variação: a superfície é uniformemente escura.
  { nome: "Umbriel", planeta: "Urano", diametroKm: 1169, distanciaKm: 266000, periodoOrbitalDias: 4.144, raioOrbitaPx: 2.6, cor: [122, 120, 118], corClara: [156, 155, 154], corEscura: [78, 77, 76], faseInicial: 4, fatoCurioso: "A mais escura das grandes luas de Urano.", massaKg: 1.172e+21, composicao: "Gelo escurecido por material carbonáceo antigo" },
  { nome: "Titânia", planeta: "Urano", diametroKm: 1578, distanciaKm: 435910, periodoOrbitalDias: 8.706, raioOrbitaPx: 3.1, cor: [178, 168, 158], corClara: [216, 208, 200], corEscura: [120, 112, 105], faseInicial: 0.9, fatoCurioso: "A maior lua de Urano, com cânions de centenas de quilômetros.", massaKg: 3.527e+21, composicao: "Metade gelo de água, metade rocha; traços de CO2" },
  { nome: "Oberon", planeta: "Urano", diametroKm: 1523, distanciaKm: 583520, periodoOrbitalDias: 13.463, raioOrbitaPx: 3.7, cor: [154, 144, 136], corClara: [194, 186, 178], corEscura: [98, 90, 85], faseInicial: 3.4, fatoCurioso: "A mais externa das grandes luas de Urano.", massaKg: 3.014e+21, composicao: "Gelo de água e rocha, com crateras de fundo escuro" },
  // --- Netuno ---
  { nome: "Galateia", planeta: "Netuno", diametroKm: 176, distanciaKm: 61953, periodoOrbitalDias: 0.429, raioOrbitaPx: 1.7, cor: [140, 148, 158], corClara: [180, 188, 198], corEscura: [92, 98, 106], faseInicial: 3, fatoCurioso: "Sua gravidade mantém um dos anéis de Netuno agrupado.", massaKg: 2.12e+18, composicao: "Gelo escuro e poroso, de formato irregular" },
  { nome: "Larissa", planeta: "Netuno", diametroKm: 194, distanciaKm: 73548, periodoOrbitalDias: 0.555, raioOrbitaPx: 2, cor: [158, 164, 172], corClara: [196, 202, 210], corEscura: [106, 111, 118], faseInicial: 5, fatoCurioso: "Tem forma irregular e superfície muito craterada.", massaKg: 4.2e+18, composicao: "Gelo de água misturado a material rochoso escuro" },
  { nome: "Proteu", planeta: "Netuno", diametroKm: 420, distanciaKm: 117647, periodoOrbitalDias: 1.122, raioOrbitaPx: 2.4, cor: [134, 140, 148], corClara: [172, 178, 186], corEscura: [88, 93, 99], faseInicial: 0.7, fatoCurioso: "É quase o maior corpo que a gravidade não conseguiu arredondar.", massaKg: 4.4e+19, composicao: "Gelo de água sob superfície muito escura e porosa" },
  // Gelo de nitrogênio rosado pelos tholins da calota sul.
  { nome: "Tritão", planeta: "Netuno", diametroKm: 2707, distanciaKm: 354759, periodoOrbitalDias: -5.877, raioOrbitaPx: 2.9, cor: [224, 208, 200], corClara: [250, 244, 240], corEscura: [172, 140, 132], faseInicial: 1.7, fatoCurioso: "Orbita ao contrário: foi capturado, não se formou ali.", massaKg: 2.14e+22, composicao: "Gelo de nitrogênio e metano sobre manto de água e rocha" },
  { nome: "Nereida", planeta: "Netuno", diametroKm: 340, distanciaKm: 5513400, periodoOrbitalDias: 360.13, raioOrbitaPx: 3.8, cor: [158, 162, 168], corClara: [194, 198, 204], corEscura: [108, 112, 118], faseInicial: 4.2, fatoCurioso: "Tem a órbita mais alongada entre as luas conhecidas.", massaKg: 3.1e+19, composicao: "Gelo de água com superfície irregular e pouco refletiva" },
];

/** Raio médio em km. A ficha mostra raio; o catálogo guarda diâmetro. */
export function raioKm(lua) {
  return lua.diametroKm / 2;
}

/** Interpola duas cores. Só serve aos padrões de `realce`/`sombra`. */
function misturar(cor, alvo, peso) {
  return [
    Math.round(cor[0] + (alvo[0] - cor[0]) * peso),
    Math.round(cor[1] + (alvo[1] - cor[1]) * peso),
    Math.round(cor[2] + (alvo[2] - cor[2]) * peso),
  ];
}

/** Tom claro do terreno (cristas, gelo fresco, calotas). */
export function realce(lua) {
  return lua.corClara ?? misturar(lua.cor, [255, 255, 255], 0.34);
}

/** Tom escuro do terreno (bacias, regolito, depósitos orgânicos). */
export function sombra(lua) {
  return lua.corEscura ?? misturar(lua.cor, [0, 0, 0], 0.45);
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
