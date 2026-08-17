/**
 * Cinemática da cena: onde cada corpo está em um dado instante.
 *
 * Órbitas circulares e coplanares (simplificação deliberada). O que é fiel são
 * as proporções entre os períodos: um ano de Netuno continua durando ~165 anos
 * terrestres.
 */

import {
  CINTURAO_UA_EXTERNO,
  FATOR_ANEL_EXTERNO,
  FATOR_LUA_COMPACTO_MAX,
  FATOR_LUA_COMPACTO_MIN,
  FOLGA_LUA_APOS_ANEL,
  CINTURAO_UA_INTERNO,
  DIAMETRO_LUA_REFERENCIA_KM,
  EXPOENTE_RAIO_CORPO,
  EXPOENTE_PERIODO_LUA,
  EXPOENTE_RAIO_LUA,
  FATOR_ROTACAO_PROPRIA,
  PERIODO_LUA_REFERENCIA_DIAS,
  RAIO_LUA_MENOR_MAX_PX,
  RAIO_LUA_MENOR_MIN_PX,
  RAIO_LUA_MENOR_PX,
  RAIO_LUA_PX,
  RAIO_ORBITA_LUA_PX,
  RAIO_ORBITA_MAX_PX,
  RAIO_ORBITA_MIN_PX,
  PERIODO_CINTURAO_DIAS,
  RAIO_PLANETA_BASE_PX,
  RAIO_SOL_PX,
  ZOOM_MINIMO_PARA_LUAS,
  ZOOM_VISAO_GERAL,
} from "../config.js";
import {
  CORPOS,
  LUAS_MENORES,
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

/**
 * Raio DESENHADO de uma lua menor, em unidades de mundo.
 *
 * Mesma lei de potência de `raioCorpoPx`, com a nossa Lua como referência e
 * limites duros nas pontas. Antes toda lua tinha o mesmo raio fixo, o que
 * apagava a única comparação de tamanho que a cena consegue oferecer: Titã e
 * Ganimedes são maiores que Mercúrio, Fobos tem 22 km.
 */
export function raioLuaMenorPx(lua) {
  const razao = Math.abs(lua.diametroKm) / DIAMETRO_LUA_REFERENCIA_KM;
  if (!(razao > 0)) return RAIO_LUA_MENOR_MIN_PX;
  const raio = RAIO_LUA_MENOR_PX * razao ** EXPOENTE_RAIO_LUA;
  return Math.min(RAIO_LUA_MENOR_MAX_PX, Math.max(RAIO_LUA_MENOR_MIN_PX, raio));
}

/**
 * Período que a lua *aparenta* ter na tela, em dias simulados.
 *
 * Na escala padrão passam 12 dias por segundo. Com o período real, Fobos
 * (0,319 dia) daria 37 voltas por segundo — um borrão. Mas também não dá para
 * dividir tudo pelo mesmo número: entre Fobos e Calisto há um fator 52, então
 * o ajuste que salva a mais rápida congela a mais lenta.
 *
 * Por isso a mesma lei de potência usada nos raios: expoente < 1 **comprime a
 * faixa** em vez de deslocá-la. A ordem real é preservada — lua interna ainda
 * gira mais rápido que a externa, que é verdade física — mas o intervalo
 * inteiro cai em 7 a 31 segundos por volta, tempo de ler o nome.
 *
 * O sinal é preservado: Tritão tem período negativo porque orbita Netuno ao
 * contrário, e elevar um negativo a 0,38 daria NaN.
 */
export function periodoAparenteDaLua(periodoRealDias) {
  if (periodoRealDias === 0) return 0;
  const sentido = periodoRealDias > 0 ? 1 : -1;
  const razao = Math.abs(periodoRealDias) ** EXPOENTE_PERIODO_LUA;
  return sentido * PERIODO_LUA_REFERENCIA_DIAS * razao;
}

/** Ângulo orbital (radianos) do corpo no instante simulado informado. */
export function anguloOrbital(corpo, tempoDias) {
  if (corpo.periodoOrbitalDias <= 0) return corpo.faseInicial;
  // A Lua da Terra é satélite e passa pela mesma compressão das luas menores:
  // senão ela sozinha giraria 5x mais rápido que as de Júpiter, ao lado.
  const periodo = ehSatelite(corpo)
    ? periodoAparenteDaLua(corpo.periodoOrbitalDias)
    : corpo.periodoOrbitalDias;
  return corpo.faseInicial + 2 * Math.PI * (tempoDias / periodo);
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

/**
 * Posição de uma lua menor, em unidades de mundo.
 *
 * O raio da órbita é múltiplo do raio DESENHADO do planeta, não da distância
 * real: em escala fiel Fobos ficaria dentro do disco de Marte e Calisto a 26
 * raios de Júpiter, fora da tela em qualquer zoom útil.
 */
export function posicaoDaLuaMenor(lua, posicaoPlaneta, raioPlaneta, tempoDias, fator) {
  const angulo =
    lua.periodoOrbitalDias === 0
      ? lua.faseInicial
      : lua.faseInicial +
        2 * Math.PI * (tempoDias / periodoAparenteDaLua(lua.periodoOrbitalDias));
  const raio = raioPlaneta * (fator ?? lua.raioOrbitaPx);
  return {
    x: posicaoPlaneta.x + raio * Math.cos(angulo),
    y: posicaoPlaneta.y + raio * Math.sin(angulo),
  };
}

/**
 * Raios interno e externo do cinturão de asteroides, em unidades de mundo.
 *
 * Passam pela mesma compressão logarítmica das órbitas, então o cinturão cai
 * exatamente entre Marte e Júpiter na tela — como acontece de verdade.
 */
export function faixaDoCinturao() {
  return [raioOrbitalPx(CINTURAO_UA_INTERNO), raioOrbitalPx(CINTURAO_UA_EXTERNO)];
}

/** Rotação do cinturão inteiro, tratado como um corpo só. */
export function anguloDoCinturao(tempoDias) {
  return 2 * Math.PI * (tempoDias / PERIODO_CINTURAO_DIAS);
}

// Faixa de raios usada no catálogo, para comprimir proporcionalmente: a lua
// mais interna continua sendo a mais interna também no modo compacto.
const FATOR_LUA_MIN = Math.min(...LUAS_MENORES.map((l) => l.raioOrbitaPx));
const FATOR_LUA_MAX = Math.max(...LUAS_MENORES.map((l) => l.raioOrbitaPx));

/**
 * Raio orbital da lua (em raios do planeta), adaptado ao zoom.
 *
 * Na visão geral não há espaço para o raio cheio, então o sistema inteiro é
 * comprimido para um anel colado ao planeta e vai se abrindo conforme a câmera
 * aproxima, até a configuração real a partir de ZOOM_MINIMO_PARA_LUAS.
 *
 * A compressão preserva a ORDEM: a lua mais interna do catálogo continua sendo
 * a mais interna no anel compacto.
 */
export function fatorOrbitaLua(fatorBase, zoom, temAneis = false) {
  const fracao = (fatorBase - FATOR_LUA_MIN) / (FATOR_LUA_MAX - FATOR_LUA_MIN);
  let compacto =
    FATOR_LUA_COMPACTO_MIN + fracao * (FATOR_LUA_COMPACTO_MAX - FATOR_LUA_COMPACTO_MIN);
  if (temAneis) {
    // Sem este deslocamento as luas de Saturno cairiam dentro dos anéis.
    compacto += FATOR_ANEL_EXTERNO + FOLGA_LUA_APOS_ANEL - FATOR_LUA_COMPACTO_MIN;
  }
  // A abertura começa em ZERO no zoom da visão geral — não em zoom zero.
  const faixa = Math.max(1e-6, ZOOM_MINIMO_PARA_LUAS - ZOOM_VISAO_GERAL);
  const abertura = Math.min(1, Math.max(0, (zoom - ZOOM_VISAO_GERAL) / faixa));
  return compacto + (fatorBase - compacto) * abertura;
}
