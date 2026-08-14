import { URL_SERVIDOR_RENDER } from "./config.js";

const ENDPOINT_RANKING = "/api/ranking";
let dadosRankingCompletos = [];

document.addEventListener("DOMContentLoaded", () => {
  carregarRanking();

  const filtroSerie = document.getElementById("filtro-serie");
  const buscaNome = document.getElementById("busca-nome");
  const formRanking = document.getElementById("form-ranking");
  const btnLimpar = document.getElementById("btn-limpar-ranking");

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
async function carregarRanking(serie = "Todas") {
  const corpoTabela = document.getElementById("tabela-corpo");
  if (corpoTabela) {
    corpoTabela.innerHTML = `<tr><td colspan="7" class="carregando"><i class="bi bi-arrow-clockwise girando"></i> Carregando classificação...</td></tr>`;
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
    corpoTabela.innerHTML = `<tr><td colspan="7" class="carregando"><i class="bi bi-info-circle"></i> Nenhum resultado registrado ainda.</td></tr>`;
    return;
  }

  const html = lista
    .map((item, index) => {
      const pos = index + 1;
      let posTag = `<span class="posicao-tag">${pos}</span>`;
      if (pos === 1) posTag = `<span class="posicao-tag pos-1"><i class="bi bi-trophy-fill"></i> 1</span>`;
      if (pos === 2) posTag = `<span class="posicao-tag pos-2"><i class="bi bi-award-fill"></i> 2</span>`;
      if (pos === 3) posTag = `<span class="posicao-tag pos-3"><i class="bi bi-award"></i> 3</span>`;

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
        <td><span class="sala-aluno">${escaparHtml(item.sala ?? "—")}</span></td>
        <td><strong>${item.pontuacao} pts</strong></td>
        <td>${item.acertos} / 10</td>
        <td><small style="color: #a1a1aa;">${dataFormatada}</small></td>
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

  // Associa manipuladores para os botões de excluir item individual
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
  btnSalvar.innerHTML = `<i class="bi bi-arrow-clockwise girando"></i> Salvando...`;

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
      msgEl.innerHTML = `<i class="bi bi-check-circle-fill"></i> Pontuação cadastrada com sucesso!`;
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
      const serieFiltro = document.getElementById("filtro-serie")?.value ?? "Todas";
      await carregarRanking(serieFiltro);
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
