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
import { CORPOS, luasDoPlaneta } from "../dados/planetas.js";
import { StatusCamera } from "../gestos/detector.js";

/** Maior contagem alcançável com uma mão só. */
const MAXIMO_DEDOS_UMA_MAO = GESTO_MINIMO_DUAS_MAOS - 1;
/** Maior gesto que ainda seleciona um corpo (o seguinte é o comando). */
const MAXIMO_GESTO_CORPO = GESTO_VISAO_GERAL - 1;
/** Perímetro do círculo de progresso (r = 34 no SVG do index.html). */
const PERIMETRO_ANEL = 2 * Math.PI * 34;

/** O catálogo guarda a cor como "48, 104, 196" (mesmo literal do desktop). */
const rgb = (cor) => `rgb(${cor})`;

/**
 * Texto da linha "MODO LUA" do debug, fiel ao que está na TELA.
 *
 * A máquina de estados só é alimentada pelo caminho do GESTO; abrir uma lua
 * pela tecla passa por fora dela. Sem esta correção o painel dizia "ocioso" com
 * a ficha da lua aberta na frente do usuário — justamente o tipo de informação
 * errada que um painel de diagnóstico não pode dar.
 */
function estadoLua(estado) {
  if (estado.fichaLuaAberta && estado.estadoSelecao !== "ficha") {
    return "ficha (teclado)";
  }
  // Sem câmera o seletor nunca é alimentado e fica parado em "ocioso", o que
  // esconderia o modo ligado pela tecla L. Aqui o teclado é o caso normal, não
  // a exceção: o app inteiro funciona sem webcam.
  if (estado.modoLuas && (!estado.estadoSelecao || estado.estadoSelecao === "ocioso")) {
    return "ativo (teclado)";
  }
  return estado.estadoSelecao || (estado.modoLuas ? "ativo" : "—");
}

/** Aceso quando há modo lua ou ficha na tela; apagado quando não há. */
function corEstadoLua(estado) {
  return estado.modoLuas || estado.fichaLuaAberta ? "destaque" : "fraco";
}

/** Verde/amarelo/vermelho conforme o valor cai abaixo dos limiares. */
function faixa(valor, bom, aceitavel) {
  if (valor >= bom) return "sucesso";
  if (valor >= aceitavel) return "aviso";
  return "erro";
}

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
    this.painelLuas = raiz.querySelector("[data-painel-luas]");
    this.rotuloLuas = raiz.querySelector("[data-rotulo-luas]");
    this.planetaLuas = raiz.querySelector("[data-planeta-luas]");
    this.listaLuas = raiz.querySelector("[data-lista-luas]");
    this.barraLuas = raiz.querySelector("[data-barra-luas]");
    this.barraLuasPreenchida = raiz.querySelector("[data-barra-luas-preenchida]");
    this._estadoCameraAtual = "";
    this._rodapeAtual = "";
    this._estadoLuasAtual = "";
    this._ativoAtual = null;
    this._botoes = null;

    this.anel.style.strokeDasharray = `${PERIMETRO_ANEL}`;
    this.anel.style.strokeDashoffset = `${PERIMETRO_ANEL}`;
    this._montarLegenda();
    this._avisosAtuais = "";
    this.debug = raiz.querySelector("[data-debug]");
    this._debugAtual = "";

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
    const { leitura, resultado, corpoAlvo, fps, escalaTempo, pausado, detector, pincaAtiva } =
      estado;

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
    this._atualizarPainelLuas(estado);
    this._atualizarAvisos(leitura, detector, pincaAtiva, estado.avisoLuas, estado.modoLuas);
    this._atualizarDebug(estado);
  }

  /**
   * Painel de diagnóstico do reconhecimento (tecla F3).
   *
   * Existe porque quase todo problema relatado como "o gesto não pega" é na
   * verdade uma de quatro coisas, e sem ver os números não dá para saber qual:
   * FPS no chão, confiança baixa, leitura instável, ou o número certo chegando
   * mas a confirmação nunca completando. O painel mostra as quatro lado a lado.
   */
  _atualizarDebug(estado) {
    if (!this.debug) return;
    if (!estado.debugVisivel) {
      if (!this.debug.hidden) this.debug.hidden = true;
      return;
    }
    this.debug.hidden = false;

    const leitura = estado.leitura;
    const pose = leitura.pose ?? { maos: [] };
    const numero = leitura.contagem === null ? "—" : String(leitura.contagem);
    const porMao = leitura.porMao?.length ? leitura.porMao.join(" + ") : "—";
    const lados = pose.maos.length
      ? pose.maos.map((m) => `${m.lado[0]}:${m.score.toFixed(2)}`).join(" / ")
      : "—";

    const linhas = [
      ["FPS", estado.fps.toFixed(1), faixa(estado.fps, 50, 30)],
      ["PLANETA", estado.planetaSelecionado?.nome ?? "—", "neutro"],
      ["MODO LUA", estadoLua(estado), corEstadoLua(estado)],
      ["NÚMERO", `${numero}  (por mão: ${porMao})`, "neutro"],
      ["ÍNDICE LUA", String(estado.indiceLua ?? "—"), "neutro"],
      ["MÃOS", `${leitura.maosVisiveis}  [${lados}]`, "neutro"],
      ["CONFIANÇA", leitura.confiancaMedia.toFixed(2), faixa(leitura.confiancaMedia, 0.85, 0.7)],
      [
        "ESTABILIDADE",
        `${(leitura.estabilidade ?? 0).toFixed(2)}${leitura.reaproveitada ? "  (reaproveitada)" : ""}`,
        faixa(leitura.estabilidade ?? 0, 0.8, 0.6),
      ],
    ];

    const progresso = Math.min(1, Math.max(0, estado.progressoLua ?? 0));
    const assinatura = linhas.map((l) => l.join(":")).join("|") + progresso.toFixed(2);
    if (assinatura === this._debugAtual) return;
    this._debugAtual = assinatura;

    this.debug.innerHTML =
      `<p class="debug-titulo">DEBUG DE GESTOS · F3</p>` +
      linhas
        .map(
          ([rotulo, valor, classe]) =>
            `<div class="debug-linha"><span>${rotulo}</span>` +
            `<b class="${classe}">${valor}</b></div>`,
        )
        .join("") +
      `<div class="debug-linha"><span>CONFIRMAÇÃO</span>` +
      `<span class="debug-barra"><i style="width:${Math.round(progresso * 100)}%"></i></span></div>`;
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

  _atualizarAvisos(leitura, detector, pincaAtiva, avisoLua = "", modoLuas = false) {
    const avisos = [];
    // O aviso do modo lua vem primeiro: quando ele existe, é a resposta direta
    // ao que o usuário acabou de fazer com as mãos.
    if (avisoLua) avisos.push(["aviso", avisoLua]);
    if (pincaAtiva) {
      // Enquanto a pinça comanda o zoom a seleção por dedos fica suspensa: sem
      // este aviso o usuário acha que o reconhecimento travou.
      avisos.push(["zoom", "MODO ZOOM — afaste ou aproxime polegar e indicador"]);
    }
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
      // A dica dos números altos só faz sentido FORA do modo lua: lá o total é
      // "L (2 dedos) + número da outra mão" e não seleciona corpo nenhum, então
      // sugerir 5+4 mandaria o usuário para o lugar errado.
      if (leitura.contagem === MAXIMO_DEDOS_UMA_MAO && !modoLuas) {
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

  /**
   * Painel superior central do modo luas: lista as luas do planeta focado
   * a partir de luasDoPlaneta() e indica a barra de progresso da histerese.
   */
  _atualizarPainelLuas(estado) {
    if (!this.painelLuas) return;
    const mostrar = Boolean(estado.modoLuas || estado.lDetectado);
    if (!mostrar) {
      if (!this.painelLuas.hidden) {
        this.painelLuas.hidden = true;
        this.avisos.style.top = "";
        this._estadoLuasAtual = "";
      }
      return;
    }

    this.painelLuas.hidden = false;
    this.painelLuas.classList.toggle("ativo", Boolean(estado.modoLuas));

    const planeta = estado.planetaSelecionado && !estado.planetaSelecionado.ehSol ? estado.planetaSelecionado : null;
    const luas = planeta ? luasDoPlaneta(planeta.nome) : [];
    const MAXIMO_LUAS = 5;
    const visiveis = luas.slice(0, MAXIMO_LUAS);
    const restantes = luas.length - visiveis.length;
    const luaAtiva = estado.luaSelecionada ? (estado.luaSelecionada.nome ?? estado.luaSelecionada) : null;
    let rotulo;
    if (estado.fichaLuaAberta) rotulo = "FICHA DA LUA";
    else if (estado.modoLuas) rotulo = "MODO LUA";
    else rotulo = "reconhecendo L...";
    // Duas barras diferentes: fora do modo, a da histerese do "L"; dentro
    // dele, a da confirmação que abre a ficha. É sempre a que está enchendo.
    const progresso = estado.modoLuas
      ? (estado.progressoLua ?? 0)
      : (estado.progressoModo ?? 0);
    const mostrarBarra = progresso > 0 && !estado.fichaLuaAberta;

    const assinatura = `${estado.modoLuas}|${planeta?.nome}|${luaAtiva}|${progresso.toFixed(2)}|${rotulo}|${mostrarBarra}`;
    if (assinatura !== this._estadoLuasAtual) {
      this._estadoLuasAtual = assinatura;

      if (this.rotuloLuas) this.rotuloLuas.textContent = rotulo;

      if (this.planetaLuas) {
        if (!planeta) {
          this.planetaLuas.textContent = "escolha um planeta primeiro";
          this.planetaLuas.className = "painel-luas-planeta vazio";
        } else {
          this.planetaLuas.textContent = planeta.nome;
          this.planetaLuas.className = "painel-luas-planeta";
        }
      }

      if (this.listaLuas) {
        if (planeta && !luas.length) {
          this.listaLuas.innerHTML = `<li class="vazio">não tem luas conhecidas</li>`;
        } else {
          let html = visiveis
            .map((lua, i) => {
              const escolhida = lua.nome === luaAtiva;
              const cor = Array.isArray(lua.cor) ? `rgb(${lua.cor.join(",")})` : rgb(lua.corBase || "200,200,200");
              return (
                `<li class="${escolhida ? "escolhida" : ""}">` +
                `<span class="marcador" style="background:${cor}"></span>` +
                `<b class="indice">${i + 1}</b>` +
                `<span>${lua.nome}</span></li>`
              );
            })
            .join("");
          if (restantes > 0) {
            html += `<li class="restantes"><span class="marcador"></span><span class="indice"></span><span>+${restantes} no catálogo</span></li>`;
          }
          this.listaLuas.innerHTML = html;
        }
      }

      if (this.barraLuas) {
        this.barraLuas.hidden = !mostrarBarra;
        if (this.barraLuasPreenchida) {
          this.barraLuasPreenchida.style.width = `${Math.round(Math.min(1, Math.max(0, progresso)) * 100)}%`;
        }
      }

      const rect = this.painelLuas.getBoundingClientRect();
      if (rect.height > 0) {
        this.avisos.style.top = `${Math.round(rect.bottom + 8)}px`;
      }
    }
  }
}
