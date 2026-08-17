"""Constantes globais da aplicação.

Todo valor ajustável do projeto mora aqui: resolução, escalas visuais, cores,
limiares de detecção de gestos e parâmetros de animação. Nenhum outro módulo
deve conter "números mágicos".
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Versão
# ---------------------------------------------------------------------------
# Uma única versão para as DUAS implementações (desktop e web). Ao alterar
# qualquer uma delas, suba este número aqui E em web/config.js — o
# verificar_paridade.py falha se os dois ficarem diferentes, e o
# publicar.py regenera o ZIP de download com a versão nova.
VERSAO: Final[str] = "1.5.0"

# Página de ranking aberta pela tecla R. É a ÚNICA URL que o desktop abre além
# da assinatura do autor, e por isso mora aqui e não solta no meio do main.py.
#
# O endereço antigo (sistema-solar-gestos.vercel.app) era um hostname obsoleto:
# responde `X-Vercel-Error: DEPLOYMENT_NOT_FOUND`, e a tecla R abria uma página
# de erro. O deployment sempre esteve no ar em interact-solar-system.vercel.app
# — que é o endereço documentado no README.
#
# Tem de ser a VERCEL, e não o GitHub Pages: só ela roda as funções de
# `api/` (o ranking é servido por /api/ranking, com os dados no MongoDB). O
# mesmo ranking.html no Pages carrega, mas sem backend renderiza vazio.
#
# Sem extensão porque o vercel.json usa `cleanUrls: true`.
URL_RANKING: Final[str] = "https://interact-solar-system.vercel.app/ranking"

# ---------------------------------------------------------------------------
# Janela e loop principal
# ---------------------------------------------------------------------------

TITULO_JANELA: Final[str] = "Sistema Solar Interativo — controle por gestos"
# Tamanho INICIAL: a janela é redimensionável (pygame.RESIZABLE), então todo o
# layout é recalculado a partir do tamanho corrente, não destas constantes.
LARGURA_JANELA: Final[int] = 1280
ALTURA_JANELA: Final[int] = 800
LARGURA_MINIMA_JANELA: Final[int] = 900
ALTURA_MINIMA_JANELA: Final[int] = 620
FPS_ALVO: Final[int] = 60

# Fontes procuradas no sistema (a primeira encontrada vence). Sem assets externos.
FAMILIA_FONTE: Final[str] = "segoeui,dejavusans,verdana,arial"
FAMILIA_FONTE_MONO: Final[str] = "consolas,dejavusansmono,couriernew"

TAM_FONTE_TITULO: Final[int] = 56
TAM_FONTE_GRANDE: Final[int] = 34
TAM_FONTE_MEDIA: Final[int] = 21
TAM_FONTE_PEQUENA: Final[int] = 16
TAM_FONTE_MINI: Final[int] = 14

# ---------------------------------------------------------------------------
# Escalas da cena — ATENÇÃO: NÃO SÃO REALISTAS (e nem podem ser)
# ---------------------------------------------------------------------------
# Em escala linear real o Sistema Solar é impossível de desenhar: se a órbita de
# Netuno (30,07 UA) coubesse na tela, Mercúrio (0,387 UA) ficaria a ~1% do raio,
# colado no Sol, e a Terra teria menos de 1 pixel de diâmetro (o Sol é ~109x
# maior que a Terra, e a órbita da Terra é ~11.700x maior que o próprio Sol).
#
# Por isso usamos duas compressões independentes e deliberadamente "erradas":
#
# 1) RAIO ORBITAL — escala LOGARÍTMICA. O raio em pixels é interpolado
#    linearmente sobre ln(distância em UA), de forma que Mercúrio cai em
#    RAIO_ORBITA_MIN_PX e Netuno em RAIO_ORBITA_MAX_PX. Isso preserva a *ordem*
#    e a *sensação* de espaçamento crescente, mas não as proporções.
#
# 2) RAIO DO CORPO — LEI DE POTÊNCIA com expoente < 1 (raiz). O raio desenhado é
#    RAIO_PLANETA_BASE_PX * (diâmetro / diâmetro da Terra) ** EXPOENTE_RAIO_CORPO.
#    Com expoente 0,40 a razão Júpiter/Mercúrio cai de ~29x para ~3,8x, o que
#    mantém Mercúrio visível sem transformar Júpiter em uma parede.
#
# 3) O Sol tem raio FIXO (RAIO_SOL_PX): mesmo comprimido pela lei de potência
#    ele engoliria as primeiras órbitas.
#
# Consequência: qualquer leitura de tamanho/distância relativos na tela é
# qualitativa. Os números reais estão sempre na ficha do planeta.

RAIO_ORBITA_MIN_PX: Final[float] = 95.0   # órbita de Mercúrio
RAIO_ORBITA_MAX_PX: Final[float] = 420.0  # órbita de Netuno

RAIO_PLANETA_BASE_PX: Final[float] = 10.0  # raio desenhado da Terra
EXPOENTE_RAIO_CORPO: Final[float] = 0.40
RAIO_SOL_PX: Final[float] = 46.0

# ---------------------------------------------------------------------------
# Tempo da simulação
# ---------------------------------------------------------------------------
# TIME_SCALE = quantos dias astronômicos passam a cada segundo real.
# Com 12, a Terra completa uma volta em ~30 s e Netuno em ~1h23 (por isso a
# opção de acelerar com "+"). Os períodos são proporcionais aos reais.
TIME_SCALE: Final[float] = 12.0
TIME_SCALE_MIN: Final[float] = 0.5
TIME_SCALE_MAX: Final[float] = 400.0
FATOR_AJUSTE_TEMPO: Final[float] = 1.5  # multiplicador aplicado por toque em +/-

# Rotação própria: em escala real Júpiter giraria absurdamente rápido em relação
# à sua translação. Comprimimos a rotação por este fator para virar um giro
# perceptível, não um borrão.
FATOR_ROTACAO_PROPRIA: Final[float] = 0.06

# Velocidade aparente das luas. O período de cada uma vira
# REFERENCIA * (período_real ** EXPOENTE): o expoente < 1 comprime a faixa
# (Fobos 0,3 dia e Calisto 16,7 dias ficam ambos legíveis) e a referência
# escolhe onde essa faixa cai. Com 130 e 0,38, uma volta leva de 7 a 31 s na
# escala de tempo padrão — dá para ler o nome da lua antes de ela dar a volta.
PERIODO_LUA_REFERENCIA_DIAS: Final[float] = 130.0
EXPOENTE_PERIODO_LUA: Final[float] = 0.38

# ---------------------------------------------------------------------------
# Câmera
# ---------------------------------------------------------------------------
ZOOM_VISAO_GERAL: Final[float] = 0.90
ZOOM_MIN: Final[float] = 0.35
ZOOM_MAX: Final[float] = 6.00
RAIO_ALVO_FOCO_PX: Final[float] = 92.0  # raio desejado na tela ao focar um corpo
DURACAO_TRANSICAO_S: Final[float] = 0.80  # ease-in-out do zoom/pan
# Ao focar, o corpo é deslocado para a DIREITA: a ficha ocupa a coluna esquerda,
# então o alvo precisa fugir dela, não do lado oposto.
DESLOCAMENTO_FOCO_X_PX: Final[float] = 150.0
# Navegação manual: arrastar com o botão esquerdo faz pan, a roda dá zoom.
FATOR_ZOOM_RODA: Final[float] = 1.15

# ---------------------------------------------------------------------------
# Renderização
# ---------------------------------------------------------------------------
COR_FUNDO: Final[tuple[int, int, int]] = (6, 7, 16)
COR_ORBITA: Final[tuple[int, int, int]] = (78, 88, 120)
COR_ORBITA_FOCADA: Final[tuple[int, int, int]] = (150, 200, 255)
ALPHA_ORBITA_NORMAL: Final[int] = 70
ALPHA_ORBITA_TENUE: Final[int] = 22     # órbitas não focadas durante o foco
ALPHA_ORBITA_FOCADA: Final[int] = 190
ALPHA_CORPO_ESMAECIDO: Final[int] = 70  # corpos não focados durante o foco
RAIO_ORBITA_MAX_DESENHAVEL_PX: Final[float] = 6000.0  # evita círculos gigantes

RAIO_TEXTURA_PX: Final[int] = 48       # raio das texturas pré-renderizadas
QUADROS_ROTACAO: Final[int] = 24       # quadros de rotação por corpo
PASSO_ANGULO_SOMBRA_GRAUS: Final[int] = 10  # granularidade do terminador

# Campo de estrelas com parallax
CAMADAS_ESTRELAS: Final[int] = 3
ESTRELAS_POR_CAMADA: Final[int] = 130
FATOR_PARALLAX: Final[tuple[float, float, float]] = (0.015, 0.045, 0.10)
SEMENTE_ALEATORIA: Final[int] = 20260813  # cena determinística entre execuções

# Texturas procedurais
LARGURA_TIRA_EM_RAIOS: Final[int] = 4  # tira equirretangular = 4x o raio
FAIXAS_GIGANTE_GASOSO: Final[float] = 9.0
FAIXAS_ROCHOSO: Final[float] = 3.0
ESCALA_RUIDO_TEXTURA: Final[int] = 10  # blocos do ruído antes do upsample
INTENSIDADE_TURBULENCIA: Final[float] = 2.6
ALPHA_SOMBRA_MAX: Final[int] = 205  # opacidade do lado noturno

# Anéis de Saturno
FATOR_ANEL_INTERNO: Final[float] = 1.35   # múltiplo do raio do planeta
FATOR_ANEL_EXTERNO: Final[float] = 2.30
ACHATAMENTO_ANEL: Final[float] = 0.28     # squash vertical (perspectiva)
INCLINACAO_ANEL_GRAUS: Final[float] = -12.0
COR_ANEL_SATURNO: Final[tuple[int, int, int]] = (226, 206, 168)

# Anel/eixo de Urano — o planeta gira "deitado" (97,77° de inclinação axial),
# então seu anel aparece quase de pé. É o indicador visual da inclinação.
FATOR_ANEL_URANO_INTERNO: Final[float] = 1.55
FATOR_ANEL_URANO_EXTERNO: Final[float] = 1.80
ACHATAMENTO_ANEL_URANO: Final[float] = 0.30
INCLINACAO_ANEL_URANO_GRAUS: Final[float] = 82.0
COR_ANEL_URANO: Final[tuple[int, int, int]] = (176, 224, 230)
ALPHA_ANEL_MAX: Final[int] = 210
COMPRIMENTO_EIXO_URANO: Final[float] = 2.2  # múltiplo do raio do planeta

# Halo do Sol
FATOR_HALO_SOL: Final[float] = 3.2
ALPHA_HALO_SOL: Final[int] = 105
COR_HALO_SOL: Final[tuple[int, int, int]] = (255, 176, 60)

# Destaque do corpo focado
COR_ANEL_DESTAQUE: Final[tuple[int, int, int]] = (140, 210, 255)
FOLGA_ANEL_DESTAQUE_PX: Final[float] = 14.0
ALPHA_ROTULO_CORPO: Final[int] = 150

# ---------------------------------------------------------------------------
# Webcam e detecção de mãos
# ---------------------------------------------------------------------------
INDICE_CAMERA: Final[int] = 0
LARGURA_CAPTURA: Final[int] = 640
ALTURA_CAPTURA: Final[int] = 480
FPS_CAPTURA: Final[int] = 30

# Trade-off performance x latência: rodar o MediaPipe em TODOS os frames custa
# caro em CPU modesta. Processamos 1 a cada N frames (~15 detecções/s com
# captura a 30 fps), o que ainda é muito mais rápido que o tempo de confirmação
# do estabilizador (~0,5 s), então o usuário não percebe atraso.
DETECTAR_A_CADA_N_FRAMES: Final[int] = 2

MAX_MAOS: Final[int] = 2
# Confiança baixa de propósito: os gestos 6, 7 e 8 exigem DUAS mãos no quadro, e
# a segunda mão costuma aparecer menor/mais inclinada. Com 0,6 ela era rejeitada
# com frequência e a contagem travava em 5. O filtro de verdade é a votação por
# maioria do estabilizador, não este limiar.
CONFIANCA_MIN_DETECCAO: Final[float] = 0.5
CONFIANCA_MIN_RASTREIO: Final[float] = 0.5
COMPLEXIDADE_MODELO: Final[int] = 0  # 0 = leve (mais rápido), 1 = preciso

# Abaixo destes valores o HUD avisa "iluminação/enquadramento ruins".
LIMIAR_AVISO_CONFIANCA: Final[float] = 0.72
LIMIAR_BRILHO_BAIXO: Final[float] = 0.26  # luminância média normalizada
# Frames de leitura falha seguidos antes de declarar a webcam desconectada.
FALHAS_ATE_DESCONEXAO: Final[int] = 30
SEGUNDOS_ENTRE_RECONEXOES: Final[float] = 3.0

# Enquadramento da mão. O MediaPipe extrapola landmarks para fora de [0, 1] mesmo
# com a mão inteira visível, então a tolerância precisa de folga — com 0,02 e
# duas mãos no quadro (necessárias para 6, 7 e 8) quase todo frame era
# descartado e a contagem nunca passava de 5.
MARGEM_QUADRO: Final[float] = 0.06
# Só descartamos a leitura quando VÁRIOS pontos saem: um dedo levemente
# extrapolado não invalida a contagem, uma mão cortada ao meio sim.
MAX_LANDMARKS_FORA_DO_QUADRO: Final[int] = 3

# Score de handedness abaixo do qual a mão é considerada lixo. O MediaPipe
# continua devolvendo 21 landmarks quando "acha" que viu uma mão numa cortina ou
# num rosto, e esses frames é que produziam a troca de gesto sozinha. Em vez de
# zerar a leitura (que apagaria o modo luas), o leitor REAPROVEITA a última pose
# boa por alguns frames — ver JANELA_REAPROVEITAMENTO_S.
CONFIANCA_MIN_UTIL: Final[float] = 0.70
# Por quanto tempo a última pose válida pode substituir frames ruins. Acima
# disso a mão provavelmente saiu mesmo, e insistir seria mentir para o usuário.
JANELA_REAPROVEITAMENTO_S: Final[float] = 0.35

# ---------------------------------------------------------------------------
# Filtro de landmarks (One Euro)
# ---------------------------------------------------------------------------
# O tremor natural da mão vale alguns pixels por frame e é justamente o que faz
# um dedo na fronteira do limiar piscar entre "aberto" e "fechado". Filtrar os
# 21 pontos ANTES de qualquer classificação resolve o problema na origem.
#
# Escolhemos o One Euro em vez de uma EMA simples porque a EMA obriga a um
# compromisso ruim: alpha baixo (suave) atrasa o gesto, alpha alto (responsivo)
# deixa passar o tremor. O One Euro varia o alpha com a VELOCIDADE — parado ele
# filtra forte, em movimento ele solta — então dá as duas coisas.
FILTRO_LANDMARKS_ATIVO: Final[bool] = True
# Frequência de corte com a mão parada. Quanto menor, mais estável (e mais
# "arrastado"). 1,2 Hz remove o tremor sem que o usuário perceba atraso.
UM_EURO_CORTE_MINIMO_HZ: Final[float] = 1.2
# Quanto o corte sobe por unidade de velocidade. É o botão da responsividade:
# alto demais e o filtro deixa de agir durante o movimento.
UM_EURO_BETA: Final[float] = 0.7
# Corte do filtro aplicado à própria derivada (padrão do artigo original).
UM_EURO_CORTE_DERIVADA_HZ: Final[float] = 1.0
# Alternativa simples, usada quando FILTRO_LANDMARKS_ATIVO é desligado ou
# quando não há timestamp confiável: média móvel exponencial pura.
ALPHA_EMA_LANDMARKS: Final[float] = 0.4

# ---------------------------------------------------------------------------
# Contagem de dedos
# ---------------------------------------------------------------------------
# Limiares expressos em frações do "tamanho da palma" (pulso -> MCP do médio),
# o que torna a contagem invariante à distância da mão até a câmera.
LIMIAR_DEDO_ESTENDIDO: Final[float] = 0.16
LIMIAR_POLEGAR_ESTENDIDO: Final[float] = 0.26
# HISTERESE: um dedo já contado como estendido só volta a "fechado" abaixo de um
# limiar MENOR. Com limiar único, um dedo parado exatamente na fronteira alterna
# a cada frame e a contagem oscila entre 3 e 4 sem o usuário mexer a mão.
# A folga é multiplicativa para acompanhar a normalização pela palma.
FOLGA_HISTERESE_DEDO: Final[float] = 0.72   # 0,16 -> sai em 0,115
FOLGA_HISTERESE_POLEGAR: Final[float] = 0.78  # 0,26 -> sai em 0,203
# Faixa em torno do limiar do polegar onde a projeção lateral não decide sozinha
# e entra o critério de distância até a base do dedo mínimo.
MARGEM_ZONA_CINZENTA_POLEGAR: Final[float] = 0.10
RAZAO_POLEGAR_ABERTO: Final[float] = 1.02
TAMANHO_PALMA_MINIMO: Final[float] = 1e-4  # evita divisão por zero

# ---------------------------------------------------------------------------
# Estabilização temporal do gesto
# ---------------------------------------------------------------------------
# O buffer guarda LEITURAS (inferências), não frames de render: com detecção a
# cada 2 frames de uma câmera de 30 fps são ~15 leituras/s, então 10 leituras com
# maioria de 70% (= 7 votos) equivalem a segurar o gesto por ~0,5 s.
TAMANHO_BUFFER_GESTOS: Final[int] = 10
FRACAO_MAIORIA: Final[float] = 0.70   # 70% do buffer precisa concordar
COOLDOWN_TROCA_S: Final[float] = 0.80
SEGUNDOS_ATE_VISAO_GERAL: Final[float] = 6.0

# Gesto de comando (não seleciona corpo): as duas mãos abertas, 5 + 5 = 10,
# reenquadram o sistema inteiro. O 9 (5 + 4) seleciona a Lua.
GESTO_VISAO_GERAL: Final[int] = 10
# Primeiro gesto que exige as duas mãos (uma mão sozinha só chega a 5).
GESTO_MINIMO_DUAS_MAOS: Final[int] = 6

# ---------------------------------------------------------------------------
# Luas dos demais planetas ("modo luas")
# ---------------------------------------------------------------------------
# Os gestos de 0 a 10 estão todos ocupados, então as luas menores não têm número
# próprio: elas aparecem em bloco quando o modo é ligado — pela tecla M ou pelo
# gesto das DUAS mãos em pinça, o único ainda livre.
# Ligadas por padrão: as luas são conteúdo, não um extra escondido atrás de
# um atalho. Na visão geral elas aparecem comprimidas (ver FATOR_LUA_COMPACTO_*).
LUAS_VISIVEIS_PADRAO: Final[bool] = True
# Raio desenhado de uma lua do TAMANHO DA NOSSA, em pixels de mundo. Não é mais
# o raio de todas: ver EXPOENTE_RAIO_LUA logo abaixo.
RAIO_LUA_MENOR_PX: Final[float] = 2.2
# Zoom a partir do qual as luas usam o raio orbital cheio. Abaixo dele o
# sistema é comprimido (ver FATOR_LUA_COMPACTO_*), não escondido.
ZOOM_MINIMO_PARA_LUAS: Final[float] = 1.6

# --- tamanho desenhado da lua ----------------------------------------------
# Mesma lei de potência dos planetas (expoente < 1 comprime a faixa), com a
# nossa Lua como referência. Antes TODAS as luas tinham 2,2 px: Titã (5.150 km)
# e Fobos (22 km) saíam idênticos na tela, e comparar tamanhos é justamente o
# que se espera de um sistema de luas desenhado lado a lado.
#
# Em escala real a razão Ganimedes/Fobos é 234x; com expoente 0,32 ela vira 5,7x
# — Fobos continua sendo um ponto e Ganimedes um disco, sem que nenhum dos dois
# saia da tela. Os números reais estão sempre na ficha.
DIAMETRO_LUA_REFERENCIA_KM: Final[float] = 3474.0  # a nossa Lua
EXPOENTE_RAIO_LUA: Final[float] = 0.32
# Pisos e tetos em pixels de mundo: abaixo de ~1,1 px a lua vira ruído de
# antisserrilhado e acima de ~3,4 px ela começa a competir com o planeta.
# O piso foi calibrado para NÃO achatar a faixa média: com 1,25 as luas de gelo
# de 400-500 km (Encélado, Miranda, Proteu) caíam todas nele e saíam do mesmo
# tamanho de Fobos, que tem 22 km. Com 1,10 só as cinco realmente minúsculas
# ficam no piso, e é o que se espera — elas são pontos mesmo.
RAIO_LUA_MENOR_MIN_PX: Final[float] = 1.10
RAIO_LUA_MENOR_MAX_PX: Final[float] = 3.40

# --- sprite esférico da lua -------------------------------------------------
# Cada lua deixou de ser um círculo de cor chapada: ganha um sprite
# pré-renderizado com manchas de terreno, escurecimento de limbo e borda suave,
# mais um terminador dia/noite apontado para o Sol — as mesmas três coisas que
# já davam volume aos planetas.
RAIO_TEXTURA_LUA_PX: Final[int] = 20
# Fases do terminador pré-rotacionadas. Bem menos que os 36 dos planetas
# (PASSO_ANGULO_SOMBRA_GRAUS): num disco de 20 px de raio, os 22,5° de erro
# máximo desta granularidade valem meio pixel na borda da sombra.
QUADROS_ILUMINACAO_LUA: Final[int] = 16
ALPHA_SOMBRA_LUA: Final[int] = 165
# Contraste das manchas de terreno, como fração da distância entre cor_escura e
# cor_clara. Alto demais e toda lua vira Jápeto.
CONTRASTE_TERRENO_LUA: Final[float] = 0.62
# Blocos da primeira oitava do ruído da lua — bem menos que os 10 dos planetas.
# O sprite tem 40 px de lado: com 10 blocos as manchas ficam com 4 px e somem
# no primeiro downscale, que é o caso normal (a lua raramente passa de 8 px na
# tela). Com 4 blocos as manchas têm 10 px e sobrevivem à redução.
ESCALA_RUIDO_LUA: Final[int] = 4

# Raio orbital COMPACTO, usado na visão geral — múltiplo do raio do planeta.
# Sem isso as luas invadem o planeta vizinho: em volta de Júpiter elas
# precisariam de 105 px e só há 70 px até Saturno. Com teto de 1,45 todo mundo
# cabe (Júpiter usa 38 px, a Lua da Terra usa 14,5 contra 34 de folga).
FATOR_LUA_COMPACTO_MIN: Final[float] = 1.15
FATOR_LUA_COMPACTO_MAX: Final[float] = 1.45
# Planetas com anéis precisam de um piso: com o fator compacto puro, as luas de
# Saturno cairiam DENTRO dos anéis, que vão até 2,3 raios.
FOLGA_LUA_APOS_ANEL: Final[float] = 0.15
COR_ORBITA_LUA: Final[tuple[int, int, int]] = (150, 160, 190)
ALPHA_ORBITA_LUA: Final[int] = 45

# --- legibilidade dos rótulos de lua ---------------------------------------
# O nome era desenhado direto sobre a cena. Contra o campo de estrelas passava,
# mas em cima do disco de Júpiter (bege claro) ou dos anéis de Saturno um texto
# cinza de 11 px some. Agora todo rótulo sai com um contorno escuro atrás — é o
# mesmo truque de legenda de mapa, e custa quatro blits pré-renderizados.
ALPHA_ROTULO_LUA: Final[int] = 205
COR_CONTORNO_ROTULO: Final[tuple[int, int, int]] = (6, 8, 18)
ESPESSURA_CONTORNO_ROTULO_PX: Final[int] = 2
# Distância mínima entre dois nomes de lua na tela. Abaixo dela o segundo é
# omitido: com Júpiter comprimido na visão geral, cinco rótulos empilhados no
# mesmo ponto viram uma mancha ilegível — e nenhum deles é lido. O rótulo da lua
# em DESTAQUE nunca é omitido, porque ele é a resposta ao gesto do usuário.
DISTANCIA_MINIMA_ROTULO_LUA_PX: Final[float] = 26.0

# ---------------------------------------------------------------------------
# Cinturão de asteroides
# ---------------------------------------------------------------------------
# Fica entre Marte (1,52 UA) e Júpiter (5,20 UA). Como o raio orbital do projeto
# é logarítmico, o cinturão ocupa a faixa correspondente a essas duas distâncias
# — os limites são calculados em nucleo/orbita.py, não fixados aqui.
CINTURAO_UA_INTERNO: Final[float] = 2.06   # borda interna real do cinturão
CINTURAO_UA_EXTERNO: Final[float] = 3.27   # borda externa real
ASTEROIDES_DESENHADOS: Final[int] = 340
COR_ASTEROIDE: Final[tuple[int, int, int]] = (150, 138, 120)
ALPHA_ASTEROIDE_MIN: Final[int] = 60
ALPHA_ASTEROIDE_MAX: Final[int] = 170
# O cinturão gira devagar, como um corpo só: seguir o período real de cada
# asteroide não mudaria nada visualmente e custaria uma volta por partícula.
PERIODO_CINTURAO_DIAS: Final[float] = 1680.0

# ---------------------------------------------------------------------------
# Gesto "L" — modificador de modo (seleção de luas)
# ---------------------------------------------------------------------------
# Uma mão em "L" faz o número da OUTRA mão significar índice de lua em vez de
# planeta. Foi a saída para um limite duro: a contagem vai de 0 a 10 e todos os
# valores já estão ocupados — não sobrava número, mas sobrava forma.
#
# Faixa angular entre polegar e indicador. Abaixo de 50° o gesto vira "apontar"
# e acima de 130° a mão está praticamente aberta; nos dois casos não é um L.
ANGULO_L_MINIMO_GRAUS: Final[float] = 50.0
ANGULO_L_MAXIMO_GRAUS: Final[float] = 130.0
# Histerese ASSIMÉTRICA de propósito: entrar devagar incomoda menos que sair
# sem querer no meio de uma seleção.
FRAMES_PARA_ENTRAR_MODO_LUAS: Final[int] = 6
FRAMES_PARA_SAIR_MODO_LUAS: Final[int] = 8
# Enquanto houver um "L" no quadro — e por este tempo depois que ele sumir — a
# contagem de dedos NÃO seleciona planeta.
#
# Sem isso, o "L" + 2 dedos virava planeta 2 (Vênus) em vez da lua 2. O motivo é
# que a seleção de planeta era alimentada pela contagem CRUA do detector, que
# soma todas as mãos e não sabe o que é forma: nos frames em que o L ainda não
# tinha completado a histerese (ou piscava por um instante), aquele número
# escapava para o estabilizador e trocava o planeta debaixo do usuário.
#
# A folga depois do L sumir existe pelo mesmo motivo do COOLDOWN_APOS_PINCA_S:
# desfazer um L passa por poses intermediárias que são lidas como 1, 2 ou 3
# dedos, e sem a pausa o gesto de SAIR do modo lua terminava escolhendo um
# planeta ao acaso.
COOLDOWN_APOS_L_S: Final[float] = 0.6
# Votação da lua escolhida, no mesmo espírito do estabilizador de planetas.
BUFFER_SELECAO_LUA: Final[int] = 6
VOTOS_SELECAO_LUA: Final[int] = 5
# Cooldown após ABRIR uma ficha de lua. Mais longo que o do estabilizador de
# planetas porque a ficha muda a tela inteira: reabrir outra em seguida, por um
# frame ruim, é bem mais incômodo que trocar de planeta sem querer.
COOLDOWN_SELECAO_LUA_S: Final[float] = 0.8

# --- confirmação da lua (PREVIEW -> FICHA) ---------------------------------
# Enquanto o "L" é mantido, o número da outra mão apenas PRÉ-VISUALIZA a lua
# (destaque na órbita + nome no HUD). A ficha só abre quando o mesmo número se
# mantém estável por FRAMES_PARA_ABRIR_FICHA_LUA leituras seguidas.
#
# São leituras (inferências), não frames de render: a ~15 leituras/s, 12
# leituras ≈ 0,8 s de mão parada. O valor foi escolhido para ser longo o
# bastante para o usuário "passear" pelos números sem abrir nada, e curto o
# bastante para não cansar o braço.
FRAMES_PARA_ABRIR_FICHA_LUA: Final[int] = 12
# Tolerância a falhas DENTRO da contagem: um único frame com número diferente
# não zera o progresso, só o desconta. Sem isso, uma piscada do rastreio no
# décimo frame obrigava a recomeçar do zero.
FALHAS_TOLERADAS_CONFIRMACAO: Final[int] = 3

# ---------------------------------------------------------------------------
# Gesto de pinça — zoom controlado pela câmera
# ---------------------------------------------------------------------------
# Medimos a distância ponta do polegar <-> ponta do indicador dividida pelo
# tamanho da palma. Normalizar pela palma torna a medida independente da
# distância até a câmera, pelo mesmo motivo dos limiares de dedo.
#
# Histerese: entra em modo zoom abaixo de ATIVA e só sai acima de SAIDA. Com um
# limiar único a pinça piscaria na fronteira e o zoom entraria e sairia sozinho.
LIMIAR_PINCA_ATIVA: Final[float] = 0.38
LIMIAR_PINCA_SAIDA: Final[float] = 0.55
# Peso do valor novo na média móvel exponencial. O tremor da mão é muito maior
# que o do mouse: sem filtro o zoom vibra a cada frame.
SUAVIZACAO_PINCA: Final[float] = 0.35
# Fator máximo de zoom aplicado por leitura — trava saltos quando o rastreio
# perde a mão por um instante e a razão dá um pulo.
FATOR_ZOOM_PINCA_MAX: Final[float] = 1.12
# Sair da pinça passa por poses intermediárias que seriam lidas como 1, 2 ou 3
# dedos; sem esta pausa o zoom terminaria trocando de planeta.
COOLDOWN_APOS_PINCA_S: Final[float] = 0.6

# ---------------------------------------------------------------------------
# Narração por voz (TTS)
# ---------------------------------------------------------------------------
NARRACAO_ATIVA_PADRAO: Final[bool] = True
IDIOMA_NARRACAO: Final[str] = "pt-BR"
VELOCIDADE_NARRACAO: Final[int] = 175  # palavras por minuto
VOLUME_NARRACAO: Final[float] = 0.9
# A narração lê a ficha inteira: nome, tipo, diâmetro, distância, períodos,
# luas, temperatura e o fato curioso. Desligado, fala só o nome e o tipo.
NARRAR_FICHA_COMPLETA: Final[bool] = True

# --- ElevenLabs (voz neural) ------------------------------------------------
# Quando há uma chave configurada, a narração usa a voz "Brian" da ElevenLabs;
# sem chave, sem rede ou em caso de erro, cai para a voz local do sistema.
#
# ATENÇÃO: isto é a única parte do projeto que fala com a internet em execução.
# O fallback existe justamente para o aplicativo continuar completo offline.
#
# A chave sai de ELEVENLABS_API_KEY (arquivo .env ao lado do main.py ou variável
# de ambiente). Ela NUNCA é embutida no código nem no executável.
ELEVENLABS_VOZ_ID: Final[str] = "nPczCjzI2devNBz1zQrb"  # Brian
ELEVENLABS_VOZ_NOME: Final[str] = "Brian"
ELEVENLABS_MODELO: Final[str] = "eleven_multilingual_v2"  # fala português
ELEVENLABS_FORMATO: Final[str] = "mp3_44100_128"
ELEVENLABS_URL: Final[str] = "https://api.elevenlabs.io/v1/text-to-speech"
ELEVENLABS_TIMEOUT_S: Final[float] = 12.0
# Cada frase sintetizada custa créditos: guardamos o áudio em disco para que o
# mesmo planeta só seja gerado uma vez, hoje e nas próximas execuções.
PASTA_CACHE_VOZ: Final[str] = "cache_voz"

# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------
LARGURA_PREVIEW_CAMERA: Final[int] = 288
ALTURA_PREVIEW_CAMERA: Final[int] = 216
MARGEM_HUD: Final[int] = 18
RAIO_ANEL_PROGRESSO: Final[int] = 46
ESPESSURA_ANEL_PROGRESSO: Final[int] = 7

COR_TEXTO: Final[tuple[int, int, int]] = (232, 236, 245)
COR_TEXTO_SECUNDARIO: Final[tuple[int, int, int]] = (150, 160, 185)
COR_DESTAQUE: Final[tuple[int, int, int]] = (120, 200, 255)
COR_AVISO: Final[tuple[int, int, int]] = (255, 190, 90)
COR_ERRO: Final[tuple[int, int, int]] = (255, 110, 110)
COR_SUCESSO: Final[tuple[int, int, int]] = (110, 226, 160)  # câmera ativa
# Trilho das barras de progresso. Precisa ser OPACO: o pygame descarta o alfa de
# uma cor RGBA ao desenhar direto na tela (que não tem canal alfa por pixel), e
# um (255,255,255,40) saía branco sólido em vez de um cinza discreto. Este é o
# valor já pré-misturado sobre o fundo do painel.
COR_TRILHO_BARRA: Final[tuple[int, int, int]] = (58, 64, 84)
COR_PAINEL: Final[tuple[int, int, int]] = (14, 17, 30)
ALPHA_PAINEL: Final[int] = 210

# Legenda de gestos: cada linha ganha um ponto com a cor do corpo, e a linha do
# corpo em foco recebe um realce de fundo — é o que permite achar "onde estou"
# sem ler a lista inteira.
RAIO_PONTO_LEGENDA: Final[int] = 4
ALPHA_LINHA_LEGENDA_ATIVA: Final[int] = 38
# Barra de atalhos rente à base da janela.
ALTURA_BARRA_ATALHOS: Final[int] = 26
# Abaixo destas alturas/larguras o HUD abre mão de blocos inteiros em vez de
# empilhá-los sobre a cena: legenda primeiro, depois a barra de atalhos.
ALTURA_MINIMA_LEGENDA: Final[int] = 700
LARGURA_MINIMA_ATALHOS: Final[int] = 1040

# Ficha do planeta
LARGURA_FICHA: Final[int] = 330
# A ficha da LUA fica ao LADO da do planeta, na mesma coluna esquerda: o
# planeta-mãe continua visível e comparar os dois lado a lado é o ponto de olhar
# uma lua. Um pouco mais estreita porque tem menos linhas.
#
# Ela já morou no canto direito, e era um erro: aquele canto é da webcam e da
# assinatura, e o preview é desenhado DEPOIS — a ficha abria atrás dele.
LARGURA_FICHA_LUA: Final[int] = 300
FOLGA_ENTRE_FICHAS: Final[int] = 12
DURACAO_ANIMACAO_FICHA_S: Final[float] = 0.45
DESLOCAMENTO_ENTRADA_FICHA_PX: Final[float] = 60.0

# ---------------------------------------------------------------------------
# Marca d'água / assinatura do autor
# ---------------------------------------------------------------------------
# Porte da marca d'água "Nandev" (originalmente CSS) para o HUD: cubo wireframe
# em rotação, texto com gradiente animado e partículas em órbita. Clicar abre o
# perfil no navegador — é a única ação do app que sai da janela, e só acontece
# por clique explícito.
ASSINATURA_TEXTO_PREFIXO: Final[str] = "Desenvolvido por "
ASSINATURA_NOME_DESTAQUE: Final[str] = "Nan"   # recebe o gradiente
ASSINATURA_NOME_RESTANTE: Final[str] = "dev"
ASSINATURA_SIMBOLO_CODIGO: Final[str] = "</>"
ASSINATURA_URL: Final[str] = (
    "https://www.linkedin.com/in/renan-de-oliveira-farias-66a9b412b/"
)

# Paleta da marca (as mesmas cores do CSS original).
COR_ASSINATURA_PRIMARIA: Final[tuple[int, int, int]] = (0, 255, 136)
COR_ASSINATURA_SECUNDARIA: Final[tuple[int, int, int]] = (0, 153, 255)
COR_ASSINATURA_ACENTO: Final[tuple[int, int, int]] = (255, 0, 136)
COR_ASSINATURA_TOPO: Final[tuple[int, int, int]] = (255, 107, 53)
COR_ASSINATURA_BASE: Final[tuple[int, int, int]] = (196, 76, 255)

# Geometria do bloco.
ASSINATURA_ALTURA: Final[int] = 40
ASSINATURA_LARGURA_MINIMA: Final[int] = 236
ASSINATURA_PADDING_X: Final[int] = 14
ASSINATURA_ESPACO_INTERNO: Final[int] = 10
ASSINATURA_ARESTA_CUBO_PX: Final[float] = 18.0
ASSINATURA_DISTANCIA_PERSPECTIVA: Final[float] = 3.0  # múltiplo da aresta

# Animações (segundos por ciclo) e opacidades.
ASSINATURA_PERIODO_CUBO_S: Final[float] = 8.0
ASSINATURA_PERIODO_MESTRE_S: Final[float] = 20.0
ASSINATURA_PERIODO_GRADIENTE_S: Final[float] = 3.0
ASSINATURA_PERIODO_ORBITA_S: Final[float] = 6.0
ASSINATURA_PERIODO_SCAN_S: Final[float] = 3.0
ASSINATURA_PERIODO_BRILHO_S: Final[float] = 2.0
ASSINATURA_PARTICULAS: Final[int] = 5
ASSINATURA_RAIO_ORBITA_PX: Final[float] = 15.0
ALPHA_ASSINATURA_PAINEL: Final[int] = 165
ALPHA_ASSINATURA_FACE_FUNDO: Final[int] = 70   # face mais distante do cubo
ALPHA_ASSINATURA_FACE_FRENTE: Final[int] = 255

# ---------------------------------------------------------------------------
# Lua (satélite da Terra)
# ---------------------------------------------------------------------------
# Raio orbital da Lua em torno da Terra, em pixels de mundo. Não segue a escala
# logarítmica dos planetas — seria invisível. É um valor visual fixo.
RAIO_ORBITA_LUA_PX: Final[float] = 28.0
# Raio desenhado da Lua (fixo, como o Sol). Em escala real seria ~0,27x a Terra,
# mas com raio base 10 px isso daria 2,7 px — pequeno demais para ver textura.
RAIO_LUA_PX: Final[float] = 4.0

