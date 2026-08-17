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
from ui.hud import Fontes, base_do_painel_status, desenhar_painel

# A ficha ocupa a coluna ESQUERDA, começando logo abaixo do painel de status e
# terminando onde o painel de gesto começa — o limite de baixo chega pronto de
# fora, porque depende do tamanho corrente da janela.
_TOPO_FICHA = base_do_painel_status()
# Cada item é rótulo + N linhas de valor + respiro; alguns valores ocupam duas
# linhas (UA e km, por exemplo), então a altura do item é calculada, não fixa.
_ALTURA_ROTULO = 17
_ALTURA_LINHA_VALOR = 17
_RESPIRO_ITEM = 10

# Acima deste período, a sobra de horas deixa de ser informação e vira ruído:
# ninguém aprende nada com "4.333 dias e 14 horas". Abaixo dele a sobra é o
# ponto (a Terra: 365 dias e 6 horas, que é a origem do ano bissexto).
_LIMITE_HORAS_NO_PERIODO_DIAS = 400.0


def formatar_inteiro(valor: float) -> str:
    """Inteiro no padrão pt-BR (1.392.700)."""
    return f"{valor:,.0f}".replace(",", ".")


def formatar_decimal(valor: float, casas: int = 2) -> str:
    """Decimal no padrão pt-BR (1,52)."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


def _dias_e_horas(dias: float) -> str:
    """Dias inteiros e, quando a sobra importa, as horas restantes.

    A Terra leva 365 dias **e 6 horas** para dar uma volta, e são essas 6 horas
    que explicam o ano bissexto: quatro voltas acumulam um dia inteiro de
    sobra. Arredondar para "365 dias" apagava justamente a parte que a ficha
    existe para ensinar — e é a resposta da questão 10 do quiz, que o aluno
    deveria conseguir conferir aqui.

    Acima de ~400 dias as horas viram ruído (Júpiter leva 4.333 dias; as 14 h de
    sobra não dizem nada a ninguém), então só os corpos de período curto as
    recebem.
    """
    if dias >= _LIMITE_HORAS_NO_PERIODO_DIAS:
        return f"{formatar_inteiro(dias)} dias"
    inteiros = int(dias)
    horas = round((dias - inteiros) * 24.0)
    if horas >= 24:
        inteiros, horas = inteiros + 1, 0
    if horas == 0:
        return f"{formatar_inteiro(inteiros)} dias"
    return f"{formatar_inteiro(inteiros)} dias e {horas} horas"


def _formatar_periodo_orbital(corpo: CorpoCeleste) -> str:
    """Período orbital em dias e, quando faz sentido, em anos terrestres."""
    if corpo.periodo_orbital_dias <= 0:
        return "— (orbita o centro da Galáxia)"
    dias = corpo.periodo_orbital_dias
    if dias < 365.26:
        return f"{formatar_decimal(dias, 2)} dias"
    anos = dias / 365.26
    return f"{formatar_decimal(anos, 2)} anos ({_dias_e_horas(dias)})"


def _formatar_rotacao(corpo: CorpoCeleste) -> str:
    """Período de rotação, sinalizando giro retrógrado."""
    horas = corpo.periodo_rotacao_horas
    sufixo = " (retrógrada)" if horas < 0 else ""
    horas = abs(horas)
    if horas >= 48:
        return f"{formatar_decimal(horas / 24, 2)} dias{sufixo}"
    return f"{formatar_decimal(horas, 2)} h{sufixo}"


def _rotulo_distancia(corpo: CorpoCeleste) -> str:
    """Rótulo da linha de distância — satélites medem do corpo-pai, não do Sol."""
    if corpo.eh_satelite:
        return f"Distância média à {corpo.orbita_em_torno_de}"
    return "Distância média ao Sol"


def _formatar_distancia(corpo: CorpoCeleste) -> str:
    """Distância média em UA e km, ou só em km para satélites.

    A UA é uma unidade heliocêntrica: expressar a órbita da Lua em UA daria
    0,00257 — um número exato e inútil. Para satélites fica só o valor em km.
    """
    if corpo.eh_satelite:
        return f"{formatar_inteiro(corpo.distancia_km)} km"
    if corpo.distancia_ua <= 0:
        return "0 (centro do sistema)"
    return (
        f"{formatar_decimal(corpo.distancia_ua, 3)} UA\n"
        f"{formatar_inteiro(corpo.distancia_km)} km"
    )


# O ``tipo`` é um identificador interno (sem acento, minúsculo): o card mostra a
# forma legível, senão a Lua aparece como "Satelite".
_NOMES_DE_TIPO: dict[str, str] = {
    "estrela": "Estrela",
    "rochoso": "Planeta rochoso",
    "gasoso": "Gigante gasoso",
    "satelite": "Satélite natural",
}


def nome_do_tipo(corpo: CorpoCeleste) -> str:
    """Nome legível do tipo do corpo, para o subtítulo da ficha."""
    return _NOMES_DE_TIPO.get(corpo.tipo, corpo.tipo.capitalize())


def linhas_da_ficha(corpo: CorpoCeleste) -> list[tuple[str, str]]:
    """Pares (rótulo, valor) exibidos no card."""
    return [
        ("Diâmetro equatorial", f"{formatar_inteiro(corpo.diametro_km)} km"),
        (_rotulo_distancia(corpo), _formatar_distancia(corpo)),
        ("Período orbital", _formatar_periodo_orbital(corpo)),
        ("Período de rotação", _formatar_rotacao(corpo)),
        ("Luas conhecidas", formatar_inteiro(corpo.luas)),
        ("Temperatura média", f"{formatar_decimal(corpo.temperatura_media_c, 1)} °C"),
        ("Inclinação axial", f"{formatar_decimal(corpo.inclinacao_axial_graus, 2)}°"),
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
        self._desenhar_card(superficie, self._corpo, fator, limite_inferior)

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

        # Coluna da ESQUERDA, no lugar da legenda de dedos (que o HUD esconde
        # enquanto há foco). A direita inteira é da webcam e da assinatura.
        retangulo = pygame.Rect(
            int(MARGEM_HUD - deslocamento),
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
        # Nome e subtítulo vivem dentro do card (mesma estrutura da versão web):
        # não há mais título flutuante, que duplicaria o nome nesta coluna.
        camada.blit(self._fontes.grande.render(corpo.nome, True, COR_TEXTO), (18, 16))
        camada.blit(
            self._fontes.mini.render(
                f"{nome_do_tipo(corpo)} · gesto {corpo.indice_gesto}".upper(),
                True,
                COR_DESTAQUE,
            ),
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


__all__ = [
    "FichaPlaneta",
    "formatar_decimal",
    "formatar_inteiro",
    "linhas_da_ficha",
    "nome_do_tipo",
]
