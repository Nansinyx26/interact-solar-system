/**
 * Estabilização temporal do gesto reconhecido.
 *
 * Reconhecimento cru oscila entre valores vizinhos (4/5/4/5...) e trocaria o
 * foco dezenas de vezes por segundo. A leitura crua passa por três filtros:
 * buffer temporal, confirmação por maioria e cooldown após cada troca.
 */

import { COOLDOWN_TROCA_S, FRACAO_MAIORIA, TAMANHO_BUFFER_GESTOS } from "../config.js";

export class EstabilizadorGestos {
  constructor() {
    this.buffer = [];
    this.votosNecessarios = Math.max(
      2,
      Math.round(TAMANHO_BUFFER_GESTOS * FRACAO_MAIORIA),
    );
    this.valorConfirmado = null;
    this._instanteUltimaTroca = -COOLDOWN_TROCA_S;
    this._instanteUltimoGesto = null;
  }

  /** Há quanto tempo (s) não chega uma leitura válida. */
  segundosSemGesto(agora) {
    if (this._instanteUltimoGesto === null) return 0;
    return agora - this._instanteUltimoGesto;
  }

  /** Esquece o alvo confirmado (usado ao voltar à visão geral). */
  reiniciar() {
    this.buffer = [];
    this.valorConfirmado = null;
  }

  /** Define o alvo diretamente (botão/tecla), zerando a votação. */
  forcar(valor, agora) {
    this.buffer = [];
    this.valorConfirmado = valor;
    this._instanteUltimaTroca = agora;
    this._instanteUltimoGesto = agora;
  }

  /**
   * Registra uma leitura e devolve o estado da confirmação.
   *
   * `leitura` é null quando não há mão utilizável; nesse caso o alvo confirmado
   * é preservado — sumir da frente da câmera não deve desfazer a seleção.
   */
  atualizar(leitura, agora) {
    this.buffer.push(leitura);
    if (this.buffer.length > TAMANHO_BUFFER_GESTOS) this.buffer.shift();
    if (leitura !== null) this._instanteUltimoGesto = agora;

    const votos = new Map();
    for (const valor of this.buffer) {
      if (valor === null) continue;
      votos.set(valor, (votos.get(valor) ?? 0) + 1);
    }

    let candidato = null;
    let contagem = 0;
    for (const [valor, quantidade] of votos) {
      if (quantidade > contagem) {
        candidato = valor;
        contagem = quantidade;
      }
    }

    const emCooldown = agora - this._instanteUltimaTroca < COOLDOWN_TROCA_S;

    // O progresso ignora o candidato já confirmado: o anel só enche quando o
    // usuário está de fato pedindo uma troca.
    let progresso =
      candidato === null || candidato === this.valorConfirmado
        ? 0
        : Math.min(1, contagem / this.votosNecessarios);

    let confirmado = null;
    if (
      candidato !== null &&
      candidato !== this.valorConfirmado &&
      contagem >= this.votosNecessarios &&
      !emCooldown
    ) {
      this.valorConfirmado = candidato;
      this._instanteUltimaTroca = agora;
      confirmado = candidato;
      progresso = 1;
    }

    return { confirmado, candidato, progresso, emCooldown };
  }
}
