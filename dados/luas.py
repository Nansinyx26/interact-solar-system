"""Catálogo das luas dos demais planetas.

Estava dentro de ``dados/planetas.py``, junto com os 9 corpos principais. Saiu
para cá quando a ficha da lua passou a exigir massa e composição: o arquivo
misturava duas coisas com ciclos de vida diferentes — os 9 corpos são fixos e
têm gesto próprio, as luas são um catálogo que cresce.

Os corpos principais continuam lá; ``planetas.py`` importa daqui e faz a fusão
(a Lua da Terra vive em ``CORPOS``, porque tem gesto próprio, mas precisa
aparecer também na listagem de luas). O sentido do import é este de propósito:
``luas.py`` não conhece ``planetas.py``, então não há ciclo.

Dados astronômicos: NASA Planetary Fact Sheet e JPL Solar System Dynamics.

ATENÇÃO à escala: ``raio_orbita_px`` é VISUAL, não proporcional. Em escala real
Calisto ficaria a 26 raios de Júpiter e Fobos a 1,4 raios de Marte — as luas
internas sumiriam dentro do planeta. O que preservamos é a ordem e o
espaçamento relativo dentro de cada sistema.
"""

from __future__ import annotations

from dataclasses import dataclass

Cor = tuple[int, int, int]


@dataclass(frozen=True)
class LuaMenor:
    """Satélite secundário: aparece na cena e tem ficha, mas não tem gesto próprio.

    Os gestos vão de 0 a 10 e todos já estão ocupados (0-8 Sol e planetas, 9
    Lua, 10 visão geral). Estas luas são alcançadas pelo MODO LUA: uma mão em
    "L" mais o número da outra mão.
    """

    nome: str
    planeta: str  # nome do corpo-pai
    diametro_km: float
    distancia_km: float  # distância média real ao planeta
    periodo_orbital_dias: float  # negativo = órbita retrógrada
    raio_orbita_px: float  # raio DESENHADO, em múltiplos do raio do planeta
    cor: Cor
    fase_inicial: float
    fato_curioso: str
    # Campos exigidos pela ficha da lua. Ficam no fim e com padrão para que
    # acrescentar uma lua nova sem massa medida não quebre o catálogo — vários
    # satélites pequenos só têm massa estimada.
    massa_kg: float = 0.0
    composicao: str = ""

    @property
    def raio_km(self) -> float:
        """Raio médio, em km. A ficha mostra raio; o catálogo guarda diâmetro."""
        return self.diametro_km / 2.0

    @property
    def retrograda(self) -> bool:
        """True quando a lua orbita no sentido contrário ao giro do planeta."""
        return self.periodo_orbital_dias < 0


LUAS_MENORES: tuple[LuaMenor, ...] = (
    # --- Marte ---------------------------------------------------------
    LuaMenor("Fobos", "Marte", 22.5, 9_376, 0.319, 2.2,
             (150, 140, 130), 0.0,
             "Está tão perto de Marte que nasce a oeste e se põe a leste.",
             massa_kg=1.0659e16,
             composicao="Rocha carbonácea porosa, coberta por poeira e sulcos"),
    LuaMenor("Deimos", "Marte", 12.4, 23_463, 1.263, 3.2,
             (170, 158, 145), 2.1,
             "A menor lua do Sistema Solar entre as bem conhecidas.",
             massa_kg=1.4762e15,
             composicao="Rocha carbonácea sob um manto espesso de regolito"),
    # --- Júpiter -------------------------------------------------------
    LuaMenor("Amalteia", "Júpiter", 167, 181_366, 0.498, 1.7,
             (196, 120, 96), 1.1,
             "É avermelhada e tem formato irregular, como uma batata.",
             massa_kg=2.08e18,
             composicao="Gelo poroso tingido de enxofre vindo de Io"),
    LuaMenor("Io", "Júpiter", 3643, 421_700, 1.769, 2.1,
             (232, 214, 120), 0.4,
             "O corpo com mais atividade vulcânica do Sistema Solar.",
             massa_kg=8.9319e22,
             composicao="Silicatos e enxofre; núcleo de ferro, sem gelo"),
    LuaMenor("Europa", "Júpiter", 3122, 671_034, 3.551, 2.6,
             (216, 206, 190), 2.0,
             "Sob a crosta de gelo há um oceano de água líquida.",
             massa_kg=4.7998e22,
             composicao="Crosta de gelo de água sobre oceano salgado e manto rochoso"),
    LuaMenor("Ganimedes", "Júpiter", 5268, 1_070_412, 7.155, 3.2,
             (168, 156, 140), 3.7,
             "É a maior lua do Sistema Solar — maior que Mercúrio.",
             massa_kg=1.4819e23,
             composicao="Gelo e silicatos; núcleo de ferro com campo magnético próprio"),
    LuaMenor("Calisto", "Júpiter", 4821, 1_882_709, 16.689, 4.0,
             (128, 118, 108), 5.2,
             "A superfície mais craterada que se conhece.",
             massa_kg=1.0759e23,
             composicao="Mistura homogênea de gelo e rocha, sem diferenciação"),
    # --- Saturno -------------------------------------------------------
    LuaMenor("Encélado", "Saturno", 504, 237_948, 1.37, 1.8,
             (236, 240, 244), 4.4,
             "Lança gêiseres de água pelo polo sul.",
             massa_kg=1.0802e20,
             composicao="Gelo de água quase puro sobre oceano subsuperficial"),
    LuaMenor("Dione", "Saturno", 1123, 377_396, 2.737, 2.2,
             (206, 204, 198), 1.9,
             "Tem penhascos de gelo que chegam a centenas de metros.",
             massa_kg=1.0955e21,
             composicao="Gelo de água com núcleo de silicatos"),
    LuaMenor("Reia", "Saturno", 1527, 527_108, 4.518, 2.7,
             (194, 192, 186), 3.1,
             "A segunda maior lua de Saturno, feita quase toda de gelo.",
             massa_kg=2.3065e21,
             composicao="Cerca de três quartos de gelo de água e um quarto de rocha"),
    LuaMenor("Titã", "Saturno", 5150, 1_221_870, 15.945, 3.3,
             (214, 168, 92), 1.2,
             "Tem atmosfera densa e rios de metano líquido.",
             massa_kg=1.3452e23,
             composicao="Gelo e rocha sob atmosfera espessa de nitrogênio e metano"),
    LuaMenor("Jápeto", "Saturno", 1469, 3_560_820, 79.33, 4.1,
             (150, 140, 126), 5.6,
             "Um hemisfério é escuro como carvão e o outro, branco como neve.",
             massa_kg=1.8056e21,
             composicao="Gelo de água com depósito escuro de compostos orgânicos"),
    # --- Urano ---------------------------------------------------------
    LuaMenor("Miranda", "Urano", 472, 129_900, 1.413, 1.8,
             (188, 190, 192), 2.7,
             "Tem um penhasco de 20 km, o mais alto conhecido.",
             massa_kg=6.59e19,
             composicao="Gelo de água e silicatos, com terreno remendado"),
    LuaMenor("Ariel", "Urano", 1158, 190_900, 2.52, 2.2,
             (198, 196, 190), 0.5,
             "A superfície mais clara e jovem entre as luas de Urano.",
             massa_kg=1.353e21,
             composicao="Gelo de água e dióxido de carbono sobre rocha"),
    LuaMenor("Umbriel", "Urano", 1169, 266_000, 4.144, 2.6,
             (132, 130, 128), 4.0,
             "A mais escura das grandes luas de Urano.",
             massa_kg=1.172e21,
             composicao="Gelo escurecido por material carbonáceo antigo"),
    LuaMenor("Titânia", "Urano", 1578, 435_910, 8.706, 3.1,
             (176, 166, 158), 0.9,
             "A maior lua de Urano, com cânions de centenas de quilômetros.",
             massa_kg=3.527e21,
             composicao="Metade gelo de água, metade rocha; traços de CO2"),
    LuaMenor("Oberon", "Urano", 1523, 583_520, 13.463, 3.7,
             (150, 142, 136), 3.4,
             "A mais externa das grandes luas de Urano.",
             massa_kg=3.014e21,
             composicao="Gelo de água e rocha, com crateras de fundo escuro"),
    # --- Netuno --------------------------------------------------------
    LuaMenor("Galateia", "Netuno", 176, 61_953, 0.429, 1.7,
             (160, 168, 176), 3.0,
             "Sua gravidade mantém um dos anéis de Netuno agrupado.",
             massa_kg=2.12e18,
             composicao="Gelo escuro e poroso, de formato irregular"),
    LuaMenor("Larissa", "Netuno", 194, 73_548, 0.555, 2.0,
             (172, 178, 184), 5.0,
             "Tem forma irregular e superfície muito craterada.",
             massa_kg=4.2e18,
             composicao="Gelo de água misturado a material rochoso escuro"),
    LuaMenor("Proteu", "Netuno", 420, 117_647, 1.122, 2.4,
             (150, 156, 162), 0.7,
             "É quase o maior corpo que a gravidade não conseguiu arredondar.",
             massa_kg=4.4e19,
             composicao="Gelo de água sob superfície muito escura e porosa"),
    LuaMenor("Tritão", "Netuno", 2707, 354_759, -5.877, 2.9,
             (198, 206, 210), 1.7,
             "Orbita ao contrário: foi capturado, não se formou ali.",
             massa_kg=2.14e22,
             composicao="Gelo de nitrogênio e metano sobre manto de água e rocha"),
    LuaMenor("Nereida", "Netuno", 340, 5_513_400, 360.13, 3.8,
             (166, 170, 174), 4.2,
             "Tem a órbita mais alongada entre as luas conhecidas.",
             massa_kg=3.1e19,
             composicao="Gelo de água com superfície irregular e pouco refletiva"),
)


def indexar_por_planeta(luas: tuple[LuaMenor, ...]) -> dict[str, tuple[LuaMenor, ...]]:
    """Agrupa as luas por nome do planeta-pai, preservando a ordem do catálogo.

    A ordem importa: é ela que numera as luas no HUD e no gesto. As entradas de
    cada planeta já estão listadas da mais interna para a mais externa, que é a
    ordem que o usuário vê na tela.
    """
    indice: dict[str, tuple[LuaMenor, ...]] = {}
    for lua in luas:
        indice[lua.planeta] = indice.get(lua.planeta, ()) + (lua,)
    return indice


__all__ = ["Cor", "LUAS_MENORES", "LuaMenor", "indexar_por_planeta"]
