"""Síntese de voz pela ElevenLabs, com cache em disco.

Usa só a biblioteca padrão (``urllib``) — não vale a pena mais uma dependência
para dois pedidos HTTP. Devolve o MP3 em bytes; quem toca é o narrador.

Duas decisões que valem registro:

* **Cache em disco.** Cada frase sintetizada consome créditos da conta. Como as
  frases são fixas (dez corpos celestes), a primeira execução paga e todas as
  seguintes leem do disco — inclusive depois de fechar o aplicativo.
* **A chave nunca entra no código.** Ela vem de ``ELEVENLABS_API_KEY``, no
  ambiente ou num ``.env`` ao lado do ``main.py`` (que está no .gitignore).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from config import (
    ELEVENLABS_FORMATO,
    ELEVENLABS_MODELO,
    ELEVENLABS_TIMEOUT_S,
    ELEVENLABS_URL,
    ELEVENLABS_VOZ_ID,
    IDIOMA_NARRACAO,
    PASTA_CACHE_VOZ,
)

NOME_VARIAVEL = "ELEVENLABS_API_KEY"


def _raiz_do_projeto() -> Path:
    """Pasta onde ficam o .env e o cache, tanto no código quanto no .exe."""
    if getattr(sys, "frozen", False):
        # No executável, __file__ aponta para dentro do bundle temporário.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def ler_chaves() -> list[str]:
    """Procura as chaves no ambiente e, se não achar, no .env do projeto.

    Aceita múltiplas chaves separadas por vírgula para suporte a fallback.
    """
    bruto = os.environ.get(NOME_VARIAVEL, "").strip()
    if not bruto:
        arquivo = _raiz_do_projeto() / ".env"
        if arquivo.is_file():
            try:
                for linha in arquivo.read_text(encoding="utf-8").splitlines():
                    limpa = linha.strip()
                    if not limpa or limpa.startswith("#") or "=" not in limpa:
                        continue
                    nome, _, valor = limpa.partition("=")
                    if nome.strip() == NOME_VARIAVEL:
                        bruto = valor.strip().strip('"').strip("'")
                        break
            except OSError:
                pass
    if not bruto:
        return []
    return [k.strip() for k in bruto.split(",") if k.strip()]


def ler_chave() -> str | None:
    """Compatibilidade: devolve a primeira chave válida da lista."""
    chaves = ler_chaves()
    return chaves[0] if chaves else None


def _caminho_do_cache(texto: str) -> Path:
    """Arquivo de cache da frase, identificado por hash do texto e da voz."""
    assinatura = f"{ELEVENLABS_VOZ_ID}|{ELEVENLABS_MODELO}|{texto}"
    digest = hashlib.sha256(assinatura.encode("utf-8")).hexdigest()[:20]
    return _raiz_do_projeto() / PASTA_CACHE_VOZ / f"{digest}.mp3"


class SinteseElevenLabs:
    """Gera o áudio de uma frase, servindo do cache quando possível."""

    def __init__(self) -> None:
        self.chaves = ler_chaves()
        self.chave = self.chaves[0] if self.chaves else None
        self.mensagem = "" if self.chaves else f"{NOME_VARIAVEL} não configurada"
        # Uma falha de rede desliga o backend até a próxima execução: insistir a
        # cada troca de planeta só adicionaria segundos de espera à narração.
        self._desativado = not self.chaves

    @property
    def disponivel(self) -> bool:
        """True enquanto vale a pena tentar a ElevenLabs."""
        return not self._desativado

    def audio(self, texto: str) -> bytes | None:
        """MP3 da frase, do cache ou da API. ``None`` se não deu para gerar."""
        cache = _caminho_do_cache(texto)
        try:
            if cache.is_file():
                return cache.read_bytes()
        except OSError:
            pass  # cache ilegível não é motivo para desistir da fala

        if self._desativado:
            return None

        dados = self._pedir_a_api(texto)
        if dados is None:
            return None
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(dados)
        except OSError:
            pass  # sem permissão de escrita: funciona, só não guarda
        return dados

    def _pedir_a_api(self, texto: str) -> bytes | None:
        """Chama a ElevenLabs e devolve o MP3, testando fallback de chaves em erro 401/403/429."""
        corpo = json.dumps(
            {
                "text": texto,
                "model_id": ELEVENLABS_MODELO,
                "language_code": IDIOMA_NARRACAO.split("-")[0],
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }
        ).encode("utf-8")

        chaves_para_testar = list(self.chaves)
        for chave in chaves_para_testar:
            pedido = urllib.request.Request(
                f"{ELEVENLABS_URL}/{ELEVENLABS_VOZ_ID}?output_format={ELEVENLABS_FORMATO}",
                data=corpo,
                headers={
                    "xi-api-key": chave,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
            )
            try:
                with urllib.request.urlopen(pedido, timeout=ELEVENLABS_TIMEOUT_S) as resposta:
                    return resposta.read()
            except urllib.error.HTTPError as erro:
                detalhe = erro.read()[:200].decode("utf-8", errors="replace")
                self.mensagem = f"ElevenLabs HTTP {erro.code}: {detalhe}"
                if erro.code in (401, 403, 429):
                    if chave in self.chaves:
                        self.chaves.remove(chave)
                    continue
                break
            except (urllib.error.URLError, TimeoutError, OSError) as erro:
                self.mensagem = f"ElevenLabs indisponível: {erro}"
                break

        if not self.chaves:
            self._desativado = True
        print(f"[narrador] {self.mensagem}", flush=True)
        return None

