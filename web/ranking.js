import { URL_SERVIDOR_RENDER } from "./config.js";

const ENDPOINT_RANKING = "/api/ranking";
let dadosRankingCompletos = [];
let turmaAtual = "Todas";
let turmasCarregadas = false;

document.addEventListener("DOMContentLoaded", () => {
  const filtroSerie = document.getElementById("filtro-serie");
  const buscaNome = document.getElementById("busca-nome");
  const formRanking = document.getElementById("form-ranking");
  const btnLimpar = document.getElementById("btn-limpar-ranking");

  const params = new URLSearchParams(window.location.search);
  const turmaParam = params.get("turma") || params.get("serie") || "Todas";
  turmaAtual = turmaParam;
  if (filtroSerie) {
    filtroSerie.value = turmaAtual;
  }

  carregarRanking(turmaAtual);

  if (filtroSerie) {
    filtroSerie.addEventListener("change", () => {
      turmaAtual = filtroSerie.value;
      if (buscaNome) buscaNome.value = "";
      const url = new URL(window.location);
      if (turmaAtual && turmaAtual !== "Todas") {
        url.searchParams.set("turma", turmaAtual);
      } else {
        url.searchParams.delete("turma");
      }
      window.history.replaceState({}, "", url);
      carregarRanking(turmaAtual);
    });
  }

  if (buscaNome) {
    buscaNome.addEventListener("input", () => {
      filtrarETabelar(buscaNome.value);
    });
  }

  if (formRanking) {
    formRanking.addEventListener("submit", async (e) => {
      e.preventDefault();
      await cadastrarResultado(formRanking);
    });
  }

  if (btnLimpar) {
    btnLimpar.addEventListener("click", () => {
      apagarRegistros(null, true);
    });
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

/**
 * Busca dados do ranking via API (/api/ranking com fallback para Render)
 */
async function carregarRanking(turma = "Todas") {
  turmaAtual = turma;
  const corpoTabela = document.getElementById("tabela-corpo");
  if (corpoTabela) {
    corpoTabela.innerHTML = `<tr><td colspan="8" class="carregando"><i class="bi bi-arrow-clockwise girando"></i> Carregando classificação...</td></tr>`;
  }

  let url = `${ENDPOINT_RANKING}?limit=100`;
  if (turma && turma !== "Todas") {
    url += `&turma=${encodeURIComponent(turma)}`;
  }

  let ranking = [];
  let listaTurmas = [];

  try {
    let resposta = await fetch(url);
    if (!resposta.ok && URL_SERVIDOR_RENDER) {
      const urlRender = `${URL_SERVIDOR_RENDER}/api/ranking?limit=100${
        turma && turma !== "Todas" ? `&turma=${encodeURIComponent(turma)}` : ""
      }`;
      resposta = await fetch(urlRender);
    }

    if (resposta.ok) {
      const json = await resposta.json();
      ranking = json.ranking ?? [];
      listaTurmas = json.turmas ?? [];
    }
  } catch (erro) {
    console.error("Falha ao buscar ranking:", erro);
  }

  dadosRankingCompletos = ranking;

  // Atualiza opções do select de turmas se recebido do backend
  if (listaTurmas.length > 0 && !turmasCarregadas) {
    atualizarSelectTurmas(listaTurmas, turma);
    turmasCarregadas = true;
  }

  atualizarPodio(ranking);
  renderizarTabela(ranking, turma);
}

/**
 * Popula dinamicamente o seletor com todas as turmas cadastradas
 */
function atualizarSelectTurmas(turmas, selecionada) {
  const select = document.getElementById("filtro-serie");
  if (!select) return;

  const valorAnterior = selecionada || select.value || "Todas";

  const opcoesHtml = [
    '<option value="Todas">Todas as salas</option>',
    ...turmas.map((t) => {
      const sufixoContagem = t.totalRespostas > 0 ? ` (${t.totalRespostas})` : "";
      return `<option value="${escaparHtml(t.id)}">${escaparHtml(t.nome)}${sufixoContagem}</option>`;
    }),
  ].join("");

  select.innerHTML = opcoesHtml;
  select.value = valorAnterior;
}

/**
 * Atualiza os cartões do Pódio (Top 3)
 */
function atualizarPodio(ranking) {
  const containerPodio = document.getElementById("podio");
  if (!containerPodio) return;

  if (!ranking || ranking.length === 0) {
    containerPodio.hidden = true;
    return;
  }

  containerPodio.hidden = false;

  [1, 2, 3].forEach((pos) => {
    const item = ranking[pos - 1];
    const el = document.getElementById(`podio-${pos}`);
    if (!el) return;

    if (item) {
      el.style.display = "block";
      const elNome = el.querySelector(".nome-aluno");
      const elSerie = el.querySelector(".serie-aluno");
      const elPontos = el.querySelector(".pontos-aluno");

      if (elNome) elNome.textContent = item.nome;
      if (elSerie) elSerie.textContent = item.turma || item.serie || "—";
      if (elPontos) elPontos.textContent = `${item.pontuacao} pts`;
    } else {
      el.style.display = "none";
    }
  });
}

/**
 * Formata duração em segundos para string amigável (ex: "1m 15s" ou "45s")
 */
function formatarTempo(segundos) {
  const segs = Math.max(0, Math.round(Number(segundos) || 0));
  if (segs === 0) return "—";
  const min = Math.floor(segs / 60);
  const resto = segs % 60;
  if (min > 0) {
    return `${min}m ${resto}s`;
  }
  return `${resto}s`;
}

/**
 * Renderiza as linhas da tabela de classificação
 */
function renderizarTabela(lista, turma = turmaAtual) {
  const corpoTabela = document.getElementById("tabela-corpo");
  if (!corpoTabela) return;

  if (!lista || lista.length === 0) {
    const mensagemVazia =
      turma && turma !== "Todas"
        ? "Nenhum aluno desta turma respondeu aos quizzes ainda."
        : "Nenhum resultado registrado ainda.";

    corpoTabela.innerHTML = `
      <tr>
        <td colspan="8" class="carregando">
          <i class="bi bi-info-circle"></i> ${mensagemVazia}
        </td>
      </tr>
    `;
    return;
  }

  const html = lista
    .map((item, index) => {
      const pos = item.posicao ?? index + 1;
      let posTag = `<span class="posicao-tag">${pos}</span>`;
      if (pos === 1) posTag = `<span class="posicao-tag pos-1"><i class="bi bi-trophy-fill"></i> 1</span>`;
      if (pos === 2) posTag = `<span class="posicao-tag pos-2"><i class="bi bi-award-fill"></i> 2</span>`;
      if (pos === 3) posTag = `<span class="posicao-tag pos-3"><i class="bi bi-award"></i> 3</span>`;

      const dataFormatada = item.data_hora
        ? new Date(item.data_hora).toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })
        : "—";

      const totalQuestoes = item.totalQuestoes ?? 10;
      const acertos = item.acertos ?? 0;
      const erros = item.erros ?? Math.max(0, totalQuestoes - acertos);
      const turmaExibicao = item.turma || (item.serie && item.sala ? `${item.serie} - ${item.sala}` : item.serie || "—");
      const quizExibicao = item.quiz || "Quiz do Sistema Solar";
      const tempoFormatado = formatarTempo(item.tempoSegundos);

      return `
      <tr>
        <td>${posTag}</td>
        <td>
          <div class="aluno-info">
            <strong class="aluno-nome">${escaparHtml(item.nome)}</strong>
          </div>
        </td>
        <td>
          <span class="turma-badge">${escaparHtml(turmaExibicao)}</span>
        </td>
        <td>
          <span class="quiz-badge" title="${escaparHtml(quizExibicao)}">
            <i class="bi bi-journal-check"></i> ${escaparHtml(quizExibicao)}
          </span>
        </td>
        <td>
          <strong class="pontuacao-valor">${item.pontuacao} pts</strong>
        </td>
        <td>
          <div class="desempenho-col">
            <span class="acertos-tag">
              <i class="bi bi-check-circle-fill"></i> ${acertos}/${totalQuestoes} acertos
            </span>
            <span class="erros-tag">
              <i class="bi bi-x-circle-fill"></i> ${erros} erro${erros === 1 ? "" : "s"}
            </span>
            ${
              tempoFormatado !== "—"
                ? `<span class="tempo-tag"><i class="bi bi-stopwatch"></i> ${tempoFormatado}</span>`
                : ""
            }
          </div>
        </td>
        <td>
          <small class="data-hora-texto">
            <i class="bi bi-calendar3"></i> ${dataFormatada}
          </small>
        </td>
        <td>
          <button type="button" class="btn-excluir-item" data-id="${item.id}" title="Apagar este registro">
            <i class="bi bi-trash"></i> Excluir
          </button>
        </td>
      </tr>
    `;
    })
    .join("");

  corpoTabela.innerHTML = html;

  // Manipuladores de exclusão individual
  corpoTabela.querySelectorAll(".btn-excluir-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      apagarRegistros(id, false);
    });
  });
}

/**
 * Filtra localmente pelo nome do aluno
 */
function filtrarETabelar(termoBusca) {
  const termo = termoBusca.toLowerCase().trim();
  if (!termo) {
    renderizarTabela(dadosRankingCompletos, turmaAtual);
    return;
  }

  const filtrados = dadosRankingCompletos.filter((item) =>
    (item.nome || "").toLowerCase().includes(termo)
  );

  const corpoTabela = document.getElementById("tabela-corpo");
  if (filtrados.length === 0 && corpoTabela) {
    corpoTabela.innerHTML = `
      <tr>
        <td colspan="8" class="carregando">
          <i class="bi bi-search"></i> Nenhum aluno encontrado com "${escaparHtml(termo)}".
        </td>
      </tr>
    `;
    return;
  }

  renderizarTabela(filtrados, turmaAtual);
}

/**
 * Cadastra uma nova pontuação
 */
async function cadastrarResultado(form) {
  const msgEl = document.getElementById("mensagem-form");
  const btnSalvar = document.getElementById("btn-salvar");

  const nome = form.nome.value.trim();
  const serie = form.serie.value;
  const sala = form.sala?.value || "Única";
  const pontuacao = parseInt(form.pontuacao.value, 10);
  const acertos = parseInt(form.acertos.value, 10);

  if (!nome) return;

  btnSalvar.disabled = true;
  btnSalvar.innerHTML = `<i class="bi bi-arrow-clockwise girando"></i> Salvando...`;

  const payload = {
    nome,
    serie,
    sala,
    quiz: "Quiz do Sistema Solar",
    pontuacao,
    acertos,
    tempoSegundos: 0,
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
      msgEl.className = "mensagem-status sucesso";
      msgEl.innerHTML = `<i class="bi bi-check-circle-fill"></i> Pontuação cadastrada com sucesso!`;
      form.reset();
      form.pontuacao.value = "100";
      form.acertos.value = "10";
      await carregarRanking(turmaAtual);
    } else {
      throw new Error(`HTTP ${resposta.status}`);
    }
  } catch (erro) {
    console.error("Erro ao salvar resultado:", erro);
    msgEl.className = "mensagem-status erro";
    msgEl.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> Falha ao salvar pontuação. Tente novamente.`;
  } finally {
    btnSalvar.disabled = false;
    btnSalvar.innerHTML = `<i class="bi bi-star-fill"></i> Cadastrar Pontuação`;
    setTimeout(() => {
      if (msgEl) msgEl.innerHTML = "";
    }, 4000);
  }
}

/**
 * Apaga registros exigindo o código de autorização "4400"
 */
async function apagarRegistros(idItem = null, limparTudo = false) {
  const mensagemPrompt = limparTudo
    ? "AVISO: Isso vai apagar TODO o ranking!\nDigite o código de autorização (4 dígitos) para confirmar:"
    : "Digite o código de autorização (4 dígitos) para apagar este registro:";

  const codigo = prompt(mensagemPrompt);
  if (!codigo) return;

  if (codigo.trim() !== "4400") {
    alert("Código de autorização incorreto! Exclusão não permitida.");
    return;
  }

  const payload = { codigo: "4400" };
  if (limparTudo) {
    payload.limparTudo = true;
  } else if (idItem) {
    payload.id = idItem;
  }

  try {
    let resposta = await fetch(ENDPOINT_RANKING, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resposta.ok && URL_SERVIDOR_RENDER) {
      resposta = await fetch(`${URL_SERVIDOR_RENDER}/api/ranking`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }

    if (resposta.ok) {
      alert("Exclusão realizada com sucesso!");
      await carregarRanking(turmaAtual);
    } else {
      const json = await resposta.json().catch(() => ({}));
      alert(`Falha ao excluir: ${json.erro || "Código de autorização inválido."}`);
    }
  } catch (erro) {
    console.error("Erro ao excluir do ranking:", erro);
    alert("Erro ao comunicar com o servidor.");
  }
}

function escaparHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
