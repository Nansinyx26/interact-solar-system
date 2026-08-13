/**
 * Conversão de landmarks da mão em número de dedos levantados.
 *
 * A heurística ingênua (comparar o y da ponta com o y da junta PIP) só funciona
 * com a mão em pé. Aqui usamos a versão robusta: montamos um referencial da
 * própria palma e projetamos os dedos nele, o que mantém a contagem correta com
 * a mão girada ou inclinada.
 */

import {
  LIMIAR_DEDO_ESTENDIDO,
  LIMIAR_POLEGAR_ESTENDIDO,
  MARGEM_QUADRO,
  MARGEM_ZONA_CINZENTA_POLEGAR,
  MAX_LANDMARKS_FORA_DO_QUADRO,
  RAZAO_POLEGAR_ABERTO,
  TAMANHO_PALMA_MINIMO,
} from "../config.js";

// Índices dos 21 landmarks do MediaPipe Hands.
const PULSO = 0;
const POLEGAR_MCP = 2;
const POLEGAR_IP = 3;
const POLEGAR_PONTA = 4;
const INDICADOR_MCP = 5;
const MEDIO_MCP = 9;
const MINIMO_MCP = 17;

/** (ponta, PIP) dos quatro dedos longos. */
const DEDOS_LONGOS = [
  [8, 6],
  [12, 10],
  [16, 14],
  [20, 18],
];

/**
 * Indica se a mão está enquadrada o bastante para ser contada.
 *
 * Exigir os 21 pontos dentro de [0, 1] é rígido demais: o modelo extrapola um
 * pouco mesmo com a mão inteira visível, e com as duas mãos no quadro
 * (necessárias para 6, 7 e 8) isso descartava quase tudo. Por isso toleramos
 * alguns pontos fora antes de invalidar a leitura.
 */
export function maoDentroDoQuadro(landmarks) {
  let fora = 0;
  for (const ponto of landmarks) {
    if (
      ponto.x < -MARGEM_QUADRO ||
      ponto.x > 1 + MARGEM_QUADRO ||
      ponto.y < -MARGEM_QUADRO ||
      ponto.y > 1 + MARGEM_QUADRO
    ) {
      fora += 1;
      if (fora > MAX_LANDMARKS_FORA_DO_QUADRO) return false;
    }
  }
  return true;
}

/**
 * Devolve {eixoDedos, eixoPolegar, tamanho} da palma.
 *
 * - eixoDedos: pulso -> MCP do médio, a direção "para cima" da mão em qualquer
 *   rotação.
 * - eixoPolegar: MCP do mínimo -> MCP do indicador. Aponta sempre para o lado do
 *   polegar; por vir da anatomia, já embute o handedness.
 * - tamanho: escala que normaliza os limiares, deixando a contagem independente
 *   da distância até a câmera.
 */
function referencialDaPalma(landmarks, lado) {
  const pulso = landmarks[PULSO];
  const medio = landmarks[MEDIO_MCP];
  const vetorX = medio.x - pulso.x;
  const vetorY = medio.y - pulso.y;
  const tamanho = Math.hypot(vetorX, vetorY);
  if (tamanho < TAMANHO_PALMA_MINIMO) {
    // Palma degenerada (mão exatamente de perfil): eixos neutros.
    return {
      eixoDedos: { x: 0, y: -1 },
      eixoPolegar: { x: 1, y: 0 },
      tamanho: TAMANHO_PALMA_MINIMO,
    };
  }
  const eixoDedos = { x: vetorX / tamanho, y: vetorY / tamanho };

  const indicador = landmarks[INDICADOR_MCP];
  const minimo = landmarks[MINIMO_MCP];
  const lateralX = indicador.x - minimo.x;
  const lateralY = indicador.y - minimo.y;
  const normaLateral = Math.hypot(lateralX, lateralY);
  let eixoPolegar;
  if (normaLateral < TAMANHO_PALMA_MINIMO) {
    // Índice e mínimo colapsados: o único palpite possível sobre o lado do
    // polegar vem do handedness do MediaPipe.
    const sinal = lado === "Right" ? 1 : -1;
    eixoPolegar = { x: sinal * -eixoDedos.y, y: sinal * eixoDedos.x };
  } else {
    eixoPolegar = { x: lateralX / normaLateral, y: lateralY / normaLateral };
  }
  return { eixoDedos, eixoPolegar, tamanho };
}

/**
 * Decide se o polegar está aberto.
 *
 * Critério principal: projetar o vetor MCP -> ponta no eixo lateral da palma.
 * O polegar aberto se afasta para o lado; o fechado cruza a palma. Na faixa
 * ambígua entra o segundo critério: comparar a distância da PONTA e da junta IP
 * até a base do dedo mínimo — abrindo o polegar a ponta se afasta.
 */
function polegarLevantado(landmarks, eixoPolegar, tamanhoPalma) {
  const ponta = landmarks[POLEGAR_PONTA];
  const mcp = landmarks[POLEGAR_MCP];
  const projecao =
    ((ponta.x - mcp.x) * eixoPolegar.x + (ponta.y - mcp.y) * eixoPolegar.y) / tamanhoPalma;

  if (projecao > LIMIAR_POLEGAR_ESTENDIDO + MARGEM_ZONA_CINZENTA_POLEGAR) return true;
  if (projecao < LIMIAR_POLEGAR_ESTENDIDO - MARGEM_ZONA_CINZENTA_POLEGAR) return false;

  const base = landmarks[MINIMO_MCP];
  const ip = landmarks[POLEGAR_IP];
  const distanciaPonta = Math.hypot(ponta.x - base.x, ponta.y - base.y);
  const distanciaIp = Math.hypot(ip.x - base.x, ip.y - base.y);
  return distanciaPonta > distanciaIp * RAZAO_POLEGAR_ABERTO;
}

/** Projeta ponta e junta no eixo da palma para saber se o dedo está aberto. */
function dedoEstendido(landmarks, ponta, pip, eixoDedos, tamanho) {
  const pulso = landmarks[PULSO];
  const alvo = landmarks[ponta];
  const junta = landmarks[pip];
  const projecaoPonta =
    (alvo.x - pulso.x) * eixoDedos.x + (alvo.y - pulso.y) * eixoDedos.y;
  const projecaoPip =
    (junta.x - pulso.x) * eixoDedos.x + (junta.y - pulso.y) * eixoDedos.y;
  return projecaoPonta - projecaoPip > LIMIAR_DEDO_ESTENDIDO * tamanho;
}

/**
 * Distância ponta do polegar <-> ponta do indicador, em palmas.
 *
 * Devolve `null` quando o indicador está dobrado: numa mão fechada as duas
 * pontas também ficam próximas, e sem esta checagem mostrar 0 dedos (o Sol)
 * seria confundido com uma pinça.
 *
 * Dividir pelo tamanho da palma torna a medida independente da distância até a
 * câmera — o mesmo princípio dos limiares de dedo.
 */
export function medirPinca(landmarks, lado) {
  const { eixoDedos, tamanho } = referencialDaPalma(landmarks, lado);
  const [pontaIndicador, pipIndicador] = DEDOS_LONGOS[0];
  if (!dedoEstendido(landmarks, pontaIndicador, pipIndicador, eixoDedos, tamanho)) {
    return null;
  }
  const polegar = landmarks[POLEGAR_PONTA];
  const indicador = landmarks[pontaIndicador];
  return Math.hypot(polegar.x - indicador.x, polegar.y - indicador.y) / tamanho;
}

/** Conta quantos dedos de UMA mão estão levantados (0 a 5). */
export function contarDedos(landmarks, lado) {
  const { eixoDedos, eixoPolegar, tamanho } = referencialDaPalma(landmarks, lado);
  let total = 0;

  for (const [indicePonta, indicePip] of DEDOS_LONGOS) {
    // Projeção no eixo da palma: equivale a "a ponta está acima da junta", só
    // que válido com a mão em qualquer ângulo.
    if (dedoEstendido(landmarks, indicePonta, indicePip, eixoDedos, tamanho)) total += 1;
  }

  if (polegarLevantado(landmarks, eixoPolegar, tamanho)) total += 1;
  return total;
}

/**
 * Soma os dedos de até duas mãos.
 *
 * Devolve null quando não há mão utilizável. Uma mão só chega a 5; 6, 7 e 8
 * exigem as duas mãos (ex.: 5 + 3 = 8 -> Netuno).
 */
export function contarDedosTotal(maos) {
  if (!maos.length) return { total: null, porMao: [], descartadaPorBorda: false };
  const porMao = [];
  for (const { landmarks, lado } of maos) {
    if (!maoDentroDoQuadro(landmarks)) {
      // Mão cortada pela borda: descarta o frame inteiro em vez de arriscar uma
      // contagem errada.
      return { total: null, porMao: [], descartadaPorBorda: true };
    }
    porMao.push(contarDedos(landmarks, lado));
  }
  return {
    total: porMao.reduce((soma, valor) => soma + valor, 0),
    porMao,
    descartadaPorBorda: false,
  };
}
