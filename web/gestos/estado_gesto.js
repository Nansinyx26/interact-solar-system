/**
 * Máquina de estados dos gestos: transforma landmarks em INTENÇÃO.
 *
 * Espelha o `gestos/estado_gesto.py` do desktop. Não conhece canvas nem
 * renderizador — recebe as mãos detectadas e devolve o que o usuário quis
 * dizer. Quem aplica é o loop principal.
 *
 * A regra central é a ordem de leitura. O "L" consome dois dedos, então ele
 * **não pode entrar na contagem numérica**: a forma é classificada antes de
 * qualquer soma. Sem isso, uma mão em L somaria 2 e o modo luas ligaria já
 * selecionando Vênus.
 */

import {
  BUFFER_SELECAO_LUA,
  COOLDOWN_SELECAO_LUA_S,
  FRAMES_PARA_ENTRAR_MODO_LUAS,
  FRAMES_PARA_SAIR_MODO_LUAS,
  VOTOS_SELECAO_LUA,
} from "../config.js";
import { contarDedos, maoDentroDoQuadro } from "./contador.js";
import { ehFormatoL } from "./formatos_mao.js";

/** Estados NORMAL e LUAS, com histerese e votação. */
export class MaquinaGestos {
  constructor() {
    this.modoLuas = false;
    this._framesComL = 0;
    this._framesSemL = 0;
    this._bufferLua = [];
    this._luaConfirmada = null;
    this._instanteUltimaLua = -COOLDOWN_SELECAO_LUA_S;
  }

  /** Volta ao modo normal (usado pelo gesto 10 e pelo ESC). */
  reiniciar() {
    this.modoLuas = false;
    this._framesComL = 0;
    this._framesSemL = 0;
    this._bufferLua = [];
    this._luaConfirmada = null;
  }

  /**
   * Liga/desliga o modo pela tecla, sem passar pela histerese.
   *
   * Existe para dar um caminho sem câmera ao mesmo estado que o gesto "L"
   * alcança — teclado é o plano B quando a webcam não colabora, e também é o
   * que torna o modo testável sem mãos na frente da tela.
   */
  alternarModoLuas() {
    this.modoLuas = !this.modoLuas;
    this._framesComL = 0;
    this._framesSemL = 0;
    this._bufferLua = [];
    return this.modoLuas;
  }

  /** Classifica as mãos e devolve a intenção do frame. */
  atualizar(maos, agora) {
    // 1. Descartar mãos cortadas pela borda antes de qualquer decisão.
    const usaveis = maos.filter(({ landmarks }) => maoDentroDoQuadro(landmarks));

    // 2. Classificar a FORMA de cada mão antes de contar qualquer dedo.
    const formas = usaveis.map((mao) => ({
      ...mao,
      ehL: ehFormatoL(mao.landmarks, mao.lado),
    }));
    const maosEmL = formas.filter((f) => f.ehL);
    const outras = formas.filter((f) => !f.ehL);

    // 3. Duas mãos em L é estado inválido: não muda nada.
    if (maosEmL.length >= 2) {
      return {
        modoLuas: this.modoLuas,
        numero: null,
        progressoModo: this._progresso(),
        modoMudou: false,
        lDetectado: true,
        luaConfirmada: null,
      };
    }

    const temL = maosEmL.length === 1;
    const modoMudou = this._atualizarHisterese(temL);

    // 4. O número sai da mão que NÃO faz o L.
    let numero;
    if (temL) {
      // Só a mão do L na tela: número 0 (mostrar todas as luas).
      numero = outras.length ? contarDedos(outras[0].landmarks, outras[0].lado) : 0;
    } else if (usaveis.length) {
      numero = usaveis.reduce((s, m) => s + contarDedos(m.landmarks, m.lado), 0);
    } else {
      numero = null;
    }

    const luaConfirmada = this.modoLuas ? this._votarLua(numero, agora) : null;

    return {
      modoLuas: this.modoLuas,
      numero,
      progressoModo: this._progresso(),
      modoMudou,
      lDetectado: temL,
      luaConfirmada,
    };
  }

  // ---------------------------------------------------------------- internos
  /** Conta frames consecutivos e troca o modo quando o limite é atingido. */
  _atualizarHisterese(temL) {
    if (temL) {
      this._framesComL += 1;
      this._framesSemL = 0;
    } else {
      this._framesSemL += 1;
      this._framesComL = 0;
    }

    if (!this.modoLuas && this._framesComL >= FRAMES_PARA_ENTRAR_MODO_LUAS) {
      this.modoLuas = true;
      this._bufferLua = [];
      return true;
    }
    if (this.modoLuas && this._framesSemL >= FRAMES_PARA_SAIR_MODO_LUAS) {
      this.modoLuas = false;
      // A lua escolhida PERMANECE: sair do modo é largar o modificador, não
      // desfazer a escolha.
      return true;
    }
    return false;
  }

  /** Quanto falta para a próxima troca de modo, de 0 a 1. */
  _progresso() {
    if (this.modoLuas) {
      return Math.min(1, this._framesSemL / FRAMES_PARA_SAIR_MODO_LUAS);
    }
    return Math.min(1, this._framesComL / FRAMES_PARA_ENTRAR_MODO_LUAS);
  }

  /** Confirma a lua por maioria, com cooldown entre trocas. */
  _votarLua(numero, agora) {
    this._bufferLua.push(numero);
    if (this._bufferLua.length > BUFFER_SELECAO_LUA) this._bufferLua.shift();

    const votos = new Map();
    for (const valor of this._bufferLua) {
      if (valor !== null) votos.set(valor, (votos.get(valor) ?? 0) + 1);
    }
    if (!votos.size) return null;

    let candidato = null;
    let melhor = 0;
    for (const [valor, total] of votos) {
      if (total > melhor) {
        melhor = total;
        candidato = valor;
      }
    }
    if (melhor < VOTOS_SELECAO_LUA) return null;
    if (candidato === this._luaConfirmada) return null;
    if (agora - this._instanteUltimaLua < COOLDOWN_SELECAO_LUA_S) return null;

    this._luaConfirmada = candidato;
    this._instanteUltimaLua = agora;
    return candidato;
  }
}
