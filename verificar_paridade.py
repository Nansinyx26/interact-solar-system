"""Compara a versão desktop (Python) com a versão web (JavaScript).

Regra do projeto: **toda alteração feita em um lado precisa ser feita no outro**.
Como as duas implementações são independentes, nada impede que elas divirjam em
silêncio — um planeta com temperatura diferente, um limiar de gesto ajustado só
no desktop, uma constante de escala que mudou num arquivo e não no outro.

Este script encontra essas divergências comparando:

1. as constantes numéricas de ``config.py`` e ``web/config.js``;
2. todos os campos dos 9 corpos em ``dados/planetas.py`` e ``web/dados/planetas.js``;
3. a presença dos módulos equivalentes nas duas árvores.

Uso:
    .venv\\Scripts\\python.exe verificar_paridade.py

Sai com código 1 se houver divergência, para poder virar passo de CI.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent
WEB = RAIZ / "web"

# Tolerância para comparação de float (0,4 e 0.40 são o mesmo número).
EPSILON = 1e-9

# Opacidades: o pygame trabalha em 0-255 e o Canvas/CSS em 0-1. Não é
# divergência, é unidade diferente — comparamos o valor da web multiplicado por
# 255, com folga de 2 níveis para o arredondamento de quem escreveu 0,28.
ALPHAS_EM_ESCALAS_DIFERENTES = {
    "ALPHA_CORPO_ESMAECIDO",
    "ALPHA_ORBITA_FOCADA",
    "ALPHA_ORBITA_NORMAL",
    "ALPHA_ORBITA_TENUE",
    "ALPHA_SOMBRA_MAX",
}
TOLERANCIA_ALPHA = 2.0

# Constantes que existem só de um lado por serem específicas da plataforma —
# comparar não faz sentido e a ausência não é divergência.
SO_DESKTOP = {
    # Janela, fontes e layout do pygame — na web quem faz isso é o CSS.
    "TITULO_JANELA", "LARGURA_JANELA", "ALTURA_JANELA", "LARGURA_MINIMA_JANELA",
    "ALTURA_MINIMA_JANELA", "FPS_ALVO", "FAMILIA_FONTE", "FAMILIA_FONTE_MONO",
    "TAM_FONTE_TITULO", "TAM_FONTE_GRANDE", "TAM_FONTE_MEDIA", "TAM_FONTE_PEQUENA",
    "TAM_FONTE_MINI", "MARGEM_HUD", "LARGURA_PREVIEW_CAMERA", "ALTURA_PREVIEW_CAMERA",
    "LARGURA_FICHA", "ALPHA_PAINEL", "RAIO_ANEL_PROGRESSO", "ESPESSURA_ANEL_PROGRESSO",
    "DURACAO_ANIMACAO_FICHA_S", "DESLOCAMENTO_ENTRADA_FICHA_PX",
    "ALPHA_LINHA_LEGENDA_ATIVA", "ALTURA_BARRA_ATALHOS", "ALTURA_MINIMA_LEGENDA",
    "LARGURA_MINIMA_ATALHOS", "RAIO_PONTO_LEGENDA",
    # Captura via OpenCV: a web usa getUserMedia, com outra API de reconexão.
    "INDICE_CAMERA", "FPS_CAPTURA", "SEGUNDOS_ENTRE_RECONEXOES", "MAX_FALHAS_LEITURA",
    "FALHAS_ATE_DESCONEXAO", "COMPLEXIDADE_MODELO", "LIMIAR_BRILHO_BAIXO",
    # Render: o Canvas resolve com gradiente o que o pygame faz por pixel.
    "PASSO_ANGULO_SOMBRA_GRAUS", "RAIO_ORBITA_MAX_DESENHAVEL_PX", "ALPHA_ANEL_MAX",
    "ALPHA_HALO_SOL", "ALPHA_ROTULO_CORPO", "COR_HALO_SOL",
    # Narração: o desktop fala direto com a ElevenLabs, a web passa por uma
    # função serverless (a chave não pode chegar ao navegador). Os parâmetros da
    # chamada ficam só do lado que a executa.
    "ELEVENLABS_TIMEOUT_S",
}
SO_WEB = {
    "ALTURA_REFERENCIA", "URL_WASM_MEDIAPIPE", "URL_MODELO_MAOS",
    "CONFIANCA_MIN_PRESENCA",
}
# A marca d'água é CSS puro na web e desenhada com pygame no desktop, então as
# constantes do desenho existem só do lado Python.
_PREFIXOS_SO_DESKTOP = ("ASSINATURA_", "ALPHA_ASSINATURA_", "COR_ASSINATURA_")

# Cores da interface: no desktop são constantes do config.py, na web são
# variáveis CSS do :root. Mesmo assim precisam ser a MESMA cor — o mapeamento
# abaixo é o que permite comparar as duas notações.
MAPA_CORES_CSS = {
    "COR_FUNDO": "--fundo",
    "COR_PAINEL": "--painel",
    "COR_TEXTO": "--texto",
    "COR_TEXTO_SECUNDARIO": "--texto-fraco",
    "COR_DESTAQUE": "--destaque",
    "COR_AVISO": "--aviso",
    "COR_ERRO": "--erro",
    "COR_SUCESSO": "--sucesso",
}

# Módulos que devem existir nas duas árvores (nome desktop -> nome web).
MODULOS_ESPELHADOS = {
    "config.py": "config.js",
    "dados/planetas.py": "dados/planetas.js",
    "dados/telemetria.py": "dados/telemetria.js",
    "nucleo/orbita.py": "nucleo/orbita.js",
    "nucleo/camera.py": "nucleo/camera.js",
    "nucleo/renderizador.py": "nucleo/renderizador.js",
    "gestos/contador.py": "gestos/contador.js",
    "gestos/estabilizador.py": "gestos/estabilizador.js",
    "gestos/detector.py": "gestos/detector.js",
    "ui/hud.py": "ui/hud.js",
    "ui/ficha_planeta.py": "ui/ficha.js",
}


# ---------------------------------------------------------------------------
# Leitura das constantes
# ---------------------------------------------------------------------------
def _para_numero(bruto: str) -> Any:
    """Converte o literal em número/tupla quando possível, senão devolve None."""
    texto = bruto.strip().rstrip(",").strip()
    texto = re.sub(r"#.*$", "", texto).strip()
    texto = re.sub(r"//.*$", "", texto).strip()
    if not texto:
        return None
    if texto in {"True", "true"}:
        return True
    if texto in {"False", "false"}:
        return False
    try:
        return float(texto)
    except ValueError:
        pass
    # Tuplas/listas de números: (1, 2, 3) e [1, 2, 3] são equivalentes aqui.
    if texto[0] in "([" and texto[-1] in ")]":
        partes = [p.strip() for p in texto[1:-1].split(",") if p.strip()]
        try:
            return tuple(float(p) for p in partes)
        except ValueError:
            return None
    # String de cor da web ("78, 88, 120") equivale à tupla do desktop.
    if texto[0] in "\"'" and texto[-1] in "\"'":
        interno = texto[1:-1]
        if re.fullmatch(r"\s*\d+\s*(,\s*\d+\s*)+", interno):
            return tuple(float(p) for p in interno.split(","))
    return None


def constantes_python(caminho: Path) -> dict[str, Any]:
    """Extrai NOME: Final[...] = valor de um módulo de configuração.

    A anotação tem colchetes aninhados (``Final[tuple[int, int, int]]``), então
    localizamos o ``=`` de nível zero em vez de casar a anotação por regex — um
    ``[^\\]]*`` pararia no primeiro ``]`` e perderia todas as constantes de cor.
    """
    constantes: dict[str, Any] = {}
    cabecalho = re.compile(r"^([A-Z][A-Z0-9_]*)\s*:\s*Final")
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        achado = cabecalho.match(linha)
        if not achado:
            continue
        profundidade = 0
        posicao = -1
        for indice, caractere in enumerate(linha):
            if caractere == "[":
                profundidade += 1
            elif caractere == "]":
                profundidade -= 1
            elif caractere == "=" and profundidade == 0:
                posicao = indice
                break
        if posicao < 0:
            continue
        valor = _para_numero(linha[posicao + 1 :])
        if valor is not None:
            constantes[achado.group(1)] = valor
    return constantes


def cores_css(caminho: Path) -> dict[str, tuple[float, ...]]:
    """Lê as variáveis do primeiro ``:root`` e devolve as que são cores RGB.

    Aceita as duas notações usadas na folha: ``#rrggbb`` e ``rgba(r, g, b, a)``
    — o alpha é descartado, porque do lado do pygame ele é uma constante à parte.
    """
    texto = caminho.read_text(encoding="utf-8")
    bloco = re.search(r":root\s*\{(.*?)\}", texto, re.S)
    if not bloco:
        return {}
    cores: dict[str, tuple[float, ...]] = {}
    for nome, valor in re.findall(r"(--[a-z-]+)\s*:\s*([^;]+);", bloco.group(1)):
        valor = valor.strip()
        hexadecimal = re.fullmatch(r"#([0-9a-fA-F]{6})", valor)
        if hexadecimal:
            digitos = hexadecimal.group(1)
            cores[nome] = tuple(float(int(digitos[i : i + 2], 16)) for i in (0, 2, 4))
            continue
        rgba = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,[^)]+)?\)", valor)
        if rgba:
            cores[nome] = tuple(float(g) for g in rgba.groups())
    return cores


def constantes_javascript(caminho: Path) -> dict[str, Any]:
    """Extrai export const NOME = valor de um módulo de configuração."""
    constantes: dict[str, Any] = {}
    texto = caminho.read_text(encoding="utf-8")
    # O valor pode estar na linha seguinte quando o formatador quebra a linha.
    padrao = re.compile(r"export\s+const\s+([A-Z][A-Z0-9_]*)\s*=\s*([^;]+);", re.S)
    for achado in padrao.finditer(texto):
        valor = _para_numero(achado.group(2))
        if valor is not None:
            constantes[achado.group(1)] = valor
    return constantes


# ---------------------------------------------------------------------------
# Leitura dos corpos celestes
# ---------------------------------------------------------------------------
def _camel_para_snake(nome: str) -> str:
    """indiceGesto -> indice_gesto."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", nome).lower()


def corpos_python() -> list[dict[str, Any]]:
    """Importa o catálogo do desktop e o devolve como dicionários."""
    sys.path.insert(0, str(RAIZ))
    from dados.planetas import CORPOS  # noqa: PLC0415 (import tardio de propósito)

    return [
        {
            campo: getattr(corpo, campo)
            for campo in corpo.__dataclass_fields__
            if isinstance(getattr(corpo, campo), (int, float, str, tuple, bool, type(None)))
        }
        for corpo in CORPOS
    ]


def corpos_javascript() -> list[dict[str, Any]]:
    """Converte o array CORPOS do planetas.js em dicionários.

    O literal é quase JSON: basta remover comentários, pôr aspas nas chaves e
    tirar as vírgulas finais. Evita depender do Node só para ler dados.
    """
    texto = (WEB / "dados" / "planetas.js").read_text(encoding="utf-8")
    inicio = texto.index("export const CORPOS = [")
    corpo_bruto = texto[inicio + len("export const CORPOS = ") :]
    # Recorta até o fechamento do array, contando colchetes.
    profundidade = 0
    for indice, caractere in enumerate(corpo_bruto):
        if caractere == "[":
            profundidade += 1
        elif caractere == "]":
            profundidade -= 1
            if profundidade == 0:
                corpo_bruto = corpo_bruto[: indice + 1]
                break

    sem_comentarios = re.sub(r"//[^\n]*", "", corpo_bruto)
    com_aspas = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', sem_comentarios)
    sem_virgula_final = re.sub(r",(\s*[}\]])", r"\1", com_aspas)
    dados = json.loads(sem_virgula_final)
    return [
        {_camel_para_snake(chave): valor for chave, valor in item.items()} for item in dados
    ]


# ---------------------------------------------------------------------------
# Comparação
# ---------------------------------------------------------------------------
def _iguais(a: Any, b: Any) -> bool:
    """Compara valores tolerando float/int e tupla/lista."""
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_iguais(x, y) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= EPSILON
    return a == b


def ler_versao(caminho: Path, padrao: str) -> str | None:
    """Extrai a string de versão de um dos arquivos de configuração."""
    achado = re.search(padrao, caminho.read_text(encoding="utf-8"))
    return achado.group(1) if achado else None


def verificar() -> int:
    """Roda todas as comparações e devolve o código de saída."""
    divergencias: list[str] = []
    avisos: list[str] = []

    print("=== versão ===")
    versao_py = ler_versao(RAIZ / "config.py", r'VERSAO:\s*Final\[str\]\s*=\s*"([^"]+)"')
    versao_js = ler_versao(WEB / "config.js", r'export const VERSAO\s*=\s*"([^"]+)"')
    if versao_py and versao_py == versao_js:
        print(f"  ok       desktop e web na versão {versao_py}")
    else:
        divergencias.append(f"versão: desktop={versao_py!r} web={versao_js!r}")
        print(f"  DIFERE   desktop={versao_py!r} web={versao_js!r}")

    print("\n=== módulos espelhados ===")
    for desktop, web in MODULOS_ESPELHADOS.items():
        existe_desktop = (RAIZ / desktop).exists()
        existe_web = (WEB / web).exists()
        if existe_desktop and existe_web:
            print(f"  ok       {desktop:28s} <-> web/{web}")
        else:
            faltando = desktop if not existe_desktop else f"web/{web}"
            divergencias.append(f"módulo ausente: {faltando}")
            print(f"  AUSENTE  {faltando}")

    print("\n=== constantes compartilhadas ===")
    py = constantes_python(RAIZ / "config.py")
    js = constantes_javascript(WEB / "config.js")
    comuns = sorted(set(py) & set(js))
    problemas_config = 0
    for nome in comuns:
        if nome in ALPHAS_EM_ESCALAS_DIFERENTES:
            iguais = abs(float(py[nome]) - float(js[nome]) * 255) <= TOLERANCIA_ALPHA
        else:
            iguais = _iguais(py[nome], js[nome])
        if not iguais:
            problemas_config += 1
            divergencias.append(f"{nome}: desktop={py[nome]!r} web={js[nome]!r}")
            print(f"  DIFERE   {nome}: desktop={py[nome]!r} web={js[nome]!r}")
    print(f"  {len(comuns)} constantes comparadas, {problemas_config} divergência(s)")

    print("\n=== cores da interface (config.py <-> :root do CSS) ===")
    css = cores_css(WEB / "estilo.css")
    for constante, variavel in sorted(MAPA_CORES_CSS.items()):
        if constante not in py or variavel not in css:
            divergencias.append(f"cor ausente: {constante} / {variavel}")
            print(f"  AUSENTE  {constante} / {variavel}")
        elif not _iguais(py[constante], css[variavel]):
            divergencias.append(
                f"{constante}: desktop={py[constante]!r} css={css[variavel]!r}"
            )
            print(f"  DIFERE   {constante}: desktop={py[constante]!r} css={css[variavel]!r}")
        else:
            print(f"  ok       {constante} = {variavel}")

    for nome in sorted(set(py) - set(js) - SO_DESKTOP - set(MAPA_CORES_CSS)):
        if nome.startswith(_PREFIXOS_SO_DESKTOP):
            continue
        avisos.append(f"{nome} existe no desktop e não na web")
    for nome in sorted(set(js) - set(py) - SO_WEB):
        avisos.append(f"{nome} existe na web e não no desktop")

    print("\n=== corpos celestes ===")
    lista_py = {corpo["nome"]: corpo for corpo in corpos_python()}
    lista_js = {corpo["nome"]: corpo for corpo in corpos_javascript()}
    if set(lista_py) != set(lista_js):
        divergencias.append(
            f"conjuntos de corpos diferem: só desktop={sorted(set(lista_py) - set(lista_js))} "
            f"só web={sorted(set(lista_js) - set(lista_py))}"
        )
    for nome in sorted(set(lista_py) & set(lista_js)):
        campos_py = lista_py[nome]
        campos_js = lista_js[nome]
        problemas = [
            f"{campo}: desktop={campos_py[campo]!r} web={campos_js[campo]!r}"
            for campo in sorted(set(campos_py) & set(campos_js))
            if not _iguais(campos_py[campo], campos_js[campo])
        ]
        if problemas:
            divergencias.extend(f"{nome}.{p}" for p in problemas)
            print(f"  DIFERE   {nome}: " + "; ".join(problemas))
        else:
            print(f"  ok       {nome}")

    if avisos:
        print("\n=== avisos (constante só de um lado) ===")
        for aviso in avisos:
            print(f"  ~ {aviso}")

    print()
    if divergencias:
        print(f"PARIDADE QUEBRADA — {len(divergencias)} divergência(s):")
        for item in divergencias:
            print(f"  - {item}")
        return 1
    print("PARIDADE OK — desktop e web estão sincronizados.")
    return 0


if __name__ == "__main__":
    sys.exit(verificar())
