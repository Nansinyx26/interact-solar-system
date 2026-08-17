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
  COOLDOWN_APOS_L_S,
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
    // Quando o "L" foi visto pela última vez. Alimenta bloqueandoPlanetas().
    this._instanteUltimoL = -COOLDOWN_APOS_L_S;
  }

  /** Volta ao modo normal (usado pelo gesto 10 e pelo ESC). */
  reiniciar() {
    this.modoLuas = false;
    this._framesComL = 0;
    this._framesSemL = 0;
    this._bufferLua = [];
    this._luaConfirmada = null;
    this._instanteUltimoL = -COOLDOWN_APOS_L_S;
  }

  /**
   * True quando a contagem de dedos NÃO deve selecionar um planeta.
   *
   * Existe porque a seleção de planeta é alimentada pela contagem CRUA do
   * detector, que soma todas as mãos do quadro e desconhece a forma de cada
   * uma. Com o planeta X selecionado, "L" numa mão + 2 dedos na outra devia
   * abrir a lua 2 de X — mas aquele 2 (ou o 4 da soma com os dois dedos do
   * próprio L) chegava ao estabilizador de planetas e levava para Vênus ou
   * Marte antes de o modo lua sequer ligar.
   *
   * A regra passa a ser: havendo um "L" no quadro, o número da outra mão é
   * índice de LUA e nada mais. Só uma contagem sem nenhum L no quadro pode
   * virar planeta — que é a leitura natural de "mostrar dois dedos".
   *
   * Vale também por COOLDOWN_APOS_L_S depois que o L some, cobrindo tanto o
   * piscar do rastreio quanto as poses intermediárias de desfazer o gesto.
   */
  bloqueandoPlanetas(agora) {
    if (this.modoLuas) return true;
    return agora - this._instanteUltimoL < COOLDOWN_APOS_L_S;
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
    // 1. Classificar a FORMA de TODAS as mãos, antes de qualquer contagem e
    //    ANTES do filtro de borda.
    //
    //    A ordem antiga descartava primeiro as mãos cortadas pela borda e só
    //    então olhava a forma — e o "L" é justamente o gesto que mais cai nesse
    //    filtro: o polegar aponta para a lateral e encosta no limite do quadro.
    //    Descartada a mão, sobrava só a do número, `temL` dava false e
    //    "L + 2 dedos" virava um simples "2" — ou seja, Vênus, em vez da lua 2
    //    do planeta selecionado.
    //
    //    Reconhecer a forma primeiro é seguro porque o "L" é geometria relativa
    //    à própria palma (ver formatos_mao.js): ele sobrevive a landmarks um
    //    pouco fora de [0, 1], que o MediaPipe extrapola de qualquer jeito. O
    //    que NÃO sobrevive à borda é a contagem de dedos.
    const formas = maos.map((mao) => ({
      ...mao,
      ehL: ehFormatoL(mao.landmarks, mao.lado),
      noQuadro: maoDentroDoQuadro(mao.landmarks),
    }));
    let maosEmL = formas.filter((f) => f.ehL);

    // 2. Para CONTAR dedos, aí sim só valem mãos inteiras: numa mão cortada ao
    //    meio a contagem é lixo, e é dela que sai o índice da lua.
    const outras = formas.filter((f) => !f.ehL && f.noQuadro);
    // Uma mão conta como presente se está inteira no quadro OU se foi
    // reconhecida como "L" — o seletor de lua exige duas mãos na tela, e sem
    // esta segunda cláusula a mão do L não entrava na conta.
    const usaveis = formas.filter((f) => f.ehL || f.noQuadro);

    // 3. Duas mãos em L: a PRIMEIRA detectada vira âncora e a segunda passa a
    //    valer como mão de número. Antes isto era estado inválido e não mudava
    //    nada — mas fazer o L com as duas mãos é um erro comum de quem está
    //    aprendendo o gesto, e congelar a tela sem explicação era o pior
    //    desfecho possível. Um L conta como 2 dedos, então o usuário vê a lua 2
    //    em preview e entende sozinho o que fazer.
    if (maosEmL.length >= 2) {
      outras.unshift(maosEmL[1]);
      maosEmL = maosEmL.slice(0, 1);
    }

    const temL = maosEmL.length === 1;
    // Marca a presença do L ANTES da histerese: o bloqueio da seleção de
    // planeta precisa valer já no primeiro frame em que a forma aparece, e não
    // só depois das FRAMES_PARA_ENTRAR_MODO_LUAS leituras que confirmam o modo.
    // Era nessa janela que o número escapava para o planeta.
    if (temL) this._instanteUltimoL = agora;
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
      // Quantas mãos utilizáveis havia no quadro. O seletor precisa disto para
      // distinguir "não mostrou número" de "só tem uma mão na tela" — são
      // avisos de HUD diferentes, e o número sozinho não conta essa história.
      maosVisiveis: usaveis.length,
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
      // DESCONTA em vez de zerar. Zerando, uma única leitura ruim no meio do
      // gesto obrigava a recomeçar do zero — e como o "L" precisa de 6 leituras
      // SEGUIDAS, bastava o rastreio piscar uma vez a cada cinco para o modo
      // lua nunca ligar, por mais que o usuário insistisse. Descontando, 4
      // acertos em 5 leituras ainda chegam lá; alternar meio a meio (que não é
      // um L firme) continua não chegando.
      this._framesComL = Math.max(0, this._framesComL - 1);
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
