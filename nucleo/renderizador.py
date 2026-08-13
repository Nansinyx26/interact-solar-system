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
    ALPHA_CORPO_ESMAECIDO,
    ALPHA_HALO_SOL,
    ALPHA_ORBITA_FOCADA,
    ALPHA_ORBITA_NORMAL,
    ALPHA_ORBITA_TENUE,
    ALPHA_ROTULO_CORPO,
    ALPHA_SOMBRA_MAX,
    ALTURA_JANELA,
    CAMADAS_ESTRELAS,
    COMPRIMENTO_EIXO_URANO,
    COR_ANEL_DESTAQUE,
    COR_ANEL_SATURNO,
    COR_ANEL_URANO,
    COR_FUNDO,
    COR_HALO_SOL,
    COR_ORBITA,
    COR_ORBITA_FOCADA,
    COR_TEXTO_SECUNDARIO,
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
    QUADROS_ROTACAO,
    RAIO_ORBITA_MAX_DESENHAVEL_PX,
    RAIO_TEXTURA_PX,
    SEMENTE_ALEATORIA,
)
from dados.planetas import CORPOS, CorpoCeleste
from nucleo.camera import Camera2D
from nucleo.orbita import (
    angulo_iluminacao,
    fase_rotacao,
    raio_corpo_px,
    raio_orbital_px,
)

# Dimensões das texturas em memória (independem do zoom: o escalonamento é feito
# na hora de desenhar).
_RAIO_TEX = RAIO_TEXTURA_PX
_TAM_TEX = _RAIO_TEX * 2
_LARGURA_TIRA = _RAIO_TEX * LARGURA_TIRA_EM_RAIOS
_ALTURA_TIRA = _TAM_TEX

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
    rng: np.random.Generator, altura: int, largura: int, oitavas: int = 3
) -> np.ndarray:
    """Ruído fractal em [0, 1], contínuo na emenda horizontal da tira."""
    total = np.zeros((altura, largura), dtype=np.float64)
    amplitude = 1.0
    soma_amplitudes = 0.0
    for oitava in range(oitavas):
        blocos = max(2, ESCALA_RUIDO_TEXTURA * (2**oitava))
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
        cor = cor * (1.0 - peso[..., None]) + tempestade[None, None, :] * peso[..., None]

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
        self._estrelas_normalizadas = self._criar_estrelas()
        self._estrelas: list[list[tuple[int, int, int, tuple[int, int, int]]]] = []
        self._camada_orbitas = pygame.Surface((largura, altura), pygame.SRCALPHA)
        self._posicionar_estrelas()
        self._cache_escala: dict[tuple, pygame.Surface] = {}
        self._rotulos: dict[str, pygame.Surface] = {}
        for corpo in CORPOS:
            rotulo = self._fonte_rotulo.render(corpo.nome, True, COR_TEXTO_SECUNDARIO)
            rotulo.set_alpha(ALPHA_ROTULO_CORPO)
            self._rotulos[corpo.nome] = rotulo

    # ------------------------------------------------------------- recursos
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
    ) -> None:
        """Desenha um frame completo da cena."""
        superficie.fill(COR_FUNDO)
        self._desenhar_estrelas(superficie, camera)
        self._desenhar_orbitas(superficie, camera, posicoes, corpo_focado)
        for corpo in CORPOS:
            self._desenhar_corpo(
                superficie, camera, corpo, posicoes[corpo.nome], tempo_dias, corpo_focado
            )

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
    ) -> None:
        """Círculos orbitais; os não focados ficam tênues durante um foco."""
        self._camada_orbitas.fill((0, 0, 0, 0))
        centro_sol = camera.mundo_para_tela((0.0, 0.0))
        desenhou = False
        for corpo in CORPOS:
            if corpo.eh_sol:
                continue

            if corpo.eh_satelite:
                pos_pai = posicoes.get(corpo.orbita_em_torno_de)
                if not pos_pai:
                    continue
                centro = camera.mundo_para_tela(pos_pai)
                raio_mundo = 28.0  # RAIO_ORBITA_LUA_PX
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
        indice = int(fase_rotacao(corpo, tempo_dias) * QUADROS_ROTACAO) % QUADROS_ROTACAO
        disco = self._escalar(
            ("corpo", corpo.nome, indice, diametro), quadros[indice], (diametro, diametro)
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
            superficie.blit(sombra, (centro[0] - diametro / 2, centro[1] - diametro / 2))

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
