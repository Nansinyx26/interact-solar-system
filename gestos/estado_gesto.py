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
    COOLDOWN_APOS_L_S,
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
    #
    # OBSOLETO: a confirmação passou para gestos/seletor_lua.py, que separa
    # PREVIEW de FICHA. O campo continua aqui porque a versão web ainda o lê e
    # o teclado ainda o alimenta; quem decide hoje é o SeletorLua.
    lua_confirmada: int | None = None
    # Quantas mãos utilizáveis havia no quadro. O seletor precisa disto para
    # distinguir "não mostrou número" de "só tem uma mão na tela" — são avisos
    # de HUD diferentes, e o número sozinho não conta essa história.
    maos_visiveis: int = 0


class MaquinaGestos:
    """Estados NORMAL e LUAS, com histerese e votação."""

    def __init__(self) -> None:
        self.modo_luas = False
        self._frames_com_l = 0
        self._frames_sem_l = 0
        self._buffer_lua: deque[int | None] = deque(maxlen=BUFFER_SELECAO_LUA)
        self._lua_confirmada: int | None = None
        self._instante_ultima_lua = -COOLDOWN_SELECAO_LUA_S
        # Quando o "L" foi visto pela última vez. Alimenta bloqueando_planetas().
        self._instante_ultimo_l = -COOLDOWN_APOS_L_S

    def reiniciar(self) -> None:
        """Volta ao modo normal (usado pelo gesto 10 e pelo ESC)."""
        self.modo_luas = False
        self._frames_com_l = 0
        self._frames_sem_l = 0
        self._buffer_lua.clear()
        self._lua_confirmada = None
        self._instante_ultimo_l = -COOLDOWN_APOS_L_S

    def bloqueando_planetas(self, agora: float) -> bool:
        """True quando a contagem de dedos NÃO deve selecionar um planeta.

        Existe porque a seleção de planeta é alimentada pela contagem CRUA do
        detector, que soma todas as mãos do quadro e desconhece a forma de cada
        uma. Com o planeta X selecionado, "L" numa mão + 2 dedos na outra devia
        abrir a lua 2 de X — mas aquele 2 (ou o 4 da soma com os dois dedos do
        próprio L) chegava ao estabilizador de planetas e levava para Vênus ou
        Marte antes de o modo lua sequer ligar.

        A regra passa a ser: havendo um "L" no quadro, o número da outra mão é
        índice de LUA e nada mais. Só uma contagem sem nenhum L no quadro pode
        virar planeta — que é a leitura natural de "mostrar dois dedos".

        Vale também por COOLDOWN_APOS_L_S depois que o L some, cobrindo tanto o
        piscar do rastreio quanto as poses intermediárias de desfazer o gesto.
        """
        if self.modo_luas:
            return True
        return (agora - self._instante_ultimo_l) < COOLDOWN_APOS_L_S

    def alternar_modo_luas(self) -> bool:
        """Liga/desliga o modo pela tecla, sem passar pela histerese.

        Existe para dar um caminho sem câmera ao mesmo estado que o gesto "L"
        alcança — teclado é o plano B quando a webcam não colabora, e também é
        o que torna o modo testável sem mãos na frente da tela.
        """
        self.modo_luas = not self.modo_luas
        self._frames_com_l = 0
        self._frames_sem_l = 0
        self._buffer_lua.clear()
        return self.modo_luas

    def atualizar(
        self, maos: list[tuple[np.ndarray, str]], agora: float
    ) -> IntencaoGesto:
        """Classifica as mãos e devolve a intenção do frame."""
        # 1. Classificar a FORMA de TODAS as mãos, antes de qualquer contagem e
        #    ANTES do filtro de borda.
        #
        #    A ordem antiga descartava primeiro as mãos cortadas pela borda e só
        #    então olhava a forma — e o "L" é justamente o gesto que mais cai
        #    nesse filtro: o polegar aponta para a lateral e encosta no limite do
        #    quadro. Descartada a mão, sobrava só a do número, `tem_l` dava False
        #    e "L + 2 dedos" virava um simples "2" — ou seja, Vênus, em vez da
        #    lua 2 do planeta selecionado.
        #
        #    Reconhecer a forma primeiro é seguro porque o "L" é geometria
        #    relativa à própria palma (ver formatos_mao.py): ele sobrevive a
        #    landmarks um pouco fora de [0, 1], que o MediaPipe extrapola de
        #    qualquer jeito. O que NÃO sobrevive à borda é a contagem de dedos.
        formas = [(pontos, lado, eh_formato_L(pontos, lado)) for pontos, lado in maos]
        maos_em_l = [f for f in formas if f[2]]

        # 2. Para CONTAR dedos, aí sim só valem mãos inteiras: numa mão cortada
        #    ao meio a contagem é lixo, e é dela que sai o índice da lua.
        outras = [f for f in formas if not f[2] and mao_dentro_do_quadro(f[0])]
        # Uma mão conta como presente se está inteira no quadro OU se foi
        # reconhecida como "L" — o seletor de lua exige duas mãos na tela, e sem
        # esta segunda cláusula a mão do L não entrava na conta.
        usaveis = [
            (pontos, lado)
            for pontos, lado, eh_l in formas
            if eh_l or mao_dentro_do_quadro(pontos)
        ]

        # 3. Duas mãos em L: a PRIMEIRA detectada vira âncora e a segunda passa
        #    a valer como mão de número. Antes isto era estado inválido e não
        #    mudava nada — mas fazer o L com as duas mãos é um erro comum de
        #    quem está aprendendo o gesto, e congelar a tela sem explicação era
        #    o pior desfecho possível. Um L conta como 2 dedos, então o usuário
        #    vê a lua 2 em preview e entende sozinho o que fazer.
        if len(maos_em_l) >= 2:
            outras = [maos_em_l[1]] + outras
            maos_em_l = maos_em_l[:1]

        tem_l = len(maos_em_l) == 1
        # Marca a presença do L ANTES da histerese: o bloqueio da seleção de
        # planeta precisa valer já no primeiro frame em que a forma aparece, e
        # não só depois das FRAMES_PARA_ENTRAR_MODO_LUAS leituras que confirmam
        # o modo. Era nessa janela que o número escapava para o planeta.
        if tem_l:
            self._instante_ultimo_l = agora
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
            maos_visiveis=len(usaveis),
        )

    # ------------------------------------------------------------- internos
    def _atualizar_histerese(self, tem_l: bool) -> bool:
        """Conta frames consecutivos e troca o modo quando o limite é atingido."""
        if tem_l:
            self._frames_com_l += 1
            self._frames_sem_l = 0
        else:
            self._frames_sem_l += 1
            # DESCONTA em vez de zerar. Zerando, uma única leitura ruim no meio
            # do gesto obrigava a recomeçar do zero — e como o "L" precisa de 6
            # leituras SEGUIDAS, bastava o rastreio piscar uma vez a cada cinco
            # para o modo lua nunca ligar, por mais que o usuário insistisse.
            # Descontando, 4 acertos em 5 leituras ainda chegam lá; alternar
            # meio a meio (que não é um L firme) continua não chegando.
            self._frames_com_l = max(0, self._frames_com_l - 1)

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
