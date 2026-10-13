/**
 * Endpoint de Ranking / Placar de Usuários (MongoDB Atlas).
 *
 * Suporta POST para cadastrar pontuação, GET para listar o ranking com
 * filtragem precisa por turma e divisão de todas as turmas cadastradas,
 * e DELETE para apagar registros (exige código de autorização 4400).
 *
 * USO:
 *   POST /api/ranking
 *   Body: { nome, serie, sala, turma, quiz, pontuacao, acertos, tempoSegundos }
 *
 *   GET /api/ranking?turma=5º%20A&limit=50
 *   GET /api/ranking?turma=Todas&limit=100
 *
 *   DELETE /api/ranking
 *   Body: { codigo: "4400", id: "<ID_DO_REGISTRO>" } OU { codigo: "4400", limparTudo: true }
 */

import { MongoClient, ObjectId } from "mongodb";

if (typeof process.loadEnvFile === "function") {
  try {
    process.loadEnvFile();
  } catch {
    // .env opcional
  }
}

const CODIGO_AUTORIZACAO = "4400";
let clientCached = null;

async function obterClienteMongo() {
  const uri = process.env.MONGODB_URI;
  if (!uri) return null;
  if (clientCached) return clientCached;

  try {
    const client = new MongoClient(uri, { serverSelectionTimeoutMS: 5000 });
    await client.connect();
    clientCached = client;
    return client;
  } catch (erro) {
    console.error("Falha ao conectar ao MongoDB:", erro);
    return null;
  }
}

/**
 * Normaliza a identificação da turma para formato canônico legível (ex: "5º A", "1º B", "Geral").
 */
export function normalizarTurma(serie, sala, turma) {
  if (turma && typeof turma === "string") {
    const m = turma.trim().match(/^(\d+)[º°]?(?:\s*Ano)?\s*([A-Za-z])/i);
    if (m) return `${m[1]}º ${m[2].toUpperCase()}`;
    if (/^geral/i.test(turma)) return "Geral";
  }

  const strSerie = String(serie ?? "").trim();
  const strSala = String(sala ?? "").trim();

  // Ex: "5º Ano A" ou "5º A"
  const mComp = strSerie.match(/^(\d+)[º°]?(?:\s*Ano)?\s*([A-Za-z])$/i);
  if (mComp) return `${mComp[1]}º ${mComp[2].toUpperCase()}`;

  const mSerie = strSerie.match(/^(\d+)[º°]?(?:\s*Ano)?$/i);
  const mSala = strSala.match(/^([A-Za-z])$/i);

  if (mSerie && mSala && strSala.toLowerCase() !== "única" && strSala.toLowerCase() !== "unica") {
    return `${mSerie[1]}º ${mSala[1].toUpperCase()}`;
  }

  if (/^geral/i.test(strSerie) || strSala.toLowerCase() === "única" || strSala.toLowerCase() === "unica") {
    return "Geral";
  }

  if (mSerie) return `${mSerie[1]}º Ano`;
  return (strSerie || strSala) ? `${strSerie} ${strSala}`.trim() : "Geral";
}

/**
 * Constrói o filtro MongoDB para buscar registros de uma turma específica
 * contemplando todas as estruturas armazenadas no banco (serie + sala, turma, etc.).
 */
export function montarFiltroTurma(turma, serie, sala) {
  const turmaAlvo = String(turma ?? serie ?? "").trim();
  if (!turmaAlvo || turmaAlvo === "Todas" || turmaAlvo === "todas" || turmaAlvo === "Todas as salas") {
    return {};
  }

  // Identifica padrão como "5º A", "5º Ano A", "5 A", "5-A"
  const match = turmaAlvo.match(/^(\d+)[º°]?(?:\s*Ano)?\s*([A-Za-z])/i);
  if (match) {
    const num = match[1];
    const letra = match[2].toUpperCase();
    return {
      $or: [
        {
          $and: [
            { serie: { $regex: new RegExp(`^${num}[º°]?(\\s*ano)?$`, "i") } },
            { sala: { $regex: new RegExp(`^${letra}$`, "i") } }
          ]
        },
        { serie: { $regex: new RegExp(`^${num}[º°]?(\\s*ano)?\\s*${letra}$`, "i") } },
        { turma: { $regex: new RegExp(`^${num}[º°]?\\s*${letra}$`, "i") } },
        { sala: { $regex: new RegExp(`^${num}[º°]?\\s*${letra}$`, "i") } }
      ]
    };
  }

  if (/^geral/i.test(turmaAlvo)) {
    return {
      $or: [
        { serie: { $regex: /^geral/i } },
        { sala: { $regex: /^única|^unica/i } },
        { turma: { $regex: /^geral/i } }
      ]
    };
  }

  // Fallback se especificado serie e sala isolados
  if (serie && serie !== "Todas" && sala && sala !== "Todas") {
    return {
      serie: { $regex: new RegExp(`^${serie}$`, "i") },
      sala: { $regex: new RegExp(`^${sala}$`, "i") }
    };
  }

  return {
    $or: [
      { turma: turmaAlvo },
      { serie: turmaAlvo },
      { sala: turmaAlvo }
    ]
  };
}

/**
 * Coleta e organiza todas as turmas cadastradas na base de dados com as turmas
 * escolares padrão, eliminando duplicatas e ordenando numericamente e alfabeticamente.
 */
export async function obterListaTurmas(colecao) {
  const turmasMap = new Map();

  // Turmas escolares padrão do ensino (1º ao 5º ano, salas A, B, C, D)
  const anosPadrao = [1, 2, 3, 4, 5];
  const salasPadrao = ["A", "B", "C", "D"];
  for (const a of anosPadrao) {
    for (const s of salasPadrao) {
      const nome = `${a}º ${s}`;
      turmasMap.set(nome, { id: nome, nome, totalRespostas: 0 });
    }
  }

  // Busca dados agregados reais do banco de dados para incluir turmas existentes
  try {
    const docs = await colecao.aggregate([
      {
        $group: {
          _id: { serie: "$serie", sala: "$sala", turma: "$turma" },
          total: { $sum: 1 }
        }
      }
    ]).toArray();

    for (const doc of docs) {
      const nomeTurma = normalizarTurma(doc._id?.serie, doc._id?.sala, doc._id?.turma);
      if (turmasMap.has(nomeTurma)) {
        turmasMap.get(nomeTurma).totalRespostas += doc.total;
      } else {
        turmasMap.set(nomeTurma, { id: nomeTurma, nome: nomeTurma, totalRespostas: doc.total });
      }
    }
  } catch (erro) {
    console.error("Erro ao agregar turmas no MongoDB:", erro);
  }

  if (!turmasMap.has("Geral")) {
    turmasMap.set("Geral", { id: "Geral", nome: "Geral / Outro", totalRespostas: 0 });
  }

  const lista = Array.from(turmasMap.values());
  lista.sort((a, b) => {
    const mA = a.id.match(/^(\d+)[º°]?\s*([A-Za-z])/);
    const mB = b.id.match(/^(\d+)[º°]?\s*([A-Za-z])/);
    if (mA && mB) {
      const numDiff = parseInt(mA[1], 10) - parseInt(mB[1], 10);
      if (numDiff !== 0) return numDiff;
      return mA[2].localeCompare(mB[2]);
    }
    if (mA) return -1;
    if (mB) return 1;
    return a.nome.localeCompare(b.nome);
  });

  return lista;
}

export default async function handler(pedido, resposta) {
  resposta.setHeader("Access-Control-Allow-Origin", "*");
  resposta.setHeader("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS");
  resposta.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

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
  // GET: Listar Ranking com filtro por turma e listagem de turmas
  // -------------------------------------------------------------------------
  if (pedido.method === "GET") {
    try {
      const turmaFiltro = String(pedido.query?.turma ?? "").trim();
      const serieFiltro = String(pedido.query?.serie ?? "").trim();
      const salaFiltro = String(pedido.query?.sala ?? "").trim();
      const limite = Math.min(Math.max(parseInt(pedido.query?.limit ?? "100", 10), 1), 200);

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

      return resposta.status(200).json({
        ok: true,
        ranking: formatados,
        turmas: turmasCadastradas,
        total: formatados.length,
        turmaSelecionada: turmaFiltro || serieFiltro || "Todas",
      });
    } catch (erro) {
      console.error("Erro ao buscar ranking:", erro);
      return resposta.status(500).json({ erro: "Falha ao obter ranking." });
    }
  }

  // -------------------------------------------------------------------------
  // POST: Cadastrar Resultado de Quiz
  // -------------------------------------------------------------------------
  if (pedido.method === "POST") {
    try {
      const dados = pedido.body ?? {};
      const nome = String(dados.nome ?? "").trim().slice(0, 50);
      const serie = String(dados.serie ?? "Geral").trim().slice(0, 30);
      const sala = String(dados.sala ?? "").trim().slice(0, 20);
      const quiz = String(dados.quiz ?? "Quiz do Sistema Solar").trim().slice(0, 60);
      const pontuacao = Math.max(0, parseInt(dados.pontuacao ?? 0, 10));
      const acertos = Math.max(0, parseInt(dados.acertos ?? 0, 10));
      const tempoSegundos = Math.max(0, parseFloat(dados.tempoSegundos ?? 0));

      if (!nome) {
        return resposta.status(400).json({ erro: "Informe o nome do aluno." });
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
      return resposta.status(201).json({
        ok: true,
        mensagem: "Resultado salvo no ranking com sucesso!",
        id: resultado.insertedId.toString(),
        turma: turmaCalculada,
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
