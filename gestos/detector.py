"""Captura de webcam + MediaPipe Hands em uma thread separada.

Processar vídeo no mesmo loop do render derruba o FPS: a leitura da webcam é
bloqueante (~33 ms a 30 fps) e a inferência custa mais alguns milissegundos. Aqui
a thread produz sempre a "última leitura válida" e o loop de render apenas
consulta esse estado — nunca espera por ela.
"""

from __future__ import annotations

from typing import Any

import os
import sys
import threading
import time
import warnings
from dataclasses import dataclass, field
from enum import Enum

import cv2
import numpy as np

# O MediaPipe despeja logs do TensorFlow Lite e um aviso de protobuf no console.
# Silenciados para que as mensagens de diagnóstico da webcam fiquem visíveis.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("GLOG_minloglevel", "2")
warnings.filterwarnings("ignore", message=".*SymbolDatabase.GetPrototype.*")

from config import (
    ALTURA_CAPTURA,
    ALTURA_PREVIEW_CAMERA,
    COMPLEXIDADE_MODELO,
    CONFIANCA_MIN_DETECCAO,
    CONFIANCA_MIN_RASTREIO,
    DETECTAR_A_CADA_N_FRAMES,
    FALHAS_ATE_DESCONEXAO,
    FPS_CAPTURA,
    INDICE_CAMERA,
    LARGURA_CAPTURA,
    LARGURA_PREVIEW_CAMERA,
    MAX_MAOS,
    SEGUNDOS_ENTRE_RECONEXOES,
)
from gestos.contador import contar_dedos, mao_dentro_do_quadro, medir_pinca

try:  # pragma: no cover - depende do ambiente
    import mediapipe as mp

    MEDIAPIPE_DISPONIVEL = True
    ERRO_IMPORT_MEDIAPIPE = ""
except ImportError as _erro:  # pragma: no cover
    # Inclui a falha de DLL no Windows (falta do VC++ Redistributable), que
    # também chega aqui como ImportError. A mensagem exata vai para o log.
    # Any (e não None puro) para o verificador de tipos aceitar mp.solutions:
    # o acesso é sempre protegido por MEDIAPIPE_DISPONIVEL.
    mp: Any = None
    MEDIAPIPE_DISPONIVEL = False
    ERRO_IMPORT_MEDIAPIPE = f"{type(_erro).__name__}: {_erro}"


class StatusCamera(Enum):
    """Situação atual da captura de vídeo."""

    INICIANDO = "iniciando"
    ATIVA = "ativa"
    INDISPONIVEL = "indisponivel"  # não abriu (ausente, ocupada ou sem permissão)
    DESCONECTADA = "desconectada"  # abriu e parou de entregar frames


@dataclass(frozen=True)
class LeituraGestos:
    """Instantâneo do que a thread de visão enxergou por último."""

    contagem: int | None = None  # soma das duas mãos; None = leitura inutilizável
    # Incrementa a cada INFERÊNCIA (não a cada frame): é assim que o loop de
    # render sabe se está diante de uma leitura nova ou da mesma repetida.
    sequencia: int = 0
    contagens_por_mao: tuple[int, ...] = ()
    maos_visiveis: int = 0
    confianca_media: float = 0.0
    brilho_medio: float = 1.0
    descartada_por_borda: bool = False
    # Separação polegar<->indicador em palmas, uma entrada por mão visível
    # (ordenadas por confiança). None = indicador dobrado, ou seja, não é pinça.
    # Ter as DUAS é o que permite distinguir "pinça de uma mão" (zoom) de
    # "pinça das duas mãos" (comando), que é o único gesto ainda livre.
    razoes_pinca: tuple[float | None, ...] = ()

    @property
    def razao_pinca(self) -> float | None:
        """Pinça da mão de maior confiança — a que comanda o zoom."""
        return self.razoes_pinca[0] if self.razoes_pinca else None
    preview: np.ndarray | None = field(default=None, repr=False)
    status: StatusCamera = StatusCamera.INICIANDO
    mensagem: str = ""

    @property
    def camera_ok(self) -> bool:
        """True quando a webcam está entregando imagem."""
        return self.status is StatusCamera.ATIVA


class DetectorMaos:
    """Thread produtora: webcam -> MediaPipe -> contagem de dedos."""

    def __init__(self, indice_camera: int = INDICE_CAMERA) -> None:
        self._indice_camera = indice_camera
        self._lock = threading.Lock()
        self._leitura = LeituraGestos()
        self._parar_evento = threading.Event()
        self._thread: threading.Thread | None = None
        self._captura: cv2.VideoCapture | None = None

    # ---------------------------------------------------------- ciclo de vida
    def iniciar(self) -> None:
        """Sobe a thread de captura (não bloqueia)."""
        if self._thread is not None:
            return
        if not MEDIAPIPE_DISPONIVEL:
            self._registrar(f"MediaPipe indisponível: {ERRO_IMPORT_MEDIAPIPE}")
            self._publicar(
                LeituraGestos(
                    status=StatusCamera.INDISPONIVEL,
                    mensagem="MediaPipe não disponível — use o teclado (0-8).",
                )
            )
            return
        self._thread = threading.Thread(
            target=self._laco, name="captura-gestos", daemon=True
        )
        self._thread.start()

    def parar(self) -> None:
        """Sinaliza o fim e espera a thread liberar a webcam."""
        self._parar_evento.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def ler(self) -> LeituraGestos:
        """Última leitura publicada pela thread (nunca bloqueia)."""
        with self._lock:
            return self._leitura

    # ----------------------------------------------------------------- thread
    def _publicar(self, leitura: LeituraGestos) -> None:
        """Troca o estado compartilhado sob lock."""
        with self._lock:
            self._leitura = leitura

    def _abrir_camera(self) -> cv2.VideoCapture | None:
        """Tenta abrir a webcam; devolve None se não conseguir.

        Tenta o DirectShow primeiro (no Windows abre em ~1 s, contra vários
        segundos do MSMF padrão) e cai para o backend genérico se falhar —
        algumas webcams só respondem a um dos dois.
        """
        backends = (
            [("DirectShow", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF), ("padrão", cv2.CAP_ANY)]
            if sys.platform == "win32"
            else [("padrão", cv2.CAP_ANY)]
        )
        for nome, backend in backends:
            try:
                captura = cv2.VideoCapture(self._indice_camera, backend)
            except cv2.error as erro:
                self._registrar(f"backend {nome} falhou: {erro}")
                continue
            if not captura.isOpened():
                captura.release()
                self._registrar(f"backend {nome}: não abriu o índice {self._indice_camera}")
                continue
            self._configurar_formato(captura)
            largura = int(captura.get(cv2.CAP_PROP_FRAME_WIDTH))
            altura = int(captura.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._registrar(
                f"aberta no índice {self._indice_camera} via {nome} ({largura}x{altura})"
            )
            return captura
        return None

    @staticmethod
    def _configurar_formato(captura: cv2.VideoCapture) -> None:
        """Ajusta resolução e FPS apenas quando divergem do que já está ativo.

        No DirectShow cada ``set`` renegocia o formato com o driver e custa
        ~0,5 s. Como a maioria das webcams já entrega 640x480 a 30 fps, chamar
        os três às cegas dobrava o tempo de abertura da câmera à toa.
        """
        if int(captura.get(cv2.CAP_PROP_FRAME_WIDTH)) != LARGURA_CAPTURA:
            captura.set(cv2.CAP_PROP_FRAME_WIDTH, LARGURA_CAPTURA)
        if int(captura.get(cv2.CAP_PROP_FRAME_HEIGHT)) != ALTURA_CAPTURA:
            captura.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTURA_CAPTURA)
        fps_atual = captura.get(cv2.CAP_PROP_FPS)
        # Vários drivers devolvem 0 aqui: nesse caso o valor não é confiável e
        # forçar o FPS só custaria tempo.
        if fps_atual > 0 and abs(fps_atual - FPS_CAPTURA) > 1:
            captura.set(cv2.CAP_PROP_FPS, FPS_CAPTURA)

    @staticmethod
    def _registrar(mensagem: str) -> None:
        """Log de diagnóstico no terminal (a webcam é a maior fonte de dúvida)."""
        print(f"[webcam] {mensagem}", flush=True)

    def _laco(self) -> None:
        """Laço da thread: abre, lê, detecta, publica — e sempre libera."""
        detector = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_MAOS,
            model_complexity=COMPLEXIDADE_MODELO,
            min_detection_confidence=CONFIANCA_MIN_DETECCAO,
            min_tracking_confidence=CONFIANCA_MIN_RASTREIO,
        )
        desenhista = mp.solutions.drawing_utils
        estilos = mp.solutions.drawing_styles
        conexoes = mp.solutions.hands.HAND_CONNECTIONS

        contador_frames = 0
        sequencia = 0
        falhas_seguidas = 0
        proxima_tentativa = 0.0
        ultimo_resultado = None
        ultima_leitura = LeituraGestos()

        try:
            while not self._parar_evento.is_set():
                agora = time.monotonic()

                # ------------------------------------------------ (re)conexão
                if self._captura is None:
                    if agora < proxima_tentativa:
                        time.sleep(0.05)
                        continue
                    proxima_tentativa = agora + SEGUNDOS_ENTRE_RECONEXOES
                    self._captura = self._abrir_camera()
                    if self._captura is None:
                        if ultima_leitura.status is not StatusCamera.INDISPONIVEL:
                            self._registrar(
                                "NÃO ABRIU — verifique se outro app está usando a "
                                "câmera e as permissões do sistema. Nova tentativa "
                                f"em {SEGUNDOS_ENTRE_RECONEXOES:.0f}s."
                            )
                        ultima_leitura = LeituraGestos(
                            status=StatusCamera.INDISPONIVEL,
                            mensagem=(
                                "Webcam não disponível (ausente, em uso por outro "
                                "app ou sem permissão) — use o teclado (0-8)."
                            ),
                        )
                        self._publicar(ultima_leitura)
                        continue
                    falhas_seguidas = 0

                sucesso, quadro = self._captura.read()
                if not sucesso or quadro is None:
                    falhas_seguidas += 1
                    if falhas_seguidas >= FALHAS_ATE_DESCONEXAO:
                        # Webcam arrancada no meio do uso: solta o recurso e
                        # continua tentando reconectar, sem derrubar o app.
                        self._captura.release()
                        self._captura = None
                        proxima_tentativa = agora + SEGUNDOS_ENTRE_RECONEXOES
                        ultimo_resultado = None
                        self._registrar("parou de entregar imagem — tentando reconectar")
                        ultima_leitura = LeituraGestos(
                            status=StatusCamera.DESCONECTADA,
                            mensagem="Webcam desconectada — use o teclado (0-8).",
                        )
                        self._publicar(ultima_leitura)
                    continue

                falhas_seguidas = 0
                quadro = cv2.flip(quadro, 1)  # espelha: o usuário se vê num espelho
                contador_frames += 1

                # ------------------------------------------------- inferência
                if contador_frames % DETECTAR_A_CADA_N_FRAMES == 0:
                    rgb = cv2.cvtColor(quadro, cv2.COLOR_BGR2RGB)
                    rgb.flags.writeable = False
                    ultimo_resultado = detector.process(rgb)
                    sequencia += 1
                    ultima_leitura = self._interpretar(ultimo_resultado, quadro)

                preview = self._montar_preview(
                    quadro, ultimo_resultado, desenhista, estilos, conexoes
                )
                self._publicar(
                    LeituraGestos(
                        contagem=ultima_leitura.contagem,
                        sequencia=sequencia,
                        contagens_por_mao=ultima_leitura.contagens_por_mao,
                        maos_visiveis=ultima_leitura.maos_visiveis,
                        confianca_media=ultima_leitura.confianca_media,
                        brilho_medio=ultima_leitura.brilho_medio,
                        descartada_por_borda=ultima_leitura.descartada_por_borda,
                        preview=preview,
                        status=StatusCamera.ATIVA,
                        mensagem="",
                    )
                )
        finally:
            # Libera a webcam mesmo se algo explodir no meio do laço.
            detector.close()
            if self._captura is not None:
                self._captura.release()
                self._captura = None

    # ------------------------------------------------------------ auxiliares
    def _interpretar(self, resultado, quadro: np.ndarray) -> LeituraGestos:
        """Converte a saída do MediaPipe em contagem de dedos + diagnóstico."""
        brilho = float(np.mean(quadro)) / 255.0

        if not resultado or not resultado.multi_hand_landmarks:
            # Sem mão no quadro: contagem None. O alvo confirmado é preservado
            # lá no estabilizador, não aqui.
            return LeituraGestos(
                contagem=None,
                maos_visiveis=0,
                confianca_media=0.0,
                brilho_medio=brilho,
                status=StatusCamera.ATIVA,
            )

        maos: list[tuple[np.ndarray, str, float]] = []
        lateralidades = resultado.multi_handedness or []
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

        # Três ou mais mãos no quadro: fica só com as duas de maior confiança.
        maos.sort(key=lambda item: item[2], reverse=True)
        maos = maos[:MAX_MAOS]

        confianca = float(np.mean([item[2] for item in maos]))

        contagens: list[int] = []
        for pontos, lado, _ in maos:
            if not mao_dentro_do_quadro(pontos):
                # Mão cortada pela borda: descarta o frame inteiro em vez de
                # arriscar uma contagem errada.
                return LeituraGestos(
                    contagem=None,
                    maos_visiveis=len(maos),
                    confianca_media=confianca,
                    brilho_medio=brilho,
                    descartada_por_borda=True,
                    status=StatusCamera.ATIVA,
                )
            contagens.append(contar_dedos(pontos, lado))

        # Medida em TODAS as mãos visíveis (a lista já vem ordenada por
        # confiança): a primeira comanda o zoom, e as duas juntas formam o
        # gesto de comando das luas.
        razoes_pinca = tuple(medir_pinca(pontos, lado) for pontos, lado, _ in maos)

        return LeituraGestos(
            contagem=sum(contagens),
            contagens_por_mao=tuple(contagens),
            maos_visiveis=len(maos),
            confianca_media=confianca,
            brilho_medio=brilho,
            razoes_pinca=razoes_pinca,
            status=StatusCamera.ATIVA,
        )

    def _montar_preview(
        self, quadro: np.ndarray, resultado, desenhista, estilos, conexoes
    ) -> np.ndarray:
        """Miniatura RGB da webcam com os landmarks desenhados por cima."""
        preview = cv2.resize(
            quadro,
            (LARGURA_PREVIEW_CAMERA, ALTURA_PREVIEW_CAMERA),
            interpolation=cv2.INTER_AREA,
        )
        if resultado and resultado.multi_hand_landmarks:
            # Landmarks são normalizados: desenham certo em qualquer resolução,
            # então desenhamos já na miniatura (bem mais barato).
            for marcos in resultado.multi_hand_landmarks:
                desenhista.draw_landmarks(
                    preview,
                    marcos,
                    conexoes,
                    estilos.get_default_hand_landmarks_style(),
                    estilos.get_default_hand_connections_style(),
                )
        return np.ascontiguousarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))


__all__ = ["DetectorMaos", "LeituraGestos", "StatusCamera", "MEDIAPIPE_DISPONIVEL"]
