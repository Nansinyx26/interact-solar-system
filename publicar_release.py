"""Publica o pacote desktop como asset de um GitHub Release.

Por que Release e não o site: o ZIP com o executável tem ~107 MB e o limite de
arquivo estático do Vercel é 100 MB no plano Hobby. Releases aceitam até 2 GB
por arquivo, e o link ``/releases/latest/download/<arquivo>`` sempre resolve
para a versão mais recente — a URL no config.js nunca precisa mudar.

O ZIP também não pode ir para o repositório: o Git do GitHub rejeita arquivos
acima de 100 MB (por isso ele está no .gitignore).

Uso:
    .venv\\Scripts\\python.exe publicar_release.py            # publica
    .venv\\Scripts\\python.exe publicar_release.py --conferir # só verifica

Precisa do GitHub CLI autenticado (``gh auth login``). Sem ele, o script
imprime o passo a passo manual pela interface web.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ZIP = RAIZ / "web" / "sistema-solar-gestos.zip"

# Repositório e URL precisam bater com o que o site anuncia.
REPOSITORIO = "Nansinyx26/interact-solar-system-exe"
URL_ESPERADA = (
    f"https://github.com/{REPOSITORIO}/releases/latest/download/{ZIP.name}"
)


def _versao() -> str:
    """Versão declarada no config.py (a mesma do site, por paridade)."""
    texto = (RAIZ / "config.py").read_text(encoding="utf-8")
    achado = re.search(r'VERSAO:\s*Final\[str\]\s*=\s*"([^"]+)"', texto)
    if not achado:
        raise SystemExit("VERSAO não encontrada em config.py")
    return achado.group(1)


def _url_configurada() -> str | None:
    """URL que o site vai usar no botão de download."""
    texto = (RAIZ / "web" / "config.js").read_text(encoding="utf-8")
    achado = re.search(
        r"URL_DOWNLOAD_EXECUTAVEL\s*=\s*\n?\s*\"([^\"]*)\"", texto
    )
    return achado.group(1) if achado else None


def _tem_gh() -> bool:
    return shutil.which("gh") is not None


def conferir() -> list[str]:
    """Valida os pré-requisitos e devolve a lista de problemas."""
    problemas: list[str] = []

    if not ZIP.exists():
        problemas.append(
            f"{ZIP.name} não existe — rode publicar.py antes (ele gera o pacote)."
        )
    else:
        tamanho_mb = ZIP.stat().st_size / 1024 / 1024
        print(f"  pacote        {ZIP.name} — {tamanho_mb:.1f} MB")
        if tamanho_mb > 2048:
            problemas.append("o pacote passa de 2 GB, limite de asset do GitHub.")

    versao = _versao()
    print(f"  versão        {versao}")

    url = _url_configurada()
    if url != URL_ESPERADA:
        problemas.append(
            f"URL_DOWNLOAD_EXECUTAVEL no web/config.js está como {url!r};\n"
            f"    deveria ser {URL_ESPERADA!r}"
        )
    else:
        print(f"  botão do site {url}")

    print(f"  GitHub CLI    {'encontrado' if _tem_gh() else 'NÃO instalado'}")
    return problemas


def _instrucoes_manuais(versao: str) -> None:
    """Passo a passo pela interface web, para quem não tem o gh CLI."""
    print(
        f"""
Sem o GitHub CLI, publique pela interface web (leva 2 minutos):

  1. Instale o CLI (opcional, automatiza tudo daqui pra frente):
         winget install --id GitHub.cli
         gh auth login

  2. Ou faça manualmente:
     a) Abra https://github.com/{REPOSITORIO}/releases/new
     b) Em "Choose a tag", digite  v{versao}  e clique em "Create new tag"
     c) Título:  Sistema Solar Interativo v{versao}
     d) Arraste o arquivo abaixo para a área de anexos:
            {ZIP}
     e) Publique com "Publish release"

  3. Confira se o link do site responde:
         {URL_ESPERADA}
"""
    )


def publicar() -> int:
    """Cria (ou atualiza) o release da versão atual e envia o ZIP."""
    print("Conferindo pré-requisitos...")
    problemas = conferir()
    if problemas:
        print("\nPendências:")
        for item in problemas:
            print(f"  - {item}")
        return 1

    versao = _versao()
    etiqueta = f"v{versao}"

    if not _tem_gh():
        _instrucoes_manuais(versao)
        return 1

    # Release já existente: troca só o asset, para o link continuar válido.
    existe = subprocess.run(
        ["gh", "release", "view", etiqueta, "--repo", REPOSITORIO],
        capture_output=True,
        check=False,
    ).returncode == 0

    if existe:
        print(f"\nRelease {etiqueta} já existe — substituindo o pacote...")
        comando = [
            "gh", "release", "upload", etiqueta, str(ZIP),
            "--repo", REPOSITORIO, "--clobber",
        ]
    else:
        print(f"\nCriando o release {etiqueta} e enviando o pacote (~107 MB)...")
        comando = [
            "gh", "release", "create", etiqueta, str(ZIP),
            "--repo", REPOSITORIO,
            "--title", f"Sistema Solar Interativo {etiqueta}",
            "--notes", _notas(versao),
        ]

    resultado = subprocess.run(comando, check=False)
    if resultado.returncode != 0:
        print("\nFalhou. Verifique se o `gh auth login` está feito.")
        return resultado.returncode

    print(f"\nPublicado. O botão do site já aponta para:\n  {URL_ESPERADA}")
    return 0


def _notas(versao: str) -> str:
    """Corpo do release."""
    return f"""\
Pacote para Windows da versão {versao} — a mesma que está no site.

**Como usar:** baixe o `sistema-solar-gestos.zip`, extraia e dê dois cliques em
`SistemaSolar.exe`. Não precisa instalar Python.

O ZIP leva o executável pronto, a pasta de bibliotecas e o código-fonte
completo. Instruções em `COMO-USAR.txt`, dentro do pacote.

Controle o Sistema Solar mostrando números com a mão para a webcam: 0 = Sol,
3 = Terra, 5 = Júpiter, 5+4 = Lua, as duas mãos abertas voltam à visão geral.
Sem webcam, as teclas 0–9 fazem o mesmo.
"""


if __name__ == "__main__":
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument(
        "--conferir",
        action="store_true",
        help="só valida os pré-requisitos, sem publicar",
    )
    if analisador.parse_args().conferir:
        pendencias = conferir()
        for item in pendencias:
            print(f"  - {item}")
        sys.exit(1 if pendencias else 0)
    sys.exit(publicar())
