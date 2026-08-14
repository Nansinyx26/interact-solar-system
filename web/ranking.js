import { URL_SERVIDOR_RENDER } from "./config.js";

const ENDPOINT_RANKING = "/api/ranking";
let dadosRankingCompletos = [];

document.addEventListener("DOMContentLoaded", () => {
  carregarRanking();

  const filtroSerie = document.getElementById("filtro-serie");
  const buscaNome = document.getElementById("busca-nome");
  const formRanking = document.getElementById("form-ranking");

  if (filtroSerie) {
    filtroSerie.addEventListener("change", () => {
      carregarRanking(filtroSerie.value);
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
});

/**
 * Busca dados do ranking via API (/api/ranking com fallback para Render)
 */
async function carregarRanking(serie = "Todas") {
  const corpoTabela = document.getElementById("tabela-corpo");
  if (corpoTabela) {
    corpoTabela.innerHTML = `<tr><td colspan="6" class="carregando">Carregando classificação...</td></tr>`;
  }

  let url = `${ENDPOINT_RANKING}?limit=100`;
  if (serie && serie !== "Todas") {
    url += `&serie=${encodeURIComponent(serie)}`;
  }

  let ranking = [];

  try {
    let resposta = await fetch(url);
    if (!resposta.ok && URL_SERVIDOR_RENDER) {
      const urlRender = `${URL_SERVIDOR_RENDER}/api/ranking?limit=100${
        serie && serie !== "Todas" ? `&serie=${encodeURIComponent(serie)}` : ""
      }`;
      resposta = await fetch(urlRender);
    }

    if (resposta.ok) {
      const json = await resposta.json();
      ranking = json.ranking ?? [];
    }
  } catch (erro) {
    console.error("Falha ao buscar ranking:", erro);
  }

  dadosRankingCompletos = ranking;
  atualizarPodio(ranking);
  renderizarTabela(ranking);
}

/**
 * Atualiza os cartões do Pódio (Top 3)
 */
function atualizarPodio(ranking) {
  const containerPodio = document.getElementById("podio");
  if (!containerPodio) return;

  if (ranking.length === 0) {
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
      el.querySelector(".nome-aluno").textContent = item.nome;
      el.querySelector(".serie-aluno").textContent = item.serie;
      el.querySelector(".pontos-aluno").textContent = `${item.pontuacao} pts`;
    } else {
      el.style.display = "none";
    }
  });
}

/**
 * Renderiza as linhas da tabela de classificação
 */
function renderizarTabela(lista) {
  const corpoTabela = document.getElementById("tabela-corpo");
  if (!corpoTabela) return;

  if (lista.length === 0) {
    corpoTabela.innerHTML = `<tr><td colspan="6" class="carregando">Nenhum resultado registrado ainda.</td></tr>`;
    return;
  }

  const html = lista
    .map((item, index) => {
      const pos = index + 1;
      let posTag = `<span class="posicao-tag">${pos}</span>`;
      if (pos === 1) posTag = `<span class="posicao-tag pos-1">🥇 1</span>`;
      if (pos === 2) posTag = `<span class="posicao-tag pos-2">🥈 2</span>`;
      if (pos === 3) posTag = `<span class="posicao-tag pos-3">🥉 3</span>`;

      const dataFormatada = item.data_hora
        ? new Date(item.data_hora).toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
          })
        : "—";

      return `
      <tr>
        <td>${posTag}</td>
        <td><strong>${escaparHtml(item.nome)}</strong></td>
        <td><span class="serie-aluno">${escaparHtml(item.serie)}</span></td>
        <td><strong>${item.pontuacao} pts</strong></td>
        <td>${item.acertos} / 10</td>
        <td><small style="color: var(--texto-fraco);">${dataFormatada}</small></td>
      </tr>
    `;
    })
    .join("");

  corpoTabela.innerHTML = html;
}

/**
 * Filtra localmente pelo nome do aluno
 */
function filtrarETabelar(termoBusca) {
  const termo = termoBusca.toLowerCase().trim();
  if (!termo) {
    renderizarTabela(dadosRankingCompletos);
    return;
  }

  const filtrados = dadosRankingCompletos.filter((item) =>
    item.nome.toLowerCase().includes(termo)
  );

  renderizarTabela(filtrados);
}

/**
 * Cadastra uma nova pontuação
 */
async function cadastrarResultado(form) {
  const msgEl = document.getElementById("mensagem-form");
  const btnSalvar = document.getElementById("btn-salvar");

  const nome = form.nome.value.trim();
  const serie = form.serie.value;
  const pontuacao = parseInt(form.pontuacao.value, 10);
  const acertos = parseInt(form.acertos.value, 10);

  if (!nome) return;

  btnSalvar.disabled = true;
  btnSalvar.textContent = "Salvando...";

  const payload = { nome, serie, pontuacao, acertos, tempoSegundos: 0 };

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
      msgEl.textContent = "✨ Pontuação cadastrada com sucesso!";
      form.reset();
      form.pontuacao.value = "100";
      form.acertos.value = "10";
      const serieFiltro = document.getElementById("filtro-serie")?.value ?? "Todas";
      await carregarRanking(serieFiltro);
    } else {
      throw new Error(`HTTP ${resposta.status}`);
    }
  } catch (erro) {
    console.error("Erro ao salvar resultado:", erro);
    msgEl.className = "mensagem-status erro";
    msgEl.textContent = "❌ Falha ao salvar pontuação. Tente novamente.";
  } finally {
    btnSalvar.disabled = false;
    btnSalvar.textContent = "⭐ Cadastrar Pontuação";
    setTimeout(() => {
      if (msgEl) msgEl.textContent = "";
    }, 4000);
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
