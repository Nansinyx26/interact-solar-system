/**
 * Leitor de mãos: de um resultado do MediaPipe a uma pose classificada e estável.
 *
 * Espelha o `gestos/leitor_maos.py` do desktop.
 *
 * Este módulo concentra TODA a etapa de percepção. Antes ela estava espalhada:
 * o detector chamava o MediaPipe e somava dedos, a máquina de estados
 * reclassificava a forma, e cada um mantinha o próprio pedaço de histórico. O
 * resultado era o sintoma clássico — a leitura piscava e trocava de gesto
 * sozinha, porque nenhuma das partes tinha memória suficiente para saber que
 * estava vendo a mesma mão de um frame para o outro.
 *
 * A ordem aqui é deliberada, e cada etapa resolve um modo de falha diferente:
 *
 * 1. **Inferência** — MediaPipe devolve 21 landmarks por mão + `handedness`.
 * 2. **Corte por confiança** — mãos com score abaixo de `CONFIANCA_MIN_UTIL`
 *    são lixo (cortina, rosto, mão do fundo). Descartadas.
 * 3. **Reaproveitamento** — se sobrar nada, a última pose boa vale por mais uns
 *    frames em vez de zerar tudo. É o que impede o modo lua de cair por causa
 *    de uma piscada do rastreio.
 * 4. **Filtro One Euro** — suaviza os landmarks, por mão, indexado pelo
 *    `handedness`. Aqui morre o tremor que fazia o dedo na fronteira oscilar.
 * 5. **Classificação com histerese** — dedos e forma, cada mão comparada com a
 *    PRÓPRIA leitura anterior.
 * 6. **Votação temporal** — o gesto exposto é a moda das últimas N leituras,
 *    não a do frame atual.
 *
 * Diferença em relação ao desktop: lá o leitor também roda a inferência (a
 * captura vive numa thread própria). Na web quem chama o MediaPipe é o
 * `detector.js`, então aqui entra o RESULTADO já pronto — a etapa 1 acontece
 * fora. Da 2 em diante é idêntico.
 *
 * Equivalências com a especificação (`HandGestureReader`):
 *
 *     update(frame)     -> atualizar(resultado, agora)
 *     current_gesture   -> gestoAtual
 *     finger_count      -> contagemDedos
 *     is_L              -> ehL
 *     stability_ratio   -> razaoEstabilidade
 */

import {
  CONFIANCA_MIN_UTIL,
  FILTRO_LANDMARKS_ATIVO,
  JANELA_REAPROVEITAMENTO_S,
  MAX_MAOS,
  TAMANHO_BUFFER_GESTOS,
} from "../config.js";
import {
  DEDOS_TODOS_FECHADOS,
  classificarDedos,
  maoDentroDoQuadro,
  medirPinca,
} from "./contador.js";
import { BancoDeFiltros } from "./filtro_landmarks.js";
import { ehFormatoL } from "./formatos_mao.js";

/** Pose vazia — o estado inicial e o de "não vi mão nenhuma". */
function poseVazia(instante = 0, confiancaMedia = 0) {
  return {
    maos: [],
    instante,
    reaproveitada: false,
    descartadaPorBorda: false,
    confiancaMedia,
  };
}

/** Soma dos dedos das mãos utilizáveis, ou null se não houver nenhuma. */
export function contagemTotal(pose) {
  const usaveis = pose.maos.filter((m) => m.noQuadro);
  if (!usaveis.length) return null;
  return usaveis.reduce((soma, m) => soma + m.contagem, 0);
}

/** Mãos que formam o "L", na ordem em que foram detectadas. */
export function maosEmL(pose) {
  return pose.maos.filter((m) => m.ehL && m.noQuadro);
}

/** (landmarks, lado) — o formato que a máquina de estados já consome. */
export function comoPares(pose) {
  return pose.maos.map((m) => ({ landmarks: m.landmarks, lado: m.lado }));
}

/**
 * Percepção completa de mãos, com memória entre frames.
 *
 * Uma instância por detector.
 */
export class LeitorMaos {
  constructor() {
    this._filtros = new BancoDeFiltros(FILTRO_LANDMARKS_ATIVO);
    // Histerese: a última classificação de cada mão, por handedness. Indexar
    // por LADO e não por posição na lista é o que impede a mão esquerda de
    // herdar o estado da direita quando o MediaPipe inverte a ordem.
    this._dedosAnteriores = new Map();
    this._buffer = [];
    this._pose = poseVazia();
    this._ultimaPoseBoa = null;
  }

  /** Esquece todo o histórico (a câmera reconectou, por exemplo). */
  reiniciar() {
    this._filtros.reiniciar();
    this._dedosAnteriores.clear();
    this._buffer = [];
    this._pose = poseVazia();
    this._ultimaPoseBoa = null;
  }

  /**
   * Processa as mãos cruas de uma inferência e devolve a pose classificada.
   *
   * `brutas` é uma lista de {landmarks, lado, score}. `agora` vem de fora
   * (`performance.now() / 1000`) porque o filtro One Euro precisa do intervalo
   * real entre amostras.
   */
  atualizar(brutas, agora) {
    this._pose = this._interpretar(brutas ?? [], agora);
    // A votação recebe a contagem já filtrada e classificada — é a última
    // camada, não a primeira.
    this._buffer.push(contagemTotal(this._pose));
    if (this._buffer.length > TAMANHO_BUFFER_GESTOS) this._buffer.shift();
    return this._pose;
  }

  /** Última pose interpretada. */
  get pose() {
    return this._pose;
  }

  /**
   * Moda do buffer temporal — o gesto *estável*, não o do frame.
   *
   * É este valor (e não `contagemDedos`) que deve comandar qualquer troca de
   * estado: o frame isolado é exatamente o que piscava.
   */
  get gestoAtual() {
    const votos = new Map();
    for (const v of this._buffer) {
      if (v !== null) votos.set(v, (votos.get(v) ?? 0) + 1);
    }
    if (!votos.size) return null;
    let melhor = null;
    let maior = 0;
    for (const [valor, total] of votos) {
      if (total > maior) {
        maior = total;
        melhor = valor;
      }
    }
    return melhor;
  }

  /** Contagem crua da leitura atual (para diagnóstico e HUD de debug). */
  get contagemDedos() {
    return contagemTotal(this._pose);
  }

  /** True quando ao menos uma mão forma o "L" nesta leitura. */
  get ehL() {
    return maosEmL(this._pose).length > 0;
  }

  /**
   * 0 a 1: fração do buffer que concorda com o gesto atual.
   *
   * 1,0 = as últimas N leituras disseram todas a mesma coisa. Abaixo de ~0,6 a
   * mão está em transição (ou a leitura está ruim) e nenhuma decisão deveria
   * ser tomada — o HUD de debug mostra isso como barra.
   */
  get razaoEstabilidade() {
    if (!this._buffer.length) return 0;
    const votos = new Map();
    for (const v of this._buffer) {
      if (v !== null) votos.set(v, (votos.get(v) ?? 0) + 1);
    }
    if (!votos.size) return 0;
    return Math.max(...votos.values()) / this._buffer.length;
  }

  // -------------------------------------------------------------- internos
  _interpretar(brutas, agora) {
    // --- corte por confiança ------------------------------------------
    // O MediaPipe devolve 21 landmarks sempre que "acha" que viu uma mão. Com
    // score baixo esses pontos são ruído estruturado — pior que ruído puro,
    // porque passam nas checagens de forma.
    let confiaveis = brutas.filter((m) => (m.score ?? 1) >= CONFIANCA_MIN_UTIL);

    if (!confiaveis.length) return this._reaproveitar(agora, brutas);

    // Ordena por confiança e fica com as duas melhores (o MediaPipe às vezes
    // entrega uma terceira mão fantasma no fundo do quadro).
    confiaveis = [...confiaveis]
      .sort((a, b) => (b.score ?? 1) - (a.score ?? 1))
      .slice(0, MAX_MAOS);

    const ladosPresentes = new Set(confiaveis.map((m) => m.lado));
    this._filtros.esquecerAusentes(ladosPresentes, agora);
    for (const lado of [...this._dedosAnteriores.keys()]) {
      if (!ladosPresentes.has(lado)) this._dedosAnteriores.delete(lado);
    }

    const maos = [];
    let algumaNaBorda = false;
    for (const { landmarks, lado, score } of confiaveis) {
      // --- filtro ----------------------------------------------------
      const suavizados = this._filtros.filtrar(landmarks, lado, agora);

      // --- classificação com histerese -------------------------------
      const anteriores = this._dedosAnteriores.get(lado) ?? DEDOS_TODOS_FECHADOS;
      const dedos = classificarDedos(suavizados, lado, anteriores);
      this._dedosAnteriores.set(lado, dedos);

      const noQuadro = maoDentroDoQuadro(suavizados);
      algumaNaBorda = algumaNaBorda || !noQuadro;

      maos.push({
        landmarks: suavizados,
        lado,
        score: score ?? 1,
        dedos,
        contagem: dedos.reduce((s, aberto) => s + (aberto ? 1 : 0), 0),
        // A FORMA é classificada sobre os landmarks JÁ filtrados e sem
        // histerese: o "L" é uma pose geométrica, e a memória que ele precisa
        // vem da contagem de frames lá na máquina de estados, não daqui.
        ehL: ehFormatoL(suavizados, lado),
        razaoPinca: medirPinca(suavizados, lado),
        noQuadro,
      });
    }

    const pose = {
      maos,
      instante: agora,
      reaproveitada: false,
      descartadaPorBorda: algumaNaBorda,
      confiancaMedia: maos.reduce((s, m) => s + m.score, 0) / maos.length,
    };
    // Só poses com pelo menos uma mão inteira viram "última pose boa": a mão
    // saindo pela borda é justamente o que não queremos congelar.
    if (maos.some((m) => m.noQuadro)) this._ultimaPoseBoa = pose;
    return pose;
  }

  /**
   * Frame sem nada aproveitável: repete a última pose boa, se recente.
   *
   * Zerar aqui seria o comportamento antigo — e era ele que derrubava o modo
   * lua no meio de uma seleção sempre que o rastreio piscava por um frame.
   * Passada a janela, a pose vazia volta: a mão saiu de verdade.
   */
  _reaproveitar(agora, brutas) {
    const anterior = this._ultimaPoseBoa;
    if (anterior && agora - anterior.instante <= JANELA_REAPROVEITAMENTO_S) {
      return { ...anterior, reaproveitada: true };
    }
    this._ultimaPoseBoa = null;
    this._dedosAnteriores.clear();
    // Distingue "não vi mão nenhuma" de "vi, mas era lixo": o segundo caso
    // vira aviso de confiança baixa no HUD.
    const media = brutas.length
      ? brutas.reduce((s, m) => s + (m.score ?? 1), 0) / brutas.length
      : 0;
    return poseVazia(agora, media);
  }
}
