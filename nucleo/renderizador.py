"""Desenho da cena do Sistema Solar.

Todas as texturas são geradas proceduralmente com NumPy na inicialização — não
há uma única imagem baixada. A rotação própria é real, não um truque: cada corpo
tem uma tira equirretangular (mapa "desenrolado") que é projetada em esfera em
``QUADROS_ROTACAO`` fases, pré-renderizadas uma vez e reaproveitadas.
"""

from __future__ import annotations

import math

import numpy as np
import pygame

from config import (
    ACHATAMENTO_ANEL,
    ACHATAMENTO_ANEL_URANO,
    ALPHA_ANEL_MAX,
    ALPHA_ASTEROIDE_MAX,
    ALPHA_ASTEROIDE_MIN,
    ALPHA_CORPO_ESMAECIDO,
    ALPHA_HALO_SOL,
    ALPHA_ORBITA_FOCADA,
    ALPHA_ORBITA_LUA,
    ALPHA_ORBITA_NORMAL,
    ALPHA_ORBITA_TENUE,
    ALPHA_ROTULO_CORPO,
    ALPHA_ROTULO_LUA,
    ALPHA_SOMBRA_LUA,
    ALPHA_SOMBRA_MAX,
    ALTURA_JANELA,
    ASTEROIDES_DESENHADOS,
    CAMADAS_ESTRELAS,
    COMPRIMENTO_EIXO_URANO,
    CONTRASTE_TERRENO_LUA,
    COR_ANEL_DESTAQUE,
    COR_ANEL_SATURNO,
    COR_ANEL_URANO,
    COR_ASTEROIDE,
    COR_CONTORNO_ROTULO,
    COR_FUNDO,
    COR_HALO_SOL,
    COR_ORBITA,
    COR_ORBITA_FOCADA,
    COR_DESTAQUE,
    COR_ORBITA_LUA,
    COR_TEXTO,
    COR_TEXTO_SECUNDARIO,
    DISTANCIA_MINIMA_ROTULO_LUA_PX,
    ESPESSURA_CONTORNO_ROTULO_PX,
    ESCALA_RUIDO_LUA,
    ESCALA_RUIDO_TEXTURA,
    ESTRELAS_POR_CAMADA,
    FAIXAS_GIGANTE_GASOSO,
    FAIXAS_ROCHOSO,
    FATOR_ANEL_EXTERNO,
    FATOR_ANEL_INTERNO,
    FATOR_ANEL_URANO_EXTERNO,
    FATOR_ANEL_URANO_INTERNO,
    FATOR_HALO_SOL,
    FATOR_PARALLAX,
    FOLGA_ANEL_DESTAQUE_PX,
    INCLINACAO_ANEL_GRAUS,
    INCLINACAO_ANEL_URANO_GRAUS,
    INTENSIDADE_TURBULENCIA,
    LARGURA_JANELA,
    LARGURA_TIRA_EM_RAIOS,
    PASSO_ANGULO_SOMBRA_GRAUS,
    QUADROS_ILUMINACAO_LUA,
    QUADROS_ROTACAO,
    RAIO_ORBITA_LUA_PX,
    RAIO_ORBITA_MAX_DESENHAVEL_PX,
    RAIO_TEXTURA_LUA_PX,
    RAIO_TEXTURA_PX,
    SEMENTE_ALEATORIA,
    ZOOM_MINIMO_PARA_LUAS,
)
from dados.luas import LuaMenor
from dados.planetas import CORPOS, CorpoCeleste, luas_do_planeta
from nucleo.camera import Camera2D
from nucleo.orbita import (
    angulo_do_cinturao,
    angulo_iluminacao,
    faixa_do_cinturao,
    fase_rotacao,
    fator_orbita_lua,
    posicao_da_lua_menor,
    raio_corpo_px,
    raio_lua_menor_px,
    raio_orbital_px,
)

# Dimensões das texturas em memória (independem do zoom: o escalonamento é feito
# na hora de desenhar).
_RAIO_TEX = RAIO_TEXTURA_PX
_TAM_TEX = _RAIO_TEX * 2
_LARGURA_TIRA = _RAIO_TEX * LARGURA_TIRA_EM_RAIOS
_ALTURA_TIRA = _TAM_TEX

_RAIO_TEX_LUA = RAIO_TEXTURA_LUA_PX
_TAM_TEX_LUA = _RAIO_TEX_LUA * 2

# Corpos que ganham calotas polares brancas na textura.
_CORPOS_COM_CALOTAS: tuple[str, ...] = ("Terra", "Marte")

# Limite do cache de superfícies escaladas (evita crescer sem fim durante zoom).
_MAX_ENTRADAS_CACHE = 400


# ---------------------------------------------------------------------------
# Ruído procedural
# ---------------------------------------------------------------------------
def _redimensionar_bilinear(mapa: np.ndarray, altura: int, largura: int) -> np.ndarray:
    """Amplia uma matriz 2D por interpolação bilinear (sem dependências extras)."""
    ys = np.linspace(0, mapa.shape[0] - 1, altura)
    xs = np.linspace(0, mapa.shape[1] - 1, largura)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, mapa.shape[0] - 1)
    x1 = np.minimum(x0 + 1, mapa.shape[1] - 1)
    peso_y = (ys - y0)[:, None]
    peso_x = (xs - x0)[None, :]
    superior = mapa[np.ix_(y0, x0)] * (1 - peso_x) + mapa[np.ix_(y0, x1)] * peso_x
    inferior = mapa[np.ix_(y1, x0)] * (1 - peso_x) + mapa[np.ix_(y1, x1)] * peso_x
    return superior * (1 - peso_y) + inferior * peso_y


def _ruido_suave(
    rng: np.random.Generator,
    altura: int,
    largura: int,
    oitavas: int = 3,
    escala: int = ESCALA_RUIDO_TEXTURA,
) -> np.ndarray:
    """Ruído fractal em [0, 1], contínuo na emenda horizontal da tira.

    ``escala`` é o número de blocos da primeira oitava: quanto menor, maiores as
    manchas. As luas usam um valor bem menor que os planetas — ver
    ESCALA_RUIDO_LUA.
    """
    total = np.zeros((altura, largura), dtype=np.float64)
    amplitude = 1.0
    soma_amplitudes = 0.0
    for oitava in range(oitavas):
        blocos = max(2, escala * (2**oitava))
        # A coluna extra repete a primeira: a textura fecha ao dar a volta.
        base = rng.random((blocos, blocos + 1))
        base[:, -1] = base[:, 0]
        total += amplitude * _redimensionar_bilinear(base, altura, largura)
        soma_amplitudes += amplitude
        amplitude *= 0.5
    return total / soma_amplitudes


# ---------------------------------------------------------------------------
# Texturas dos corpos
# ---------------------------------------------------------------------------
def _tira_equirretangular(corpo: CorpoCeleste) -> np.ndarray:
    """Mapa "desenrolado" do corpo, em RGB float (altura, largura, 3)."""
    # Semente fixa por corpo: a cena é idêntica em toda execução.
    rng = np.random.default_rng(SEMENTE_ALEATORIA + corpo.indice_gesto)
    ruido = _ruido_suave(rng, _ALTURA_TIRA, _LARGURA_TIRA)
    ruido_fino = _ruido_suave(rng, _ALTURA_TIRA, _LARGURA_TIRA, oitavas=4)

    # Latitude normalizada em [-1, 1] (-1 = polo sul).
    latitude = np.linspace(-1.0, 1.0, _ALTURA_TIRA)[:, None]
    longitude = np.linspace(-1.0, 1.0, _LARGURA_TIRA)[None, :]

    if corpo.faixas:
        frequencia = FAIXAS_GIGANTE_GASOSO if corpo.tipo == "gasoso" else FAIXAS_ROCHOSO
        turbulencia = (ruido - 0.5) * INTENSIDADE_TURBULENCIA
        mistura = 0.5 + 0.5 * np.sin(latitude * np.pi * frequencia + turbulencia)
    else:
        # Manchas irregulares: continentes (Terra), crateras (Mercúrio/Marte),
        # granulação (Sol).
        mistura = np.clip((ruido - 0.46) * 5.0, 0.0, 1.0)

    base = np.array(corpo.cor_base, dtype=np.float64)
    secundaria = np.array(corpo.cor_secundaria, dtype=np.float64)
    detalhe = np.array(corpo.cor_detalhe, dtype=np.float64)

    cor = base[None, None, :] * (1.0 - mistura[..., None]) + secundaria[
        None, None, :
    ] * mistura[..., None]

    # Realces finos (nuvens, cristas, plumas).
    realce = np.clip((ruido_fino - 0.68) * 2.4, 0.0, 1.0)[..., None]
    cor = cor * (1.0 - realce * 0.55) + detalhe[None, None, :] * realce * 0.55

    # Tempestade oval característica (Júpiter, Netuno).
    if corpo.cor_tempestade is not None:
        distancia = ((latitude + 0.30) / 0.16) ** 2 + ((longitude - 0.35) / 0.09) ** 2
        peso = np.clip(1.0 - distancia, 0.0, 1.0) ** 0.5
        tempestade = np.array(corpo.cor_tempestade, dtype=np.float64)
        cor = (
            cor * (1.0 - peso[..., None])
            + tempestade[None, None, :] * peso[..., None]
        )

    # Calotas polares.
    if corpo.nome in _CORPOS_COM_CALOTAS:
        calota = np.clip((np.abs(latitude) - 0.82) * 6.0, 0.0, 1.0)
        calota = np.broadcast_to(calota, (_ALTURA_TIRA, _LARGURA_TIRA))[..., None]
        cor = cor * (1.0 - calota) + np.array([238.0, 244.0, 250.0]) * calota

    return np.clip(cor, 0.0, 255.0)


def _mapa_esferico() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Índices de amostragem da tira para projetar meia esfera no disco.

    Devolve (linhas, colunas, brilho, alpha). O ``arcsin`` nos dois eixos faz a
    textura comprimir perto da borda, como numa esfera de verdade.
    """
    coord_y, coord_x = np.mgrid[0:_TAM_TEX, 0:_TAM_TEX].astype(np.float64)
    u = (coord_x - _RAIO_TEX + 0.5) / _RAIO_TEX
    v = (coord_y - _RAIO_TEX + 0.5) / _RAIO_TEX
    raio_quadrado = u * u + v * v

    latitude = np.arcsin(np.clip(v, -1.0, 1.0))
    cos_latitude = np.maximum(np.cos(latitude), 1e-6)
    longitude = np.arcsin(np.clip(u / cos_latitude, -1.0, 1.0))

    # O hemisfério visível cobre metade da tira.
    colunas = ((longitude / np.pi + 0.5) * (_LARGURA_TIRA // 2)).astype(np.int32)
    linhas = np.clip(
        ((latitude / np.pi + 0.5) * _ALTURA_TIRA).astype(np.int32), 0, _ALTURA_TIRA - 1
    )

    # Escurecimento de limbo + borda suave de 1 px (antisserrilhado barato).
    brilho = 0.45 + 0.55 * np.clip(1.0 - raio_quadrado, 0.0, 1.0) ** 0.35
    alpha = np.clip((1.0 - raio_quadrado) * _RAIO_TEX * 0.9, 0.0, 1.0) * 255.0
    return linhas, colunas, brilho, alpha


def _superficie_rgba(matriz: np.ndarray) -> pygame.Surface:
    """Converte uma matriz (altura, largura, 4) uint8 em Surface com alpha."""
    dados = np.ascontiguousarray(matriz, dtype=np.uint8)
    altura, largura = dados.shape[0], dados.shape[1]
    superficie = pygame.image.frombuffer(dados.tobytes(), (largura, altura), "RGBA")
    return superficie.convert_alpha()


def _quadros_rotacao(corpo: CorpoCeleste, mapa: tuple) -> list[pygame.Surface]:
    """Pré-renderiza o disco do corpo em cada fase de rotação."""
    linhas, colunas, brilho, alpha = mapa
    tira = _tira_equirretangular(corpo)

    # O Sol brilha por conta própria: quase sem escurecimento de limbo.
    if corpo.eh_sol:
        brilho = 0.86 + 0.14 * brilho

    quadros: list[pygame.Surface] = []
    for indice in range(QUADROS_ROTACAO):
        deslocamento = int(indice / QUADROS_ROTACAO * _LARGURA_TIRA)
        colunas_giradas = (colunas + deslocamento) % _LARGURA_TIRA
        rgb = tira[linhas, colunas_giradas] * brilho[..., None]
        rgba = np.empty((_TAM_TEX, _TAM_TEX, 4), dtype=np.uint8)
        rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        rgba[..., 3] = alpha.astype(np.uint8)
        quadros.append(_superficie_rgba(rgba))
    return quadros


def _superficies_sombra(mapa: tuple) -> list[pygame.Surface]:
    """Terminador dia/noite pré-rotacionado, um quadro a cada N graus."""
    _, _, _, alpha_disco = mapa
    coord_y, coord_x = np.mgrid[0:_TAM_TEX, 0:_TAM_TEX].astype(np.float64)
    u = (coord_x - _RAIO_TEX + 0.5) / _RAIO_TEX

    # Escuro no lado +x; a rotação leva esse lado para a direção oposta ao Sol.
    escuridao = np.clip((u + 0.15) * 1.5, 0.0, 1.0) ** 1.2
    rgba = np.zeros((_TAM_TEX, _TAM_TEX, 4), dtype=np.uint8)
    rgba[..., 3] = (escuridao * (alpha_disco / 255.0) * ALPHA_SOMBRA_MAX).astype(
        np.uint8
    )
    base = _superficie_rgba(rgba)

    quadros: list[pygame.Surface] = []
    for graus in range(0, 360, PASSO_ANGULO_SOMBRA_GRAUS):
        girada = pygame.transform.rotate(base, graus)
        recorte = pygame.Surface((_TAM_TEX, _TAM_TEX), pygame.SRCALPHA)
        # Recorta de volta ao quadrado do disco: a rotação é em torno do centro.
        destino = girada.get_rect(center=(_RAIO_TEX, _RAIO_TEX))
        recorte.blit(girada, destino.topleft)
        quadros.append(recorte.convert_alpha())
    return quadros


def _semente_do_nome(nome: str) -> int:
    """Semente estável a partir do nome (FNV-1a de 32 bits).

    As luas não têm ``indice_gesto`` para semear o ruído como os 9 corpos, e
    usar a posição no catálogo faria a textura de todas mudar ao inserir uma lua
    nova no meio da lista.
    """
    hash_ = 2166136261
    for caractere in nome:
        hash_ = ((hash_ ^ ord(caractere)) * 16777619) & 0xFFFFFFFF
    return hash_


def _sprite_lua(lua: LuaMenor) -> pygame.Surface:
    """Disco esférico de uma lua: manchas de terreno + escurecimento de limbo.

    É o mesmo princípio dos planetas, sem a tira equirretangular: as luas não
    têm rotação própria animada (todas as grandes são síncronas — mostram
    sempre a mesma face ao planeta), então projetar um mapa que gira seria custo
    puro. O que falta para o disco parecer esférico é o escurecimento na borda,
    e isso o ruído sozinho não dá.
    """
    rng = np.random.default_rng(SEMENTE_ALEATORIA + _semente_do_nome(lua.nome))
    ruido = _ruido_suave(
        rng, _TAM_TEX_LUA, _TAM_TEX_LUA, escala=ESCALA_RUIDO_LUA
    )
    # Normalização: a soma de oitavas puxa o ruído para perto de 0,5, e sem
    # esticar de volta para [0, 1] o terreno usa só o miolo da paleta. Era isso
    # que fazia Jápeto — a lua de DOIS hemisférios, um branco e um preto — sair
    # como um bege uniforme, igual a todas as outras.
    minimo = float(ruido.min())
    amplitude_ruido = float(ruido.max()) - minimo
    if amplitude_ruido > 1e-6:
        ruido = (ruido - minimo) / amplitude_ruido

    coord_y, coord_x = np.mgrid[0:_TAM_TEX_LUA, 0:_TAM_TEX_LUA].astype(np.float64)
    u = (coord_x - _RAIO_TEX_LUA + 0.5) / _RAIO_TEX_LUA
    v = (coord_y - _RAIO_TEX_LUA + 0.5) / _RAIO_TEX_LUA
    raio_quadrado = u * u + v * v

    base = np.array(lua.cor, dtype=np.float64)
    clara = np.array(lua.realce, dtype=np.float64)
    escura = np.array(lua.sombra, dtype=np.float64)

    # Terreno: o ruído puxa para o tom claro acima de 0,5 e para o escuro
    # abaixo. Centrado, para que a cor média do disco continue sendo `cor`.
    desvio = (ruido - 0.5) * 2.0 * CONTRASTE_TERRENO_LUA
    peso_claro = np.clip(desvio, 0.0, 1.0)[..., None]
    peso_escuro = np.clip(-desvio, 0.0, 1.0)[..., None]
    cor = (
        base[None, None, :] * (1.0 - peso_claro - peso_escuro)
        + clara[None, None, :] * peso_claro
        + escura[None, None, :] * peso_escuro
    )

    brilho = 0.45 + 0.55 * np.clip(1.0 - raio_quadrado, 0.0, 1.0) ** 0.35
    # Mesma borda suave de 1 px dos planetas: antisserrilhado barato.
    alpha = np.clip((1.0 - raio_quadrado) * _RAIO_TEX_LUA * 0.9, 0.0, 1.0) * 255.0

    rgba = np.empty((_TAM_TEX_LUA, _TAM_TEX_LUA, 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(cor * brilho[..., None], 0, 255).astype(np.uint8)
    rgba[..., 3] = alpha.astype(np.uint8)
    return _superficie_rgba(rgba)


def _superficies_sombra_lua() -> list[pygame.Surface]:
    """Terminador dia/noite da lua, um quadro a cada 360/N graus.

    Uma série só para TODAS as luas: a sombra não depende da cor, e 22 cópias
    idênticas na memória não comprariam nada.
    """
    coord_y, coord_x = np.mgrid[0:_TAM_TEX_LUA, 0:_TAM_TEX_LUA].astype(np.float64)
    u = (coord_x - _RAIO_TEX_LUA + 0.5) / _RAIO_TEX_LUA
    v = (coord_y - _RAIO_TEX_LUA + 0.5) / _RAIO_TEX_LUA
    disco = np.clip((1.0 - (u * u + v * v)) * _RAIO_TEX_LUA * 0.9, 0.0, 1.0)

    # Escuro no lado +x; a rotação leva esse lado para a direção oposta ao Sol.
    escuridao = np.clip((u + 0.15) * 1.5, 0.0, 1.0) ** 1.2
    rgba = np.zeros((_TAM_TEX_LUA, _TAM_TEX_LUA, 4), dtype=np.uint8)
    rgba[..., 3] = (escuridao * disco * ALPHA_SOMBRA_LUA).astype(np.uint8)
    base = _superficie_rgba(rgba)

    quadros: list[pygame.Surface] = []
    for indice in range(QUADROS_ILUMINACAO_LUA):
        graus = indice * 360.0 / QUADROS_ILUMINACAO_LUA
        girada = pygame.transform.rotate(base, graus)
        recorte = pygame.Surface((_TAM_TEX_LUA, _TAM_TEX_LUA), pygame.SRCALPHA)
        destino = girada.get_rect(center=(_RAIO_TEX_LUA, _RAIO_TEX_LUA))
        recorte.blit(girada, destino.topleft)
        quadros.append(recorte.convert_alpha())
    return quadros


def _criar_anel(
    fator_interno: float,
    fator_externo: float,
    achatamento: float,
    cor: tuple[int, int, int],
    inclinacao_graus: float,
) -> pygame.Surface:
    """Gera um anel elíptico com faixas e divisões, já inclinado."""
    largura = int(_RAIO_TEX * fator_externo * 2)
    altura = max(4, int(largura * achatamento))
    coord_y, coord_x = np.mgrid[0:altura, 0:largura].astype(np.float64)
    u = (coord_x - largura / 2) / (largura / 2) * fator_externo
    v = (coord_y - altura / 2) / (altura / 2) * fator_externo
    raio = np.sqrt(u * u + v * v)

    dentro = (raio >= fator_interno) & (raio <= fator_externo)
    faixa = 0.55 + 0.45 * np.sin(raio * 34.0)
    # Divisão de Cassini: uma lacuna escura no meio do anel.
    meio = (fator_interno + fator_externo) / 2.0
    lacuna = np.clip(np.abs(raio - meio) * 26.0, 0.0, 1.0)
    intensidade = np.where(dentro, faixa * lacuna, 0.0)

    rgba = np.zeros((altura, largura, 4), dtype=np.uint8)
    rgba[..., 0] = cor[0]
    rgba[..., 1] = cor[1]
    rgba[..., 2] = cor[2]
    rgba[..., 3] = (intensidade * ALPHA_ANEL_MAX).astype(np.uint8)
    superficie = _superficie_rgba(rgba)
    if inclinacao_graus:
        superficie = pygame.transform.rotate(superficie, inclinacao_graus)
    return superficie.convert_alpha()


def _criar_halo() -> pygame.Surface:
    """Brilho aditivo em volta do Sol (blit com BLEND_RGB_ADD)."""
    tamanho = int(_TAM_TEX * FATOR_HALO_SOL)
    coord_y, coord_x = np.mgrid[0:tamanho, 0:tamanho].astype(np.float64)
    centro = tamanho / 2.0
    raio = np.sqrt((coord_x - centro) ** 2 + (coord_y - centro) ** 2) / centro
    queda = np.clip(1.0 - raio, 0.0, 1.0) ** 3.0
    intensidade = queda * (ALPHA_HALO_SOL / 255.0)
    rgba = np.zeros((tamanho, tamanho, 4), dtype=np.uint8)
    for canal in range(3):
        rgba[..., canal] = (intensidade * COR_HALO_SOL[canal]).astype(np.uint8)
    rgba[..., 3] = 255
    return _superficie_rgba(rgba)


# ---------------------------------------------------------------------------
# Renderizador
# ---------------------------------------------------------------------------
class Renderizador:
    """Mantém os recursos pré-renderizados e desenha um frame da cena."""

    def __init__(
        self,
        fonte_rotulo: pygame.font.Font,
        largura: int = LARGURA_JANELA,
        altura: int = ALTURA_JANELA,
    ) -> None:
        self._fonte_rotulo = fonte_rotulo
        self._largura = largura
        self._altura = altura
        mapa = _mapa_esferico()

        self._quadros: dict[str, list[pygame.Surface]] = {
            corpo.nome: _quadros_rotacao(corpo, mapa) for corpo in CORPOS
        }
        self._sombras = _superficies_sombra(mapa)
        self._halo = _criar_halo()
        self._aneis: dict[str, tuple[pygame.Surface, str]] = {
            "Saturno": (
                _criar_anel(
                    FATOR_ANEL_INTERNO,
                    FATOR_ANEL_EXTERNO,
                    ACHATAMENTO_ANEL,
                    COR_ANEL_SATURNO,
                    INCLINACAO_ANEL_GRAUS,
                ),
                "horizontal",
            ),
            # Urano quase deitado: o anel aparece "de pé" e a divisão é vertical.
            "Urano": (
                _criar_anel(
                    FATOR_ANEL_URANO_INTERNO,
                    FATOR_ANEL_URANO_EXTERNO,
                    ACHATAMENTO_ANEL_URANO,
                    COR_ANEL_URANO,
                    INCLINACAO_ANEL_URANO_GRAUS,
                ),
                "vertical",
            ),
        }
        # Um sprite por lua do catálogo, gerado uma vez. São 22 discos de 40x40
        # — menos memória que UM quadro de rotação de planeta.
        self._sprites_lua: dict[str, pygame.Surface] = {}
        for corpo in CORPOS:
            for lua in luas_do_planeta(corpo.nome):
                if lua.nome not in self._sprites_lua:
                    self._sprites_lua[lua.nome] = _sprite_lua(lua)
        self._sombras_lua = _superficies_sombra_lua()

        self._asteroides = self._criar_asteroides()
        self._estrelas_normalizadas = self._criar_estrelas()
        self._estrelas: list[list[tuple[int, int, int, tuple[int, int, int]]]] = []
        self._camada_orbitas = pygame.Surface((largura, altura), pygame.SRCALPHA)
        self._posicionar_estrelas()
        self._cache_escala: dict[tuple, pygame.Surface] = {}
        # Pastilhas do cinturão, por (lado, alpha). Antes cada asteroide criava
        # uma Surface NOVA a cada frame: 340 alocações por quadro, 20 mil por
        # segundo, e o coletor pagando a conta no meio da animação.
        self._pastilhas: dict[tuple[int, int], pygame.Surface] = {}
        self._rotulos: dict[str, pygame.Surface] = {}
        for corpo in CORPOS:
            self._rotulos[corpo.nome] = self._rotulo_contornado(
                corpo.nome, COR_TEXTO_SECUNDARIO, ALPHA_ROTULO_CORPO
            )
        # Rótulos de lua: dois por lua (normal e em destaque), pré-renderizados.
        # Renderizar texto é a operação mais cara do pygame e antes acontecia a
        # cada frame, para cada lua visível.
        self._rotulos_lua: dict[tuple[str, bool], pygame.Surface] = {}
        for corpo in CORPOS:
            for lua in luas_do_planeta(corpo.nome):
                self._rotulos_lua[(lua.nome, True)] = self._rotulo_contornado(
                    lua.nome, COR_TEXTO, 255
                )
                self._rotulos_lua[(lua.nome, False)] = self._rotulo_contornado(
                    lua.nome, COR_TEXTO_SECUNDARIO, ALPHA_ROTULO_LUA
                )
        # Reaproveitada a cada frame para o antiempilhamento de rótulos.
        self._rotulos_desenhados: list[tuple[float, float]] = []

    # ------------------------------------------------------------- recursos
    def _rotulo_contornado(
        self, texto: str, cor: tuple[int, int, int], alpha: int
    ) -> pygame.Surface:
        """Texto com contorno escuro, pré-renderizado uma única vez.

        O contorno não é enfeite: o mesmo cinza de 14 px que se lê contra o
        campo de estrelas desaparece sobre o disco bege de Júpiter ou sobre os
        anéis de Saturno — exatamente onde os rótulos de lua caem.

        O pygame não tem ``strokeText``, então o contorno sai de oito cópias do
        texto deslocadas em volta. Como isto roda uma vez por rótulo na
        inicialização e nunca mais, o custo é irrelevante.
        """
        espessura = ESPESSURA_CONTORNO_ROTULO_PX
        frente = self._fonte_rotulo.render(texto, True, cor)
        fundo = self._fonte_rotulo.render(texto, True, COR_CONTORNO_ROTULO)
        largura = frente.get_width() + espessura * 2
        altura = frente.get_height() + espessura * 2
        camada = pygame.Surface((largura, altura), pygame.SRCALPHA)
        for dx in (-espessura, 0, espessura):
            for dy in (-espessura, 0, espessura):
                if dx or dy:
                    camada.blit(fundo, (espessura + dx, espessura + dy))
        camada.blit(frente, (espessura, espessura))
        # convert_alpha() ANTES do set_alpha: a conversão devolve uma Surface
        # nova, e o alfa global definido na antiga não viria junto.
        pronta = camada.convert_alpha()
        pronta.set_alpha(alpha)
        return pronta

    def _criar_asteroides(self) -> list[tuple[float, float, float, int]]:
        """Sorteia (raio, ângulo, brilho, tamanho) de cada asteroide.

        Semente fixa, como o campo de estrelas: o cinturão precisa ser o mesmo
        em toda execução. A densidade cai perto das bordas — no cinturão real as
        lacunas de Kirkwood e o próprio espalhamento deixam o miolo mais cheio.
        """
        rng = np.random.default_rng(SEMENTE_ALEATORIA + 977)
        interno, externo = faixa_do_cinturao()
        meio = (interno + externo) / 2.0
        largura = (externo - interno) / 2.0
        asteroides: list[tuple[float, float, float, int]] = []
        for _ in range(ASTEROIDES_DESENHADOS):
            # Distribuição triangular: mais denso no meio da faixa.
            desvio = (rng.random() + rng.random() - 1.0) * largura
            raio = meio + desvio
            angulo = rng.random() * 2.0 * math.pi
            brilho = rng.random() ** 1.4
            tamanho = 1 if rng.random() < 0.75 else 2
            asteroides.append((raio, angulo, brilho, tamanho))
        return asteroides

    def _criar_estrelas(
        self,
    ) -> list[list[tuple[float, float, int, tuple[int, int, int]]]]:
        """Camadas de estrelas (x, y normalizados, tamanho, cor) do parallax.

        As posições ficam em [0, 1) para o campo sobreviver a qualquer
        redimensionamento da janela sem precisar de novo sorteio.
        """
        rng = np.random.default_rng(SEMENTE_ALEATORIA)
        camadas = []
        for indice in range(CAMADAS_ESTRELAS):
            profundidade = (indice + 1) / CAMADAS_ESTRELAS
            estrelas = []
            for _ in range(ESTRELAS_POR_CAMADA):
                x = float(rng.random())
                y = float(rng.random())
                tamanho = 1 if profundidade < 0.7 else int(rng.integers(1, 3))
                brilho = int(70 + 150 * profundidade * rng.random())
                matiz = int(brilho * (0.90 + 0.10 * rng.random()))
                estrelas.append((x, y, tamanho, (matiz, matiz, min(255, brilho + 18))))
            camadas.append(estrelas)
        return camadas

    def _posicionar_estrelas(self) -> None:
        """Converte as estrelas normalizadas em pixels do tamanho atual."""
        self._estrelas = [
            [
                (int(x * self._largura), int(y * self._altura), tamanho, cor)
                for x, y, tamanho, cor in camada
            ]
            for camada in self._estrelas_normalizadas
        ]

    def redimensionar(self, largura: int, altura: int) -> None:
        """Reajusta as superfícies internas ao novo tamanho da janela."""
        if largura == self._largura and altura == self._altura:
            return
        self._largura = largura
        self._altura = altura
        self._camada_orbitas = pygame.Surface((largura, altura), pygame.SRCALPHA)
        self._posicionar_estrelas()

    def _escalar(self, chave: tuple, origem: pygame.Surface, tamanho: tuple[int, int]):
        """Escala com cache — o zoom só muda durante as transições."""
        cache = self._cache_escala.get(chave)
        if cache is not None:
            return cache
        if len(self._cache_escala) > _MAX_ENTRADAS_CACHE:
            self._cache_escala.clear()
        escalada = pygame.transform.smoothscale(origem, tamanho)
        self._cache_escala[chave] = escalada
        return escalada

    # -------------------------------------------------------------- desenho
    def desenhar(
        self,
        superficie: pygame.Surface,
        camera: Camera2D,
        posicoes: dict[str, tuple[float, float]],
        tempo_dias: float,
        corpo_focado: CorpoCeleste | None,
        luas_visiveis: bool = False,
        lua_destacada: str | None = None,
    ) -> None:
        """Desenha um frame completo da cena.

        ``lua_destacada`` é o NOME da lua em preview no modo lua. Ela ganha
        anel, disco maior e rótulo sempre visível — sem isso o usuário mostra o
        número e não tem como saber qual ponto na tela ele acabou de escolher.
        """
        superficie.fill(COR_FUNDO)
        self._rotulos_desenhados.clear()
        self._desenhar_estrelas(superficie, camera)
        self._desenhar_cinturao(superficie, camera, tempo_dias, corpo_focado)
        self._desenhar_orbitas(
            superficie, camera, posicoes, corpo_focado, luas_visiveis, lua_destacada
        )
        for corpo in CORPOS:
            # Satélites seguem a regra das luas menores: sumem na visão geral,
            # onde seriam 4 px em cima do planeta — e onde a órbita colidiria
            # com o vizinho. Quando o próprio satélite é o alvo, sempre aparece.
            if (
                corpo.eh_satelite
                and not luas_visiveis
                and camera.zoom < ZOOM_MINIMO_PARA_LUAS
                and (corpo_focado is None or corpo_focado.nome != corpo.nome)
            ):
                continue
            self._desenhar_corpo(
                superficie,
                camera,
                corpo,
                posicoes[corpo.nome],
                tempo_dias,
                corpo_focado,
            )
            if luas_visiveis:
                self._desenhar_luas(
                    superficie,
                    camera,
                    corpo,
                    posicoes[corpo.nome],
                    tempo_dias,
                    corpo_focado,
                    lua_destacada,
                )

    def _desenhar_cinturao(
        self,
        superficie: pygame.Surface,
        camera: Camera2D,
        tempo_dias: float,
        corpo_focado: CorpoCeleste | None,
    ) -> None:
        """Cinturão de asteroides entre Marte e Júpiter.

        Desenhado como pontos com raio e brilho sorteados uma vez (semente fixa)
        e girados em bloco. Simular a órbita de cada asteroide não mudaria nada
        na tela e custaria uma volta trigonométrica por partícula por frame.
        """
        giro = angulo_do_cinturao(tempo_dias)
        # Durante o foco em um corpo, o cinturão recua junto com as órbitas.
        alpha_max = ALPHA_ASTEROIDE_MAX if corpo_focado is None else ALPHA_ASTEROIDE_MIN
        faixa = alpha_max - ALPHA_ASTEROIDE_MIN
        escala_lado = min(2.0, camera.zoom)
        # A projeção é feita à mão dentro do laço: `mundo_para_tela` monta uma
        # tupla nova, e 340 tuplas descartadas por frame são 20 mil por segundo.
        # Mesma conta de `Camera2D.mundo_para_tela`, com as dimensões da CÂMERA
        # (não as do renderizador) para não divergir dela em nenhum frame.
        zoom = camera.zoom
        base_x = camera.largura / 2 + camera.deslocamento_x - camera.centro_x * zoom
        base_y = camera.altura / 2 - camera.centro_y * zoom
        limite_x = self._largura + 8
        limite_y = self._altura + 8

        for raio, angulo, brilho, tamanho in self._asteroides:
            a = angulo + giro
            tela_x = raio * math.cos(a) * zoom + base_x
            if tela_x < -8 or tela_x > limite_x:
                continue
            tela_y = raio * math.sin(a) * zoom + base_y
            if tela_y < -8 or tela_y > limite_y:
                continue
            # O alfa é quantizado em passos de 8 para que a mesma pastilha sirva
            # a muitos asteroides: são ~24 Surfaces no cache em vez de uma nova
            # por partícula por frame, e a diferença entre dois passos vizinhos
            # é de 3% de opacidade num ponto de 1 px.
            alpha = int(ALPHA_ASTEROIDE_MIN + brilho * faixa) & ~7
            lado = max(1, int(tamanho * escala_lado))
            pastilha = self._pastilhas.get((lado, alpha))
            if pastilha is None:
                pastilha = pygame.Surface((lado, lado), pygame.SRCALPHA)
                pastilha.fill((*COR_ASTEROIDE, max(0, min(255, alpha))))
                self._pastilhas[(lado, alpha)] = pastilha
            superficie.blit(pastilha, (int(tela_x), int(tela_y)))

    def _desenhar_luas(
        self,
        superficie: pygame.Surface,
        camera: Camera2D,
        corpo: CorpoCeleste,
        posicao: tuple[float, float],
        tempo_dias: float,
        corpo_focado: CorpoCeleste | None,
        lua_destacada: str | None = None,
    ) -> None:
        """Luas menores de um planeta: disco esférico, terminador e rótulo.

        A ÓRBITA não é desenhada aqui — ela vai junto com as demais em
        ``_desenhar_orbitas``, para o anel passar por trás do planeta como as
        órbitas dos planetas passam por trás do Sol.

        Cada lua sai como um sprite pré-renderizado, não como um círculo de cor
        chapada: com o disco liso, cinco luas de tons parecidos em volta de
        Saturno eram cinco pontos iguais, e não havia como dizer qual estava
        iluminada por qual lado.
        """
        luas = luas_do_planeta(corpo.nome)
        if not luas:
            return
        raio_planeta = raio_corpo_px(corpo)
        centro = camera.mundo_para_tela(posicao)
        # Descarte barato: com um planeta em foco, os outros oito estão quase
        # sempre fora da tela e as luas deles custariam dois blits cada. O 5 é o
        # teto de `raio_orbita_px` no catálogo (4,1 em Jápeto) com folga.
        margem = camera.escalar(raio_planeta * 5.0) + 80.0
        if (
            centro[0] < -margem
            or centro[0] > self._largura + margem
            or centro[1] < -margem
            or centro[1] > self._altura + margem
        ):
            return

        esmaecido = corpo_focado is not None and corpo_focado.nome != corpo.nome
        alpha_lua = ALPHA_CORPO_ESMAECIDO if esmaecido else 255
        # Uma direção de luz por PLANETA, não por lua: a lua mais externa fica a
        # poucos pixels do planeta contra as centenas que os separam do Sol,
        # então o ângulo é o mesmo dentro de bem menos de um grau.
        graus_luz = math.degrees(angulo_iluminacao(posicao)) % 360.0
        indice_sombra = int(
            graus_luz / (360.0 / QUADROS_ILUMINACAO_LUA)
        ) % QUADROS_ILUMINACAO_LUA

        for lua in luas:
            destacada = lua.nome == lua_destacada
            # Comprimido na visão geral, aberto conforme a câmera aproxima.
            fator = fator_orbita_lua(lua.raio_orbita_px, camera.zoom, corpo.tem_aneis)
            posicao_lua = posicao_da_lua_menor(
                lua, posicao, raio_planeta, tempo_dias, fator
            )
            tela = camera.mundo_para_tela(posicao_lua)

            # O tamanho agora vem do diâmetro real (comprimido): Titã e
            # Ganimedes saem visivelmente maiores que Fobos, como deve ser.
            raio_desenho = max(1.4, camera.escalar(raio_lua_menor_px(lua)))
            # A destacada cresce: com 2 px ela some entre as vizinhas, e o ponto
            # do preview é justamente distinguir qual foi escolhida.
            if destacada:
                raio_desenho = max(raio_desenho * 1.7, 5.0)

            diametro = max(2, int(raio_desenho * 2))
            sprite = self._sprites_lua.get(lua.nome)
            canto = (tela[0] - diametro / 2, tela[1] - diametro / 2)
            if sprite is not None:
                disco = self._escalar(
                    ("lua", lua.nome, diametro), sprite, (diametro, diametro)
                )
                disco.set_alpha(255 if destacada else alpha_lua)
                superficie.blit(disco, canto)
                # Terminador: só compensa acima de ~5 px de diâmetro. Abaixo
                # disso a sombra ocuparia meio pixel e o único efeito seria
                # escurecer a lua inteira.
                if diametro >= 5:
                    sombra = self._escalar(
                        ("sombra_lua", indice_sombra, diametro),
                        self._sombras_lua[indice_sombra],
                        (diametro, diametro),
                    )
                    sombra.set_alpha(255 if destacada else alpha_lua)
                    superficie.blit(sombra, canto)
            else:
                # Lua fora do catálogo pré-renderizado: o disco chapado serve.
                pygame.draw.circle(
                    superficie, lua.cor, (int(tela[0]), int(tela[1])), max(1, diametro // 2)
                )

            if destacada:
                # Anel em volta do disco, como a mira de um alvo.
                pygame.draw.circle(
                    superficie,
                    COR_DESTAQUE,
                    (int(tela[0]), int(tela[1])),
                    int(raio_desenho) + 5,
                    width=2,
                )

            # O nome só cabe quando o planeta está realmente próximo — mas o da
            # lua destacada aparece SEMPRE: sem ele o preview não diz qual lua é.
            mostrar = destacada or (
                not esmaecido
                and camera.zoom >= ZOOM_MINIMO_PARA_LUAS * 1.6
                and self._cabe_rotulo(tela)
            )
            if not mostrar:
                continue
            rotulo = self._rotulos_lua.get((lua.nome, destacada))
            if rotulo is None:
                continue
            superficie.blit(
                rotulo,
                (
                    tela[0] + raio_desenho + (7 if destacada else 5),
                    tela[1] - rotulo.get_height() / 2,
                ),
            )
            self._rotulos_desenhados.append(tela)

    def _cabe_rotulo(self, ponto: tuple[float, float]) -> bool:
        """Há espaço para mais um nome neste ponto da tela?

        Sem esta checagem, um planeta com cinco luas próximas empilhava cinco
        nomes na mesma faixa de pixels — e o resultado não é "cinco nomes
        densos", é zero nome legível. Omitir os que colidem deixa pelo menos um
        ser lido.
        """
        for anterior in self._rotulos_desenhados:
            if (
                abs(anterior[0] - ponto[0]) < DISTANCIA_MINIMA_ROTULO_LUA_PX
                and abs(anterior[1] - ponto[1]) < DISTANCIA_MINIMA_ROTULO_LUA_PX
            ):
                return False
        return True

    def corpo_no_ponto(
        self,
        camera: Camera2D,
        posicoes: dict[str, tuple[float, float]],
        ponto: tuple[float, float],
    ) -> CorpoCeleste | None:
        """Corpo cujo disco contém o ponto de tela (usado no toque/clique).

        Porte de ``corpoNoPonto`` da versão web, com o mesmo raio mínimo de 22
        px: na visão geral Mercúrio tem 3 px de raio na tela e seria impossível
        de acertar com o dedo. O piso vale como área de toque, não como desenho.

        Quando dois alvos se sobrepõem (uma lua sobre o planeta, por exemplo)
        vence o de centro mais próximo do clique.
        """
        escolhido: CorpoCeleste | None = None
        menor_distancia = float("inf")
        for corpo in CORPOS:
            centro = camera.mundo_para_tela(posicoes[corpo.nome])
            raio = max(22.0, camera.escalar(raio_corpo_px(corpo)))
            distancia = math.hypot(centro[0] - ponto[0], centro[1] - ponto[1])
            if distancia <= raio and distancia < menor_distancia:
                menor_distancia = distancia
                escolhido = corpo
        return escolhido

    def _desenhar_estrelas(self, superficie: pygame.Surface, camera: Camera2D) -> None:
        """Campo de estrelas com deslocamento proporcional à profundidade."""
        for indice, estrelas in enumerate(self._estrelas):
            fator = FATOR_PARALLAX[min(indice, len(FATOR_PARALLAX) - 1)]
            desloc_x = int(-camera.centro_x * fator * camera.zoom) % self._largura
            desloc_y = int(-camera.centro_y * fator * camera.zoom) % self._altura
            for x, y, tamanho, cor in estrelas:
                px = (x + desloc_x) % self._largura
                py = (y + desloc_y) % self._altura
                superficie.fill(cor, (px, py, tamanho, tamanho))

    def _desenhar_orbitas(
        self,
        superficie: pygame.Surface,
        camera: Camera2D,
        posicoes: dict[str, tuple[float, float]],
        corpo_focado: CorpoCeleste | None,
        luas_visiveis: bool = False,
        lua_destacada: str | None = None,
    ) -> None:
        """Círculos orbitais; os não focados ficam tênues durante um foco."""
        self._camada_orbitas.fill((0, 0, 0, 0))
        centro_sol = camera.mundo_para_tela((0.0, 0.0))
        desenhou = False
        if luas_visiveis:
            desenhou = self._desenhar_orbitas_de_luas(
                camera, posicoes, corpo_focado, lua_destacada
            )
        for corpo in CORPOS:
            if corpo.eh_sol:
                continue

            if corpo.eh_satelite:
                # Com o modo luas desligado, some de longe: a órbita cheia
                # (raio 28) invadiria Vênus, a 24,2 px da Terra. Com o modo
                # ligado ela aparece comprimida — o usuário pediu para ver.
                if not luas_visiveis and camera.zoom < ZOOM_MINIMO_PARA_LUAS:
                    continue
                # `orbita_em_torno_de` é str | None no catálogo; o `or ""` evita
                # passar None para o dict.get (que o verificador de tipos recusa)
                # e cai no `continue` logo abaixo, que já é o comportamento certo.
                pos_pai = posicoes.get(corpo.orbita_em_torno_de or "")
                pai = next(
                    (c for c in CORPOS if c.nome == corpo.orbita_em_torno_de), None
                )
                if not pos_pai or pai is None:
                    continue
                centro = camera.mundo_para_tela(pos_pai)
                # Mesmo fator adaptativo das luas menores: comprimido de longe.
                fator_lua = RAIO_ORBITA_LUA_PX / raio_corpo_px(pai)
                raio_mundo = raio_corpo_px(pai) * fator_orbita_lua(
                    fator_lua, camera.zoom, pai.tem_aneis
                )
            else:
                centro = centro_sol
                raio_mundo = raio_orbital_px(corpo.distancia_ua)

            raio = camera.escalar(raio_mundo)
            if raio < 2.0 or raio > RAIO_ORBITA_MAX_DESENHAVEL_PX:
                continue
            if corpo_focado is None:
                cor, alpha = COR_ORBITA, ALPHA_ORBITA_NORMAL
            elif corpo_focado.nome in (corpo.nome, corpo.orbita_em_torno_de):
                cor, alpha = COR_ORBITA_FOCADA, ALPHA_ORBITA_FOCADA
            else:
                cor, alpha = COR_ORBITA, ALPHA_ORBITA_TENUE
            pygame.draw.circle(
                self._camada_orbitas,
                (*cor, alpha),
                (int(centro[0]), int(centro[1])),
                int(raio),
                width=1,
            )
            desenhou = True
        if desenhou:
            superficie.blit(self._camada_orbitas, (0, 0))

    def _desenhar_orbitas_de_luas(
        self,
        camera: Camera2D,
        posicoes: dict[str, tuple[float, float]],
        corpo_focado: CorpoCeleste | None,
        lua_destacada: str | None,
    ) -> bool:
        """Anéis orbitais das luas, na MESMA camada das demais órbitas.

        Ficam antes dos planetas de propósito: assim o anel passa por trás do
        disco do planeta, do mesmo jeito que a órbita de Mercúrio passa por trás
        do Sol. Antes eram desenhados depois, e o traço cruzava o planeta por
        cima — o que lia como um anel de Saturno extra em volta de Júpiter.

        Reaproveitar ``_camada_orbitas`` também elimina as ~22 Surfaces que
        antes nasciam e morriam a cada frame, uma por órbita de lua.

        Devolve True se desenhou alguma coisa (a camada só é blitada se sim).
        """
        desenhou = False
        for corpo in CORPOS:
            luas = luas_do_planeta(corpo.nome)
            if not luas:
                continue
            posicao = posicoes.get(corpo.nome)
            if posicao is None:
                continue

            raio_planeta = raio_corpo_px(corpo)
            centro = camera.mundo_para_tela(posicao)
            margem = camera.escalar(raio_planeta * 5.0) + 80.0
            if (
                centro[0] < -margem
                or centro[0] > self._largura + margem
                or centro[1] < -margem
                or centro[1] > self._altura + margem
            ):
                continue
            esmaecido = corpo_focado is not None and corpo_focado.nome != corpo.nome

            for lua in luas:
                # Comprimido na visão geral, aberto conforme a câmera aproxima.
                fator = fator_orbita_lua(
                    lua.raio_orbita_px, camera.zoom, corpo.tem_aneis
                )
                raio_orbita = camera.escalar(raio_planeta * fator)
                if raio_orbita <= 3:
                    continue
                if lua.nome == lua_destacada:
                    # A órbita da lua escolhida acende na cor DELA: é o que liga
                    # o número mostrado com a mão ao ponto na tela.
                    cor_orbita, alpha_orbita, espessura = lua.cor, 190, 2
                else:
                    cor_orbita = COR_ORBITA_LUA
                    alpha_orbita = 20 if esmaecido else ALPHA_ORBITA_LUA
                    espessura = 1
                pygame.draw.circle(
                    self._camada_orbitas,
                    (*cor_orbita, alpha_orbita),
                    (int(centro[0]), int(centro[1])),
                    int(raio_orbita),
                    width=espessura,
                )
                desenhou = True
        return desenhou

    def _desenhar_corpo(
        self,
        superficie: pygame.Surface,
        camera: Camera2D,
        corpo: CorpoCeleste,
        posicao: tuple[float, float],
        tempo_dias: float,
        corpo_focado: CorpoCeleste | None,
    ) -> None:
        """Desenha halo, anéis, disco, terminador, rótulo e destaque de foco."""
        centro = camera.mundo_para_tela(posicao)
        raio_tela = camera.escalar(raio_corpo_px(corpo))
        focado = corpo_focado is not None and corpo_focado.nome == corpo.nome

        # Descarte barato: fora da janela e sem foco, nem desenha.
        margem = raio_tela * FATOR_ANEL_EXTERNO + 60
        if not focado and (
            centro[0] < -margem
            or centro[0] > self._largura + margem
            or centro[1] < -margem
            or centro[1] > self._altura + margem
        ):
            return

        alpha = 255 if (corpo_focado is None or focado) else ALPHA_CORPO_ESMAECIDO
        diametro = max(2, int(raio_tela * 2))

        # O halo é aditivo: se o Sol está esmaecido por outro foco, some.
        if corpo.eh_sol and alpha >= 255:
            self._desenhar_halo(superficie, centro, raio_tela)

        anel = self._aneis.get(corpo.nome)
        if anel is not None:
            self._desenhar_anel(
                superficie, centro, raio_tela, corpo.nome, anel, alpha, frente=False
            )
        if corpo.nome == "Urano":
            self._desenhar_eixo_urano(superficie, centro, raio_tela, alpha)

        # Disco com a fase de rotação corrente.
        quadros = self._quadros[corpo.nome]
        fase = fase_rotacao(corpo, tempo_dias)
        indice = int(fase * QUADROS_ROTACAO) % QUADROS_ROTACAO
        disco = self._escalar(
            ("corpo", corpo.nome, indice, diametro),
            quadros[indice],
            (diametro, diametro),
        )
        disco.set_alpha(alpha)
        superficie.blit(disco, (centro[0] - diametro / 2, centro[1] - diametro / 2))

        # Terminador: o lado oposto ao Sol fica na sombra (o Sol não tem noite).
        if not corpo.eh_sol:
            graus = math.degrees(angulo_iluminacao(posicao)) % 360.0
            indice_sombra = int(graus / PASSO_ANGULO_SOMBRA_GRAUS) % len(self._sombras)
            sombra = self._escalar(
                ("sombra", indice_sombra, diametro),
                self._sombras[indice_sombra],
                (diametro, diametro),
            )
            sombra.set_alpha(alpha)
            superficie.blit(
                sombra, (centro[0] - diametro / 2, centro[1] - diametro / 2)
            )

        if anel is not None:
            self._desenhar_anel(
                superficie, centro, raio_tela, corpo.nome, anel, alpha, frente=True
            )

        if focado:
            self._desenhar_destaque(superficie, centro, raio_tela)
        elif corpo_focado is None:
            rotulo = self._rotulos[corpo.nome]
            superficie.blit(
                rotulo, (centro[0] - rotulo.get_width() / 2, centro[1] + raio_tela + 6)
            )

    def _desenhar_halo(
        self, superficie: pygame.Surface, centro: tuple[float, float], raio_tela: float
    ) -> None:
        """Coroa solar, somada ao fundo em vez de sobreposta."""
        tamanho = max(4, int(raio_tela * 2 * FATOR_HALO_SOL))
        halo = self._escalar(("halo", tamanho), self._halo, (tamanho, tamanho))
        superficie.blit(
            halo,
            (centro[0] - tamanho / 2, centro[1] - tamanho / 2),
            special_flags=pygame.BLEND_RGB_ADD,
        )

    def _desenhar_anel(
        self,
        superficie: pygame.Surface,
        centro: tuple[float, float],
        raio_tela: float,
        nome: str,
        anel: tuple[pygame.Surface, str],
        alpha: int,
        frente: bool,
    ) -> None:
        """Desenha metade do anel: atrás do planeta ou na frente dele."""
        origem, eixo = anel
        escala = (raio_tela * 2) / _TAM_TEX
        largura = max(4, int(origem.get_width() * escala))
        altura = max(2, int(origem.get_height() * escala))
        completo = self._escalar(
            ("anel", nome, largura, altura), origem, (largura, altura)
        )
        if eixo == "horizontal":
            # Metade de baixo passa na frente do planeta (está mais perto).
            recorte = (
                (0, altura // 2, largura, altura - altura // 2)
                if frente
                else (0, 0, largura, altura // 2)
            )
            destino = (
                centro[0] - largura / 2,
                centro[1] - altura / 2 + (altura // 2 if frente else 0),
            )
        else:
            recorte = (
                (largura // 2, 0, largura - largura // 2, altura)
                if frente
                else (0, 0, largura // 2, altura)
            )
            destino = (
                centro[0] - largura / 2 + (largura // 2 if frente else 0),
                centro[1] - altura / 2,
            )
        completo.set_alpha(alpha)
        superficie.blit(completo, destino, recorte)

    def _desenhar_eixo_urano(
        self,
        superficie: pygame.Surface,
        centro: tuple[float, float],
        raio_tela: float,
        alpha: int,
    ) -> None:
        """Linha do eixo de rotação — Urano gira deitado (97,77°)."""
        comprimento = raio_tela * COMPRIMENTO_EIXO_URANO
        # O eixo é perpendicular ao plano do anel.
        angulo = math.radians(INCLINACAO_ANEL_URANO_GRAUS + 90.0)
        dx, dy = math.cos(angulo) * comprimento, -math.sin(angulo) * comprimento
        cor = (*COR_ANEL_URANO, alpha)
        camada = pygame.Surface(
            (int(abs(dx) * 2 + 8), int(abs(dy) * 2 + 8)), pygame.SRCALPHA
        )
        meio = (camada.get_width() / 2, camada.get_height() / 2)
        pygame.draw.line(
            camada,
            cor,
            (meio[0] - dx, meio[1] - dy),
            (meio[0] + dx, meio[1] + dy),
            max(1, int(raio_tela * 0.06)),
        )
        superficie.blit(
            camada, (centro[0] - meio[0], centro[1] - meio[1])
        )

    def _desenhar_destaque(
        self, superficie: pygame.Surface, centro: tuple[float, float], raio_tela: float
    ) -> None:
        """Anel pontilhado em volta do corpo focado."""
        raio = int(raio_tela + FOLGA_ANEL_DESTAQUE_PX)
        lado = raio * 2 + 8
        camada = pygame.Surface((lado, lado), pygame.SRCALPHA)
        pygame.draw.circle(
            camada, (*COR_ANEL_DESTAQUE, 170), (lado // 2, lado // 2), raio, width=2
        )
        superficie.blit(camada, (centro[0] - lado / 2, centro[1] - lado / 2))


__all__ = ["Renderizador"]
