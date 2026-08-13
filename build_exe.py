"""Gera o executável do Sistema Solar Interativo com o PyInstaller.

Uso (dentro da pasta do projeto, com o venv já montado):

    .venv\\Scripts\\python.exe -m pip install pyinstaller
    .venv\\Scripts\\python.exe build_exe.py

O resultado é ``SistemaSolar.exe`` na raiz do projeto, junto de uma pasta
``_internal_sistema_solar`` com as bibliotecas. É preciso manter os dois lado a
lado — a pasta é o "corpo" do programa, o .exe apenas o lançador.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
NOME_APP = "SistemaSolar"
PASTA_BIBLIOTECAS = "_internal_sistema_solar"

# O MediaPipe carrega os modelos .tflite/.binarypb de dentro do próprio pacote:
# sem coletar esses arquivos o executável abre e falha ao criar o Hands.
COLETAR = ["mediapipe"]

# O pyttsx3 escolhe o driver de voz por import dinâmico (SAPI5 no Windows), algo
# que o PyInstaller não enxerga sozinho — sem estes nomes o executável sobe sem
# a voz local de reserva.
IMPORTES_OCULTOS = [
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",
    "pyttsx3.drivers.dummy",
]

# Dependências pesadas que o mediapipe declara mas que o caminho do Hands nunca
# executa (jax/scipy sozinhos passam de 600 MB). ATENÇÃO: matplotlib NÃO pode
# entrar aqui — mp.solutions.drawing_utils o importa no topo do módulo, e sem
# ele o executável sobe em modo teclado com "No module named 'matplotlib'".
EXCLUIR = [
    "jax",
    "jaxlib",
    "scipy",
    "sentencepiece",
    "sounddevice",
    "pytest",
    "IPython",
    # matplotlib só precisa do backend Agg aqui (nada é plotado em tela).
    "tkinter",
]

# Arquivos que o PyInstaller copia por precaução e que este aplicativo nunca
# toca. Cada linha traz o motivo de ser seguro remover — sem isso o bundle passa
# de 340 MB, quase tudo em código que nunca executa.
LIXO_APOS_BUILD = [
    # Codecs de arquivo de vídeo do OpenCV: só abrimos webcam (DirectShow/MSMF),
    # nunca arquivos .mp4/.avi. ~52 MB em duas DLLs.
    "cv2/opencv_videoio_ffmpeg*.dll",
    # Interpretador Tcl/Tk, arrastado pelo matplotlib junto do backend TkAgg.
    "_tcl_data",
    "_tk_data",
    "tcl8",
    "tk",
    # Decodificador AVIF do Pillow: nenhuma imagem é carregada de disco.
    "PIL/_avif*.pyd",
]

# Modelos do MediaPipe usados pelo mp.solutions.hands. Todos os outros
# (pose, face, íris, holistic, objectron, segmentação) vêm no wheel e ficam
# ocupando espaço sem nunca serem carregados.
MODELOS_USADOS = {"hand_landmark", "palm_detection"}


def construir() -> int:
    """Chama o PyInstaller e move o resultado para a raiz do projeto."""
    comando = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        NOME_APP,
        # onedir: abre em ~2 s. O modo onefile descompactaria ~400 MB em um
        # diretório temporário a cada execução, levando mais de 20 s.
        "--onedir",
        "--contents-directory",
        PASTA_BIBLIOTECAS,
        # Console visível de propósito: é onde saem as linhas [webcam ] que
        # dizem se a câmera abriu, e é a primeira coisa a olhar se algo falhar.
        "--console",
        "--distpath",
        str(RAIZ / "build_dist"),
        "--workpath",
        str(RAIZ / "build_temp"),
        "--specpath",
        str(RAIZ / "build_temp"),
    ]
    for pacote in COLETAR:
        comando += ["--collect-all", pacote]
    for modulo in IMPORTES_OCULTOS:
        comando += ["--hidden-import", modulo]
    for modulo in EXCLUIR:
        comando += ["--exclude-module", modulo]
    comando.append(str(RAIZ / "main.py"))

    print("Executando:", " ".join(comando), "\n")
    resultado = subprocess.run(comando, check=False)
    if resultado.returncode != 0:
        print("\nFALHA no PyInstaller.")
        return resultado.returncode

    _publicar_na_raiz()
    liberado = _enxugar_bundle()
    print(f"\nPronto: {RAIZ / (NOME_APP + '.exe')}")
    print(f"Bibliotecas em: {RAIZ / PASTA_BIBLIOTECAS}")
    print(f"Enxugado: -{liberado / 1024 / 1024:.1f} MB de código nunca executado")
    print(f"Tamanho final: {_tamanho_bundle() / 1024 / 1024:.1f} MB")
    return 0


def _caminho_longo(caminho: Path) -> str:
    """Prefixo \\\\?\\ para escapar do limite de 260 caracteres do Windows.

    A árvore do mediapipe dentro do bundle ultrapassa esse limite e qualquer
    ``stat``/``remove`` falha sem isto, mesmo o caminho existindo.
    """
    return "\\\\?\\" + str(caminho.resolve())


def _tamanho_bundle() -> int:
    """Soma o executável e todas as bibliotecas ao lado dele."""
    total = (RAIZ / f"{NOME_APP}.exe").stat().st_size
    for item in (RAIZ / PASTA_BIBLIOTECAS).rglob("*"):
        try:
            if item.is_file():
                total += Path(_caminho_longo(item)).stat().st_size
        except OSError:
            pass
    return total


def _enxugar_bundle() -> int:
    """Remove do bundle o que este aplicativo comprovadamente não usa."""
    base = RAIZ / PASTA_BIBLIOTECAS
    liberado = 0

    for padrao in LIXO_APOS_BUILD:
        for alvo in base.glob(padrao):
            if alvo.is_dir():
                liberado += sum(
                    Path(_caminho_longo(p)).stat().st_size
                    for p in alvo.rglob("*")
                    if p.is_file()
                )
                shutil.rmtree(alvo, ignore_errors=True)
            elif alvo.is_file():
                liberado += alvo.stat().st_size
                alvo.unlink()

    modulos = base / "mediapipe" / "modules"
    if modulos.is_dir():
        for pasta in modulos.iterdir():
            if pasta.is_dir() and pasta.name not in MODELOS_USADOS:
                liberado += sum(
                    Path(_caminho_longo(p)).stat().st_size
                    for p in pasta.rglob("*")
                    if p.is_file()
                )
                shutil.rmtree(pasta, ignore_errors=True)
    return liberado


def _publicar_na_raiz() -> None:
    """Move o .exe e suas bibliotecas do build_dist para a raiz do projeto."""
    origem = RAIZ / "build_dist" / NOME_APP
    destino_exe = RAIZ / f"{NOME_APP}.exe"
    destino_libs = RAIZ / PASTA_BIBLIOTECAS

    if destino_libs.exists():
        shutil.rmtree(destino_libs)
    if destino_exe.exists():
        destino_exe.unlink()

    shutil.move(str(origem / PASTA_BIBLIOTECAS), str(destino_libs))
    shutil.move(str(origem / f"{NOME_APP}.exe"), str(destino_exe))

    # Restos do build não servem para nada depois que o resultado foi movido.
    for pasta in ("build_dist", "build_temp"):
        shutil.rmtree(RAIZ / pasta, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(construir())
