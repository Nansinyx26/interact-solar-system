"""Catálogo dos 9 corpos celestes da cena (Sol + 8 planetas).

Todos os dados astronômicos são valores médios publicados pelo NASA Planetary
Fact Sheet. Nada aqui é baixado em runtime: é Python puro.
"""

from __future__ import annotations

from dataclasses import dataclass

Cor = tuple[int, int, int]


@dataclass(frozen=True)
class CorpoCeleste:
    """Um corpo do Sistema Solar, com dados reais e parâmetros de desenho."""

    # --- identidade / gesto -------------------------------------------------
    nome: str
    indice_gesto: int  # número de dedos que seleciona este corpo (0..8)
    tipo: str  # "estrela", "rochoso" ou "gasoso"

    # --- dados astronômicos reais (exibidos na ficha) -----------------------
    diametro_km: float
    distancia_ua: float  # distância média ao Sol (0 para o Sol)
    distancia_km: float
    periodo_orbital_dias: float  # 0 para o Sol
    periodo_rotacao_horas: float  # negativo = rotação retrógrada
    luas: int
    temperatura_media_c: float
    inclinacao_axial_graus: float
    fato_curioso: str

    # --- parâmetros visuais -------------------------------------------------
    cor_base: Cor
    cor_secundaria: Cor
    cor_detalhe: Cor
    cor_tempestade: Cor | None = None  # mancha oval (Grande Mancha Vermelha etc.)
    faixas: bool = False  # bandas horizontais tipo gigante gasoso
    manchas: bool = False  # blobs irregulares (continentes / crateras)
    tem_aneis: bool = False
    fase_inicial: float = 0.0  # ângulo orbital inicial, em radianos
    orbita_em_torno_de: str | None = None  # nome do corpo-pai (satélites)

    @property
    def eh_sol(self) -> bool:
        """Indica se o corpo é a estrela central."""
        return self.tipo == "estrela"

    @property
    def eh_satelite(self) -> bool:
        """Indica se o corpo é um satélite (orbita outro corpo, não o Sol)."""
        return self.orbita_em_torno_de is not None


# Fases iniciais espalhadas para que os planetas não nasçam alinhados.
CORPOS: list[CorpoCeleste] = [
    CorpoCeleste(
        nome="Sol",
        indice_gesto=0,
        tipo="estrela",
        diametro_km=1_392_700,
        distancia_ua=0.0,
        distancia_km=0.0,
        periodo_orbital_dias=0.0,
        periodo_rotacao_horas=609.12,  # ~25,38 dias no equador
        luas=0,
        temperatura_media_c=5505.0,  # superfície (fotosfera)
        inclinacao_axial_graus=7.25,
        fato_curioso="Concentra 99,86% de toda a massa do Sistema Solar.",
        cor_base=(255, 214, 96),
        cor_secundaria=(255, 148, 32),
        cor_detalhe=(255, 252, 226),
        manchas=True,  # granulação da fotosfera
        fase_inicial=0.0,
    ),
    CorpoCeleste(
        nome="Mercúrio",
        indice_gesto=1,
        tipo="rochoso",
        diametro_km=4_879,
        distancia_ua=0.387,
        distancia_km=57_900_000,
        periodo_orbital_dias=87.97,
        periodo_rotacao_horas=1407.6,
        luas=0,
        temperatura_media_c=167.0,
        inclinacao_axial_graus=0.03,
        fato_curioso="Um dia solar ali dura dois anos mercurianos.",
        cor_base=(154, 148, 141),
        cor_secundaria=(104, 99, 95),
        cor_detalhe=(188, 183, 175),
        manchas=True,
        fase_inicial=0.6,
    ),
    CorpoCeleste(
        nome="Vênus",
        indice_gesto=2,
        tipo="rochoso",
        diametro_km=12_104,
        distancia_ua=0.723,
        distancia_km=108_200_000,
        periodo_orbital_dias=224.70,
        periodo_rotacao_horas=-5832.5,  # retrógrada
        luas=0,
        temperatura_media_c=464.0,
        inclinacao_axial_graus=177.36,
        fato_curioso="Gira ao contrário e é o planeta mais quente, não Mercúrio.",
        cor_base=(226, 188, 124),
        cor_secundaria=(184, 140, 78),
        cor_detalhe=(246, 226, 178),
        faixas=True,
        fase_inicial=2.4,
    ),
    CorpoCeleste(
        nome="Terra",
        indice_gesto=3,
        tipo="rochoso",
        diametro_km=12_756,
        distancia_ua=1.000,
        distancia_km=149_600_000,
        periodo_orbital_dias=365.26,
        periodo_rotacao_horas=23.93,
        luas=1,
        temperatura_media_c=15.0,
        inclinacao_axial_graus=23.44,
        fato_curioso="Único mundo conhecido com água líquida estável na superfície.",
        cor_base=(48, 104, 196),
        cor_secundaria=(66, 142, 84),
        cor_detalhe=(238, 244, 252),
        manchas=True,
        fase_inicial=4.1,
    ),
    CorpoCeleste(
        nome="Marte",
        indice_gesto=4,
        tipo="rochoso",
        diametro_km=6_792,
        distancia_ua=1.524,
        distancia_km=227_900_000,
        periodo_orbital_dias=686.98,
        periodo_rotacao_horas=24.62,
        luas=2,
        temperatura_media_c=-65.0,
        inclinacao_axial_graus=25.19,
        fato_curioso="Abriga o Olympus Mons, vulcão de ~22 km — o maior conhecido.",
        cor_base=(191, 88, 54),
        cor_secundaria=(138, 58, 40),
        cor_detalhe=(233, 168, 130),
        manchas=True,
        fase_inicial=1.3,
    ),
    CorpoCeleste(
        nome="Júpiter",
        indice_gesto=5,
        tipo="gasoso",
        diametro_km=142_984,
        distancia_ua=5.204,
        distancia_km=778_600_000,
        periodo_orbital_dias=4_332.59,
        periodo_rotacao_horas=9.93,
        luas=95,
        temperatura_media_c=-110.0,
        inclinacao_axial_graus=3.13,
        fato_curioso="A Grande Mancha Vermelha é uma tempestade maior que a Terra.",
        cor_base=(214, 178, 138),
        cor_secundaria=(158, 112, 78),
        cor_detalhe=(242, 224, 200),
        cor_tempestade=(198, 96, 64),  # Grande Mancha Vermelha
        faixas=True,
        manchas=True,
        fase_inicial=5.5,
    ),
    CorpoCeleste(
        nome="Saturno",
        indice_gesto=6,
        tipo="gasoso",
        diametro_km=120_536,
        distancia_ua=9.583,
        distancia_km=1_433_500_000,
        periodo_orbital_dias=10_759.22,
        periodo_rotacao_horas=10.66,
        luas=146,
        temperatura_media_c=-140.0,
        inclinacao_axial_graus=26.73,
        fato_curioso="Sua densidade é menor que a da água: flutuaria numa banheira.",
        cor_base=(228, 205, 152),
        cor_secundaria=(182, 152, 104),
        cor_detalhe=(248, 236, 206),
        faixas=True,
        tem_aneis=True,
        fase_inicial=3.0,
    ),
    CorpoCeleste(
        nome="Urano",
        indice_gesto=7,
        tipo="gasoso",
        diametro_km=51_118,
        distancia_ua=19.191,
        distancia_km=2_872_500_000,
        periodo_orbital_dias=30_685.4,
        periodo_rotacao_horas=-17.24,  # retrógrada
        luas=28,
        temperatura_media_c=-195.0,
        inclinacao_axial_graus=97.77,
        fato_curioso="Gira praticamente deitado: seu eixo aponta quase para o Sol.",
        cor_base=(146, 214, 220),
        cor_secundaria=(102, 176, 194),
        cor_detalhe=(206, 240, 244),
        faixas=True,
        fase_inicial=0.9,
    ),
    CorpoCeleste(
        nome="Netuno",
        indice_gesto=8,
        tipo="gasoso",
        diametro_km=49_528,
        distancia_ua=30.070,
        distancia_km=4_495_100_000,
        periodo_orbital_dias=60_189.0,
        periodo_rotacao_horas=16.11,
        luas=16,
        temperatura_media_c=-200.0,
        inclinacao_axial_graus=28.32,
        fato_curioso="Tem os ventos mais rápidos do Sistema Solar: até 2.100 km/h.",
        cor_base=(58, 96, 214),
        cor_secundaria=(34, 62, 158),
        cor_detalhe=(160, 196, 250),
        cor_tempestade=(24, 40, 122),  # Grande Mancha Escura
        faixas=True,
        manchas=True,
        fase_inicial=2.0,
    ),
    CorpoCeleste(
        nome="Lua",
        indice_gesto=9,
        tipo="satelite",
        diametro_km=3_474,
        distancia_ua=0.0,        # não orbita o Sol diretamente
        distancia_km=384_400,    # distância média à Terra
        periodo_orbital_dias=27.32,
        periodo_rotacao_horas=655.73,  # síncrona (= período orbital)
        luas=0,
        temperatura_media_c=-20.0,
        inclinacao_axial_graus=6.68,
        fato_curioso="É o único outro satélite natural que a humanidade já pisou.",
        cor_base=(180, 180, 178),
        cor_secundaria=(120, 118, 114),
        cor_detalhe=(210, 208, 204),
        manchas=True,
        fase_inicial=0.0,
        orbita_em_torno_de="Terra",
    ),
]

# Índice de gesto -> corpo. Gesto 10 fica de fora de propósito.
CORPOS_POR_GESTO: dict[int, CorpoCeleste] = {c.indice_gesto: c for c in CORPOS}

# Diâmetro de referência para a lei de potência de tamanho (ver config.py).
DIAMETRO_REFERENCIA_KM: float = 12_756.0

# Distâncias extremas usadas na compressão logarítmica das órbitas.
DISTANCIA_UA_MINIMA: float = min(c.distancia_ua for c in CORPOS if c.distancia_ua > 0)
DISTANCIA_UA_MAXIMA: float = max(c.distancia_ua for c in CORPOS)


# ---------------------------------------------------------------------------
# Luas dos demais planetas
# ---------------------------------------------------------------------------
# Ficam FORA de CORPOS de propósito: os gestos vão de 0 a 10 e já estão todos
# ocupados (0-8 Sol e planetas, 9 Lua, 10 visão geral). Estas luas não são
# selecionáveis por contagem de dedos — elas aparecem em bloco quando o "modo
# luas" é ligado, e podem ser focadas por toque/clique.
#
# Só as principais de cada planeta: Júpiter sozinho tem 95 luas conhecidas, e
# desenhar todas viraria ruído em volta do disco.
#
# ATENÇÃO à escala: o raio orbital em pixels é VISUAL, não proporcional. Em
# escala real Calisto ficaria a 26 raios de Júpiter e Fobos a 1,4 raios de
# Marte — as luas internas sumiriam dentro do planeta. O que preservamos é a
# ordem e o espaçamento relativo dentro de cada sistema.


@dataclass(frozen=True)
class LuaMenor:
    """Satélite secundário: aparece na cena, mas não tem gesto próprio."""

    nome: str
    planeta: str  # nome do corpo-pai
    diametro_km: float
    distancia_km: float  # distância média real ao planeta
    periodo_orbital_dias: float
    raio_orbita_px: float  # raio DESENHADO, em múltiplos do raio do planeta
    cor: Cor
    fase_inicial: float
    fato_curioso: str


LUAS_MENORES: tuple[LuaMenor, ...] = (
    # --- Marte ---------------------------------------------------------
    LuaMenor("Fobos", "Marte", 22.5, 9_376, 0.319, 2.2,
             (150, 140, 130), 0.0,
             "Está tão perto de Marte que nasce a oeste e se põe a leste."),
    LuaMenor("Deimos", "Marte", 12.4, 23_463, 1.263, 3.2,
             (170, 158, 145), 2.1,
             "A menor lua do Sistema Solar entre as bem conhecidas."),
    # --- Júpiter -------------------------------------------------------
    LuaMenor("Amalteia", "Júpiter", 167, 181_366, 0.498, 1.7,
             (196, 120, 96), 1.1,
             "É avermelhada e tem formato irregular, como uma batata."),
    LuaMenor("Io", "Júpiter", 3643, 421_700, 1.769, 2.1,
             (232, 214, 120), 0.4,
             "O corpo com mais atividade vulcânica do Sistema Solar."),
    LuaMenor("Europa", "Júpiter", 3122, 671_034, 3.551, 2.6,
             (216, 206, 190), 2.0,
             "Sob a crosta de gelo há um oceano de água líquida."),
    LuaMenor("Ganimedes", "Júpiter", 5268, 1_070_412, 7.155, 3.2,
             (168, 156, 140), 3.7,
             "É a maior lua do Sistema Solar — maior que Mercúrio."),
    LuaMenor("Calisto", "Júpiter", 4821, 1_882_709, 16.689, 4.0,
             (128, 118, 108), 5.2,
             "A superfície mais craterada que se conhece."),
    # --- Saturno -------------------------------------------------------
    LuaMenor("Encélado", "Saturno", 504, 237_948, 1.37, 1.8,
             (236, 240, 244), 4.4,
             "Lança gêiseres de água pelo polo sul."),
    LuaMenor("Dione", "Saturno", 1123, 377_396, 2.737, 2.2,
             (206, 204, 198), 1.9,
             "Tem penhascos de gelo que chegam a centenas de metros."),
    LuaMenor("Reia", "Saturno", 1527, 527_108, 4.518, 2.7,
             (194, 192, 186), 3.1,
             "A segunda maior lua de Saturno, feita quase toda de gelo."),
    LuaMenor("Titã", "Saturno", 5150, 1_221_870, 15.945, 3.3,
             (214, 168, 92), 1.2,
             "Tem atmosfera densa e rios de metano líquido."),
    LuaMenor("Jápeto", "Saturno", 1469, 3_560_820, 79.33, 4.1,
             (150, 140, 126), 5.6,
             "Um hemisfério é escuro como carvão e o outro, branco como neve."),
    # --- Urano ---------------------------------------------------------
    LuaMenor("Miranda", "Urano", 472, 129_900, 1.413, 1.8,
             (188, 190, 192), 2.7,
             "Tem um penhasco de 20 km, o mais alto conhecido."),
    LuaMenor("Ariel", "Urano", 1158, 190_900, 2.52, 2.2,
             (198, 196, 190), 0.5,
             "A superfície mais clara e jovem entre as luas de Urano."),
    LuaMenor("Umbriel", "Urano", 1169, 266_000, 4.144, 2.6,
             (132, 130, 128), 4.0,
             "A mais escura das grandes luas de Urano."),
    LuaMenor("Titânia", "Urano", 1578, 435_910, 8.706, 3.1,
             (176, 166, 158), 0.9,
             "A maior lua de Urano, com cânions de centenas de quilômetros."),
    LuaMenor("Oberon", "Urano", 1523, 583_520, 13.463, 3.7,
             (150, 142, 136), 3.4,
             "A mais externa das grandes luas de Urano."),
    # --- Netuno --------------------------------------------------------
    LuaMenor("Galateia", "Netuno", 176, 61_953, 0.429, 1.7,
             (160, 168, 176), 3.0,
             "Sua gravidade mantém um dos anéis de Netuno agrupado."),
    LuaMenor("Larissa", "Netuno", 194, 73_548, 0.555, 2.0,
             (172, 178, 184), 5.0,
             "Tem forma irregular e superfície muito craterada."),
    LuaMenor("Proteu", "Netuno", 420, 117_647, 1.122, 2.4,
             (150, 156, 162), 0.7,
             "É quase o maior corpo que a gravidade não conseguiu arredondar."),
    LuaMenor("Tritão", "Netuno", 2707, 354_759, -5.877, 2.9,
             (198, 206, 210), 1.7,
             "Orbita ao contrário: foi capturado, não se formou ali."),
    LuaMenor("Nereida", "Netuno", 340, 5_513_400, 360.13, 3.8,
             (166, 170, 174), 4.2,
             "Tem a órbita mais alongada entre as luas conhecidas."),
)

# Índice por planeta, para o renderizador não filtrar a lista inteira por frame.
LUAS_POR_PLANETA: dict[str, tuple[LuaMenor, ...]] = {}
for _lua in LUAS_MENORES:
    LUAS_POR_PLANETA.setdefault(_lua.planeta, ())
    LUAS_POR_PLANETA[_lua.planeta] += (_lua,)

# A Lua da Terra vive em CORPOS, não em LUAS_MENORES, porque tem gesto próprio
# (o 9). Mas ela É uma lua: precisa aparecer aqui, senão a lista que o HUD
# numera e o modo luas consulta diria que a Terra não tem satélite nenhum.
# Esta é a fonte ÚNICA de "quais luas este planeta tem".
for _corpo in CORPOS:
    if not _corpo.eh_satelite or _corpo.orbita_em_torno_de is None:
        continue
    _pai = _corpo.orbita_em_torno_de
    LUAS_POR_PLANETA.setdefault(_pai, ())
    LUAS_POR_PLANETA[_pai] = (
        LuaMenor(
            nome=_corpo.nome,
            planeta=_pai,
            diametro_km=_corpo.diametro_km,
            distancia_km=_corpo.distancia_km,
            periodo_orbital_dias=_corpo.periodo_orbital_dias,
            # 2,8 = RAIO_ORBITA_LUA_PX / RAIO_PLANETA_BASE_PX, o mesmo raio que
            # o renderizador já usava para ela.
            raio_orbita_px=2.8,
            cor=_corpo.cor_base,
            fase_inicial=_corpo.fase_inicial,
            fato_curioso=_corpo.fato_curioso,
        ),
    ) + LUAS_POR_PLANETA[_pai]


def luas_do_planeta(nome_planeta: str) -> tuple[LuaMenor, ...]:
    """Luas desenhadas ao redor de um planeta (vazio se não houver)."""
    return LUAS_POR_PLANETA.get(nome_planeta, ())


def corpo_por_gesto(numero_dedos: int) -> CorpoCeleste | None:
    """Devolve o corpo mapeado para um número de dedos, ou None se inválido."""
    return CORPOS_POR_GESTO.get(numero_dedos)


def legenda_gestos() -> list[tuple[int, str]]:
    """Lista (dedos, nome) para exibir a tabela de mapeamento no HUD."""
    return [(c.indice_gesto, c.nome) for c in CORPOS]


__all__ = [
    "CorpoCeleste",
    "LuaMenor",
    "LUAS_MENORES",
    "LUAS_POR_PLANETA",
    "luas_do_planeta",
    "CORPOS",
    "CORPOS_POR_GESTO",
    "DIAMETRO_REFERENCIA_KM",
    "DISTANCIA_UA_MINIMA",
    "DISTANCIA_UA_MAXIMA",
    "corpo_por_gesto",
    "legenda_gestos",
]
