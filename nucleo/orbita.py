"""Cinemática da cena: onde cada corpo está em um dado instante.

As órbitas são circulares e coplanares (simplificação deliberada — excentricidade
e inclinação estão fora de escopo). O que é fiel aqui são as *proporções entre
períodos*: um ano de Netuno continua durando ~165 anos terrestres.
"""

from __future__ import annotations

import math

from config import (
    CINTURAO_UA_EXTERNO,
    FATOR_ANEL_EXTERNO,
    FATOR_LUA_COMPACTO_MAX,
    FATOR_LUA_COMPACTO_MIN,
    FOLGA_LUA_APOS_ANEL,
    CINTURAO_UA_INTERNO,
    EXPOENTE_RAIO_CORPO,
    EXPOENTE_PERIODO_LUA,
    FATOR_ROTACAO_PROPRIA,
    PERIODO_LUA_REFERENCIA_DIAS,
    RAIO_LUA_PX,
    RAIO_ORBITA_LUA_PX,
    RAIO_ORBITA_MAX_PX,
    RAIO_ORBITA_MIN_PX,
    PERIODO_CINTURAO_DIAS,
    RAIO_PLANETA_BASE_PX,
    RAIO_SOL_PX,
    ZOOM_MINIMO_PARA_LUAS,
    ZOOM_VISAO_GERAL,
)
from dados.planetas import (
    CORPOS,
    DIAMETRO_REFERENCIA_KM,
    DISTANCIA_UA_MAXIMA,
    DISTANCIA_UA_MINIMA,
    CorpoCeleste,
    LUAS_MENORES,
    LuaMenor,
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
    if corpo.eh_satelite:
        return RAIO_LUA_PX
    razao = corpo.diametro_km / DIAMETRO_REFERENCIA_KM
    return RAIO_PLANETA_BASE_PX * (razao**EXPOENTE_RAIO_CORPO)


def periodo_aparente_da_lua(periodo_real_dias: float) -> float:
    """Período que a lua *aparenta* ter na tela, em dias simulados.

    Na escala padrão passam 12 dias por segundo. Com o período real, Fobos
    (0,319 dia) daria 37 voltas por segundo — um borrão. Mas também não dá para
    dividir tudo pelo mesmo número: entre Fobos e Calisto há um fator 52, então
    o ajuste que salva a mais rápida congela a mais lenta.

    Por isso a mesma lei de potência usada nos raios: expoente < 1 **comprime a
    faixa** em vez de deslocá-la. A ordem real é preservada — lua interna ainda
    gira mais rápido que a externa, que é verdade física — mas o intervalo
    inteiro cai em 7 a 31 segundos por volta, tempo de ler o nome.

    O sinal é preservado: Tritão tem período negativo porque orbita Netuno ao
    contrário, e elevar um negativo a 0,38 daria número complexo.
    """
    if periodo_real_dias == 0.0:
        return 0.0
    sentido = 1.0 if periodo_real_dias > 0.0 else -1.0
    razao = abs(periodo_real_dias) ** EXPOENTE_PERIODO_LUA
    return sentido * PERIODO_LUA_REFERENCIA_DIAS * razao


def angulo_orbital(corpo: CorpoCeleste, tempo_dias: float) -> float:
    """Ângulo orbital (radianos) do corpo no instante simulado informado."""
    if corpo.periodo_orbital_dias <= 0.0:
        return corpo.fase_inicial
    # A Lua da Terra é satélite e passa pela mesma compressão das luas menores:
    # senão ela sozinha giraria 5x mais rápido que as de Júpiter, ao lado.
    periodo = (
        periodo_aparente_da_lua(corpo.periodo_orbital_dias)
        if corpo.eh_satelite
        else corpo.periodo_orbital_dias
    )
    voltas = tempo_dias / periodo
    return corpo.fase_inicial + 2.0 * math.pi * voltas


def posicao_orbital(corpo: CorpoCeleste, tempo_dias: float) -> tuple[float, float]:
    """Posição (x, y) do corpo em unidades de mundo, com o Sol na origem.

    Para satélites, devolve o deslocamento relativo ao corpo-pai (sem somá-lo).
    """
    if corpo.eh_satelite:
        angulo = angulo_orbital(corpo, tempo_dias)
        return (
            RAIO_ORBITA_LUA_PX * math.cos(angulo),
            RAIO_ORBITA_LUA_PX * math.sin(angulo),
        )
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
    """Posição de todos os corpos no instante informado, indexada pelo nome.

    Planetas são resolvidos primeiro; satélites somam o offset ao corpo-pai.
    """
    posicoes: dict[str, tuple[float, float]] = {}
    # Primeiro: corpos que orbitam o Sol (planetas + Sol).
    for corpo in CORPOS:
        if not corpo.eh_satelite:
            posicoes[corpo.nome] = posicao_orbital(corpo, tempo_dias)
    # Depois: satélites (offset sobre a posição do corpo-pai).
    for corpo in CORPOS:
        if corpo.eh_satelite:
            pai = posicoes.get(corpo.orbita_em_torno_de or "", (0.0, 0.0))
            rel = posicao_orbital(corpo, tempo_dias)
            posicoes[corpo.nome] = (pai[0] + rel[0], pai[1] + rel[1])
    return posicoes


# Faixa de raios usada no catálogo, para comprimir proporcionalmente: a lua
# mais interna continua sendo a mais interna também no modo compacto.
_FATOR_LUA_MIN = min(l.raio_orbita_px for l in LUAS_MENORES)
_FATOR_LUA_MAX = max(l.raio_orbita_px for l in LUAS_MENORES)


def fator_orbita_lua(fator_base: float, zoom: float, tem_aneis: bool = False) -> float:
    """Raio orbital da lua (em raios do planeta), adaptado ao zoom.

    Na visão geral não há espaço para o raio cheio: as luas de Júpiter
    precisariam de 105 px e só existem 70 px até Saturno. Em vez de escondê-las,
    o sistema inteiro é **comprimido** para um anel colado ao planeta e vai se
    abrindo conforme a câmera aproxima, até a configuração real a partir de
    ``ZOOM_MINIMO_PARA_LUAS``.

    A compressão preserva a ORDEM: a lua mais interna do catálogo continua
    sendo a mais interna no anel compacto.
    """
    fracao = (fator_base - _FATOR_LUA_MIN) / (_FATOR_LUA_MAX - _FATOR_LUA_MIN)
    compacto = FATOR_LUA_COMPACTO_MIN + fracao * (
        FATOR_LUA_COMPACTO_MAX - FATOR_LUA_COMPACTO_MIN
    )
    if tem_aneis:
        # Sem este deslocamento as luas de Saturno cairiam dentro dos anéis,
        # que se estendem até FATOR_ANEL_EXTERNO raios.
        compacto += FATOR_ANEL_EXTERNO + FOLGA_LUA_APOS_ANEL - FATOR_LUA_COMPACTO_MIN

    # A abertura começa em ZERO no zoom da visão geral — não em zoom zero.
    # Dividir direto por ZOOM_MINIMO_PARA_LUAS deixava o sistema 56% aberto já
    # no panorama, que é justamente onde ele não pode caber.
    faixa = max(1e-6, ZOOM_MINIMO_PARA_LUAS - ZOOM_VISAO_GERAL)
    abertura = min(1.0, max(0.0, (zoom - ZOOM_VISAO_GERAL) / faixa))
    return compacto + (fator_base - compacto) * abertura


def posicao_da_lua_menor(
    lua: LuaMenor,
    posicao_planeta: tuple[float, float],
    raio_planeta: float,
    tempo_dias: float,
    fator: float | None = None,
) -> tuple[float, float]:
    """Posição de uma lua menor, em unidades de mundo.

    O raio da órbita é múltiplo do raio DESENHADO do planeta, não da distância
    real: em escala fiel Fobos ficaria dentro do disco de Marte e Calisto a 26
    raios de Júpiter, fora da tela em qualquer zoom útil.
    """
    if lua.periodo_orbital_dias == 0.0:
        angulo = lua.fase_inicial
    else:
        periodo = periodo_aparente_da_lua(lua.periodo_orbital_dias)
        angulo = lua.fase_inicial + 2.0 * math.pi * (tempo_dias / periodo)
    raio = raio_planeta * (fator if fator is not None else lua.raio_orbita_px)
    return (
        posicao_planeta[0] + raio * math.cos(angulo),
        posicao_planeta[1] + raio * math.sin(angulo),
    )


def faixa_do_cinturao() -> tuple[float, float]:
    """Raios interno e externo do cinturão de asteroides, em unidades de mundo.

    Passam pela mesma compressão logarítmica das órbitas, então o cinturão cai
    exatamente entre Marte e Júpiter na tela — como acontece de verdade.
    """
    return (
        raio_orbital_px(CINTURAO_UA_INTERNO),
        raio_orbital_px(CINTURAO_UA_EXTERNO),
    )


def angulo_do_cinturao(tempo_dias: float) -> float:
    """Rotação do cinturão inteiro, tratado como um corpo só."""
    return 2.0 * math.pi * (tempo_dias / PERIODO_CINTURAO_DIAS)


def angulo_iluminacao(posicao: tuple[float, float]) -> float:
    """Ângulo (radianos) da direção Sol -> corpo, usado para o terminador."""
    x, y = posicao
    if x == 0.0 and y == 0.0:
        return 0.0
    return math.atan2(y, x)


__all__ = [
    "angulo_do_cinturao",
    "angulo_iluminacao",
    "angulo_orbital",
    "fase_rotacao",
    "faixa_do_cinturao",
    "fator_orbita_lua",
    "posicao_da_lua_menor",
    "posicao_orbital",
    "posicoes_do_sistema",
    "raio_corpo_px",
    "raio_orbital_px",
]
