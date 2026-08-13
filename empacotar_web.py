"""Gera o ZIP da versão desktop servido pelo botão "Baixar" do site.

O pacote leva o **executável pronto** (``SistemaSolar.exe`` mais a pasta de
bibliotecas ao lado dele) e o código-fonte completo, tudo dentro de uma única
pasta ``sistema_solar_gestos/``. Quem baixa extrai e dá dois cliques — sem
Python, sem pip, sem ambiente virtual.

Se o executável ainda não tiver sido gerado (``build_exe.py``), o pacote sai só
com o código-fonte e o script avisa.

Uso:
    .venv\\Scripts\\python.exe empacotar_web.py
    .venv\\Scripts\\python.exe empacotar_web.py --sem-exe   (só o código-fonte)
"""

from __future__ import annotations

import argparse
import sys
import time
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "web" / "sistema-solar-gestos.zip"
NOME_PASTA = "sistema_solar_gestos"

# Limite de upload de arquivos estáticos do Vercel (docs/limits): 100 MB no
# plano Hobby, 1 GB no Pro. Acima disso o deploy falha — o script avisa em vez
# de deixar a descoberta para o dia da publicação.
LIMITE_VERCEL_HOBBY_MB = 100
LIMITE_VERCEL_PRO_MB = 1024

# Executável e a pasta de bibliotecas que precisa viajar ao lado dele.
NOME_EXECUTAVEL = "SistemaSolar.exe"
PASTA_BIBLIOTECAS = "_internal_sistema_solar"

# Tudo que o usuário precisa para rodar e para gerar o próprio executável.
ARQUIVOS = [
    "main.py",
    "config.py",
    "requirements.txt",
    "README.md",
    "ROADMAP.md",
    "TAREFAS.md",
    "build_exe.py",
    "empacotar_web.py",
    "publicar.py",
    "verificar_paridade.py",
    ".gitignore",
]
PACOTES = ["dados", "nucleo", "gestos", "ui"]
EXTRAS = ["docs"]

# O que nunca entra: ambiente virtual, caches e a versão web (já publicada).
IGNORADOS = {".venv", "__pycache__", "web", "build_dist", "build_temp"}

LEIA_ME = """\
SISTEMA SOLAR INTERATIVO POR GESTOS
===================================

COMO RODAR (mais simples)
-------------------------
Dê dois cliques em SistemaSolar.exe.

Não precisa instalar Python nem nada. O executável depende da pasta
_internal_sistema_solar que está aqui do lado: mantenha as duas juntas.

Na primeira execução o Windows pode perguntar se confia no programa
(ele não tem assinatura digital paga). Escolha "Mais informações" e
"Executar assim mesmo".


COMO USAR
---------
Mostre um número com a mão para a webcam e segure por meio segundo:

    0 = Sol        5 = Jupiter        (mao aberta)
    1 = Mercurio   6 = Saturno        (5 + 1, duas maos)
    2 = Venus      7 = Urano          (5 + 2)
    3 = Terra      8 = Netuno         (5 + 3)
    4 = Marte      9 = Lua            (5 + 4)

    10 = as duas maos abertas: volta para a visao geral

Uma mao so chega a 5. De 6 a 9 e preciso usar as duas maos.

Sem webcam funciona igual: teclas 0-9 focam, V volta a visao geral,
ESPACO pausa, + e - mudam a velocidade do tempo, C liga/desliga a
camera, Q sai. O mouse arrasta a cena e a roda da zoom.


RODAR PELO CODIGO-FONTE
-----------------------
    python -m venv .venv
    .venv\\Scripts\\activate
    pip install -r requirements.txt
    python main.py

Detalhes completos no README.md.
"""


def _caminho_longo(caminho: Path) -> str:
    """Prefixo \\\\?\\ para escapar do limite de 260 caracteres do Windows.

    A árvore do mediapipe dentro do bundle ultrapassa esse limite e qualquer
    leitura falha sem isto, mesmo o arquivo existindo.
    """
    return "\\\\?\\" + str(caminho.resolve())


def _deve_incluir(caminho: Path) -> bool:
    """Filtra caches e diretórios de build."""
    return not any(parte in IGNORADOS for parte in caminho.parts)


def _escrever(pacote: zipfile.ZipFile, origem: Path, destino: str) -> int:
    """Grava um arquivo no ZIP tolerando caminhos longos do Windows."""
    pacote.write(_caminho_longo(origem), destino)
    return 1


def empacotar(com_exe: bool = True) -> int:
    """Escreve o ZIP e devolve o código de saída."""
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    executavel = RAIZ / NOME_EXECUTAVEL
    bibliotecas = RAIZ / PASTA_BIBLIOTECAS
    incluir_exe = com_exe and executavel.exists() and bibliotecas.is_dir()

    if com_exe and not incluir_exe:
        print(
            f"  aviso: {NOME_EXECUTAVEL} não encontrado — o pacote sai só com o\n"
            "         código-fonte. Rode build_exe.py antes para incluí-lo."
        )

    inicio = time.perf_counter()
    total = 0
    # compresslevel 6: o nível 9 leva ~40% mais tempo e economiza menos de 1%
    # num bundle que já é quase todo DLL comprimida.
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as pacote:
        pacote.writestr(f"{NOME_PASTA}/COMO-USAR.txt", LEIA_ME)
        total += 1

        for nome in ARQUIVOS:
            origem = RAIZ / nome
            if not origem.exists():
                print(f"  aviso: {nome} não encontrado, ignorando")
                continue
            total += _escrever(pacote, origem, f"{NOME_PASTA}/{nome}")

        for pasta in PACOTES + EXTRAS:
            base = RAIZ / pasta
            if not base.exists():
                continue
            for arquivo in sorted(base.rglob("*")):
                relativo = arquivo.relative_to(RAIZ)
                if arquivo.is_dir() or not _deve_incluir(relativo):
                    continue
                total += _escrever(pacote, arquivo, f"{NOME_PASTA}/{relativo.as_posix()}")

        if incluir_exe:
            print("  empacotando o executável (leva ~1 min)...")
            total += _escrever(pacote, executavel, f"{NOME_PASTA}/{NOME_EXECUTAVEL}")
            for arquivo in sorted(bibliotecas.rglob("*")):
                try:
                    if not arquivo.is_file():
                        continue
                except OSError:
                    continue
                relativo = arquivo.relative_to(RAIZ)
                total += _escrever(pacote, arquivo, f"{NOME_PASTA}/{relativo.as_posix()}")

    tamanho_mb = DESTINO.stat().st_size / 1024 / 1024
    duracao = time.perf_counter() - inicio
    conteudo = "código-fonte + executável" if incluir_exe else "código-fonte"
    print(f"{DESTINO} — {total} arquivos, {tamanho_mb:.1f} MB ({conteudo}, {duracao:.0f}s)")

    if tamanho_mb > LIMITE_VERCEL_HOBBY_MB:
        print(
            f"\n  ATENÇÃO: {tamanho_mb:.1f} MB passa do limite de "
            f"{LIMITE_VERCEL_HOBBY_MB} MB por arquivo estático do plano Hobby do\n"
            f"  Vercel — o deploy vai falhar. Saídas possíveis:\n"
            f"    • plano Pro (limite de {LIMITE_VERCEL_PRO_MB} MB); ou\n"
            "    • publicar o executável em GitHub Releases e apontar\n"
            "      URL_DOWNLOAD_EXECUTAVEL em web/config.js para lá; ou\n"
            "    • rodar com --sem-exe (o site passa a oferecer só o código-fonte)."
        )
    return 0


if __name__ == "__main__":
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument(
        "--sem-exe",
        action="store_true",
        help="empacota apenas o código-fonte (pacote de ~400 KB)",
    )
    sys.exit(empacotar(com_exe=not analisador.parse_args().sem_exe))
