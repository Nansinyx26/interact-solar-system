"""Ficha da lua: painel com os dados do satélite em foco.

Vive na coluna DIREITA, ao contrário da ficha do planeta. Não é preciosismo de
layout: no modo lua o planeta-mãe continua selecionado e a ficha dele continua
aberta à esquerda, e é exatamente a comparação entre as duas — Europa tem 1/4 do
diâmetro da Terra, Titã é maior que Mercúrio — que dá sentido a olhar uma lua.
Empilhar uma ficha sobre a outra jogaria fora essa leitura.

Reaproveita a animação, o painel e os formatadores numéricos da ficha do
planeta: são as mesmas convenções visuais, e duplicá-las faria as duas
divergirem no primeiro ajuste.
"""

from __future__ import annotations

import pygame

from config import (
    ALTURA_JANELA,
    COR_DESTAQUE,
    COR_TEXTO,
    COR_TEXTO_SECUNDARIO,
    DESLOCAMENTO_ENTRADA_FICHA_PX,
    DURACAO_ANIMACAO_FICHA_S,
    LARGURA_FICHA_LUA,
    LARGURA_JANELA,
    MARGEM_HUD,
)
from dados.luas import LuaMenor
from nucleo.camera import suavizar
from ui.ficha_planeta import formatar_decimal, formatar_inteiro
from ui.hud import Fontes, desenhar_painel

# Métricas de linha da ficha do planeta, com UMA diferença: 19 px de entrelinha
# em vez de 17. Aqui os valores quebram em duas linhas com frequência (a
# composição é texto corrido), e com 17 px os glifos de 16 px quase se encostam
# — o traço separador chegava a cortar a última linha. Na ficha do planeta só a
# distância quebra, então lá o valor original continua servindo.
_ALTURA_ROTULO = 17
_ALTURA_LINHA_VALOR = 19
_RESPIRO_ITEM = 10
_PADDING = 18


def formatar_massa(kg: float) -> str:
    """Massa em notação científica legível, mais a comparação com a Lua.

    Um número como 4,8e22 kg não diz nada sozinho para o público do projeto.
    A referência à Lua da Terra é o que transforma o dado em informação — é o
    mesmo recurso que a ficha do planeta usa ao dar distâncias em UA *e* em km.
    """
    if kg <= 0:
        return "— (não medida com precisão)"
    expoente = 0
    mantissa = kg
    while mantissa >= 10.0:
        mantissa /= 10.0
        expoente += 1
    texto = f"{formatar_decimal(mantissa, 2)} × 10^{expoente} kg"

    # 7,342e22 kg = massa da Lua. Comparar com ela é o jeito mais direto de dar
    # escala, já que é a única lua que todo mundo conhece de vista.
    razao = kg / 7.342e22
    if razao >= 1.0:
        return f"{texto}\n{formatar_decimal(razao, 2)}× a massa da Lua"
    return f"{texto}\n{formatar_decimal(1.0 / razao, 1)}× menor que a Lua"


def formatar_periodo(dias: float) -> str:
    """Período orbital em dias/horas, sinalizando órbita retrógrada."""
    sufixo = " (retrógrada)" if dias < 0 else ""
    dias = abs(dias)
    if dias < 1.0:
        # Fobos dá uma volta em 7h39: em dias ele viraria "0,32", que esconde o
        # fato mais interessante da lua.
        return f"{formatar_decimal(dias * 24.0, 1)} horas{sufixo}"
    return f"{formatar_decimal(dias, 3)} dias{sufixo}"


def linhas_da_ficha_lua(lua: LuaMenor) -> list[tuple[str, str]]:
    """Pares (rótulo, valor) exibidos no card da lua."""
    return [
        ("Raio médio", f"{formatar_inteiro(lua.raio_km)} km"),
        ("Massa", formatar_massa(lua.massa_kg)),
        (
            f"Distância média a {lua.planeta}",
            f"{formatar_inteiro(lua.distancia_km)} km",
        ),
        ("Período orbital", formatar_periodo(lua.periodo_orbital_dias)),
        ("Composição / superfície", lua.composicao or "—"),
    ]


class FichaLua:
    """Card da lua em foco, com a mesma animação de entrada e saída da ficha."""

    def __init__(
        self,
        fontes: Fontes,
        largura: int = LARGURA_JANELA,
        altura: int = ALTURA_JANELA,
    ) -> None:
        self._fontes = fontes
        self._largura = largura
        self._altura = altura
        self._lua: LuaMenor | None = None
        self._progresso: float = 0.0  # 0 = escondida, 1 = totalmente visível
        self._entrando: bool = False

    def redimensionar(self, largura: int, altura: int) -> None:
        """Reposiciona a ficha para o novo tamanho da janela."""
        self._largura = largura
        self._altura = altura

    def mostrar(self, lua: LuaMenor) -> None:
        """Inicia a animação de entrada para uma nova lua."""
        if self._lua is not None and self._lua.nome != lua.nome:
            self._progresso = 0.0  # troca direta: reanima o card
        self._lua = lua
        self._entrando = True

    def ocultar(self) -> None:
        """Inicia a animação de saída (soltar o "L" ou tecla ESC)."""
        self._entrando = False

    def atualizar(self, dt: float) -> None:
        """Avança a animação em ``dt`` segundos."""
        passo = dt / DURACAO_ANIMACAO_FICHA_S
        if self._entrando:
            self._progresso = min(1.0, self._progresso + passo)
        else:
            self._progresso = max(0.0, self._progresso - passo)
            if self._progresso == 0.0:
                self._lua = None

    @property
    def visivel(self) -> bool:
        """True enquanto houver algo a desenhar."""
        return self._lua is not None and self._progresso > 0.0

    # -------------------------------------------------------------- desenho
    def desenhar(self, superficie: pygame.Surface, limite_inferior: int) -> None:
        """Desenha o card conforme o progresso da animação.

        ``limite_inferior`` é o y máximo que o card pode ocupar — quem define é
        o chamador, porque depende de o preview da webcam estar visível ou não.
        """
        if not self.visivel or self._lua is None:
            return
        self._desenhar_card(
            superficie, self._lua, suavizar(self._progresso), limite_inferior
        )

    def _desenhar_card(
        self,
        superficie: pygame.Surface,
        lua: LuaMenor,
        fator: float,
        limite_inferior: int,
    ) -> None:
        """Card com os dados da lua e a curiosidade."""
        largura_texto = LARGURA_FICHA_LUA - _PADDING * 2
        itens: list[tuple[str, list[str]]] = []
        for rotulo, valor in linhas_da_ficha_lua(lua):
            partes: list[str] = []
            for pedaco in valor.split("\n"):
                # Composição é texto corrido e quase sempre passa da largura:
                # quebrar aqui (e não só no fato curioso) evita o corte seco.
                partes.extend(self._quebrar(pedaco, largura_texto))
            itens.append((rotulo, partes))

        altura_itens = sum(
            _ALTURA_ROTULO + len(partes) * _ALTURA_LINHA_VALOR + _RESPIRO_ITEM
            for _, partes in itens
        )
        curiosidade = self._quebrar(lua.fato_curioso, largura_texto)
        # O +26 do fim é a faixa da dica de fechar, desenhada em `altura - 22`.
        # Sem reservá-la aqui, ela era escrita POR CIMA da última linha da
        # curiosidade — o card fechava exatamente onde o texto terminava.
        altura = 78 + altura_itens + 34 + len(curiosidade) * 18 + 16 + 26
        altura = max(120, min(altura, limite_inferior - MARGEM_HUD))

        # Entra pela DIREITA (a ficha do planeta entra pela esquerda): as duas
        # animações apontam para fora da tela, cada uma do seu lado.
        deslocamento = (1.0 - fator) * DESLOCAMENTO_ENTRADA_FICHA_PX
        retangulo = pygame.Rect(
            int(self._largura - LARGURA_FICHA_LUA - MARGEM_HUD + deslocamento),
            MARGEM_HUD,
            LARGURA_FICHA_LUA,
            int(altura),
        )
        camada = pygame.Surface(retangulo.size, pygame.SRCALPHA)
        desenhar_painel(camada, camada.get_rect())

        # Faixa superior com a cor da própria lua — é o mesmo tom usado para
        # desenhá-la na órbita, então o card e o ponto na tela se identificam.
        pygame.draw.rect(
            camada, (*lua.cor, 210), (0, 0, LARGURA_FICHA_LUA, 4), border_radius=2
        )
        camada.blit(
            self._fontes.grande.render(lua.nome, True, COR_TEXTO), (_PADDING, 16)
        )
        camada.blit(
            self._fontes.mini.render(
                f"LUA DE {lua.planeta}".upper(), True, COR_DESTAQUE
            ),
            (_PADDING, 58),
        )

        y = 78
        for rotulo, partes in itens:
            camada.blit(
                self._fontes.mini.render(rotulo.upper(), True, COR_TEXTO_SECUNDARIO),
                (_PADDING, y),
            )
            for indice, parte in enumerate(partes):
                camada.blit(
                    self._fontes.pequena.render(parte, True, COR_TEXTO),
                    (_PADDING, y + _ALTURA_ROTULO + indice * _ALTURA_LINHA_VALOR),
                )
            y += _ALTURA_ROTULO + len(partes) * _ALTURA_LINHA_VALOR + _RESPIRO_ITEM

        # O separador fica ABAIXO do respiro do último item, não dentro dele:
        # em `y - 6` ele caía a 1 px do texto e parecia riscá-lo.
        pygame.draw.line(
            camada,
            (255, 255, 255, 30),
            (_PADDING, y),
            (LARGURA_FICHA_LUA - _PADDING, y),
        )
        camada.blit(
            self._fontes.mini.render("CURIOSIDADE", True, COR_DESTAQUE),
            (_PADDING, y + 10),
        )
        y += 32
        for linha in curiosidade:
            camada.blit(
                self._fontes.pequena.render(linha, True, COR_TEXTO), (_PADDING, y)
            )
            y += 18

        # Lembrete de como sair. A ficha abre por gesto e some por gesto, então
        # sem esta linha o usuário de teclado não tem como saber que o ESC vale.
        camada.blit(
            self._fontes.mini.render(
                "solte o L ou aperte ESC para fechar", True, COR_TEXTO_SECUNDARIO
            ),
            (_PADDING, int(altura) - 22),
        )

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


__all__ = ["FichaLua", "formatar_massa", "formatar_periodo", "linhas_da_ficha_lua"]
