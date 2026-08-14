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
| 36 | **Gesto de mão para as luas (pinça dupla)** | ⬜ | ⬜ | **a fazer** |
| 37 | Aviso `has-symbols` no npm | — | ✅ | investigado: sem ação |
| 38 | **Rebuild + republicar com as luas e o cinturão** | ⬜ | ⬜ | **a fazer** |

---

## O que falta, em detalhe

### 35 · Gesto de mão para as luas — o que falta

As 11 luas já existem e ligam/desligam pela tecla `M`. Falta o **gesto**.

**Qual gesto sobrou?** O mapa atual está assim:

| Gesto | Uso |
|:---:|---|
| 0–8 | Sol e os 8 planetas |
| 9 | Lua |
| 10 | comando: voltar à visão geral |
| pinça | comando: zoom |

Com duas mãos o máximo é 10, e **todos os valores estão ocupados**. Por isso as
luas não ganharam número: elas entram e saem pela tecla `M`.

O único gesto ainda livre é a **pinça com as DUAS mãos ao mesmo tempo** — hoje a
pinça só é lida na mão de maior confiança, então duas pinças simultâneas são um
estado que nada usa. Implementar exige medir a pinça em ambas as mãos no
detector e dar prioridade ao comando sobre o zoom (senão a mão dominante
começaria a dar zoom antes de o comando ser reconhecido).

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
