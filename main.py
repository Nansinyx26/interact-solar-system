"""Sistema Solar Interativo controlado por gestos de mão.

Loop principal: consome a última leitura da thread de visão, estabiliza o gesto,
move a câmera e desenha a cena. A aplicação funciona por completo sem webcam —
nesse caso as teclas 0-9 fazem o papel dos dedos.

Uso:
    python main.py
"""

from __future__ import annotations

import argparse
import sys
import time
import webbrowser
from dataclasses import replace

import pygame

from config import (
    ALTURA_JANELA,
    ALTURA_MINIMA_JANELA,
    FATOR_AJUSTE_TEMPO,
    FATOR_ZOOM_RODA,
    FPS_ALVO,
    GESTO_VISAO_GERAL,
    INDICE_CAMERA,
    LARGURA_JANELA,
    LARGURA_MINIMA_JANELA,
    LUAS_VISIVEIS_PADRAO,
    MARGEM_HUD,
    SEGUNDOS_ATE_VISAO_GERAL,
    TIME_SCALE,
    TIME_SCALE_MAX,
    TIME_SCALE_MIN,
    TITULO_JANELA,
)
from dados.planetas import (
    CORPOS_POR_GESTO,
    CorpoCeleste,
    LuaMenor,
    corpo_por_gesto,
    luas_do_planeta,
)
from dados.telemetria import TelemetriaMongo
from gestos.detector import MEDIAPIPE_DISPONIVEL, DetectorMaos, LeituraGestos
from gestos.estabilizador import EstabilizadorGestos, ResultadoEstabilizacao
from gestos.estado_gesto import IntencaoGesto, MaquinaGestos
from gestos.pinca import ControladorPinca
from nucleo.camera import Camera2D
from nucleo.orbita import posicoes_do_sistema, raio_corpo_px
from nucleo.renderizador import Renderizador
from ui.ficha_planeta import FichaPlaneta
from ui.hud import (
    ALTURA_BLOCO_PREVIEW,
    HUD,
    EstadoHUD,
    Fontes,
    topo_do_painel_gesto,
)
from ui.marca_dagua import MarcaDagua
from ui.narrador import Narrador, texto_do_corpo
from ui.quiz import QuizDesktop

# Limite de dt: se a janela for arrastada ou o processo travar por um instante,
# a simulação não deve dar um salto gigante.
_DT_MAXIMO = 0.1

# Teclas numéricas (fila principal e teclado numérico) -> índice de gesto.
_TECLAS_NUMERICAS: dict[int, int] = {}
for _indice in CORPOS_POR_GESTO:
    _TECLAS_NUMERICAS[getattr(pygame, f"K_{_indice}")] = _indice
    _TECLAS_NUMERICAS[getattr(pygame, f"K_KP{_indice}")] = _indice

_TECLAS_ACELERAR = (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS)
_TECLAS_DESACELERAR = (pygame.K_MINUS, pygame.K_KP_MINUS)
_TECLAS_SAIR = (pygame.K_ESCAPE, pygame.K_q)
# "V" de visão geral — o equivalente de teclado ao gesto das duas mãos abertas.
_TECLA_VISAO_GERAL = pygame.K_v
# "N" de narração: liga/desliga a voz que anuncia o corpo focado.
_TECLA_NARRACAO = pygame.K_n
# "M" de luas (moons): mostra/esconde as luas dos demais planetas.
_TECLA_LUAS = pygame.K_m


class Aplicacao:
    """Orquestra captura de gestos, simulação e renderização."""

    def __init__(self, indice_camera: int = INDICE_CAMERA) -> None:
        # A webcam é o recurso mais lento do arranque (~2 s no Windows para o
        # DirectShow negociar o formato). Subir a thread ANTES do pygame faz
        # essa espera correr em paralelo com a geração das texturas, de modo
        # que a imagem já está pronta quando a janela aparece.
        self.detector = DetectorMaos(indice_camera)
        self.detector.iniciar()
        # O motor de voz também demora a subir (SAPI no Windows): junto com a
        # webcam, essa espera corre em paralelo com a montagem da cena.
        self.narrador = Narrador()
        self.narrador.iniciar()
        self.telemetria = TelemetriaMongo()
        self.telemetria.registrar_sessao("desktop")
        try:
            self._construir()
        except BaseException:
            # Sem isto, uma falha na montagem da cena deixaria a webcam presa.
            self.detector.parar()
            self.narrador.parar()
            raise

    def _construir(self) -> None:
        """Monta janela, recursos gráficos e estado inicial da simulação."""
        pygame.init()
        pygame.display.set_caption(TITULO_JANELA)
        # RESIZABLE dá à janela os botões padrão do sistema (minimizar,
        # maximizar, fechar) e permite arrastar as bordas para redimensionar.
        self.tela = pygame.display.set_mode(
            (LARGURA_JANELA, ALTURA_JANELA), pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        self.largura, self.altura = self.tela.get_size()
        self.relogio = pygame.time.Clock()

        self.fontes = Fontes.carregar()
        self.renderizador = Renderizador(self.fontes.mini, self.largura, self.altura)
        self.hud = HUD(self.fontes, self.largura, self.altura)
        self.ficha = FichaPlaneta(self.fontes, self.largura, self.altura)
        self.marca = MarcaDagua(self.fontes, self.largura, self.altura)
        self.quiz = QuizDesktop(self.fontes, self.largura, self.altura, self.telemetria)
        self.camera = Camera2D(self.largura, self.altura)
        self.estabilizador = EstabilizadorGestos()
        self.pinca = ControladorPinca()

        self.tempo_dias: float = 0.0
        self.escala_tempo: float = TIME_SCALE
        self.pausado: bool = False
        self.mostrar_preview: bool = True
        self.corpo_alvo: CorpoCeleste | None = None
        self.executando: bool = True
        # Modo livre: o usuário assumiu a câmera com o mouse e o rastreamento
        # automático do alvo fica suspenso até o próximo gesto/atalho.
        self.luas_visiveis: bool = LUAS_VISIVEIS_PADRAO
        self.maquina_gestos = MaquinaGestos()
        # Planeta e lua são campos SEPARADOS de propósito. Com um só, sair do
        # modo luas mantendo a lua em foco deixaria o usuário sem caminho de
        # volta ao planeta a não ser passando pela visão geral.
        self.planeta_selecionado: CorpoCeleste | None = None
        self.lua_selecionada: LuaMenor | None = None
        self.aviso_luas: str = ""
        self.intencao = IntencaoGesto(
            modo_luas=False,
            numero=None,
            progresso_modo=0.0,
            modo_mudou=False,
            l_detectado=False,
        )
        self.camera_livre: bool = False
        self._arrastando: bool = False

        # Estado compartilhado entre atualização e desenho, já inicializado para
        # o caso de uma tecla chegar antes do primeiro _atualizar().
        self.posicoes = posicoes_do_sistema(0.0)
        self.leitura = LeituraGestos()
        self.resultado_gesto = ResultadoEstabilizacao(
            confirmado=None, candidato=None, progresso=0.0, em_cooldown=False
        )
        self._ultima_sequencia: int = -1

    # ------------------------------------------------------------ ciclo alto
    def executar(self) -> None:
        """Roda o loop principal até o usuário sair, sempre liberando recursos."""
        try:
            while self.executando:
                dt = min(self.relogio.tick(FPS_ALVO) / 1000.0, _DT_MAXIMO)
                self._tratar_eventos()
                self._atualizar(dt)
                self._desenhar()
                pygame.display.flip()
        finally:
            # A webcam precisa ser liberada mesmo se algo estourar acima.
            self.detector.parar()
            self.narrador.parar()
            pygame.quit()

    # -------------------------------------------------------------- entrada
    def _tratar_eventos(self) -> None:
        """Processa a fila de eventos do pygame (teclado é fallback completo)."""
        for evento in pygame.event.get():
            # Quando o quiz está ativo, ele tem prioridade sobre cliques e teclas.
            if self.quiz.ativo and self.quiz.tratar_evento(evento):
                continue
            # A assinatura é clicável: quando ela consome o clique, ele não pode
            # virar um arrasto de câmera atrás do painel.
            if self.marca.tratar_evento(evento):
                continue
            if evento.type == pygame.QUIT:
                self.executando = False
            elif evento.type == pygame.KEYDOWN:
                self._tratar_tecla(evento.key)
            elif evento.type == pygame.VIDEORESIZE:
                self._redimensionar(evento.w, evento.h)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._arrastando = True
            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                self._arrastando = False
            elif evento.type == pygame.MOUSEMOTION and self._arrastando:
                # Arrastar assume a câmera: o alvo continua selecionado (a ficha
                # permanece), mas a cena para de segui-lo até o próximo comando.
                self.camera_livre = True
                self.camera.arrastar(*evento.rel)
            elif evento.type == pygame.MOUSEWHEEL:
                self.camera_livre = True
                self.camera.aplicar_zoom(FATOR_ZOOM_RODA**evento.y)

    def _redimensionar(self, largura: int, altura: int) -> None:
        """Aplica o novo tamanho da janela, respeitando o mínimo utilizável."""
        largura = max(LARGURA_MINIMA_JANELA, largura)
        altura = max(ALTURA_MINIMA_JANELA, altura)
        self.tela = pygame.display.set_mode(
            (largura, altura), pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        self.largura, self.altura = self.tela.get_size()
        self.camera.redimensionar(self.largura, self.altura)
        self.renderizador.redimensionar(self.largura, self.altura)
        self.hud.redimensionar(self.largura, self.altura)
        self.ficha.redimensionar(self.largura, self.altura)
        self.marca.redimensionar(self.largura, self.altura)
        self.quiz.redimensionar(self.largura, self.altura)

    def _tratar_tecla(self, tecla: int) -> None:
        """Aplica o atalho correspondente à tecla pressionada."""
        if tecla in _TECLAS_SAIR:
            self.executando = False
        elif tecla == pygame.K_SPACE:
            self.pausado = not self.pausado
        elif tecla == _TECLA_VISAO_GERAL:
            self._voltar_visao_geral()
        elif tecla == _TECLA_NARRACAO:
            self.narrador.alternar()
        elif tecla == _TECLA_LUAS:
            # Não há número de dedos livre (0-10 estão todos ocupados), então as
            # luas menores entram e saem por tecla.
            self.luas_visiveis = not self.luas_visiveis
        elif tecla == pygame.K_r:
            webbrowser.open("https://sistema-solar-gestos.vercel.app/ranking.html")
        elif tecla == pygame.K_a:
            if self.quiz.ativo:
                self.quiz.fechar()
            else:
                self.quiz.abrir()
        elif tecla == pygame.K_c:
            self.mostrar_preview = not self.mostrar_preview
        elif tecla == pygame.K_l:
            lua = corpo_por_gesto(9)
            if lua:
                self.estabilizador.forcar(9, time.monotonic())
                self._selecionar(lua)
        elif tecla in _TECLAS_ACELERAR:
            self.escala_tempo = min(
                TIME_SCALE_MAX, self.escala_tempo * FATOR_AJUSTE_TEMPO
            )
        elif tecla in _TECLAS_DESACELERAR:
            self.escala_tempo = max(
                TIME_SCALE_MIN, self.escala_tempo / FATOR_AJUSTE_TEMPO
            )
        elif tecla in _TECLAS_NUMERICAS:
            indice = _TECLAS_NUMERICAS[tecla]
            self.estabilizador.forcar(indice, time.monotonic())
            self._selecionar(corpo_por_gesto(indice))

    # ---------------------------------------------------------- atualização
    def _atualizar(self, dt: float) -> None:
        """Avança simulação, gestos, câmera e animações da interface."""
        if not self.pausado:
            self.tempo_dias += dt * self.escala_tempo
        self.posicoes = posicoes_do_sistema(self.tempo_dias)

        agora = time.monotonic()
        self.leitura = self.detector.ler()

        # O estabilizador só avança quando chega uma INFERÊNCIA nova (~15 Hz).
        # Alimentá-lo a 60 Hz encheria o buffer com a mesma leitura repetida e
        # a confirmação viraria quase instantânea, perdendo o efeito de filtro.
        if self.leitura.sequencia != self._ultima_sequencia:
            self._ultima_sequencia = self.leitura.sequencia

            # Pinça primeiro: enquanto ela comanda o zoom, a pose seria contada
            # como 2 dedos (Vênus) e trocaria o foco no meio do movimento.
            estado_pinca = self.pinca.atualizar(self.leitura.razoes_pinca, agora)
            if estado_pinca.comando_luas:
                # As duas mãos em pinça: o único gesto que sobrou, já que 0-10
                # estão todos ocupados. Alterna as luas dos planetas.
                self.luas_visiveis = not self.luas_visiveis
            elif estado_pinca.fator_zoom != 1.0:
                self.camera_livre = True
                self.camera.aplicar_zoom(estado_pinca.fator_zoom)

            # A FORMA da mão vem antes da contagem: o "L" consome dois dedos e
            # não pode entrar na soma (viraria 2 = Vênus).
            self.intencao = self.maquina_gestos.atualizar(
                list(self.leitura.maos), agora
            )

            if self.intencao.modo_luas:
                # No modo luas o número significa índice de lua, não planeta:
                # o estabilizador de corpos fica de fora.
                if self.intencao.lua_confirmada is not None:
                    self._selecionar_lua(self.intencao.lua_confirmada)
                self.resultado_gesto = replace(self.resultado_gesto, confirmado=None)
            else:
                # 0-9 selecionam um corpo e 10 é o comando "visão geral".
                contagem = self.leitura.contagem
                valido = contagem in CORPOS_POR_GESTO or contagem == GESTO_VISAO_GERAL
                leitura_valida = contagem if valido else None
                if self.pinca.bloqueando_gestos(agora):
                    leitura_valida = None
                self.resultado_gesto = self.estabilizador.atualizar(
                    leitura_valida, agora
                )
        elif self.resultado_gesto.confirmado is not None:
            # Não reconfirma o mesmo evento nos frames seguintes.
            self.resultado_gesto = replace(self.resultado_gesto, confirmado=None)

        confirmado = self.resultado_gesto.confirmado
        if confirmado == GESTO_VISAO_GERAL:
            # Duas mãos abertas (5 + 5): reenquadra o sistema inteiro. O valor
            # segue confirmado no estabilizador para não disparar em looping.
            self._voltar_visao_geral(reiniciar_gesto=False)
        elif confirmado is not None:
            self._selecionar(corpo_por_gesto(confirmado))
        elif (
            self.leitura.camera_ok
            and self.corpo_alvo is not None
            and self.estabilizador.segundos_sem_gesto(agora) > SEGUNDOS_ATE_VISAO_GERAL
        ):
            # Ninguém na frente da câmera há um bom tempo: volta ao panorama.
            self._voltar_visao_geral()

        if self.corpo_alvo is not None and not self.camera_livre:
            # O alvo continua orbitando: o destino é reavaliado a cada frame,
            # sem reiniciar a interpolação em andamento.
            self.camera.focar_corpo(
                self.posicoes[self.corpo_alvo.nome],
                raio_corpo_px(self.corpo_alvo),
                reiniciar=False,
            )
        self.camera.atualizar(dt)
        self.ficha.atualizar(dt)
        self.marca.atualizar(dt, self._base_canto_direito())
        if self.quiz.ativo:
            self.quiz.atualizar(dt)

    def _selecionar(self, corpo: CorpoCeleste | None) -> None:
        """Foca um corpo (ignora índices sem corpo associado)."""
        mesmo_alvo = self.corpo_alvo is not None and corpo is self.corpo_alvo
        if corpo is None or (mesmo_alvo and not self.camera_livre):
            return
        self.camera_livre = False  # um comando novo devolve a câmera ao app
        self.corpo_alvo = corpo
        if not corpo.eh_satelite:
            # Guarda o contexto: é este planeta que o modo luas vai consultar.
            self.planeta_selecionado = corpo
            self.lua_selecionada = None
            self.aviso_luas = ""
        self.camera.focar_corpo(
            self.posicoes[corpo.nome], raio_corpo_px(corpo), reiniciar=True
        )
        self.ficha.mostrar(corpo)
        self.narrador.anunciar(texto_do_corpo(corpo))
        self.telemetria.registrar_interacao(corpo.nome, corpo.indice_gesto, "desktop")

    def _selecionar_lua(self, indice: int) -> None:
        """Aplica o número recebido no modo luas como índice de lua.

        O alvo é o planeta em contexto. Sem planeta (Sol ou visão geral) a Terra
        assume, que é o caso mais provável de quem está começando a explorar.
        """
        alvo = self.planeta_selecionado
        if alvo is None or alvo.eh_sol:
            alvo = corpo_por_gesto(3)  # Terra
            self.planeta_selecionado = alvo
        if alvo is None:
            return

        luas = luas_do_planeta(alvo.nome)
        if not luas:
            self.aviso_luas = f"{alvo.nome} não tem luas conhecidas."
            self.lua_selecionada = None
            return

        self.luas_visiveis = True
        if indice == 0:
            # Zero mostra TODAS: é a única forma de voltar à visão do sistema
            # de luas sem largar o modificador.
            self.lua_selecionada = None
            self.aviso_luas = f"{alvo.nome}: todas as {len(luas)} luas."
            return
        if indice > len(luas):
            # Número maior que a quantidade não troca nada — só avisa. A lista
            # do HUD sai do catálogo, então ela nunca promete o que não existe.
            plural = "luas" if len(luas) > 1 else "lua"
            self.aviso_luas = f"{alvo.nome} tem {len(luas)} {plural}."
            return

        # O foco vem ANTES de gravar a lua: _selecionar() limpa lua_selecionada
        # (é o que faz escolher um planeta desfazer a lua), então inverter a
        # ordem apagaria a escolha no mesmo frame em que ela foi feita.
        #
        # A câmera fica no PLANETA: a lua é destacada, mas o planeta continua
        # como referência de escala, que é o ponto de olhar para uma lua.
        if self.corpo_alvo is not alvo:
            self._selecionar(alvo)
            self.planeta_selecionado = alvo
        self.lua_selecionada = luas[indice - 1]
        self.aviso_luas = ""

    def _voltar_visao_geral(self, reiniciar_gesto: bool = True) -> None:
        """Desfaz o foco e reenquadra o sistema inteiro.

        ``reiniciar_gesto`` limpa o valor confirmado no estabilizador. Fica
        desligado quando a volta veio do próprio gesto de comando (10), senão
        ele seria reconfirmado a cada meio segundo com as mãos ainda abertas.
        """
        if self.corpo_alvo is None and not self.camera_livre:
            return
        self.camera_livre = False
        self.corpo_alvo = None
        # O gesto 10 e a tecla V sempre zeram o modo luas, como combinado.
        self.maquina_gestos.reiniciar()
        self.lua_selecionada = None
        self.aviso_luas = ""
        self.camera.voltar_visao_geral()
        self.ficha.ocultar()
        self.telemetria.registrar_interacao("Visao Geral", GESTO_VISAO_GERAL, "desktop")
        if reiniciar_gesto:
            self.estabilizador.reiniciar()

    # -------------------------------------------------------------- desenho
    def _base_canto_direito(self) -> int:
        """y da base livre no canto inferior direito (acima do preview)."""
        base = self.altura - MARGEM_HUD
        if self.mostrar_preview:
            base -= ALTURA_BLOCO_PREVIEW + MARGEM_HUD
        return base

    def _desenhar(self) -> None:
        """Compõe o frame: cena, ficha, HUD e assinatura, nessa ordem."""
        self.renderizador.desenhar(
            self.tela,
            self.camera,
            self.posicoes,
            self.tempo_dias,
            self.corpo_alvo,
            self.luas_visiveis,
        )
        # A ficha vive na coluna esquerda e só pode descer até onde o painel de
        # gesto começa — a coluna direita é da webcam e da assinatura.
        self.ficha.desenhar(self.tela, topo_do_painel_gesto(self.altura) - MARGEM_HUD)
        self.hud.desenhar(
            self.tela,
            EstadoHUD(
                fps=self.relogio.get_fps(),
                leitura=self.leitura,
                resultado=self.resultado_gesto,
                corpo_alvo=self.corpo_alvo,
                mostrar_preview=self.mostrar_preview,
                pausado=self.pausado,
                escala_tempo=self.escala_tempo,
                valor_confirmado=self.estabilizador.valor_confirmado,
                pinca_ativa=self.pinca.ativa,
                narracao_ativa=self.narrador.ativo,
            ),
        )
        self.marca.desenhar(self.tela)
        if self.quiz.ativo:
            self.quiz.desenhar(self.tela)


def main() -> int:
    """Ponto de entrada. Aceita ``--camera N`` para escolher a webcam."""
    analisador = argparse.ArgumentParser(description=TITULO_JANELA)
    analisador.add_argument(
        "--camera",
        type=int,
        default=INDICE_CAMERA,
        help="índice da webcam (0 é a padrão; tente 1 ou 2 se houver mais de uma)",
    )
    argumentos = analisador.parse_args()

    print(TITULO_JANELA)
    print(
        "Teclas: 0-9 focar (9/L = Lua) | V visão geral | ESPAÇO pausa | "
        "+/- tempo | C câmera | N voz | Q sair"
    )
    print("Mouse: arrastar = pan | roda = zoom | janela redimensionável")
    versao_python = sys.version.split()[0]
    print(f"Python {versao_python} | webcam pedida: índice {argumentos.camera}")
    if not MEDIAPIPE_DISPONIVEL:
        print(
            "AVISO: MediaPipe não pôde ser importado. A aplicação roda em modo\n"
            "       teclado, sem gestos. Instale com:\n"
            "       pip install -r requirements.txt"
        )
    Aplicacao(argumentos.camera).executar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
