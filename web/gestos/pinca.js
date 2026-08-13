/**
 * Zoom por gesto de pinça: aproximar e afastar polegar e indicador.
 *
 * Recebe a razão medida por `medirPinca` (separação das pontas dividida pelo
 * tamanho da palma) e devolve o fator de zoom a aplicar no frame. A câmera não
 * precisa de nada novo: `Camera2D.aplicarZoom` já é o mesmo caminho da roda do
 * mouse.
 *
 * Enquanto a pinça está ativa a leitura **não** deve alimentar o estabilizador —
 * a pose seria contada como 2 dedos (Vênus) e trocaria o foco no meio do zoom.
 *
 * Porte do gestos/pinca.py: mesma histerese, mesma suavização, mesmo cooldown.
 */

import {
  COOLDOWN_APOS_PINCA_S,
  FATOR_ZOOM_PINCA_MAX,
  LIMIAR_PINCA_ATIVA,
  LIMIAR_PINCA_SAIDA,
  SUAVIZACAO_PINCA,
} from "../config.js";

export class ControladorPinca {
  constructor() {
    this._ativa = false;
    this._razaoSuave = null;
    this._fimDaPinca = -COOLDOWN_APOS_PINCA_S;
  }

  /** True enquanto o modo zoom estiver ligado. */
  get ativa() {
    return this._ativa;
  }

  /**
   * True enquanto a seleção por dedos deve ficar suspensa.
   *
   * Cobre a pinça em si e o rabicho depois dela: ao abrir a mão o gesto passa
   * por 1, 2 e 3 dedos, que sem esta pausa trocariam de planeta.
   */
  bloqueandoGestos(agora) {
    return this._ativa || agora - this._fimDaPinca < COOLDOWN_APOS_PINCA_S;
  }

  /** Esquece o estado (câmera desligada, mão sumiu do quadro). */
  reiniciar() {
    this._ativa = false;
    this._razaoSuave = null;
  }

  /** Processa uma leitura e devolve { ativa, fatorZoom, razao }. */
  atualizar(razao, agora) {
    if (razao === null || razao === undefined) {
      // Sem indicador estendido não há pinça: encerra o modo zoom.
      if (this._ativa) {
        this._ativa = false;
        this._fimDaPinca = agora;
      }
      this._razaoSuave = null;
      return { ativa: false, fatorZoom: 1, razao: null };
    }

    const anterior = this._razaoSuave;
    // Média móvel exponencial: o tremor da mão é muito maior que o do mouse e
    // sem filtro o zoom vibra a cada frame.
    this._razaoSuave =
      anterior === null ? razao : anterior + (razao - anterior) * SUAVIZACAO_PINCA;
    const suave = this._razaoSuave;

    // Histerese: entra fechado, só sai bem aberto. Com limiar único a pinça
    // piscaria na fronteira e o zoom entraria e sairia sozinho.
    if (!this._ativa && suave < LIMIAR_PINCA_ATIVA) {
      this._ativa = true;
      return { ativa: true, fatorZoom: 1, razao: suave };
    }
    if (this._ativa && suave > LIMIAR_PINCA_SAIDA) {
      this._ativa = false;
      this._fimDaPinca = agora;
      return { ativa: false, fatorZoom: 1, razao: suave };
    }

    if (!this._ativa || anterior === null || anterior <= 0) {
      return { ativa: this._ativa, fatorZoom: 1, razao: suave };
    }

    // Fator RELATIVO ao frame anterior. Aplicar razaoAtual/razaoInicial a cada
    // frame faria o zoom crescer exponencialmente; o incremental acumula
    // exatamente a mesma proporção total, sem explodir.
    let fator = suave / anterior;
    fator = Math.min(FATOR_ZOOM_PINCA_MAX, Math.max(1 / FATOR_ZOOM_PINCA_MAX, fator));
    return { ativa: true, fatorZoom: fator, razao: suave };
  }
}
