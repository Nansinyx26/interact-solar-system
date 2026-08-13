/**
 * Cinemática da cena: onde cada corpo está em um dado instante.
 *
 * Órbitas circulares e coplanares (simplificação deliberada). O que é fiel são
 * as proporções entre os períodos: um ano de Netuno continua durando ~165 anos
 * terrestres.
 */

import {
  EXPOENTE_RAIO_CORPO,
  FATOR_ROTACAO_PROPRIA,
  RAIO_ORBITA_MAX_PX,
  RAIO_ORBITA_MIN_PX,
  RAIO_PLANETA_BASE_PX,
  RAIO_SOL_PX,
} from "../config.js";
import {
  CORPOS,
  DIAMETRO_REFERENCIA_KM,
  DISTANCIA_UA_MAXIMA,
  DISTANCIA_UA_MINIMA,
  ehSol,
} from "../dados/planetas.js";

const LN_UA_MIN = Math.log(DISTANCIA_UA_MINIMA);
const LN_UA_MAX = Math.log(DISTANCIA_UA_MAXIMA);

/**
 * Converte distância média (UA) em raio orbital de mundo.
 * Compressão logarítmica: em escala linear Mercúrio ficaria a 1,3% do raio de
 * Netuno e sumiria dentro do Sol.
 */
export function raioOrbitalPx(distanciaUa) {
  if (distanciaUa <= 0) return 0;
  const fracao = (Math.log(distanciaUa) - LN_UA_MIN) / (LN_UA_MAX - LN_UA_MIN);
  return RAIO_ORBITA_MIN_PX + fracao * (RAIO_ORBITA_MAX_PX - RAIO_ORBITA_MIN_PX);
}

/**
 * Raio desenhado do corpo, em unidades de mundo. Lei de potência com expoente
 * menor que 1: sem ela, ou Mercúrio vira 1 px ou Júpiter ocupa meia tela.
 */
export function raioCorpoPx(corpo) {
  if (ehSol(corpo)) return RAIO_SOL_PX;
  const razao = corpo.diametroKm / DIAMETRO_REFERENCIA_KM;
  return RAIO_PLANETA_BASE_PX * razao ** EXPOENTE_RAIO_CORPO;
}

/** Ângulo orbital (radianos) do corpo no instante simulado informado. */
export function anguloOrbital(corpo, tempoDias) {
  if (corpo.periodoOrbitalDias <= 0) return corpo.faseInicial;
  return corpo.faseInicial + 2 * Math.PI * (tempoDias / corpo.periodoOrbitalDias);
}

/** Posição {x, y} do corpo em unidades de mundo, com o Sol na origem. */
export function posicaoOrbital(corpo, tempoDias) {
  const raio = raioOrbitalPx(corpo.distanciaUa);
  if (raio === 0) return { x: 0, y: 0 };
  const angulo = anguloOrbital(corpo, tempoDias);
  return { x: raio * Math.cos(angulo), y: raio * Math.sin(angulo) };
}

/** Posição de todos os corpos no instante informado, indexada pelo nome. */
export function posicoesDoSistema(tempoDias) {
  const posicoes = new Map();
  for (const corpo of CORPOS) posicoes.set(corpo.nome, posicaoOrbital(corpo, tempoDias));
  return posicoes;
}

/**
 * Fase da rotação própria, normalizada em [0, 1). O sinal do período é
 * preservado (Vênus e Urano giram ao contrário) e a velocidade é comprimida.
 */
export function faseRotacao(corpo, tempoDias) {
  if (corpo.periodoRotacaoHoras === 0) return 0;
  const periodoDias = corpo.periodoRotacaoHoras / 24;
  const voltas = (tempoDias * FATOR_ROTACAO_PROPRIA) / periodoDias;
  return ((voltas % 1) + 1) % 1;
}

/** Ângulo (radianos) da direção Sol -> corpo, usado para o terminador. */
export function anguloIluminacao(posicao) {
  if (posicao.x === 0 && posicao.y === 0) return 0;
  return Math.atan2(posicao.y, posicao.x);
}
