"""Cinemática da cena: onde cada corpo está em um dado instante.

As órbitas são circulares e coplanares (simplificação deliberada — excentricidade
e inclinação estão fora de escopo). O que é fiel aqui são as *proporções entre
períodos*: um ano de Netuno continua durando ~165 anos terrestres.
"""

from __future__ import annotations

import math

from config import (
    EXPOENTE_RAIO_CORPO,
    FATOR_ROTACAO_PROPRIA,
    RAIO_ORBITA_MAX_PX,
    RAIO_ORBITA_MIN_PX,
    RAIO_PLANETA_BASE_PX,
    RAIO_SOL_PX,
)
from dados.planetas import (
    CORPOS,
    DIAMETRO_REFERENCIA_KM,
    DISTANCIA_UA_MAXIMA,
    DISTANCIA_UA_MINIMA,
    CorpoCeleste,
)

_LN_UA_MIN = math.log(DISTANCIA_UA_MINIMA)
_LN_UA_MAX = math.log(DISTANCIA_UA_MAXIMA)


def raio_orbital_px(distancia_ua: float) -> float:
    """Converte distância média (UA) em raio orbital de tela (unidades de mundo).

    Compressão logarítmica: ver a justificativa completa em ``config.py``. Em
    escala linear, Mercúrio ficaria a 1,3% do raio de Netuno e sumiria dentro
    do Sol.
    """
    if distancia_ua <= 0.0:
        return 0.0
    fracao = (math.log(distancia_ua) - _LN_UA_MIN) / (_LN_UA_MAX - _LN_UA_MIN)
    return RAIO_ORBITA_MIN_PX + fracao * (RAIO_ORBITA_MAX_PX - RAIO_ORBITA_MIN_PX)


def raio_corpo_px(corpo: CorpoCeleste) -> float:
    """Raio desenhado do corpo, em unidades de mundo.

    Lei de potência com expoente < 1 (não é linear e nem tenta ser): sem ela,
    ou Mercúrio vira um ponto de 1 px ou Júpiter ocupa meia tela.
    """
    if corpo.eh_sol:
        return RAIO_SOL_PX
    razao = corpo.diametro_km / DIAMETRO_REFERENCIA_KM
    return RAIO_PLANETA_BASE_PX * (razao**EXPOENTE_RAIO_CORPO)


def angulo_orbital(corpo: CorpoCeleste, tempo_dias: float) -> float:
    """Ângulo orbital (radianos) do corpo no instante simulado informado."""
    if corpo.periodo_orbital_dias <= 0.0:
        return corpo.fase_inicial
    voltas = tempo_dias / corpo.periodo_orbital_dias
    return corpo.fase_inicial + 2.0 * math.pi * voltas


def posicao_orbital(corpo: CorpoCeleste, tempo_dias: float) -> tuple[float, float]:
    """Posição (x, y) do corpo em unidades de mundo, com o Sol na origem."""
    raio = raio_orbital_px(corpo.distancia_ua)
    if raio == 0.0:
        return (0.0, 0.0)
    angulo = angulo_orbital(corpo, tempo_dias)
    return (raio * math.cos(angulo), raio * math.sin(angulo))


def fase_rotacao(corpo: CorpoCeleste, tempo_dias: float) -> float:
    """Fase da rotação própria, normalizada em [0, 1).

    O sinal do período é preservado: Vênus e Urano giram para o outro lado.
    A velocidade é comprimida por ``FATOR_ROTACAO_PROPRIA`` — na proporção real
    Júpiter (9,93 h) giraria rápido demais para o olho acompanhar.
    """
    if corpo.periodo_rotacao_horas == 0.0:
        return 0.0
    periodo_dias = corpo.periodo_rotacao_horas / 24.0
    voltas = (tempo_dias * FATOR_ROTACAO_PROPRIA) / periodo_dias
    return voltas % 1.0


def posicoes_do_sistema(tempo_dias: float) -> dict[str, tuple[float, float]]:
    """Posição de todos os corpos no instante informado, indexada pelo nome."""
    return {corpo.nome: posicao_orbital(corpo, tempo_dias) for corpo in CORPOS}


def angulo_iluminacao(posicao: tuple[float, float]) -> float:
    """Ângulo (radianos) da direção Sol -> corpo, usado para o terminador."""
    x, y = posicao
    if x == 0.0 and y == 0.0:
        return 0.0
    return math.atan2(y, x)


__all__ = [
    "angulo_iluminacao",
    "angulo_orbital",
    "fase_rotacao",
    "posicao_orbital",
    "posicoes_do_sistema",
    "raio_corpo_px",
    "raio_orbital_px",
]
