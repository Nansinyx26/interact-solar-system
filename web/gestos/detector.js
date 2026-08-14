/**
 * Captura da webcam + MediaPipe Hand Landmarker (WASM) no navegador.
 *
 * Equivalente web do gestos/detector.py: expõe sempre a "última leitura válida"
 * para o loop de render consultar, sem nunca bloqueá-lo.
 */

import {
  ALTURA_CAPTURA,
  CONFIANCA_MIN_DETECCAO,
  CONFIANCA_MIN_PRESENCA,
  CONFIANCA_MIN_RASTREIO,
  LARGURA_CAPTURA,
  MAX_MAOS,
  URL_MODELO_MAOS,
  URL_WASM_MEDIAPIPE,
} from "../config.js";
import { contarDedosTotal, medirPinca } from "./contador.js";

/** Situação atual da captura de vídeo. */
export const StatusCamera = {
  PARADA: "parada",
  INICIANDO: "iniciando",
  ATIVA: "ativa",
  INDISPONIVEL: "indisponivel",
};

/** Conexões do esqueleto da mão, para desenhar os landmarks no preview. */
const CONEXOES_MAO = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
];

export class DetectorMaos {
  /**
   * @param {HTMLVideoElement} video elemento que recebe o stream da webcam
   * @param {HTMLCanvasElement} canvasPreview onde os landmarks são desenhados
   */
  constructor(video, canvasPreview) {
    this.video = video;
    this.canvasPreview = canvasPreview;
    this.ctxPreview = canvasPreview.getContext("2d");
    this.status = StatusCamera.PARADA;
    this.mensagem = "";
    this.leitura = {
      contagem: null,
      porMao: [],
      // Separação polegar<->indicador em palmas, uma entrada por mão visível
      // (ordenadas por confiança). null = indicador dobrado, não é pinça.
      razoesPinca: [],
      razaoPinca: null,
      maosVisiveis: 0,
      confiancaMedia: 0,
      descartadaPorBorda: false,
      sequencia: 0,
    };
    this._landmarker = null;
    this._stream = null;
    this._ultimoTempoVideo = -1;
    this._sequencia = 0;
    this._ultimoResultado = null;
  }

  /**
   * Pede a webcam e carrega o modelo. Só pode ser chamado a partir de um gesto
   * do usuário: os navegadores exigem interação para liberar a câmera.
   */
  async iniciar() {
    this.status = StatusCamera.INICIANDO;
    this.mensagem = "Carregando modelo e abrindo a câmera...";
    try {
      // Câmera e modelo em paralelo: o modelo tem ~7 MB e a permissão da câmera
      // depende do usuário, então não faz sentido serializar as duas esperas.
      const [stream] = await Promise.all([this._abrirCamera(), this._carregarModelo()]);
      this._stream = stream;
      this.video.srcObject = stream;
      await this.video.play();
      this.canvasPreview.width = this.video.videoWidth || LARGURA_CAPTURA;
      this.canvasPreview.height = this.video.videoHeight || ALTURA_CAPTURA;
      this.status = StatusCamera.ATIVA;
      this.mensagem = "";
    } catch (erro) {
      this.status = StatusCamera.INDISPONIVEL;
      this.mensagem = this._traduzirErro(erro);
      this.parar();
    }
    return this.status === StatusCamera.ATIVA;
  }

  /** Encerra o stream e libera a câmera (o LED do dispositivo apaga). */
  parar() {
    if (this._stream) {
      for (const trilha of this._stream.getTracks()) trilha.stop();
      this._stream = null;
    }
    this.video.srcObject = null;
    if (this.status === StatusCamera.ATIVA) this.status = StatusCamera.PARADA;
    this.leitura = {
      ...this.leitura,
      contagem: null,
      porMao: [],
      razoesPinca: [],
      razaoPinca: null,
      maosVisiveis: 0,
    };
  }

  get ativa() {
    return this.status === StatusCamera.ATIVA;
  }

  async _abrirCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("SEM_API");
    }
    return navigator.mediaDevices.getUserMedia({
      video: {
        // facingMode "user" = câmera frontal no celular, que é a que enxerga
        // as mãos de quem está segurando o aparelho.
        facingMode: "user",
        width: { ideal: LARGURA_CAPTURA },
        height: { ideal: ALTURA_CAPTURA },
      },
      audio: false,
    });
  }

  async _carregarModelo() {
    const { FilesetResolver, HandLandmarker } = await import(
      /* @vite-ignore */ `${URL_WASM_MEDIAPIPE.replace("/wasm", "")}/vision_bundle.mjs`
    );
    const fileset = await FilesetResolver.forVisionTasks(URL_WASM_MEDIAPIPE);
    this._landmarker = await HandLandmarker.createFromOptions(fileset, {
      baseOptions: { modelAssetPath: URL_MODELO_MAOS, delegate: "GPU" },
      runningMode: "VIDEO",
      numHands: MAX_MAOS,
      minHandDetectionConfidence: CONFIANCA_MIN_DETECCAO,
      minHandPresenceConfidence: CONFIANCA_MIN_PRESENCA,
      minTrackingConfidence: CONFIANCA_MIN_RASTREIO,
    });
  }

  _traduzirErro(erro) {
    const nome = erro?.name ?? "";
    if (erro?.message === "SEM_API" || nome === "NotSupportedError") {
      return "Este navegador não expõe a câmera. Em celular, use HTTPS e um navegador atual.";
    }
    if (nome === "NotAllowedError" || nome === "SecurityError") {
      return "Permissão de câmera negada. Libere o acesso nas configurações do site e tente de novo.";
    }
    if (nome === "NotFoundError" || nome === "OverconstrainedError") {
      return "Nenhuma câmera encontrada neste dispositivo.";
    }
    if (nome === "NotReadableError") {
      return "A câmera está sendo usada por outro aplicativo. Feche-o e tente de novo.";
    }
    return `Falha ao iniciar a câmera: ${erro?.message ?? erro}`;
  }

  /**
   * Roda a inferência no frame atual do vídeo, se houver um novo.
   * Devolve true quando produziu uma leitura inédita.
   */
  processarFrame() {
    if (!this.ativa || !this._landmarker) return false;
    if (this.video.readyState < 2) return false;
    // O vídeo entrega ~30 fps; sem esta guarda reprocessaríamos o mesmo frame.
    if (this.video.currentTime === this._ultimoTempoVideo) return false;
    this._ultimoTempoVideo = this.video.currentTime;

    const resultado = this._landmarker.detectForVideo(this.video, performance.now());
    this._ultimoResultado = resultado;
    this._sequencia += 1;

    const maos = [];
    const marcos = resultado.landmarks ?? [];
    const lateralidades = resultado.handedness ?? resultado.handednesses ?? [];
    for (let i = 0; i < marcos.length; i += 1) {
      const classificacao = lateralidades[i]?.[0];
      maos.push({
        landmarks: marcos[i],
        // A imagem do preview é espelhada, então invertemos o rótulo para que
        // "Right" signifique a mão direita de quem está na frente da câmera.
        lado: classificacao?.categoryName === "Left" ? "Right" : "Left",
        score: classificacao?.score ?? 1,
      });
    }
    // Três ou mais mãos: fica só com as duas de maior confiança.
    maos.sort((a, b) => b.score - a.score);
    const selecionadas = maos.slice(0, MAX_MAOS);

    const { total, porMao, descartadaPorBorda } = contarDedosTotal(selecionadas);
    // Medida em TODAS as mãos visíveis (a lista já vem ordenada por
    // confiança): a primeira comanda o zoom, e as duas juntas formam o gesto
    // de comando das luas — o único ainda livre.
    const razoesPinca = selecionadas.map((m) => medirPinca(m.landmarks, m.lado));
    this.leitura = {
      contagem: total,
      porMao,
      razoesPinca,
      razaoPinca: razoesPinca[0] ?? null,
      maosVisiveis: selecionadas.length,
      confiancaMedia: selecionadas.length
        ? selecionadas.reduce((soma, m) => soma + m.score, 0) / selecionadas.length
        : 0,
      descartadaPorBorda,
      // As mãos cruas seguem no resultado MESMO com o frame descartado pela
      // borda: quem lê formato (o "L") filtra mão por mão e ainda aproveita a
      // que está inteira. Sem isso, uma segunda mão encostando na borda zerava
      // o modo luas — e o polegar do L encosta na borda com frequência.
      maos: selecionadas.map(({ landmarks, lado }) => ({ landmarks, lado })),
      sequencia: this._sequencia,
    };
    return true;
  }

  /** Redesenha o preview espelhado com o esqueleto da mão por cima. */
  desenharPreview() {
    const ctx = this.ctxPreview;
    const { width, height } = this.canvasPreview;
    ctx.save();
    ctx.clearRect(0, 0, width, height);
    if (!this.ativa || this.video.readyState < 2) {
      ctx.restore();
      return;
    }
    // Espelha para o usuário se ver como num espelho.
    ctx.translate(width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(this.video, 0, 0, width, height);

    const marcos = this._ultimoResultado?.landmarks ?? [];
    for (const mao of marcos) {
      ctx.strokeStyle = "rgba(120, 200, 255, 0.9)";
      ctx.lineWidth = Math.max(1.5, width / 220);
      for (const [a, b] of CONEXOES_MAO) {
        ctx.beginPath();
        ctx.moveTo(mao[a].x * width, mao[a].y * height);
        ctx.lineTo(mao[b].x * width, mao[b].y * height);
        ctx.stroke();
      }
      ctx.fillStyle = "rgba(255, 214, 96, 0.95)";
      const raio = Math.max(2, width / 150);
      for (const ponto of mao) {
        ctx.beginPath();
        ctx.arc(ponto.x * width, ponto.y * height, raio, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.restore();
  }
}
