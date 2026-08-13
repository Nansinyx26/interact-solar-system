/**
 * Ficha com os dados astronômicos do corpo focado.
 *
 * Diferente da versão desktop (que desenha o card no próprio canvas), aqui a
 * ficha é HTML: fica nítida em qualquer densidade de tela e o CSS a reposiciona
 * sozinha entre desktop e celular.
 */

const formatadorInteiro = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

function formatarDecimal(valor, casas = 2) {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }).format(valor);
}

/** Período orbital em anos terrestres quando faz sentido, senão em dias. */
function formatarPeriodoOrbital(corpo) {
  if (corpo.periodoOrbitalDias <= 0) return "— (orbita o centro da Galáxia)";
  const dias = corpo.periodoOrbitalDias;
  if (dias < 365.26) return `${formatarDecimal(dias)} dias`;
  return `${formatarDecimal(dias / 365.26)} anos (${formatadorInteiro.format(dias)} dias)`;
}

/** Período de rotação, sinalizando giro retrógrado. */
function formatarRotacao(corpo) {
  const sufixo = corpo.periodoRotacaoHoras < 0 ? " (retrógrada)" : "";
  const horas = Math.abs(corpo.periodoRotacaoHoras);
  if (horas >= 48) return `${formatarDecimal(horas / 24)} dias${sufixo}`;
  return `${formatarDecimal(horas)} h${sufixo}`;
}

/** Rótulo da distância — satélites medem do corpo-pai, não do Sol. */
function rotuloDistancia(corpo) {
  return corpo.orbitaEmTornoDe
    ? `Distância média à ${corpo.orbitaEmTornoDe}`
    : "Distância média ao Sol";
}

/**
 * Distância média em UA e km, ou só em km para satélites.
 *
 * A UA é uma unidade heliocêntrica: expressar a órbita da Lua em UA daria
 * 0,00257 — um número exato e inútil. Para satélites fica só o valor em km.
 */
function formatarDistancia(corpo) {
  if (corpo.orbitaEmTornoDe) return `${formatadorInteiro.format(corpo.distanciaKm)} km`;
  if (corpo.distanciaUa <= 0) return "0 (centro do sistema)";
  return `${formatarDecimal(corpo.distanciaUa, 3)} UA<br>${formatadorInteiro.format(
    corpo.distanciaKm,
  )} km`;
}

/**
 * O `tipo` é um identificador interno (sem acento, minúsculo): a ficha mostra a
 * forma legível, senão a Lua aparece como "Satelite".
 */
const NOMES_DE_TIPO = {
  estrela: "Estrela",
  rochoso: "Planeta rochoso",
  gasoso: "Gigante gasoso",
  satelite: "Satélite natural",
};

/** Nome legível do tipo do corpo, para o subtítulo da ficha. */
export function nomeDoTipo(corpo) {
  return NOMES_DE_TIPO[corpo.tipo] ?? corpo.tipo.charAt(0).toUpperCase() + corpo.tipo.slice(1);
}

/** Pares (rótulo, valor) exibidos no card. */
export function linhasDaFicha(corpo) {
  return [
    ["Diâmetro equatorial", `${formatadorInteiro.format(corpo.diametroKm)} km`],
    [rotuloDistancia(corpo), formatarDistancia(corpo)],
    ["Período orbital", formatarPeriodoOrbital(corpo)],
    ["Período de rotação", formatarRotacao(corpo)],
    ["Luas conhecidas", formatadorInteiro.format(corpo.luas)],
    ["Temperatura média", `${formatarDecimal(corpo.temperaturaMediaC, 1)} °C`],
    ["Inclinação axial", `${formatarDecimal(corpo.inclinacaoAxialGraus)}°`],
  ];
}

export class Ficha {
  constructor(raiz) {
    this.raiz = raiz;
    this.titulo = raiz.querySelector("[data-ficha-titulo]");
    this.legenda = raiz.querySelector("[data-ficha-legenda]");
    this.faixa = raiz.querySelector("[data-ficha-faixa]");
    this.dados = raiz.querySelector("[data-ficha-dados]");
    this.fato = raiz.querySelector("[data-ficha-fato]");
    this.corpoAtual = null;
  }

  /** Preenche e revela a ficha (a animação de entrada fica no CSS). */
  mostrar(corpo) {
    if (this.corpoAtual?.nome === corpo.nome) return;
    this.corpoAtual = corpo;

    this.titulo.textContent = corpo.nome;
    this.legenda.textContent = `${nomeDoTipo(corpo)} · gesto ${corpo.indiceGesto}`;
    this.faixa.style.background = `rgb(${corpo.corBase.join(", ")})`;

    this.dados.innerHTML = linhasDaFicha(corpo)
      .map(
        ([rotulo, valor]) =>
          `<div class="item"><dt>${rotulo}</dt><dd>${valor}</dd></div>`,
      )
      .join("");
    this.fato.textContent = corpo.fatoCurioso;

    // Reinicia a animação de entrada mesmo trocando direto de um corpo a outro.
    this.raiz.classList.remove("visivel");
    void this.raiz.offsetWidth;
    this.raiz.classList.add("visivel");
    this.raiz.hidden = false;
  }

  /** Esconde a ficha ao voltar para a visão geral. */
  ocultar() {
    if (!this.corpoAtual) return;
    this.corpoAtual = null;
    this.raiz.classList.remove("visivel");
  }
}
