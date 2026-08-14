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
VERSAO: Final[str] = "1.3.1"

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

# ---------------------------------------------------------------------------
# Contagem de dedos
# ---------------------------------------------------------------------------
# Limiares expressos em frações do "tamanho da palma" (pulso -> MCP do médio),
# o que torna a contagem invariante à distância da mão até a câmera.
LIMIAR_DEDO_ESTENDIDO: Final[float] = 0.16
LIMIAR_POLEGAR_ESTENDIDO: Final[float] = 0.26
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
LUAS_VISIVEIS_PADRAO: Final[bool] = False
# Raio desenhado de cada lua menor, em pixels de mundo. Fixo, como o da Lua: em
# proporção real Encélado (504 km) teria 0,2 px ao lado de Saturno.
RAIO_LUA_MENOR_PX: Final[float] = 2.2
# As luas só aparecem quando o planeta está grande o bastante na tela; abaixo
# disto elas viram um borrão de pontos em cima do disco.
ZOOM_MINIMO_PARA_LUAS: Final[float] = 1.6
COR_ORBITA_LUA: Final[tuple[int, int, int]] = (150, 160, 190)
ALPHA_ORBITA_LUA: Final[int] = 45

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

