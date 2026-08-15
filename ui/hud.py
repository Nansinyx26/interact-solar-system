"""HUD: indicadores de gesto, legenda, avisos e preview da webcam.

Organização dos blocos na janela::

    ┌──────────────────────────────────────────────────────────────┐
    │ status (fps, tempo, câmera)              avisos centralizados│
    │                                                              │
    │                                              ficha do corpo  │
    │                                                              │
    │                                          preview da webcam   │
    │ painel de gesto   legenda dedos → corpo                      │
    │ barra de atalhos                                             │
    └──────────────────────────────────────────────────────────────┘

Em janelas baixas a legenda some (a informação continua na barra de atalhos) e
em janelas estreitas a barra de atalhos encurta — nada nunca é desenhado por
cima da cena sem caber.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pygame

from config import (
    ALPHA_LINHA_LEGENDA_ATIVA,
    ALPHA_PAINEL,
    ALTURA_BARRA_ATALHOS,
    ALTURA_JANELA,
    ALTURA_MINIMA_LEGENDA,
    ALTURA_PREVIEW_CAMERA,
    COR_AVISO,
    COR_DESTAQUE,
    COR_ERRO,
    COR_PAINEL,
    COR_SUCESSO,
    COR_TRILHO_BARRA,
    COR_TEXTO,
    COR_TEXTO_SECUNDARIO,
    ESPESSURA_ANEL_PROGRESSO,
    FAMILIA_FONTE,
    FAMILIA_FONTE_MONO,
    GESTO_MINIMO_DUAS_MAOS,
    GESTO_VISAO_GERAL,
    LARGURA_JANELA,
    LARGURA_MINIMA_ATALHOS,
    LARGURA_PREVIEW_CAMERA,
    LIMIAR_AVISO_CONFIANCA,
    LIMIAR_BRILHO_BAIXO,
    MARGEM_HUD,
    RAIO_ANEL_PROGRESSO,
    RAIO_PONTO_LEGENDA,
    TAM_FONTE_GRANDE,
    TAM_FONTE_MEDIA,
    TAM_FONTE_MINI,
    TAM_FONTE_PEQUENA,
    TAM_FONTE_TITULO,
)
from dados.planetas import CORPOS, CorpoCeleste, luas_do_planeta
from gestos.detector import LeituraGestos, StatusCamera
from gestos.estabilizador import ResultadoEstabilizacao

# Painel de gesto (canto inferior esquerdo).
_LARGURA_PAINEL_GESTO = 232
_ALTURA_PAINEL_GESTO = 142

# Legenda dedos -> corpo, ao lado do painel de gesto.
_LARGURA_PAINEL_LEGENDA = 316
_ALTURA_LINHA_LEGENDA = 20
_PADDING_LEGENDA = 12

# Painel de status (canto superior esquerdo).
_LARGURA_PAINEL_STATUS = 232
_ALTURA_PAINEL_STATUS = 78

# Painel do modo luas (topo, centralizado). Fica na faixa central porque é o
# único bloco que aparece e some durante o uso: nos cantos ele seria confundido
# com o HUD fixo, e no meio ele avisa que o significado dos números mudou.
_LARGURA_PAINEL_LUAS = 280
_ALTURA_LINHA_LUA = 19
_PADDING_LUAS = 12
# Acima disso a lista é truncada com "+N": Júpiter e Saturno têm 5 luas cada,
# mas a lista é gerada do catálogo e ele pode crescer sem quebrar o layout.
_MAXIMO_LUAS_LISTADAS = 6

_MAXIMO_DEDOS_UMA_MAO = GESTO_MINIMO_DUAS_MAOS - 1

# Painel de debug (tecla F3), ancorado no rodapé central. Fica ali porque é a
# única faixa que nenhum bloco fixo ocupa: os cantos são do HUD normal e o topo
# central é do modo lua — justamente o que este painel serve para diagnosticar.
_LARGURA_PAINEL_DEBUG = 360
_PADDING_DEBUG = 12
_ALTURA_LINHA_DEBUG = 17


def topo_do_painel_gesto(altura_janela: int) -> int:
    """Y onde começa o painel de gesto, ancorado na base da coluna esquerda.

    A ficha do corpo focado divide essa coluna com ele e precisa parar aqui —
    por isso o valor é exposto em vez de recalculado em outro módulo.
    """
    return altura_janela - MARGEM_HUD - _ALTURA_PAINEL_GESTO - ALTURA_BARRA_ATALHOS


def base_do_painel_status() -> int:
    """Y logo abaixo do painel de status, onde a ficha pode começar."""
    return MARGEM_HUD + _ALTURA_PAINEL_STATUS + MARGEM_HUD

# Altura total do bloco do preview (imagem + rodapé com a legenda da tecla C).
# A ficha do planeta usa isto para não invadir o espaço da webcam.
ALTURA_BLOCO_PREVIEW = ALTURA_PREVIEW_CAMERA + 22

# Texto da barra de atalhos, em duas versões: a janela estreita perde a cauda
# sobre o mouse, que é a parte descobrível sem ajuda.
_ATALHOS_COMPLETOS = (
    "0–9 focar   clique seleciona   L modo lua   V visão geral   A Quiz   R Ranking   ESPAÇO pausa   +/− tempo   "
    "C câmera   N voz   F3 debug   Q sair   ·   arraste com o mouse, roda = zoom"
)
_ATALHOS_CURTOS = (
    "0–9 focar   L modo lua   V visão geral   A Quiz   ESPAÇO pausa   +/− tempo   C câmera   N voz   F3 debug   Q sair"
)

# Rótulo do gesto de comando na legenda.
_ROTULO_VISAO_GERAL = "visão geral  (tecla V)"


@dataclass(frozen=True)
class Fontes:
    """Conjunto de fontes usado por toda a interface."""

    titulo: pygame.font.Font
    grande: pygame.font.Font
    media: pygame.font.Font
    pequena: pygame.font.Font
    mini: pygame.font.Font
    mono: pygame.font.Font

    @staticmethod
    def carregar() -> "Fontes":
        """Carrega fontes do sistema (sem arquivos externos no projeto)."""
        return Fontes(
            titulo=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_TITULO, bold=True),
            grande=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_GRANDE, bold=True),
            media=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_MEDIA),
            pequena=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_PEQUENA),
            mini=pygame.font.SysFont(FAMILIA_FONTE, TAM_FONTE_MINI),
            mono=pygame.font.SysFont(FAMILIA_FONTE_MONO, TAM_FONTE_PEQUENA),
        )


@dataclass(frozen=True)
class EstadoHUD:
    """Tudo que o HUD precisa saber para desenhar um frame."""

    fps: float
    leitura: LeituraGestos
    resultado: ResultadoEstabilizacao
    corpo_alvo: CorpoCeleste | None
    mostrar_preview: bool
    pausado: bool
    escala_tempo: float
    valor_confirmado: int | None = None  # inclui o gesto de comando (10)
    pinca_ativa: bool = False  # modo zoom pela câmera
    narracao_ativa: bool = False
    # --- modo luas (gesto "L") ---
    modo_luas: bool = False
    l_detectado: bool = False  # há um "L" na tela, mesmo antes de confirmar
    progresso_modo: float = 0.0  # 0 a 1: quanto falta para o modo trocar
    planeta_luas: CorpoCeleste | None = None  # de quem as luas estão listadas
    lua_selecionada: str | None = None
    # Número mostrado pela mão B (1..N). Em PREVIEW ele já destaca a lua, mas a
    # ficha ainda não abriu — é o que a barra de confirmação está medindo.
    indice_lua: int | None = None
    progresso_lua: float = 0.0  # 0 a 1: quanto falta para a FICHA abrir
    ficha_lua_aberta: bool = False
    aviso_lua: str = ""  # mensagem vinda do SeletorLua (casos de borda)
    # --- HUD de debug (tecla F3) ---
    debug_visivel: bool = False
    estado_selecao: str = ""  # nome do estado da máquina, para diagnóstico


def desenhar_painel(
    superficie: pygame.Surface, retangulo: pygame.Rect, alpha: int = ALPHA_PAINEL
) -> None:
    """Fundo translúcido arredondado, base de todos os blocos do HUD."""
    camada = pygame.Surface(retangulo.size, pygame.SRCALPHA)
    pygame.draw.rect(
        camada, (*COR_PAINEL, alpha), camada.get_rect(), border_radius=10
    )
    pygame.draw.rect(
        camada, (255, 255, 255, 26), camada.get_rect(), width=1, border_radius=10
    )
    superficie.blit(camada, retangulo.topleft)


def _desenhar_arco_grosso(
    superficie: pygame.Surface,
    centro: tuple[int, int],
    raio: int,
    fracao: float,
    cor: tuple[int, int, int],
    alpha: int = 255,
) -> None:
    """Arco de progresso — ``pygame.draw.arc`` grosso sai serrilhado, então
    empilhamos arcos de 1 px."""
    if fracao <= 0.0:
        return
    inicio = math.pi / 2
    fim = inicio + 2 * math.pi * min(1.0, fracao)
    camada = pygame.Surface((raio * 2 + 4, raio * 2 + 4), pygame.SRCALPHA)
    for passo in range(ESPESSURA_ANEL_PROGRESSO):
        atual = raio - passo
        caixa = pygame.Rect(
            raio + 2 - atual, raio + 2 - atual, atual * 2, atual * 2
        )
        pygame.draw.arc(camada, (*cor, alpha), caixa, inicio, fim, 2)
    superficie.blit(camada, (centro[0] - raio - 2, centro[1] - raio - 2))


def _desenhar_ponto(
    superficie: pygame.Surface, centro: tuple[int, int], cor: tuple[int, int, int]
) -> None:
    """Bolinha da cor do corpo, usada como marcador na legenda."""
    pygame.draw.circle(superficie, cor, centro, RAIO_PONTO_LEGENDA)
    pygame.draw.circle(
        superficie, (255, 255, 255), centro, RAIO_PONTO_LEGENDA, width=1
    )


class HUD:
    """Desenha overlays sobre a cena já renderizada."""

    def __init__(
        self,
        fontes: Fontes,
        largura: int = LARGURA_JANELA,
        altura: int = ALTURA_JANELA,
    ) -> None:
        self._fontes = fontes
        self._largura = largura
        self._altura = altura
        self._superficie_preview: pygame.Surface | None = None
        # Legenda pré-montada: (dedos, nome, cor do ponto, cor do texto). Só o
        # realce da linha ativa muda entre frames.
        self._legenda: list[tuple[int, str, tuple[int, int, int], tuple[int, int, int]]] = [
            (corpo.indice_gesto, corpo.nome, corpo.cor_base, COR_TEXTO)
            for corpo in CORPOS
        ]
        self._legenda.append(
            (GESTO_VISAO_GERAL, _ROTULO_VISAO_GERAL, COR_DESTAQUE, COR_DESTAQUE)
        )
        self._altura_legenda = (
            _ALTURA_LINHA_LEGENDA * len(self._legenda) + _PADDING_LEGENDA * 2 + 44
        )

    def redimensionar(self, largura: int, altura: int) -> None:
        """Reposiciona os blocos para o novo tamanho da janela."""
        self._largura = largura
        self._altura = altura

    # ------------------------------------------------------------- principal
    def desenhar(self, superficie: pygame.Surface, estado: EstadoHUD) -> None:
        """Desenha o HUD completo."""
        self._desenhar_status(superficie, estado)
        self._desenhar_painel_gesto(superficie, estado)
        # A ficha do corpo focado ocupa a mesma coluna esquerda da legenda: com
        # um corpo em foco valem os dados; sem foco, vale a tabela de dedos.
        if estado.corpo_alvo is None and self._altura >= ALTURA_MINIMA_LEGENDA:
            self._desenhar_legenda(superficie, estado)
        self._desenhar_barra_atalhos(superficie)
        # Antes dos avisos: o painel é o contexto que explica o aviso, e os dois
        # disputam a mesma faixa central do topo — por isso o painel devolve
        # onde termina, e os avisos começam abaixo dele.
        topo_avisos = MARGEM_HUD
        if estado.modo_luas or estado.l_detectado:
            topo_avisos = self._desenhar_painel_luas(superficie, estado) + 8
        self._desenhar_avisos(superficie, estado, topo_avisos)
        if estado.mostrar_preview:
            self._desenhar_preview(superficie, estado.leitura)
        # Por último: o debug é uma sobreposição de diagnóstico e precisa ficar
        # acima de tudo, inclusive do preview da webcam.
        if estado.debug_visivel:
            self._desenhar_debug(superficie, estado)

    # --------------------------------------------------------------- blocos
    def _estado_camera(self, leitura: LeituraGestos) -> tuple[str, tuple[int, int, int]]:
        """Texto curto + cor do indicador de câmera do painel de status."""
        if leitura.status is StatusCamera.ATIVA:
            if leitura.maos_visiveis:
                return f"câmera · {leitura.maos_visiveis} mão(s)", COR_SUCESSO
            return "câmera · sem mãos", COR_SUCESSO
        if leitura.status is StatusCamera.INICIANDO:
            return "abrindo câmera...", COR_AVISO
        if leitura.status is StatusCamera.DESCONECTADA:
            return "câmera desconectada", COR_ERRO
        return "sem câmera · use o teclado", COR_ERRO

    def _desenhar_status(self, superficie: pygame.Surface, estado: EstadoHUD) -> None:
        """Canto superior esquerdo: FPS, velocidade do tempo e estado da câmera."""
        retangulo = pygame.Rect(
            MARGEM_HUD, MARGEM_HUD, _LARGURA_PAINEL_STATUS, _ALTURA_PAINEL_STATUS
        )
        desenhar_painel(superficie, retangulo)

        x = retangulo.x + 14
        superficie.blit(
            self._fontes.mini.render("SISTEMA SOLAR", True, COR_TEXTO_SECUNDARIO),
            (x, retangulo.y + 10),
        )

        # Linha do relógio: FPS em destaque, velocidade do tempo ao lado. A
        # fonte mono impede que os números "dancem" a cada frame.
        texto_fps = self._fontes.mono.render(f"{estado.fps:5.1f} FPS", True, COR_TEXTO)
        superficie.blit(texto_fps, (x, retangulo.y + 28))
        cor_tempo = COR_AVISO if estado.pausado else COR_TEXTO_SECUNDARIO
        rotulo_tempo = "PAUSADO" if estado.pausado else f"×{estado.escala_tempo:.1f}"
        superficie.blit(
            self._fontes.mono.render(rotulo_tempo, True, cor_tempo),
            (x + texto_fps.get_width() + 12, retangulo.y + 28),
        )

        # Pastilha da câmera: um ponto colorido diz o estado antes de qualquer
        # leitura de texto.
        rotulo_camera, cor_camera = self._estado_camera(estado.leitura)
        pygame.draw.circle(superficie, cor_camera, (x + 4, retangulo.y + 56), 4)
        superficie.blit(
            self._fontes.mini.render(rotulo_camera, True, cor_camera),
            (x + 15, retangulo.y + 49),
        )

    def _desenhar_painel_gesto(
        self, superficie: pygame.Surface, estado: EstadoHUD
    ) -> None:
        """Número detectado (com anel de progresso) e número confirmado."""
        topo = topo_do_painel_gesto(self._altura)
        retangulo = pygame.Rect(
            MARGEM_HUD, topo, _LARGURA_PAINEL_GESTO, _ALTURA_PAINEL_GESTO
        )
        desenhar_painel(superficie, retangulo)

        leitura = estado.leitura
        resultado = estado.resultado

        centro_anel = (retangulo.x + 62, retangulo.y + 64)
        # Trilho do anel.
        pygame.draw.circle(
            superficie, (52, 60, 84), centro_anel, RAIO_ANEL_PROGRESSO, width=3
        )
        cor_anel = COR_AVISO if resultado.em_cooldown else COR_DESTAQUE
        _desenhar_arco_grosso(
            superficie, centro_anel, RAIO_ANEL_PROGRESSO, resultado.progresso, cor_anel
        )

        detectado = "—" if leitura.contagem is None else str(leitura.contagem)
        cor_numero = COR_TEXTO if leitura.contagem is not None else COR_TEXTO_SECUNDARIO
        texto = self._fontes.titulo.render(detectado, True, cor_numero)
        superficie.blit(texto, texto.get_rect(center=centro_anel))

        # O rótulo abaixo do anel vira instrução enquanto o gesto está sendo
        # confirmado: é o único momento em que o usuário precisa *não* mexer.
        if resultado.em_cooldown:
            rodape, cor_rodape = "AGUARDE", COR_AVISO
        elif resultado.progresso > 0.0 and resultado.candidato is not None:
            rodape, cor_rodape = "SEGURE...", COR_DESTAQUE
        else:
            rodape, cor_rodape = "DETECTADO", COR_TEXTO_SECUNDARIO
        largura_rodape = self._fontes.mini.size(rodape)[0]
        superficie.blit(
            self._fontes.mini.render(rodape, True, cor_rodape),
            (centro_anel[0] - largura_rodape // 2, retangulo.bottom - 26),
        )

        # Coluna direita: valor já confirmado e alvo correspondente.
        coluna_x = retangulo.x + 126
        superficie.blit(
            self._fontes.mini.render("CONFIRMADO", True, COR_TEXTO_SECUNDARIO),
            (coluna_x, retangulo.y + 16),
        )
        confirmado = estado.valor_confirmado
        if confirmado is None and estado.corpo_alvo is not None:
            confirmado = estado.corpo_alvo.indice_gesto
        superficie.blit(
            self._fontes.grande.render(
                "—" if confirmado is None else str(confirmado), True, COR_DESTAQUE
            ),
            (coluna_x, retangulo.y + 32),
        )
        # O alvo é o que o usuário realmente quer ler: recebe a cor do corpo.
        if estado.corpo_alvo is not None:
            nome_alvo = estado.corpo_alvo.nome
            cor_alvo = estado.corpo_alvo.cor_base
            _desenhar_ponto(superficie, (coluna_x + 4, retangulo.y + 86), cor_alvo)
            deslocamento_nome = 14
        else:
            nome_alvo = "visão geral"
            deslocamento_nome = 0
        superficie.blit(
            self._fontes.pequena.render(nome_alvo, True, COR_TEXTO),
            (coluna_x + deslocamento_nome, retangulo.y + 78),
        )
        # Detalhe por mão: com 6-9 é o que revela se a segunda mão foi perdida
        # ("1 mão: 5") ou se uma delas está contando errado ("2 mãos: 5+0").
        if leitura.contagens_por_mao:
            detalhe = "+".join(str(valor) for valor in leitura.contagens_por_mao)
            maos = f"{leitura.maos_visiveis} mão(s): {detalhe}"
        else:
            maos = f"{leitura.maos_visiveis} mão(s)"
        superficie.blit(
            self._fontes.mini.render(maos, True, COR_TEXTO_SECUNDARIO),
            (coluna_x, retangulo.y + 106),
        )

    def _desenhar_legenda(
        self, superficie: pygame.Surface, estado: EstadoHUD
    ) -> None:
        """Tabela gesto -> corpo celeste, com a linha do corpo em foco realçada."""
        retangulo = pygame.Rect(
            MARGEM_HUD + _LARGURA_PAINEL_GESTO + 12,
            self._altura - MARGEM_HUD - self._altura_legenda - ALTURA_BARRA_ATALHOS,
            _LARGURA_PAINEL_LEGENDA,
            self._altura_legenda,
        )
        desenhar_painel(superficie, retangulo)
        superficie.blit(
            self._fontes.mini.render("DEDOS → CORPO CELESTE", True, COR_TEXTO_SECUNDARIO),
            (retangulo.x + 14, retangulo.y + 10),
        )

        # Qual linha está ativa: o corpo em foco ou, sem foco, o comando 10.
        ativo = (
            estado.corpo_alvo.indice_gesto
            if estado.corpo_alvo is not None
            else GESTO_VISAO_GERAL
        )

        y = retangulo.y + 30
        for dedos, nome, cor_ponto, cor_texto in self._legenda:
            if dedos == ativo:
                realce = pygame.Surface(
                    (retangulo.width - 2 * _PADDING_LEGENDA, _ALTURA_LINHA_LEGENDA),
                    pygame.SRCALPHA,
                )
                pygame.draw.rect(
                    realce,
                    (*COR_DESTAQUE, ALPHA_LINHA_LEGENDA_ATIVA),
                    realce.get_rect(),
                    border_radius=5,
                )
                superficie.blit(realce, (retangulo.x + _PADDING_LEGENDA, y - 2))
            _desenhar_ponto(superficie, (retangulo.x + 22, y + 8), cor_ponto)
            superficie.blit(
                self._fontes.mono.render(str(dedos), True, COR_DESTAQUE),
                (retangulo.x + 34, y),
            )
            superficie.blit(
                self._fontes.pequena.render(nome, True, cor_texto),
                (retangulo.x + 62, y),
            )
            y += _ALTURA_LINHA_LEGENDA

        superficie.blit(
            self._fontes.mini.render(
                f"{GESTO_MINIMO_DUAS_MAOS}–{GESTO_VISAO_GERAL} exigem as duas mãos "
                f"(ex.: 5+4 = Lua)",
                True,
                COR_TEXTO_SECUNDARIO,
            ),
            (retangulo.x + 22, retangulo.bottom - 24),
        )

    def _desenhar_barra_atalhos(self, superficie: pygame.Surface) -> None:
        """Linha de atalhos rente à base — encurta em janelas estreitas."""
        atalhos = (
            _ATALHOS_COMPLETOS
            if self._largura >= LARGURA_MINIMA_ATALHOS
            else _ATALHOS_CURTOS
        )
        superficie.blit(
            self._fontes.mini.render(atalhos, True, COR_TEXTO_SECUNDARIO),
            (MARGEM_HUD + 4, self._altura - MARGEM_HUD - 14),
        )

    def _desenhar_painel_luas(
        self, superficie: pygame.Surface, estado: EstadoHUD
    ) -> int:
        """Painel do modo luas: crachá, planeta, lista numerada e confirmação.

        A lista sai de ``luas_do_planeta()`` — a MESMA função que o renderizador
        usa para desenhar. Com um dicionário próprio aqui, o HUD poderia numerar
        uma lua que não existe na cena, e o usuário mostraria o número para nada.
        """
        planeta = estado.planeta_luas
        luas = luas_do_planeta(planeta.nome) if planeta else ()
        visiveis = luas[:_MAXIMO_LUAS_LISTADAS]
        restantes = len(luas) - len(visiveis)

        linhas = len(visiveis) + (1 if restantes > 0 else 0)
        altura = _PADDING_LUAS * 2 + 40 + max(1, linhas) * _ALTURA_LINHA_LUA
        if estado.progresso_modo > 0.0 and not estado.modo_luas:
            altura += 10
        retangulo = pygame.Rect(
            (self._largura - _LARGURA_PAINEL_LUAS) // 2,
            MARGEM_HUD,
            _LARGURA_PAINEL_LUAS,
            altura,
        )
        desenhar_painel(superficie, retangulo)

        x = retangulo.x + _PADDING_LUAS
        y = retangulo.y + _PADDING_LUAS

        # Crachá: aceso quando o modo está ativo, apagado enquanto confirma.
        cor_cracha = COR_DESTAQUE if estado.modo_luas else COR_TEXTO_SECUNDARIO
        icone = self._fontes.media.render("L", True, cor_cracha)
        moldura = pygame.Rect(x, y, 22, 22)
        pygame.draw.rect(superficie, cor_cracha, moldura, width=2, border_radius=5)
        superficie.blit(icone, icone.get_rect(center=moldura.center))

        if estado.ficha_lua_aberta:
            rotulo = "FICHA DA LUA"
        elif estado.modo_luas:
            rotulo = "MODO LUA"
        else:
            rotulo = "reconhecendo L..."
        superficie.blit(
            self._fontes.pequena.render(rotulo, True, cor_cracha), (x + 30, y + 2)
        )
        y += 26

        if planeta is None:
            superficie.blit(
                self._fontes.mini.render(
                    "escolha um planeta primeiro", True, COR_AVISO
                ),
                (x, y),
            )
        else:
            superficie.blit(
                self._fontes.pequena.render(planeta.nome, True, COR_TEXTO), (x, y)
            )
        y += 20

        if planeta is not None and not luas:
            superficie.blit(
                self._fontes.mini.render("não tem luas conhecidas", True, COR_AVISO),
                (x, y),
            )
        for indice, lua in enumerate(visiveis, start=1):
            escolhida = lua.nome == estado.lua_selecionada
            cor = COR_DESTAQUE if escolhida else COR_TEXTO_SECUNDARIO
            if escolhida:
                pygame.draw.circle(superficie, lua.cor, (x + 5, y + 7), 4)
            superficie.blit(
                self._fontes.mini.render(f"{indice}  {lua.nome}", True, cor),
                (x + 14, y),
            )
            # Barra de confirmação POR LINHA, só na lua em preview: é ela que
            # está enchendo, e desenhá-la ao lado do nome mostra exatamente o
            # que vai abrir. Some quando a ficha já abriu.
            if (
                escolhida
                and estado.progresso_lua > 0.0
                and not estado.ficha_lua_aberta
            ):
                trilho = pygame.Rect(
                    retangulo.right - _PADDING_LUAS - 60, y + 6, 60, 3
                )
                pygame.draw.rect(
                    superficie, COR_TRILHO_BARRA, trilho, border_radius=2
                )
                cheio = trilho.copy()
                cheio.width = int(trilho.width * min(1.0, estado.progresso_lua))
                pygame.draw.rect(superficie, COR_DESTAQUE, cheio, border_radius=2)
            y += _ALTURA_LINHA_LUA
        if restantes > 0:
            superficie.blit(
                self._fontes.mini.render(
                    f"+{restantes} no catálogo", True, COR_TEXTO_SECUNDARIO
                ),
                (x + 14, y),
            )
            y += _ALTURA_LINHA_LUA

        # Barra de confirmação: sem ela o usuário repete o gesto achando que
        # não pegou, e a repetição atrapalha justamente a contagem de frames.
        if not estado.modo_luas and estado.progresso_modo > 0.0:
            trilho = pygame.Rect(x, y + 2, retangulo.width - _PADDING_LUAS * 2, 4)
            pygame.draw.rect(superficie, COR_TRILHO_BARRA, trilho, border_radius=2)
            preenchido = trilho.copy()
            preenchido.width = int(trilho.width * min(1.0, estado.progresso_modo))
            pygame.draw.rect(superficie, COR_DESTAQUE, preenchido, border_radius=2)

        return retangulo.bottom

    def _desenhar_avisos(
        self, superficie: pygame.Surface, estado: EstadoHUD, topo: int = MARGEM_HUD
    ) -> None:
        """Mensagens de webcam, iluminação e dica das duas mãos."""
        avisos: list[tuple[str, tuple[int, int, int]]] = []
        leitura = estado.leitura

        # O aviso do modo lua vem primeiro: quando ele existe, é a resposta
        # direta ao que o usuário acabou de fazer com as mãos.
        if estado.aviso_lua:
            avisos.append((estado.aviso_lua, COR_AVISO))

        if estado.pinca_ativa:
            # Enquanto a pinça comanda o zoom a seleção por dedos fica suspensa:
            # sem este aviso o usuário acha que o reconhecimento travou.
            avisos.append(
                ("MODO ZOOM — afaste ou aproxime polegar e indicador", COR_SUCESSO)
            )

        if leitura.status in (StatusCamera.INDISPONIVEL, StatusCamera.DESCONECTADA):
            avisos.append((leitura.mensagem or "Webcam indisponível.", COR_ERRO))
        elif leitura.status is StatusCamera.INICIANDO:
            avisos.append(("Abrindo a webcam...", COR_TEXTO_SECUNDARIO))
        elif estado.pinca_ativa:
            pass  # em modo zoom, as dicas de contagem só atrapalhariam
        else:
            if leitura.brilho_medio < LIMIAR_BRILHO_BAIXO:
                avisos.append(
                    ("Iluminação baixa — a detecção pode falhar.", COR_AVISO)
                )
            elif (
                leitura.maos_visiveis > 0
                and leitura.confianca_media < LIMIAR_AVISO_CONFIANCA
            ):
                avisos.append(
                    ("Confiança baixa — aproxime e centralize a mão.", COR_AVISO)
                )
            if leitura.descartada_por_borda:
                avisos.append(("Mão saindo do quadro — leitura descartada.", COR_AVISO))
            # A dica dos números altos só faz sentido FORA do modo lua: lá o
            # total é "L (2 dedos) + número da outra mão" e não seleciona corpo
            # nenhum, então sugerir 5+4 mandaria o usuário para o lugar errado.
            if leitura.contagem == _MAXIMO_DEDOS_UMA_MAO and not estado.modo_luas:
                avisos.append(
                    ("Use as duas mãos para 6–9 (ex.: 5 + 4 = Lua).", COR_DESTAQUE)
                )

        if not avisos:
            return
        y = topo
        for texto, cor in avisos:
            renderizado = self._fontes.pequena.render(texto, True, cor)
            largura = renderizado.get_width() + 32
            retangulo = pygame.Rect(
                (self._largura - largura) // 2, y, largura, renderizado.get_height() + 12
            )
            desenhar_painel(superficie, retangulo)
            # Faixa colorida na borda esquerda: diferencia erro de dica sem
            # depender só da cor do texto.
            pygame.draw.rect(
                superficie,
                cor,
                pygame.Rect(retangulo.x + 1, retangulo.y + 6, 3, retangulo.height - 12),
                border_radius=2,
            )
            superficie.blit(renderizado, (retangulo.x + 16, retangulo.y + 6))
            y += retangulo.height + 6

    def _desenhar_debug(self, superficie: pygame.Surface, estado: EstadoHUD) -> None:
        """Painel de diagnóstico do reconhecimento (tecla F3).

        Existe porque quase todo problema relatado como "o gesto não pega" é na
        verdade uma de quatro coisas, e sem ver os números não dá para saber
        qual: FPS no chão, confiança baixa, leitura instável, ou o número certo
        chegando mas a confirmação nunca completando. O painel mostra as quatro
        lado a lado.
        """
        leitura = estado.leitura
        pose = leitura.pose

        planeta = estado.planeta_luas.nome if estado.planeta_luas else "—"
        numero = "—" if leitura.contagem is None else str(leitura.contagem)
        por_mao = " + ".join(str(c) for c in leitura.contagens_por_mao) or "—"
        lados = " / ".join(f"{m.lado[:1]}:{m.score:.2f}" for m in pose.maos) or "—"

        linhas: list[tuple[str, str, tuple[int, int, int]]] = [
            ("FPS", f"{estado.fps:5.1f}", self._cor_por_limiar(estado.fps, 50, 30)),
            ("PLANETA", planeta, COR_TEXTO),
            ("MODO LUA", self._estado_lua(estado), self._cor_estado_lua(estado)),
            ("NÚMERO", f"{numero}  (por mão: {por_mao})", COR_TEXTO),
            ("ÍNDICE LUA", str(estado.indice_lua or "—"), COR_TEXTO),
            ("MÃOS", f"{leitura.maos_visiveis}  [{lados}]", COR_TEXTO),
            (
                "CONFIANÇA",
                f"{leitura.confianca_media:.2f}",
                self._cor_por_limiar(leitura.confianca_media, 0.85, 0.70),
            ),
            (
                "ESTABILIDADE",
                f"{leitura.estabilidade:.2f}"
                + ("  (reaproveitada)" if leitura.reaproveitada else ""),
                self._cor_por_limiar(leitura.estabilidade, 0.80, 0.60),
            ),
        ]

        # +1 linha para a barra de confirmação, sempre desenhada (mesmo vazia):
        # o painel não pode mudar de altura a cada frame, senão pisca.
        altura = _PADDING_DEBUG * 2 + 22 + len(linhas) * _ALTURA_LINHA_DEBUG + 22
        retangulo = pygame.Rect(
            (self._largura - _LARGURA_PAINEL_DEBUG) // 2,
            self._altura - MARGEM_HUD - ALTURA_BARRA_ATALHOS - int(altura),
            _LARGURA_PAINEL_DEBUG,
            int(altura),
        )
        desenhar_painel(superficie, retangulo)

        x = retangulo.x + _PADDING_DEBUG
        y = retangulo.y + _PADDING_DEBUG
        superficie.blit(
            self._fontes.mini.render("DEBUG DE GESTOS  ·  F3", True, COR_DESTAQUE),
            (x, y),
        )
        y += 22

        for rotulo, valor, cor in linhas:
            superficie.blit(
                self._fontes.mini.render(rotulo, True, COR_TEXTO_SECUNDARIO), (x, y)
            )
            # Coluna fixa para os valores: alinhados, eles são legíveis de
            # relance enquanto se mexe a mão — que é quando o painel serve.
            superficie.blit(self._fontes.mono.render(valor, True, cor), (x + 108, y))
            y += _ALTURA_LINHA_DEBUG

        # Barra de confirmação da ficha da lua.
        y += 4
        superficie.blit(
            self._fontes.mini.render("CONFIRMAÇÃO", True, COR_TEXTO_SECUNDARIO), (x, y)
        )
        trilho = pygame.Rect(x + 108, y + 5, retangulo.right - _PADDING_DEBUG - x - 108, 5)
        pygame.draw.rect(superficie, COR_TRILHO_BARRA, trilho, border_radius=2)
        cheio = trilho.copy()
        cheio.width = int(trilho.width * min(1.0, max(0.0, estado.progresso_lua)))
        if cheio.width > 0:
            pygame.draw.rect(
                superficie,
                COR_SUCESSO if estado.ficha_lua_aberta else COR_DESTAQUE,
                cheio,
                border_radius=2,
            )

    @staticmethod
    def _estado_lua(estado: EstadoHUD) -> str:
        """Texto da linha "MODO LUA" do debug, fiel ao que está na TELA.

        A máquina de estados só é alimentada pelo caminho do GESTO; abrir uma
        lua pela tecla passa por fora dela. Sem esta correção o painel dizia
        "ocioso" com a ficha da lua aberta na frente do usuário — justamente o
        tipo de informação errada que um painel de diagnóstico não pode dar.
        """
        if estado.ficha_lua_aberta and estado.estado_selecao != "ficha":
            return "ficha (teclado)"
        # Sem câmera o seletor nunca é alimentado e fica parado em "ocioso", o
        # que esconderia o modo ligado pela tecla L. Aqui o teclado é o caso
        # normal, não a exceção: o app inteiro funciona sem webcam.
        if estado.modo_luas and estado.estado_selecao in ("", "ocioso"):
            return "ativo (teclado)"
        if estado.estado_selecao:
            return estado.estado_selecao
        return "ativo" if estado.modo_luas else "—"

    @staticmethod
    def _cor_estado_lua(estado: EstadoHUD) -> tuple[int, int, int]:
        """Aceso quando há modo lua ou ficha na tela; apagado quando não há."""
        if estado.modo_luas or estado.ficha_lua_aberta:
            return COR_DESTAQUE
        return COR_TEXTO_SECUNDARIO

    @staticmethod
    def _cor_por_limiar(
        valor: float, bom: float, aceitavel: float
    ) -> tuple[int, int, int]:
        """Verde/amarelo/vermelho conforme o valor cai abaixo dos limiares."""
        if valor >= bom:
            return COR_SUCESSO
        if valor >= aceitavel:
            return COR_AVISO
        return COR_ERRO

    def _desenhar_preview(
        self, superficie: pygame.Surface, leitura: LeituraGestos
    ) -> None:
        """Miniatura da webcam ancorada no canto inferior direito."""
        retangulo = pygame.Rect(
            self._largura - LARGURA_PREVIEW_CAMERA - MARGEM_HUD,
            self._altura - ALTURA_BLOCO_PREVIEW - MARGEM_HUD,
            LARGURA_PREVIEW_CAMERA,
            ALTURA_BLOCO_PREVIEW,
        )
        desenhar_painel(superficie, retangulo)

        quadro = leitura.preview
        if quadro is not None:
            self._superficie_preview = pygame.image.frombuffer(
                np.ascontiguousarray(quadro).tobytes(),
                (quadro.shape[1], quadro.shape[0]),
                "RGB",
            )
        if self._superficie_preview is not None:
            superficie.blit(self._superficie_preview, (retangulo.x, retangulo.y))
        else:
            superficie.blit(
                self._fontes.pequena.render("sem imagem", True, COR_TEXTO_SECUNDARIO),
                (retangulo.x + 12, retangulo.y + 12),
            )
        superficie.blit(
            self._fontes.mini.render(
                "webcam (C oculta/mostra)", True, COR_TEXTO_SECUNDARIO
            ),
            (retangulo.x + 8, retangulo.bottom - 18),
        )


__all__ = ["HUD", "EstadoHUD", "Fontes", "desenhar_painel"]
