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
| 39 | Gesto "L" como modificador: selecionar lua individual | 🔄 | 🔄 | catálogo pronto; falta o gesto |
| 40 | BUG: órbita da Lua colidia com Vênus e Marte | ✅ | ✅ | corrigido |

---

## O que falta, em detalhe

### 40 · BUG — a órbita da Lua invade Vênus e Marte

Confirmado com número. A órbita da Lua tem raio fixo de **28 px**, mas na escala
logarítmica os planetas vizinhos da Terra estão mais perto do que isso:

```
Mercúrio  órbita=  95.0
Vênus     órbita= 141.7   distância até a anterior=  46.7
Terra     órbita= 165.9   distância até Vênus     =  24.2  <-- menor que 28
Marte     órbita= 197.3   distância até a Terra   =  31.5  <-- quase 28
```

Com a Lua a 28 px do centro da Terra, ela varre de **137,9 a 193,9 px** — e
Vênus está em 141,7 px, bem no meio dessa faixa. Marte, em 197,3, fica a 3,4 px
da borda.

**Por que não basta diminuir o raio.** A folga real entre os discos de Vênus e
Terra é de apenas ~4,4 px (24,2 menos os dois raios). Para a Lua caber ali sem
encostar, a órbita dela teria que ter raio ≈ 7 px — **menor que o raio desenhado
da própria Terra (10 px)**, ou seja, a Lua ficaria dentro do planeta. Não existe
valor que resolva na visão geral.

**Correção aplicada:** a Lua passou a seguir a mesma regra que as luas menores
já seguiam — só desenhar acima de `ZOOM_MINIMO_PARA_LUAS`. Na visão geral a Lua e
sua órbita somem (onde de qualquer forma seriam 4 px indistinguíveis); com a
câmera aproximada na Terra, Vênus está fora do enquadramento e não há
sobreposição possível. Isso também deixa o comportamento da Lua coerente com o
das outras 21, em vez de ser um caso especial.

Netuno↔Urano (33,5 px) e Saturno↔Júpiter (45,6 px) têm folga parecida — as luas
**menores** desses planetas nunca colidiram justamente porque já respeitavam o
zoom mínimo. A Lua era o único caso especial, e era o que quebrava.

Uma exceção necessária: **quando o próprio satélite é o alvo em foco, ele
sempre aparece**, mesmo abaixo do limiar. Sem isso, selecionar a Lua com zoom
baixo (pelo gesto 9 durante uma transição de câmera) faria o alvo sumir.

Verificado: na visão geral (zoom 0,90) a Lua e sua órbita não são desenhadas; ao
focá-la (zoom 6,00) ela aparece; e com a Lua como alvo em zoom baixo, ela
continua visível.


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

**Catálogo (feito).** Ampliado de 11 para 22 luas, com um critério que evita
inventar corpo: as maiores/mais notáveis de cada planeta, ordenadas pela
distância REAL ao corpo-pai.

| Planeta | No catálogo | Luas reais |
|---|---|---|
| Marte | 2 — Fobos, Deimos | **2** (não existe terceira) |
| Júpiter | 5 — Amalteia, Io, Europa, Ganimedes, Calisto | 95 |
| Saturno | 5 — Encélado, Dione, Reia, Titã, Jápeto | 146 |
| Urano | 5 — Miranda, Ariel, Umbriel, Titânia, Oberon | 28 |
| Netuno | 5 — Galateia, Larissa, Proteu, Tritão, Nereida | 16 |

Marte é o caso que a regra "5 por planeta" não alcança, e está certo assim. O
teto de 5 vem do gesto (uma mão conta até 5), não da astronomia — por isso o
HUD **precisa** numerar a partir de `luas_do_planeta()`: em Marte a lista tem
dois itens, e um dicionário fixo prometeria um terceiro.

#### Três decisões pendentes (perguntas do próprio pedido)

| # | Pergunta | Recomendação |
|---|---|---|
| 1 | Ao sair do modo, mantém a lua em foco ou volta ao planeta? | **Manter**, como proposto. Sair do modo é largar o modificador, não desfazer a escolha — e um corte de câmera ao soltar a mão pareceria bug. |
| 2 | `0` mostra todas as luas ou sai do modo? | **Todas.** Sair já tem dois caminhos (soltar o L, gesto 10); gastar o `0` nisso perde a única forma de voltar à visão do sistema de luas sem largar o modificador. |
| 3 | O "L" deve servir de "voltar" fora do modo luas? | **Não.** Um gesto com dois significados dependendo do contexto é o tipo de coisa que o usuário erra — e "voltar" já é o gesto 10 e a tecla `V`. |

**Decisões tomadas:** as três recomendações acima foram aceitas, com três
acréscimos que mudam o plano de execução:

**a) Estado separado — `planeta_selecionado` e `lua_selecionada` como campos
distintos.** "Manter a lua em foco ao sair do modo" só funciona bem assim: com
um campo único não existe caminho de volta ao planeta sem passar pela visão
geral. Sair do modo mantém a lua; um número sem o "L" volta ao planeta.

**b) O catálogo entra em commit separado.** Ampliar `LUAS_MENORES` para 5 luas
por planeta é entrada de dados — raio orbital, período e escala de cada corpo
novo. Não tem relação com a máquina de estados do gesto, e juntar as duas coisas
num commit só significa que uma falha não diz se foi o gesto ou o dado.

**c) O release vem ANTES, não depois.** O gesto "L" é feature grande, de vários
commits; publicar só no fim deixaria o executável defasado esse tempo todo. Uma
v1.3.1 no ar antes de começar também dá **baseline** para comparar se o gesto
introduzir regressão.

**d) A lista do HUD vem do catálogo, não de um dicionário fixo.** A
especificação lista 5 luas para Saturno e Urano, mas o catálogo real tem 11 no
total. Se o HUD numerar a partir de um dicionário próprio, ele promete uma lua
que o renderizador não desenha. A numeração precisa sair de
`luas_do_planeta(nome)` — a mesma fonte que a cena usa.

**Ordem de execução:**

1. ✅ publicar a v1.3.1 (baseline, com a pinça dupla)
2. ✅ catálogo ampliado de 11 para 22 luas — commit isolado (`5da8fbf`)
3. ⬜ máquina de estados do "L" + testes com landmarks sintéticos
4. ⬜ HUD do modo luas, numerando a partir do catálogo

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
