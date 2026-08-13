"""Prepara o projeto para publicação: verifica paridade e regenera o download.

Rode isto **antes de todo deploy**. Ele garante a regra do projeto — desktop e
web sempre na mesma versão — em três passos:

1. ``verificar_paridade.py``: constantes, cores e dados dos 9 corpos precisam
   bater entre Python e JavaScript. Falhou, para aqui.
2. ``empacotar_web.py``: regenera ``web/sistema-solar-gestos.zip`` com o código
   Python **atual**, para quem baixar pelo site receber exatamente a versão que
   está no ar.
3. Confere se o ZIP recém-gerado carrega a mesma ``VERSAO`` do site.

Uso:
    .venv\\Scripts\\python.exe publicar.py
    .venv\\Scripts\\python.exe publicar.py --com-exe   (regenera o executável)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ZIP_DOWNLOAD = RAIZ / "web" / "sistema-solar-gestos.zip"


def _rodar(descricao: str, argumentos: list[str]) -> bool:
    """Executa um passo e informa o resultado."""
    print(f"\n{'=' * 62}\n{descricao}\n{'=' * 62}")
    resultado = subprocess.run([sys.executable, *argumentos], check=False, cwd=RAIZ)
    if resultado.returncode != 0:
        print(f"\nFALHOU: {descricao}")
        return False
    return True


def _versao_do_zip() -> str | None:
    """Lê a VERSAO do config.py que foi de fato empacotado no ZIP."""
    with zipfile.ZipFile(ZIP_DOWNLOAD) as pacote:
        alvo = next((n for n in pacote.namelist() if n.endswith("/config.py")), None)
        if alvo is None:
            return None
        conteudo = pacote.read(alvo).decode("utf-8")
    achado = re.search(r'VERSAO:\s*Final\[str\]\s*=\s*"([^"]+)"', conteudo)
    return achado.group(1) if achado else None


def _versao_do_site() -> str | None:
    """Lê a VERSAO que o site vai servir."""
    texto = (RAIZ / "web" / "config.js").read_text(encoding="utf-8")
    achado = re.search(r'export const VERSAO\s*=\s*"([^"]+)"', texto)
    return achado.group(1) if achado else None


def publicar(com_exe: bool) -> int:
    """Roda a sequência de publicação e devolve o código de saída."""
    if not _rodar("1/3 · Paridade desktop <-> web", ["verificar_paridade.py"]):
        print("\nCorrija as divergências antes de publicar.")
        return 1

    if not _rodar("2/3 · Empacotando o download da versão desktop", ["empacotar_web.py"]):
        return 1

    print(f"\n{'=' * 62}\n3/3 · Conferindo a versão do pacote\n{'=' * 62}")
    versao_zip = _versao_do_zip()
    versao_site = _versao_do_site()
    if versao_zip is None or versao_zip != versao_site:
        print(f"  DIVERGE: zip={versao_zip!r} site={versao_site!r}")
        return 1
    tamanho_kb = ZIP_DOWNLOAD.stat().st_size / 1024
    print(f"  ok  site e download na versão {versao_site} ({tamanho_kb:.0f} KB)")

    if com_exe:
        # O executável é opcional porque o build leva ~3 min e ocupa ~350 MB —
        # o site não depende dele (serve o código-fonte, não o binário).
        if not _rodar("Extra · Regerando o executável", ["build_exe.py"]):
            return 1

    print(
        "\nPronto para publicar."
        "\n  • Site:     pasta web/ (Root Directory no Vercel)"
        f"\n  • Download: {ZIP_DOWNLOAD.name}, versão {versao_site}"
    )
    return 0


if __name__ == "__main__":
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument(
        "--com-exe",
        action="store_true",
        help="também regenera SistemaSolar.exe (leva ~3 min)",
    )
    sys.exit(publicar(analisador.parse_args().com_exe))
