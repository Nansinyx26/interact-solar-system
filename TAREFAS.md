# Tarefas — registro de implementações

Histórico do que já está **pronto e verificado**. O que ainda não foi feito vive
no [ROADMAP.md](ROADMAP.md).

> **Regra do projeto:** toda alteração feita no aplicativo desktop precisa ser
> feita também na versão web, e vice-versa. Isso não é só convenção — o
> [verificar_paridade.py](verificar_paridade.py) falha se os dois lados
> divergirem, e o [publicar.py](publicar.py) roda essa checagem antes de gerar o
> pacote de download.

---

## v1.2.0 — zoom por pinça e narração por voz

| # | Entrega | Onde | Status |
|---|---|---|---|
| 1 | Zoom controlado por pinça na frente da câmera | `gestos/pinca.py`, `web/gestos/pinca.js` | ✅ |
| 2 | Narração do corpo focado com a voz **Brian** (ElevenLabs) | `ui/voz_elevenlabs.py`, `web/api/voz.js` | ✅ |
| 3 | Voz local de reserva (pyttsx3 / Web Speech) para funcionar offline | `ui/narrador.py`, `web/ui/narrador.js` | ✅ |
| 4 | Cache de áudio em disco e na CDN | `ui/voz_elevenlabs.py`, `web/api/voz.js` | ✅ |
| 5 | Controles: botão 🔊 no site, tecla `N` nos dois | `web/index.html`, `main.py` | ✅ |
| 6 | Aviso "MODO ZOOM" enquanto a pinça comanda | `ui/hud.py`, `web/ui/hud.js` | ✅ |
| 7 | Narração lê a **ficha inteira** do corpo | `ui/narrador.py`, `web/ui/narrador.js` | ✅ |
| 8 | Ficha movida para a coluna esquerda (saía atrás da webcam) | `ui/ficha_planeta.py`, `web/estilo.css` | ✅ |
| 9 | Log `[narrador]` dizendo qual voz está ativa | `ui/narrador.py` | ✅ |
| 10 | Interpretador do editor apontado para o `.venv` | `pyrefly.toml`, `.vscode/settings.json` | ✅ |

> **O executável precisa ser reconstruído a cada mudança.** Ele é uma fotografia
> do código: rodar `main.py` mostra o estado atual, mas o `SistemaSolar.exe`
> continua com o que havia no momento do build. Um executável de antes destas
> entregas não tem narração, nem pinça, nem a ficha reposicionada — mesmo com o
> código-fonte já atualizado ao lado dele. Use `publicar.py --com-exe`.

### A ficha lida em voz alta

A narração diz a ficha em orações completas, não como uma planilha:

> "A Terra é um planeta rochoso. Tem 12.756 quilômetros de diâmetro. Fica a 1,00
> unidades astronômicas do Sol, ou seja, 149.600.000 quilômetros. Uma volta
> completa leva 1,0 anos terrestres. Gira em torno de si mesmo em 23,9 horas.
> Tem uma lua conhecida. A temperatura média é de 15 graus Celsius. Único mundo
> conhecido com água líquida estável na superfície."

Casos que o texto trata sozinho: o Sol não tem órbita nem luas, a Lua mede
distância até a Terra (e não até o Sol), Vênus e Urano giram "no sentido
contrário ao dos demais", e "Tem uma lua conhecida" no singular.

Um detalhe que o verificador de paridade pegou: o Python arredonda com
half-even e o `Intl.NumberFormat` do JavaScript com half-up. A rotação de
Mercúrio (58,65 dias) saía como 58,6 no desktop e 58,7 na web — o formatador do
Python passou a usar `Decimal` com `ROUND_HALF_UP` para os dois falarem igual.

### Zoom por pinça — o que mudou em relação ao plano

O desenho original mandava aplicar `razao_atual / razao_inicial` a cada frame.
Isso faria o zoom **crescer exponencialmente**, porque `aplicar_zoom` multiplica
o zoom corrente. O controlador usa o fator **relativo ao frame anterior**, cujo
produto acumulado dá exatamente a mesma proporção total, sem explodir.

Três defesas que a prática exigiu:

- **Histerese** (entra abaixo de 0,38 palma, só sai acima de 0,55). Com limiar
  único a pinça pisca na fronteira e o zoom liga e desliga sozinho.
- **Indicador estendido é obrigatório** para valer como pinça. Numa mão fechada
  as pontas do polegar e do indicador também ficam próximas — sem essa checagem,
  mostrar 0 dedos (o Sol) seria lido como pinça.
- **Teto de 1,12× por leitura.** Quando o rastreio perde a mão por um instante a
  razão dá um pulo, e sem o limite a cena saltava.

O risco previsto no roadmap se confirmou e está coberto: durante o zoom a pose
seria contada como 2 dedos (Vênus). O estabilizador fica suspenso enquanto a
pinça está ativa **e** por 0,6 s depois dela, o que cobre as poses intermediárias
da abertura da mão. Verificado em teste: `NÃO trocou para Vênus durante o zoom`.

### Narração — a decisão de idioma foi medida, não adivinhada

A voz Brian da ElevenLabs é americana, e o modelo identifica o idioma **pelo
texto**. Sintetizando e transcrevendo de volta com a API de speech-to-text da
própria ElevenLabs, o diagnóstico ficou claro:

| Frase | Idioma reconhecido |
|---|---|
| `Sol. Estrela` | espanhol |
| `Terra. Planeta rochoso` | inglês |
| `Marte. Planeta rochoso` | inglês |
| `Lua. Satélite natural` | português |

O `language_code: "pt"` **não resolve** — testado nos quatro modelos
(`multilingual_v2`, `turbo_v2_5`, `flash_v2_5`, com e sem o parâmetro), o
resultado não mudou. O que resolve é a frase ter marcadores gramaticais do
português. Trocando a lista de termos por uma oração completa —
**`"{Nome} é um/uma {tipo}."`** — os 10 corpos passaram a ser reconhecidos como
português:

```
ok [por] Sol       'O Sol é uma estrela.'
ok [por] Marte     'Marte é um planeta rochoso.'
ok [por] Júpiter   'Júpiter é um gigante gasoso.'
ok [por] Lua       'A Lua é um satélite natural.'
```

### Segurança da chave da API

A chave **nunca chega ao navegador**. O site não fala com a ElevenLabs: ele
chama `/api/voz`, uma função serverless que guarda a chave em variável de
ambiente do servidor. No desktop a chave sai do `.env` (que está no
`.gitignore`) e não é embutida no executável.

Cada frase sintetizada custa créditos, então há cache dos dois lados: em disco
no desktop (`cache_voz/`, ~314 KB para os 10 corpos) e na CDN do Vercel pela
resposta da função. Fora isso, esta é a **única** parte do projeto que usa rede
em execução — e a voz local de reserva mantém o aplicativo completo offline.

---

## v1.1.0 — paridade desktop ↔ web

| # | Entrega | Onde | Status |
|---|---|---|---|
| 1 | Versão web completa em Canvas 2D + MediaPipe Tasks (WASM) | `web/` | ✅ |
| 2 | Deploy estático no Vercel (`vercel.json`, headers, `cleanUrls`) | `web/vercel.json` | ✅ |
| 3 | Botão de download da versão desktop no site | `web/index.html` | ✅ |
| 4 | ZIP do desktop regerado a cada publicação, **com o executável dentro** | `empacotar_web.py`, `publicar.py` | ✅ |
| 4b | Bundle do executável enxugado de 340 MB para 265 MB | `build_exe.py` | ✅ |
| 5 | Versão única (`VERSAO`) compartilhada e exibida nos dois | `config.py`, `web/config.js` | ✅ |
| 6 | Verificador automático de paridade | `verificar_paridade.py` | ✅ |
| 7 | Responsividade de 320 px a 4K, retrato e paisagem | `web/estilo.css` | ✅ |
| 8 | Pastilha de estado da câmera na web | `web/ui/hud.js`, `web/estilo.css` | ✅ |
| 9 | Lua como corpo selecionável (gesto 9 / tecla `L`) | ambos | ✅ |
| 10 | Marca d'água do autor, clicável | `ui/marca_dagua.py`, `web/estilo.css` | ✅ |

### O que o verificador de paridade cobre

```
.venv\Scripts\python.exe verificar_paridade.py
```

- **Versão** — `VERSAO` precisa ser idêntica nos dois lados.
- **Módulos espelhados** — cada arquivo do desktop tem seu par na web.
- **Constantes compartilhadas** — 70 constantes comparadas (escalas, limiares de
  gesto, tempos de animação). Opacidades são comparadas com conversão, porque o
  pygame usa 0–255 e o Canvas usa 0–1 — mesma cor, unidade diferente.
- **Cores da interface** — as 7 cores do HUD existem como constante no
  `config.py` e como variável CSS no `:root`; o script compara `(6, 7, 16)` com
  `#060710`.
- **Os 10 corpos** — todos os campos de cada corpo, um a um.

Constantes legitimamente exclusivas de uma plataforma (tamanho de janela do
pygame, URLs do WASM, geometria da marca d'água desenhada em Python) estão
listadas como exceções no próprio script, com o motivo.

### Como publicar mantendo tudo em sincronia

```powershell
.venv\Scripts\python.exe publicar.py            # paridade + ZIP de download
.venv\Scripts\python.exe publicar.py --com-exe  # e regenera o executável
```

O passo 3 abre o ZIP recém-criado e confere se o `config.py` **empacotado**
declara a mesma versão que o site vai servir — é o que impede o site anunciar
v1.1.0 e entregar um download da v1.0.0.

### O pacote de download

O ZIP leva o executável pronto **e** o código-fonte na mesma pasta: quem baixa
extrai e dá dois cliques, sem instalar Python.

| Conteúdo | Tamanho | Serve no Vercel Hobby? |
|---|---:|---|
| Só código-fonte (`--sem-exe`) | 0,4 MB | sim |
| Código-fonte + executável (padrão) | 107 MB | **não** — limite é 100 MB |

O limite de arquivo estático do Vercel é 100 MB no Hobby e 1 GB no Pro. Com o
executável, o pacote fica 7 MB acima do teto gratuito. Alternativas (plano Pro,
GitHub Releases via `URL_DOWNLOAD_EXECUTAVEL`, ou `--sem-exe`) estão no
[README da web](web/README.md#️-o-pacote-com-o-executável-passa-de-100-mb). O
empacotador avisa no terminal sempre que passa do limite.

**Enxugamento do bundle (340 MB → 265 MB).** O `--collect-all mediapipe` traz o
pacote inteiro e o PyInstaller copia dependências por precaução. Foram removidos,
com o motivo registrado no `build_exe.py`:

| Removido | Peso | Por que é seguro |
|---|---:|---|
| `opencv_videoio_ffmpeg*.dll` | 52 MB | só abrimos webcam, nunca arquivos de vídeo |
| Modelos de pose, face, íris, holistic… | 17 MB | `mp.solutions.hands` usa só `hand_landmark` e `palm_detection` |
| Tcl/Tk (`_tcl_data`, `_tk_data`) | 4 MB | matplotlib só precisa do backend Agg aqui |
| `PIL/_avif.pyd` | 7 MB | nenhuma imagem é carregada de disco |

Verificado depois do corte: o executável extraído do ZIP abre, cria o
`HandLandmarker` e registra `[webcam] aberta no índice 0 via DirectShow`.

---

## v1.0.0 — aplicativo desktop

| # | Entrega | Status |
|---|---|---|
| 1 | Cena do Sistema Solar: 9 corpos, órbitas animadas, escalas comprimidas documentadas | ✅ |
| 2 | Texturas 100% procedurais, rotação própria real, anéis, halo solar, parallax | ✅ |
| 3 | Detecção de mãos em thread separada, 30+ FPS | ✅ |
| 4 | Contagem de dedos robusta a rotação (referencial da palma) | ✅ |
| 5 | Estabilização: buffer + maioria de 70% + cooldown de 0,8 s | ✅ |
| 6 | Foco com easing, esmaecimento dos demais corpos, ficha astronômica | ✅ |
| 7 | Fallback completo por teclado e mouse; janela redimensionável | ✅ |
| 8 | Gesto 10 (duas mãos abertas) e tecla `V` para visão geral | ✅ |
| 9 | Executável Windows (`SistemaSolar.exe`) via PyInstaller | ✅ |
| 10 | Diagnóstico `[webcam]` no console e `--camera N` | ✅ |

### Correções relevantes

| Sintoma | Causa raiz | Correção |
|---|---|---|
| Gesto 6 nunca era reconhecido | A checagem de enquadramento descartava a leitura se **um único** dos 21 landmarks saísse com 2% de tolerância — com duas mãos no quadro isso acontecia sempre | Tolerância para 6% e descarte só acima de 3 pontos fora; confiança de detecção 0,6 → 0,5 |
| Webcam demorava ~2,3 s para abrir | Três `cap.set()` renegociando um formato que a câmera **já** usava (0,5 s cada) | Só configura o que diverge → 0,8 s |
| Executável subia sem gestos | `matplotlib` excluído do build, mas `mp.solutions.drawing_utils` o importa | Removido da lista de exclusões (documentado no `build_exe.py`) |
| Zoom estourava o limite ao redimensionar | `ZOOM_MAX` fixo enquanto o zoom era multiplicado pela proporção da janela | Limites de zoom passaram a escalar junto com a altura da janela |
