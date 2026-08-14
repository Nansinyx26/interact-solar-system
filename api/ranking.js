/**
 * Endpoint de Ranking / Placar de Usuários (MongoDB Atlas).
 *
 * Suporta POST para cadastrar pontuação, GET para listar o ranking e DELETE para apagar (exige código 4400).
 *
 * USO:
 *   POST /api/ranking
 *   Body: { nome, serie, sala, pontuacao, acertos, tempoSegundos }
 *
 *   GET /api/ranking?serie=5º%20Ano&sala=A&limit=50
 *
 *   DELETE /api/ranking
 *   Body: { codigo: "4400", id: "<ID_DO_REGISTRO>" } OU { codigo: "4400", limparTudo: true }
 */

import { MongoClient, ObjectId } from "mongodb";

const CODIGO_AUTORIZACAO = "4400";
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
  resposta.setHeader("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS");
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
      const salaFiltro = String(pedido.query?.sala ?? "").trim();
      const limite = Math.min(Math.max(parseInt(pedido.query?.limit ?? "50", 10), 1), 100);

      const filtro = {};
      if (serieFiltro && serieFiltro !== "Todas") {
        filtro.serie = serieFiltro;
      }
      // A classificação pode ser vista por sala: é o recorte que a turma usa.
      if (salaFiltro && salaFiltro !== "Todas") {
        filtro.sala = salaFiltro;
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
        sala: item.sala ?? "—",
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
      const sala = String(dados.sala ?? "").trim().slice(0, 20);
      const pontuacao = Math.max(0, parseInt(dados.pontuacao ?? 0, 10));
      const acertos = Math.max(0, parseInt(dados.acertos ?? 0, 10));
      const tempoSegundos = Math.max(0, parseFloat(dados.tempoSegundos ?? 0));

      if (!nome) {
        return resposta.status(400).json({ erro: "Informe o nome do aluno." });
      }

      const doc = {
        nome,
        serie: serie || "Geral",
        sala: sala || "Única",
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

  // -------------------------------------------------------------------------
  // DELETE: Apagar Informações (Exige Código 4400)
  // -------------------------------------------------------------------------
  if (pedido.method === "DELETE") {
    try {
      const dados = pedido.body ?? {};
      const codigoFornecido = String(dados.codigo ?? pedido.query?.codigo ?? "").trim();

      if (codigoFornecido !== CODIGO_AUTORIZACAO) {
        return resposta.status(403).json({
          erro: "Código de autorização inválido. Exclusão não permitida.",
        });
      }

      if (dados.limparTudo === true || pedido.query?.limparTudo === "true") {
        await colecao.deleteMany({});
        return resposta.status(200).json({
          ok: true,
          mensagem: "Todos os registros do ranking foram apagados com sucesso.",
        });
      }

      const idAlvo = String(dados.id ?? pedido.query?.id ?? "").trim();
      if (!idAlvo) {
        return resposta.status(400).json({
          erro: "Informe o ID do registro a ser apagado ou limparTudo: true.",
        });
      }

      const resDelete = await colecao.deleteOne({ _id: new ObjectId(idAlvo) });
      if (resDelete.deletedCount === 0) {
        return resposta.status(404).json({ erro: "Registro não encontrado." });
      }

      return resposta.status(200).json({
        ok: true,
        mensagem: "Registro do ranking apagado com sucesso.",
      });
    } catch (erro) {
      console.error("Erro ao apagar registro do ranking:", erro);
      return resposta.status(500).json({ erro: "Falha ao apagar registro." });
    }
  }

  return resposta.status(405).json({ erro: "Método não permitido. Use GET, POST ou DELETE." });
}
