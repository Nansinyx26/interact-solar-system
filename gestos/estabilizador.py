"""Estabilização temporal do gesto reconhecido.

Reconhecimento cru oscila entre valores vizinhos (4/5/4/5...) e trocaria o foco
dezenas de vezes por segundo. Aqui a leitura crua passa por três filtros:

1. buffer temporal das últimas N leituras;
2. confirmação por maioria (o mesmo número em >= 70% do buffer);
3. cooldown após cada troca confirmada.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass

from config import (
    COOLDOWN_TROCA_S,
    FRACAO_MAIORIA,
    TAMANHO_BUFFER_GESTOS,
)


@dataclass(frozen=True)
class ResultadoEstabilizacao:
    """Saída de um ciclo do estabilizador."""

    confirmado: int | None  # valor confirmado NESTE instante (dispara a troca)
    candidato: int | None  # valor liderando a votação
    progresso: float  # 0..1 — quanto falta para confirmar
    em_cooldown: bool


class EstabilizadorGestos:
    """Transforma leituras ruidosas em trocas de alvo confiáveis."""

    def __init__(self) -> None:
        self._buffer: deque[int | None] = deque(maxlen=TAMANHO_BUFFER_GESTOS)
        self._votos_necessarios = max(
            2, int(round(TAMANHO_BUFFER_GESTOS * FRACAO_MAIORIA))
        )
        self._valor_confirmado: int | None = None
        self._instante_ultima_troca: float = -COOLDOWN_TROCA_S
        self._instante_ultimo_gesto: float | None = None

    @property
    def valor_confirmado(self) -> int | None:
        """Último número confirmado (mantido mesmo sem mãos no quadro)."""
        return self._valor_confirmado

    def segundos_sem_gesto(self, agora: float) -> float:
        """Há quanto tempo não chega uma leitura válida."""
        if self._instante_ultimo_gesto is None:
            return 0.0
        return agora - self._instante_ultimo_gesto

    def reiniciar(self) -> None:
        """Esquece o alvo confirmado (usado ao voltar à visão geral)."""
        self._buffer.clear()
        self._valor_confirmado = None

    def forcar(self, valor: int, agora: float) -> None:
        """Define o alvo diretamente (atalho de teclado), zerando a votação."""
        self._buffer.clear()
        self._valor_confirmado = valor
        self._instante_ultima_troca = agora
        self._instante_ultimo_gesto = agora

    def atualizar(self, leitura: int | None, agora: float) -> ResultadoEstabilizacao:
        """Registra uma leitura e devolve o estado da confirmação.

        ``leitura`` é ``None`` quando não há mão utilizável no quadro; nesse caso
        o alvo confirmado é preservado — sumir da frente da câmera não deve
        desfazer a seleção.
        """
        self._buffer.append(leitura)
        if leitura is not None:
            self._instante_ultimo_gesto = agora

        votos = Counter(v for v in self._buffer if v is not None)
        candidato: int | None = None
        contagem = 0
        if votos:
            candidato, contagem = votos.most_common(1)[0]

        em_cooldown = (agora - self._instante_ultima_troca) < COOLDOWN_TROCA_S

        # O progresso ignora o candidato já confirmado: o anel só enche quando o
        # usuário está de fato pedindo uma troca.
        if candidato is None or candidato == self._valor_confirmado:
            progresso = 0.0
        else:
            progresso = min(1.0, contagem / self._votos_necessarios)

        confirmado: int | None = None
        if (
            candidato is not None
            and candidato != self._valor_confirmado
            and contagem >= self._votos_necessarios
            and not em_cooldown
        ):
            self._valor_confirmado = candidato
            self._instante_ultima_troca = agora
            confirmado = candidato
            progresso = 1.0

        return ResultadoEstabilizacao(
            confirmado=confirmado,
            candidato=candidato,
            progresso=progresso,
            em_cooldown=em_cooldown,
        )


__all__ = ["EstabilizadorGestos", "ResultadoEstabilizacao"]
