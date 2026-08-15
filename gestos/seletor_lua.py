"""Máquina de estados da seleção de luas por gesto de duas mãos.

O fluxo tem quatro estados, e cada transição é comandada por um gesto:

    OCIOSO ──(gesto seleciona planeta)──► PLANETA_SELECIONADO
                                              │
                        (mão A faz "L")       │
                                              ▼
                                         PREVIEW_LUA ◄──┐
                                              │         │ (mão B troca o número)
                        (mesmo número por N   │         │
                         leituras seguidas)   ▼         │
                                         FICHA_LUA ─────┘
                                              │
                        (soltar o L, ou ESC)  │
                                              ▼
                                    PLANETA_SELECIONADO

A separação entre PREVIEW e FICHA é o ponto do módulo. Antes, o número da mão B
abria a lua direto: passar de 2 para 5 dedos atravessava o 3 e o 4, e cada um
abria uma ficha no caminho. Com o preview o usuário "passeia" pelos números
livremente — só o número que ele SEGURA vira ficha.

O módulo não conhece pygame nem o renderizador. Ele recebe o planeta em
contexto e a intenção lida dos gestos, e devolve o que deve estar na tela,
incluindo a mensagem de HUD para cada caso de borda. Manter as mensagens aqui
(e não no ``main``) é o que garante que teclado e gesto digam a mesma coisa.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from config import (
    COOLDOWN_SELECAO_LUA_S,
    FALHAS_TOLERADAS_CONFIRMACAO,
    FRAMES_PARA_ABRIR_FICHA_LUA,
)
from dados.luas import LuaMenor
from dados.planetas import CorpoCeleste, luas_do_planeta


class EstadoSelecao(Enum):
    """Onde o usuário está no fluxo de seleção."""

    OCIOSO = "ocioso"                        # nada em foco
    PLANETA_SELECIONADO = "planeta"          # planeta em foco, sem modo lua
    PREVIEW_LUA = "preview"                  # "L" ativo, lua destacada
    FICHA_LUA = "ficha"                      # ficha aberta


@dataclass(frozen=True)
class ResultadoSelecao:
    """O que deve estar na tela depois desta leitura."""

    estado: EstadoSelecao
    planeta: CorpoCeleste | None
    # Lua em destaque na órbita. Vale tanto no PREVIEW quanto na FICHA — a
    # diferença entre os dois é a ficha estar aberta, não o destaque.
    lua: LuaMenor | None
    indice: int | None  # número mostrado pela mão B (1..N), None se inválido
    progresso: float  # 0 a 1: quanto falta para a ficha abrir
    aviso: str  # mensagem de HUD; "" quando não há nada a dizer
    # Eventos deste frame (não estado): disparam narração e telemetria uma vez.
    ficha_abriu: bool = False
    ficha_fechou: bool = False


class SeletorLua:
    """Traduz "L + número" em preview e ficha, com confirmação por permanência."""

    def __init__(self) -> None:
        self._estado = EstadoSelecao.OCIOSO
        self._planeta: CorpoCeleste | None = None
        self._lua: LuaMenor | None = None
        self._indice_preview: int | None = None
        # Contagem de permanência do número atual. Sobe a cada leitura que
        # concorda e desce (sem zerar) a cada leitura que discorda — ver
        # FALHAS_TOLERADAS_CONFIRMACAO.
        self._permanencia: int = 0
        self._falhas: int = 0
        self._instante_ultima_ficha: float = -COOLDOWN_SELECAO_LUA_S

    # ------------------------------------------------------------ consultas
    @property
    def estado(self) -> EstadoSelecao:
        """Estado corrente da máquina."""
        return self._estado

    @property
    def lua(self) -> LuaMenor | None:
        """Lua em destaque (preview ou ficha aberta)."""
        return self._lua

    @property
    def indice_preview(self) -> int | None:
        """Número da lua em preview (1..N), ou None quando não há destaque."""
        return self._indice_preview

    @property
    def ficha_aberta(self) -> bool:
        """True quando a ficha da lua está na tela."""
        return self._estado is EstadoSelecao.FICHA_LUA

    @property
    def progresso(self) -> float:
        """0 a 1 da barra de confirmação (0 quando não há o que confirmar)."""
        if self._estado is not EstadoSelecao.PREVIEW_LUA:
            return 0.0
        return min(1.0, self._permanencia / FRAMES_PARA_ABRIR_FICHA_LUA)

    # ------------------------------------------------------------ comandos
    def definir_planeta(self, planeta: CorpoCeleste | None) -> None:
        """Registra o planeta em contexto (veio de um gesto ou de uma tecla).

        Trocar de planeta desfaz a lua: os números passam a significar outra
        lista, e manter a lua antiga em destaque diria que ela pertence ao
        planeta novo.
        """
        if planeta is self._planeta:
            return
        self._planeta = planeta
        self._lua = None
        self._indice_preview = None
        self._permanencia = 0
        self._falhas = 0
        self._estado = (
            EstadoSelecao.PLANETA_SELECIONADO if planeta else EstadoSelecao.OCIOSO
        )

    def fechar_ficha(self) -> bool:
        """Fecha a ficha e volta ao planeta (tecla ESC). True se havia algo aberto."""
        if self._estado is not EstadoSelecao.FICHA_LUA:
            return False
        self._estado = EstadoSelecao.PLANETA_SELECIONADO
        self._lua = None
        self._indice_preview = None
        self._permanencia = 0
        self._falhas = 0
        return True

    def reiniciar(self) -> None:
        """Volta ao início (visão geral / gesto 10)."""
        self._estado = EstadoSelecao.OCIOSO
        self._planeta = None
        self._lua = None
        self._indice_preview = None
        self._permanencia = 0
        self._falhas = 0

    # -------------------------------------------------------------- núcleo
    def atualizar(
        self,
        modo_lua_ativo: bool,
        numero: int | None,
        maos_visiveis: int,
        agora: float,
    ) -> ResultadoSelecao:
        """Avança a máquina uma leitura.

        ``modo_lua_ativo`` é o "L" já confirmado pela histerese da
        ``MaquinaGestos`` — este módulo não classifica forma de mão, só
        consome a decisão. ``numero`` é o que a mão B mostra (0 a 5), e
        ``maos_visiveis`` existe só para distinguir "não mostrou número" de
        "não tem a outra mão na tela", que são avisos diferentes.
        """
        # --- soltar o "L" fecha a ficha e volta ao planeta -----------------
        if not modo_lua_ativo:
            fechou = self._estado in (
                EstadoSelecao.PREVIEW_LUA,
                EstadoSelecao.FICHA_LUA,
            )
            if fechou:
                self._estado = (
                    EstadoSelecao.PLANETA_SELECIONADO
                    if self._planeta
                    else EstadoSelecao.OCIOSO
                )
                self._lua = None
                self._indice_preview = None
                self._permanencia = 0
                self._falhas = 0
            return self._resultado(aviso="", ficha_fechou=fechou)

        # --- casos de borda que impedem qualquer seleção -------------------
        if self._planeta is None:
            return self._resultado(aviso="Escolha um planeta primeiro.")

        luas = luas_do_planeta(self._planeta.nome)
        if not luas:
            # Mercúrio e Vênus. O modo continua ativo (o "L" está lá), só não
            # há o que selecionar — travar aqui seria pior que avisar.
            return self._resultado(
                aviso=f"{self._planeta.nome} não tem luas cadastradas."
            )

        # Só a mão do "L" na tela: o modo está ligado, falta o número.
        if maos_visiveis < 2 or numero is None:
            self._permanencia = 0
            self._falhas = 0
            return self._resultado(aviso="Mostre a outra mão com o número da lua.")

        if numero == 0:
            # Zero é "mostrar todas": desfaz o destaque sem sair do modo.
            self._indice_preview = None
            self._lua = None
            self._permanencia = 0
            self._estado = EstadoSelecao.PREVIEW_LUA
            plural = "luas" if len(luas) > 1 else "lua"
            return self._resultado(
                aviso=f"{self._planeta.nome}: todas as {len(luas)} {plural}."
            )

        if numero > len(luas):
            # Número maior que o catálogo. Não troca nada — só explica, com o
            # número REAL, para o usuário não ficar tentando o 5 em Marte.
            self._permanencia = 0
            plural = "luas cadastradas" if len(luas) > 1 else "lua cadastrada"
            return self._resultado(
                aviso=f"{self._planeta.nome} tem só {len(luas)} {plural}."
            )

        # --- preview + contagem de permanência -----------------------------
        if numero != self._indice_preview:
            # A tolerância protege uma confirmação EM ANDAMENTO. Com a ficha já
            # aberta não há o que proteger, e absorver as leituras discordantes
            # ali só atrasaria a troca deliberada de lua — o usuário mostra
            # outro número e a tela demoraria a responder.
            em_confirmacao = self._estado is EstadoSelecao.PREVIEW_LUA
            if (
                em_confirmacao
                and self._falhas < FALHAS_TOLERADAS_CONFIRMACAO
                and self._permanencia > 0
            ):
                # Uma leitura discordante no meio da contagem é quase sempre uma
                # piscada do rastreio, não uma mudança de ideia: desconta em vez
                # de zerar, senão a confirmação nunca chega ao fim.
                self._falhas += 1
                self._permanencia = max(0, self._permanencia - 1)
                return self._resultado(aviso="")
            # Mudança de ideia mesmo: novo preview, contagem recomeça.
            #
            # Começa em 1, não em 0: esta leitura JÁ é a primeira em que o
            # número aparece, e descontá-la faria a ficha exigir N+1 leituras.
            self._indice_preview = numero
            self._lua = luas[numero - 1]
            self._permanencia = 1
            self._falhas = 0
            # Trocar de número com a ficha aberta volta ao PREVIEW: a ficha
            # nova só aparece quando o novo número for confirmado.
            self._estado = EstadoSelecao.PREVIEW_LUA
            return self._resultado(aviso="")

        # Número estável.
        self._falhas = 0
        self._lua = luas[numero - 1]

        if self._estado is EstadoSelecao.FICHA_LUA:
            # Já aberta e o usuário segue mostrando o mesmo número: nada muda.
            return self._resultado(aviso="")

        self._estado = EstadoSelecao.PREVIEW_LUA
        self._permanencia += 1

        if self._permanencia < FRAMES_PARA_ABRIR_FICHA_LUA:
            return self._resultado(aviso="")

        # --- confirmação: abre a ficha -------------------------------------
        if agora - self._instante_ultima_ficha < COOLDOWN_SELECAO_LUA_S:
            # Cooldown: acabou de fechar uma ficha e o mesmo gesto abriria outra
            # no frame seguinte. Segura o progresso cheio até liberar.
            return self._resultado(aviso="")

        self._instante_ultima_ficha = agora
        self._estado = EstadoSelecao.FICHA_LUA
        return self._resultado(aviso="", ficha_abriu=True)

    # ------------------------------------------------------------ interno
    def _resultado(
        self, aviso: str, ficha_abriu: bool = False, ficha_fechou: bool = False
    ) -> ResultadoSelecao:
        """Empacota o estado corrente no formato que o loop principal consome."""
        return ResultadoSelecao(
            estado=self._estado,
            planeta=self._planeta,
            lua=self._lua,
            indice=self._indice_preview,
            progresso=self.progresso,
            aviso=aviso,
            ficha_abriu=ficha_abriu,
            ficha_fechou=ficha_fechou,
        )


__all__ = ["EstadoSelecao", "ResultadoSelecao", "SeletorLua"]
