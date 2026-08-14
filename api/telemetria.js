/**
 * Endpoint de telemetria / estatísticas do MongoDB Atlas.
 *
 * Registra acessos e interações (seleção de planetas, gestos) no banco MongoDB Atlas.
 *
 * Uso: POST /api/telemetria
 * Body: { evento: "sessao", origem: "web" }
 *       { evento: "interacao", corpo: "Saturno", gesto: "2", origem: "web" }
 */

import { MongoClient } from "mongodb";

let clientCached = null;

async function obterClienteMongo() {
  const uri = process.env.MONGODB_URI;
  if (!uri) return null;
  if (clientCached) return clientCached;

  const client = new MongoClient(uri, {
    serverSelectionTimeoutMS: 3000,
  });
  await client.connect();
  clientCached = client;
  return client;
}

export default async function handler(pedido, resposta) {
  if (pedido.method !== "POST") {
    return resposta.status(405).json({ erro: "Use POST." });
  }

  const uri = process.env.MONGODB_URI;
  if (!uri) {
    return resposta.status(503).json({ erro: "MONGODB_URI não configurada." });
  }

  try {
    const client = await obterClienteMongo();
    if (!client) {
      return resposta.status(500).json({ erro: "Falha ao conectar ao MongoDB." });
    }

    const db = client.db("sistema_solar");
    const dados = pedido.body ?? {};
    const evento = String(dados.evento ?? "interacao").toLowerCase();
    const origem = String(dados.origem ?? "web");

    if (evento === "sessao") {
      const colecao = db.collection("sessoes");
      await colecao.insertOne({
        origem,
        versao: "1.2.0",
        data_hora: new Date(),
        timestamp: Date.now() / 1000,
      });
      return resposta.status(200).json({ ok: true, tipo: "sessao" });
    }

    const corpo = String(dados.corpo ?? "").trim();
    if (!corpo) {
      return resposta.status(400).json({ erro: "Faltou o parâmetro 'corpo'." });
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

    return resposta.status(200).json({ ok: true, tipo: "interacao", corpo });
  } catch (erro) {
    console.error("Erro na telemetria:", erro);
    return resposta.status(502).json({ erro: "Falha ao registrar no MongoDB." });
  }
}
