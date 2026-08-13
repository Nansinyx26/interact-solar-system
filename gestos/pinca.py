"""Zoom por gesto de pinça: aproximar e afastar polegar e indicador.

Recebe a razão medida por ``medir_pinca`` (separação das pontas dividida pelo
tamanho da palma) e devolve o fator de zoom a aplicar no frame. A câmera não
precisa de nada novo: ``Camera2D.aplicar_zoom`` já é o mesmo caminho da roda do
mouse.

Enquanto a pinça está ativa, a leitura **não** deve alimentar o estabilizador —
a pose seria contada como 2 dedos (Vênus) e trocaria o foco no meio do zoom.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import (
    COOLDOWN_APOS_PINCA_S,
    FATOR_ZOOM_PINCA_MAX,
    LIMIAR_PINCA_ATIVA,
    LIMIAR_PINCA_SAIDA,
    SUAVIZACAO_PINCA,
)


@dataclass(frozen=True)
class EstadoPinca:
    """Resultado de uma leitura, pronto para o loop principal usar."""

    ativa: bool
    fator_zoom: float  # 1.0 = não mexer
    razao: float | None  # razão suavizada, para o HUD


class ControladorPinca:
    """Converte a distância entre polegar e indicador em zoom contínuo."""

    def __init__(self) -> None:
        self._ativa = False
        self._razao_suave: float | None = None
        self._fim_da_pinca: float = -COOLDOWN_APOS_PINCA_S

    @property
    def ativa(self) -> bool:
        """True enquanto o modo zoom estiver ligado."""
        return self._ativa

    def bloqueando_gestos(self, agora: float) -> bool:
        """True enquanto a seleção por dedos deve ficar suspensa.

        Cobre a pinça em si e o rabicho depois dela: ao abrir a mão o gesto
        passa por 1, 2 e 3 dedos, que sem esta pausa trocariam de planeta.
        """
        return self._ativa or (agora - self._fim_da_pinca) < COOLDOWN_APOS_PINCA_S

    def reiniciar(self) -> None:
        """Esquece o estado (câmera desligada, mão sumiu do quadro)."""
        self._ativa = False
        self._razao_suave = None

    def atualizar(self, razao: float | None, agora: float) -> EstadoPinca:
        """Processa uma leitura e devolve o fator de zoom do frame."""
        if razao is None:
            # Sem indicador estendido não há pinça: encerra o modo zoom.
            if self._ativa:
                self._ativa = False
                self._fim_da_pinca = agora
            self._razao_suave = None
            return EstadoPinca(ativa=False, fator_zoom=1.0, razao=None)

        anterior = self._razao_suave
        # Média móvel exponencial: o tremor da mão é muito maior que o do mouse
        # e sem filtro o zoom vibra a cada frame.
        self._razao_suave = (
            razao
            if anterior is None
            else anterior + (razao - anterior) * SUAVIZACAO_PINCA
        )
        suave = self._razao_suave

        # Histerese: entra fechado, só sai bem aberto. Com limiar único a pinça
        # piscaria na fronteira e o zoom entraria e sairia sozinho.
        if not self._ativa and suave < LIMIAR_PINCA_ATIVA:
            self._ativa = True
            return EstadoPinca(ativa=True, fator_zoom=1.0, razao=suave)
        if self._ativa and suave > LIMIAR_PINCA_SAIDA:
            self._ativa = False
            self._fim_da_pinca = agora
            return EstadoPinca(ativa=False, fator_zoom=1.0, razao=suave)

        if not self._ativa or anterior is None or anterior <= 0.0:
            return EstadoPinca(ativa=self._ativa, fator_zoom=1.0, razao=suave)

        # Fator RELATIVO ao frame anterior. Aplicar razao_atual/razao_inicial a
        # cada frame faria o zoom crescer exponencialmente; o incremental
        # acumula exatamente a mesma proporção total, sem explodir.
        fator = suave / anterior
        fator = min(FATOR_ZOOM_PINCA_MAX, max(1.0 / FATOR_ZOOM_PINCA_MAX, fator))
        return EstadoPinca(ativa=True, fator_zoom=fator, razao=suave)
