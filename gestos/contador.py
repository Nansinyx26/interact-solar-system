"""Conversão de landmarks da mão em número de dedos levantados.

A heurística ingênua (comparar o `y` da ponta com o `y` da junta PIP) só funciona
com a mão em pé. Aqui usamos a versão robusta: montamos um referencial da própria
palma e projetamos os dedos nele, o que mantém a contagem correta com a mão
girada ou inclinada. A alternativa simples está descrita nos comentários.
"""

from __future__ import annotations

import numpy as np

from config import (
    LIMIAR_DEDO_ESTENDIDO,
    LIMIAR_POLEGAR_ESTENDIDO,
    MARGEM_QUADRO,
    MARGEM_ZONA_CINZENTA_POLEGAR,
    MAX_LANDMARKS_FORA_DO_QUADRO,
    RAZAO_POLEGAR_ABERTO,
    TAMANHO_PALMA_MINIMO,
)

# Índices dos 21 landmarks do MediaPipe Hands.
PULSO = 0
POLEGAR_MCP = 2
POLEGAR_IP = 3
POLEGAR_PONTA = 4
INDICADOR_MCP = 5
MEDIO_MCP = 9
MINIMO_MCP = 17

# (ponta, PIP) dos quatro dedos longos.
DEDOS_LONGOS: tuple[tuple[int, int], ...] = ((8, 6), (12, 10), (16, 14), (20, 18))


def mao_dentro_do_quadro(landmarks: np.ndarray) -> bool:
    """Indica se a mão está enquadrada o bastante para ser contada.

    Mão cortada pela borda produz coordenadas extrapoladas pelo MediaPipe e
    contagem errada. Mas exigir os 21 pontos dentro de [0, 1] é rígido demais:
    o modelo extrapola um pouco mesmo com a mão inteira visível, e com as duas
    mãos no quadro (necessárias para 6, 7 e 8) isso descartava quase tudo.
    Por isso toleramos alguns pontos fora antes de invalidar a leitura.
    """
    pontos = landmarks[:, :2]
    fora = np.count_nonzero(
        (pontos < -MARGEM_QUADRO) | (pontos > 1.0 + MARGEM_QUADRO)
    )
    return bool(fora <= MAX_LANDMARKS_FORA_DO_QUADRO)


def _referencial_da_palma(
    landmarks: np.ndarray, lado: str
) -> tuple[np.ndarray, np.ndarray, float]:
    """Devolve (eixo_dedos, eixo_polegar, tamanho_da_palma).

    - ``eixo_dedos``: pulso -> MCP do médio. É a direção "para cima" da mão,
      seja qual for a rotação dela na imagem.
    - ``eixo_polegar``: MCP do mínimo -> MCP do indicador. Aponta sempre para o
      lado do polegar, tanto na mão esquerda quanto na direita — é justamente
      por ser tirado da anatomia que ele já embute o ``handedness``.
    - ``tamanho_da_palma``: escala usada para normalizar os limiares, deixando a
      contagem independente da distância até a câmera.
    """
    origem = landmarks[PULSO, :2]
    vetor_dedos = landmarks[MEDIO_MCP, :2] - origem
    tamanho = float(np.linalg.norm(vetor_dedos))
    if tamanho < TAMANHO_PALMA_MINIMO:
        # Palma degenerada (mão exatamente de perfil): eixos neutros.
        return np.array([0.0, -1.0]), np.array([1.0, 0.0]), TAMANHO_PALMA_MINIMO
    eixo_dedos = vetor_dedos / tamanho

    vetor_lateral = landmarks[INDICADOR_MCP, :2] - landmarks[MINIMO_MCP, :2]
    norma_lateral = float(np.linalg.norm(vetor_lateral))
    if norma_lateral < TAMANHO_PALMA_MINIMO:
        # Índice e mínimo colapsados: sem anatomia utilizável, o único palpite
        # possível sobre o lado do polegar vem do handedness do MediaPipe.
        sinal = 1.0 if lado == "Right" else -1.0
        eixo_polegar = sinal * np.array([-eixo_dedos[1], eixo_dedos[0]])
    else:
        eixo_polegar = vetor_lateral / norma_lateral
    return eixo_dedos, eixo_polegar, tamanho


def _polegar_levantado(
    landmarks: np.ndarray, eixo_polegar: np.ndarray, tamanho_palma: float
) -> bool:
    """Decide se o polegar está aberto.

    Critério principal: projetar o vetor MCP -> ponta do polegar no eixo lateral
    da palma. O polegar aberto se afasta para o lado; o fechado cruza a palma e
    a projeção vira quase zero (ou negativa).

    Na faixa ambígua entra o segundo critério, sugerido justamente por ser mais
    robusto: comparar a distância da PONTA e da articulação IP até a base do
    dedo mínimo — abrindo o polegar a ponta se afasta, dobrando ela se aproxima.

    (A regra clássica "comparar o x da ponta com o x do IP invertendo pelo
    handedness" foi descartada: ela depende da mão estar em pé na imagem e
    quebra com a mão girada, que é o caso comum em uso real.)
    """
    vetor = landmarks[POLEGAR_PONTA, :2] - landmarks[POLEGAR_MCP, :2]
    projecao = float(np.dot(vetor, eixo_polegar)) / tamanho_palma
    if projecao > LIMIAR_POLEGAR_ESTENDIDO + MARGEM_ZONA_CINZENTA_POLEGAR:
        return True
    if projecao < LIMIAR_POLEGAR_ESTENDIDO - MARGEM_ZONA_CINZENTA_POLEGAR:
        return False

    base_minimo = landmarks[MINIMO_MCP, :2]
    distancia_ponta = float(np.linalg.norm(landmarks[POLEGAR_PONTA, :2] - base_minimo))
    distancia_ip = float(np.linalg.norm(landmarks[POLEGAR_IP, :2] - base_minimo))
    return distancia_ponta > distancia_ip * RAZAO_POLEGAR_ABERTO


def contar_dedos(landmarks: np.ndarray, lado: str) -> int:
    """Conta quantos dedos de UMA mão estão levantados (0 a 5)."""
    eixo_dedos, eixo_polegar, tamanho = _referencial_da_palma(landmarks, lado)

    total = 0
    for ponta, pip in DEDOS_LONGOS:
        # Projeção no eixo da palma: equivale a "a ponta está acima da junta",
        # só que válido com a mão em qualquer ângulo.
        if _dedo_estendido(landmarks, ponta, pip, eixo_dedos, tamanho):
            total += 1

    if _polegar_levantado(landmarks, eixo_polegar, tamanho):
        total += 1
    return total


def _dedo_estendido(
    landmarks: np.ndarray, ponta: int, pip: int, eixo_dedos: np.ndarray, tamanho: float
) -> bool:
    """Projeta ponta e junta no eixo da palma para saber se o dedo está aberto."""
    origem = landmarks[PULSO, :2]
    projecao_ponta = float(np.dot(landmarks[ponta, :2] - origem, eixo_dedos))
    projecao_pip = float(np.dot(landmarks[pip, :2] - origem, eixo_dedos))
    return (projecao_ponta - projecao_pip) > LIMIAR_DEDO_ESTENDIDO * tamanho


def medir_pinca(landmarks: np.ndarray, lado: str) -> float | None:
    """Distância ponta do polegar <-> ponta do indicador, em palmas.

    Devolve ``None`` quando o indicador está dobrado: numa mão fechada as duas
    pontas também ficam próximas, e sem esta checagem mostrar 0 dedos (o Sol)
    seria confundido com uma pinça.

    Dividir pelo tamanho da palma é o que torna a medida independente da
    distância até a câmera — o mesmo princípio dos limiares de dedo.
    """
    eixo_dedos, _eixo_polegar, tamanho = _referencial_da_palma(landmarks, lado)
    ponta_indicador, pip_indicador = DEDOS_LONGOS[0]
    if not _dedo_estendido(landmarks, ponta_indicador, pip_indicador, eixo_dedos, tamanho):
        return None
    separacao = float(
        np.linalg.norm(landmarks[POLEGAR_PONTA, :2] - landmarks[ponta_indicador, :2])
    )
    return separacao / tamanho


def contar_dedos_total(maos: list[tuple[np.ndarray, str]]) -> int | None:
    """Soma os dedos de até duas mãos.

    Devolve ``None`` quando não há mão utilizável — alguma está cortada pela
    borda do quadro ou não há mão nenhuma. Uma mão só chega a 5; 6, 7 e 8 exigem
    as duas mãos (ex.: 5 + 3 = 8 -> Netuno).
    """
    if not maos:
        return None
    total = 0
    for landmarks, lado in maos:
        if not mao_dentro_do_quadro(landmarks):
            return None
        total += contar_dedos(landmarks, lado)
    return total


__all__ = [
    "DEDOS_LONGOS",
    "contar_dedos",
    "contar_dedos_total",
    "mao_dentro_do_quadro",
]
