/**
 * Catálogo dos 9 corpos celestes (Sol + 8 planetas).
 *
 * Dados médios do NASA Planetary Fact Sheet. Mesmo conteúdo do dados/planetas.py
 * do aplicativo desktop.
 */

/** @typedef {typeof CORPOS[number]} CorpoCeleste */

export const CORPOS = [
  {
    nome: "Sol",
    indiceGesto: 0,
    tipo: "estrela",
    diametroKm: 1392700,
    distanciaUa: 0,
    distanciaKm: 0,
    periodoOrbitalDias: 0,
    periodoRotacaoHoras: 609.12, // ~25,38 dias no equador
    luas: 0,
    temperaturaMediaC: 5505, // superfície (fotosfera)
    inclinacaoAxialGraus: 7.25,
    fatoCurioso: "Concentra 99,86% de toda a massa do Sistema Solar.",
    corBase: [255, 214, 96],
    corSecundaria: [255, 148, 32],
    corDetalhe: [255, 252, 226],
    corTempestade: null,
    faixas: false,
    manchas: true, // granulação da fotosfera
    faseInicial: 0,
  },
  {
    nome: "Mercúrio",
    indiceGesto: 1,
    tipo: "rochoso",
    diametroKm: 4879,
    distanciaUa: 0.387,
    distanciaKm: 57900000,
    periodoOrbitalDias: 87.97,
    periodoRotacaoHoras: 1407.6,
    luas: 0,
    temperaturaMediaC: 167,
    inclinacaoAxialGraus: 0.03,
    fatoCurioso: "Um dia solar ali dura dois anos mercurianos.",
    corBase: [154, 148, 141],
    corSecundaria: [104, 99, 95],
    corDetalhe: [188, 183, 175],
    corTempestade: null,
    faixas: false,
    manchas: true,
    faseInicial: 0.6,
  },
  {
    nome: "Vênus",
    indiceGesto: 2,
    tipo: "rochoso",
    diametroKm: 12104,
    distanciaUa: 0.723,
    distanciaKm: 108200000,
    periodoOrbitalDias: 224.7,
    periodoRotacaoHoras: -5832.5, // retrógrada
    luas: 0,
    temperaturaMediaC: 464,
    inclinacaoAxialGraus: 177.36,
    fatoCurioso: "Gira ao contrário e é o planeta mais quente, não Mercúrio.",
    corBase: [226, 188, 124],
    corSecundaria: [184, 140, 78],
    corDetalhe: [246, 226, 178],
    corTempestade: null,
    faixas: true,
    manchas: false,
    faseInicial: 2.4,
  },
  {
    nome: "Terra",
    indiceGesto: 3,
    tipo: "rochoso",
    diametroKm: 12756,
    distanciaUa: 1,
    distanciaKm: 149600000,
    periodoOrbitalDias: 365.26,
    periodoRotacaoHoras: 23.93,
    luas: 1,
    temperaturaMediaC: 15,
    inclinacaoAxialGraus: 23.44,
    fatoCurioso: "Único mundo conhecido com água líquida estável na superfície.",
    corBase: [48, 104, 196],
    corSecundaria: [66, 142, 84],
    corDetalhe: [238, 244, 252],
    corTempestade: null,
    faixas: false,
    manchas: true,
    faseInicial: 4.1,
  },
  {
    nome: "Marte",
    indiceGesto: 4,
    tipo: "rochoso",
    diametroKm: 6792,
    distanciaUa: 1.524,
    distanciaKm: 227900000,
    periodoOrbitalDias: 686.98,
    periodoRotacaoHoras: 24.62,
    luas: 2,
    temperaturaMediaC: -65,
    inclinacaoAxialGraus: 25.19,
    fatoCurioso: "Abriga o Olympus Mons, vulcão de ~22 km — o maior conhecido.",
    corBase: [191, 88, 54],
    corSecundaria: [138, 58, 40],
    corDetalhe: [233, 168, 130],
    corTempestade: null,
    faixas: false,
    manchas: true,
    faseInicial: 1.3,
  },
  {
    nome: "Júpiter",
    indiceGesto: 5,
    tipo: "gasoso",
    diametroKm: 142984,
    distanciaUa: 5.204,
    distanciaKm: 778600000,
    periodoOrbitalDias: 4332.59,
    periodoRotacaoHoras: 9.93,
    luas: 95,
    temperaturaMediaC: -110,
    inclinacaoAxialGraus: 3.13,
    fatoCurioso: "A Grande Mancha Vermelha é uma tempestade maior que a Terra.",
    corBase: [214, 178, 138],
    corSecundaria: [158, 112, 78],
    corDetalhe: [242, 224, 200],
    corTempestade: [198, 96, 64],
    faixas: true,
    manchas: true,
    faseInicial: 5.5,
  },
  {
    nome: "Saturno",
    indiceGesto: 6,
    tipo: "gasoso",
    diametroKm: 120536,
    distanciaUa: 9.583,
    distanciaKm: 1433500000,
    periodoOrbitalDias: 10759.22,
    periodoRotacaoHoras: 10.66,
    luas: 146,
    temperaturaMediaC: -140,
    inclinacaoAxialGraus: 26.73,
    fatoCurioso: "Sua densidade é menor que a da água: flutuaria numa banheira.",
    corBase: [228, 205, 152],
    corSecundaria: [182, 152, 104],
    corDetalhe: [248, 236, 206],
    corTempestade: null,
    faixas: true,
    manchas: false,
    temAneis: true,
    faseInicial: 3,
  },
  {
    nome: "Urano",
    indiceGesto: 7,
    tipo: "gasoso",
    diametroKm: 51118,
    distanciaUa: 19.191,
    distanciaKm: 2872500000,
    periodoOrbitalDias: 30685.4,
    periodoRotacaoHoras: -17.24, // retrógrada
    luas: 28,
    temperaturaMediaC: -195,
    inclinacaoAxialGraus: 97.77,
    fatoCurioso: "Gira praticamente deitado: seu eixo aponta quase para o Sol.",
    corBase: [146, 214, 220],
    corSecundaria: [102, 176, 194],
    corDetalhe: [206, 240, 244],
    corTempestade: null,
    faixas: true,
    manchas: false,
    faseInicial: 0.9,
  },
  {
    nome: "Netuno",
    indiceGesto: 8,
    tipo: "gasoso",
    diametroKm: 49528,
    distanciaUa: 30.07,
    distanciaKm: 4495100000,
    periodoOrbitalDias: 60189,
    periodoRotacaoHoras: 16.11,
    luas: 16,
    temperaturaMediaC: -200,
    inclinacaoAxialGraus: 28.32,
    fatoCurioso: "Tem os ventos mais rápidos do Sistema Solar: até 2.100 km/h.",
    corBase: [58, 96, 214],
    corSecundaria: [34, 62, 158],
    corDetalhe: [160, 196, 250],
    corTempestade: [24, 40, 122],
    faixas: true,
    manchas: true,
    faseInicial: 2,
  },
  {
    nome: "Lua",
    indiceGesto: 9,
    tipo: "satelite",
    diametroKm: 3474,
    distanciaUa: 0,        // não orbita o Sol diretamente
    distanciaKm: 384400,   // distância média à Terra
    periodoOrbitalDias: 27.32,
    periodoRotacaoHoras: 655.73, // síncrona (= período orbital)
    luas: 0,
    temperaturaMediaC: -20,
    inclinacaoAxialGraus: 6.68,
    fatoCurioso: "É o único outro mundo que a humanidade já pisou.",
    corBase: [180, 180, 178],
    corSecundaria: [120, 118, 114],
    corDetalhe: [210, 208, 204],
    corTempestade: null,
    faixas: false,
    manchas: true,
    faseInicial: 0,
    orbitaEmTornoDe: "Terra",
  },
];

/** Índice de gesto -> corpo. Gestos 10 fica de fora de propósito. */
export const CORPOS_POR_GESTO = new Map(CORPOS.map((c) => [c.indiceGesto, c]));

/** Diâmetro de referência da lei de potência de tamanho (a Terra). */
export const DIAMETRO_REFERENCIA_KM = 12756;

export const DISTANCIA_UA_MINIMA = Math.min(
  ...CORPOS.filter((c) => c.distanciaUa > 0).map((c) => c.distanciaUa),
);
export const DISTANCIA_UA_MAXIMA = Math.max(...CORPOS.map((c) => c.distanciaUa));

/** Devolve o corpo mapeado para um número de dedos, ou null se inválido. */
export function corpoPorGesto(numeroDedos) {
  return CORPOS_POR_GESTO.get(numeroDedos) ?? null;
}

/** Indica se o corpo é a estrela central. */
export function ehSol(corpo) {
  return corpo.tipo === "estrela";
}

/** Indica se o corpo é um satélite (orbita outro corpo, não o Sol). */
export function ehSatelite(corpo) {
  return Boolean(corpo.orbitaEmTornoDe);
}

/** Referência rápida à Lua. */
export const LUA = CORPOS.find((c) => c.nome === "Lua");

