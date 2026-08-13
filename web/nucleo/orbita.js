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
  RAIO_LUA_PX,
  RAIO_ORBITA_LUA_PX,
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
  ehSatelite,
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
  if (ehSatelite(corpo)) return RAIO_LUA_PX;
  const razao = corpo.diametroKm / DIAMETRO_REFERENCIA_KM;
  return RAIO_PLANETA_BASE_PX * razao ** EXPOENTE_RAIO_CORPO;
}

/** Ângulo orbital (radianos) do corpo no instante simulado informado. */
export function anguloOrbital(corpo, tempoDias) {
  if (corpo.periodoOrbitalDias <= 0) return corpo.faseInicial;
  return corpo.faseInicial + 2 * Math.PI * (tempoDias / corpo.periodoOrbitalDias);
}

/**
 * Posição {x, y} do corpo em unidades de mundo, com o Sol na origem.
 * Para satélites, devolve o deslocamento relativo ao corpo-pai (sem somá-lo).
 */
export function posicaoOrbital(corpo, tempoDias) {
  if (ehSatelite(corpo)) {
    // Satélite: órbita ao redor do corpo-pai, não do Sol.
    const angulo = anguloOrbital(corpo, tempoDias);
    return {
      x: RAIO_ORBITA_LUA_PX * Math.cos(angulo),
      y: RAIO_ORBITA_LUA_PX * Math.sin(angulo),
    };
  }
  const raio = raioOrbitalPx(corpo.distanciaUa);
  if (raio === 0) return { x: 0, y: 0 };
  const angulo = anguloOrbital(corpo, tempoDias);
  return { x: raio * Math.cos(angulo), y: raio * Math.sin(angulo) };
}

/**
 * Posição de todos os corpos no instante informado, indexada pelo nome.
 * Planetas são resolvidos primeiro; satélites somam o offset ao corpo-pai.
 */
export function posicoesDoSistema(tempoDias) {
  const posicoes = new Map();
  // Primeiro: corpos que orbitam o Sol (planetas + Sol).
  for (const corpo of CORPOS) {
    if (!ehSatelite(corpo)) {
      posicoes.set(corpo.nome, posicaoOrbital(corpo, tempoDias));
    }
  }
  // Depois: satélites (offset sobre a posição do corpo-pai).
  for (const corpo of CORPOS) {
    if (ehSatelite(corpo)) {
      const pai = posicoes.get(corpo.orbitaEmTornoDe) ?? { x: 0, y: 0 };
      const rel = posicaoOrbital(corpo, tempoDias);
      posicoes.set(corpo.nome, { x: pai.x + rel.x, y: pai.y + rel.y });
    }
  }
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
