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


def _token_do_git() -> str | None:
    """Obtém o token do GitHub já guardado pelo credential helper do Git.

    É a mesma credencial que o ``git push`` usa nesta máquina, lida pelo canal
    oficial (``git credential fill``) — nada é digitado nem gravado por aqui.
    Permite publicar o release sem instalar o GitHub CLI.
    """
    try:
        resultado = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if resultado.returncode != 0:
        return None
    for linha in resultado.stdout.splitlines():
        if linha.startswith("password="):
            return linha.partition("=")[2].strip() or None
    return None


def _publicar_pela_api(etiqueta: str, versao: str, token: str) -> int:
    """Cria o release e envia o ZIP usando a API REST do GitHub."""
    import json
    import urllib.error
    import urllib.request

    base = f"https://api.github.com/repos/{REPOSITORIO}"
    cabecalhos = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "sistema-solar-gestos",
    }

    def _pedir(url: str, dados: bytes | None = None, extra: dict | None = None,
               metodo: str | None = None):
        pedido = urllib.request.Request(
            url, data=dados, headers={**cabecalhos, **(extra or {})}, method=metodo
        )
        with urllib.request.urlopen(pedido, timeout=900) as resposta:
            corpo = resposta.read()
            return json.loads(corpo) if corpo else {}

    # O GitHub recusa criar release em repositório sem nenhum commit
    # ("Repository is empty"), então o primeiro uso semeia um README.
    try:
        _pedir(f"{base}/contents/README.md")
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            print("  repositório vazio — criando o README inicial...")
            import base64

            corpo = json.dumps(
                {
                    "message": "Adiciona o README dos pacotes de instalação",
                    "content": base64.b64encode(_leia_me_do_repositorio().encode()).decode(),
                }
            ).encode()
            try:
                _pedir(
                    f"{base}/contents/README.md",
                    corpo,
                    {"Content-Type": "application/json"},
                    metodo="PUT",
                )
            except urllib.error.HTTPError as falha:
                print(f"  HTTP {falha.code}: {falha.read()[:300]!r}")
                return 1

    # Release já existente: reaproveita, para o link /latest/ não mudar.
    try:
        release = _pedir(f"{base}/releases/tags/{etiqueta}")
        print(f"  release {etiqueta} já existe (id {release['id']})")
    except urllib.error.HTTPError as erro:
        if erro.code != 404:
            print(f"  falha ao consultar o release: HTTP {erro.code} {erro.read()[:200]!r}")
            return 1
        print(f"  criando o release {etiqueta}...")
        corpo = json.dumps(
            {
                "tag_name": etiqueta,
                "name": f"Sistema Solar Interativo {etiqueta}",
                "body": _notas(versao),
                "draft": False,
                "prerelease": False,
            }
        ).encode()
        try:
            release = _pedir(f"{base}/releases", corpo, {"Content-Type": "application/json"})
        except urllib.error.HTTPError as falha:
            print(f"  HTTP {falha.code}: {falha.read()[:300]!r}")
            if falha.code in (401, 403):
                print("  O token salvo não tem permissão de escrita neste repositório.")
            return 1

    # Asset com o mesmo nome precisa sair antes: a API não sobrescreve.
    for asset in release.get("assets", []):
        if asset["name"] == ZIP.name:
            print(f"  removendo o asset anterior ({asset['size'] / 1024 / 1024:.1f} MB)...")
            _pedir(f"{base}/releases/assets/{asset['id']}", metodo="DELETE")

    tamanho_mb = ZIP.stat().st_size / 1024 / 1024
    print(f"  enviando {ZIP.name} ({tamanho_mb:.1f} MB) — pode levar vários minutos...")
    url_upload = release["upload_url"].split("{")[0] + f"?name={ZIP.name}"
    try:
        enviado = _pedir(
            url_upload,
            ZIP.read_bytes(),
            {"Content-Type": "application/zip"},
        )
    except urllib.error.HTTPError as falha:
        print(f"  HTTP {falha.code}: {falha.read()[:300]!r}")
        return 1

    print(f"  asset publicado: {enviado.get('browser_download_url')}")
    return 0


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
        # Sem o CLI, tenta a API REST com a credencial que o Git já usa.
        token = _token_do_git()
        if token:
            print("\nGitHub CLI ausente — publicando pela API com a credencial do Git.")
            codigo = _publicar_pela_api(etiqueta, versao, token)
            if codigo == 0:
                print(f"\nPublicado. O botão do site já aponta para:\n  {URL_ESPERADA}")
            return codigo
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


def _leia_me_do_repositorio() -> str:
    """README do repositório de pacotes (ele existe só para hospedar releases)."""
    return """\
# Sistema Solar Interativo — pacotes para Windows

Este repositório existe para **hospedar o executável**. O pacote tem ~107 MB, o
que passa dos limites de 100 MB por arquivo tanto do Git quanto do plano Hobby
do Vercel — GitHub Releases aceita até 2 GB por arquivo e resolve o problema.

## Baixar

**[⬇ Baixar a versão mais recente](../../releases/latest)**

Extraia o ZIP e dê dois cliques em `SistemaSolar.exe`. Não precisa instalar
Python. Instruções completas em `COMO-USAR.txt`, dentro do pacote.

## O que é

Um Sistema Solar animado que você controla **mostrando números com a mão** para
a webcam: 0 = Sol, 3 = Terra, 5 = Júpiter, 5+4 = Lua, as duas mãos abertas
voltam à visão geral. Sem webcam funciona igual, pelas teclas 0–9.

O reconhecimento roda localmente (MediaPipe): nenhuma imagem sai do computador.

## Código-fonte

O código, a versão web e a documentação ficam em
**[interact-solar-system](https://github.com/Nansinyx26/interact-solar-system)**.
O código-fonte completo também vai dentro de cada pacote publicado aqui.
"""


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
