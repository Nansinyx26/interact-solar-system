"""Integração com MongoDB Atlas para registro de telemetria e uso do sistema.

Todos os registros são assíncronos (executados em threads separadas) para nunca
bloquear nem congelar a renderização do Pygame nem causar atrasos no loop.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import VERSAO

# Tenta importar pymongo
try:
    import pymongo

    PYMONGO_DISPONIVEL = True
except ImportError:  # pragma: no cover
    pymongo = None  # type: ignore[assignment]
    PYMONGO_DISPONIVEL = False

NOME_VARIAVEL_URI = "MONGODB_URI"


def _raiz_do_projeto() -> Path:
    """Pasta onde fica o arquivo .env."""
    import sys

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def ler_uri_mongo() -> str | None:
    """Lê a URI do MongoDB do ambiente ou do arquivo .env."""
    do_ambiente = os.environ.get(NOME_VARIAVEL_URI, "").strip()
    if do_ambiente:
        return do_ambiente

    arquivo = _raiz_do_projeto() / ".env"
    if not arquivo.is_file():
        return None
    try:
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            limpa = linha.strip()
            if not limpa or limpa.startswith("#") or "=" not in limpa:
                continue
            nome, _, valor = limpa.partition("=")
            if nome.strip() == NOME_VARIAVEL_URI:
                return valor.strip().strip('"').strip("'") or None
    except OSError:
        return None
    return None


class TelemetriaMongo:
    """Gerencia a conexão com o MongoDB Atlas e grava eventos em segundo plano."""

    def __init__(self) -> None:
        self.uri = ler_uri_mongo()
        self._cliente: Any = None
        self._colecao_sessoes: Any = None
        self._colecao_interacoes: Any = None
        self._colecao_ranking: Any = None
        self._disponivel = PYMONGO_DISPONIVEL and (pymongo is not None) and bool(self.uri)
        self._lock = threading.Lock()
        self._conectado = False

    @property
    def disponivel(self) -> bool:
        """True se a extensão pymongo e a URI do MongoDB estiverem configuradas."""
        return self._disponivel and pymongo is not None

    def _conectar(self) -> bool:
        if not self._disponivel or not self.uri or pymongo is None:
            return False
        if self._conectado:
            return True
        with self._lock:
            if self._conectado:
                return True
            try:
                self._cliente = pymongo.MongoClient(
                    self.uri, serverSelectionTimeoutMS=3000
                )
                db = self._cliente["sistema_solar"]
                self._colecao_sessoes = db["sessoes"]
                self._colecao_interacoes = db["interacoes"]
                self._colecao_ranking = db["ranking"]
                self._conectado = True
                print("[telemetria] Conectado ao MongoDB Atlas com sucesso.", flush=True)
                return True
            except Exception as erro:
                print(f"[telemetria] Falha ao conectar ao MongoDB: {erro}", flush=True)
                self._disponivel = False
                return False

    def registrar_sessao(self, origem: str = "desktop") -> None:
        """Registra o início de uma sessão do aplicativo em segundo plano."""
        if not self._disponivel:
            return

        def _tarefa() -> None:
            if not self._conectar():
                return
            try:
                doc = {
                    "origem": origem,
                    "versao": VERSAO,
                    "data_hora": datetime.now(timezone.utc),
                    "timestamp": time.time(),
                }
                self._colecao_sessoes.insert_one(doc)
            except Exception as erro:
                print(f"[telemetria] Erro ao registrar sessão: {erro}", flush=True)

        threading.Thread(target=_tarefa, daemon=True, name="telemetria_sessao").start()

    def registrar_interacao(
        self, corpo: str, gesto: str | int | None = None, origem: str = "desktop"
    ) -> None:
        """Registra a seleção/foco de um corpo celeste em segundo plano."""
        if not self._disponivel:
            return

        def _tarefa() -> None:
            if not self._conectar():
                return
            try:
                doc = {
                    "corpo": corpo,
                    "gesto": str(gesto) if gesto is not None else None,
                    "origem": origem,
                    "versao": VERSAO,
                    "data_hora": datetime.now(timezone.utc),
                    "timestamp": time.time(),
                }
                self._colecao_interacoes.insert_one(doc)
            except Exception as erro:
                print(f"[telemetria] Erro ao registrar interação: {erro}", flush=True)

        threading.Thread(
            target=_tarefa, daemon=True, name="telemetria_interacao"
        ).start()

    def registrar_ranking(
        self,
        nome: str,
        serie: str = "Geral",
        pontuacao: int = 100,
        acertos: int = 10,
        tempo_segundos: float = 0.0,
        origem: str = "desktop",
    ) -> None:
        """Registra a pontuação de um aluno no ranking do MongoDB em segundo plano."""
        if not self._disponivel:
            return

        def _tarefa() -> None:
            if not self._conectar():
                return
            try:
                doc = {
                    "nome": nome.strip()[:50],
                    "serie": serie.strip()[:30] or "Geral",
                    "pontuacao": max(0, int(pontuacao)),
                    "acertos": max(0, int(acertos)),
                    "tempoSegundos": max(0.0, float(tempo_segundos)),
                    "origem": origem,
                    "versao": VERSAO,
                    "data_hora": datetime.now(timezone.utc),
                    "timestamp": time.time(),
                }
                self._colecao_ranking.insert_one(doc)
                print(f"[ranking] Pontuação de '{nome}' ({serie}) registrada no MongoDB.", flush=True)
            except Exception as erro:
                print(f"[ranking] Erro ao registrar pontuação: {erro}", flush=True)

        threading.Thread(target=_tarefa, daemon=True, name="ranking_registro").start()

    def obter_top_ranking(self, serie: str = "Todas", limite: int = 10) -> list[dict[str, Any]]:
        """Retorna as melhores pontuações do ranking no MongoDB."""
        if not self._disponivel or not self._conectar():
            return []
        try:
            filtro = {}
            if serie and serie != "Todas":
                filtro["serie"] = serie
            cursor = (
                self._colecao_ranking.find(filtro)
                .sort([("pontuacao", -1), ("tempoSegundos", 1), ("timestamp", -1)])
                .limit(limite)
            )
            return list(cursor)
        except Exception as erro:
            print(f"[ranking] Erro ao buscar top ranking: {erro}", flush=True)
            return []

    def remover_ranking(self, id_registro: str, codigo: str = "4400") -> bool:
        """Remove um registro do ranking pelo ID (requer código 4400)."""
        if codigo != "4400":
            print("[ranking] Código de autorização incorreto! Exclusão negada.", flush=True)
            return False
        if not self._disponivel or not self._conectar():
            return False
        try:
            from bson.objectid import ObjectId
            res = self._colecao_ranking.delete_one({"_id": ObjectId(id_registro)})
            return res.deleted_count > 0
        except Exception as erro:
            print(f"[ranking] Erro ao remover registro: {erro}", flush=True)
            return False

    def limpar_ranking(self, codigo: str = "4400") -> bool:
        """Limpa todo o ranking (requer código 4400)."""
        if codigo != "4400":
            print("[ranking] Código de autorização incorreto! Exclusão negada.", flush=True)
            return False
        if not self._disponivel or not self._conectar():
            return False
        try:
            self._colecao_ranking.delete_many({})
            print("[ranking] Todo o ranking foi limpo.", flush=True)
            return True
        except Exception as erro:
            print(f"[ranking] Erro ao limpar ranking: {erro}", flush=True)
            return False
