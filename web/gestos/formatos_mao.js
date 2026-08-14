/**
 * Classificação da FORMA da mão, além da simples contagem de dedos.
 *
 * Espelha o `gestos/formatos_mao.py` do desktop. Hoje só existe uma forma
 * especial: o **"L"** — polegar e indicador estendidos em ângulo aberto, os
 * outros três fechados. Ele não é um número: é um *modificador* de modo.
 * Enquanto uma mão faz o L, o número mostrado pela outra deixa de significar
 * planeta e passa a significar índice de lua.
 *
 * Isso resolve um limite duro do projeto: a contagem vai de 0 a 10 e todos os
 * valores já estão ocupados (Sol, 8 planetas, Lua e visão geral). Não sobrava
 * número para selecionar luas — mas sobrava *forma*.
 */

import { ANGULO_L_MAXIMO_GRAUS, ANGULO_L_MINIMO_GRAUS } from "../config.js";
import {
  DEDOS_LONGOS,
  INDICADOR_MCP,
  POLEGAR_MCP,
  POLEGAR_PONTA,
  dedoEstendido,
  polegarLevantado,
  referencialDaPalma,
} from "./contador.js";

// Ponta do indicador, para o vetor do dedo.
const INDICADOR_PONTA = DEDOS_LONGOS[0][0];

/** Ângulo em graus entre dois vetores 2D (0 a 180). */
export function anguloEntre(ax, ay, bx, by) {
  const normaA = Math.hypot(ax, ay);
  const normaB = Math.hypot(bx, by);
  if (normaA < 1e-9 || normaB < 1e-9) return 0;
  const cosseno = (ax * bx + ay * by) / (normaA * normaB);
  return (Math.acos(Math.max(-1, Math.min(1, cosseno))) * 180) / Math.PI;
}

/**
 * Ângulo entre o polegar (MCP→ponta) e o indicador (MCP→ponta), em graus.
 *
 * Usa vetores relativos a juntas da própria mão, nunca coordenadas de tela:
 * é isso que faz o "L" ser reconhecido de cabeça para baixo ou espelhado.
 */
export function aberturaDoL(landmarks) {
  const pp = landmarks[POLEGAR_PONTA];
  const pm = landmarks[POLEGAR_MCP];
  const ip = landmarks[INDICADOR_PONTA];
  const im = landmarks[INDICADOR_MCP];
  return anguloEntre(pp.x - pm.x, pp.y - pm.y, ip.x - im.x, ip.y - im.y);
}

/**
 * True quando a mão forma um "L".
 *
 * Três condições, todas necessárias:
 *
 * 1. **Indicador estendido** e **polegar estendido**.
 * 2. **Médio, anelar e mínimo dobrados.** É o que separa o L de uma mão aberta
 *    e, principalmente, do "2" — que também tem dois dedos para cima, mas os
 *    errados (indicador + médio, com o polegar recolhido).
 * 3. **Ângulo entre polegar e indicador entre 50° e 130°.** Sem isso, um gesto
 *    de apontar (dedos quase paralelos) passaria como L.
 *
 * Funciona com qualquer mão e em qualquer rotação: o referencial vem da própria
 * palma, e o ângulo usa vetores relativos.
 */
export function ehFormatoL(landmarks, lado) {
  const { eixoDedos, eixoPolegar, tamanho } = referencialDaPalma(landmarks, lado);

  const [pontaIndicador, pipIndicador] = DEDOS_LONGOS[0];
  if (!dedoEstendido(landmarks, pontaIndicador, pipIndicador, eixoDedos, tamanho)) {
    return false;
  }

  // Os três dedos restantes precisam estar recolhidos.
  for (const [ponta, pip] of DEDOS_LONGOS.slice(1)) {
    if (dedoEstendido(landmarks, ponta, pip, eixoDedos, tamanho)) return false;
  }

  if (!polegarLevantado(landmarks, eixoPolegar, tamanho)) return false;

  const abertura = aberturaDoL(landmarks);
  return abertura >= ANGULO_L_MINIMO_GRAUS && abertura <= ANGULO_L_MAXIMO_GRAUS;
}
