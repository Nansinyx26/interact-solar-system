# Roadmap — tarefas de desenvolvimento

Backlog do Sistema Solar Interativo. As tarefas abaixo estão **planejadas, não
implementadas** — cada uma traz o desenho técnico e os pontos de atenção
levantados durante o desenvolvimento das versões desktop e web.

Legenda de esforço: **P** (poucas horas) · **M** (um dia) · **G** (vários dias).

---

## 1. Zoom por gesto de pinça na câmera — **M**

Controlar o zoom aproximando e afastando polegar e indicador **na frente da
webcam**, sem tocar em nada.

> Atenção para não confundir com o que já existe: a versão web já tem zoom por
> pinça **na tela sensível ao toque** ([web/app.js](web/app.js), evento
> `touchmove` com dois toques). A tarefa aqui é a pinça **detectada pela
> câmera**, que hoje não existe em nenhuma das duas versões.

### Desenho

1. **Detectar a pose de pinça.** Em [gestos/contador.py](gestos/contador.py) já
   temos o referencial da palma; acrescentar uma função
   `distancia_pinca(landmarks) -> float | None` que devolva
   `|ponta_polegar − ponta_indicador| / tamanho_palma`. Normalizar pelo tamanho
   da palma é o que torna a medida independente da distância até a câmera — a
   mesma razão pela qual os limiares de dedo já são frações da palma.
2. **Separar "pinça" de "contagem".** A pose de pinça tem polegar e indicador
   estendidos e os outros três fechados, o que hoje seria contado como **2**
   (Vênus). Antes de somar dedos, verificar se a razão da pinça está abaixo de
   um limiar (`LIMIAR_PINCA_ATIVA`); se estiver, a leitura vira um comando de
   zoom e **não** entra no buffer do estabilizador.
3. **Mapear distância → zoom.** Guardar a razão do primeiro frame da pinça como
   referência e aplicar `camera.aplicar_zoom(razao_atual / razao_inicial)`. A
   `Camera2D` já tem `aplicar_zoom` e `congelar` (usados hoje pela roda do
   mouse), então nada novo é necessário do lado da câmera.
4. **Suavizar.** Passar a razão por uma média móvel exponencial: o tremor da mão
   é muito maior que o do mouse e sem filtro o zoom vibra.
5. **Feedback no HUD.** Mostrar um indicador de "modo zoom" enquanto a pinça
   estiver ativa, senão o usuário não entende por que o gesto parou de trocar de
   planeta.

### Riscos

- Sair da pinça passa por poses intermediárias que podem ser lidas como 1, 2 ou
  3 dedos e disparar uma troca de foco indesejada. Mitigação: bloquear o
  estabilizador por ~0,5 s depois que a pinça termina (mesmo mecanismo do
  `COOLDOWN_TROCA_S`).
- Com duas mãos no quadro, decidir qual delas comanda o zoom. Sugestão: a de
  maior confiança, que é a ordenação que o detector já faz.

### Arquivos afetados

`config.py` · `gestos/contador.py` · `gestos/detector.py` · `main.py` ·
`ui/hud.py` — e os equivalentes em `web/`.

---

## 2. Narração por voz (TTS) do corpo focado — **P** (web) / **M** (desktop)

Ao confirmar um gesto, falar em voz alta o nome do planeta e, opcionalmente, a
ficha resumida ("Saturno. Gigante gasoso. 146 luas conhecidas.").

### Web — usar a Web Speech API (sem dependência nova)

```js
const fala = new SpeechSynthesisUtterance(`${corpo.nome}. ${corpo.fatoCurioso}`);
fala.lang = "pt-BR";
speechSynthesis.cancel();   // corta a narração anterior
speechSynthesis.speak(fala);
```

Pontos de atenção:

- `speechSynthesis.getVoices()` volta vazio no primeiro acesso em vários
  navegadores; escutar o evento `voiceschanged` antes de escolher a voz pt-BR.
- Só disparar após a primeira interação do usuário (mesma restrição da câmera).
- Trocar de planeta rápido empilha falas — sempre `cancel()` antes de `speak()`.
- Botão de mudo no HUD e preferência salva em `localStorage`.

### Desktop — precisa de uma dependência

O Python não traz TTS embutido. Opções, em ordem de preferência:

| Opção | Prós | Contras |
|---|---|---|
| `pyttsx3` | offline, multiplataforma, usa a voz do SAPI5 no Windows | mais uma dependência; qualidade da voz varia |
| `win32com` (SAPI direto) | zero dependência nova além do `pywin32` | só Windows |
| serviço em nuvem | melhor voz | quebra o requisito de zero rede em runtime — **descartado** |

Recomendação: `pyttsx3`, **em thread separada**. O `engine.say()` é bloqueante e
travaria o loop de render — o mesmo motivo pelo qual a captura de vídeo já roda
fora do loop principal. Fila de mensagens com no máximo um item pendente:
trocando de planeta rápido, a fala mais recente substitui a anterior.

### Arquivos afetados

Novo `ui/narrador.py` e `web/ui/narrador.js` · `config.py` (idioma, velocidade,
ligado/desligado) · `main.py` e `web/app.js` (disparo em `_selecionar`) ·
`ui/hud.py` (botão de mudo).

---

## 3. Outras ideias registradas

| Ideia | Esforço | Nota |
|---|---|---|
| Versão 3D com Ursina/VPython | G | reescrita completa do renderizador |
| Luas orbitando os gigantes | M | exige um segundo nível de órbita e mais escala comprimida |
| Modo apresentação (tour automático) | P | percorre os 9 corpos com pausa em cada um |
| PWA instalável na versão web | P | manifest + service worker; o app já é totalmente offline depois do primeiro acesso |
| Empacotar o modelo do MediaPipe no deploy | P | serve `hand_landmarker.task` do próprio domínio, eliminando o CDN em runtime |
