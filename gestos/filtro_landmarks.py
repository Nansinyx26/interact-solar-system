"""Suavização dos 21 landmarks da mão, ANTES de qualquer classificação.

O reconhecimento piscava por um motivo simples: o MediaPipe entrega cada ponto
com alguns pixels de ruído por frame, e um dedo parado exatamente na fronteira
do limiar alternava entre "aberto" e "fechado" sem o usuário mexer a mão.
Filtrar depois (votando no gesto) esconde o sintoma; filtrar aqui remove a
causa — e sai mais barato, porque o filtro roda sobre 21 pontos em vez de sobre
uma máquina de estados inteira.

Usamos o **One Euro Filter** (Casiez, Roussel e Vogel, 2012). A alternativa
óbvia, uma média móvel exponencial de alpha fixo, força um compromisso ruim:

- alpha baixo (~0,2): estável parado, mas o gesto chega atrasado;
- alpha alto (~0,7): responsivo, mas o tremor passa inteiro.

O One Euro resolve variando o alpha com a **velocidade** do ponto: com a mão
parada ele filtra forte (o tremor some), com a mão em movimento ele solta (o
gesto não atrasa). A EMA continua disponível em ``FiltroEMA`` para comparação e
para o caso de o intervalo entre amostras não ser confiável.

O módulo não conhece pygame, câmera nem MediaPipe: recebe um array (21, 2) e
devolve outro do mesmo formato.
"""

from __future__ import annotations

import math

import numpy as np

from config import (
    ALPHA_EMA_LANDMARKS,
    UM_EURO_BETA,
    UM_EURO_CORTE_DERIVADA_HZ,
    UM_EURO_CORTE_MINIMO_HZ,
)

# Piso do intervalo entre amostras. Dois frames com o mesmo instante (ou com o
# relógio andando para trás) dariam divisão por zero no cálculo da velocidade.
_DT_MINIMO = 1e-3
# Teto: se a mão sumiu por meio segundo, tratamos como amostra nova em vez de
# calcular uma "velocidade" gigantesca a partir de uma pose antiga.
_DT_MAXIMO = 0.5


def _alpha(corte_hz: float, dt: float) -> float:
    """Converte frequência de corte + intervalo em peso de uma passa-baixa.

    É a forma discreta do filtro RC: ``alpha = dt / (tau + dt)``, com
    ``tau = 1 / (2·pi·fc)``. Corte alto -> alpha perto de 1 (quase sem filtro).
    """
    tau = 1.0 / (2.0 * math.pi * max(corte_hz, 1e-6))
    return dt / (tau + dt)


class FiltroUmEuro:
    """One Euro Filter aplicado a um array de pontos 2D.

    Guarda o estado de UMA mão. Como o MediaPipe pode trocar a ordem das mãos
    entre frames, quem chama deve manter uma instância por ``handedness`` — é o
    que ``BancoDeFiltros`` faz.
    """

    def __init__(
        self,
        corte_minimo_hz: float = UM_EURO_CORTE_MINIMO_HZ,
        beta: float = UM_EURO_BETA,
        corte_derivada_hz: float = UM_EURO_CORTE_DERIVADA_HZ,
    ) -> None:
        self._corte_minimo = corte_minimo_hz
        self._beta = beta
        self._corte_derivada = corte_derivada_hz
        self._valor: np.ndarray | None = None      # última saída filtrada
        self._derivada: np.ndarray | None = None   # velocidade filtrada
        self._instante: float | None = None

    def reiniciar(self) -> None:
        """Esquece o histórico (a mão saiu do quadro e voltou em outro lugar).

        Sem isto, a mão reaparecendo do outro lado da tela seria interpolada
        desde a posição antiga e cruzaria o quadro em linha reta por alguns
        frames — tempo de sobra para produzir contagens absurdas.
        """
        self._valor = None
        self._derivada = None
        self._instante = None

    def filtrar(self, pontos: np.ndarray, agora: float) -> np.ndarray:
        """Devolve a versão suavizada de ``pontos`` (mesmo formato da entrada)."""
        pontos = np.asarray(pontos, dtype=np.float64)

        if self._valor is None or self._instante is None:
            # Primeira amostra: não há o que filtrar, ela vira o estado inicial.
            self._valor = pontos.copy()
            self._derivada = np.zeros_like(pontos)
            self._instante = agora
            return self._valor.copy()

        dt = agora - self._instante
        if dt <= 0.0 or dt > _DT_MAXIMO:
            # Buraco grande na sequência: recomeça em vez de extrapolar.
            self.reiniciar()
            return self.filtrar(pontos, agora)
        dt = max(dt, _DT_MINIMO)
        self._instante = agora

        # 1. Velocidade bruta, ela mesma suavizada — senão o ruído da posição
        #    entraria duas vezes: uma na saída e outra pela porta do beta.
        derivada_bruta = (pontos - self._valor) / dt
        alpha_derivada = _alpha(self._corte_derivada, dt)
        derivada = self._derivada
        if derivada is None:
            derivada = np.zeros_like(pontos)
        derivada = alpha_derivada * derivada_bruta + (1.0 - alpha_derivada) * derivada
        self._derivada = derivada

        # 2. Corte adaptativo POR PONTO: cada landmark tem a própria velocidade,
        #    então o polegar em movimento não perde nitidez só porque os outros
        #    quatro dedos estão parados.
        velocidade = np.linalg.norm(derivada, axis=-1, keepdims=True)
        corte = self._corte_minimo + self._beta * velocidade
        tau = 1.0 / (2.0 * math.pi * np.maximum(corte, 1e-6))
        alpha = dt / (tau + dt)

        self._valor = alpha * pontos + (1.0 - alpha) * self._valor
        return self._valor.copy()


class FiltroEMA:
    """Média móvel exponencial de alpha fixo — o plano B do One Euro.

    Mais simples e sem dependência do intervalo entre amostras. Fica disponível
    porque em máquinas onde a taxa de inferência oscila muito o ``dt`` do One
    Euro fica ruidoso, e aí a EMA acaba se saindo melhor.
    """

    def __init__(self, alpha: float = ALPHA_EMA_LANDMARKS) -> None:
        self._alpha = min(1.0, max(0.0, alpha))
        self._valor: np.ndarray | None = None

    def reiniciar(self) -> None:
        """Esquece o histórico."""
        self._valor = None

    def filtrar(self, pontos: np.ndarray, agora: float) -> np.ndarray:
        """Suaviza ``pontos``. ``agora`` é ignorado (assinatura compartilhada)."""
        del agora  # a EMA não depende do intervalo entre amostras
        pontos = np.asarray(pontos, dtype=np.float64)
        if self._valor is None:
            self._valor = pontos.copy()
        else:
            self._valor = self._alpha * pontos + (1.0 - self._alpha) * self._valor
        return self._valor.copy()


class BancoDeFiltros:
    """Um filtro por mão, endereçado pelo ``handedness`` do MediaPipe.

    Manter o estado por LADO (e não pela posição na lista) é o que impede a
    troca de mão A com mão B: o MediaPipe não garante ordem estável entre
    frames, e um filtro compartilhado interpolaria a mão esquerda em direção à
    direita a cada inversão — exatamente o "pisca e troca de gesto sozinho".
    """

    def __init__(self, usar_um_euro: bool = True) -> None:
        self._usar_um_euro = usar_um_euro
        self._filtros: dict[str, FiltroUmEuro | FiltroEMA] = {}
        self._vistas: dict[str, float] = {}

    def _obter(self, lado: str) -> FiltroUmEuro | FiltroEMA:
        """Filtro daquele lado, criado sob demanda."""
        filtro = self._filtros.get(lado)
        if filtro is None:
            filtro = FiltroUmEuro() if self._usar_um_euro else FiltroEMA()
            self._filtros[lado] = filtro
        return filtro

    def filtrar(self, pontos: np.ndarray, lado: str, agora: float) -> np.ndarray:
        """Suaviza os landmarks de uma mão identificada por ``lado``."""
        self._vistas[lado] = agora
        return self._obter(lado).filtrar(pontos, agora)

    def esquecer_ausentes(
        self, lados_presentes: set[str], agora: float, tolerancia_s: float = 0.5
    ) -> None:
        """Zera o histórico das mãos que sumiram há mais de ``tolerancia_s``.

        Chamado a cada leitura: uma mão que volta depois de uma ausência longa
        merece começar do zero, não ser interpolada desde onde estava.
        """
        for lado, visto_em in list(self._vistas.items()):
            if lado in lados_presentes:
                continue
            if agora - visto_em > tolerancia_s:
                self._filtros.pop(lado, None)
                self._vistas.pop(lado, None)

    def reiniciar(self) -> None:
        """Zera tudo (a webcam reconectou, por exemplo)."""
        self._filtros.clear()
        self._vistas.clear()


__all__ = ["BancoDeFiltros", "FiltroEMA", "FiltroUmEuro"]
