import { URL_SERVIDOR_RENDER } from "./config.js";

const ENDPOINT_RANKING = "/api/ranking";

const QUESTOES = [
  {
    id: 1,
    pergunta: "1. Qual é o maior planeta de todo o Sistema Solar?",
    opcoes: ["Terra", "Júpiter", "Saturno", "Sol"],
    correta: 1, // Júpiter
  },
  {
    id: 2,
    pergunta: "2. Qual planeta é conhecido popularmente como o 'Planeta Vermelho'?",
    opcoes: ["Vênus", "Mercúrio", "Marte", "Júpiter"],
    correta: 2, // Marte
  },
  {
    id: 3,
    pergunta: "3. Qual é o único satélite natural do planeta Terra?",
    opcoes: ["Lua", "Fobos", "Titã", "Europa"],
    correta: 0, // Lua
  },
  {
    id: 4,
    pergunta: "4. Qual é o planeta mais QUENTE do Sistema Solar (devido ao efeito estufa denso)?",
    opcoes: ["Mercúrio", "Vênus", "Marte", "Sol"],
    correta: 1, // Vênus
  },
  {
    id: 5,
    pergunta: "5. Qual planeta é famoso por ter os anéis mais impressionantes e brilhantes?",
    opcoes: ["Urano", "Netuno", "Saturno", "Júpiter"],
    correta: 2, // Saturno
  },
  {
    id: 6,
    pergunta: "6. Qual é o planeta mais próximo do Sol?",
    opcoes: ["Mercúrio", "Vênus", "Terra", "Marte"],
    correta: 0, // Mercúrio
  },
  {
    id: 7,
    pergunta: "7. Qual planeta possui uma inclinação extrema de 98º e gira quase 'deitado'?",
    opcoes: ["Netuno", "Urano", "Saturno", "Mercúrio"],
    correta: 1, // Urano
  },
  {
    id: 8,
    pergunta: "8. Qual é o planeta mais distante do Sol no nosso Sistema Solar?",
    opcoes: ["Urano", "Saturno", "Netuno", "Júpiter"],
    correta: 2, // Netuno
  },
  {
    id: 9,
    pergunta: "9. O que está localizado exatamente no centro do nosso Sistema Solar?",
    opcoes: ["A Terra", "O Sol (uma estrela)", "Júpiter", "A Lua"],
    correta: 1, // O Sol
  },
  {
    id: 10,
    pergunta: "10. Quanto tempo a Terra leva para dar uma volta completa ao redor do Sol?",
    opcoes: ["24 horas", "30 dias", "365 dias e 6 horas (1 ano)", "12 anos"],
    correta: 2, // 365 dias
  },
];

let estadoQuiz = {
  nomeAluno: "",
  serieAluno: "",
  // Sala separada da série: a classificação agrupa por sala.
  salaAluno: "",
  indiceQuestao: 0,
  respostasUsuario: Array(QUESTOES.length).fill(null),
  tempoInicio: 0,
  tempoTotalSegundos: 0,
  intervaloCronometro: null,
};

document.addEventListener("DOMContentLoaded", () => {
  const formIdentificacao = document.getElementById("form-identificacao");
  const btnResponder = document.getElementById("btn-responder");
  const btnEnviarRanking = document.getElementById("btn-enviar-ranking");
  const btnReiniciar = document.getElementById("btn-reiniciar");

  if (formIdentificacao) {
    formIdentificacao.addEventListener("submit", (e) => {
      e.preventDefault();
      iniciarQuiz();
    });
  }

  if (btnResponder) {
    btnResponder.addEventListener("click", responderEAvancar);
  }

  if (btnEnviarRanking) {
    btnEnviarRanking.addEventListener("click", enviarParaRanking);
  }

  if (btnReiniciar) {
    btnReiniciar.addEventListener("click", reiniciarQuiz);
  }

  const btnTema = document.getElementById("btn-alternar-tema");
  if (btnTema) {
    const atualizarIcone = () => {
      const ehClaro = document.documentElement.classList.contains("tema-claro");
      btnTema.innerHTML = ehClaro
        ? '<i class="bi bi-moon-stars"></i> <span>Escuro</span>'
        : '<i class="bi bi-sun"></i> <span>Claro</span>';
    };
    atualizarIcone();
    btnTema.addEventListener("click", () => {
      document.documentElement.classList.toggle("tema-claro");
      document.body.classList.toggle("tema-claro");
      const ehClaro = document.documentElement.classList.contains("tema-claro");
      localStorage.setItem("tema_sistema_solar", ehClaro ? "claro" : "escuro");
      atualizarIcone();
    });
  }
});

function iniciarQuiz() {
  const inputNome = document.getElementById("nome-aluno");
  const selectSerie = document.getElementById("serie-aluno");
  const selectSala = document.getElementById("sala-aluno");

  estadoQuiz.nomeAluno = inputNome.value.trim();
  estadoQuiz.serieAluno = selectSerie.value;
  estadoQuiz.salaAluno = selectSala.value;
  estadoQuiz.indiceQuestao = 0;
  estadoQuiz.respostasUsuario = Array(QUESTOES.length).fill(null);
  estadoQuiz.tempoInicio = Date.now();

  document.getElementById("passo-identificacao").hidden = true;
  document.getElementById("passo-quiz").hidden = false;

  iniciarCronometro();
  exibirQuestao();
}

function iniciarCronometro() {
  const elCrono = document.getElementById("cronometro");
  if (estadoQuiz.intervaloCronometro) clearInterval(estadoQuiz.intervaloCronometro);

  estadoQuiz.intervaloCronometro = setInterval(() => {
    const segs = Math.floor((Date.now() - estadoQuiz.tempoInicio) / 1000);
    const mins = Math.floor(segs / 60);
    const segsRest = segs % 60;
    elCrono.innerHTML = `<i class="bi bi-stopwatch"></i> ${String(mins).padStart(2, "0")}:${String(segsRest).padStart(
      2,
      "0"
    )}`;
  }, 1000);
}

function exibirQuestao() {
  const q = QUESTOES[estadoQuiz.indiceQuestao];
  const total = QUESTOES.length;

  document.getElementById("numero-questao").textContent = `Questão ${
    estadoQuiz.indiceQuestao + 1
  } de ${total}`;

  const pct = ((estadoQuiz.indiceQuestao + 1) / total) * 100;
  document.getElementById("linha-progresso").style.width = `${pct}%`;

  const containerConteudo = document.getElementById("conteudo-questao");
  const letras = ["A", "B", "C", "D"];

  const selecaoAtual = estadoQuiz.respostasUsuario[estadoQuiz.indiceQuestao];

  containerConteudo.innerHTML = `
    <h2 class="titulo-questao">${q.pergunta}</h2>
    <div class="opcoes-lista">
      ${q.opcoes
        .map(
          (opt, idx) => `
        <div class="opcao-item ${selecaoAtual === idx ? "selecionada" : ""}" data-idx="${idx}">
          <span class="opcao-letra">${letras[idx]}</span>
          <span class="opcao-texto">${opt}</span>
        </div>
      `
        )
        .join("")}
    </div>
  `;

  // Adiciona evento de clique nas opções
  const itens = containerConteudo.querySelectorAll(".opcao-item");
  itens.forEach((item) => {
    item.addEventListener("click", () => {
      itens.forEach((i) => i.classList.remove("selecionada"));
      item.classList.add("selecionada");
      const idx = parseInt(item.dataset.idx, 10);
      estadoQuiz.respostasUsuario[estadoQuiz.indiceQuestao] = idx;
    });
  });

  const btn = document.getElementById("btn-responder");
  btn.innerHTML =
    estadoQuiz.indiceQuestao === total - 1
      ? '<i class="bi bi-check2-circle"></i> Finalizar Atividade'
      : 'Próxima Questão <i class="bi bi-arrow-right-circle"></i>';
}

function responderEAvancar() {
  const selecao = estadoQuiz.respostasUsuario[estadoQuiz.indiceQuestao];
  if (selecao === null || selecao === undefined) {
    alert("Por favor, selecione uma opção para continuar!");
    return;
  }

  if (estadoQuiz.indiceQuestao < QUESTOES.length - 1) {
    estadoQuiz.indiceQuestao++;
    exibirQuestao();
  } else {
    finalizarQuiz();
  }
}

function finalizarQuiz() {
  if (estadoQuiz.intervaloCronometro) clearInterval(estadoQuiz.intervaloCronometro);
  estadoQuiz.tempoTotalSegundos = Math.floor((Date.now() - estadoQuiz.tempoInicio) / 1000);

  document.getElementById("passo-quiz").hidden = true;
  document.getElementById("passo-resultado").hidden = false;

  // Cálculo dos acertos e pontuação
  let acertos = 0;
  QUESTOES.forEach((q, idx) => {
    if (estadoQuiz.respostasUsuario[idx] === q.correta) {
      acertos++;
    }
  });

  // Cada acerto vale 100 pontos (máximo 1000 pts)
  const pontuacaoTotal = acertos * 100;

  document.getElementById("res-pontos").textContent = `${pontuacaoTotal} pts`;
  document.getElementById("res-acertos").textContent = `${acertos} / ${QUESTOES.length}`;
  document.getElementById("res-tempo").textContent = `${estadoQuiz.tempoTotalSegundos}s`;

  document.getElementById(
    "subtitulo-resultado"
  ).textContent = `Parabéns, ${estadoQuiz.nomeAluno} — ${estadoQuiz.serieAluno}, sala ${estadoQuiz.salaAluno}! Seu resultado foi gravado.`;

  gerarGabarito();
}

function gerarGabarito() {
  const container = document.getElementById("gabarito-lista");
  const letras = ["A", "B", "C", "D"];

  const html = QUESTOES.map((q, idx) => {
    const respUser = estadoQuiz.respostasUsuario[idx];
    const acertou = respUser === q.correta;

    return `
      <div class="gabarito-item ${acertou ? "correta" : "incorreta"}">
        <strong>${q.pergunta}</strong><br>
        <span style="color: ${acertou ? "var(--sucesso)" : "var(--erro)"}; font-weight: bold;">
          ${acertou ? '<i class="bi bi-check-circle-fill"></i> Correto!' : '<i class="bi bi-x-circle-fill"></i> Incorreto!'}
        </span>
        Sua resposta: <em>${respUser !== null ? q.opcoes[respUser] : "Nenhuma"}</em>
        ${!acertou ? `<br><i class="bi bi-arrow-right" style="color: var(--destaque)"></i> Resposta certa: <strong>${q.opcoes[q.correta]}</strong>` : ""}
      </div>
    `;
  }).join("");

  container.innerHTML = html;
}

async function enviarParaRanking() {
  const btn = document.getElementById("btn-enviar-ranking");
  const msg = document.getElementById("mensagem-ranking");

  let acertos = 0;
  QUESTOES.forEach((q, idx) => {
    if (estadoQuiz.respostasUsuario[idx] === q.correta) acertos++;
  });
  const pontuacao = acertos * 100;

  btn.disabled = true;
  btn.textContent = "Enviando...";

  const payload = {
    nome: estadoQuiz.nomeAluno,
    serie: estadoQuiz.serieAluno,
    sala: estadoQuiz.salaAluno,
    pontuacao,
    acertos,
    tempoSegundos: estadoQuiz.tempoTotalSegundos,
  };

  try {
    let resposta = await fetch(ENDPOINT_RANKING, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resposta.ok && URL_SERVIDOR_RENDER) {
      resposta = await fetch(`${URL_SERVIDOR_RENDER}/api/ranking`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }

    if (resposta.ok) {
      msg.className = "mensagem-status sucesso";
      msg.innerHTML = '<i class="bi bi-trophy-fill"></i> Resultado registrado no Ranking com sucesso!';
      setTimeout(() => {
        window.location.href = "ranking.html";
      }, 1500);
    } else {
      throw new Error(`HTTP ${resposta.status}`);
    }
  } catch (erro) {
    console.error("Erro ao enviar resultado para o ranking:", erro);
    msg.className = "mensagem-status erro";
    msg.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i> Falha ao enviar para o ranking. Tente novamente.';
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-trophy"></i> Enviar Resultado para o Ranking';
  }
}

function reiniciarQuiz() {
  document.getElementById("passo-resultado").hidden = true;
  document.getElementById("passo-identificacao").hidden = false;
}
