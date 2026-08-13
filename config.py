"""Constantes globais da aplicação.

Todo valor ajustável do projeto mora aqui: resolução, escalas visuais, cores,
limiares de detecção de gestos e parâmetros de animação. Nenhum outro módulo
deve conter "números mágicos".
"""

from __future__ import annotations

from typing import Final

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
# Ao focar, o corpo é deslocado para a esquerda para não ficar sob a ficha.
DESLOCAMENTO_FOCO_X_PX: Final[float] = -150.0
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
# reenquadram o sistema inteiro. 9 continua sem significado.
GESTO_VISAO_GERAL: Final[int] = 10

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
COR_PAINEL: Final[tuple[int, int, int]] = (14, 17, 30)
ALPHA_PAINEL: Final[int] = 210

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

