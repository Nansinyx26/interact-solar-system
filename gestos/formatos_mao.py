"""Classificação da FORMA da mão, além da simples contagem de dedos.

Hoje só existe uma forma especial: o **"L"** — polegar e indicador estendidos em
ângulo aberto, os outros três fechados. Ele não é um número: é um *modificador*
de modo. Enquanto uma mão faz o L, o número mostrado pela outra deixa de
significar planeta e passa a significar índice de lua.

Isso resolve um limite duro do projeto: a contagem vai de 0 a 10 e todos os
valores já estão ocupados (Sol, 8 planetas, Lua e visão geral). Não sobrava
número para selecionar luas — mas sobrava *forma*.

O módulo não conhece pygame nem estado: recebe landmarks, devolve classificação.
"""

from __future__ import annotations

import math

import numpy as np

from config import ANGULO_L_MAXIMO_GRAUS, ANGULO_L_MINIMO_GRAUS
from gestos.contador import (
    DEDOS_LONGOS,
    INDICADOR_MCP,
    POLEGAR_MCP,
    POLEGAR_PONTA,
    _dedo_estendido,
    _polegar_levantado,
    _referencial_da_palma,
)

# Ponta do indicador, para o vetor do dedo.
INDICADOR_PONTA = DEDOS_LONGOS[0][0]


def angulo_entre(vetor_a: np.ndarray, vetor_b: np.ndarray) -> float:
    """Ângulo em graus entre dois vetores 2D (0 a 180)."""
    norma_a = float(np.linalg.norm(vetor_a))
    norma_b = float(np.linalg.norm(vetor_b))
    if norma_a < 1e-9 or norma_b < 1e-9:
        return 0.0
    cosseno = float(np.dot(vetor_a, vetor_b)) / (norma_a * norma_b)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosseno))))


def abertura_do_L(landmarks: np.ndarray) -> float:
    """Ângulo entre o polegar (MCP→ponta) e o indicador (MCP→ponta), em graus.

    Usa vetores relativos a juntas da própria mão, nunca coordenadas de tela:
    é isso que faz o "L" ser reconhecido de cabeça para baixo ou espelhado.
    """
    vetor_polegar = landmarks[POLEGAR_PONTA, :2] - landmarks[POLEGAR_MCP, :2]
    vetor_indicador = landmarks[INDICADOR_PONTA, :2] - landmarks[INDICADOR_MCP, :2]
    return angulo_entre(vetor_polegar, vetor_indicador)


def eh_formato_L(landmarks: np.ndarray, lado: str) -> bool:
    """True quando a mão forma um "L".

    Três condições, todas necessárias:

    1. **Indicador estendido** e **polegar estendido**.
    2. **Médio, anelar e mínimo dobrados.** É o que separa o L de uma mão
       aberta e, principalmente, do "2" — que também tem dois dedos para cima,
       mas os errados (indicador + médio, com o polegar recolhido).
    3. **Ângulo entre polegar e indicador entre 50° e 130°.** Sem isso, um gesto
       de apontar (dedos quase paralelos) passaria como L.

    Funciona com qualquer mão e em qualquer rotação: o referencial vem da
    própria palma, e o ângulo usa vetores relativos.
    """
    eixo_dedos, eixo_polegar, tamanho = _referencial_da_palma(landmarks, lado)

    ponta_indicador, pip_indicador = DEDOS_LONGOS[0]
    if not _dedo_estendido(
        landmarks, ponta_indicador, pip_indicador, eixo_dedos, tamanho
    ):
        return False

    # Os três dedos restantes precisam estar recolhidos.
    for ponta, pip in DEDOS_LONGOS[1:]:
        if _dedo_estendido(landmarks, ponta, pip, eixo_dedos, tamanho):
            return False

    if not _polegar_levantado(landmarks, eixo_polegar, tamanho):
        return False

    abertura = abertura_do_L(landmarks)
    return ANGULO_L_MINIMO_GRAUS <= abertura <= ANGULO_L_MAXIMO_GRAUS


__all__ = ["abertura_do_L", "angulo_entre", "eh_formato_L"]
