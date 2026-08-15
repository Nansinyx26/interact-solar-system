/**
 * Ficha da lua: painel com os dados do satélite em foco.
 *
 * Espelha o `ui/ficha_lua.py` do desktop, com a mesma diferença de sempre entre
 * as duas versões: lá o card é desenhado no canvas, aqui ele é HTML.
 *
 * Vive na coluna DIREITA, ao contrário da ficha do planeta. Não é preciosismo
 * de layout: no modo lua o planeta-mãe continua selecionado e a ficha dele
 * continua aberta à esquerda, e é exatamente a comparação entre as duas —
 * Europa tem 1/4 do diâmetro da Terra, Titã é maior que Mercúrio — que dá
 * sentido a olhar uma lua. Empilhar uma ficha sobre a outra jogaria fora essa
 * leitura.
 */

import { raioKm } from "../dados/luas.js";

const formatadorInteiro = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

function formatarDecimal(valor, casas = 2) {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }).format(valor);
}

/**
 * Massa em notação científica legível, mais a comparação com a Lua.
 *
 * Um número como 4,8e22 kg não diz nada sozinho para o público do projeto. A
 * referência à Lua da Terra é o que transforma o dado em informação — é o mesmo
 * recurso que a ficha do planeta usa ao dar distâncias em UA *e* em km.
 */
export function formatarMassa(kg) {
  if (!kg || kg <= 0) return "— (não medida com precisão)";
  let expoente = 0;
  let mantissa = kg;
  while (mantissa >= 10) {
    mantissa /= 10;
    expoente += 1;
  }
  const texto = `${formatarDecimal(mantissa)} × 10<sup>${expoente}</sup> kg`;

  // 7,342e22 kg = massa da Lua. Comparar com ela é o jeito mais direto de dar
  // escala, já que é a única lua que todo mundo conhece de vista.
  const razao = kg / 7.342e22;
  if (razao >= 1) return `${texto}<br>${formatarDecimal(razao)}× a massa da Lua`;
  return `${texto}<br>${formatarDecimal(1 / razao, 1)}× menor que a Lua`;
}

/** Período orbital em dias/horas, sinalizando órbita retrógrada. */
export function formatarPeriodo(dias) {
  const sufixo = dias < 0 ? " (retrógrada)" : "";
  const absoluto = Math.abs(dias);
  if (absoluto < 1) {
    // Fobos dá uma volta em 7h39: em dias ele viraria "0,32", que esconde o
    // fato mais interessante da lua.
    return `${formatarDecimal(absoluto * 24, 1)} horas${sufixo}`;
  }
  return `${formatarDecimal(absoluto, 3)} dias${sufixo}`;
}

/** Pares (rótulo, valor) exibidos no card da lua. */
export function linhasDaFichaLua(lua) {
  return [
    ["Raio médio", `${formatadorInteiro.format(raioKm(lua))} km`],
    ["Massa", formatarMassa(lua.massaKg)],
    [
      `Distância média a ${lua.planeta}`,
      `${formatadorInteiro.format(lua.distanciaKm)} km`,
    ],
    ["Período orbital", formatarPeriodo(lua.periodoOrbitalDias)],
    ["Composição / superfície", lua.composicao || "—"],
  ];
}

export class FichaLua {
  constructor(raiz) {
    this.raiz = raiz;
    this.titulo = raiz.querySelector("[data-lua-titulo]");
    this.legenda = raiz.querySelector("[data-lua-legenda]");
    this.faixa = raiz.querySelector("[data-lua-faixa]");
    this.dados = raiz.querySelector("[data-lua-dados]");
    this.curiosidade = raiz.querySelector("[data-lua-curiosidade]");
    this.luaAtual = null;
  }

  /** Preenche e revela a ficha (a animação de entrada fica no CSS). */
  mostrar(lua) {
    if (this.luaAtual?.nome === lua.nome) return;
    this.luaAtual = lua;

    this.titulo.textContent = lua.nome;
    this.legenda.textContent = `Lua de ${lua.planeta}`;
    // Faixa na cor da própria lua — o mesmo tom usado para desenhá-la na
    // órbita, então o card e o ponto na tela se identificam.
    this.faixa.style.background = `rgb(${lua.cor.join(", ")})`;

    this.dados.innerHTML = linhasDaFichaLua(lua)
      .map(([rotulo, valor]) => `<div class="item"><dt>${rotulo}</dt><dd>${valor}</dd></div>`)
      .join("");
    this.curiosidade.textContent = lua.fatoCurioso;

    // Reinicia a animação mesmo trocando direto de uma lua para outra.
    this.raiz.classList.remove("visivel");
    void this.raiz.offsetWidth;
    this.raiz.classList.add("visivel");
    this.raiz.hidden = false;
  }

  /** True enquanto o card estiver na tela (o HUD descreve o que se vê). */
  get visivel() {
    return Boolean(this.luaAtual);
  }

  /** Esconde a ficha (soltar o "L" ou tecla ESC). */
  ocultar() {
    if (!this.luaAtual) return;
    this.luaAtual = null;
    this.raiz.classList.remove("visivel");
  }
}
