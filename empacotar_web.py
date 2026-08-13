"""Gera o ZIP da versão desktop servido pelo botão "Baixar" do site.

O pacote leva o código-fonte Python, o requirements.txt, o README e o script de
build do executável — não o executável pronto, que tem ~350 MB e estouraria o
limite de deploy do Vercel (100 MB por implantação).

Uso:
    .venv\\Scripts\\python.exe empacotar_web.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "web" / "sistema-solar-gestos.zip"
NOME_PASTA = "sistema_solar_gestos"

# Tudo que o usuário precisa para rodar e para gerar o próprio executável.
ARQUIVOS = [
    "main.py",
    "config.py",
    "requirements.txt",
    "README.md",
    "build_exe.py",
    ".gitignore",
]
PACOTES = ["dados", "nucleo", "gestos", "ui"]
EXTRAS = ["docs"]

# O que nunca entra: ambiente virtual, caches, o próprio executável e a versão
# web (que já está publicada).
IGNORADOS = {".venv", "__pycache__", "_internal_sistema_solar", "web", "build_dist", "build_temp"}


def _deve_incluir(caminho: Path) -> bool:
    """Filtra caches e diretórios de build."""
    return not any(parte in IGNORADOS for parte in caminho.parts)


def empacotar() -> int:
    """Escreve o ZIP e devolve o código de saída."""
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as pacote:
        for nome in ARQUIVOS:
            origem = RAIZ / nome
            if not origem.exists():
                print(f"  aviso: {nome} não encontrado, ignorando")
                continue
            pacote.write(origem, f"{NOME_PASTA}/{nome}")
            total += 1

        for pasta in PACOTES + EXTRAS:
            base = RAIZ / pasta
            if not base.exists():
                continue
            for arquivo in sorted(base.rglob("*")):
                if arquivo.is_dir() or not _deve_incluir(arquivo.relative_to(RAIZ)):
                    continue
                pacote.write(arquivo, f"{NOME_PASTA}/{arquivo.relative_to(RAIZ).as_posix()}")
                total += 1

    tamanho_kb = DESTINO.stat().st_size / 1024
    print(f"{DESTINO} — {total} arquivos, {tamanho_kb:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(empacotar())
