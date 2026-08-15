/**
 * Suavização dos 21 landmarks da mão, ANTES de qualquer classificação.
 *
 * Espelha o `gestos/filtro_landmarks.py` do desktop.
 *
 * O reconhecimento piscava por um motivo simples: o MediaPipe entrega cada ponto
 * com alguns pixels de ruído por frame, e um dedo parado exatamente na fronteira
 * do limiar alternava entre "aberto" e "fechado" sem o usuário mexer a mão.
 * Filtrar depois (votando no gesto) esconde o sintoma; filtrar aqui remove a
 * causa — e sai mais barato, porque o filtro roda sobre 21 pontos em vez de
 * sobre uma máquina de estados inteira.
 *
 * Usamos o **One Euro Filter** (Casiez, Roussel e Vogel, 2012). A alternativa
 * óbvia, uma média móvel exponencial de alpha fixo, força um compromisso ruim:
 *
 * - alpha baixo (~0,2): estável parado, mas o gesto chega atrasado;
 * - alpha alto (~0,7): responsivo, mas o tremor passa inteiro.
 *
 * O One Euro resolve variando o alpha com a **velocidade** do ponto: com a mão
 * parada ele filtra forte (o tremor some), com a mão em movimento ele solta (o
 * gesto não atrasa).
 *
 * O módulo não conhece canvas nem MediaPipe: recebe um array de {x, y} e devolve
 * outro do mesmo formato.
 */

import {
  ALPHA_EMA_LANDMARKS,
  UM_EURO_BETA,
  UM_EURO_CORTE_DERIVADA_HZ,
  UM_EURO_CORTE_MINIMO_HZ,
} from "../config.js";

// Piso do intervalo entre amostras. Dois frames com o mesmo instante (ou com o
// relógio andando para trás) dariam divisão por zero no cálculo da velocidade.
const DT_MINIMO = 1e-3;
// Teto: se a mão sumiu por meio segundo, tratamos como amostra nova em vez de
// calcular uma "velocidade" gigantesca a partir de uma pose antiga.
const DT_MAXIMO = 0.5;

/**
 * Converte frequência de corte + intervalo em peso de uma passa-baixa.
 *
 * É a forma discreta do filtro RC: `alpha = dt / (tau + dt)`, com
 * `tau = 1 / (2·pi·fc)`. Corte alto -> alpha perto de 1 (quase sem filtro).
 */
function alphaDeCorte(corteHz, dt) {
  const tau = 1 / (2 * Math.PI * Math.max(corteHz, 1e-6));
  return dt / (tau + dt);
}

/**
 * One Euro Filter aplicado a um array de pontos {x, y}.
 *
 * Guarda o estado de UMA mão. Como o MediaPipe pode trocar a ordem das mãos
 * entre frames, quem chama deve manter uma instância por `handedness` — é o que
 * `BancoDeFiltros` faz.
 */
export class FiltroUmEuro {
  constructor(
    corteMinimoHz = UM_EURO_CORTE_MINIMO_HZ,
    beta = UM_EURO_BETA,
    corteDerivadaHz = UM_EURO_CORTE_DERIVADA_HZ,
  ) {
    this._corteMinimo = corteMinimoHz;
    this._beta = beta;
    this._corteDerivada = corteDerivadaHz;
    this._valor = null; // última saída filtrada
    this._derivada = null; // velocidade filtrada
    this._instante = null;
  }

  /**
   * Esquece o histórico (a mão saiu do quadro e voltou em outro lugar).
   *
   * Sem isto, a mão reaparecendo do outro lado da tela seria interpolada desde
   * a posição antiga e cruzaria o quadro em linha reta por alguns frames —
   * tempo de sobra para produzir contagens absurdas.
   */
  reiniciar() {
    this._valor = null;
    this._derivada = null;
    this._instante = null;
  }

  /** Devolve a versão suavizada de `pontos` (mesmo formato da entrada). */
  filtrar(pontos, agora) {
    if (!this._valor || this._instante === null) {
      // Primeira amostra: não há o que filtrar, ela vira o estado inicial.
      this._valor = pontos.map((p) => ({ x: p.x, y: p.y }));
      this._derivada = pontos.map(() => ({ x: 0, y: 0 }));
      this._instante = agora;
      return this._valor.map((p) => ({ x: p.x, y: p.y }));
    }

    let dt = agora - this._instante;
    if (dt <= 0 || dt > DT_MAXIMO) {
      // Buraco grande na sequência: recomeça em vez de extrapolar.
      this.reiniciar();
      return this.filtrar(pontos, agora);
    }
    dt = Math.max(dt, DT_MINIMO);
    this._instante = agora;

    const alphaDerivada = alphaDeCorte(this._corteDerivada, dt);
    const saida = new Array(pontos.length);

    for (let i = 0; i < pontos.length; i += 1) {
      const alvo = pontos[i];
      const anterior = this._valor[i] ?? { x: alvo.x, y: alvo.y };
      const derivadaAnterior = this._derivada[i] ?? { x: 0, y: 0 };

      // 1. Velocidade bruta, ela mesma suavizada — senão o ruído da posição
      //    entraria duas vezes: uma na saída e outra pela porta do beta.
      const brutaX = (alvo.x - anterior.x) / dt;
      const brutaY = (alvo.y - anterior.y) / dt;
      const dX = alphaDerivada * brutaX + (1 - alphaDerivada) * derivadaAnterior.x;
      const dY = alphaDerivada * brutaY + (1 - alphaDerivada) * derivadaAnterior.y;
      this._derivada[i] = { x: dX, y: dY };

      // 2. Corte adaptativo POR PONTO: cada landmark tem a própria velocidade,
      //    então o polegar em movimento não perde nitidez só porque os outros
      //    quatro dedos estão parados.
      const velocidade = Math.hypot(dX, dY);
      const alpha = alphaDeCorte(this._corteMinimo + this._beta * velocidade, dt);

      const novo = {
        x: alpha * alvo.x + (1 - alpha) * anterior.x,
        y: alpha * alvo.y + (1 - alpha) * anterior.y,
      };
      this._valor[i] = novo;
      saida[i] = { x: novo.x, y: novo.y };
    }
    return saida;
  }
}

/**
 * Média móvel exponencial de alpha fixo — o plano B do One Euro.
 *
 * Mais simples e sem dependência do intervalo entre amostras. Fica disponível
 * porque em máquinas onde a taxa de inferência oscila muito o `dt` do One Euro
 * fica ruidoso, e aí a EMA acaba se saindo melhor.
 */
export class FiltroEMA {
  constructor(alpha = ALPHA_EMA_LANDMARKS) {
    this._alpha = Math.min(1, Math.max(0, alpha));
    this._valor = null;
  }

  reiniciar() {
    this._valor = null;
  }

  /** Suaviza `pontos`. O instante é ignorado (assinatura compartilhada). */
  filtrar(pontos) {
    if (!this._valor) {
      this._valor = pontos.map((p) => ({ x: p.x, y: p.y }));
    } else {
      for (let i = 0; i < pontos.length; i += 1) {
        const anterior = this._valor[i] ?? pontos[i];
        this._valor[i] = {
          x: this._alpha * pontos[i].x + (1 - this._alpha) * anterior.x,
          y: this._alpha * pontos[i].y + (1 - this._alpha) * anterior.y,
        };
      }
    }
    return this._valor.map((p) => ({ x: p.x, y: p.y }));
  }
}

/**
 * Um filtro por mão, endereçado pelo `handedness` do MediaPipe.
 *
 * Manter o estado por LADO (e não pela posição na lista) é o que impede a troca
 * de mão A com mão B: o MediaPipe não garante ordem estável entre frames, e um
 * filtro compartilhado interpolaria a mão esquerda em direção à direita a cada
 * inversão — exatamente o "pisca e troca de gesto sozinho".
 */
export class BancoDeFiltros {
  constructor(usarUmEuro = true) {
    this._usarUmEuro = usarUmEuro;
    this._filtros = new Map();
    this._vistas = new Map();
  }

  _obter(lado) {
    let filtro = this._filtros.get(lado);
    if (!filtro) {
      filtro = this._usarUmEuro ? new FiltroUmEuro() : new FiltroEMA();
      this._filtros.set(lado, filtro);
    }
    return filtro;
  }

  /** Suaviza os landmarks de uma mão identificada por `lado`. */
  filtrar(pontos, lado, agora) {
    this._vistas.set(lado, agora);
    return this._obter(lado).filtrar(pontos, agora);
  }

  /**
   * Zera o histórico das mãos que sumiram há mais de `toleranciaS`.
   *
   * Chamado a cada leitura: uma mão que volta depois de uma ausência longa
   * merece começar do zero, não ser interpolada desde onde estava.
   */
  esquecerAusentes(ladosPresentes, agora, toleranciaS = 0.5) {
    for (const [lado, vistoEm] of [...this._vistas]) {
      if (ladosPresentes.has(lado)) continue;
      if (agora - vistoEm > toleranciaS) {
        this._filtros.delete(lado);
        this._vistas.delete(lado);
      }
    }
  }

  /** Zera tudo (a câmera reconectou, por exemplo). */
  reiniciar() {
    this._filtros.clear();
    this._vistas.clear();
  }
}
