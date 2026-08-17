/**
 * Desenho da cena do Sistema Solar em Canvas 2D.
 *
 * Todas as texturas são geradas proceduralmente na inicialização — não há uma
 * única imagem baixada. A rotação própria é real: cada corpo tem uma tira
 * equirretangular (mapa "desenrolado") projetada em esfera em QUADROS_ROTACAO
 * fases, pré-renderizadas uma vez e reaproveitadas.
 */

import {
  ACHATAMENTO_ANEL,
  ALPHA_ASTEROIDE_MAX,
  ALPHA_ASTEROIDE_MIN,
  ALPHA_ORBITA_LUA,
  ALPHA_ROTULO_LUA,
  ALPHA_SOMBRA_LUA,
  ASTEROIDES_DESENHADOS,
  ACHATAMENTO_ANEL_URANO,
  ALPHA_CORPO_ESMAECIDO,
  ALPHA_ORBITA_FOCADA,
  ALPHA_ORBITA_NORMAL,
  ALPHA_ORBITA_TENUE,
  ALPHA_SOMBRA_MAX,
  CAMADAS_ESTRELAS,
  COMPRIMENTO_EIXO_URANO,
  CONTRASTE_TERRENO_LUA,
  COR_ANEL_DESTAQUE,
  COR_ANEL_SATURNO,
  COR_ANEL_URANO,
  COR_ASTEROIDE,
  COR_CONTORNO_ROTULO,
  COR_FUNDO,
  COR_ORBITA,
  COR_ORBITA_FOCADA,
  COR_ORBITA_LUA,
  DISTANCIA_MINIMA_ROTULO_LUA_PX,
  ESCALA_RUIDO_LUA,
  ESCALA_RUIDO_TEXTURA,
  ESPESSURA_CONTORNO_ROTULO_PX,
  ESTRELAS_POR_CAMADA,
  FAIXAS_GIGANTE_GASOSO,
  FAIXAS_ROCHOSO,
  FATOR_ANEL_EXTERNO,
  FATOR_ANEL_INTERNO,
  FATOR_ANEL_URANO_EXTERNO,
  FATOR_ANEL_URANO_INTERNO,
  FATOR_HALO_SOL,
  FATOR_PARALLAX,
  FOLGA_ANEL_DESTAQUE_PX,
  INCLINACAO_ANEL_GRAUS,
  INCLINACAO_ANEL_URANO_GRAUS,
  INTENSIDADE_TURBULENCIA,
  LARGURA_TIRA_EM_RAIOS,
  QUADROS_ROTACAO,
  RAIO_ORBITA_LUA_PX,
  RAIO_TEXTURA_LUA_PX,
  RAIO_TEXTURA_PX,
  SEMENTE_ALEATORIA,
  ZOOM_MINIMO_PARA_LUAS,
} from "../config.js";
import { CORPOS, ehSol, luasDoPlaneta } from "../dados/planetas.js";
import { realce, sombra } from "../dados/luas.js";
import {
  anguloDoCinturao,
  anguloIluminacao,
  faixaDoCinturao,
  fatorOrbitaLua,
  posicaoDaLuaMenor,
  faseRotacao,
  raioCorpoPx,
  raioLuaMenorPx,
  raioOrbitalPx,
} from "./orbita.js";

const RAIO_TEX = RAIO_TEXTURA_PX;
const TAM_TEX = RAIO_TEX * 2;
const LARGURA_TIRA = RAIO_TEX * LARGURA_TIRA_EM_RAIOS;
const ALTURA_TIRA = TAM_TEX;

const RAIO_TEX_LUA = RAIO_TEXTURA_LUA_PX;
const TAM_TEX_LUA = RAIO_TEX_LUA * 2;

/** Corpos que ganham calotas polares brancas na textura. */
const CORPOS_COM_CALOTAS = new Set(["Terra", "Marte"]);

/** Fonte única dos rótulos da cena: definida uma vez por frame, não por lua. */
const FONTE_ROTULO = "600 11px system-ui, sans-serif";
const COR_ROTULO_DESTAQUE = "#e8ecf5";
const COR_ROTULO_NORMAL = "#a8b2c9";

/**
 * Níveis de quantização usados para agrupar o que é desenhado aos milhares.
 *
 * Trocar `fillStyle` no Canvas 2D reconfigura o contexto e (com template
 * string) aloca; fazer isso uma vez por partícula era o item mais caro do
 * frame. Agrupando, o custo passa a ser proporcional ao número de FAIXAS, não
 * ao de partículas.
 */
const FAIXAS_BRILHO_ASTEROIDE = 10;
const PASSO_QUANTIZACAO_COR = 12;

/** Arredonda um canal de cor ao múltiplo de PASSO_QUANTIZACAO_COR mais próximo. */
function quantizarCanal(valor) {
  return Math.min(
    255,
    Math.round(valor / PASSO_QUANTIZACAO_COR) * PASSO_QUANTIZACAO_COR,
  );
}

/** PRNG com semente: a cena precisa ser idêntica em toda execução. */
function criarAleatorio(semente) {
  let estado = semente >>> 0;
  return function proximo() {
    estado |= 0;
    estado = (estado + 0x6d2b79f5) | 0;
    let t = Math.imul(estado ^ (estado >>> 15), 1 | estado);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function criarCanvas(largura, altura) {
  const canvas = document.createElement("canvas");
  canvas.width = largura;
  canvas.height = altura;
  return canvas;
}

/** Amplia uma matriz 2D por interpolação bilinear. */
function redimensionarBilinear(mapa, larguraOrigem, alturaOrigem, largura, altura) {
  const saida = new Float64Array(largura * altura);
  for (let y = 0; y < altura; y += 1) {
    const posY = (y * (alturaOrigem - 1)) / (altura - 1);
    const y0 = Math.floor(posY);
    const y1 = Math.min(y0 + 1, alturaOrigem - 1);
    const pesoY = posY - y0;
    for (let x = 0; x < largura; x += 1) {
      const posX = (x * (larguraOrigem - 1)) / (largura - 1);
      const x0 = Math.floor(posX);
      const x1 = Math.min(x0 + 1, larguraOrigem - 1);
      const pesoX = posX - x0;
      const superior =
        mapa[y0 * larguraOrigem + x0] * (1 - pesoX) + mapa[y0 * larguraOrigem + x1] * pesoX;
      const inferior =
        mapa[y1 * larguraOrigem + x0] * (1 - pesoX) + mapa[y1 * larguraOrigem + x1] * pesoX;
      saida[y * largura + x] = superior * (1 - pesoY) + inferior * pesoY;
    }
  }
  return saida;
}

/**
 * Ruído fractal em [0, 1], contínuo na emenda horizontal da tira.
 *
 * `escala` é o número de blocos da primeira oitava: quanto menor, maiores as
 * manchas. As luas usam um valor bem menor que os planetas — ver
 * ESCALA_RUIDO_LUA.
 */
function ruidoSuave(aleatorio, altura, largura, oitavas = 3, escala = ESCALA_RUIDO_TEXTURA) {
  const total = new Float64Array(altura * largura);
  let amplitude = 1;
  let somaAmplitudes = 0;
  for (let oitava = 0; oitava < oitavas; oitava += 1) {
    const blocos = Math.max(2, escala * 2 ** oitava);
    const largBase = blocos + 1;
    const base = new Float64Array(blocos * largBase);
    for (let y = 0; y < blocos; y += 1) {
      for (let x = 0; x < blocos; x += 1) base[y * largBase + x] = aleatorio();
      // A coluna extra repete a primeira: a textura fecha ao dar a volta.
      base[y * largBase + blocos] = base[y * largBase];
    }
    const ampliado = redimensionarBilinear(base, largBase, blocos, largura, altura);
    for (let i = 0; i < total.length; i += 1) total[i] += amplitude * ampliado[i];
    somaAmplitudes += amplitude;
    amplitude *= 0.5;
  }
  for (let i = 0; i < total.length; i += 1) total[i] /= somaAmplitudes;
  return total;
}

/** Mapa "desenrolado" do corpo, em RGB (altura * largura * 3). */
function tiraEquirretangular(corpo) {
  const aleatorio = criarAleatorio(SEMENTE_ALEATORIA + corpo.indiceGesto);
  const ruido = ruidoSuave(aleatorio, ALTURA_TIRA, LARGURA_TIRA);
  const ruidoFino = ruidoSuave(aleatorio, ALTURA_TIRA, LARGURA_TIRA, 4);
  const tira = new Float64Array(ALTURA_TIRA * LARGURA_TIRA * 3);

  const frequencia = corpo.tipo === "gasoso" ? FAIXAS_GIGANTE_GASOSO : FAIXAS_ROCHOSO;
  const [baseR, baseG, baseB] = corpo.corBase;
  const [secR, secG, secB] = corpo.corSecundaria;
  const [detR, detG, detB] = corpo.corDetalhe;

  for (let y = 0; y < ALTURA_TIRA; y += 1) {
    const latitude = (y / (ALTURA_TIRA - 1)) * 2 - 1;
    for (let x = 0; x < LARGURA_TIRA; x += 1) {
      const i = y * LARGURA_TIRA + x;
      const longitude = (x / (LARGURA_TIRA - 1)) * 2 - 1;

      let mistura;
      if (corpo.faixas) {
        const turbulencia = (ruido[i] - 0.5) * INTENSIDADE_TURBULENCIA;
        mistura = 0.5 + 0.5 * Math.sin(latitude * Math.PI * frequencia + turbulencia);
      } else {
        // Manchas irregulares: continentes (Terra), crateras (Mercúrio/Marte),
        // granulação (Sol).
        mistura = Math.min(1, Math.max(0, (ruido[i] - 0.46) * 5));
      }

      let r = baseR * (1 - mistura) + secR * mistura;
      let g = baseG * (1 - mistura) + secG * mistura;
      let b = baseB * (1 - mistura) + secB * mistura;

      // Realces finos (nuvens, cristas, plumas).
      const realce = Math.min(1, Math.max(0, (ruidoFino[i] - 0.68) * 2.4)) * 0.55;
      r = r * (1 - realce) + detR * realce;
      g = g * (1 - realce) + detG * realce;
      b = b * (1 - realce) + detB * realce;

      // Tempestade oval característica (Júpiter, Netuno).
      if (corpo.corTempestade) {
        const distancia =
          ((latitude + 0.3) / 0.16) ** 2 + ((longitude - 0.35) / 0.09) ** 2;
        const peso = Math.sqrt(Math.min(1, Math.max(0, 1 - distancia)));
        if (peso > 0) {
          const [tr, tg, tb] = corpo.corTempestade;
          r = r * (1 - peso) + tr * peso;
          g = g * (1 - peso) + tg * peso;
          b = b * (1 - peso) + tb * peso;
        }
      }

      // Calotas polares.
      if (CORPOS_COM_CALOTAS.has(corpo.nome)) {
        const calota = Math.min(1, Math.max(0, (Math.abs(latitude) - 0.82) * 6));
        if (calota > 0) {
          r = r * (1 - calota) + 238 * calota;
          g = g * (1 - calota) + 244 * calota;
          b = b * (1 - calota) + 250 * calota;
        }
      }

      tira[i * 3] = r;
      tira[i * 3 + 1] = g;
      tira[i * 3 + 2] = b;
    }
  }
  return tira;
}

/**
 * Índices de amostragem da tira para projetar meia esfera no disco.
 * O arcsin nos dois eixos faz a textura comprimir perto da borda, como numa
 * esfera de verdade.
 */
function mapaEsferico() {
  const linhas = new Int32Array(TAM_TEX * TAM_TEX);
  const colunas = new Int32Array(TAM_TEX * TAM_TEX);
  const brilho = new Float64Array(TAM_TEX * TAM_TEX);
  const alpha = new Float64Array(TAM_TEX * TAM_TEX);
  const metadeTira = LARGURA_TIRA / 2;

  for (let y = 0; y < TAM_TEX; y += 1) {
    const v = (y - RAIO_TEX + 0.5) / RAIO_TEX;
    for (let x = 0; x < TAM_TEX; x += 1) {
      const u = (x - RAIO_TEX + 0.5) / RAIO_TEX;
      const i = y * TAM_TEX + x;
      const raioQuadrado = u * u + v * v;

      const latitude = Math.asin(Math.min(1, Math.max(-1, v)));
      const cosLatitude = Math.max(Math.cos(latitude), 1e-6);
      const longitude = Math.asin(Math.min(1, Math.max(-1, u / cosLatitude)));

      // O hemisfério visível cobre metade da tira.
      colunas[i] = Math.floor((longitude / Math.PI + 0.5) * metadeTira);
      linhas[i] = Math.min(
        ALTURA_TIRA - 1,
        Math.max(0, Math.floor((latitude / Math.PI + 0.5) * ALTURA_TIRA)),
      );
      // Escurecimento de limbo + borda suave de 1 px (antisserrilhado barato).
      brilho[i] = 0.45 + 0.55 * Math.min(1, Math.max(0, 1 - raioQuadrado)) ** 0.35;
      alpha[i] = Math.min(1, Math.max(0, (1 - raioQuadrado) * RAIO_TEX * 0.9));
    }
  }
  return { linhas, colunas, brilho, alpha };
}

/** Pré-renderiza o disco do corpo em cada fase de rotação. */
function quadrosRotacao(corpo, mapa) {
  const { linhas, colunas, brilho, alpha } = mapa;
  const tira = tiraEquirretangular(corpo);
  const solar = ehSol(corpo);
  const quadros = [];

  for (let indice = 0; indice < QUADROS_ROTACAO; indice += 1) {
    const deslocamento = Math.floor((indice / QUADROS_ROTACAO) * LARGURA_TIRA);
    const canvas = criarCanvas(TAM_TEX, TAM_TEX);
    const ctx = canvas.getContext("2d");
    const imagem = ctx.createImageData(TAM_TEX, TAM_TEX);
    const dados = imagem.data;

    for (let i = 0; i < TAM_TEX * TAM_TEX; i += 1) {
      if (alpha[i] <= 0) continue;
      const coluna = (colunas[i] + deslocamento) % LARGURA_TIRA;
      const origem = (linhas[i] * LARGURA_TIRA + coluna) * 3;
      // O Sol brilha por conta própria: quase sem escurecimento de limbo.
      const fator = solar ? 0.86 + 0.14 * brilho[i] : brilho[i];
      dados[i * 4] = Math.min(255, tira[origem] * fator);
      dados[i * 4 + 1] = Math.min(255, tira[origem + 1] * fator);
      dados[i * 4 + 2] = Math.min(255, tira[origem + 2] * fator);
      dados[i * 4 + 3] = alpha[i] * 255;
    }
    ctx.putImageData(imagem, 0, 0);
    quadros.push(canvas);
  }
  return quadros;
}

/** Terminador dia/noite: escuro no lado +x, girado no desenho. */
function criarSombra(mapa) {
  const canvas = criarCanvas(TAM_TEX, TAM_TEX);
  const ctx = canvas.getContext("2d");
  const imagem = ctx.createImageData(TAM_TEX, TAM_TEX);
  const dados = imagem.data;
  for (let y = 0; y < TAM_TEX; y += 1) {
    for (let x = 0; x < TAM_TEX; x += 1) {
      const i = y * TAM_TEX + x;
      const u = (x - RAIO_TEX + 0.5) / RAIO_TEX;
      const escuridao = Math.min(1, Math.max(0, (u + 0.15) * 1.5)) ** 1.2;
      dados[i * 4 + 3] = escuridao * mapa.alpha[i] * ALPHA_SOMBRA_MAX * 255;
    }
  }
  ctx.putImageData(imagem, 0, 0);
  return canvas;
}

/**
 * Semente estável a partir do nome (FNV-1a de 32 bits).
 *
 * As luas não têm `indiceGesto` para semear o ruído como os 9 corpos, e usar a
 * posição no catálogo faria a textura de todas mudar ao inserir uma lua nova no
 * meio da lista.
 */
function sementeDoNome(nome) {
  let hash = 2166136261;
  for (let i = 0; i < nome.length; i += 1) {
    hash ^= nome.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

/**
 * Sprite esférico de uma lua: manchas de terreno + escurecimento de limbo.
 *
 * É o mesmo princípio dos planetas, sem a tira equirretangular: as luas não têm
 * rotação própria animada (todas as grandes são síncronas — mostram sempre a
 * mesma face ao planeta), então projetar um mapa que gira seria custo puro. O
 * que falta para o disco parecer esférico é o escurecimento na borda, e isso o
 * ruído sozinho não dá.
 */
function spriteLua(lua) {
  const aleatorio = criarAleatorio(SEMENTE_ALEATORIA + sementeDoNome(lua.nome));
  const ruido = ruidoSuave(aleatorio, TAM_TEX_LUA, TAM_TEX_LUA, 3, ESCALA_RUIDO_LUA);
  // Normalização: a soma de oitavas puxa o ruído para perto de 0,5, e sem
  // esticar de volta para [0, 1] o terreno usa só o miolo da paleta. Era isso
  // que fazia Jápeto — a lua de DOIS hemisférios, um branco e um preto — sair
  // como um bege uniforme, igual a todas as outras.
  let minimo = Infinity;
  let maximo = -Infinity;
  for (let i = 0; i < ruido.length; i += 1) {
    if (ruido[i] < minimo) minimo = ruido[i];
    if (ruido[i] > maximo) maximo = ruido[i];
  }
  const amplitudeRuido = maximo - minimo;
  if (amplitudeRuido > 1e-6) {
    for (let i = 0; i < ruido.length; i += 1) ruido[i] = (ruido[i] - minimo) / amplitudeRuido;
  }

  const [baseR, baseG, baseB] = lua.cor;
  const [claraR, claraG, claraB] = realce(lua);
  const [escuraR, escuraG, escuraB] = sombra(lua);

  const canvas = criarCanvas(TAM_TEX_LUA, TAM_TEX_LUA);
  const ctx = canvas.getContext("2d");
  const imagem = ctx.createImageData(TAM_TEX_LUA, TAM_TEX_LUA);
  const dados = imagem.data;

  for (let y = 0; y < TAM_TEX_LUA; y += 1) {
    const v = (y - RAIO_TEX_LUA + 0.5) / RAIO_TEX_LUA;
    for (let x = 0; x < TAM_TEX_LUA; x += 1) {
      const i = y * TAM_TEX_LUA + x;
      const u = (x - RAIO_TEX_LUA + 0.5) / RAIO_TEX_LUA;
      const raioQuadrado = u * u + v * v;
      // Mesma borda suave de 1 px dos planetas: antisserrilhado barato.
      const alpha = Math.min(1, Math.max(0, (1 - raioQuadrado) * RAIO_TEX_LUA * 0.9));
      if (alpha <= 0) continue;

      // Terreno: o ruído puxa para o tom claro acima de 0,5 e para o escuro
      // abaixo. Centrado, para que a cor média do disco continue sendo `cor`.
      const desvio = (ruido[i] - 0.5) * 2 * CONTRASTE_TERRENO_LUA;
      let r;
      let g;
      let b;
      if (desvio >= 0) {
        r = baseR + (claraR - baseR) * desvio;
        g = baseG + (claraG - baseG) * desvio;
        b = baseB + (claraB - baseB) * desvio;
      } else {
        r = baseR + (escuraR - baseR) * -desvio;
        g = baseG + (escuraG - baseG) * -desvio;
        b = baseB + (escuraB - baseB) * -desvio;
      }

      const brilho = 0.45 + 0.55 * Math.min(1, Math.max(0, 1 - raioQuadrado)) ** 0.35;
      dados[i * 4] = Math.min(255, r * brilho);
      dados[i * 4 + 1] = Math.min(255, g * brilho);
      dados[i * 4 + 2] = Math.min(255, b * brilho);
      dados[i * 4 + 3] = alpha * 255;
    }
  }
  ctx.putImageData(imagem, 0, 0);
  return canvas;
}

/**
 * Terminador dia/noite da lua, escuro no lado +x e girado no desenho.
 *
 * Um só para todas: a sombra não depende da cor da lua, e 22 cópias idênticas
 * na memória não comprariam nada.
 */
function criarSombraLua() {
  const canvas = criarCanvas(TAM_TEX_LUA, TAM_TEX_LUA);
  const ctx = canvas.getContext("2d");
  const imagem = ctx.createImageData(TAM_TEX_LUA, TAM_TEX_LUA);
  const dados = imagem.data;
  for (let y = 0; y < TAM_TEX_LUA; y += 1) {
    const v = (y - RAIO_TEX_LUA + 0.5) / RAIO_TEX_LUA;
    for (let x = 0; x < TAM_TEX_LUA; x += 1) {
      const i = y * TAM_TEX_LUA + x;
      const u = (x - RAIO_TEX_LUA + 0.5) / RAIO_TEX_LUA;
      const disco = Math.min(1, Math.max(0, (1 - (u * u + v * v)) * RAIO_TEX_LUA * 0.9));
      if (disco <= 0) continue;
      const escuridao = Math.min(1, Math.max(0, (u + 0.15) * 1.5)) ** 1.2;
      dados[i * 4 + 3] = escuridao * disco * ALPHA_SOMBRA_LUA * 255;
    }
  }
  ctx.putImageData(imagem, 0, 0);
  return canvas;
}

/** Gera um anel elíptico com faixas e divisão de Cassini, já inclinado. */
function criarAnel(fatorInterno, fatorExterno, achatamento, cor, inclinacaoGraus) {
  const largura = Math.round(RAIO_TEX * fatorExterno * 2);
  const altura = Math.max(4, Math.round(largura * achatamento));
  const plano = criarCanvas(largura, altura);
  const ctx = plano.getContext("2d");
  const imagem = ctx.createImageData(largura, altura);
  const dados = imagem.data;
  const [corR, corG, corB] = cor.split(",").map((valor) => Number(valor.trim()));
  const meio = (fatorInterno + fatorExterno) / 2;

  for (let y = 0; y < altura; y += 1) {
    const v = ((y - altura / 2) / (altura / 2)) * fatorExterno;
    for (let x = 0; x < largura; x += 1) {
      const u = ((x - largura / 2) / (largura / 2)) * fatorExterno;
      const raio = Math.hypot(u, v);
      const i = (y * largura + x) * 4;
      if (raio < fatorInterno || raio > fatorExterno) continue;
      const faixa = 0.55 + 0.45 * Math.sin(raio * 34);
      const lacuna = Math.min(1, Math.abs(raio - meio) * 26);
      dados[i] = corR;
      dados[i + 1] = corG;
      dados[i + 2] = corB;
      dados[i + 3] = faixa * lacuna * 210;
    }
  }
  ctx.putImageData(imagem, 0, 0);

  if (!inclinacaoGraus) return plano;
  // Pré-inclina uma vez: no desenho o anel só é escalado e recortado ao meio.
  const lado = Math.ceil(Math.hypot(largura, altura));
  const girado = criarCanvas(lado, lado);
  const ctxGirado = girado.getContext("2d");
  ctxGirado.translate(lado / 2, lado / 2);
  ctxGirado.rotate((-inclinacaoGraus * Math.PI) / 180);
  ctxGirado.drawImage(plano, -largura / 2, -altura / 2);
  return girado;
}

export class Renderizador {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.largura = canvas.width;
    this.altura = canvas.height;

    const mapa = mapaEsferico();
    this.quadros = new Map(CORPOS.map((c) => [c.nome, quadrosRotacao(c, mapa)]));
    this.sombra = criarSombra(mapa);
    this.aneis = new Map([
      [
        "Saturno",
        {
          imagem: criarAnel(
            FATOR_ANEL_INTERNO,
            FATOR_ANEL_EXTERNO,
            ACHATAMENTO_ANEL,
            COR_ANEL_SATURNO,
            INCLINACAO_ANEL_GRAUS,
          ),
          eixo: "horizontal",
        },
      ],
      // Urano quase deitado: o anel aparece "de pé" e a divisão é vertical.
      [
        "Urano",
        {
          imagem: criarAnel(
            FATOR_ANEL_URANO_INTERNO,
            FATOR_ANEL_URANO_EXTERNO,
            ACHATAMENTO_ANEL_URANO,
            COR_ANEL_URANO,
            INCLINACAO_ANEL_URANO_GRAUS,
          ),
          eixo: "vertical",
        },
      ],
    ]);
    // Um sprite por lua do catálogo, gerado uma vez. São 22 discos de 40x40 —
    // menos memória que UM quadro de rotação de planeta.
    this.spritesLua = new Map();
    for (const corpo of CORPOS) {
      for (const lua of luasDoPlaneta(corpo.nome)) {
        if (!this.spritesLua.has(lua.nome)) {
          this.spritesLua.set(lua.nome, spriteLua(lua));
        }
      }
    }
    this.sombraLua = criarSombraLua();

    this.asteroides = this._criarAsteroides();
    this.estrelas = this._criarEstrelas();
    // Reaproveitados a cada frame para não alocar no laço quente do desenho.
    this._rotulosDesenhados = [];
  }

  redimensionar(largura, altura) {
    this.largura = largura;
    this.altura = altura;
  }

  /**
   * Sorteia (raio, ângulo, brilho, tamanho) de cada asteroide, já AGRUPADO por
   * faixa de brilho.
   *
   * Semente fixa, como o campo de estrelas: o cinturão precisa ser o mesmo em
   * toda execução. A densidade cai perto das bordas — no cinturão real as
   * lacunas de Kirkwood e o próprio espalhamento deixam o miolo mais cheio.
   *
   * O agrupamento é o que tira o cinturão do caminho crítico: com 340 brilhos
   * distintos, o desenho trocava `fillStyle` 340 vezes por frame, e cada troca
   * é uma string nova e uma reconfiguração do contexto. Quantizado em
   * FAIXAS_BRILHO_ASTEROIDE níveis, são 10 trocas e um único `fill()` por
   * nível — a olho nu o cinturão é o mesmo, porque a diferença entre dois
   * níveis vizinhos é de 4% de opacidade num ponto de 1 px.
   */
  _criarAsteroides() {
    const aleatorio = criarAleatorio(SEMENTE_ALEATORIA + 977);
    const [interno, externo] = faixaDoCinturao();
    const meio = (interno + externo) / 2;
    const largura = (externo - interno) / 2;
    const grupos = Array.from({ length: FAIXAS_BRILHO_ASTEROIDE }, (_, i) => ({
      // Centro da faixa: o brilho representativo do grupo.
      brilho: (i + 0.5) / FAIXAS_BRILHO_ASTEROIDE,
      itens: [],
    }));
    for (let i = 0; i < ASTEROIDES_DESENHADOS; i += 1) {
      // Distribuição triangular: mais denso no meio da faixa.
      const desvio = (aleatorio() + aleatorio() - 1) * largura;
      const raio = meio + desvio;
      const angulo = aleatorio() * 2 * Math.PI;
      const brilho = aleatorio() ** 1.4;
      const tamanho = aleatorio() < 0.75 ? 1 : 2;
      const faixa = Math.min(
        FAIXAS_BRILHO_ASTEROIDE - 1,
        Math.floor(brilho * FAIXAS_BRILHO_ASTEROIDE),
      );
      grupos[faixa].itens.push({ raio, angulo, tamanho });
    }
    return grupos.filter((grupo) => grupo.itens.length > 0);
  }

  /**
   * Camadas de estrelas normalizadas, agrupadas por cor.
   *
   * As posições ficam em [0, 1) para o campo sobreviver a qualquer
   * redimensionamento. A cor é quantizada pelo mesmo motivo do cinturão: 390
   * estrelas com 390 cores exatas custavam 390 trocas de `fillStyle` por frame
   * para uma variação que ninguém enxerga num ponto de 1 px.
   */
  _criarEstrelas() {
    const aleatorio = criarAleatorio(SEMENTE_ALEATORIA);
    const camadas = [];
    for (let indice = 0; indice < CAMADAS_ESTRELAS; indice += 1) {
      const profundidade = (indice + 1) / CAMADAS_ESTRELAS;
      const porCor = new Map();
      for (let n = 0; n < ESTRELAS_POR_CAMADA; n += 1) {
        const brilho = Math.round(70 + 150 * profundidade * aleatorio());
        const matiz = Math.round(brilho * (0.9 + 0.1 * aleatorio()));
        const azul = Math.min(255, brilho + 18);
        const chave =
          `${quantizarCanal(matiz)},${quantizarCanal(matiz)},${quantizarCanal(azul)}`;
        let grupo = porCor.get(chave);
        if (!grupo) {
          grupo = { cor: `rgb(${chave})`, itens: [] };
          porCor.set(chave, grupo);
        }
        grupo.itens.push({
          x: aleatorio(),
          y: aleatorio(),
          tamanho: profundidade < 0.7 ? 1 : 1 + Math.round(aleatorio()),
        });
      }
      camadas.push([...porCor.values()]);
    }
    return camadas;
  }

  /** Desenha um frame completo da cena (fundo, órbitas e corpos). */
  /**
   * Desenha um frame completo da cena.
   *
   * `luaDestacada` é o NOME da lua em preview no modo lua. Ela ganha anel,
   * disco maior e rótulo sempre visível — sem isso o usuário mostra o número e
   * não tem como saber qual ponto na tela ele acabou de escolher.
   */
  desenhar(camera, posicoes, tempoDias, corpoFocado, luasVisiveis = false, luaDestacada = null) {
    const { ctx } = this;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = COR_FUNDO;
    ctx.fillRect(0, 0, this.largura, this.altura);

    // Estado de texto fixado uma vez por frame: `ctx.font` é a propriedade mais
    // cara do Canvas 2D (reprocessa a string CSS), e antes ela era reatribuída
    // uma vez por rótulo de lua.
    ctx.font = FONTE_ROTULO;
    this._rotulosDesenhados.length = 0;

    this._desenharEstrelas(camera);
    this._desenharCinturao(camera, tempoDias, corpoFocado);
    this._desenharOrbitas(camera, posicoes, corpoFocado, luasVisiveis, luaDestacada);
    for (const corpo of CORPOS) {
      // Satélites seguem a regra das luas menores: somem na visão geral, onde
      // seriam 4 px em cima do planeta — e onde a órbita colidiria com o
      // vizinho. Quando o próprio satélite é o alvo, sempre aparece.
      if (
        corpo.orbitaEmTornoDe &&
        !luasVisiveis &&
        camera.zoom < ZOOM_MINIMO_PARA_LUAS &&
        corpoFocado?.nome !== corpo.nome
      ) {
        continue;
      }
      this._desenharCorpo(camera, corpo, posicoes.get(corpo.nome), tempoDias, corpoFocado);
      if (luasVisiveis) {
        this._desenharLuas(
          camera,
          corpo,
          posicoes.get(corpo.nome),
          tempoDias,
          corpoFocado,
          luaDestacada,
        );
      }
    }
  }

  /**
   * Cinturão de asteroides entre Marte e Júpiter.
   *
   * Pontos com raio e brilho sorteados uma vez (semente fixa) e girados em
   * bloco. Simular a órbita de cada asteroide não mudaria nada na tela e
   * custaria uma volta trigonométrica por partícula por frame.
   */
  _desenharCinturao(camera, tempoDias, corpoFocado) {
    const { ctx } = this;
    const giro = anguloDoCinturao(tempoDias);
    // Durante o foco em um corpo, o cinturão recua junto com as órbitas.
    const alphaMax = corpoFocado ? ALPHA_ASTEROIDE_MIN : ALPHA_ASTEROIDE_MAX;
    const escalaLado = Math.min(2, camera.zoom);
    // A projeção é feita à mão dentro do laço: `mundoParaTela` devolve um objeto
    // novo, e 340 objetos descartados por frame é lixo que o coletor vai cobrar
    // no meio de uma animação.
    const { zoom, centroX, centroY, deslocamentoX, deslocamentoY } = camera;
    const baseX = this.largura / 2 + deslocamentoX;
    const baseY = this.altura / 2 + deslocamentoY;

    for (const grupo of this.asteroides) {
      const alpha = ALPHA_ASTEROIDE_MIN + grupo.brilho * (alphaMax - ALPHA_ASTEROIDE_MIN);
      ctx.fillStyle = `rgba(${COR_ASTEROIDE}, ${alpha.toFixed(3)})`;
      ctx.beginPath();
      let algum = false;
      for (const { raio, angulo, tamanho } of grupo.itens) {
        const a = angulo + giro;
        const x = (raio * Math.cos(a) - centroX) * zoom + baseX;
        if (x < -8 || x > this.largura + 8) continue;
        const y = (raio * Math.sin(a) - centroY) * zoom + baseY;
        if (y < -8 || y > this.altura + 8) continue;
        const lado = Math.max(1, tamanho * escalaLado);
        ctx.rect(x, y, lado, lado);
        algum = true;
      }
      if (algum) ctx.fill();
    }
  }

  /**
   * Luas menores em volta de um planeta: disco esférico, terminador e rótulo.
   *
   * A ÓRBITA não é desenhada aqui — ela vai junto com as demais em
   * `_desenharOrbitas`, para o anel passar por trás do planeta como as órbitas
   * dos planetas passam por trás do Sol.
   *
   * Cada lua sai como um sprite pré-renderizado, não como um círculo de cor
   * chapada: com o disco liso, cinco luas de tons parecidos em volta de Saturno
   * eram cinco pontos iguais, e não havia como dizer qual estava iluminada por
   * qual lado.
   */
  _desenharLuas(camera, corpo, posicao, tempoDias, corpoFocado, luaDestacada = null) {
    const luas = luasDoPlaneta(corpo.nome);
    if (!luas.length) return;

    const { ctx } = this;
    const raioPlaneta = raioCorpoPx(corpo);
    const centro = camera.mundoParaTela(posicao);
    // Descarte barato: com um planeta em foco, os outros oito estão quase
    // sempre fora da tela e as luas deles custariam dois drawImage cada. O 5 é
    // o teto de `raioOrbitaPx` no catálogo (4,1 em Jápeto) com folga.
    const margem = camera.escalar(raioPlaneta * 5) + 80;
    if (
      centro.x < -margem ||
      centro.x > this.largura + margem ||
      centro.y < -margem ||
      centro.y > this.altura + margem
    ) {
      return;
    }

    const esmaecido = Boolean(corpoFocado) && corpoFocado.nome !== corpo.nome;
    const alphaLua = esmaecido ? ALPHA_CORPO_ESMAECIDO : 1;
    // Uma direção de luz por PLANETA, não por lua: a lua mais externa fica a
    // poucos pixels do planeta contra as centenas que os separam do Sol, então
    // o ângulo é o mesmo dentro de bem menos de um grau.
    const anguloLuz = anguloIluminacao(posicao);

    for (const lua of luas) {
      const destacada = lua.nome === luaDestacada;
      const fator = fatorOrbitaLua(lua.raioOrbitaPx, camera.zoom, corpo.temAneis);
      const posicaoLua = posicaoDaLuaMenor(lua, posicao, raioPlaneta, tempoDias, fator);
      const tela = camera.mundoParaTela(posicaoLua);

      // O tamanho agora vem do diâmetro real (comprimido): Titã e Ganimedes
      // saem visivelmente maiores que Fobos, como deve ser.
      let raioDesenho = Math.max(1.4, camera.escalar(raioLuaMenorPx(lua)));
      // A destacada cresce: com 2 px ela some entre as vizinhas, e o ponto do
      // preview é justamente distinguir qual foi escolhida.
      if (destacada) raioDesenho = Math.max(raioDesenho * 1.7, 5);

      const diametro = raioDesenho * 2;
      const sprite = this.spritesLua.get(lua.nome);
      ctx.globalAlpha = destacada ? 1 : alphaLua;
      if (sprite) {
        ctx.drawImage(sprite, tela.x - raioDesenho, tela.y - raioDesenho, diametro, diametro);
        // Terminador: só compensa acima de ~2,5 px de raio. Abaixo disso a
        // sombra ocuparia meio pixel e o único efeito seria escurecer a lua.
        if (raioDesenho >= 2.5) {
          ctx.save();
          ctx.translate(tela.x, tela.y);
          ctx.rotate(anguloLuz);
          ctx.drawImage(this.sombraLua, -raioDesenho, -raioDesenho, diametro, diametro);
          ctx.restore();
        }
      } else {
        // Lua fora do catálogo pré-renderizado: o disco chapado ainda serve.
        ctx.fillStyle = `rgb(${lua.cor})`;
        ctx.beginPath();
        ctx.arc(tela.x, tela.y, raioDesenho, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      if (destacada) {
        // Anel em volta do disco, como a mira de um alvo.
        ctx.strokeStyle = `rgb(${COR_ANEL_DESTAQUE})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(tela.x, tela.y, raioDesenho + 5, 0, Math.PI * 2);
        ctx.stroke();
      }

      // O nome só cabe quando o planeta está realmente próximo — mas o da lua
      // destacada aparece SEMPRE: sem ele o preview não diz qual lua é.
      if (destacada) {
        this._rotulo(lua.nome, tela.x + raioDesenho + 7, tela.y, COR_ROTULO_DESTAQUE, 1);
        this._rotulosDesenhados.push(tela);
      } else if (
        !esmaecido &&
        camera.zoom >= ZOOM_MINIMO_PARA_LUAS * 1.6 &&
        this._cabeRotulo(tela)
      ) {
        this._rotulo(
          lua.nome,
          tela.x + raioDesenho + 5,
          tela.y,
          COR_ROTULO_NORMAL,
          ALPHA_ROTULO_LUA,
        );
        this._rotulosDesenhados.push(tela);
      }
    }
  }

  /**
   * Há espaço para mais um nome neste ponto da tela?
   *
   * Sem esta checagem, um planeta com cinco luas próximas empilhava cinco nomes
   * na mesma faixa de pixels — e o resultado não é "cinco nomes densos", é zero
   * nome legível. Omitir os que colidem deixa pelo menos um lido.
   */
  _cabeRotulo(ponto) {
    for (const anterior of this._rotulosDesenhados) {
      if (
        Math.abs(anterior.x - ponto.x) < DISTANCIA_MINIMA_ROTULO_LUA_PX &&
        Math.abs(anterior.y - ponto.y) < DISTANCIA_MINIMA_ROTULO_LUA_PX
      ) {
        return false;
      }
    }
    return true;
  }

  /**
   * Texto da cena com contorno escuro.
   *
   * O contorno não é enfeite: o mesmo cinza de 11 px que se lê contra o campo
   * de estrelas desaparece sobre o disco bege de Júpiter ou sobre os anéis de
   * Saturno — exatamente onde os rótulos de lua caem.
   */
  _rotulo(texto, x, y, cor, alpha) {
    const { ctx } = this;
    ctx.globalAlpha = alpha;
    ctx.textBaseline = "middle";
    ctx.lineJoin = "round";
    ctx.lineWidth = ESPESSURA_CONTORNO_ROTULO_PX;
    ctx.strokeStyle = `rgba(${COR_CONTORNO_ROTULO}, 0.9)`;
    ctx.strokeText(texto, x, y);
    ctx.fillStyle = cor;
    ctx.fillText(texto, x, y);
    ctx.globalAlpha = 1;
  }

  _desenharEstrelas(camera) {
    const { ctx } = this;
    this.estrelas.forEach((grupos, indice) => {
      const fator = FATOR_PARALLAX[Math.min(indice, FATOR_PARALLAX.length - 1)];
      const deslocX = ((-camera.centroX * fator * camera.zoom) % this.largura + this.largura) % this.largura;
      const deslocY = ((-camera.centroY * fator * camera.zoom) % this.altura + this.altura) % this.altura;
      // Um `fillStyle` e um `fill()` por COR, não por estrela.
      for (const grupo of grupos) {
        ctx.fillStyle = grupo.cor;
        ctx.beginPath();
        for (const estrela of grupo.itens) {
          const px = (estrela.x * this.largura + deslocX) % this.largura;
          const py = (estrela.y * this.altura + deslocY) % this.altura;
          ctx.rect(px, py, estrela.tamanho, estrela.tamanho);
        }
        ctx.fill();
      }
    });
  }

  _desenharOrbitas(
    camera,
    posicoes,
    corpoFocado,
    luasVisiveis = false,
    luaDestacada = null,
  ) {
    const { ctx } = this;
    const centroSol = camera.mundoParaTela({ x: 0, y: 0 });
    ctx.lineWidth = 1;

    if (luasVisiveis) this._desenharOrbitasDeLuas(camera, posicoes, corpoFocado, luaDestacada);

    for (const corpo of CORPOS) {
      if (ehSol(corpo)) continue;

      let centro = centroSol;
      let raioMundo = 0;

      if (corpo.orbitaEmTornoDe) {
        // Satélite (ex.: Lua ao redor da Terra). Só com a câmera aproximada:
        // na visão geral a órbita da Lua (raio 28) invadiria Vênus, que fica a
        // 24,2 px da Terra — e não há raio que resolva, já que a folga entre os
        // discos é de ~4 px, menor que o raio desenhado da própria Terra.
        if (!luasVisiveis && camera.zoom < ZOOM_MINIMO_PARA_LUAS) continue;
        const posPai = posicoes.get(corpo.orbitaEmTornoDe);
        if (!posPai) continue;
        centro = camera.mundoParaTela(posPai);
        const pai = CORPOS.find((c) => c.nome === corpo.orbitaEmTornoDe);
        const raioPai = pai ? raioCorpoPx(pai) : 1;
        raioMundo =
          raioPai * fatorOrbitaLua(RAIO_ORBITA_LUA_PX / raioPai, camera.zoom, pai?.temAneis);
      } else {
        raioMundo = raioOrbitalPx(corpo.distanciaUa);
      }

      const raio = camera.escalar(raioMundo);
      if (raio < 2) continue;

      let cor = COR_ORBITA;
      let alpha = ALPHA_ORBITA_NORMAL;
      if (corpoFocado && (corpoFocado.nome === corpo.nome || corpoFocado.nome === corpo.orbitaEmTornoDe)) {
        cor = COR_ORBITA_FOCADA;
        alpha = ALPHA_ORBITA_FOCADA;
      } else if (corpoFocado) {
        alpha = ALPHA_ORBITA_TENUE;
      }

      ctx.strokeStyle = `rgba(${cor}, ${alpha})`;
      ctx.beginPath();
      ctx.arc(centro.x, centro.y, raio, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  /**
   * Anéis orbitais das luas menores, junto com as demais órbitas.
   *
   * Ficam ANTES dos planetas de propósito: assim o anel passa por trás do disco
   * do planeta, do mesmo jeito que a órbita de Mercúrio passa por trás do Sol.
   * Antes eram desenhados depois, e o traço cruzava o planeta por cima — o que
   * lia como um anel de Saturno extra em volta de Júpiter.
   */
  _desenharOrbitasDeLuas(camera, posicoes, corpoFocado, luaDestacada) {
    const { ctx } = this;
    for (const corpo of CORPOS) {
      const luas = luasDoPlaneta(corpo.nome);
      if (!luas.length) continue;
      const posicao = posicoes.get(corpo.nome);
      if (!posicao) continue;

      const raioPlaneta = raioCorpoPx(corpo);
      const centro = camera.mundoParaTela(posicao);
      const margem = camera.escalar(raioPlaneta * 5) + 80;
      if (
        centro.x < -margem ||
        centro.x > this.largura + margem ||
        centro.y < -margem ||
        centro.y > this.altura + margem
      ) {
        continue;
      }
      const esmaecido = Boolean(corpoFocado) && corpoFocado.nome !== corpo.nome;

      for (const lua of luas) {
        // Comprimido na visão geral, aberto conforme a câmera aproxima.
        const fator = fatorOrbitaLua(lua.raioOrbitaPx, camera.zoom, corpo.temAneis);
        const raioOrbita = camera.escalar(raioPlaneta * fator);
        if (raioOrbita <= 3) continue;
        if (lua.nome === luaDestacada) {
          // A órbita da lua escolhida acende na cor DELA: é o que liga o número
          // mostrado com a mão ao ponto na tela.
          ctx.strokeStyle = `rgba(${lua.cor}, 0.75)`;
          ctx.lineWidth = 2;
        } else {
          ctx.strokeStyle = `rgba(${COR_ORBITA_LUA}, ${esmaecido ? 0.08 : ALPHA_ORBITA_LUA})`;
          ctx.lineWidth = 1;
        }
        ctx.beginPath();
        ctx.arc(centro.x, centro.y, raioOrbita, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
    ctx.lineWidth = 1;
  }

  _desenharCorpo(camera, corpo, posicao, tempoDias, corpoFocado) {
    const { ctx } = this;
    const centro = camera.mundoParaTela(posicao);
    const raioTela = camera.escalar(raioCorpoPx(corpo));
    const focado = Boolean(corpoFocado) && corpoFocado.nome === corpo.nome;

    // Descarte barato: fora da tela e sem foco, nem desenha.
    const margem = raioTela * FATOR_ANEL_EXTERNO + 60;
    if (
      !focado &&
      (centro.x < -margem ||
        centro.x > this.largura + margem ||
        centro.y < -margem ||
        centro.y > this.altura + margem)
    ) {
      return;
    }

    const alpha = !corpoFocado || focado ? 1 : ALPHA_CORPO_ESMAECIDO;
    const diametro = Math.max(2, raioTela * 2);

    if (ehSol(corpo) && alpha >= 1) this._desenharHalo(centro, raioTela);

    const anel = this.aneis.get(corpo.nome);
    if (anel) this._desenharAnel(centro, raioTela, anel, alpha, false);
    if (corpo.nome === "Urano") this._desenharEixoUrano(centro, raioTela, alpha);

    // Disco com a fase de rotação corrente.
    const quadros = this.quadros.get(corpo.nome);
    const indice =
      Math.floor(faseRotacao(corpo, tempoDias) * QUADROS_ROTACAO) % QUADROS_ROTACAO;
    ctx.globalAlpha = alpha;
    ctx.drawImage(
      quadros[indice],
      centro.x - diametro / 2,
      centro.y - diametro / 2,
      diametro,
      diametro,
    );

    // Terminador: o lado oposto ao Sol fica na sombra (o Sol não tem noite).
    if (!ehSol(corpo)) {
      ctx.save();
      ctx.translate(centro.x, centro.y);
      ctx.rotate(anguloIluminacao(posicao));
      ctx.drawImage(this.sombra, -diametro / 2, -diametro / 2, diametro, diametro);
      ctx.restore();
    }
    ctx.globalAlpha = 1;

    if (anel) this._desenharAnel(centro, raioTela, anel, alpha, true);
    if (focado) this._desenharDestaque(centro, raioTela);
  }

  /** Coroa solar: gradiente radial somado ao fundo. */
  _desenharHalo(centro, raioTela) {
    const { ctx } = this;
    const raio = raioTela * FATOR_HALO_SOL;
    const gradiente = ctx.createRadialGradient(
      centro.x,
      centro.y,
      raioTela * 0.6,
      centro.x,
      centro.y,
      raio,
    );
    gradiente.addColorStop(0, "rgba(255, 176, 60, 0.42)");
    gradiente.addColorStop(0.45, "rgba(255, 150, 40, 0.12)");
    gradiente.addColorStop(1, "rgba(255, 140, 30, 0)");
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.fillStyle = gradiente;
    ctx.beginPath();
    ctx.arc(centro.x, centro.y, raio, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  /** Desenha metade do anel: atrás do planeta ou na frente dele. */
  _desenharAnel(centro, raioTela, anel, alpha, frente) {
    const { ctx } = this;
    const escala = (raioTela * 2) / TAM_TEX;
    const largura = anel.imagem.width * escala;
    const altura = anel.imagem.height * escala;
    const x = centro.x - largura / 2;
    const y = centro.y - altura / 2;

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.beginPath();
    if (anel.eixo === "horizontal") {
      // Metade de baixo passa na frente do planeta (está mais perto).
      if (frente) ctx.rect(x, centro.y, largura, altura / 2);
      else ctx.rect(x, y, largura, altura / 2);
    } else if (frente) {
      ctx.rect(centro.x, y, largura / 2, altura);
    } else {
      ctx.rect(x, y, largura / 2, altura);
    }
    ctx.clip();
    ctx.drawImage(anel.imagem, x, y, largura, altura);
    ctx.restore();
  }

  /** Linha do eixo de rotação — Urano gira deitado (97,77°). */
  _desenharEixoUrano(centro, raioTela, alpha) {
    const { ctx } = this;
    const comprimento = raioTela * COMPRIMENTO_EIXO_URANO;
    const angulo = ((INCLINACAO_ANEL_URANO_GRAUS + 90) * Math.PI) / 180;
    const dx = Math.cos(angulo) * comprimento;
    const dy = -Math.sin(angulo) * comprimento;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = `rgb(${COR_ANEL_URANO})`;
    ctx.lineWidth = Math.max(1, raioTela * 0.06);
    ctx.beginPath();
    ctx.moveTo(centro.x - dx, centro.y - dy);
    ctx.lineTo(centro.x + dx, centro.y + dy);
    ctx.stroke();
    ctx.restore();
  }

  /** Anel de destaque em volta do corpo focado. */
  _desenharDestaque(centro, raioTela) {
    const { ctx } = this;
    ctx.save();
    ctx.strokeStyle = `rgba(${COR_ANEL_DESTAQUE}, 0.67)`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(centro.x, centro.y, raioTela + FOLGA_ANEL_DESTAQUE_PX, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  /** Corpo cujo disco contém o ponto de tela (usado no toque/clique). */
  corpoNoPonto(camera, posicoes, ponto) {
    let escolhido = null;
    let menorDistancia = Infinity;
    for (const corpo of CORPOS) {
      const centro = camera.mundoParaTela(posicoes.get(corpo.nome));
      const raio = Math.max(22, camera.escalar(raioCorpoPx(corpo)));
      const distancia = Math.hypot(centro.x - ponto.x, centro.y - ponto.y);
      if (distancia <= raio && distancia < menorDistancia) {
        menorDistancia = distancia;
        escolhido = corpo;
      }
    }
    return escolhido;
  }
}
