/**
 * Máquina de estados da seleção de luas por gesto de duas mãos.
 *
 * Espelha o `gestos/seletor_lua.py` do desktop.
 *
 * O fluxo tem quatro estados, e cada transição é comandada por um gesto:
 *
 *     OCIOSO ──(gesto seleciona planeta)──► PLANETA_SELECIONADO
 *                                               │
 *                         (mão A faz "L")       │
 *                                               ▼
 *                                          PREVIEW_LUA ◄──┐
 *                                               │         │ (mão B troca o nº)
 *                         (mesmo número por N   │         │
 *                          leituras seguidas)   ▼         │
 *                                          FICHA_LUA ─────┘
 *                                               │
 *                         (soltar o L, ou ESC)  │
 *                                               ▼
 *                                     PLANETA_SELECIONADO
 *
 * A separação entre PREVIEW e FICHA é o ponto do módulo. Antes, o número da mão
 * B abria a lua direto: passar de 2 para 5 dedos atravessava o 3 e o 4, e cada
 * um abria uma ficha no caminho. Com o preview o usuário "passeia" pelos
 * números livremente — só o número que ele SEGURA vira ficha.
 *
 * O módulo não conhece canvas nem renderizador. Ele recebe o planeta em
 * contexto e a intenção lida dos gestos, e devolve o que deve estar na tela,
 * incluindo a mensagem de HUD para cada caso de borda. Manter as mensagens aqui
 * (e não no `app.js`) é o que garante que teclado e gesto digam a mesma coisa.
 */

import {
  COOLDOWN_SELECAO_LUA_S,
  FALHAS_TOLERADAS_CONFIRMACAO,
  FRAMES_PARA_ABRIR_FICHA_LUA,
} from "../config.js";
import { luasDoPlaneta } from "../dados/planetas.js";

/** Onde o usuário está no fluxo de seleção. */
export const EstadoSelecao = Object.freeze({
  OCIOSO: "ocioso", // nada em foco
  PLANETA_SELECIONADO: "planeta", // planeta em foco, sem modo lua
  PREVIEW_LUA: "preview", // "L" ativo, lua destacada
  FICHA_LUA: "ficha", // ficha aberta
});

/** Traduz "L + número" em preview e ficha, com confirmação por permanência. */
export class SeletorLua {
  constructor() {
    this._estado = EstadoSelecao.OCIOSO;
    this._planeta = null;
    this._lua = null;
    this._indicePreview = null;
    // Contagem de permanência do número atual. Sobe a cada leitura que concorda
    // e desce (sem zerar) a cada leitura que discorda — ver
    // FALHAS_TOLERADAS_CONFIRMACAO.
    this._permanencia = 0;
    this._falhas = 0;
    this._instanteUltimaFicha = -COOLDOWN_SELECAO_LUA_S;
  }

  // ------------------------------------------------------------- consultas
  get estado() {
    return this._estado;
  }

  /** Lua em destaque (preview ou ficha aberta). */
  get lua() {
    return this._lua;
  }

  /** Número da lua em preview (1..N), ou null quando não há destaque. */
  get indicePreview() {
    return this._indicePreview;
  }

  /** True quando a ficha da lua está na tela. */
  get fichaAberta() {
    return this._estado === EstadoSelecao.FICHA_LUA;
  }

  /** 0 a 1 da barra de confirmação (0 quando não há o que confirmar). */
  get progresso() {
    if (this._estado !== EstadoSelecao.PREVIEW_LUA) return 0;
    return Math.min(1, this._permanencia / FRAMES_PARA_ABRIR_FICHA_LUA);
  }

  // -------------------------------------------------------------- comandos
  /**
   * Registra o planeta em contexto (veio de um gesto ou de uma tecla).
   *
   * Trocar de planeta desfaz a lua: os números passam a significar outra lista,
   * e manter a lua antiga em destaque diria que ela pertence ao planeta novo.
   */
  definirPlaneta(planeta) {
    if (planeta === this._planeta) return;
    this._planeta = planeta;
    this._lua = null;
    this._indicePreview = null;
    this._permanencia = 0;
    this._falhas = 0;
    this._estado = planeta
      ? EstadoSelecao.PLANETA_SELECIONADO
      : EstadoSelecao.OCIOSO;
  }

  /** Fecha a ficha e volta ao planeta (tecla ESC). True se havia algo aberto. */
  fecharFicha() {
    if (this._estado !== EstadoSelecao.FICHA_LUA) return false;
    this._estado = EstadoSelecao.PLANETA_SELECIONADO;
    this._lua = null;
    this._indicePreview = null;
    this._permanencia = 0;
    this._falhas = 0;
    return true;
  }

  /** Volta ao início (visão geral / gesto 10). */
  reiniciar() {
    this._estado = EstadoSelecao.OCIOSO;
    this._planeta = null;
    this._lua = null;
    this._indicePreview = null;
    this._permanencia = 0;
    this._falhas = 0;
  }

  // ---------------------------------------------------------------- núcleo
  /**
   * Avança a máquina uma leitura.
   *
   * `modoLuaAtivo` é o "L" já confirmado pela histerese da `MaquinaGestos` —
   * este módulo não classifica forma de mão, só consome a decisão. `numero` é o
   * que a mão B mostra (0 a 5), e `maosVisiveis` existe só para distinguir "não
   * mostrou número" de "não tem a outra mão na tela", que são avisos
   * diferentes.
   */
  atualizar(modoLuaAtivo, numero, maosVisiveis, agora) {
    // --- soltar o "L" fecha a ficha e volta ao planeta -----------------
    if (!modoLuaAtivo) {
      const fechou =
        this._estado === EstadoSelecao.PREVIEW_LUA ||
        this._estado === EstadoSelecao.FICHA_LUA;
      if (fechou) {
        this._estado = this._planeta
          ? EstadoSelecao.PLANETA_SELECIONADO
          : EstadoSelecao.OCIOSO;
        this._lua = null;
        this._indicePreview = null;
        this._permanencia = 0;
        this._falhas = 0;
      }
      return this._resultado("", false, fechou);
    }

    // --- casos de borda que impedem qualquer seleção -------------------
    if (!this._planeta) return this._resultado("Escolha um planeta primeiro.");

    const luas = luasDoPlaneta(this._planeta.nome);
    if (!luas.length) {
      // Mercúrio e Vênus. O modo continua ativo (o "L" está lá), só não há o
      // que selecionar — travar aqui seria pior que avisar.
      return this._resultado(`${this._planeta.nome} não tem luas cadastradas.`);
    }

    // Só a mão do "L" na tela: o modo está ligado, falta o número.
    if (maosVisiveis < 2 || numero === null || numero === undefined) {
      this._permanencia = 0;
      this._falhas = 0;
      return this._resultado("Mostre a outra mão com o número da lua.");
    }

    if (numero === 0) {
      // Zero é "mostrar todas": desfaz o destaque sem sair do modo.
      this._indicePreview = null;
      this._lua = null;
      this._permanencia = 0;
      this._estado = EstadoSelecao.PREVIEW_LUA;
      const plural = luas.length > 1 ? "luas" : "lua";
      return this._resultado(
        `${this._planeta.nome}: todas as ${luas.length} ${plural}.`,
      );
    }

    if (numero > luas.length) {
      // Número maior que o catálogo. Não troca nada — só explica, com o número
      // REAL, para o usuário não ficar tentando o 5 em Marte.
      this._permanencia = 0;
      const plural = luas.length > 1 ? "luas cadastradas" : "lua cadastrada";
      return this._resultado(
        `${this._planeta.nome} tem só ${luas.length} ${plural}.`,
      );
    }

    // --- preview + contagem de permanência -----------------------------
    if (numero !== this._indicePreview) {
      // A tolerância protege uma confirmação EM ANDAMENTO. Com a ficha já
      // aberta não há o que proteger, e absorver as leituras discordantes ali
      // só atrasaria a troca deliberada de lua — o usuário mostra outro número
      // e a tela demoraria a responder.
      const emConfirmacao = this._estado === EstadoSelecao.PREVIEW_LUA;
      if (
        emConfirmacao &&
        this._falhas < FALHAS_TOLERADAS_CONFIRMACAO &&
        this._permanencia > 0
      ) {
        // Uma leitura discordante no meio da contagem é quase sempre uma
        // piscada do rastreio, não uma mudança de ideia: desconta em vez de
        // zerar, senão a confirmação nunca chega ao fim.
        this._falhas += 1;
        this._permanencia = Math.max(0, this._permanencia - 1);
        return this._resultado("");
      }
      // Mudança de ideia mesmo: novo preview, contagem recomeça.
      //
      // Começa em 1, não em 0: esta leitura JÁ é a primeira em que o número
      // aparece, e descontá-la faria a ficha exigir N+1 leituras.
      this._indicePreview = numero;
      this._lua = luas[numero - 1];
      this._permanencia = 1;
      this._falhas = 0;
      // Trocar de número com a ficha aberta volta ao PREVIEW: a ficha nova só
      // aparece quando o novo número for confirmado.
      this._estado = EstadoSelecao.PREVIEW_LUA;
      return this._resultado("");
    }

    // Número estável.
    this._falhas = 0;
    this._lua = luas[numero - 1];

    if (this._estado === EstadoSelecao.FICHA_LUA) {
      // Já aberta e o usuário segue mostrando o mesmo número: nada muda.
      return this._resultado("");
    }

    this._estado = EstadoSelecao.PREVIEW_LUA;
    this._permanencia += 1;

    if (this._permanencia < FRAMES_PARA_ABRIR_FICHA_LUA) return this._resultado("");

    // --- confirmação: abre a ficha -------------------------------------
    if (agora - this._instanteUltimaFicha < COOLDOWN_SELECAO_LUA_S) {
      // Cooldown: acabou de fechar uma ficha e o mesmo gesto abriria outra no
      // frame seguinte. Segura o progresso cheio até liberar.
      return this._resultado("");
    }

    this._instanteUltimaFicha = agora;
    this._estado = EstadoSelecao.FICHA_LUA;
    return this._resultado("", true);
  }

  // --------------------------------------------------------------- interno
  /** Empacota o estado corrente no formato que o loop principal consome. */
  _resultado(aviso, fichaAbriu = false, fichaFechou = false) {
    return {
      estado: this._estado,
      planeta: this._planeta,
      lua: this._lua,
      indice: this._indicePreview,
      progresso: this.progresso,
      aviso,
      fichaAbriu,
      fichaFechou,
    };
  }
}
