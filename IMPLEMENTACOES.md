# Implementações — o que foi pedido, o que está pronto, o que falta

Lista viva de **todos** os pedidos feitos ao longo do projeto. Atualizada a cada
entrega. O detalhe técnico de cada item concluído está em [TAREFAS.md](TAREFAS.md);
o backlog antigo, em [ROADMAP.md](ROADMAP.md).

Legenda: ✅ pronto e verificado · 🔄 em andamento · ⬜ não começado

---

## Situação atual

| # | Pedido | Desktop | Web | Situação |
|---|---|:---:|:---:|---|
| 1 | Sistema Solar animado com 8 planetas + Sol | ✅ | ✅ | pronto |
| 2 | Seleção por número de dedos (0–8) | ✅ | ✅ | pronto |
| 3 | Estabilização (buffer, maioria, cooldown) | ✅ | ✅ | pronto |
| 4 | Ficha astronômica do corpo focado | ✅ | ✅ | pronto |
| 5 | Fallback completo por teclado | ✅ | ✅ | pronto |
| 6 | Janela redimensionável / minimizar / arrastar | ✅ | — | pronto |
| 7 | Preview da webcam no canto inferior direito | ✅ | ✅ | pronto |
| 8 | Duas mãos abertas (10) volta à visão geral | ✅ | ✅ | pronto |
| 9 | Tecla `V` para visão geral | ✅ | ✅ | pronto |
| 10 | Executável Windows | ✅ | — | pronto |
| 11 | Gesto 6 não era reconhecido | ✅ | ✅ | corrigido |
| 12 | Versão web publicável no Vercel | — | ✅ | pronto |
| 13 | Download da versão desktop pelo site | — | ✅ | pronto |
| 14 | Executável **dentro** do ZIP de download | ✅ | ✅ | pronto |
| 15 | Paridade automática desktop ↔ web | ✅ | ✅ | pronto |
| 16 | Responsividade (320 px → 4K, retrato/paisagem) | — | ✅ | pronto |
| 17 | Publicação por GitHub Releases | ✅ | ✅ | pronto |
| 18 | Lua da Terra (gesto 9 / tecla `L`) | ✅ | ✅ | pronto |
| 19 | Ficha à esquerda (saía atrás da webcam) | ✅ | ✅ | pronto |
| 20 | Zoom por gesto de pinça na câmera | ✅ | ✅ | pronto |
| 21 | Narração por voz (ElevenLabs "Brian") | ✅ | ✅ | pronto |
| 22 | Narração lê a ficha inteira | ✅ | ✅ | pronto |
| 23 | Narração toda em português do Brasil | ✅ | ✅ | corrigido |
| 24 | Leitura dos números na narração | ✅ | ✅ | corrigido |
| 25 | Imports sublinhados em vermelho no editor | ✅ | — | corrigido |
| 26 | Voz da ElevenLabs não tocava no site | — | ✅ | corrigido |
| 27 | Página de atividades com 10 questões | ✅ | ✅ | verificado |
| 28 | Identificação (nome, série, sala) antes do quiz | ✅ | ✅ | verificado |
| 29 | Salvar nota no MongoDB | ✅ | ✅ | verificado |
| 30 | Ranking com as maiores notas | ✅ | ✅ | verificado |
| 31 | Luas dos outros planetas (11 luas) | ✅ | ✅ | pronto |
| 32 | Comando para ver as luas (tecla `M`) | ✅ | ✅ | pronto |
| 33 | Cinturão de asteroides | ✅ | ✅ | pronto |
| 34 | Campo **sala** no quiz e no ranking | — | ✅ | pronto |
| 35 | Erros de lint em `nucleo/renderizador.py` | ✅ | — | corrigido |
| 36 | Gesto de mão para as luas (pinça dupla) | ✅ | ✅ | pronto |
| 37 | Aviso `has-symbols` no npm | — | ✅ | investigado: sem ação |
| 38 | Rebuild + republicar (exe/ZIP/site na mesma versão) | ✅ | ✅ | v1.3.0 no ar |
| 39 | **Gesto "L" como modificador: selecionar lua individual** | ⬜ | ⬜ | **especificado, aguarda decisão** |

---

## O que falta, em detalhe

### 39 · Gesto "L" como modificador de modo — especificado, aguarda decisão

**O que é.** Uma mão forma o "L" (polegar + indicador estendidos, ~90° entre
eles) e vira um *modificador*: enquanto ele está ativo, o número mostrado pela
**outra mão** deixa de significar planeta e passa a significar **índice da lua**
do corpo em foco. É a saída para o problema que já vinha de antes — com 0 a 10
todos ocupados, não havia como selecionar uma lua específica.

**Relação com o que já existe.** Não substitui nada: a pinça dupla (item 36)
continua sendo o liga/desliga rápido das luas, e a tecla `M` também. O "L"
acrescenta a **seleção individual**, que nenhum dos dois faz.

**Pontos técnicos que a especificação acerta e valem destaque:**

- A mão do "L" **não pode entrar na contagem numérica** — o gesto consome dois
  dedos. A ordem de parsing precisa classificar a forma antes de contar.
- Distinguir "L" de "2" (indicador + médio) exige checar **quais** dedos estão
  dobrados, não só quantos. Merece teste dedicado com landmarks sintéticos.
- Histerese **assimétrica** (6 frames para entrar, 8 para sair): sair sem querer
  é pior que entrar devagar. Mesmo princípio da histerese da pinça.
- Duas mãos em "L" = estado inválido, ignora o frame.

**Estrutura proposta** (`gestos/formatos_mao.py` + `gestos/estado_gesto.py`,
sem conhecer o pygame) casa com a separação que o projeto já tem entre
`contador.py` (mede), `pinca.py` (decide) e o loop (aplica).

**Ajuste necessário nos dados:** a especificação lista até 5 luas por planeta
(Mimas, Reia, Jápeto, Ariel, Umbriel, Miranda, Nereida, Proteu), enquanto o
catálogo atual tem 11 no total. Seria preciso ampliar `LUAS_MENORES` nos dois
lados — e o limite de 5 existe porque **uma mão conta até 5**.

#### Três decisões pendentes (perguntas do próprio pedido)

| # | Pergunta | Recomendação |
|---|---|---|
| 1 | Ao sair do modo, mantém a lua em foco ou volta ao planeta? | **Manter**, como proposto. Sair do modo é largar o modificador, não desfazer a escolha — e um corte de câmera ao soltar a mão pareceria bug. |
| 2 | `0` mostra todas as luas ou sai do modo? | **Todas.** Sair já tem dois caminhos (soltar o L, gesto 10); gastar o `0` nisso perde a única forma de voltar à visão do sistema de luas sem largar o modificador. |
| 3 | O "L" deve servir de "voltar" fora do modo luas? | **Não.** Um gesto com dois significados dependendo do contexto é o tipo de coisa que o usuário erra — e "voltar" já é o gesto 10 e a tecla `V`. |

**Estado:** especificação registrada, nada implementado. Aguarda as respostas
acima para começar.

### 36 · Gesto de mão para as luas — pronto

As 11 luas ligam/desligam pela tecla `M` **ou pela pinça com as duas mãos**.

**Qual gesto sobrou?** O mapa ficou assim:

| Gesto | Uso |
|:---:|---|
| 0–8 | Sol e os 8 planetas |
| 9 | Lua |
| 10 | comando: voltar à visão geral |
| pinça (1 mão) | comando: zoom |
| **pinça (2 mãos)** | **comando: mostrar/esconder as luas** |

Com duas mãos o máximo é 10 e **todos os números estavam ocupados** — por isso as
luas não ganharam contagem própria. A pinça com as DUAS mãos era o único estado
que nada usava, já que a pinça simples só é lida na mão de maior confiança.

Três detalhes que a implementação exigiu:

- **O detector passou a medir a pinça em todas as mãos** (`razoes_pinca`), não
  só na dominante. Sem isso não há como saber que as duas estão fechadas.
- **O comando tem prioridade sobre o zoom.** Se o zoom fosse avaliado primeiro,
  a mão dominante começaria a aproximar a cena antes de o gesto ser reconhecido.
- **É evento, não estado.** Dispara só na transição para pinça dupla; mantendo
  as mãos fechadas nada mais acontece. Sem isso as luas piscariam a 15 Hz.

Verificado nos dois lados com o mesmo roteiro de leituras — Python e JavaScript
disparam exatamente nos mesmos momentos: `[F, F, F, V, F, F, F, V]`.

### 37 · Aviso `has-symbols` no npm — investigado, sem ação necessária

Não é dependência do projeto: entra cinco níveis abaixo, pelo `express`.

```
interact-solar-system@1.2.0
└─ express@4.22.2
   └─ qs@6.15.3
      └─ side-channel@1.1.1
         └─ side-channel-map@1.0.1
            └─ get-intrinsic@1.3.0
               └─ has-symbols@1.1.0
```

`npm audit --omit=dev` reporta **0 vulnerabilidades**. O aviso é de
**depreciação**: o autor marcou o pacote como obsoleto porque `Symbol` já é
nativo em qualquer runtime que o projeto suporta. Nada a corrigir do nosso lado
— sairá sozinho quando a cadeia do Express atualizar. Forçar um `override` aqui
traria risco sem benefício.

### 38 · Rebuild e republicação — OBRIGATÓRIO a cada entrega

**Não esquecer:** o executável, o ZIP de download e o site precisam estar
sempre na MESMA versão. O `.exe` é uma fotografia do código — enquanto não for
reconstruído, ele continua sem as luas e sem o cinturão, mesmo com o
código-fonte já atualizado ao lado dele.

Sequência obrigatória depois de qualquer mudança:

```powershell
# 1. sobe VERSAO em config.py E em web/config.js (o verificador exige iguais)
.venv\Scripts\python.exe verificar_paridade.py    # constantes, cores, corpos
.venv\Scripts\python.exe build_exe.py             # regenera o .exe
.venv\Scripts\python.exe publicar.py              # regenera o ZIP + confere versão
.venv\Scripts\python.exe publicar_release.py      # publica no GitHub Releases
git add -A && git commit && git push                # site atualiza no Vercel
```

O `publicar.py` abre o ZIP recém-gerado e lê o `config.py` **empacotado**: é o
passo que impede o site anunciar uma versão e entregar outra no download.

### 27 a 30 · Atividades, MongoDB e ranking — verificado

- **10 questões**: confirmado em `web/atividades.js`.
- **Identificação antes de começar**: nome completo, série e **sala** (este
  faltava e foi adicionado — série e sala são campos separados porque a
  classificação agrupa por sala).
- **MongoDB**: `POST /api/ranking` grava nome, série, sala, pontuação, acertos e
  tempo. Testado em produção: responde 200.
- **Classificação**: `GET /api/ranking` ordena por pontuação (desc) e desempata
  pelo tempo; aceita filtro por série e por sala.

---

## Correções registradas

| Sintoma | Causa raiz | Correção |
|---|---|---|
| Gesto 6 nunca reconhecido | descarte da leitura com 1 landmark fora e 2% de tolerância — com duas mãos isso era sempre | tolerância 6% e descarte só acima de 3 pontos fora |
| Webcam demorava 2,3 s | três `cap.set()` renegociando formato que a câmera já usava | só configura o que diverge → 0,8 s |
| Executável sem gestos | `matplotlib` excluído do build, mas `drawing_utils` o importa | removido da lista de exclusões |
| Ficha cortada atrás da webcam | ficha e preview no mesmo canto, ficha sem `z-index` | ficha foi para a coluna esquerda, altura medida por `ResizeObserver` |
| Narração em espanhol/inglês | nomes latinos soltos são ambíguos entre línguas | frases viraram orações completas com verbo e artigo |
| "dois luas", "1,00 unidades", "243,0 dias" | número formatado sem concordância nem corte de decimal | funções de quantidade, concordância e escala (milhões/bilhões) |
| Mercúrio: 58,6 no desktop e 58,7 na web | Python arredonda half-even, JavaScript half-up | `Decimal` com `ROUND_HALF_UP` no Python |
| Voz do Brian não tocava no site | `new Audio()` fora de gesto do usuário é bloqueado pelo autoplay; o `play()` rejeitava e caía na voz do navegador | um único elemento de áudio, destravado no primeiro clique/toque/tecla |
| Executável "sem" as novidades | o `.exe` é uma fotografia do código e não tinha sido reconstruído | rebuild; `publicar.py --com-exe` |
