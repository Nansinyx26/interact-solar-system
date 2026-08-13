"""Marca d'água "Nandev": a assinatura do autor sobre a cena.

Porte para pygame da marca d'água que o autor usa na web (`marcadagua.css`):
painel de vidro com um cubo wireframe em rotação, o texto "Desenvolvido por
Nandev" com gradiente animado, partículas em órbita e uma varredura holográfica.

O bloco é clicável, como o `<a>` do original: um clique abre o perfil do autor
no navegador padrão. É a única ação do app que sai da janela e só ocorre por
clique explícito — nada é acessado em segundo plano.
"""

from __future__ import annotations

import math
import webbrowser

import pygame

from config import (
    ALPHA_ASSINATURA_FACE_FRENTE,
    ALPHA_ASSINATURA_FACE_FUNDO,
    ALPHA_ASSINATURA_PAINEL,
    ALTURA_JANELA,
    ASSINATURA_ALTURA,
    ASSINATURA_ARESTA_CUBO_PX,
    ASSINATURA_DISTANCIA_PERSPECTIVA,
    ASSINATURA_ESPACO_INTERNO,
    ASSINATURA_LARGURA_MINIMA,
    ASSINATURA_NOME_DESTAQUE,
    ASSINATURA_NOME_RESTANTE,
    ASSINATURA_PADDING_X,
    ASSINATURA_PARTICULAS,
    ASSINATURA_PERIODO_BRILHO_S,
    ASSINATURA_PERIODO_CUBO_S,
    ASSINATURA_PERIODO_GRADIENTE_S,
    ASSINATURA_PERIODO_MESTRE_S,
    ASSINATURA_PERIODO_ORBITA_S,
    ASSINATURA_PERIODO_SCAN_S,
    ASSINATURA_RAIO_ORBITA_PX,
    ASSINATURA_SIMBOLO_CODIGO,
    ASSINATURA_TEXTO_PREFIXO,
    ASSINATURA_URL,
    COR_ASSINATURA_ACENTO,
    COR_ASSINATURA_BASE,
    COR_ASSINATURA_PRIMARIA,
    COR_ASSINATURA_SECUNDARIA,
    COR_ASSINATURA_TOPO,
    COR_PAINEL,
    COR_TEXTO,
    COR_TEXTO_SECUNDARIO,
    LARGURA_JANELA,
    MARGEM_HUD,
)
from ui.hud import Fontes

Cor = tuple[int, int, int]

# Altura reservada no layout: o bloco mais o respiro para quem vier acima dele.
ALTURA_BLOCO_ASSINATURA = ASSINATURA_ALTURA + MARGEM_HUD

# Vértices do cubo unitário centrado na origem: o bit 0 é x, o 1 é y e o 2 é z.
_VERTICES: tuple[tuple[float, float, float], ...] = tuple(
    (
        (1.0 if indice & 1 else -1.0) * 0.5,
        (1.0 if indice & 2 else -1.0) * 0.5,
        (1.0 if indice & 4 else -1.0) * 0.5,
    )
    for indice in range(8)
)

# Faces em ordem de contorno (cada uma com a cor que o CSS dá a ela). O eixo y
# cresce para baixo na tela, então "topo" é a face de y negativo.
_FACES: tuple[tuple[tuple[int, int, int, int], Cor], ...] = (
    ((4, 5, 7, 6), COR_ASSINATURA_PRIMARIA),    # frente
    ((0, 1, 3, 2), COR_ASSINATURA_SECUNDARIA),  # trás
    ((1, 5, 7, 3), COR_ASSINATURA_ACENTO),      # direita
    ((0, 4, 6, 2), COR_ASSINATURA_PRIMARIA),    # esquerda
    ((0, 1, 5, 4), COR_ASSINATURA_TOPO),        # topo
    ((2, 3, 7, 6), COR_ASSINATURA_BASE),        # base
)

# Frações onde entram as linhas internas do wireframe (só na face da frente).
_FRACOES_LINHAS_INTERNAS = (0.25, 0.5, 0.75)

# Instante em que TODAS as animações voltam ao início juntas. O relógio interno
# é reduzido por este valor para não perder precisão do float depois de horas
# rodando; usar qualquer número menor daria um salto no meio de algum ciclo.
# Os períodos são inteiros por construção, então o m.m.c. resolve — se algum
# virar fracionário, arredonde-o aqui de propósito ou o salto volta.
_CICLO_COMPLETO_S = float(
    math.lcm(
        int(ASSINATURA_PERIODO_CUBO_S),
        int(ASSINATURA_PERIODO_MESTRE_S),
        int(ASSINATURA_PERIODO_GRADIENTE_S),
        int(ASSINATURA_PERIODO_ORBITA_S),
        int(ASSINATURA_PERIODO_SCAN_S),
        int(ASSINATURA_PERIODO_BRILHO_S),
    )
)

# Partículas: (fração x, fração y, atraso em segundos) — os mesmos valores dos
# `nth-child` do CSS.
_PARTICULAS: tuple[tuple[float, float, float], ...] = (
    (0.10, 0.20, 0.0),
    (0.90, 0.60, 2.0),
    (0.30, 0.80, 4.0),
    (0.70, 0.40, 1.0),
    (0.60, 0.10, 3.0),
)[:ASSINATURA_PARTICULAS]


def _misturar(inicio: Cor, fim: Cor, fator: float) -> Cor:
    """Interpolação linear entre duas cores (``fator`` de 0 a 1)."""
    fator = max(0.0, min(1.0, fator))
    return (
        round(inicio[0] + (fim[0] - inicio[0]) * fator),
        round(inicio[1] + (fim[1] - inicio[1]) * fator),
        round(inicio[2] + (fim[2] - inicio[2]) * fator),
    )


def _gradiente_horizontal(largura: int, altura: int, fase: float) -> pygame.Surface:
    """Faixa primária → acento que desliza, para multiplicar sobre o texto.

    Reproduz o `nandev-gradient-shift`: a fase caminha com o tempo e o gradiente
    vai e volta entre as duas cores em vez de saltar na emenda.
    """
    faixa = pygame.Surface((max(1, largura), max(1, altura)))
    for x in range(faixa.get_width()):
        # Onda senoidal = ida e volta suave, sem costura visível no loop.
        posicao = (math.sin(2 * math.pi * (x / faixa.get_width() * 0.5 + fase)) + 1) / 2
        pygame.draw.line(
            faixa,
            _misturar(COR_ASSINATURA_PRIMARIA, COR_ASSINATURA_ACENTO, posicao),
            (x, 0),
            (x, faixa.get_height()),
        )
    return faixa


class MarcaDagua:
    """Assinatura animada do autor, ancorada no canto inferior direito."""

    def __init__(
        self,
        fontes: Fontes,
        largura: int = LARGURA_JANELA,
        altura: int = ALTURA_JANELA,
    ) -> None:
        self._largura = largura
        self._altura = altura
        self._tempo: float = 0.0
        self._sobre: bool = False

        # A caixa do cubo precisa caber o vértice mais distante depois da
        # projeção; senão a rotação corta os cantos contra a borda do painel.
        self._lado_caixa = self._calcular_caixa_cubo()

        # Os textos são fixos: renderiza uma vez e reaproveita todo frame.
        self._prefixo = fontes.mini.render(
            ASSINATURA_TEXTO_PREFIXO, True, COR_TEXTO_SECUNDARIO
        )
        self._prefixo_sobre = fontes.mini.render(
            ASSINATURA_TEXTO_PREFIXO, True, COR_TEXTO
        )
        self._destaque_mascara = fontes.mini.render(
            ASSINATURA_NOME_DESTAQUE, True, (255, 255, 255)
        )
        self._restante = fontes.mini.render(
            ASSINATURA_NOME_RESTANTE, True, COR_TEXTO
        )
        self._simbolo = fontes.mono.render(
            ASSINATURA_SIMBOLO_CODIGO, True, COR_ASSINATURA_PRIMARIA
        )

        largura_texto = (
            self._prefixo.get_width()
            + self._destaque_mascara.get_width()
            + self._restante.get_width()
        )
        self._largura_bloco = max(
            ASSINATURA_LARGURA_MINIMA,
            ASSINATURA_PADDING_X * 2
            + self._lado_caixa
            + ASSINATURA_ESPACO_INTERNO
            + largura_texto
            + ASSINATURA_ESPACO_INTERNO
            + self._simbolo.get_width(),
        )
        self._retangulo = pygame.Rect(0, 0, self._largura_bloco, ASSINATURA_ALTURA)
        self.posicionar(altura - MARGEM_HUD)

    @staticmethod
    def _calcular_caixa_cubo() -> int:
        """Lado da superfície do cubo, com folga para a projeção em perspectiva.

        O vértice do cubo fica sempre a `aresta·√3/2` da origem; o pior caso da
        projeção é o ponto que maximiza `r·f/(f−z)` sobre essa esfera, que cai
        em `z = R²/f`.
        """
        raio = ASSINATURA_ARESTA_CUBO_PX * math.sqrt(3) / 2
        distancia = ASSINATURA_ARESTA_CUBO_PX * ASSINATURA_DISTANCIA_PERSPECTIVA
        z_critico = raio * raio / distancia
        raio_projetado = (
            math.sqrt(raio * raio - z_critico * z_critico)
            * distancia
            / (distancia - z_critico)
        )
        return int(math.ceil(raio_projetado * 2)) + 2

    # ------------------------------------------------------------------ layout
    def redimensionar(self, largura: int, altura: int) -> None:
        """Reposiciona o bloco para o novo tamanho da janela."""
        self._largura = largura
        self._altura = altura

    def posicionar(self, base_y: int) -> None:
        """Ancora o bloco à direita, com a base em ``base_y``.

        Quem chama decide a base porque ela depende do preview da webcam estar
        visível ou não.
        """
        self._retangulo.bottomright = (self._largura - MARGEM_HUD, base_y)

    @property
    def retangulo(self) -> pygame.Rect:
        """Área ocupada pelo bloco na tela."""
        return self._retangulo.copy()

    # ----------------------------------------------------------------- entrada
    def tratar_evento(self, evento: pygame.event.Event) -> bool:
        """Trata mouse sobre o bloco. Devolve True quando consome o evento.

        Consumir o clique impede que ele também inicie um arrasto da câmera.
        """
        if evento.type == pygame.MOUSEMOTION:
            self._definir_hover(self._retangulo.collidepoint(evento.pos))
        elif (
            evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and self._retangulo.collidepoint(evento.pos)
        ):
            self._abrir_perfil()
            return True
        return False

    def _definir_hover(self, sobre: bool) -> None:
        """Liga/desliga o realce e o cursor de link (só na transição)."""
        if sobre == self._sobre:
            return
        self._sobre = sobre
        try:
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND if sobre else pygame.SYSTEM_CURSOR_ARROW
            )
        except pygame.error:
            # Alguns drivers de vídeo não expõem cursores do sistema; o realce
            # visual continua funcionando sem isso.
            pass

    def _abrir_perfil(self) -> None:
        """Abre o perfil do autor no navegador padrão."""
        try:
            webbrowser.open(ASSINATURA_URL)
        except (webbrowser.Error, OSError):
            # Sem navegador configurado não há o que fazer — e travar o app por
            # causa da assinatura seria o pior desfecho possível.
            pass

    # ------------------------------------------------------------- atualização
    def atualizar(self, dt: float, base_y: int) -> None:
        """Avança as animações e reancora o bloco."""
        self._tempo = (self._tempo + dt) % _CICLO_COMPLETO_S
        self.posicionar(base_y)

    # ----------------------------------------------------------------- desenho
    def desenhar(self, superficie: pygame.Surface) -> None:
        """Desenha o bloco completo sobre a cena."""
        camada = pygame.Surface(self._retangulo.size, pygame.SRCALPHA)
        self._desenhar_painel(camada)
        self._desenhar_particulas(camada)
        self._desenhar_scanlines(camada)

        centro_cubo = (
            ASSINATURA_PADDING_X + self._lado_caixa // 2,
            self._retangulo.height // 2,
        )
        self._desenhar_cubo(camada, centro_cubo)
        self._desenhar_texto(camada)
        superficie.blit(camada, self._retangulo.topleft)

    def _desenhar_painel(self, camada: pygame.Surface) -> None:
        """Fundo de vidro; sob o mouse ganha o tom da cor primária."""
        area = camada.get_rect()
        if self._sobre:
            fundo = (*_misturar(COR_PAINEL, COR_ASSINATURA_PRIMARIA, 0.18), 170)
            borda = (*COR_ASSINATURA_PRIMARIA, 170)
        else:
            fundo = (*COR_PAINEL, ALPHA_ASSINATURA_PAINEL)
            borda = (255, 255, 255, 30)
        pygame.draw.rect(camada, fundo, area, border_radius=8)
        pygame.draw.rect(camada, borda, area, width=1, border_radius=8)

    def _desenhar_scanlines(self, camada: pygame.Surface) -> None:
        """Varredura holográfica: linhas tênues descendo em loop."""
        fase = (self._tempo % ASSINATURA_PERIODO_SCAN_S) / ASSINATURA_PERIODO_SCAN_S
        deslocamento = int(fase * 4)
        cor = (*COR_ASSINATURA_PRIMARIA, 10)
        for y in range(deslocamento, camada.get_height(), 4):
            pygame.draw.line(camada, cor, (1, y), (camada.get_width() - 2, y))

    def _desenhar_particulas(self, camada: pygame.Surface) -> None:
        """Pontos em órbita, aparecendo e sumindo como no CSS."""
        largura, altura = camada.get_size()
        for fracao_x, fracao_y, atraso in _PARTICULAS:
            fase = ((self._tempo + atraso) % ASSINATURA_PERIODO_ORBITA_S) / (
                ASSINATURA_PERIODO_ORBITA_S
            )
            angulo = 2 * math.pi * fase
            x = fracao_x * largura + math.cos(angulo) * ASSINATURA_RAIO_ORBITA_PX
            y = fracao_y * altura + math.sin(angulo) * ASSINATURA_RAIO_ORBITA_PX * 0.6
            # Fade nas pontas do ciclo (0-10% e 90-100%), como o keyframe.
            visibilidade = min(1.0, min(fase, 1.0 - fase) / 0.1)
            pygame.draw.circle(
                camada,
                (*COR_ASSINATURA_PRIMARIA, int(200 * visibilidade)),
                (int(x), int(y)),
                1,
            )

    def _desenhar_cubo(self, camada: pygame.Surface, centro: tuple[int, int]) -> None:
        """Cubo wireframe: 6 faces coloridas, ordenadas da mais distante à frente."""
        giro = 2 * math.pi * (self._tempo / ASSINATURA_PERIODO_CUBO_S)
        mestre = 2 * math.pi * (self._tempo / ASSINATURA_PERIODO_MESTRE_S)
        pontos = [
            self._projetar(vertice, giro, giro + mestre, giro * 0.5)
            for vertice in _VERTICES
        ]

        # Painter's algorithm: a profundidade média da face define a ordem de
        # desenho e a opacidade, o que dá volume sem teste de oclusão.
        faces = sorted(
            (
                (sum(pontos[indice][1] for indice in indices) / 4, indices, cor)
                for indices, cor in _FACES
            ),
            key=lambda item: item[0],
        )
        menor = faces[0][0]
        faixa = max(1e-6, faces[-1][0] - menor)

        for profundidade, indices, cor in faces:
            fator = (profundidade - menor) / faixa
            alpha = int(
                ALPHA_ASSINATURA_FACE_FUNDO
                + (ALPHA_ASSINATURA_FACE_FRENTE - ALPHA_ASSINATURA_FACE_FUNDO) * fator
            )
            quadro = [
                (centro[0] + pontos[indice][0][0], centro[1] + pontos[indice][0][1])
                for indice in indices
            ]
            pygame.draw.lines(camada, (*cor, alpha), True, quadro)
            if fator >= 1.0:
                self._desenhar_linhas_internas(camada, quadro, cor, alpha)

    @staticmethod
    def _desenhar_linhas_internas(
        camada: pygame.Surface,
        quadro: list[tuple[float, float]],
        cor: Cor,
        alpha: int,
    ) -> None:
        """Grade interna da face da frente (as `inner-line` do CSS)."""
        origem, seguinte, oposto, ultimo = quadro
        for fracao in _FRACOES_LINHAS_INTERNAS:
            inicio = (
                origem[0] + (ultimo[0] - origem[0]) * fracao,
                origem[1] + (ultimo[1] - origem[1]) * fracao,
            )
            fim = (
                seguinte[0] + (oposto[0] - seguinte[0]) * fracao,
                seguinte[1] + (oposto[1] - seguinte[1]) * fracao,
            )
            pygame.draw.line(camada, (*cor, alpha // 2), inicio, fim)

    @staticmethod
    def _projetar(
        vertice: tuple[float, float, float], ax: float, ay: float, az: float
    ) -> tuple[tuple[float, float], float]:
        """Rotaciona o vértice nos três eixos e projeta em perspectiva.

        Devolve o ponto na tela e o z rotacionado (usado para ordenar as faces).
        """
        x = vertice[0] * ASSINATURA_ARESTA_CUBO_PX
        y = vertice[1] * ASSINATURA_ARESTA_CUBO_PX
        z = vertice[2] * ASSINATURA_ARESTA_CUBO_PX

        cos, sen = math.cos(ax), math.sin(ax)
        y, z = y * cos - z * sen, y * sen + z * cos
        cos, sen = math.cos(ay), math.sin(ay)
        x, z = x * cos + z * sen, -x * sen + z * cos
        cos, sen = math.cos(az), math.sin(az)
        x, y = x * cos - y * sen, x * sen + y * cos

        distancia = ASSINATURA_ARESTA_CUBO_PX * ASSINATURA_DISTANCIA_PERSPECTIVA
        escala = distancia / (distancia - z)
        return (x * escala, y * escala), z

    def _desenhar_texto(self, camada: pygame.Surface) -> None:
        """"Desenvolvido por Nandev </>" com o gradiente animado no "Nan"."""
        x = ASSINATURA_PADDING_X + self._lado_caixa + ASSINATURA_ESPACO_INTERNO
        centro_y = camada.get_height() // 2

        prefixo = self._prefixo_sobre if self._sobre else self._prefixo
        camada.blit(prefixo, prefixo.get_rect(midleft=(x, centro_y)))
        x += prefixo.get_width()

        destaque = self._destaque_mascara.copy()
        fase = (self._tempo % ASSINATURA_PERIODO_GRADIENTE_S) / (
            ASSINATURA_PERIODO_GRADIENTE_S
        )
        destaque.blit(
            _gradiente_horizontal(*destaque.get_size(), fase),
            (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        camada.blit(destaque, destaque.get_rect(midleft=(x, centro_y)))
        x += destaque.get_width()

        camada.blit(self._restante, self._restante.get_rect(midleft=(x, centro_y)))
        x += self._restante.get_width() + ASSINATURA_ESPACO_INTERNO

        # O `</>` pulsa entre 70% e 100% de opacidade (nandev-code-glow).
        brilho = (
            math.sin(2 * math.pi * self._tempo / ASSINATURA_PERIODO_BRILHO_S) + 1
        ) / 2
        simbolo = self._simbolo.copy()
        simbolo.set_alpha(int(178 + 77 * brilho))
        camada.blit(simbolo, simbolo.get_rect(midleft=(x, centro_y)))


__all__ = ["MarcaDagua", "ALTURA_BLOCO_ASSINATURA"]
