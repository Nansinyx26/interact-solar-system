"""Leitor de mãos: de um frame de webcam a uma pose classificada e estável.

Este módulo concentra TODA a etapa de percepção. Antes ela estava espalhada:
o detector chamava o MediaPipe e somava dedos, a máquina de estados
reclassificava a forma, e cada um mantinha o próprio pedaço de histórico. O
resultado era o sintoma clássico — a leitura piscava e trocava de gesto
sozinha, porque nenhuma das partes tinha memória suficiente para saber que
estava vendo a mesma mão de um frame para o outro.

A ordem aqui é deliberada, e cada etapa resolve um modo de falha diferente:

1. **Inferência** — MediaPipe devolve 21 landmarks por mão + ``handedness``.
2. **Corte por confiança** — mãos com score abaixo de ``CONFIANCA_MIN_UTIL``
   são lixo (cortina, rosto, mão do fundo). Descartadas.
3. **Reaproveitamento** — se sobrar nada, a última pose boa vale por mais uns
   frames em vez de zerar tudo. É o que impede o modo luas de cair por causa de
   uma piscada do rastreio.
4. **Filtro One Euro** — suaviza os landmarks, por mão, indexado pelo
   ``handedness``. Aqui morre o tremor que fazia o dedo na fronteira oscilar.
5. **Classificação com histerese** — dedos e forma, cada mão comparada com a
   PRÓPRIA leitura anterior.
6. **Votação temporal** — o gesto exposto é a moda das últimas N leituras, não
   a do frame atual.

Nada de pygame nem de OpenCV além do ``cvtColor``: entra frame, sai pose.

Equivalências com a especificação (``HandGestureReader``)::

    update(frame)     -> atualizar(quadro)
    current_gesture   -> gesto_atual
    finger_count      -> contagem_dedos
    is_L              -> eh_L
    stability_ratio   -> razao_estabilidade
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np

from config import (
    CONFIANCA_MIN_DETECCAO,
    CONFIANCA_MIN_RASTREIO,
    CONFIANCA_MIN_UTIL,
    COMPLEXIDADE_MODELO,
    FILTRO_LANDMARKS_ATIVO,
    JANELA_REAPROVEITAMENTO_S,
    MAX_MAOS,
    TAMANHO_BUFFER_GESTOS,
)
from gestos.contador import (
    DEDOS_TODOS_FECHADOS,
    EstadoDedos,
    classificar_dedos,
    mao_dentro_do_quadro,
    medir_pinca,
)
from gestos.filtro_landmarks import BancoDeFiltros
from gestos.formatos_mao import eh_formato_L


@dataclass(frozen=True)
class MaoLida:
    """Uma mão já filtrada e classificada."""

    landmarks: np.ndarray  # (21, 2), suavizados
    lado: str  # handedness do MediaPipe: "Left" ou "Right"
    score: float
    dedos: EstadoDedos
    contagem: int
    eh_l: bool
    razao_pinca: float | None
    no_quadro: bool  # False = cortada pela borda, use com cautela


@dataclass(frozen=True)
class PoseMaos:
    """O que o leitor enxergou numa leitura."""

    maos: tuple[MaoLida, ...] = ()
    instante: float = 0.0
    # True quando esta pose é a anterior reapresentada porque o frame atual não
    # tinha nada aproveitável. Quem consome deve tratar como leitura válida —
    # é justamente esse o ponto — mas o HUD mostra o indicador.
    reaproveitada: bool = False
    descartada_por_borda: bool = False
    confianca_media: float = 0.0

    @property
    def contagem_total(self) -> int | None:
        """Soma dos dedos das mãos utilizáveis, ou None se não houver nenhuma."""
        usaveis = [m for m in self.maos if m.no_quadro]
        if not usaveis:
            return None
        return sum(m.contagem for m in usaveis)

    @property
    def maos_em_l(self) -> tuple[MaoLida, ...]:
        """Mãos que formam o "L", na ordem em que foram detectadas."""
        return tuple(m for m in self.maos if m.eh_l and m.no_quadro)

    @property
    def razoes_pinca(self) -> tuple[float | None, ...]:
        """Razão de pinça de cada mão, na ordem de confiança."""
        return tuple(m.razao_pinca for m in self.maos)

    @property
    def como_pares(self) -> tuple[tuple[np.ndarray, str], ...]:
        """(landmarks, lado) — o formato que a máquina de estados já consome."""
        return tuple((m.landmarks, m.lado) for m in self.maos)


class LeitorMaos:
    """Percepção completa de mãos, com memória entre frames.

    Uma instância por câmera. Não é thread-safe: quem cuida disso é o
    ``DetectorMaos``, que a usa dentro da própria thread de captura.
    """

    def __init__(self, modulo_mediapipe: Any) -> None:
        # O módulo entra por parâmetro em vez de ser importado aqui: o import do
        # MediaPipe pode falhar (falta de VC++ no Windows) e quem trata isso —
        # com mensagem e fallback de teclado — é o detector.
        self._maos = modulo_mediapipe.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_MAOS,
            model_complexity=COMPLEXIDADE_MODELO,
            min_detection_confidence=CONFIANCA_MIN_DETECCAO,
            min_tracking_confidence=CONFIANCA_MIN_RASTREIO,
        )
        self._filtros = BancoDeFiltros(usar_um_euro=FILTRO_LANDMARKS_ATIVO)
        # Histerese: a última classificação de cada mão, por handedness. Indexar
        # por LADO e não por posição na lista é o que impede a mão esquerda de
        # herdar o estado da direita quando o MediaPipe inverte a ordem.
        self._dedos_anteriores: dict[str, EstadoDedos] = {}
        self._buffer: deque[int | None] = deque(maxlen=TAMANHO_BUFFER_GESTOS)
        self._pose = PoseMaos()
        self._ultima_pose_boa: PoseMaos | None = None
        self._resultado_bruto: Any = None

    # ------------------------------------------------------------- ciclo alto
    def fechar(self) -> None:
        """Libera o modelo do MediaPipe."""
        self._maos.close()

    def reiniciar(self) -> None:
        """Esquece todo o histórico (webcam reconectou, por exemplo)."""
        self._filtros.reiniciar()
        self._dedos_anteriores.clear()
        self._buffer.clear()
        self._pose = PoseMaos()
        self._ultima_pose_boa = None
        self._resultado_bruto = None

    def atualizar(self, quadro: np.ndarray, agora: float) -> PoseMaos:
        """Processa um frame BGR e devolve a pose classificada.

        Equivale ao ``update(frame)`` da especificação. ``agora`` vem de fora
        (``time.monotonic()``) porque o filtro One Euro precisa do intervalo
        real entre amostras, e medi-lo aqui dentro esconderia o custo da
        inferência dentro do próprio dt.
        """
        rgb = cv2.cvtColor(quadro, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self._resultado_bruto = self._maos.process(rgb)
        self._pose = self._interpretar(self._resultado_bruto, agora)
        # A votação recebe a contagem já filtrada e classificada — é a última
        # camada, não a primeira.
        self._buffer.append(self._pose.contagem_total)
        return self._pose

    @property
    def resultado_bruto(self) -> Any:
        """Saída crua do MediaPipe, só para o preview desenhar os landmarks."""
        return self._resultado_bruto

    # ------------------------------------------------------------ interface
    @property
    def pose(self) -> PoseMaos:
        """Última pose interpretada."""
        return self._pose

    @property
    def gesto_atual(self) -> int | None:
        """Moda do buffer temporal — o gesto *estável*, não o do frame.

        É este valor (e não ``contagem_dedos``) que deve comandar qualquer
        troca de estado: o frame isolado é exatamente o que piscava.
        """
        votos = Counter(v for v in self._buffer if v is not None)
        if not votos:
            return None
        return votos.most_common(1)[0][0]

    @property
    def contagem_dedos(self) -> int | None:
        """Contagem crua da leitura atual (para diagnóstico e HUD de debug)."""
        return self._pose.contagem_total

    @property
    def eh_L(self) -> bool:
        """True quando ao menos uma mão forma o "L" nesta leitura."""
        return bool(self._pose.maos_em_l)

    @property
    def razao_estabilidade(self) -> float:
        """0 a 1: fração do buffer que concorda com o gesto atual.

        1,0 = as últimas N leituras disseram todas a mesma coisa. Abaixo de
        ~0,6 a mão está em transição (ou a leitura está ruim) e nenhuma decisão
        deveria ser tomada — o HUD de debug mostra isso como barra.
        """
        if not self._buffer:
            return 0.0
        votos = Counter(v for v in self._buffer if v is not None)
        if not votos:
            return 0.0
        return votos.most_common(1)[0][1] / len(self._buffer)

    # ------------------------------------------------------------- internos
    def _interpretar(self, resultado: Any, agora: float) -> PoseMaos:
        """Aplica corte por confiança, filtro, histerese e reaproveitamento."""
        brutas = self._extrair(resultado)

        # --- corte por confiança -------------------------------------------
        # O MediaPipe devolve 21 landmarks sempre que "acha" que viu uma mão.
        # Com score baixo esses pontos são ruído estruturado — pior que ruído
        # puro, porque passam nas checagens de forma.
        confiaveis = [m for m in brutas if m[2] >= CONFIANCA_MIN_UTIL]

        if not confiaveis:
            return self._reaproveitar(agora, brutas)

        # Ordena por confiança e fica com as duas melhores (o MediaPipe às vezes
        # entrega uma terceira mão fantasma no fundo do quadro).
        confiaveis.sort(key=lambda item: item[2], reverse=True)
        confiaveis = confiaveis[:MAX_MAOS]

        lados_presentes = {lado for _, lado, _ in confiaveis}
        self._filtros.esquecer_ausentes(lados_presentes, agora)
        self._dedos_anteriores = {
            lado: estado
            for lado, estado in self._dedos_anteriores.items()
            if lado in lados_presentes
        }

        maos: list[MaoLida] = []
        alguma_na_borda = False
        for pontos, lado, score in confiaveis:
            # --- filtro ---------------------------------------------------
            suavizados = self._filtros.filtrar(pontos, lado, agora)

            # --- classificação com histerese ------------------------------
            anteriores = self._dedos_anteriores.get(lado, DEDOS_TODOS_FECHADOS)
            dedos = classificar_dedos(suavizados, lado, anteriores)
            self._dedos_anteriores[lado] = dedos

            no_quadro = mao_dentro_do_quadro(suavizados)
            alguma_na_borda = alguma_na_borda or not no_quadro

            maos.append(
                MaoLida(
                    landmarks=suavizados,
                    lado=lado,
                    score=score,
                    dedos=dedos,
                    contagem=sum(dedos),
                    # A FORMA é classificada sobre os landmarks JÁ filtrados e
                    # sem histerese: o "L" é uma pose geométrica, e a memória
                    # que ele precisa vem da contagem de frames lá na máquina
                    # de estados, não daqui.
                    eh_l=eh_formato_L(suavizados, lado),
                    razao_pinca=medir_pinca(suavizados, lado),
                    no_quadro=no_quadro,
                )
            )

        pose = PoseMaos(
            maos=tuple(maos),
            instante=agora,
            reaproveitada=False,
            descartada_por_borda=alguma_na_borda,
            confianca_media=float(np.mean([m.score for m in maos])),
        )
        # Só poses com pelo menos uma mão inteira viram "última pose boa": a
        # mão saindo pela borda é justamente o que não queremos congelar.
        if any(m.no_quadro for m in maos):
            self._ultima_pose_boa = pose
        return pose

    @staticmethod
    def _extrair(resultado: Any) -> list[tuple[np.ndarray, str, float]]:
        """Converte a saída do MediaPipe em (landmarks, lado, score)."""
        if not resultado or not resultado.multi_hand_landmarks:
            return []
        lateralidades = resultado.multi_handedness or []
        maos: list[tuple[np.ndarray, str, float]] = []
        for indice, marcos in enumerate(resultado.multi_hand_landmarks):
            pontos = np.array(
                [(ponto.x, ponto.y) for ponto in marcos.landmark], dtype=np.float64
            )
            lado = "Right"
            score = 1.0
            if indice < len(lateralidades):
                classificacao = lateralidades[indice].classification[0]
                lado = classificacao.label
                score = float(classificacao.score)
            maos.append((pontos, lado, score))
        return maos

    def _reaproveitar(
        self, agora: float, brutas: list[tuple[np.ndarray, str, float]]
    ) -> PoseMaos:
        """Frame sem nada aproveitável: repete a última pose boa, se recente.

        Zerar aqui seria o comportamento antigo — e era ele que derrubava o modo
        luas no meio de uma seleção sempre que o rastreio piscava por um frame.
        Passada a janela, a pose vazia volta: a mão saiu de verdade.
        """
        anterior = self._ultima_pose_boa
        if anterior is not None and (agora - anterior.instante) <= JANELA_REAPROVEITAMENTO_S:
            return PoseMaos(
                maos=anterior.maos,
                instante=anterior.instante,
                reaproveitada=True,
                descartada_por_borda=anterior.descartada_por_borda,
                confianca_media=anterior.confianca_media,
            )
        self._ultima_pose_boa = None
        self._dedos_anteriores.clear()
        return PoseMaos(
            instante=agora,
            # Distingue "não vi mão nenhuma" de "vi, mas era lixo": o segundo
            # caso vira aviso de confiança baixa no HUD.
            confianca_media=(
                float(np.mean([s for _, _, s in brutas])) if brutas else 0.0
            ),
        )


__all__ = ["LeitorMaos", "MaoLida", "PoseMaos"]
