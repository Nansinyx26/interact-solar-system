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
]


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
    for modulo in EXCLUIR:
        comando += ["--exclude-module", modulo]
    comando.append(str(RAIZ / "main.py"))

    print("Executando:", " ".join(comando), "\n")
    resultado = subprocess.run(comando, check=False)
    if resultado.returncode != 0:
        print("\nFALHA no PyInstaller.")
        return resultado.returncode

    _publicar_na_raiz()
    print(f"\nPronto: {RAIZ / (NOME_APP + '.exe')}")
    print(f"Bibliotecas em: {RAIZ / PASTA_BIBLIOTECAS}")
    return 0


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
