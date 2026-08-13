# Tarefas — registro de implementações

Histórico do que já está **pronto e verificado**. O que ainda não foi feito vive
no [ROADMAP.md](ROADMAP.md).

> **Regra do projeto:** toda alteração feita no aplicativo desktop precisa ser
> feita também na versão web, e vice-versa. Isso não é só convenção — o
> [verificar_paridade.py](verificar_paridade.py) falha se os dois lados
> divergirem, e o [publicar.py](publicar.py) roda essa checagem antes de gerar o
> pacote de download.

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
