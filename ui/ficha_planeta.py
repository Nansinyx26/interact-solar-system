"""Ficha lateral com os dados do corpo focado + título animado."""

from __future__ import annotations

import pygame

from config import (
    ALTURA_JANELA,
    COR_DESTAQUE,
    COR_TEXTO,
    COR_TEXTO_SECUNDARIO,
    DESLOCAMENTO_ENTRADA_FICHA_PX,
    DURACAO_ANIMACAO_FICHA_S,
    LARGURA_FICHA,
    LARGURA_JANELA,
    MARGEM_HUD,
)
from dados.planetas import CorpoCeleste
from nucleo.camera import suavizar
from ui.hud import Fontes, desenhar_painel

# A ficha ocupa a faixa direita a partir do topo; o preview da webcam fica no
# canto inferior direito, então o limite de baixo chega pronto de fora.
_TOPO_FICHA = MARGEM_HUD
_TOPO_TITULO = 120
# Cada item é rótulo + N linhas de valor + respiro; alguns valores ocupam duas
# linhas (UA e km, por exemplo), então a altura do item é calculada, não fixa.
_ALTURA_ROTULO = 17
_ALTURA_LINHA_VALOR = 17
_RESPIRO_ITEM = 10


def _formatar_inteiro(valor: float) -> str:
    """Inteiro no padrão pt-BR (1.392.700)."""
    return f"{valor:,.0f}".replace(",", ".")


def _formatar_decimal(valor: float, casas: int = 2) -> str:
    """Decimal no padrão pt-BR (1,52)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


def _formatar_periodo_orbital(corpo: CorpoCeleste) -> str:
    """Período orbital em dias e, quando faz sentido, em anos terrestres."""
    if corpo.periodo_orbital_dias <= 0:
        return "— (orbita o centro da Galáxia)"
    dias = corpo.periodo_orbital_dias
    if dias < 365.26:
        return f"{_formatar_decimal(dias, 2)} dias"
    anos = dias / 365.26
    return f"{_formatar_decimal(anos, 2)} anos ({_formatar_inteiro(dias)} dias)"


def _formatar_rotacao(corpo: CorpoCeleste) -> str:
    """Período de rotação, sinalizando giro retrógrado."""
    horas = corpo.periodo_rotacao_horas
    sufixo = " (retrógrada)" if horas < 0 else ""
    horas = abs(horas)
    if horas >= 48:
        return f"{_formatar_decimal(horas / 24, 2)} dias{sufixo}"
    return f"{_formatar_decimal(horas, 2)} h{sufixo}"


def _formatar_distancia(corpo: CorpoCeleste) -> str:
    """Distância média ao Sol em UA e km."""
    if corpo.distancia_ua <= 0:
        return "0 (centro do sistema)"
    return (
        f"{_formatar_decimal(corpo.distancia_ua, 3)} UA\n"
        f"{_formatar_inteiro(corpo.distancia_km)} km"
    )


def linhas_da_ficha(corpo: CorpoCeleste) -> list[tuple[str, str]]:
    """Pares (rótulo, valor) exibidos no card."""
    return [
        ("Diâmetro equatorial", f"{_formatar_inteiro(corpo.diametro_km)} km"),
        ("Distância média ao Sol", _formatar_distancia(corpo)),
        ("Período orbital", _formatar_periodo_orbital(corpo)),
        ("Período de rotação", _formatar_rotacao(corpo)),
        ("Luas conhecidas", _formatar_inteiro(corpo.luas)),
        ("Temperatura média", f"{_formatar_decimal(corpo.temperatura_media_c, 1)} °C"),
        ("Inclinação axial", f"{_formatar_decimal(corpo.inclinacao_axial_graus, 2)}°"),
    ]


class FichaPlaneta:
    """Card lateral + título, com animação de entrada e saída."""

    def __init__(
        self,
        fontes: Fontes,
        largura: int = LARGURA_JANELA,
        altura: int = ALTURA_JANELA,
    ) -> None:
        self._fontes = fontes
        self._largura = largura
        self._altura = altura
        self._corpo: CorpoCeleste | None = None
        self._progresso: float = 0.0  # 0 = escondida, 1 = totalmente visível
        self._entrando: bool = False

    def redimensionar(self, largura: int, altura: int) -> None:
        """Reposiciona a ficha para o novo tamanho da janela."""
        self._largura = largura
        self._altura = altura

    def mostrar(self, corpo: CorpoCeleste) -> None:
        """Inicia a animação de entrada para um novo corpo."""
        if self._corpo is not None and self._corpo.nome != corpo.nome:
            self._progresso = 0.0  # troca direta: reanima o card
        self._corpo = corpo
        self._entrando = True

    def ocultar(self) -> None:
        """Inicia a animação de saída."""
        self._entrando = False

    def atualizar(self, dt: float) -> None:
        """Avança a animação em ``dt`` segundos."""
        passo = dt / DURACAO_ANIMACAO_FICHA_S
        if self._entrando:
            self._progresso = min(1.0, self._progresso + passo)
        else:
            self._progresso = max(0.0, self._progresso - passo)
            if self._progresso == 0.0:
                self._corpo = None

    @property
    def visivel(self) -> bool:
        """True enquanto houver algo a desenhar."""
        return self._corpo is not None and self._progresso > 0.0

    # -------------------------------------------------------------- desenho
    def desenhar(self, superficie: pygame.Surface, limite_inferior: int) -> None:
        """Desenha título e card conforme o progresso da animação.

        ``limite_inferior`` é o y máximo que o card pode ocupar — quem define é
        o chamador, porque depende de o preview da webcam estar visível ou não.
        """
        if not self.visivel or self._corpo is None:
            return
        fator = suavizar(self._progresso)
        self._desenhar_titulo(superficie, self._corpo, fator)
        self._desenhar_card(superficie, self._corpo, fator, limite_inferior)

    def _desenhar_titulo(
        self, superficie: pygame.Surface, corpo: CorpoCeleste, fator: float
    ) -> None:
        """Nome do corpo em destaque, entrando de baixo com fade."""
        texto = self._fontes.titulo.render(corpo.nome, True, COR_TEXTO)
        legenda = self._fontes.media.render(
            f"{corpo.tipo.capitalize()} · gesto {corpo.indice_gesto}",
            True,
            COR_DESTAQUE,
        )
        deslocamento = (1.0 - fator) * DESLOCAMENTO_ENTRADA_FICHA_PX
        alpha = int(255 * fator)
        texto.set_alpha(alpha)
        legenda.set_alpha(alpha)
        superficie.blit(texto, (MARGEM_HUD + 12, _TOPO_TITULO + deslocamento))
        superficie.blit(
            legenda,
            (MARGEM_HUD + 16, _TOPO_TITULO + texto.get_height() + 2 + deslocamento),
        )

    def _desenhar_card(
        self,
        superficie: pygame.Surface,
        corpo: CorpoCeleste,
        fator: float,
        limite_inferior: int,
    ) -> None:
        """Card com os dados astronômicos e o fato curioso."""
        linhas = linhas_da_ficha(corpo)
        itens = [(rotulo, valor.split("\n")) for rotulo, valor in linhas]
        altura_itens = sum(
            _ALTURA_ROTULO + len(partes) * _ALTURA_LINHA_VALOR + _RESPIRO_ITEM
            for _, partes in itens
        )
        fato = self._quebrar(corpo.fato_curioso, LARGURA_FICHA - 36)
        altura = 78 + altura_itens + 34 + len(fato) * 18 + 16
        altura = max(120, min(altura, limite_inferior - _TOPO_FICHA))
        deslocamento = (1.0 - fator) * DESLOCAMENTO_ENTRADA_FICHA_PX

        retangulo = pygame.Rect(
            int(self._largura - LARGURA_FICHA - MARGEM_HUD + deslocamento),
            _TOPO_FICHA,
            LARGURA_FICHA,
            int(altura),
        )
        camada = pygame.Surface(retangulo.size, pygame.SRCALPHA)
        desenhar_painel(camada, camada.get_rect())

        # Cabeçalho com a cor característica do corpo.
        pygame.draw.rect(
            camada, (*corpo.cor_base, 210), (0, 0, LARGURA_FICHA, 4), border_radius=2
        )
        camada.blit(self._fontes.grande.render(corpo.nome, True, COR_TEXTO), (18, 16))
        camada.blit(
            self._fontes.mini.render("FICHA ASTRONÔMICA", True, COR_TEXTO_SECUNDARIO),
            (18, 58),
        )

        y = 78
        for rotulo, partes in itens:
            camada.blit(
                self._fontes.mini.render(rotulo.upper(), True, COR_TEXTO_SECUNDARIO),
                (18, y),
            )
            for indice, parte in enumerate(partes):
                camada.blit(
                    self._fontes.pequena.render(parte, True, COR_TEXTO),
                    (18, y + _ALTURA_ROTULO + indice * _ALTURA_LINHA_VALOR),
                )
            y += _ALTURA_ROTULO + len(partes) * _ALTURA_LINHA_VALOR + _RESPIRO_ITEM

        # Fato curioso, quebrado em linhas que cabem no card.
        pygame.draw.line(
            camada, (255, 255, 255, 30), (18, y - 6), (LARGURA_FICHA - 18, y - 6)
        )
        camada.blit(
            self._fontes.mini.render("FATO CURIOSO", True, COR_DESTAQUE), (18, y + 4)
        )
        y += 26
        for linha in fato:
            camada.blit(self._fontes.pequena.render(linha, True, COR_TEXTO), (18, y))
            y += 18

        camada.set_alpha(int(255 * fator))
        superficie.blit(camada, retangulo.topleft)

    def _quebrar(self, texto: str, largura_max: int) -> list[str]:
        """Quebra o texto em linhas que cabem na largura informada."""
        palavras = texto.split()
        linhas: list[str] = []
        atual = ""
        for palavra in palavras:
            tentativa = f"{atual} {palavra}".strip()
            if self._fontes.pequena.size(tentativa)[0] <= largura_max:
                atual = tentativa
            else:
                if atual:
                    linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        return linhas


__all__ = ["FichaPlaneta", "linhas_da_ficha"]
