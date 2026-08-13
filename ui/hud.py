"""HUD: indicadores de gesto, legenda, avisos e preview da webcam."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pygame

from config import (
    ALPHA_PAINEL,
    ALTURA_JANELA,
    ALTURA_PREVIEW_CAMERA,
    COR_AVISO,
    COR_DESTAQUE,
    COR_ERRO,
    COR_PAINEL,
    COR_TEXTO,
    COR_TEXTO_SECUNDARIO,
    ESPESSURA_ANEL_PROGRESSO,
    FAMILIA_FONTE,
    FAMILIA_FONTE_MONO,
    GESTO_VISAO_GERAL,
    LARGURA_JANELA,
    LARGURA_PREVIEW_CAMERA,
    LIMIAR_AVISO_CONFIANCA,
    LIMIAR_BRILHO_BAIXO,
    MARGEM_HUD,
    RAIO_ANEL_PROGRESSO,
    TAM_FONTE_GRANDE,
    TAM_FONTE_MEDIA,
    TAM_FONTE_MINI,
    TAM_FONTE_PEQUENA,
    TAM_FONTE_TITULO,
)
from dados.planetas import CorpoCeleste, legenda_gestos
from gestos.detector import LeituraGestos, StatusCamera
from gestos.estabilizador import ResultadoEstabilizacao

# Cantos do painel de gestos e da legenda.
_LARGURA_PAINEL_GESTO = 226
_ALTURA_PAINEL_GESTO = 138
_LARGURA_PAINEL_LEGENDA = 300
_ALTURA_LINHA_LEGENDA = 19
_MAXIMO_DEDOS_UMA_MAO = 5

# Altura total do bloco do preview (imagem + rodapé com a legenda da tecla C).
# A ficha do planeta usa isto para não invadir o espaço da webcam.
ALTURA_BLOCO_PREVIEW = ALTURA_PREVIEW_CAMERA + 22


@dataclass(frozen=True)
class Fontes:
    """Conjunto de fontes usado por toda a interface."""

    titulo: pygame.font.Font
    grande: pygame.font.Font
    media: pygame.font.Font
    pequena: pygame.font.Font
    mini: pygame.font.Font
    mono: pygame.font.Font

    @staticmethod
    def carregar() -> "Fontes":
        """Carrega fontes do sistema (sem arquivos externos no projeto)."""
        return Fontes(
            titulo=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_TITULO, bold=True),
            grande=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_GRANDE, bold=True),
            media=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_MEDIA),
            pequena=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_PEQUENA),
            mini=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_MINI),
            mono=pygame.font.SysFont(FAMILIA_FONTE_MONO, TAM_FONTE_PEQUENA),
        )


@dataclass(frozen=True)
class EstadoHUD:
    """Tudo que o HUD precisa saber para desenhar um frame."""

    fps: float
    leitura: LeituraGestos
    resultado: ResultadoEstabilizacao
    corpo_alvo: CorpoCeleste | None
    mostrar_preview: bool
    pausado: bool
    escala_tempo: float
    valor_confirmado: int | None = None  # inclui o gesto de comando (10)


def desenhar_painel(
    superficie: pygame.Surface, retangulo: pygame.Rect, alpha: int = ALPHA_PAINEL
) -> None:
    """Fundo translúcido arredondado, base de todos os blocos do HUD."""
    camada = pygame.Surface(retangulo.size, pygame.SRCALPHA)
    pygame.draw.rect(
        camada, (*COR_PAINEL, alpha), camada.get_rect(), border_radius=10
    )
    pygame.draw.rect(
        camada, (255, 255, 255, 26), camada.get_rect(), width=1, border_radius=10
    )
    superficie.blit(camada, retangulo.topleft)


def _desenhar_arco_grosso(
    superficie: pygame.Surface,
    centro: tuple[int, int],
    raio: int,
    fracao: float,
    cor: tuple[int, int, int],
    alpha: int = 255,
) -> None:
    """Arco de progresso — ``pygame.draw.arc`` grosso sai serrilhado, então
    empilhamos arcos de 1 px."""
    if fracao <= 0.0:
        return
    inicio = math.pi / 2
    fim = inicio + 2 * math.pi * min(1.0, fracao)
    camada = pygame.Surface((raio * 2 + 4, raio * 2 + 4), pygame.SRCALPHA)
    for passo in range(ESPESSURA_ANEL_PROGRESSO):
        atual = raio - passo
        caixa = pygame.Rect(
            raio + 2 - atual, raio + 2 - atual, atual * 2, atual * 2
        )
        pygame.draw.arc(camada, (*cor, alpha), caixa, inicio, fim, 2)
    superficie.blit(camada, (centro[0] - raio - 2, centro[1] - raio - 2))


class HUD:
    """Desenha overlays sobre a cena já renderizada."""

    def __init__(
        self,
        fontes: Fontes,
        largura: int = LARGURA_JANELA,
        altura: int = ALTURA_JANELA,
    ) -> None:
        self._fontes = fontes
        self._largura = largura
        self._altura = altura
        self._legenda = legenda_gestos()
        self._superficie_preview: pygame.Surface | None = None

    def redimensionar(self, largura: int, altura: int) -> None:
        """Reposiciona os blocos para o novo tamanho da janela."""
        self._largura = largura
        self._altura = altura

    # ------------------------------------------------------------- principal
    def desenhar(self, superficie: pygame.Surface, estado: EstadoHUD) -> None:
        """Desenha o HUD completo."""
        self._desenhar_status(superficie, estado)
        self._desenhar_painel_gesto(superficie, estado)
        self._desenhar_legenda(superficie)
        self._desenhar_avisos(superficie, estado)
        if estado.mostrar_preview:
            self._desenhar_preview(superficie, estado.leitura)

    # --------------------------------------------------------------- blocos
    def _desenhar_status(self, superficie: pygame.Surface, estado: EstadoHUD) -> None:
        """Canto superior esquerdo: FPS, velocidade do tempo e atalhos."""
        linhas = [
            f"{estado.fps:5.1f} FPS",
            f"tempo x{estado.escala_tempo:.1f}" + ("  [PAUSADO]" if estado.pausado else ""),
        ]
        y = MARGEM_HUD
        for indice, texto in enumerate(linhas):
            cor = COR_TEXTO if indice == 0 else COR_TEXTO_SECUNDARIO
            superficie.blit(self._fontes.mono.render(texto, True, cor), (MARGEM_HUD, y))
            y += 20

        atalhos = (
            "0-8 focar   V visão geral   ESPAÇO pausa   +/- tempo   C câmera   "
            "Q sair   ·   arraste com o mouse, roda = zoom"
        )
        superficie.blit(
            self._fontes.mini.render(atalhos, True, COR_TEXTO_SECUNDARIO),
            (MARGEM_HUD, self._altura - MARGEM_HUD - 16),
        )

    def _desenhar_painel_gesto(
        self, superficie: pygame.Surface, estado: EstadoHUD
    ) -> None:
        """Número detectado (com anel de progresso) e número confirmado."""
        topo = self._altura - MARGEM_HUD - _ALTURA_PAINEL_GESTO - 26
        retangulo = pygame.Rect(
            MARGEM_HUD, topo, _LARGURA_PAINEL_GESTO, _ALTURA_PAINEL_GESTO
        )
        desenhar_painel(superficie, retangulo)

        leitura = estado.leitura
        resultado = estado.resultado

        centro_anel = (retangulo.x + 62, retangulo.y + 66)
        # Trilho do anel.
        pygame.draw.circle(
            superficie, (52, 60, 84), centro_anel, RAIO_ANEL_PROGRESSO, width=3
        )
        cor_anel = COR_AVISO if resultado.em_cooldown else COR_DESTAQUE
        _desenhar_arco_grosso(
            superficie, centro_anel, RAIO_ANEL_PROGRESSO, resultado.progresso, cor_anel
        )

        detectado = "—" if leitura.contagem is None else str(leitura.contagem)
        cor_numero = COR_TEXTO if leitura.contagem is not None else COR_TEXTO_SECUNDARIO
        texto = self._fontes.titulo.render(detectado, True, cor_numero)
        superficie.blit(texto, texto.get_rect(center=centro_anel))

        superficie.blit(
            self._fontes.mini.render("DETECTADO", True, COR_TEXTO_SECUNDARIO),
            (retangulo.x + 20, retangulo.bottom - 26),
        )

        # Coluna direita: valor já confirmado e alvo correspondente.
        coluna_x = retangulo.x + 124
        superficie.blit(
            self._fontes.mini.render("CONFIRMADO", True, COR_TEXTO_SECUNDARIO),
            (coluna_x, retangulo.y + 18),
        )
        confirmado = estado.valor_confirmado
        if confirmado is None and estado.corpo_alvo is not None:
            confirmado = estado.corpo_alvo.indice_gesto
        superficie.blit(
            self._fontes.grande.render(
                "—" if confirmado is None else str(confirmado), True, COR_DESTAQUE
            ),
            (coluna_x, retangulo.y + 36),
        )
        nome_alvo = estado.corpo_alvo.nome if estado.corpo_alvo else "visão geral"
        superficie.blit(
            self._fontes.pequena.render(nome_alvo, True, COR_TEXTO),
            (coluna_x, retangulo.y + 80),
        )
        # Detalhe por mão: com 6-8 é o que revela se a segunda mão foi perdida
        # ("1 mão: 5") ou se uma delas está contando errado ("2 mãos: 5+0").
        if leitura.contagens_por_mao:
            detalhe = "+".join(str(valor) for valor in leitura.contagens_por_mao)
            maos = f"{leitura.maos_visiveis} mão(s): {detalhe}"
        else:
            maos = f"{leitura.maos_visiveis} mão(s)"
        superficie.blit(
            self._fontes.mini.render(maos, True, COR_TEXTO_SECUNDARIO),
            (coluna_x, retangulo.y + 104),
        )

    def _desenhar_legenda(self, superficie: pygame.Surface) -> None:
        """Tabela gesto -> corpo celeste."""
        altura = _ALTURA_LINHA_LEGENDA * (len(self._legenda) + 1) + 58
        retangulo = pygame.Rect(
            MARGEM_HUD + _LARGURA_PAINEL_GESTO + 12,
            self._altura - MARGEM_HUD - altura - 26,
            _LARGURA_PAINEL_LEGENDA,
            altura,
        )
        desenhar_painel(superficie, retangulo)
        superficie.blit(
            self._fontes.mini.render("DEDOS → CORPO CELESTE", True, COR_TEXTO_SECUNDARIO),
            (retangulo.x + 14, retangulo.y + 10),
        )
        y = retangulo.y + 30
        itens: list[tuple[str, str, tuple[int, int, int]]] = [
            (str(dedos), nome, COR_TEXTO) for dedos, nome in self._legenda
        ]
        # Gesto de comando: duas mãos abertas (ou a tecla V) reenquadram tudo.
        itens.append((str(GESTO_VISAO_GERAL), "visão geral  (tecla V)", COR_DESTAQUE))
        for dedos, nome, cor in itens:
            superficie.blit(
                self._fontes.mono.render(dedos, True, COR_DESTAQUE),
                (retangulo.x + 18, y),
            )
            superficie.blit(
                self._fontes.pequena.render(nome, True, cor),
                (retangulo.x + 46, y),
            )
            y += _ALTURA_LINHA_LEGENDA
        superficie.blit(
            self._fontes.mini.render(
                "6–8 exigem as duas mãos · 9: ignorado",
                True,
                COR_TEXTO_SECUNDARIO,
            ),
            (retangulo.x + 18, retangulo.bottom - 22),
        )

    def _desenhar_avisos(self, superficie: pygame.Surface, estado: EstadoHUD) -> None:
        """Mensagens de webcam, iluminação e dica das duas mãos."""
        avisos: list[tuple[str, tuple[int, int, int]]] = []
        leitura = estado.leitura

        if leitura.status in (StatusCamera.INDISPONIVEL, StatusCamera.DESCONECTADA):
            avisos.append((leitura.mensagem or "Webcam indisponível.", COR_ERRO))
        elif leitura.status is StatusCamera.INICIANDO:
            avisos.append(("Abrindo a webcam...", COR_TEXTO_SECUNDARIO))
        else:
            if leitura.brilho_medio < LIMIAR_BRILHO_BAIXO:
                avisos.append(
                    ("Iluminação baixa — a detecção pode falhar.", COR_AVISO)
                )
            elif (
                leitura.maos_visiveis > 0
                and leitura.confianca_media < LIMIAR_AVISO_CONFIANCA
            ):
                avisos.append(
                    ("Confiança baixa — aproxime e centralize a mão.", COR_AVISO)
                )
            if leitura.descartada_por_borda:
                avisos.append(("Mão saindo do quadro — leitura descartada.", COR_AVISO))
            if leitura.contagem == _MAXIMO_DEDOS_UMA_MAO:
                avisos.append(("Use as duas mãos para 6–8 (ex.: 5 + 3 = Netuno).", COR_DESTAQUE))

        if not avisos:
            return
        y = MARGEM_HUD
        for texto, cor in avisos:
            renderizado = self._fontes.pequena.render(texto, True, cor)
            largura = renderizado.get_width() + 24
            retangulo = pygame.Rect(
                (self._largura - largura) // 2, y, largura, renderizado.get_height() + 12
            )
            desenhar_painel(superficie, retangulo)
            superficie.blit(renderizado, (retangulo.x + 12, retangulo.y + 6))
            y += retangulo.height + 6

    def _desenhar_preview(
        self, superficie: pygame.Surface, leitura: LeituraGestos
    ) -> None:
        """Miniatura da webcam ancorada no canto inferior direito."""
        retangulo = pygame.Rect(
            self._largura - LARGURA_PREVIEW_CAMERA - MARGEM_HUD,
            self._altura - ALTURA_BLOCO_PREVIEW - MARGEM_HUD,
            LARGURA_PREVIEW_CAMERA,
            ALTURA_BLOCO_PREVIEW,
        )
        desenhar_painel(superficie, retangulo)

        quadro = leitura.preview
        if quadro is not None:
            self._superficie_preview = pygame.image.frombuffer(
                np.ascontiguousarray(quadro).tobytes(),
                (quadro.shape[1], quadro.shape[0]),
                "RGB",
            )
        if self._superficie_preview is not None:
            superficie.blit(self._superficie_preview, (retangulo.x, retangulo.y))
        else:
            superficie.blit(
                self._fontes.pequena.render("sem imagem", True, COR_TEXTO_SECUNDARIO),
                (retangulo.x + 12, retangulo.y + 12),
            )
        superficie.blit(
            self._fontes.mini.render(
                "webcam (C oculta/mostra)", True, COR_TEXTO_SECUNDARIO
            ),
            (retangulo.x + 8, retangulo.bottom - 18),
        )


__all__ = ["HUD", "EstadoHUD", "Fontes", "desenhar_painel"]
