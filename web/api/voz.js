/**
 * Proxy de síntese de voz (ElevenLabs) — função serverless do Vercel.
 *
 * Existe por um motivo de segurança: a chave da API **não pode** chegar ao
 * navegador. O front é público e qualquer visitante leria o valor no código,
 * podendo gastar a cota da conta. Aqui a chave fica em `ELEVENLABS_API_KEY`,
 * variável de ambiente do projeto no Vercel, e nunca sai do servidor.
 *
 * Uso: GET /api/voz?texto=Saturno.%20Gigante%20gasoso  ->  audio/mpeg
 *
 * Sem a variável configurada, responde 503 e o narrador do site cai sozinho
 * para a voz do próprio navegador (Web Speech API).
 */

const VOZ_ID = "nPczCjzI2devNBz1zQrb"; // Brian
const MODELO = "eleven_multilingual_v2"; // fala português
const FORMATO = "mp3_44100_128";
const IDIOMA = "pt";
/**
 * Trava contra uso da rota como serviço de TTS genérico por terceiros.
 * A ficha completa de um corpo dá ~450 caracteres; 700 deixa folga sem abrir a
 * rota para textos arbitrários.
 */
const TAMANHO_MAXIMO_TEXTO = 700;

export default async function handler(pedido, resposta) {
  if (pedido.method !== "GET") {
    return resposta.status(405).json({ erro: "Use GET." });
  }

  const texto = String(pedido.query?.texto ?? "").trim();
  if (!texto) {
    return resposta.status(400).json({ erro: "Faltou o parâmetro 'texto'." });
  }
  if (texto.length > TAMANHO_MAXIMO_TEXTO) {
    return resposta.status(413).json({ erro: "Texto longo demais." });
  }

  const chave = process.env.ELEVENLABS_API_KEY;
  if (!chave) {
    // 503 é o sinal combinado com o front: ele usa a voz do navegador.
    return resposta
      .status(503)
      .json({ erro: "ELEVENLABS_API_KEY não configurada no servidor." });
  }

  try {
    const alvo =
      `https://api.elevenlabs.io/v1/text-to-speech/${VOZ_ID}` +
      `?output_format=${FORMATO}`;
    const upstream = await fetch(alvo, {
      method: "POST",
      headers: {
        "xi-api-key": chave,
        "Content-Type": "application/json",
        Accept: "audio/mpeg",
      },
      body: JSON.stringify({
        text: texto,
        model_id: MODELO,
        language_code: IDIOMA,
        voice_settings: { stability: 0.5, similarity_boost: 0.75 },
      }),
    });

    if (!upstream.ok) {
      const detalhe = (await upstream.text()).slice(0, 200);
      // Não repassamos o corpo do erro da ElevenLabs adiante sem filtrar: ele
      // pode citar dados da conta.
      console.error("ElevenLabs respondeu", upstream.status, detalhe);
      return resposta
        .status(502)
        .json({ erro: `Síntese indisponível (HTTP ${upstream.status}).` });
    }

    const audio = Buffer.from(await upstream.arrayBuffer());
    resposta.setHeader("Content-Type", "audio/mpeg");
    resposta.setHeader("Content-Length", String(audio.length));
    // As frases são fixas (dez corpos celestes): o cache da CDN evita pagar
    // créditos de novo a cada visitante.
    resposta.setHeader(
      "Cache-Control",
      "public, max-age=86400, s-maxage=2592000, immutable",
    );
    return resposta.status(200).send(audio);
  } catch (erro) {
    console.error("Falha ao sintetizar:", erro);
    return resposta.status(502).json({ erro: "Falha ao sintetizar a voz." });
  }
}
