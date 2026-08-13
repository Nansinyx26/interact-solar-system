"""Câmera 2D com zoom/pan interpolados.

A câmera nunca "corta" para o alvo: toda troca dispara uma transição com easing
ease-in-out. Como o alvo continua orbitando durante a transição, o destino é
reavaliado a cada frame — o que interpolamos é o *progresso*, não um ponto fixo.
"""

from __future__ import annotations

from config import (
    ALTURA_JANELA,
    DESLOCAMENTO_FOCO_X_PX,
    DURACAO_TRANSICAO_S,
    LARGURA_JANELA,
    RAIO_ALVO_FOCO_PX,
    ZOOM_MAX,
    ZOOM_MIN,
    ZOOM_VISAO_GERAL,
)

# A visão geral é enquadrada para o tamanho inicial da janela; ao redimensionar,
# o zoom base acompanha a menor dimensão para o sistema continuar cabendo.
_ALTURA_REFERENCIA = ALTURA_JANELA


def suavizar(t: float) -> float:
    """Easing ease-in-out cúbico sobre t em [0, 1]."""
    t = min(1.0, max(0.0, t))
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


def _interpolar(inicio: float, fim: float, fator: float) -> float:
    """Interpolação linear simples."""
    return inicio + (fim - inicio) * fator


def zoom_para_focar(raio_corpo: float, escala_janela: float = 1.0) -> float:
    """Zoom que faz um corpo de raio informado ocupar ``RAIO_ALVO_FOCO_PX``.

    ``escala_janela`` mantém a proporção do corpo na tela quando a janela é
    redimensionada — os próprios limites de zoom acompanham essa escala.
    """
    if raio_corpo <= 0.0:
        return ZOOM_VISAO_GERAL * escala_janela
    alvo = RAIO_ALVO_FOCO_PX * escala_janela / raio_corpo
    return min(ZOOM_MAX * escala_janela, max(ZOOM_MIN * escala_janela, alvo))


class Camera2D:
    """Converte coordenadas de mundo em coordenadas de tela.

    Mantém centro (mundo), zoom e um deslocamento de tela usado para empurrar o
    corpo focado para longe da ficha lateral.
    """

    def __init__(
        self, largura: int = LARGURA_JANELA, altura: int = ALTURA_JANELA
    ) -> None:
        self.largura = largura
        self.altura = altura
        self.centro_x: float = 0.0
        self.centro_y: float = 0.0
        self.zoom: float = self.zoom_visao_geral()
        self.deslocamento_x: float = 0.0

        # Estado da transição em andamento.
        self._centro_x_inicial: float = 0.0
        self._centro_y_inicial: float = 0.0
        self._zoom_inicial: float = self.zoom
        self._deslocamento_inicial: float = 0.0
        self._progresso: float = 1.0

        # Destino corrente (atualizado a cada frame quando há alvo móvel).
        self._centro_alvo: tuple[float, float] = (0.0, 0.0)
        self._zoom_alvo: float = self.zoom
        self._deslocamento_alvo: float = 0.0

    # ----------------------------------------------------------- dimensões
    @property
    def escala_janela(self) -> float:
        """Quanto a janela atual é maior/menor que a de referência."""
        return self.altura / _ALTURA_REFERENCIA

    def zoom_visao_geral(self) -> float:
        """Zoom do panorama, ajustado ao tamanho atual da janela."""
        return ZOOM_VISAO_GERAL * self.escala_janela

    def limitar_zoom(self, zoom: float) -> float:
        """Aplica os limites de zoom, que escalam junto com a janela."""
        return min(
            ZOOM_MAX * self.escala_janela,
            max(ZOOM_MIN * self.escala_janela, zoom),
        )

    def redimensionar(self, largura: int, altura: int) -> None:
        """Informa o novo tamanho da janela (o enquadramento acompanha)."""
        if largura == self.largura and altura == self.altura:
            return
        proporcao = altura / self.altura
        self.largura = largura
        self.altura = altura
        # Mantém o mesmo campo de visão vertical após o redimensionamento.
        self.zoom *= proporcao
        self._zoom_inicial *= proporcao
        self._zoom_alvo *= proporcao

    # ------------------------------------------------------------------ alvo
    def iniciar_transicao(
        self,
        centro_alvo: tuple[float, float],
        zoom_alvo: float,
        deslocamento_alvo: float,
    ) -> None:
        """Congela o estado atual como origem e começa uma nova interpolação."""
        self._centro_x_inicial = self.centro_x
        self._centro_y_inicial = self.centro_y
        self._zoom_inicial = self.zoom
        self._deslocamento_inicial = self.deslocamento_x
        self._progresso = 0.0
        self.definir_alvo(centro_alvo, zoom_alvo, deslocamento_alvo)

    def definir_alvo(
        self,
        centro_alvo: tuple[float, float],
        zoom_alvo: float,
        deslocamento_alvo: float,
    ) -> None:
        """Atualiza o destino sem reiniciar o progresso (alvo em movimento)."""
        self._centro_alvo = centro_alvo
        self._zoom_alvo = self.limitar_zoom(zoom_alvo)
        self._deslocamento_alvo = deslocamento_alvo

    def focar_corpo(
        self, posicao: tuple[float, float], raio_corpo: float, reiniciar: bool
    ) -> None:
        """Aponta a câmera para um corpo, com ou sem reiniciar a transição."""
        escala = self.escala_janela
        alvo = (
            posicao,
            zoom_para_focar(raio_corpo, escala),
            DESLOCAMENTO_FOCO_X_PX * escala,
        )
        if reiniciar:
            self.iniciar_transicao(*alvo)
        else:
            self.definir_alvo(*alvo)

    def voltar_visao_geral(self, reiniciar: bool = True) -> None:
        """Volta suavemente ao enquadramento do sistema inteiro."""
        if reiniciar:
            self.iniciar_transicao((0.0, 0.0), self.zoom_visao_geral(), 0.0)
        else:
            self.definir_alvo((0.0, 0.0), self.zoom_visao_geral(), 0.0)

    # ------------------------------------------------------- controle manual
    def congelar(self) -> None:
        """Encerra a transição, fixando a câmera onde ela está agora."""
        self._progresso = 1.0
        self._centro_alvo = (self.centro_x, self.centro_y)
        self._zoom_alvo = self.zoom
        self._deslocamento_alvo = self.deslocamento_x
        self._centro_x_inicial = self.centro_x
        self._centro_y_inicial = self.centro_y
        self._zoom_inicial = self.zoom
        self._deslocamento_inicial = self.deslocamento_x

    def arrastar(self, dx_tela: float, dy_tela: float) -> None:
        """Pan manual: desloca a cena conforme o mouse, em pixels de tela."""
        self.congelar()
        alvo_x, alvo_y = self._centro_alvo
        self._centro_alvo = (alvo_x - dx_tela / self.zoom, alvo_y - dy_tela / self.zoom)

    def aplicar_zoom(self, fator: float) -> None:
        """Zoom manual (roda do mouse), respeitando os limites globais."""
        self.congelar()
        self._zoom_alvo = self.limitar_zoom(self.zoom * fator)

    # --------------------------------------------------------------- runtime
    @property
    def em_transicao(self) -> bool:
        """True enquanto a interpolação não terminou."""
        return self._progresso < 1.0

    def atualizar(self, dt: float) -> None:
        """Avança a interpolação em ``dt`` segundos."""
        if self._progresso < 1.0:
            self._progresso = min(1.0, self._progresso + dt / DURACAO_TRANSICAO_S)

        fator = suavizar(self._progresso)
        alvo_x, alvo_y = self._centro_alvo
        self.centro_x = _interpolar(self._centro_x_inicial, alvo_x, fator)
        self.centro_y = _interpolar(self._centro_y_inicial, alvo_y, fator)
        self.zoom = _interpolar(self._zoom_inicial, self._zoom_alvo, fator)
        self.deslocamento_x = _interpolar(
            self._deslocamento_inicial, self._deslocamento_alvo, fator
        )

    # ------------------------------------------------------------ conversões
    def mundo_para_tela(self, posicao: tuple[float, float]) -> tuple[float, float]:
        """Projeta um ponto de mundo em pixels da janela."""
        x, y = posicao
        tela_x = (x - self.centro_x) * self.zoom + self.largura / 2 + self.deslocamento_x
        tela_y = (y - self.centro_y) * self.zoom + self.altura / 2
        return (tela_x, tela_y)

    def escalar(self, comprimento: float) -> float:
        """Converte um comprimento de mundo para pixels de tela."""
        return comprimento * self.zoom


__all__ = ["Camera2D", "suavizar", "zoom_para_focar"]
