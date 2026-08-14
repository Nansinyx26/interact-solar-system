/**
 * Narração por voz do corpo focado, usando a Web Speech API do navegador.
 *
 * Equivalente web do ui/narrador.py — mesma frase, mesmo idioma, mesma regra de
 * substituir a fala anterior em vez de enfileirar. Aqui não há thread: a API já
 * é assíncrona, mas ela tem duas armadilhas próprias tratadas abaixo.
 */

import {
  ELEVENLABS_VOZ_NOME,
  ENDPOINT_VOZ,
  IDIOMA_NARRACAO,
  NARRACAO_ATIVA_PADRAO,
  NARRAR_FICHA_COMPLETA,
  URL_SERVIDOR_RENDER,
  VELOCIDADE_NARRACAO,
  VOLUME_NARRACAO,
} from "../config.js";
import { nomeDoTipo } from "./ficha.js";

const CHAVE_PREFERENCIA = "sistema-solar:narracao";
/** O pyttsx3 mede em palavras por minuto; a Web Speech usa 1 = natural. */
const PPM_NATURAL = 165;

// Artigo definido antes do nome. Em português corrente dizemos "o Sol" e "a
// Terra", mas "Marte" e "Júpiter" dispensam artigo.
const ARTIGO_DEFINIDO = { Sol: "O", Terra: "A", Lua: "A" };

// Descrição do tipo já com artigo indefinido, para a frase fechar concordância.
const TIPO_NARRADO = {
  estrela: "uma estrela",
  rochoso: "um planeta rochoso",
  gasoso: "um gigante gasoso",
  satelite: "um satélite natural",
};

/** Número no padrão pt-BR, que é como o sintetizador lê corretamente. */
function numero(valor, casas = 0) {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }).format(valor);
}

/**
 * A ficha do corpo em orações completas, prontas para serem lidas.
 *
 * É a mesma informação do card, dita em português corrente: "Tem 12.756
 * quilômetros de diâmetro" em vez de "Diâmetro equatorial: 12.756 km". Rótulo e
 * valor soltos soariam como uma planilha sendo lida em voz alta.
 */
/**
 * Número para ser dito em voz alta, sem casas decimais inúteis.
 *
 * "243,0 dias" era lido como "duzentos e quarenta e três vírgula zero"; o zero
 * à direita não informa nada e atrapalha a fala.
 */
function quantidade(valor, casas = 1) {
  if (Math.abs(valor - Math.round(valor)) < 10 ** -casas / 2) {
    return numero(Math.round(valor));
  }
  return numero(valor, casas);
}

/** Escolhe singular ou plural conforme o número dito. */
function concordar(valor, singular, plural) {
  return Math.abs(valor - 1) < 1e-9 ? singular : plural;
}

/**
 * Distância em escala legível.
 *
 * Ninguém diz "149.600.000 quilômetros" em voz alta, e o sintetizador se perde
 * no meio dos nove dígitos — na transcrição saía "149.600 mil". Acima de um
 * milhão a frase passa a usar milhões e bilhões.
 */
function distanciaFalada(km) {
  if (km >= 1_000_000_000) {
    const bilhoes = km / 1_000_000_000;
    return `${quantidade(bilhoes, 2)} ${concordar(bilhoes, "bilhão", "bilhões")} de quilômetros`;
  }
  if (km >= 1_000_000) {
    const milhoes = km / 1_000_000;
    return `${quantidade(milhoes, 1)} ${concordar(milhoes, "milhão", "milhões")} de quilômetros`;
  }
  return `${numero(km)} quilômetros`;
}

/**
 * Temperatura com o sinal dito por extenso.
 * O "−" antes do número desaparecia na fala: −65 virava "65 graus".
 */
function temperaturaFalada(graus) {
  return graus < 0
    ? `${numero(Math.abs(graus))} graus Celsius negativos`
    : `${numero(graus)} graus Celsius`;
}

/** Frase das luas, com o gênero certo — "2 luas" saía como "dois luas". */
function luasFaladas(luas) {
  if (luas <= 0) return null;
  if (luas === 1) return "Tem uma lua conhecida.";
  if (luas === 2) return "Tem duas luas conhecidas.";
  return `Tem ${numero(luas)} luas conhecidas.`;
}

export function frasesDaFicha(corpo) {
  const frases = [`Tem ${numero(corpo.diametroKm)} quilômetros de diâmetro.`];

  if (corpo.orbitaEmTornoDe) {
    const preposicao = corpo.orbitaEmTornoDe === "Terra" ? "da" : "de";
    frases.push(
      `Fica a ${distanciaFalada(corpo.distanciaKm)} ${preposicao} ${corpo.orbitaEmTornoDe}.`,
    );
  } else if (corpo.distanciaUa > 0) {
    const ua = corpo.distanciaUa;
    frases.push(
      `Fica a ${quantidade(ua, 2)} ` +
        `${concordar(ua, "unidade astronômica", "unidades astronômicas")} do Sol, ` +
        `ou seja, ${distanciaFalada(corpo.distanciaKm)}.`,
    );
  }

  if (corpo.periodoOrbitalDias > 0) {
    if (corpo.periodoOrbitalDias >= 365.26) {
      const anos = corpo.periodoOrbitalDias / 365.26;
      frases.push(
        `Uma volta completa leva ${quantidade(anos, 1)} ` +
          `${concordar(anos, "ano terrestre", "anos terrestres")}.`,
      );
    } else {
      const dias = corpo.periodoOrbitalDias;
      frases.push(
        `Uma volta completa leva ${quantidade(dias, 0)} ${concordar(dias, "dia", "dias")}.`,
      );
    }
  }

  const horas = Math.abs(corpo.periodoRotacaoHoras);
  const sentido =
    corpo.periodoRotacaoHoras < 0 ? " no sentido contrário ao dos demais" : "";
  if (horas >= 48) {
    const diasRotacao = horas / 24;
    frases.push(
      `Gira em torno de si mesmo em ${quantidade(diasRotacao, 1)} ` +
        `${concordar(diasRotacao, "dia", "dias")}${sentido}.`,
    );
  } else {
    frases.push(
      `Gira em torno de si mesmo em ${quantidade(horas, 1)} ` +
        `${concordar(horas, "hora", "horas")}${sentido}.`,
    );
  }

  const luas = luasFaladas(corpo.luas);
  if (luas) frases.push(luas);

  frases.push(`A temperatura média é de ${temperaturaFalada(corpo.temperaturaMediaC)}.`);
  frases.push(corpo.fatoCurioso);
  return frases;
}

/**
 * Texto narrado ao focar um corpo.
 *
 * A abertura é uma **oração completa** ("A Terra é um planeta rochoso.") e não
 * uma lista de termos ("Terra. Planeta rochoso"). O motivo é prático: o modelo
 * de voz identifica o idioma pelo texto, e nomes latinos soltos são ambíguos —
 * medindo com a transcrição da própria ElevenLabs, "Sol. Estrela" saía em
 * espanhol e "Marte. Planeta rochoso" em inglês. O verbo "é" acentuado e os
 * artigos são o que ancora a frase no português.
 */
export function textoDoCorpo(corpo) {
  const artigo = ARTIGO_DEFINIDO[corpo.nome];
  const sujeito = artigo ? `${artigo} ${corpo.nome}` : corpo.nome;
  const descricao = TIPO_NARRADO[corpo.tipo] ?? "um corpo celeste";
  const partes = [`${sujeito} é ${descricao}.`];
  if (NARRAR_FICHA_COMPLETA) partes.push(...frasesDaFicha(corpo));
  return partes.join(" ");
}

export class Narrador {
  constructor() {
    this.disponivel = typeof window !== "undefined" && "speechSynthesis" in window;
    // A voz neural é tentada até dar errado uma vez; a do navegador é o piso.
    this._neuralDisponivel = typeof fetch === "function";
    this.ativo = (this.disponivel || this._neuralDisponivel) && this._preferenciaSalva();
    this._voz = null;
    this._audio = null;
    // Contador de pedidos: descarta o áudio que chega depois de o usuário já
    // ter escolhido outro planeta.
    this._pedidoAtual = 0;
    if (this.disponivel) this._carregarVozes();
  }

  /** Nome do backend em uso, para o HUD mostrar. */
  get backend() {
    return this._neuralDisponivel ? ELEVENLABS_VOZ_NOME : "voz do navegador";
  }

  /**
   * A lista de vozes costuma vir vazia na primeira chamada: o navegador a
   * carrega de forma assíncrona e avisa por `voiceschanged`.
   */
  _carregarVozes() {
    const escolher = () => {
      const vozes = window.speechSynthesis.getVoices();
      if (!vozes.length) return;
      const alvo = IDIOMA_NARRACAO.toLowerCase();
      const curto = alvo.split("-")[0];
      this._voz =
        vozes.find((v) => v.lang?.toLowerCase() === alvo) ??
        vozes.find((v) => v.lang?.toLowerCase().startsWith(curto)) ??
        null;
    };
    escolher();
    window.speechSynthesis.addEventListener("voiceschanged", escolher);
  }

  _preferenciaSalva() {
    try {
      const salvo = localStorage.getItem(CHAVE_PREFERENCIA);
      return salvo === null ? NARRACAO_ATIVA_PADRAO : salvo === "1";
    } catch {
      // localStorage bloqueado (modo privado, cookies desativados).
      return NARRACAO_ATIVA_PADRAO;
    }
  }

  _salvarPreferencia() {
    try {
      localStorage.setItem(CHAVE_PREFERENCIA, this.ativo ? "1" : "0");
    } catch {
      // Sem persistência a preferência vale só para esta sessão.
    }
  }

  /** Liga/desliga a narração e devolve o novo estado. */
  alternar() {
    if (!this.disponivel && !this._neuralDisponivel) return false;
    this.ativo = !this.ativo;
    if (!this.ativo) this._calar();
    this._salvarPreferencia();
    return this.ativo;
  }

  /**
   * Fala uma frase, cortando a anterior.
   *
   * Tenta primeiro a voz neural (ElevenLabs, via /api/voz) e cai para a voz do
   * navegador se a função não existir, não estiver configurada ou falhar.
   */
  anunciar(texto) {
    if (!this.ativo || !texto) return;
    this._calar();
    if (this._neuralDisponivel) {
      this._falarNeural(texto);
      return;
    }
    this._falarLocal(texto);
  }

  /**
   * Toca o áudio vindo de /api/voz.
   *
   * A rota devolve 503 quando o servidor não tem chave configurada — é o sinal
   * combinado para desistir da voz neural pelo resto da sessão e não repetir
   * uma ida à rede a cada troca de planeta.
   */
  async _falarNeural(texto) {
    const pedido = ++this._pedidoAtual;
    try {
      let resposta = await fetch(`${ENDPOINT_VOZ}?texto=${encodeURIComponent(texto)}`);
      if (!resposta.ok && URL_SERVIDOR_RENDER) {
        try {
          const respRender = await fetch(`${URL_SERVIDOR_RENDER}/api/voz?texto=${encodeURIComponent(texto)}`);
          if (respRender.ok) resposta = respRender;
        } catch {
          // ignora falha de rede do render
        }
      }
      if (!resposta.ok) {
        if (resposta.status === 503 || resposta.status === 404) {
          this._neuralDisponivel = false;
        }
        throw new Error(`HTTP ${resposta.status}`);
      }
      const blob = await resposta.blob();
      // Outro planeta foi escolhido enquanto o áudio baixava: este já não vale.
      if (pedido !== this._pedidoAtual || !this.ativo) return;
      const audio = new Audio(URL.createObjectURL(blob));
      audio.volume = VOLUME_NARRACAO;
      audio.addEventListener("ended", () => URL.revokeObjectURL(audio.src));
      this._audio = audio;
      await audio.play();
    } catch {
      if (pedido === this._pedidoAtual && this.ativo) this._falarLocal(texto);
    }
  }

  /** Voz do próprio navegador (Web Speech API). */
  _falarLocal(texto) {
    if (!this.disponivel) return;
    const fala = new SpeechSynthesisUtterance(texto);
    fala.lang = IDIOMA_NARRACAO;
    fala.rate = VELOCIDADE_NARRACAO / PPM_NATURAL;
    fala.volume = VOLUME_NARRACAO;
    if (this._voz) fala.voice = this._voz;
    window.speechSynthesis.speak(fala);
  }

  /** Interrompe qualquer fala em andamento, dos dois backends. */
  _calar() {
    this._pedidoAtual += 1;
    // Sem o cancel as falas empilham: trocando de planeta rápido o usuário
    // ouviria uma fila inteira de nomes antigos.
    if (this.disponivel) window.speechSynthesis.cancel();
    if (this._audio) {
      this._audio.pause();
      this._audio = null;
    }
  }

  /** Silencia imediatamente (usado ao sair da página). */
  parar() {
    this._calar();
  }
}
