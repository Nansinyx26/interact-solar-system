/**
 * HUD: indicadores de gesto, avisos, legenda e botões de toque.
 *
 * Todo o HUD é DOM (não canvas): o texto fica nítido em telas de alta densidade
 * e o CSS reorganiza tudo sozinho entre desktop e celular.
 *
 * Espelha o ui/hud.py do desktop — mesmos blocos, mesmos rótulos e a mesma regra
 * de realce do corpo em foco. Só o meio de desenho muda.
 */

import {
  ARQUIVO_DOWNLOAD_LOCAL,
  GESTO_MINIMO_DUAS_MAOS,
  GESTO_VISAO_GERAL,
  LIMIAR_AVISO_CONFIANCA,
  URL_DOWNLOAD_EXECUTAVEL,
  VERSAO,
} from "../config.js";
import { CORPOS } from "../dados/planetas.js";
import { StatusCamera } from "../gestos/detector.js";

/** Maior contagem alcançável com uma mão só. */
const MAXIMO_DEDOS_UMA_MAO = GESTO_MINIMO_DUAS_MAOS - 1;
/** Maior gesto que ainda seleciona um corpo (o seguinte é o comando). */
const MAXIMO_GESTO_CORPO = GESTO_VISAO_GERAL - 1;
/** Perímetro do círculo de progresso (r = 34 no SVG do index.html). */
const PERIMETRO_ANEL = 2 * Math.PI * 34;

/** O catálogo guarda a cor como "48, 104, 196" (mesmo literal do desktop). */
const rgb = (cor) => `rgb(${cor})`;

export class HUD {
  constructor(raiz) {
    this.raiz = raiz;
    this.fps = raiz.querySelector("[data-fps]");
    this.tempo = raiz.querySelector("[data-escala-tempo]");
    this.detectado = raiz.querySelector("[data-detectado]");
    this.rodapeAnel = raiz.querySelector("[data-rodape-anel]");
    this.confirmado = raiz.querySelector("[data-confirmado]");
    this.alvo = raiz.querySelector("[data-alvo]");
    this.alvoCor = raiz.querySelector("[data-alvo-cor]");
    this.maos = raiz.querySelector("[data-maos]");
    this.anel = raiz.querySelector("[data-anel-progresso]");
    this.avisos = raiz.querySelector("[data-avisos]");
    this.legenda = raiz.querySelector("[data-legenda]");
    this.notaLegenda = raiz.querySelector("[data-nota-legenda]");
    this.estadoCamera = raiz.querySelector("[data-estado-camera]");
    this._estadoCameraAtual = "";
    this._rodapeAtual = "";
    this._ativoAtual = null;
    this._botoes = null;

    this.anel.style.strokeDasharray = `${PERIMETRO_ANEL}`;
    this.anel.style.strokeDashoffset = `${PERIMETRO_ANEL}`;
    this._montarLegenda();
    this._avisosAtuais = "";

    // Site e ZIP de download carregam a MESMA versão: é o que permite conferir
    // de bate-pronto se o desktop baixado corresponde ao site que está no ar.
    const versao = raiz.querySelector("[data-versao]");
    if (versao) versao.textContent = `v${VERSAO}`;
    const download = raiz.querySelector("[data-download]");
    if (download) {
      // Com URL externa configurada (GitHub Releases, por exemplo), o botão
      // aponta para lá; sem ela, serve o ZIP gerado ao lado do site.
      const externo = Boolean(URL_DOWNLOAD_EXECUTAVEL);
      download.href = externo ? URL_DOWNLOAD_EXECUTAVEL : ARQUIVO_DOWNLOAD_LOCAL;
      if (externo) {
        download.removeAttribute("download");
        download.rel = "noopener";
      }
      download.title =
        `Windows · versão ${VERSAO}, a mesma deste site — ` +
        "executável pronto + código-fonte";
    }
  }

  _montarLegenda() {
    // A bolinha na cor do corpo é o que deixa achar a linha certa sem ler a
    // lista inteira — é a mesma pista de cor que a cena usa.
    const itens = CORPOS.map(
      (corpo) =>
        `<li data-linha="${corpo.indiceGesto}">` +
        `<i style="background:${rgb(corpo.corBase)}"></i>` +
        `<b>${corpo.indiceGesto}</b><span>${corpo.nome}</span></li>`,
    );
    itens.push(
      `<li class="comando" data-linha="${GESTO_VISAO_GERAL}"><i></i>` +
        `<b>${GESTO_VISAO_GERAL}</b><span>visão geral (tecla V)</span></li>`,
    );
    this.legenda.innerHTML = itens.join("");
    this._linhas = new Map(
      [...this.legenda.querySelectorAll("[data-linha]")].map((no) => [
        Number(no.dataset.linha),
        no,
      ]),
    );
    if (this.notaLegenda) {
      this.notaLegenda.textContent =
        `${GESTO_MINIMO_DUAS_MAOS}–${GESTO_VISAO_GERAL} exigem as duas mãos (ex.: 5+4 = Lua)`;
    }
  }

  /**
   * Atualiza todos os indicadores.
   * @param {object} estado leitura, resultado do estabilizador e contexto do app
   */
  atualizar(estado) {
    const { leitura, resultado, corpoAlvo, fps, escalaTempo, pausado, detector } = estado;

    this.fps.textContent = `${fps.toFixed(0)} FPS`;
    this.tempo.textContent = `tempo ×${escalaTempo.toFixed(1)}${pausado ? " · PAUSADO" : ""}`;
    this.tempo.classList.toggle("pausado", pausado);

    this.detectado.textContent = leitura.contagem === null ? "—" : String(leitura.contagem);
    this.detectado.classList.toggle("inativo", leitura.contagem === null);

    const confirmado = resultado.valorConfirmado ?? corpoAlvo?.indiceGesto ?? null;
    this.confirmado.textContent = confirmado === null ? "—" : String(confirmado);
    this.alvo.textContent = corpoAlvo ? corpoAlvo.nome : "visão geral";
    if (this.alvoCor) {
      this.alvoCor.hidden = !corpoAlvo;
      if (corpoAlvo) this.alvoCor.style.background = rgb(corpoAlvo.corBase);
    }

    // Detalhe por mão: com 6-9 é o que revela se a segunda mão foi perdida
    // ("1 mão: 5") ou se uma delas está contando errado ("2 mãos: 5+0").
    this.maos.textContent = leitura.porMao?.length
      ? `${leitura.maosVisiveis} mão(s): ${leitura.porMao.join("+")}`
      : `${leitura.maosVisiveis} mão(s)`;

    const progresso = Math.min(1, Math.max(0, resultado.progresso ?? 0));
    this.anel.style.strokeDashoffset = `${PERIMETRO_ANEL * (1 - progresso)}`;
    this.anel.classList.toggle("cooldown", Boolean(resultado.emCooldown));

    this._atualizarRodapeAnel(resultado, progresso);
    this._atualizarAtivo(corpoAlvo);
    this._atualizarEstadoCamera(detector, leitura);
    this._atualizarAvisos(leitura, detector);
  }

  /**
   * Rótulo abaixo do anel. Vira instrução enquanto a leitura está sendo
   * confirmada: é o único momento em que o usuário precisa NÃO mexer a mão.
   */
  _atualizarRodapeAnel(resultado, progresso) {
    if (!this.rodapeAnel) return;
    let classe = "";
    let texto = "detectado";
    if (resultado.emCooldown) {
      classe = "cooldown";
      texto = "aguarde";
    } else if (progresso > 0 && resultado.candidato != null) {
      classe = "segurando";
      texto = "segure...";
    }
    if (texto === this._rodapeAtual) return;
    this._rodapeAtual = texto;
    this.rodapeAnel.textContent = texto;
    this.rodapeAnel.className = `rodape-anel ${classe}`;
  }

  /**
   * Realça a linha da legenda e o botão do corpo em foco. Sem foco, o realce vai
   * para o comando de visão geral — sempre há exatamente uma linha ativa.
   */
  _atualizarAtivo(corpoAlvo) {
    const ativo = corpoAlvo ? corpoAlvo.indiceGesto : GESTO_VISAO_GERAL;
    if (ativo === this._ativoAtual) return;

    this._linhas?.get(this._ativoAtual)?.classList.remove("ativo");
    this._linhas?.get(ativo)?.classList.add("ativo");

    // Os botões de toque nascem depois do HUD (o app.js os monta em seguida),
    // então a consulta fica adiada até eles existirem.
    if (!this._botoes) {
      const encontrados = this.raiz.querySelectorAll("[data-gesto]");
      if (encontrados.length) {
        this._botoes = new Map(
          [...encontrados].map((no) => [
            no.dataset.gesto === "visao" ? GESTO_VISAO_GERAL : Number(no.dataset.gesto),
            no,
          ]),
        );
      }
    }
    this._botoes?.get(this._ativoAtual)?.classList.remove("ativo");
    this._botoes?.get(ativo)?.classList.add("ativo");

    this._ativoAtual = ativo;
  }

  /**
   * Pastilha de estado da câmera: a cor do ponto entrega a situação antes de
   * qualquer leitura de texto. Espelha o `_estado_camera` do HUD desktop.
   */
  _atualizarEstadoCamera(detector, leitura) {
    if (!this.estadoCamera) return;
    let classe = "desligada";
    let texto = "câmera desligada";
    if (detector.status === StatusCamera.INICIANDO) {
      classe = "iniciando";
      texto = "abrindo câmera...";
    } else if (detector.status === StatusCamera.INDISPONIVEL) {
      classe = "erro";
      texto = "câmera indisponível";
    } else if (detector.status === StatusCamera.ATIVA) {
      classe = "ativa";
      texto = leitura.maosVisiveis
        ? `rastreando ${leitura.maosVisiveis} mão(s)`
        : "câmera ativa";
    }
    // Só toca no DOM quando muda: isto roda a 60 Hz.
    const assinatura = `${classe}|${texto}`;
    if (assinatura === this._estadoCameraAtual) return;
    this._estadoCameraAtual = assinatura;
    this.estadoCamera.className = `estado-camera ${classe}`;
    this.estadoCamera.innerHTML = `<i></i>${texto}`;
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
        avisos.push([
          "dica",
          `Use as duas mãos para ${GESTO_MINIMO_DUAS_MAOS}–${MAXIMO_GESTO_CORPO} ` +
            "(ex.: 5 + 4 = Lua).",
        ]);
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
