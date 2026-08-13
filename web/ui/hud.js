/**
 * HUD: indicadores de gesto, avisos, legenda e botões de toque.
 *
 * Todo o HUD é DOM (não canvas): o texto fica nítido em telas de alta densidade
 * e o CSS reorganiza tudo sozinho entre desktop e celular.
 */

import { GESTO_VISAO_GERAL, LIMIAR_AVISO_CONFIANCA } from "../config.js";
import { CORPOS } from "../dados/planetas.js";
import { StatusCamera } from "../gestos/detector.js";

const MAXIMO_DEDOS_UMA_MAO = 5;
/** Perímetro do círculo de progresso (r = 34 no SVG do index.html). */
const PERIMETRO_ANEL = 2 * Math.PI * 34;

export class HUD {
  constructor(raiz) {
    this.fps = raiz.querySelector("[data-fps]");
    this.tempo = raiz.querySelector("[data-escala-tempo]");
    this.detectado = raiz.querySelector("[data-detectado]");
    this.confirmado = raiz.querySelector("[data-confirmado]");
    this.alvo = raiz.querySelector("[data-alvo]");
    this.maos = raiz.querySelector("[data-maos]");
    this.anel = raiz.querySelector("[data-anel-progresso]");
    this.avisos = raiz.querySelector("[data-avisos]");
    this.legenda = raiz.querySelector("[data-legenda]");

    this.anel.style.strokeDasharray = `${PERIMETRO_ANEL}`;
    this.anel.style.strokeDashoffset = `${PERIMETRO_ANEL}`;
    this._montarLegenda();
    this._avisosAtuais = "";
  }

  _montarLegenda() {
    const itens = CORPOS.map(
      (corpo) =>
        `<li><b>${corpo.indiceGesto}</b><span>${corpo.nome}</span></li>`,
    );
    itens.push(
      `<li class="comando"><b>${GESTO_VISAO_GERAL}</b><span>visão geral (tecla V)</span></li>`,
    );
    this.legenda.innerHTML = itens.join("");
  }

  /**
   * Atualiza todos os indicadores.
   * @param {object} estado leitura, resultado do estabilizador e contexto do app
   */
  atualizar(estado) {
    const { leitura, resultado, corpoAlvo, fps, escalaTempo, pausado, detector } = estado;

    this.fps.textContent = `${fps.toFixed(0)} FPS`;
    this.tempo.textContent = `tempo ×${escalaTempo.toFixed(1)}${pausado ? " · PAUSADO" : ""}`;

    this.detectado.textContent = leitura.contagem === null ? "—" : String(leitura.contagem);
    this.detectado.classList.toggle("inativo", leitura.contagem === null);

    const confirmado = resultado.valorConfirmado ?? corpoAlvo?.indiceGesto ?? null;
    this.confirmado.textContent = confirmado === null ? "—" : String(confirmado);
    this.alvo.textContent = corpoAlvo ? corpoAlvo.nome : "visão geral";

    // Detalhe por mão: com 6-8 é o que revela se a segunda mão foi perdida
    // ("1 mão: 5") ou se uma delas está contando errado ("2 mãos: 5+0").
    this.maos.textContent = leitura.porMao?.length
      ? `${leitura.maosVisiveis} mão(s): ${leitura.porMao.join("+")}`
      : `${leitura.maosVisiveis} mão(s)`;

    const progresso = Math.min(1, Math.max(0, resultado.progresso ?? 0));
    this.anel.style.strokeDashoffset = `${PERIMETRO_ANEL * (1 - progresso)}`;
    this.anel.classList.toggle("cooldown", Boolean(resultado.emCooldown));

    this._atualizarAvisos(leitura, detector);
  }

  _atualizarAvisos(leitura, detector) {
    const avisos = [];
    if (detector.status === StatusCamera.INDISPONIVEL) {
      avisos.push(["erro", detector.mensagem]);
    } else if (detector.status === StatusCamera.INICIANDO) {
      avisos.push(["neutro", detector.mensagem || "Abrindo a câmera..."]);
    } else if (detector.status === StatusCamera.ATIVA) {
      if (leitura.maosVisiveis > 0 && leitura.confiancaMedia < LIMIAR_AVISO_CONFIANCA) {
        avisos.push(["aviso", "Confiança baixa — aproxime e centralize a mão."]);
      }
      if (leitura.descartadaPorBorda) {
        avisos.push(["aviso", "Mão saindo do quadro — leitura descartada."]);
      }
      if (leitura.contagem === MAXIMO_DEDOS_UMA_MAO) {
        avisos.push(["dica", "Use as duas mãos para 6–8 (ex.: 5 + 3 = Netuno)."]);
      }
    }

    // Só toca no DOM quando o conteúdo muda: isto roda a 60 Hz.
    const assinatura = avisos.map(([t, m]) => `${t}:${m}`).join("|");
    if (assinatura === this._avisosAtuais) return;
    this._avisosAtuais = assinatura;
    this.avisos.innerHTML = avisos
      .map(([tipo, mensagem]) => `<p class="${tipo}">${mensagem}</p>`)
      .join("");
  }
}
