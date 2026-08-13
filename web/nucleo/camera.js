/**
 * Câmera 2D com zoom/pan interpolados.
 *
 * A câmera nunca "corta" para o alvo: toda troca dispara uma transição com
 * easing. Como o alvo continua orbitando durante a transição, o destino é
 * reavaliado a cada frame — o que interpolamos é o progresso, não um ponto fixo.
 */

import {
  ALTURA_REFERENCIA,
  DESLOCAMENTO_FOCO_X_PX,
  DURACAO_TRANSICAO_S,
  RAIO_ALVO_FOCO_PX,
  ZOOM_MAX,
  ZOOM_MIN,
  ZOOM_VISAO_GERAL,
} from "../config.js";

/** Easing ease-in-out cúbico sobre t em [0, 1]. */
export function suavizar(t) {
  const v = Math.min(1, Math.max(0, t));
  return v < 0.5 ? 4 * v * v * v : 1 - (-2 * v + 2) ** 3 / 2;
}

function interpolar(inicio, fim, fator) {
  return inicio + (fim - inicio) * fator;
}

/**
 * Zoom que faz um corpo de raio informado ocupar RAIO_ALVO_FOCO_PX.
 * `escalaJanela` mantém a proporção do corpo quando a tela muda de tamanho.
 */
export function zoomParaFocar(raioCorpo, escalaJanela = 1) {
  if (raioCorpo <= 0) return ZOOM_VISAO_GERAL * escalaJanela;
  const alvo = (RAIO_ALVO_FOCO_PX * escalaJanela) / raioCorpo;
  return Math.min(ZOOM_MAX * escalaJanela, Math.max(ZOOM_MIN * escalaJanela, alvo));
}

export class Camera2D {
  constructor(largura, altura) {
    this.largura = largura;
    this.altura = altura;
    this.centroX = 0;
    this.centroY = 0;
    this.zoom = this.zoomVisaoGeral();
    this.deslocamentoX = 0;

    this._centroXInicial = 0;
    this._centroYInicial = 0;
    this._zoomInicial = this.zoom;
    this._deslocamentoInicial = 0;
    this._progresso = 1;

    this._centroAlvo = { x: 0, y: 0 };
    this._zoomAlvo = this.zoom;
    this._deslocamentoAlvo = 0;
  }

  /** Quanto a tela atual é maior/menor que a de referência. */
  get escalaJanela() {
    return this.altura / ALTURA_REFERENCIA;
  }

  /** Zoom do panorama, ajustado ao tamanho atual da tela. */
  zoomVisaoGeral() {
    return ZOOM_VISAO_GERAL * (this.altura / ALTURA_REFERENCIA);
  }

  /** Aplica os limites de zoom, que escalam junto com a tela. */
  limitarZoom(zoom) {
    const escala = this.escalaJanela;
    return Math.min(ZOOM_MAX * escala, Math.max(ZOOM_MIN * escala, zoom));
  }

  /** Informa o novo tamanho da tela (o enquadramento acompanha). */
  redimensionar(largura, altura) {
    if (largura === this.largura && altura === this.altura) return;
    const proporcao = altura / this.altura;
    this.largura = largura;
    this.altura = altura;
    // Mantém o mesmo campo de visão vertical após o redimensionamento.
    this.zoom *= proporcao;
    this._zoomInicial *= proporcao;
    this._zoomAlvo *= proporcao;
  }

  /** Congela o estado atual como origem e começa uma nova interpolação. */
  iniciarTransicao(centroAlvo, zoomAlvo, deslocamentoAlvo) {
    this._centroXInicial = this.centroX;
    this._centroYInicial = this.centroY;
    this._zoomInicial = this.zoom;
    this._deslocamentoInicial = this.deslocamentoX;
    this._progresso = 0;
    this.definirAlvo(centroAlvo, zoomAlvo, deslocamentoAlvo);
  }

  /** Atualiza o destino sem reiniciar o progresso (alvo em movimento). */
  definirAlvo(centroAlvo, zoomAlvo, deslocamentoAlvo) {
    this._centroAlvo = centroAlvo;
    this._zoomAlvo = this.limitarZoom(zoomAlvo);
    this._deslocamentoAlvo = deslocamentoAlvo;
  }

  /** Aponta a câmera para um corpo, com ou sem reiniciar a transição. */
  focarCorpo(posicao, raioCorpo, reiniciar) {
    const escala = this.escalaJanela;
    const zoom = zoomParaFocar(raioCorpo, escala);
    // Em telas estreitas (celular) a ficha ocupa a parte de baixo, não a
    // lateral, então não faz sentido empurrar o planeta para o lado.
    const deslocamento = this.largura < 820 ? 0 : DESLOCAMENTO_FOCO_X_PX * escala;
    if (reiniciar) this.iniciarTransicao(posicao, zoom, deslocamento);
    else this.definirAlvo(posicao, zoom, deslocamento);
  }

  /** Volta suavemente ao enquadramento do sistema inteiro. */
  voltarVisaoGeral(reiniciar = true) {
    if (reiniciar) this.iniciarTransicao({ x: 0, y: 0 }, this.zoomVisaoGeral(), 0);
    else this.definirAlvo({ x: 0, y: 0 }, this.zoomVisaoGeral(), 0);
  }

  /** Encerra a transição, fixando a câmera onde ela está agora. */
  congelar() {
    this._progresso = 1;
    this._centroAlvo = { x: this.centroX, y: this.centroY };
    this._zoomAlvo = this.zoom;
    this._deslocamentoAlvo = this.deslocamentoX;
    this._centroXInicial = this.centroX;
    this._centroYInicial = this.centroY;
    this._zoomInicial = this.zoom;
    this._deslocamentoInicial = this.deslocamentoX;
  }

  /** Pan manual: desloca a cena conforme o ponteiro, em pixels de tela. */
  arrastar(dxTela, dyTela) {
    this.congelar();
    this._centroAlvo = {
      x: this._centroAlvo.x - dxTela / this.zoom,
      y: this._centroAlvo.y - dyTela / this.zoom,
    };
  }

  /** Zoom manual (roda do mouse ou pinça), respeitando os limites globais. */
  aplicarZoom(fator) {
    this.congelar();
    this._zoomAlvo = this.limitarZoom(this.zoom * fator);
  }

  /** Avança a interpolação em `dt` segundos. */
  atualizar(dt) {
    if (this._progresso < 1) {
      this._progresso = Math.min(1, this._progresso + dt / DURACAO_TRANSICAO_S);
    }
    const fator = suavizar(this._progresso);
    this.centroX = interpolar(this._centroXInicial, this._centroAlvo.x, fator);
    this.centroY = interpolar(this._centroYInicial, this._centroAlvo.y, fator);
    this.zoom = interpolar(this._zoomInicial, this._zoomAlvo, fator);
    this.deslocamentoX = interpolar(
      this._deslocamentoInicial,
      this._deslocamentoAlvo,
      fator,
    );
  }

  /** Projeta um ponto de mundo em pixels da tela. */
  mundoParaTela(posicao) {
    return {
      x: (posicao.x - this.centroX) * this.zoom + this.largura / 2 + this.deslocamentoX,
      y: (posicao.y - this.centroY) * this.zoom + this.altura / 2,
    };
  }

  /** Converte um comprimento de mundo para pixels de tela. */
  escalar(comprimento) {
    return comprimento * this.zoom;
  }
}
