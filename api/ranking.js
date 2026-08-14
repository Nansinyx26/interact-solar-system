/**
 * Endpoint de Ranking / Placar de Usuários (MongoDB Atlas).
 *
 * Suporta POST para cadastrar pontuação e GET para listar o ranking (com filtro por série).
 *
 * USO:
 *   POST /api/ranking
 *   Body: { nome: "Renan", serie: "7º Ano A", pontuacao: 950, acertos: 9, tempoSegundos: 45 }
 *
 *   GET /api/ranking?serie=7º%20Ano%20A&limit=50
 */

import { MongoClient } from "mongodb";

let clientCached = null;

async function obterClienteMongo() {
  const uri = process.env.MONGODB_URI;
  if (!uri) return null;
  if (clientCached) return clientCached;

  try {
    const client = new MongoClient(uri, { serverSelectionTimeoutMS: 3000 });
    await client.connect();
    clientCached = client;
    return client;
  } catch (erro) {
    console.error("Falha ao conectar ao MongoDB:", erro);
    return null;
  }
}

export default async function handler(pedido, resposta) {
  // CORS Headers
  resposta.setHeader("Access-Control-Allow-Origin", "*");
  resposta.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  resposta.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (pedido.method === "OPTIONS") {
    return resposta.status(200).end();
  }

  const client = await obterClienteMongo();
  if (!client) {
    return resposta.status(503).json({ erro: "Banco de dados indisponível." });
  }

  const db = client.db("sistema_solar");
  const colecao = db.collection("ranking");

  // -------------------------------------------------------------------------
  // GET: Listar Ranking
  // -------------------------------------------------------------------------
  if (pedido.method === "GET") {
    try {
      const serieFiltro = String(pedido.query?.serie ?? "").trim();
      const limite = Math.min(Math.max(parseInt(pedido.query?.limit ?? "50", 10), 1), 100);

      const filtro = {};
      if (serieFiltro && serieFiltro !== "Todas") {
        filtro.serie = serieFiltro;
      }

      const resultados = await colecao
        .find(filtro)
        .sort({ pontuacao: -1, tempoSegundos: 1, timestamp: -1 })
        .limit(limite)
        .toArray();

      const formatados = resultados.map((item, index) => ({
        posicao: index + 1,
        id: item._id.toString(),
        nome: item.nome ?? "Anônimo",
        serie: item.serie ?? "Geral",
        pontuacao: item.pontuacao ?? 0,
        acertos: item.acertos ?? 0,
        tempoSegundos: item.tempoSegundos ?? 0,
        data_hora: item.data_hora ?? new Date().toISOString(),
      }));

      return resposta.status(200).json({ ok: true, ranking: formatados });
    } catch (erro) {
      console.error("Erro ao buscar ranking:", erro);
      return resposta.status(500).json({ erro: "Falha ao obter ranking." });
    }
  }

  // -------------------------------------------------------------------------
  // POST: Cadastrar Resultado
  // -------------------------------------------------------------------------
  if (pedido.method === "POST") {
    try {
      const dados = pedido.body ?? {};
      const nome = String(dados.nome ?? "").trim().slice(0, 50);
      const serie = String(dados.serie ?? "Geral").trim().slice(0, 30);
      const pontuacao = Math.max(0, parseInt(dados.pontuacao ?? 0, 10));
      const acertos = Math.max(0, parseInt(dados.acertos ?? 0, 10));
      const tempoSegundos = Math.max(0, parseFloat(dados.tempoSegundos ?? 0));

      if (!nome) {
        return resposta.status(400).json({ erro: "Informe o nome do aluno." });
      }

      const doc = {
        nome,
        serie: serie || "Geral",
        pontuacao,
        acertos,
        tempoSegundos,
        data_hora: new Date(),
        timestamp: Date.now() / 1000,
      };

      const resultado = await colecao.insertOne(doc);
      return resposta.status(201).json({
        ok: true,
        mensagem: "Resultado salvo no ranking com sucesso!",
        id: resultado.insertedId.toString(),
      });
    } catch (erro) {
      console.error("Erro ao salvar resultado no ranking:", erro);
      return resposta.status(500).json({ erro: "Falha ao registrar resultado." });
    }
  }

  return resposta.status(405).json({ erro: "Método não permitido. Use GET ou POST." });
}
