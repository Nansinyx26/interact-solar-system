/**
 * Servidor Backend do Sistema Solar Interativo (para Deploy no Render.com).
 *
 * Oferece endpoints REST de telemetria (MongoDB Atlas) e síntese de voz (ElevenLabs)
 * com suporte a CORS para se comunicar nativamente com a versão Web no Vercel.
 */

import express from "express";
import cors from "cors";
import { MongoClient } from "mongodb";
import { normalizarTurma, montarFiltroTurma, obterListaTurmas } from "./api/ranking.js";

if (typeof process.loadEnvFile === "function") {
  try {
    process.loadEnvFile();
  } catch {
    // .env opcional
  }
}

const app = express();
const PORT = process.env.PORT || 3000;

// Permite chamadas CORS do Vercel e outros domínios autorizados
app.use(
  cors({
    origin: "*",
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);

app.use(express.json());
app.use(express.static("web"));

// URI do MongoDB Atlas obtida estritamente das variáveis de ambiente (.env / Render env)
const MONGODB_URI = process.env.MONGODB_URI ?? "";

let clientCached = null;

async function obterClienteMongo() {
  if (clientCached) return clientCached;
  try {
    const client = new MongoClient(MONGODB_URI, {
      serverSelectionTimeoutMS: 5000,
    });
    await client.connect();
    clientCached = client;
    return client;
  } catch (erro) {
    console.error("[Render Server] Erro ao conectar ao MongoDB:", erro);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Healthcheck & Status da API
// ---------------------------------------------------------------------------
app.get("/api/status", (req, res) => {
  res.json({
    status: "online",
    servidor: "Render",
    app: "Sistema Solar Interativo",
    versao: "1.2.0",
    endpoints: ["/api/telemetria", "/api/voz", "/api/ranking"],
    timestamp: new Date().toISOString(),
  });
});

app.get("/health", (req, res) => {
  res.json({ status: "ok", uptime: process.uptime() });
});

// ---------------------------------------------------------------------------
// Endpoint de Ranking / Resultados (/api/ranking)
// ---------------------------------------------------------------------------
app.get("/api/ranking", async (req, res) => {
  try {
    const client = await obterClienteMongo();
    if (!client) {
      return res.status(503).json({ erro: "Banco de dados indisponível." });
    }

    const db = client.db("sistema_solar");
    const colecao = db.collection("ranking");
    const turmaFiltro = String(req.query.turma ?? "").trim();
    const serieFiltro = String(req.query.serie ?? "").trim();
    const salaFiltro = String(req.query.sala ?? "").trim();
    const limite = Math.min(Math.max(parseInt(req.query.limit ?? "100", 10), 1), 200);

    const filtro = montarFiltroTurma(turmaFiltro, serieFiltro, salaFiltro);

    const [resultados, turmasCadastradas] = await Promise.all([
      colecao
        .find(filtro)
        .sort({ pontuacao: -1, tempoSegundos: 1, timestamp: -1 })
        .limit(limite)
        .toArray(),
      obterListaTurmas(colecao)
    ]);

    const formatados = resultados.map((item, index) => {
      const turmaCalculada = normalizarTurma(item.serie, item.sala, item.turma);
      const acertos = Math.max(0, parseInt(item.acertos ?? 0, 10));
      const totalQuestoes = 10;
      const erros = Math.max(0, totalQuestoes - acertos);

      return {
        posicao: index + 1,
        id: item._id.toString(),
        nome: item.nome ?? "Anônimo",
        turma: turmaCalculada,
        serie: item.serie ?? "Geral",
        sala: item.sala ?? "—",
        quiz: item.quiz ?? "Quiz do Sistema Solar",
        pontuacao: item.pontuacao ?? 0,
        acertos,
        totalQuestoes,
        erros,
        tempoSegundos: item.tempoSegundos ?? 0,
        data_hora: item.data_hora ?? new Date().toISOString(),
        timestamp: item.timestamp ?? (item.data_hora ? new Date(item.data_hora).getTime() / 1000 : 0),
      };
    });

    return res.status(200).json({
      ok: true,
      ranking: formatados,
      turmas: turmasCadastradas,
      total: formatados.length,
      turmaSelecionada: turmaFiltro || serieFiltro || "Todas",
    });
  } catch (erro) {
    console.error("[Render Server] Erro ao buscar ranking:", erro);
    return res.status(500).json({ erro: "Falha ao obter ranking." });
  }
});

app.post("/api/ranking", async (req, res) => {
  try {
    const client = await obterClienteMongo();
    if (!client) {
      return res.status(503).json({ erro: "Banco de dados indisponível." });
    }

    const db = client.db("sistema_solar");
    const colecao = db.collection("ranking");
    const dados = req.body ?? {};
    const nome = String(dados.nome ?? "").trim().slice(0, 50);
    const serie = String(dados.serie ?? "Geral").trim().slice(0, 30);
    const sala = String(dados.sala ?? "").trim().slice(0, 20);
    const quiz = String(dados.quiz ?? "Quiz do Sistema Solar").trim().slice(0, 60);
    const pontuacao = Math.max(0, parseInt(dados.pontuacao ?? 0, 10));
    const acertos = Math.max(0, parseInt(dados.acertos ?? 0, 10));
    const tempoSegundos = Math.max(0, parseFloat(dados.tempoSegundos ?? 0));

    if (!nome) {
      return res.status(400).json({ erro: "Informe o nome do aluno." });
    }

    const turmaInformada = dados.turma ? String(dados.turma).trim() : null;
    const turmaCalculada = turmaInformada
      ? normalizarTurma(null, null, turmaInformada)
      : normalizarTurma(serie, sala);

    const doc = {
      nome,
      serie: serie || "Geral",
      sala: sala || "Única",
      turma: turmaCalculada,
      quiz: quiz || "Quiz do Sistema Solar",
      pontuacao,
      acertos,
      totalQuestoes: 10,
      tempoSegundos,
      data_hora: new Date(),
      timestamp: Date.now() / 1000,
    };

    const resultado = await colecao.insertOne(doc);
    return res.status(201).json({
      ok: true,
      mensagem: "Resultado salvo no ranking com sucesso!",
      id: resultado.insertedId.toString(),
      turma: turmaCalculada,
    });
  } catch (erro) {
    console.error("[Render Server] Erro ao salvar ranking:", erro);
    return res.status(500).json({ erro: "Falha ao registrar resultado." });
  }
});

const CODIGO_AUTORIZACAO = "4400";

app.delete("/api/ranking", async (req, res) => {
  try {
    const client = await obterClienteMongo();
    if (!client) {
      return res.status(503).json({ erro: "Banco de dados indisponível." });
    }

    const db = client.db("sistema_solar");
    const colecao = db.collection("ranking");
    const dados = req.body ?? {};
    const codigoFornecido = String(dados.codigo ?? req.query.codigo ?? "").trim();

    if (codigoFornecido !== CODIGO_AUTORIZACAO) {
      return res.status(403).json({
        erro: "Código de autorização inválido. Exclusão não permitida.",
      });
    }

    if (dados.limparTudo === true || req.query.limparTudo === "true") {
      await colecao.deleteMany({});
      return res.status(200).json({
        ok: true,
        mensagem: "Todos os registros do ranking foram apagados com sucesso.",
      });
    }

    const idAlvo = String(dados.id ?? req.query.id ?? "").trim();
    if (!idAlvo) {
      return res.status(400).json({
        erro: "Informe o ID do registro a ser apagado ou limparTudo: true.",
      });
    }

    const { ObjectId } = await import("mongodb");
    const resDelete = await colecao.deleteOne({ _id: new ObjectId(idAlvo) });
    if (resDelete.deletedCount === 0) {
      return res.status(404).json({ erro: "Registro não encontrado." });
    }

    return res.status(200).json({
      ok: true,
      mensagem: "Registro do ranking apagado com sucesso.",
    });
  } catch (erro) {
    console.error("[Render Server] Erro ao apagar registro do ranking:", erro);
    return res.status(500).json({ erro: "Falha ao apagar registro." });
  }
});

// ---------------------------------------------------------------------------
// Endpoint de Telemetria (/api/telemetria)
// ---------------------------------------------------------------------------
app.post("/api/telemetria", async (req, res) => {
  try {
    const client = await obterClienteMongo();
    if (!client) {
      return res.status(500).json({ erro: "Falha ao conectar ao MongoDB." });
    }

    const db = client.db("sistema_solar");
    const dados = req.body ?? {};
    const evento = String(dados.evento ?? "interacao").toLowerCase();
    const origem = String(dados.origem ?? "web-vercel");

    if (evento === "sessao") {
      const colecao = db.collection("sessoes");
      await colecao.insertOne({
        origem,
        versao: "1.2.0",
        data_hora: new Date(),
        timestamp: Date.now() / 1000,
      });
      return res.status(200).json({ ok: true, tipo: "sessao" });
    }

    const corpo = String(dados.corpo ?? "").trim();
    if (!corpo) {
      return res.status(400).json({ erro: "Faltou o parâmetro 'corpo'." });
    }

    const colecao = db.collection("interacoes");
    await colecao.insertOne({
      corpo,
      gesto: dados.gesto != null ? String(dados.gesto) : null,
      origem,
      versao: "1.2.0",
      data_hora: new Date(),
      timestamp: Date.now() / 1000,
    });

    return res.status(200).json({ ok: true, tipo: "interacao", corpo });
  } catch (erro) {
    console.error("[Render Server] Erro na telemetria:", erro);
    return res.status(502).json({ erro: "Falha ao registrar no MongoDB." });
  }
});

// ---------------------------------------------------------------------------
// Endpoint de Síntese de Voz ElevenLabs (/api/voz)
// ---------------------------------------------------------------------------
const VOZ_ID = "nPczCjzI2devNBz1zQrb";
const MODELO = "eleven_multilingual_v2";
const FORMATO = "mp3_44100_128";
const IDIOMA = "pt";
const TAMANHO_MAXIMO_TEXTO = 700;

app.get("/api/voz", async (req, res) => {
  const texto = String(req.query.texto ?? "").trim();
  if (!texto) {
    return res.status(400).json({ erro: "Faltou o parâmetro 'texto'." });
  }
  if (texto.length > TAMANHO_MAXIMO_TEXTO) {
    return res.status(413).json({ erro: "Texto longo demais." });
  }

  const rawChaves = process.env.ELEVENLABS_API_KEY ?? "";
  const chaves = rawChaves
    .split(",")
    .map((c) => c.trim())
    .filter(Boolean);

  if (chaves.length === 0) {
    return res
      .status(503)
      .json({ erro: "ELEVENLABS_API_KEY não configurada no servidor." });
  }

  const alvo =
    `https://api.elevenlabs.io/v1/text-to-speech/${VOZ_ID}` +
    `?output_format=${FORMATO}`;

  let ultimoErro = null;

  for (const chave of chaves) {
    try {
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

      if (upstream.ok) {
        const audio = Buffer.from(await upstream.arrayBuffer());
        res.setHeader("Content-Type", "audio/mpeg");
        res.setHeader("Content-Length", String(audio.length));
        res.setHeader(
          "Cache-Control",
          "public, max-age=86400, s-maxage=2592000, immutable"
        );
        return res.status(200).send(audio);
      }

      const detalhe = (await upstream.text()).slice(0, 200);
      console.error("[Render Server] ElevenLabs respondeu", upstream.status, detalhe);
      ultimoErro = `Síntese indisponível (HTTP ${upstream.status}).`;
    } catch (erro) {
      console.error("[Render Server] Falha ao sintetizar:", erro);
      ultimoErro = "Falha ao sintetizar a voz.";
    }
  }

  return res.status(502).json({ erro: ultimoErro ?? "Falha ao sintetizar a voz." });
});

// Inicialização do servidor
app.listen(PORT, () => {
  console.log(`[Render Server] Servidor escutando na porta ${PORT}`);
});
