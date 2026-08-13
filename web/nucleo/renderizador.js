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
  ACHATAMENTO_ANEL_URANO,
  ALPHA_CORPO_ESMAECIDO,
  ALPHA_ORBITA_FOCADA,
  ALPHA_ORBITA_NORMAL,
  ALPHA_ORBITA_TENUE,
  ALPHA_SOMBRA_MAX,
  CAMADAS_ESTRELAS,
  COMPRIMENTO_EIXO_URANO,
  COR_ANEL_DESTAQUE,
  COR_ANEL_SATURNO,
  COR_ANEL_URANO,
  COR_FUNDO,
  COR_ORBITA,
  COR_ORBITA_FOCADA,
  ESCALA_RUIDO_TEXTURA,
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
  RAIO_TEXTURA_PX,
  SEMENTE_ALEATORIA,
} from "../config.js";
import { CORPOS, ehSol } from "../dados/planetas.js";
import {
  anguloIluminacao,
  faseRotacao,
  raioCorpoPx,
  raioOrbitalPx,
} from "./orbita.js";

const RAIO_TEX = RAIO_TEXTURA_PX;
const TAM_TEX = RAIO_TEX * 2;
const LARGURA_TIRA = RAIO_TEX * LARGURA_TIRA_EM_RAIOS;
const ALTURA_TIRA = TAM_TEX;

/** Corpos que ganham calotas polares brancas na textura. */
const CORPOS_COM_CALOTAS = new Set(["Terra", "Marte"]);

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

/** Ruído fractal em [0, 1], contínuo na emenda horizontal da tira. */
function ruidoSuave(aleatorio, altura, largura, oitavas = 3) {
  const total = new Float64Array(altura * largura);
  let amplitude = 1;
  let somaAmplitudes = 0;
  for (let oitava = 0; oitava < oitavas; oitava += 1) {
    const blocos = Math.max(2, ESCALA_RUIDO_TEXTURA * 2 ** oitava);
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
    this.estrelas = this._criarEstrelas();
  }

  redimensionar(largura, altura) {
    this.largura = largura;
    this.altura = altura;
  }

  /** Camadas de estrelas normalizadas: sobrevivem a qualquer redimensionamento. */
  _criarEstrelas() {
    const aleatorio = criarAleatorio(SEMENTE_ALEATORIA);
    const camadas = [];
    for (let indice = 0; indice < CAMADAS_ESTRELAS; indice += 1) {
      const profundidade = (indice + 1) / CAMADAS_ESTRELAS;
      const estrelas = [];
      for (let n = 0; n < ESTRELAS_POR_CAMADA; n += 1) {
        const brilho = Math.round(70 + 150 * profundidade * aleatorio());
        const matiz = Math.round(brilho * (0.9 + 0.1 * aleatorio()));
        estrelas.push({
          x: aleatorio(),
          y: aleatorio(),
          tamanho: profundidade < 0.7 ? 1 : 1 + Math.round(aleatorio()),
          cor: `rgb(${matiz}, ${matiz}, ${Math.min(255, brilho + 18)})`,
        });
      }
      camadas.push(estrelas);
    }
    return camadas;
  }

  /** Desenha um frame completo da cena (fundo, órbitas e corpos). */
  desenhar(camera, posicoes, tempoDias, corpoFocado) {
    const { ctx } = this;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = COR_FUNDO;
    ctx.fillRect(0, 0, this.largura, this.altura);

    this._desenharEstrelas(camera);
    this._desenharOrbitas(camera, posicoes, corpoFocado);
    for (const corpo of CORPOS) {
      this._desenharCorpo(camera, corpo, posicoes.get(corpo.nome), tempoDias, corpoFocado);
    }
  }

  _desenharEstrelas(camera) {
    const { ctx } = this;
    this.estrelas.forEach((estrelas, indice) => {
      const fator = FATOR_PARALLAX[Math.min(indice, FATOR_PARALLAX.length - 1)];
      const deslocX = ((-camera.centroX * fator * camera.zoom) % this.largura + this.largura) % this.largura;
      const deslocY = ((-camera.centroY * fator * camera.zoom) % this.altura + this.altura) % this.altura;
      for (const estrela of estrelas) {
        ctx.fillStyle = estrela.cor;
        const px = (estrela.x * this.largura + deslocX) % this.largura;
        const py = (estrela.y * this.altura + deslocY) % this.altura;
        ctx.fillRect(px, py, estrela.tamanho, estrela.tamanho);
      }
    });
  }

  _desenharOrbitas(camera, posicoes, corpoFocado) {
    const { ctx } = this;
    const centroSol = camera.mundoParaTela({ x: 0, y: 0 });
    ctx.lineWidth = 1;

    for (const corpo of CORPOS) {
      if (ehSol(corpo)) continue;

      let centro = centroSol;
      let raioMundo = 0;

      if (corpo.orbitaEmTornoDe) {
        // Satélite (ex: Lua ao redor da Terra)
        const posPai = posicoes.get(corpo.orbitaEmTornoDe);
        if (!posPai) continue;
        centro = camera.mundoParaTela(posPai);
        raioMundo = 28; // RAIO_ORBITA_LUA_PX
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
