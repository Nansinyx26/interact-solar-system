/**
 * Sistema Solar Interativo por gestos — versão web.
 *
 * Loop principal: consome a última leitura do detector, estabiliza o gesto,
 * move a câmera e desenha a cena. Funciona por completo sem câmera: teclado no
 * desktop e botões de toque no celular fazem o papel dos dedos.
 */

import {
  DETECTAR_A_CADA_N_FRAMES,
  FATOR_AJUSTE_TEMPO,
  FATOR_ZOOM_RODA,
  GESTO_VISAO_GERAL,
  SEGUNDOS_ATE_VISAO_GERAL,
  TIME_SCALE,
  TIME_SCALE_MAX,
  TIME_SCALE_MIN,
} from "./config.js";
import { CORPOS, CORPOS_POR_GESTO, corpoPorGesto } from "./dados/planetas.js";
import { DetectorMaos, StatusCamera } from "./gestos/detector.js";
import { EstabilizadorGestos } from "./gestos/estabilizador.js";
import { Camera2D } from "./nucleo/camera.js";
import { posicoesDoSistema, raioCorpoPx } from "./nucleo/orbita.js";
import { Renderizador } from "./nucleo/renderizador.js";
import { ControladorPinca } from "./gestos/pinca.js";
import { Ficha } from "./ui/ficha.js";
import { HUD } from "./ui/hud.js";
import { Narrador, textoDoCorpo } from "./ui/narrador.js";

/** Se o quadro demorar demais (aba em segundo plano), não damos um salto. */
const DT_MAXIMO = 0.1;

class Aplicacao {
  constructor() {
    this.canvas = document.getElementById("cena");
    this.detector = new DetectorMaos(
      document.getElementById("video"),
      document.getElementById("preview"),
    );
    this.estabilizador = new EstabilizadorGestos();
    this.pinca = new ControladorPinca();
    this.narrador = new Narrador();

    this._ajustarCanvas();
    this.renderizador = new Renderizador(this.canvas);
    this.camera = new Camera2D(this.canvas.width, this.canvas.height);
    this.hud = new HUD(document.body);
    this.ficha = new Ficha(document.getElementById("ficha"));

    this.tempoDias = 0;
    this.escalaTempo = TIME_SCALE;
    this.pausado = false;
    this.corpoAlvo = null;
    this.cameraLivre = false;
    this.posicoes = posicoesDoSistema(0);
    this.resultadoGesto = { confirmado: null, candidato: null, progresso: 0 };
    this._ultimaSequencia = -1;
    this._contadorFrames = 0;
    this._ultimoInstante = performance.now();
    this._fps = 0;
    this._arrastando = false;
    this._ultimoPonteiro = null;
    this._distanciaPinca = null;

    this._ligarEventos();
    this._observarPainelGesto();
    this._montarBotoes();
  }

  // ------------------------------------------------------------------ setup
  _ajustarCanvas() {
    // devicePixelRatio limitado a 2: em celulares com DPR 3 o custo por pixel
    // triplica sem ganho visual perceptível nesta cena.
    const escala = Math.min(window.devicePixelRatio || 1, 2);
    const largura = this.canvas.clientWidth;
    const altura = this.canvas.clientHeight;
    this.canvas.width = Math.round(largura * escala);
    this.canvas.height = Math.round(altura * escala);
    this._escalaTela = escala;
  }

  _redimensionar() {
    this._ajustarCanvas();
    this.camera.redimensionar(this.canvas.width, this.canvas.height);
    this.renderizador.redimensionar(this.canvas.width, this.canvas.height);
  }

  /**
   * Publica a altura do painel de gesto em `--altura-painel-gesto`.
   *
   * A ficha divide a coluna esquerda com esse painel e precisa parar onde ele
   * começa. A altura muda entre desktop e celular e com a fonte do sistema, por
   * isso é medida em tempo real em vez de estimada no CSS.
   */
  _observarPainelGesto() {
    const painel = document.querySelector(".painel-gesto");
    if (!painel) return;
    const publicar = () => {
      const altura = Math.round(painel.getBoundingClientRect().height);
      document.documentElement.style.setProperty(
        "--altura-painel-gesto",
        `${altura}px`,
      );
    };
    if (typeof ResizeObserver === "function") {
      new ResizeObserver(publicar).observe(painel);
    } else {
      window.addEventListener("resize", publicar);
    }
    publicar();
  }

  _montarBotoes() {
    const barra = document.getElementById("botoes-gesto");
    // A tira de cor no topo do botão repete a cor do corpo na cena e na legenda:
    // no celular, onde a legenda não cabe, é a única pista visual do alvo.
    const itens = CORPOS.map(
      (corpo) =>
        `<button type="button" data-gesto="${corpo.indiceGesto}" title="${corpo.nome}">` +
        `<i style="background:rgb(${corpo.corBase})"></i>` +
        `<b>${corpo.indiceGesto}</b><span>${corpo.nome}</span></button>`,
    );
    itens.push(
      `<button type="button" data-gesto="visao" class="comando" title="Visão geral">` +
        `<b>V</b><span>visão geral</span></button>`,
    );
    barra.innerHTML = itens.join("");
    barra.addEventListener("click", (evento) => {
      const botao = evento.target.closest("button");
      if (!botao) return;
      const valor = botao.dataset.gesto;
      if (valor === "visao") {
        this.estabilizador.forcar(GESTO_VISAO_GERAL, performance.now() / 1000);
        this._voltarVisaoGeral();
      } else {
        const indice = Number(valor);
        this.estabilizador.forcar(indice, performance.now() / 1000);
        this._selecionar(corpoPorGesto(indice));
      }
    });
  }

  _ligarEventos() {
    window.addEventListener("resize", () => this._redimensionar());
    window.addEventListener("orientationchange", () => this._redimensionar());

    document.addEventListener("keydown", (evento) => this._tratarTecla(evento));

    document.getElementById("btn-camera").addEventListener("click", () => {
      this._alternarCamera();
    });
    document.getElementById("btn-pausa").addEventListener("click", () => {
      this.pausado = !this.pausado;
    });
    document.getElementById("btn-narracao").addEventListener("click", () => {
      this._alternarNarracao();
    });
    document.getElementById("btn-ajuda").addEventListener("click", () => {
      document.getElementById("ajuda").classList.toggle("aberta");
    });
    document.getElementById("fechar-ajuda").addEventListener("click", () => {
      document.getElementById("ajuda").classList.remove("aberta");
    });

    // Pan/zoom por ponteiro (mouse e toque usam o mesmo caminho).
    this.canvas.addEventListener("pointerdown", (evento) => {
      this.canvas.setPointerCapture(evento.pointerId);
      this._arrastando = true;
      this._moveu = false;
      this._ultimoPonteiro = { x: evento.clientX, y: evento.clientY };
    });
    this.canvas.addEventListener("pointermove", (evento) => {
      if (!this._arrastando || !this._ultimoPonteiro) return;
      const dx = evento.clientX - this._ultimoPonteiro.x;
      const dy = evento.clientY - this._ultimoPonteiro.y;
      if (Math.hypot(dx, dy) > 3) this._moveu = true;
      this._ultimoPonteiro = { x: evento.clientX, y: evento.clientY };
      if (this._moveu) {
        this.cameraLivre = true;
        this.camera.arrastar(dx * this._escalaTela, dy * this._escalaTela);
      }
    });
    this.canvas.addEventListener("pointerup", (evento) => {
      this._arrastando = false;
      // Toque curto sem arrasto = seleção direta do corpo tocado.
      if (!this._moveu) this._selecionarNoPonto(evento);
    });
    this.canvas.addEventListener("pointercancel", () => {
      this._arrastando = false;
    });
    this.canvas.addEventListener(
      "wheel",
      (evento) => {
        evento.preventDefault();
        this.cameraLivre = true;
        this.camera.aplicarZoom(FATOR_ZOOM_RODA ** (evento.deltaY > 0 ? -1 : 1));
      },
      { passive: false },
    );

    // Pinça de dois dedos para zoom no celular.
    this.canvas.addEventListener("touchmove", (evento) => {
      if (evento.touches.length !== 2) return;
      evento.preventDefault();
      const [a, b] = evento.touches;
      const distancia = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
      if (this._distanciaPinca) {
        this.cameraLivre = true;
        this.camera.aplicarZoom(distancia / this._distanciaPinca);
      }
      this._distanciaPinca = distancia;
    }, { passive: false });
    this.canvas.addEventListener("touchend", () => {
      this._distanciaPinca = null;
    });
  }

  _tratarTecla(evento) {
    const tecla = evento.key;
    if (tecla >= "0" && tecla <= "9") {
      const indice = Number(tecla);
      this.estabilizador.forcar(indice, performance.now() / 1000);
      this._selecionar(corpoPorGesto(indice));
    } else if (tecla === "l" || tecla === "L") {
      const lua = corpoPorGesto(9);
      if (lua) {
        this.estabilizador.forcar(9, performance.now() / 1000);
        this._selecionar(lua);
      }
    } else if (tecla === "v" || tecla === "V") {
      this._voltarVisaoGeral();
    } else if (tecla === " ") {
      evento.preventDefault();
      this.pausado = !this.pausado;
    } else if (tecla === "+" || tecla === "=") {
      this.escalaTempo = Math.min(TIME_SCALE_MAX, this.escalaTempo * FATOR_AJUSTE_TEMPO);
    } else if (tecla === "-") {
      this.escalaTempo = Math.max(TIME_SCALE_MIN, this.escalaTempo / FATOR_AJUSTE_TEMPO);
    } else if (tecla === "n" || tecla === "N") {
      this._alternarNarracao();
    } else if (tecla === "c" || tecla === "C") {
      this._alternarCamera();
    }
  }

  _selecionarNoPonto(evento) {
    const caixa = this.canvas.getBoundingClientRect();
    const ponto = {
      x: (evento.clientX - caixa.left) * this._escalaTela,
      y: (evento.clientY - caixa.top) * this._escalaTela,
    };
    const corpo = this.renderizador.corpoNoPonto(this.camera, this.posicoes, ponto);
    if (corpo) {
      this.estabilizador.forcar(corpo.indiceGesto, performance.now() / 1000);
      this._selecionar(corpo);
    }
  }

  /** Liga/desliga a narração e reflete o estado no botão. */
  _alternarNarracao() {
    const ativo = this.narrador.alternar();
    const botao = document.getElementById("btn-narracao");
    if (!botao) return;
    botao.classList.toggle("ativo", ativo);
    botao.textContent = ativo ? "🔊 Voz" : "🔇 Voz";
    botao.title = ativo
      ? `Narração ligada (${this.narrador.backend}) — tecla N`
      : "Narração desligada — tecla N";
    // Navegadores só liberam áudio depois de um gesto do usuário: ligar pelo
    // botão é o momento certo de confirmar em voz alta que a voz funciona.
    if (ativo && this.corpoAlvo) this.narrador.anunciar(textoDoCorpo(this.corpoAlvo));
  }

  // ----------------------------------------------------------------- câmera
  async _alternarCamera() {
    const botao = document.getElementById("btn-camera");
    const painel = document.getElementById("painel-camera");
    if (this.detector.ativa) {
      this.detector.parar();
      painel.hidden = true;
      botao.textContent = "Ativar câmera";
      botao.classList.remove("ativo");
      return;
    }
    botao.disabled = true;
    botao.textContent = "Abrindo...";
    painel.hidden = false;
    const ok = await this.detector.iniciar();
    botao.disabled = false;
    botao.textContent = ok ? "Desligar câmera" : "Ativar câmera";
    botao.classList.toggle("ativo", ok);
    if (!ok) painel.hidden = true;
  }

  // ------------------------------------------------------------ atualização
  _atualizar(dt) {
    if (!this.pausado) this.tempoDias += dt * this.escalaTempo;
    this.posicoes = posicoesDoSistema(this.tempoDias);

    const agora = performance.now() / 1000;
    this._contadorFrames += 1;
    // Inferência 1 a cada N frames: ~30 leituras/s já é muito mais rápido que
    // os ~0,5 s de confirmação, e sobra CPU para o render.
    if (this._contadorFrames % DETECTAR_A_CADA_N_FRAMES === 0) {
      this.detector.processarFrame();
      this.detector.desenharPreview();
    }

    const leitura = this.detector.leitura;
    // O estabilizador só avança com INFERÊNCIA nova: alimentá-lo a 60 Hz
    // encheria o buffer com a mesma leitura repetida e a confirmação viraria
    // instantânea, perdendo o efeito de filtro.
    if (leitura.sequencia !== this._ultimaSequencia) {
      this._ultimaSequencia = leitura.sequencia;

      // Pinça primeiro: enquanto ela comanda o zoom, a pose seria contada como
      // 2 dedos (Vênus) e trocaria o foco no meio do movimento.
      const estadoPinca = this.pinca.atualizar(leitura.razaoPinca, agora);
      if (estadoPinca.fatorZoom !== 1) {
        this.cameraLivre = true;
        this.camera.aplicarZoom(estadoPinca.fatorZoom);
      }

      // 0-9 selecionam um corpo (9 = Lua) e 10 é o comando "visão geral".
      // Qualquer outra contagem entra como leitura inválida.
      const contagem = leitura.contagem;
      const valido = CORPOS_POR_GESTO.has(contagem) || contagem === GESTO_VISAO_GERAL;
      const bloqueado = this.pinca.bloqueandoGestos(agora);
      this.resultadoGesto = this.estabilizador.atualizar(
        valido && !bloqueado ? contagem : null,
        agora,
      );
    } else if (this.resultadoGesto.confirmado !== null) {
      this.resultadoGesto = { ...this.resultadoGesto, confirmado: null };
    }

    const confirmado = this.resultadoGesto.confirmado;
    if (confirmado === GESTO_VISAO_GERAL) {
      // O valor segue confirmado no estabilizador para não disparar em looping
      // enquanto as duas mãos continuam abertas.
      this._voltarVisaoGeral(false);
    } else if (confirmado !== null) {
      this._selecionar(corpoPorGesto(confirmado));
    } else if (
      this.detector.ativa &&
      this.corpoAlvo &&
      this.estabilizador.segundosSemGesto(agora) > SEGUNDOS_ATE_VISAO_GERAL
    ) {
      this._voltarVisaoGeral();
    }

    if (this.corpoAlvo && !this.cameraLivre) {
      // O alvo continua orbitando: o destino é reavaliado a cada frame, sem
      // reiniciar a interpolação em andamento.
      this.camera.focarCorpo(
        this.posicoes.get(this.corpoAlvo.nome),
        raioCorpoPx(this.corpoAlvo),
        false,
      );
    }
    this.camera.atualizar(dt);
  }

  _selecionar(corpo) {
    if (!corpo) return;
    if (corpo === this.corpoAlvo && !this.cameraLivre) return;
    this.cameraLivre = false;
    this.corpoAlvo = corpo;
    this.camera.focarCorpo(this.posicoes.get(corpo.nome), raioCorpoPx(corpo), true);
    this.ficha.mostrar(corpo);
    this.narrador.anunciar(textoDoCorpo(corpo));
    // A ficha ocupa o lugar da legenda no canto esquerdo: uma entra, a outra sai.
    document.body.classList.add("com-foco");
  }

  _voltarVisaoGeral(reiniciarGesto = true) {
    if (!this.corpoAlvo && !this.cameraLivre) return;
    this.cameraLivre = false;
    this.corpoAlvo = null;
    this.camera.voltarVisaoGeral();
    this.ficha.ocultar();
    document.body.classList.remove("com-foco");
    if (reiniciarGesto) this.estabilizador.reiniciar();
  }

  // --------------------------------------------------------------- execução
  iniciar() {
    const quadro = (instante) => {
      const dt = Math.min((instante - this._ultimoInstante) / 1000, DT_MAXIMO);
      this._ultimoInstante = instante;
      // Média móvel só para o indicador não piscar a cada frame.
      if (dt > 0) this._fps = this._fps * 0.9 + (1 / dt) * 0.1;

      this._atualizar(dt);
      this.renderizador.desenhar(
        this.camera,
        this.posicoes,
        this.tempoDias,
        this.corpoAlvo,
      );
      this.hud.atualizar({
        leitura: this.detector.leitura,
        resultado: {
          ...this.resultadoGesto,
          valorConfirmado: this.estabilizador.valorConfirmado,
        },
        corpoAlvo: this.corpoAlvo,
        fps: this._fps,
        escalaTempo: this.escalaTempo,
        pausado: this.pausado,
        detector: this.detector,
        pincaAtiva: this.pinca.ativa,
      });
      requestAnimationFrame(quadro);
    };
    requestAnimationFrame(quadro);
  }
}

const app = new Aplicacao();
app.iniciar();

// Libera a câmera se a aba for fechada ou escondida por muito tempo.
window.addEventListener("pagehide", () => app.detector.parar());

export { app, StatusCamera };
