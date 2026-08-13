# Versão web — Sistema Solar Interativo por Gestos

Mesmo aplicativo do desktop, rodando no navegador: cena em Canvas 2D e detecção
de mãos pelo **MediaPipe Tasks Vision** compilado para WebAssembly. Funciona no
celular, no tablet e no computador, sem instalar nada.

O vídeo **nunca sai do aparelho** — a inferência roda no próprio navegador.

---

## Rodar localmente

Precisa de um servidor HTTP: módulos ES e WebAssembly não carregam por
`file://`, e a câmera exige contexto seguro (`localhost` conta como seguro).

```powershell
cd sistema_solar_gestos\web
python -m http.server 8000
```

Abra <http://localhost:8000/>.

---

## Publicar no Vercel

O site é estático — não há build, bundler nem dependência de npm.

### Pelo painel

1. Importe o repositório em <https://vercel.com/new>.
2. **Framework Preset:** `Other`.
3. **Root Directory:** `sistema_solar_gestos/web` ← passo mais importante.
4. Deixe *Build Command* e *Output Directory* vazios.
5. Deploy.

### Pela CLI

```powershell
npm i -g vercel
cd sistema_solar_gestos\web
vercel            # pré-visualização
vercel --prod     # produção
```

O [vercel.json](vercel.json) já define `Permissions-Policy: camera=(self)` — sem
esse cabeçalho o navegador bloqueia `getUserMedia` em alguns contextos — além do
`Content-Disposition` que faz o ZIP baixar em vez de abrir.

> **HTTPS é obrigatório** para a câmera. O Vercel serve HTTPS por padrão; se
> você hospedar em outro lugar, um domínio HTTP simplesmente não terá acesso à
> webcam.

---

## Antes de publicar

```powershell
cd sistema_solar_gestos
.venv\Scripts\python.exe publicar.py
```

Isso verifica a paridade com a versão desktop e **regenera o
`sistema-solar-gestos.zip`** servido pelo botão "Baixar versão desktop", para
que o download entregue exatamente a versão que está no ar. Detalhes em
[../TAREFAS.md](../TAREFAS.md).

### O que vai dentro do ZIP

```
sistema_solar_gestos/
├── SistemaSolar.exe            ← duplo clique e roda
├── _internal_sistema_solar/    ← bibliotecas do executável
├── COMO-USAR.txt               ← instruções em texto puro
├── main.py, config.py, …       ← código-fonte completo
└── dados/ nucleo/ gestos/ ui/
```

Quem baixa extrai e dá dois cliques — sem Python, sem pip, sem venv. O
código-fonte vai junto para quem quiser rodar ou modificar.

### ⚠️ O pacote com o executável passa de 100 MB

| Conteúdo | Tamanho |
|---|---|
| Só código-fonte (`--sem-exe`) | ~0,4 MB |
| Código-fonte **+ executável** | ~107 MB |

O limite de upload de arquivo estático do Vercel é **100 MB no plano Hobby** e
**1 GB no Pro** ([docs/limits](https://vercel.com/docs/limits)). Com o executável
dentro, o deploy no plano gratuito **falha**. Três saídas, em ordem de esforço:

1. **Plano Pro** — cabe folgado, nada muda no projeto.
2. **GitHub Releases** — publique o ZIP como release e cole a URL em
   `URL_DOWNLOAD_EXECUTAVEL` no [config.js](config.js). O botão passa a apontar
   para lá e o Vercel só serve a página. Releases aceitam até 2 GB por arquivo.
3. **`publicar.py` com `--sem-exe`** — o site oferece só o código-fonte
   (~0,4 MB), como antes.

O `empacotar_web.py` avisa no terminal sempre que o pacote ultrapassa o limite,
para a descoberta não acontecer no dia da publicação.

> O bundle já foi enxugado de 340 MB para 265 MB: o build remove os codecs de
> arquivo de vídeo do OpenCV (só abrimos webcam), o Tcl/Tk que vem junto do
> matplotlib e os modelos do MediaPipe de pose, face e íris, que este aplicativo
> nunca carrega. Os cortes estão documentados em [../build_exe.py](../build_exe.py).

---

## Estrutura

```
web/
├── index.html                 estrutura da página e painel de ajuda
├── estilo.css                 layout responsivo + marca d'água
├── config.js                  constantes (espelha o config.py)
├── app.js                     loop principal, entrada e orquestração
├── dados/planetas.js          catálogo dos 10 corpos
├── nucleo/
│   ├── orbita.js              posição orbital, escalas comprimidas
│   ├── camera.js              zoom/pan com easing
│   └── renderizador.js        cena em Canvas 2D, texturas procedurais
├── gestos/
│   ├── detector.js            getUserMedia + HandLandmarker (WASM)
│   ├── contador.js            landmarks → número de dedos
│   └── estabilizador.js       buffer, maioria, cooldown
├── ui/
│   ├── hud.js                 indicadores, legenda, avisos
│   └── ficha.js               card de dados do corpo focado
├── sistema-solar-gestos.zip   download da versão desktop (gerado)
└── vercel.json
```

A lógica é a mesma do desktop, portada arquivo a arquivo. Os módulos puros
(`orbita`, `camera`, `contador`, `estabilizador`) produzem exatamente os mesmos
números que a versão Python — isso é verificado por teste.

---

## Suporte a dispositivos

| Faixa | Layout |
|---|---|
| ≤ 360 px | só o essencial: números sem rótulo, título e pausa ocultos |
| ≤ 480 px | ficha em coluna única, FPS oculto, preview de 132 px |
| ≤ 900 px | ficha vira folha deslizante na base, botões de toque na barra inferior |
| paisagem (altura ≤ 560 px) | ficha volta a ser painel lateral; preview desce para a esquerda |
| ≥ 1600 px | tudo cresce: ficha de 390 px, anel de 92 px, preview de 320 px |

Alvos de toque têm no mínimo 44 px em telas com ponteiro grosso, e o layout
respeita `safe-area-inset` (notch e barra inferior do iPhone).

**Controles por toque:** toque direto no planeta para focar, arraste para mover a
cena, pinça de dois dedos para zoom, botões numerados na barra inferior.

---

## MediaPipe: CDN ou local

Por padrão o WASM vem do jsDelivr e o modelo do storage do Google — o site
funciona sem nenhum arquivo grande no repositório. Para servir tudo do próprio
domínio (deploy realmente offline), baixe os dois artefatos para `web/vendor/` e
aponte `URL_WASM_MEDIAPIPE` e `URL_MODELO_MAOS` no [config.js](config.js) para os
caminhos locais. Nenhum outro código muda.

O modelo tem ~7,5 MB e o runtime WASM ~10 MB; ambos cabem no limite de 100 MB por
deploy do plano gratuito do Vercel.

---

## Diferenças em relação ao desktop

Nada de funcionalidade — os 10 corpos, os gestos, a estabilização e as fichas são
idênticos. As diferenças são de plataforma:

| | Desktop | Web |
|---|---|---|
| Render | pygame (superfícies) | Canvas 2D |
| HUD | desenhado no canvas | DOM + CSS |
| Câmera | OpenCV + thread | `getUserMedia` + `requestAnimationFrame` |
| MediaPipe | `mp.solutions.hands` (modelo embutido) | Tasks Vision WASM (modelo por URL) |
| Sair | `Q` / `ESC` | fechar a aba |
