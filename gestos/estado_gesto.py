"""Máquina de estados dos gestos: transforma landmarks em INTENÇÃO.

Não conhece pygame, câmera nem renderizador — recebe as mãos detectadas e
devolve o que o usuário quis dizer. Quem aplica é o loop principal.

A regra central é a ordem de leitura. O "L" consome dois dedos, então ele
**não pode entrar na contagem numérica**: a forma é classificada antes de
qualquer soma. Sem isso, uma mão em L somaria 2 e o modo luas ligaria já
selecionando Vênus.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from config import (
    BUFFER_SELECAO_LUA,
    COOLDOWN_SELECAO_LUA_S,
    FRAMES_PARA_ENTRAR_MODO_LUAS,
    FRAMES_PARA_SAIR_MODO_LUAS,
    VOTOS_SELECAO_LUA,
)
from gestos.contador import contar_dedos, mao_dentro_do_quadro
from gestos.formatos_mao import eh_formato_L


@dataclass(frozen=True)
class IntencaoGesto:
    """O que o usuário quis dizer neste instante."""

    modo_luas: bool
    # Número mostrado. No modo luas vem de UMA mão (0-5); fora dele é a soma
    # das duas (0-10). None quando a leitura não é utilizável.
    numero: int | None
    # 0 a 1: quanto falta para o modo trocar. Alimenta a barra de confirmação —
    # sem ela o usuário repete o gesto achando que não pegou.
    progresso_modo: float
    # True apenas no frame em que o modo mudou (evento, não estado).
    modo_mudou: bool
    # True quando alguma mão está em L, mesmo antes de o modo confirmar.
    # Serve para o HUD mostrar o ícone assim que reconhece a forma.
    l_detectado: bool
    # Índice de lua confirmado neste frame (só no modo luas). None = sem troca.
    lua_confirmada: int | None = None


class MaquinaGestos:
    """Estados NORMAL e LUAS, com histerese e votação."""

    def __init__(self) -> None:
        self.modo_luas = False
        self._frames_com_l = 0
        self._frames_sem_l = 0
        self._buffer_lua: deque[int | None] = deque(maxlen=BUFFER_SELECAO_LUA)
        self._lua_confirmada: int | None = None
        self._instante_ultima_lua = -COOLDOWN_SELECAO_LUA_S

    def reiniciar(self) -> None:
        """Volta ao modo normal (usado pelo gesto 10 e pelo ESC)."""
        self.modo_luas = False
        self._frames_com_l = 0
        self._frames_sem_l = 0
        self._buffer_lua.clear()
        self._lua_confirmada = None

    def atualizar(
        self, maos: list[tuple[np.ndarray, str]], agora: float
    ) -> IntencaoGesto:
        """Classifica as mãos e devolve a intenção do frame."""
        # 1. Descartar mãos cortadas pela borda antes de qualquer decisão.
        usaveis = [
            (pontos, lado) for pontos, lado in maos if mao_dentro_do_quadro(pontos)
        ]

        # 2. Classificar a FORMA de cada mão antes de contar qualquer dedo.
        formas = [
            (pontos, lado, eh_formato_L(pontos, lado)) for pontos, lado in usaveis
        ]
        maos_em_l = [f for f in formas if f[2]]
        outras = [f for f in formas if not f[2]]

        # 3. Duas mãos em L é estado inválido: não muda nada.
        if len(maos_em_l) >= 2:
            return IntencaoGesto(
                modo_luas=self.modo_luas,
                numero=None,
                progresso_modo=self._progresso(),
                modo_mudou=False,
                l_detectado=True,
            )

        tem_l = len(maos_em_l) == 1
        modo_mudou = self._atualizar_histerese(tem_l)

        # 4. O número sai da mão que NÃO faz o L.
        if tem_l:
            # Só a mão do L na tela: número 0 (mostrar todas as luas).
            numero = contar_dedos(*outras[0][:2]) if outras else 0
        elif usaveis:
            numero = sum(contar_dedos(pontos, lado) for pontos, lado in usaveis)
        else:
            numero = None

        lua = self._votar_lua(numero, agora) if self.modo_luas else None

        return IntencaoGesto(
            modo_luas=self.modo_luas,
            numero=numero,
            progresso_modo=self._progresso(),
            modo_mudou=modo_mudou,
            l_detectado=tem_l,
            lua_confirmada=lua,
        )

    # ------------------------------------------------------------- internos
    def _atualizar_histerese(self, tem_l: bool) -> bool:
        """Conta frames consecutivos e troca o modo quando o limite é atingido."""
        if tem_l:
            self._frames_com_l += 1
            self._frames_sem_l = 0
        else:
            self._frames_sem_l += 1
            self._frames_com_l = 0

        if not self.modo_luas and self._frames_com_l >= FRAMES_PARA_ENTRAR_MODO_LUAS:
            self.modo_luas = True
            self._buffer_lua.clear()
            return True
        if self.modo_luas and self._frames_sem_l >= FRAMES_PARA_SAIR_MODO_LUAS:
            self.modo_luas = False
            # A lua escolhida PERMANECE: sair do modo é largar o modificador,
            # não desfazer a escolha.
            return True
        return False

    def _progresso(self) -> float:
        """Quanto falta para a próxima troca de modo, de 0 a 1."""
        if self.modo_luas:
            return min(1.0, self._frames_sem_l / FRAMES_PARA_SAIR_MODO_LUAS)
        return min(1.0, self._frames_com_l / FRAMES_PARA_ENTRAR_MODO_LUAS)

    def _votar_lua(self, numero: int | None, agora: float) -> int | None:
        """Confirma a lua por maioria, com cooldown entre trocas."""
        self._buffer_lua.append(numero)
        votos: dict[int, int] = {}
        for valor in self._buffer_lua:
            if valor is not None:
                votos[valor] = votos.get(valor, 0) + 1
        if not votos:
            return None

        candidato = max(votos, key=lambda v: votos[v])
        if votos[candidato] < VOTOS_SELECAO_LUA:
            return None
        if candidato == self._lua_confirmada:
            return None
        if agora - self._instante_ultima_lua < COOLDOWN_SELECAO_LUA_S:
            return None

        self._lua_confirmada = candidato
        self._instante_ultima_lua = agora
        return candidato


__all__ = ["IntencaoGesto", "MaquinaGestos"]
