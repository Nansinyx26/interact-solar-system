"""Módulo de Atividades & Quiz interativo para o Sistema Solar (Pygame).

Contém a classe QuizDesktop que gerencia:
1. Tela de Identificação (Nome e Série do Aluno)
2. Tela de Questões (10 perguntas astronômicas com tempo e barra de progresso)
3. Tela de Resultados (Pontuação, acertos, tempo, gabarito e envio ao Ranking)
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pygame

from config import (
    COR_AVISO,
    COR_DESTAQUE,
    COR_ERRO,
    COR_PAINEL,
    COR_SUCESSO,
    COR_TEXTO,
    COR_TEXTO_SECUNDARIO,
)
from ui.hud import Fontes, desenhar_painel
from ui.icones import (
    desenhar_chapeu_formatura,
    desenhar_check,
    desenhar_cronometro,
    desenhar_estrela,
    desenhar_lapis,
    desenhar_nuvem_upload,
    desenhar_recarregar,
    desenhar_trofeu,
    desenhar_usuario,
    desenhar_x,
)

if TYPE_CHECKING:
    from dados.telemetria import TelemetriaMongo


@dataclass(frozen=True)
class QuestaoQuiz:
    id: int
    pergunta: str
    opcoes: list[str]
    correta: int  # Índice 0..3


QUESTOES_QUIZ: list[QuestaoQuiz] = [
    QuestaoQuiz(
        id=1,
        pergunta="1. Qual é o maior planeta de todo o Sistema Solar?",
        opcoes=["Terra", "Júpiter", "Saturno", "Sol"],
        correta=1,
    ),
    QuestaoQuiz(
        id=2,
        pergunta="2. Qual planeta é conhecido popularmente como o 'Planeta Vermelho'?",
        opcoes=["Vênus", "Mercúrio", "Marte", "Júpiter"],
        correta=2,
    ),
    QuestaoQuiz(
        id=3,
        pergunta="3. Qual é o único satélite natural do planeta Terra?",
        opcoes=["Lua", "Fobos", "Titã", "Europa"],
        correta=0,
    ),
    QuestaoQuiz(
        id=4,
        pergunta="4. Qual é o planeta mais QUENTE do Sistema Solar (devido ao efeito estufa denso)?",
        opcoes=["Mercúrio", "Vênus", "Marte", "Sol"],
        correta=1,
    ),
    QuestaoQuiz(
        id=5,
        pergunta="5. Qual planeta é famoso por ter os anéis mais impressionantes e brilhantes?",
        opcoes=["Urano", "Netuno", "Saturno", "Júpiter"],
        correta=2,
    ),
    QuestaoQuiz(
        id=6,
        pergunta="6. Qual é o planeta mais próximo do Sol?",
        opcoes=["Mercúrio", "Vênus", "Terra", "Marte"],
        correta=0,
    ),
    QuestaoQuiz(
        id=7,
        pergunta="7. Qual planeta possui uma inclinação extrema de 98º e gira quase 'deitado'?",
        opcoes=["Netuno", "Urano", "Saturno", "Mercúrio"],
        correta=1,
    ),
    QuestaoQuiz(
        id=8,
        pergunta="8. Qual é o planeta mais distante do Sol no nosso Sistema Solar?",
        opcoes=["Urano", "Saturno", "Netuno", "Plutão"],
        correta=2,
    ),
    QuestaoQuiz(
        id=9,
        pergunta="9. O que está localizado exatamente no centro do nosso Sistema Solar?",
        opcoes=["A Terra", "O Sol (uma estrela)", "Júpiter", "A Lua"],
        correta=1,
    ),
    QuestaoQuiz(
        id=10,
        pergunta="10. Quanto tempo a Terra leva para dar uma volta completa ao redor do Sol?",
        opcoes=["24 horas", "30 dias", "365 dias (1 ano)", "12 anos"],
        correta=2,
    ),
]

# Séries e salas EXATAMENTE como no <select> de web/atividades.html — os dois
# lados gravam no mesmo ranking, e um valor escrito de outro jeito ("5º Ano A"
# contra "5º Ano" + sala "A") viraria uma linha separada na classificação.
OPCOES_SERIE: list[str] = [
    "1º Ano",
    "2º Ano",
    "3º Ano",
    "4º Ano",
    "5º Ano",
    "6º Ano",
    "7º Ano",
    "8º Ano",
    "9º Ano",
    "Outro",
]

# Sala separada da série: a classificação é comparada por sala, e juntar as duas
# num campo só impediria esse agrupamento. (Mesmo comentário do atividades.html.)
OPCOES_SALA: list[str] = ["A", "B", "C", "D", "E", "Única"]


class EstadoQuiz:
    IDENTIFICACAO = "identificacao"
    QUESTOES = "questoes"
    RESULTADO = "resultado"


class QuizDesktop:
    """Gerencia e renderiza o Quiz astronômico interativo no Pygame."""

    def __init__(
        self,
        fontes: Fontes,
        largura: int,
        altura: int,
        telemetria: TelemetriaMongo | None = None,
    ) -> None:
        self.fontes = fontes
        self.largura = largura
        self.altura = altura
        self.telemetria = telemetria

        self.ativo: bool = False
        self.estado: str = EstadoQuiz.IDENTIFICACAO

        # Dados do aluno
        self.nome_aluno: str = ""
        self.indice_serie: int = 4  # Padrão: "5º Ano" (o público principal)
        self.indice_sala: int = 5  # Padrão: "Única"
        self.campo_foco: str = "nome"  # 'nome', 'serie' ou 'sala'
        self.cursor_visivel: bool = True
        self.tempo_ultimo_cursor: float = 0.0

        # Progresso das questões
        self.indice_questao: int = 0
        self.respostas: list[int | None] = [None] * len(QUESTOES_QUIZ)
        self.opcao_hover: int | None = None
        self.tempo_inicio: float = 0.0
        self.tempo_total_segundos: float = 0.0

        # Resultados e Ranking
        self.pontuacao: int = 0
        self.acertos: int = 0
        self.status_envio_ranking: str = ""  # "", "enviando", "sucesso", "erro"
        self.offset_scroll_gabarito: int = 0

        # Retângulos interativos (atualizados a cada desenho)
        self._ret_botoes: dict[str, pygame.Rect] = {}
        self._ret_opcoes: list[pygame.Rect] = []

    def abrir(self) -> None:
        """Abre o quiz iniciando na tela de identificação."""
        self.ativo = True
        self.estado = EstadoQuiz.IDENTIFICACAO
        self.status_envio_ranking = ""
        self.offset_scroll_gabarito = 0

    def fechar(self) -> None:
        """Fecha o quiz e retorna à simulação."""
        self.ativo = False

    def redimensionar(self, largura: int, altura: int) -> None:
        """Atualiza dimensões para desenhar de acordo com a resolução da janela."""
        self.largura = largura
        self.altura = altura

    def iniciar_questoes(self) -> None:
        """Inicia as 10 perguntas."""
        if not self.nome_aluno.strip():
            self.nome_aluno = "Astrônomo(a) Anônimo(a)"
        self.indice_questao = 0
        self.respostas = [None] * len(QUESTOES_QUIZ)
        self.tempo_inicio = time.time()
        self.estado = EstadoQuiz.QUESTOES

    def finalizar_questoes(self) -> None:
        """Calcula o resultado final e avança para a tela de resultados."""
        self.tempo_total_segundos = max(1.0, time.time() - self.tempo_inicio)
        self.acertos = sum(
            1 for idx, q in enumerate(QUESTOES_QUIZ) if self.respostas[idx] == q.correta
        )
        self.pontuacao = self.acertos * 100
        self.status_envio_ranking = ""
        self.offset_scroll_gabarito = 0
        self.estado = EstadoQuiz.RESULTADO

    def enviar_ranking(self) -> None:
        """Envia a pontuação para a telemetria do MongoDB."""
        if not self.telemetria:
            self.status_envio_ranking = "erro"
            return

        self.status_envio_ranking = "enviando"
        try:
            serie = OPCOES_SERIE[self.indice_serie]
            sala = OPCOES_SALA[self.indice_sala]
            self.telemetria.registrar_ranking(
                nome=self.nome_aluno,
                serie=serie,
                sala=sala,
                pontuacao=self.pontuacao,
                acertos=self.acertos,
                tempo_segundos=self.tempo_total_segundos,
                origem="desktop_quiz",
            )
            self.status_envio_ranking = "sucesso"
        except Exception as e:
            print(f"[quiz] Falha ao enviar ranking: {e}")
            self.status_envio_ranking = "erro"

    # ---------------------------------------------------------------- Eventos
    def tratar_evento(self, evento: pygame.event.Event) -> bool:
        """Processa cliques e teclas. Retorna True se o evento foi consumido pelo quiz."""
        if not self.ativo:
            return False

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.fechar()
                return True

            if self.estado == EstadoQuiz.IDENTIFICACAO:
                self._tratar_tecla_identificacao(evento)
            elif self.estado == EstadoQuiz.QUESTOES:
                self._tratar_tecla_questoes(evento)
            elif self.estado == EstadoQuiz.RESULTADO:
                self._tratar_tecla_resultado(evento)
            return True

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = evento.pos
            if self.estado == EstadoQuiz.IDENTIFICACAO:
                self._tratar_clique_identificacao(pos)
            elif self.estado == EstadoQuiz.QUESTOES:
                self._tratar_clique_questoes(pos)
            elif self.estado == EstadoQuiz.RESULTADO:
                self._tratar_clique_resultado(pos)
            return True

        if evento.type == pygame.MOUSEWHEEL and self.estado == EstadoQuiz.RESULTADO:
            self.offset_scroll_gabarito = max(
                0, min(self.offset_scroll_gabarito - evento.y * 30, 400)
            )
            return True

        return True

    # Ordem do TAB, espelhando a ordem dos campos no formulário da web.
    _ORDEM_CAMPOS = ("nome", "serie", "sala")

    def _tratar_tecla_identificacao(self, evento: pygame.event.Event) -> None:
        if evento.key == pygame.K_TAB:
            # Com três campos o alternador binário não serve mais: cicla.
            indice = self._ORDEM_CAMPOS.index(self.campo_foco)
            self.campo_foco = self._ORDEM_CAMPOS[(indice + 1) % len(self._ORDEM_CAMPOS)]
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.iniciar_questoes()
        elif self.campo_foco == "nome":
            if evento.key == pygame.K_BACKSPACE:
                self.nome_aluno = self.nome_aluno[:-1]
            elif len(self.nome_aluno) < 40 and evento.unicode.isprintable():
                self.nome_aluno += evento.unicode
        elif self.campo_foco == "serie":
            if evento.key in (pygame.K_LEFT, pygame.K_UP):
                self.indice_serie = (self.indice_serie - 1) % len(OPCOES_SERIE)
            elif evento.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self.indice_serie = (self.indice_serie + 1) % len(OPCOES_SERIE)
        elif self.campo_foco == "sala":
            if evento.key in (pygame.K_LEFT, pygame.K_UP):
                self.indice_sala = (self.indice_sala - 1) % len(OPCOES_SALA)
            elif evento.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self.indice_sala = (self.indice_sala + 1) % len(OPCOES_SALA)

    def _tratar_clique_identificacao(self, pos: tuple[int, int]) -> None:
        if "btn_iniciar" in self._ret_botoes and self._ret_botoes["btn_iniciar"].collidepoint(pos):
            self.iniciar_questoes()
            return
        if "campo_nome" in self._ret_botoes and self._ret_botoes["campo_nome"].collidepoint(pos):
            self.campo_foco = "nome"
            return
        if "btn_serie_esq" in self._ret_botoes and self._ret_botoes["btn_serie_esq"].collidepoint(pos):
            self.indice_serie = (self.indice_serie - 1) % len(OPCOES_SERIE)
            self.campo_foco = "serie"
            return
        if "btn_serie_dir" in self._ret_botoes and self._ret_botoes["btn_serie_dir"].collidepoint(pos):
            self.indice_serie = (self.indice_serie + 1) % len(OPCOES_SERIE)
            self.campo_foco = "serie"
            return
        if "btn_sala_esq" in self._ret_botoes and self._ret_botoes["btn_sala_esq"].collidepoint(pos):
            self.indice_sala = (self.indice_sala - 1) % len(OPCOES_SALA)
            self.campo_foco = "sala"
            return
        if "btn_sala_dir" in self._ret_botoes and self._ret_botoes["btn_sala_dir"].collidepoint(pos):
            self.indice_sala = (self.indice_sala + 1) % len(OPCOES_SALA)
            self.campo_foco = "sala"
            return
        if "btn_fechar" in self._ret_botoes and self._ret_botoes["btn_fechar"].collidepoint(pos):
            self.fechar()
            return

    def _tratar_tecla_questoes(self, evento: pygame.event.Event) -> None:
        # Atalhos 1-4 ou A-D para selecionar opção
        teclas_opcoes = {
            pygame.K_1: 0,
            pygame.K_KP1: 0,
            pygame.K_a: 0,
            pygame.K_2: 1,
            pygame.K_KP2: 1,
            pygame.K_b: 1,
            pygame.K_3: 2,
            pygame.K_KP3: 2,
            pygame.K_c: 2,
            pygame.K_4: 3,
            pygame.K_KP4: 3,
            pygame.K_d: 3,
        }
        if evento.key in teclas_opcoes:
            self.respostas[self.indice_questao] = teclas_opcoes[evento.key]
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.respostas[self.indice_questao] is not None:
                if self.indice_questao < len(QUESTOES_QUIZ) - 1:
                    self.indice_questao += 1
                else:
                    self.finalizar_questoes()

    def _tratar_clique_questoes(self, pos: tuple[int, int]) -> None:
        for idx, rect in enumerate(self._ret_opcoes):
            if rect.collidepoint(pos):
                self.respostas[self.indice_questao] = idx
                return

        if "btn_avancar" in self._ret_botoes and self._ret_botoes["btn_avancar"].collidepoint(pos):
            if self.respostas[self.indice_questao] is not None:
                if self.indice_questao < len(QUESTOES_QUIZ) - 1:
                    self.indice_questao += 1
                else:
                    self.finalizar_questoes()
            return

        if "btn_voltar_q" in self._ret_botoes and self._ret_botoes["btn_voltar_q"].collidepoint(pos):
            if self.indice_questao > 0:
                self.indice_questao -= 1
            return

        if "btn_fechar" in self._ret_botoes and self._ret_botoes["btn_fechar"].collidepoint(pos):
            self.fechar()
            return

    def _tratar_tecla_resultado(self, evento: pygame.event.Event) -> None:
        if evento.key in (pygame.K_r, pygame.K_BACKSPACE):
            self.iniciar_questoes()
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            if self.status_envio_ranking != "sucesso":
                self.enviar_ranking()

    def _tratar_clique_resultado(self, pos: tuple[int, int]) -> None:
        if "btn_ranking" in self._ret_botoes and self._ret_botoes["btn_ranking"].collidepoint(pos):
            if self.status_envio_ranking != "sucesso":
                self.enviar_ranking()
            return
        if "btn_reiniciar" in self._ret_botoes and self._ret_botoes["btn_reiniciar"].collidepoint(pos):
            self.iniciar_questoes()
            return
        if "btn_fechar" in self._ret_botoes and self._ret_botoes["btn_fechar"].collidepoint(pos):
            self.fechar()
            return

    # -------------------------------------------------------------- Animação & Atualização
    def atualizar(self, dt: float) -> None:
        """Atualiza piscada do cursor e timers."""
        if not self.ativo:
            return

        agora = time.time()
        if agora - self.tempo_ultimo_cursor > 0.5:
            self.cursor_visivel = not self.cursor_visivel
            self.tempo_ultimo_cursor = agora

    # -------------------------------------------------------------- Renderização
    def desenhar(self, tela: pygame.Surface) -> None:
        """Desenha a tela do quiz como um overlay elegante por cima do simulador."""
        if not self.ativo:
            return

        # 1. Overlay escuro de fundo com efeito translúcido
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((4, 6, 14, 215))
        tela.blit(overlay, (0, 0))

        # 2. Dimensões do cartão principal centralizado
        largura_painel = min(780, self.largura - 40)
        altura_painel = min(620, self.altura - 60)
        x_painel = (self.largura - largura_painel) // 2
        y_painel = (self.altura - altura_painel) // 2
        rect_painel = pygame.Rect(x_painel, y_painel, largura_painel, altura_painel)

        # Fundo do cartão
        desenhar_painel(tela, rect_painel, alpha=235)
        # Borda sutil de destaque no topo
        pygame.draw.rect(tela, (*COR_DESTAQUE, 90), rect_painel, width=2, border_radius=10)

        # Botão Fechar no canto superior direito do cartão
        ret_fechar = pygame.Rect(x_painel + largura_painel - 42, y_painel + 14, 28, 28)
        self._ret_botoes["btn_fechar"] = ret_fechar
        pygame.draw.rect(tela, (255, 255, 255, 20), ret_fechar, border_radius=6)
        desenhar_x(tela, ret_fechar.center, tamanho=14, cor=COR_TEXTO_SECUNDARIO)

        # Desenha a tela específica
        self._ret_opcoes.clear()
        if self.estado == EstadoQuiz.IDENTIFICACAO:
            self._desenhar_identificacao(tela, rect_painel)
        elif self.estado == EstadoQuiz.QUESTOES:
            self._desenhar_questoes(tela, rect_painel)
        elif self.estado == EstadoQuiz.RESULTADO:
            self._desenhar_resultado(tela, rect_painel)

    def _desenhar_identificacao(self, tela: pygame.Surface, rect_p: pygame.Rect) -> None:
        """Desenha a tela de entrada: Nome + Série + Sala."""
        cx = rect_p.centerx
        topo = rect_p.y + 40

        # Ícone do Topo (Chapéu de Formatura / Desafio)
        desenhar_chapeu_formatura(tela, (cx, topo), tamanho=36, cor=COR_DESTAQUE)
        topo += 32

        surf_tit = self.fontes.grande.render("Desafio Astronômico", True, COR_DESTAQUE)
        tela.blit(surf_tit, surf_tit.get_rect(center=(cx, topo)))
        topo += 34

        surf_sub = self.fontes.pequena.render(
            "10 questões interativas para testar seus conhecimentos sobre o Sistema Solar!",
            True,
            COR_TEXTO_SECUNDARIO,
        )
        tela.blit(surf_sub, surf_sub.get_rect(center=(cx, topo)))
        topo += 48

        # Campo Nome do Aluno
        largura_campo = min(480, rect_p.width - 80)
        x_campo = cx - largura_campo // 2

        desenhar_usuario(tela, (x_campo + 10, topo + 8), tamanho=16, cor=COR_DESTAQUE)
        lbl_nome = self.fontes.pequena.render("Seu Nome Completo:", True, COR_TEXTO)
        tela.blit(lbl_nome, (x_campo + 24, topo))
        topo += 26

        ret_nome = pygame.Rect(x_campo, topo, largura_campo, 46)
        self._ret_botoes["campo_nome"] = ret_nome
        borda_cor = COR_DESTAQUE if self.campo_foco == "nome" else COR_TEXTO_SECUNDARIO
        pygame.draw.rect(tela, (20, 24, 40), ret_nome, border_radius=8)
        pygame.draw.rect(tela, borda_cor, ret_nome, width=2, border_radius=8)

        texto_exibido = self.nome_aluno if self.nome_aluno else "Digite seu nome..."
        cor_texto_input = COR_TEXTO if self.nome_aluno else COR_TEXTO_SECUNDARIO
        surf_nome = self.fontes.media.render(texto_exibido, True, cor_texto_input)
        tela.blit(surf_nome, (x_campo + 14, topo + 12))

        if self.campo_foco == "nome" and self.cursor_visivel and self.nome_aluno:
            x_cursor = x_campo + 14 + surf_nome.get_width() + 2
            pygame.draw.line(tela, COR_DESTAQUE, (x_cursor, topo + 10), (x_cursor, topo + 36), 2)
        topo += 65

        # Campo Série (sem "Turma": a turma agora é o campo Sala, abaixo — os
        # dois juntos num rótulo só era o que impedia agrupar por sala).
        topo = self._desenhar_seletor(
            tela, "serie", "Sua Série:", OPCOES_SERIE[self.indice_serie],
            x_campo, topo, largura_campo, cx,
        )

        # Campo Sala
        topo = self._desenhar_seletor(
            tela, "sala", "Sua Sala:", OPCOES_SALA[self.indice_sala],
            x_campo, topo, largura_campo, cx,
        )

        # Botão Iniciar Atividade
        ret_iniciar = pygame.Rect(x_campo, topo, largura_campo, 52)
        self._ret_botoes["btn_iniciar"] = ret_iniciar
        pygame.draw.rect(tela, (40, 110, 225), ret_iniciar, border_radius=10)
        pygame.draw.rect(tela, (90, 160, 255), ret_iniciar, width=2, border_radius=10)

        desenhar_lapis(tela, (ret_iniciar.centerx - 110, ret_iniciar.centery), tamanho=20, cor=(255, 255, 255))
        surf_btn = self.fontes.media.render("Iniciar Atividade (ENTER)", True, (255, 255, 255))
        tela.blit(surf_btn, (ret_iniciar.centerx - 90, ret_iniciar.centery - 12))

        # Dica de rodapé
        surf_dica = self.fontes.mini.render(
            "TAB alterna campos | setas mudam série e sala | ESC cancela",
            True,
            COR_TEXTO_SECUNDARIO,
        )
        tela.blit(surf_dica, surf_dica.get_rect(center=(cx, rect_p.bottom - 25)))

    def _desenhar_seletor(
        self,
        tela: pygame.Surface,
        campo: str,
        rotulo: str,
        valor: str,
        x_campo: int,
        topo: int,
        largura_campo: int,
        cx: int,
    ) -> int:
        """Desenha um seletor ◀ valor ▶ e devolve o y logo abaixo dele.

        Série e sala têm exatamente o mesmo comportamento, e duplicar o bloco
        de desenho faria os dois divergirem no primeiro ajuste de layout. As
        chaves dos retângulos seguem o padrão ``btn_<campo>_esq/dir``, que é o
        que o tratador de clique já espera.
        """
        desenhar_chapeu_formatura(tela, (x_campo + 10, topo + 8), tamanho=16, cor=COR_DESTAQUE)
        tela.blit(self.fontes.pequena.render(rotulo, True, COR_TEXTO), (x_campo + 24, topo))
        topo += 26

        ret = pygame.Rect(x_campo, topo, largura_campo, 46)
        borda = COR_DESTAQUE if self.campo_foco == campo else COR_TEXTO_SECUNDARIO
        pygame.draw.rect(tela, (20, 24, 40), ret, border_radius=8)
        pygame.draw.rect(tela, borda, ret, width=2, border_radius=8)

        ret_esq = pygame.Rect(x_campo + 6, topo + 6, 34, 34)
        self._ret_botoes[f"btn_{campo}_esq"] = ret_esq
        pygame.draw.rect(tela, (35, 42, 68), ret_esq, border_radius=6)
        self._desenhar_seta(tela, ret_esq.center, para_direita=False)

        surf_valor = self.fontes.media.render(valor, True, COR_DESTAQUE)
        tela.blit(surf_valor, surf_valor.get_rect(center=(cx, topo + 23)))

        ret_dir = pygame.Rect(x_campo + largura_campo - 40, topo + 6, 34, 34)
        self._ret_botoes[f"btn_{campo}_dir"] = ret_dir
        pygame.draw.rect(tela, (35, 42, 68), ret_dir, border_radius=6)
        self._desenhar_seta(tela, ret_dir.center, para_direita=True)

        return topo + 62

    @staticmethod
    def _desenhar_seta(
        tela: pygame.Surface, centro: tuple[int, int], para_direita: bool
    ) -> None:
        """Triângulo desenhado, em vez do caractere "◀"/"▶".

        As setas eram renderizadas como texto e saíam como quadrados vazios: a
        fonte padrão do sistema (via SysFont) não traz esses glifos em todas as
        instalações do Windows. Um polígono não depende de fonte nenhuma.
        """
        x, y = centro
        largura, altura = 5, 7
        sinal = 1 if para_direita else -1
        pygame.draw.polygon(
            tela,
            COR_TEXTO,
            [
                (x - sinal * largura, y - altura),
                (x - sinal * largura, y + altura),
                (x + sinal * largura, y),
            ],
        )

    def _desenhar_questoes(self, tela: pygame.Surface, rect_p: pygame.Rect) -> None:
        """Desenha a tela de questões com progresso e opções."""
        q = QUESTOES_QUIZ[self.indice_questao]
        total = len(QUESTOES_QUIZ)
        topo = rect_p.y + 30
        cx = rect_p.centerx

        # Barra de Progresso
        largura_barra = rect_p.width - 80
        x_barra = rect_p.x + 40
        ret_bg_barra = pygame.Rect(x_barra, topo, largura_barra, 8)
        pygame.draw.rect(tela, (25, 30, 50), ret_bg_barra, border_radius=4)

        pct = (self.indice_questao + 1) / total
        ret_progresso = pygame.Rect(x_barra, topo, int(largura_barra * pct), 8)
        pygame.draw.rect(tela, COR_DESTAQUE, ret_progresso, border_radius=4)
        topo += 22

        # Linha de Informações: Questão X de 10 e Cronômetro
        surf_num = self.fontes.pequena.render(
            f"Questão {self.indice_questao + 1} de {total}", True, COR_DESTAQUE
        )
        tela.blit(surf_num, (x_barra, topo))

        segs = int(time.time() - self.tempo_inicio)
        mins = segs // 60
        segs_rest = segs % 60
        surf_timer = self.fontes.pequena.render(
            f"Tempo: {mins:02d}:{segs_rest:02d}", True, COR_TEXTO_SECUNDARIO
        )
        x_timer = x_barra + largura_barra - surf_timer.get_width()
        desenhar_cronometro(tela, (x_timer - 12, topo + 9), tamanho=15, cor=COR_TEXTO_SECUNDARIO)
        tela.blit(surf_timer, (x_timer, topo))
        topo += 35

        # Título da Questão (com quebra de linha se necessário)
        linhas_pergunta = self._quebrar_texto(q.pergunta, self.fontes.media, largura_barra)
        for linha in linhas_pergunta:
            surf_linha = self.fontes.media.render(linha, True, COR_TEXTO)
            tela.blit(surf_linha, (x_barra, topo))
            topo += 28
        topo += 12

        # 4 Opções
        letras = ["A", "B", "C", "D"]
        selecao = self.respostas[self.indice_questao]

        mouse_pos = pygame.mouse.get_pos()
        for idx, opt_texto in enumerate(q.opcoes):
            ret_opt = pygame.Rect(x_barra, topo, largura_barra, 46)
            self._ret_opcoes.append(ret_opt)

            eh_selecionada = selecao == idx
            eh_hover = ret_opt.collidepoint(mouse_pos)

            if eh_selecionada:
                cor_fundo = (30, 60, 100)
                cor_borda = COR_DESTAQUE
                cor_letra_bg = COR_DESTAQUE
                cor_letra_fg = (6, 7, 16)
            elif eh_hover:
                cor_fundo = (25, 32, 55)
                cor_borda = (80, 140, 200)
                cor_letra_bg = (50, 65, 95)
                cor_letra_fg = COR_TEXTO
            else:
                cor_fundo = (16, 20, 36)
                cor_borda = (40, 48, 75)
                cor_letra_bg = (30, 38, 60)
                cor_letra_fg = COR_TEXTO_SECUNDARIO

            pygame.draw.rect(tela, cor_fundo, ret_opt, border_radius=8)
            pygame.draw.rect(tela, cor_borda, ret_opt, width=2 if eh_selecionada else 1, border_radius=8)

            # Círculo com a letra A, B, C, D
            ret_circ = pygame.Rect(ret_opt.x + 10, ret_opt.y + 7, 32, 32)
            pygame.draw.rect(tela, cor_letra_bg, ret_circ, border_radius=16)
            surf_l = self.fontes.pequena.render(letras[idx], True, cor_letra_fg)
            tela.blit(surf_l, surf_l.get_rect(center=ret_circ.center))

            # Texto da opção
            surf_opt = self.fontes.pequena.render(opt_texto, True, COR_TEXTO)
            tela.blit(surf_opt, (ret_opt.x + 52, ret_opt.y + 14))

            topo += 54

        # Botão Avançar / Finalizar
        topo += 8
        largura_btn = 260
        ret_avancar = pygame.Rect(cx - largura_btn // 2, topo, largura_btn, 48)
        self._ret_botoes["btn_avancar"] = ret_avancar

        tem_resposta = selecao is not None
        cor_btn = (40, 120, 230) if tem_resposta else (25, 45, 80)
        cor_txt = (255, 255, 255) if tem_resposta else COR_TEXTO_SECUNDARIO
        pygame.draw.rect(tela, cor_btn, ret_avancar, border_radius=8)
        pygame.draw.rect(tela, (80, 160, 255) if tem_resposta else (50, 70, 100), ret_avancar, width=2, border_radius=8)

        texto_btn = (
            "Finalizar Atividade (ENTER)"
            if self.indice_questao == total - 1
            else "Próxima Questão (ENTER) ▶"
        )
        surf_btn = self.fontes.pequena.render(texto_btn, True, cor_txt)
        tela.blit(surf_btn, surf_btn.get_rect(center=ret_avancar.center))

        # Botão Anterior (se não for a primeira)
        if self.indice_questao > 0:
            ret_voltar = pygame.Rect(x_barra, topo, 120, 48)
            self._ret_botoes["btn_voltar_q"] = ret_voltar
            pygame.draw.rect(tela, (20, 26, 45), ret_voltar, border_radius=8)
            pygame.draw.rect(tela, (45, 55, 85), ret_voltar, width=1, border_radius=8)
            surf_voltar = self.fontes.pequena.render("◀ Anterior", True, COR_TEXTO_SECUNDARIO)
            tela.blit(surf_voltar, surf_voltar.get_rect(center=ret_voltar.center))

        # Rodapé com dicas de teclas
        surf_dica = self.fontes.mini.render(
            "Use as teclas 1–4 ou A–D para escolher | ENTER para avançar | ESC para sair",
            True,
            COR_TEXTO_SECUNDARIO,
        )
        tela.blit(surf_dica, surf_dica.get_rect(center=(cx, rect_p.bottom - 22)))

    def _desenhar_resultado(self, tela: pygame.Surface, rect_p: pygame.Rect) -> None:
        """Desenha a tela de resultado, pontuação e gabarito."""
        cx = rect_p.centerx
        topo = rect_p.y + 25

        # Ícone Troféu Vetorial Estilo Bootstrap
        desenhar_trofeu(tela, (cx, topo), tamanho=38, cor=COR_AVISO)
        topo += 32

        # Título
        surf_tit = self.fontes.grande.render("Atividade Concluída!", True, COR_SUCESSO)
        tela.blit(surf_tit, surf_tit.get_rect(center=(cx, topo)))
        topo += 28

        # Mesma composição da mensagem da web ("nome — série, sala X"): é por
        # série E sala que o aluno vai se procurar no ranking.
        serie = OPCOES_SERIE[self.indice_serie]
        sala = OPCOES_SALA[self.indice_sala]
        surf_sub = self.fontes.pequena.render(
            f"Aluno: {self.nome_aluno} — {serie}, sala {sala}",
            True,
            COR_TEXTO_SECUNDARIO,
        )
        tela.blit(surf_sub, surf_sub.get_rect(center=(cx, topo)))
        topo += 32

        # 3 Blocos de Placar (Pontuação, Acertos, Tempo)
        largura_bloco = 180
        espaco_blocos = 16
        largura_total_blocos = 3 * largura_bloco + 2 * espaco_blocos
        x_bloco_inicio = cx - largura_total_blocos // 2

        blocos = [
            ("PONTUAÇÃO", f"{self.pontuacao} pts", COR_DESTAQUE, "estrela"),
            ("ACERTOS", f"{self.acertos} / 10", COR_SUCESSO if self.acertos >= 6 else COR_AVISO, "check"),
            ("TEMPO", f"{int(self.tempo_total_segundos)}s", COR_TEXTO, "tempo"),
        ]

        for i, (rotulo, valor, cor_val, tipo_ico) in enumerate(blocos):
            x_b = x_bloco_inicio + i * (largura_bloco + espaco_blocos)
            ret_b = pygame.Rect(x_b, topo, largura_bloco, 60)
            pygame.draw.rect(tela, (20, 25, 45), ret_b, border_radius=8)
            pygame.draw.rect(tela, (45, 55, 85), ret_b, width=1, border_radius=8)

            # Ícone do bloco
            if tipo_ico == "estrela":
                desenhar_estrela(tela, (ret_b.x + 22, ret_b.y + 16), tamanho=14, cor=COR_DESTAQUE)
            elif tipo_ico == "check":
                desenhar_check(tela, (ret_b.x + 22, ret_b.y + 16), tamanho=14, cor=cor_val)
            elif tipo_ico == "tempo":
                desenhar_cronometro(tela, (ret_b.x + 22, ret_b.y + 16), tamanho=14, cor=COR_TEXTO_SECUNDARIO)

            surf_rot = self.fontes.mini.render(rotulo, True, COR_TEXTO_SECUNDARIO)
            tela.blit(surf_rot, (ret_b.x + 36, ret_b.y + 9))

            surf_v = self.fontes.media.render(valor, True, cor_val)
            tela.blit(surf_v, surf_v.get_rect(center=(ret_b.centerx, ret_b.y + 40)))
        topo += 74

        # Mensagem de Envio ao Ranking
        if self.status_envio_ranking == "sucesso":
            msg_rank = "Pontuação salva no Ranking com sucesso!"
            cor_rank = COR_SUCESSO
        elif self.status_envio_ranking == "erro":
            msg_rank = "Falha ao conectar ao servidor de ranking."
            cor_rank = COR_ERRO
        elif self.status_envio_ranking == "enviando":
            msg_rank = "Enviando pontuação para o servidor..."
            cor_rank = COR_AVISO
        else:
            msg_rank = ""
            cor_rank = COR_TEXTO_SECUNDARIO

        if msg_rank:
            surf_msg = self.fontes.pequena.render(msg_rank, True, cor_rank)
            tela.blit(surf_msg, surf_msg.get_rect(center=(cx, topo)))
            topo += 28

        # Botões de Ação
        largura_btn_acao = 220
        x_btn1 = cx - largura_btn_acao - 10
        x_btn2 = cx + 10

        # Botão Enviar ao Ranking
        ret_rank = pygame.Rect(x_btn1, topo, largura_btn_acao, 44)
        self._ret_botoes["btn_ranking"] = ret_rank
        pode_enviar = self.status_envio_ranking != "sucesso"
        cor_bg_rank = (190, 120, 20) if pode_enviar else (40, 50, 70)
        pygame.draw.rect(tela, cor_bg_rank, ret_rank, border_radius=8)
        
        desenhar_nuvem_upload(tela, (ret_rank.x + 24, ret_rank.centery), tamanho=18, cor=(255, 255, 255))
        txt_rank = "Salvar no Ranking" if pode_enviar else "Salvo no Ranking"
        surf_btn_r = self.fontes.pequena.render(txt_rank, True, (255, 255, 255))
        tela.blit(surf_btn_r, (ret_rank.x + 44, ret_rank.centery - 10))

        # Botão Refazer Atividade
        ret_reinicio = pygame.Rect(x_btn2, topo, largura_btn_acao, 44)
        self._ret_botoes["btn_reiniciar"] = ret_reinicio
        pygame.draw.rect(tela, (30, 40, 70), ret_reinicio, border_radius=8)
        pygame.draw.rect(tela, (60, 80, 120), ret_reinicio, width=1, border_radius=8)
        
        desenhar_recarregar(tela, (ret_reinicio.x + 24, ret_reinicio.centery), tamanho=18, cor=COR_TEXTO)
        surf_btn_re = self.fontes.pequena.render("Refazer Atividade", True, COR_TEXTO)
        tela.blit(surf_btn_re, (ret_reinicio.x + 44, ret_reinicio.centery - 10))
        topo += 56

        # Área de Gabarito / Correção das Questões
        lbl_gab = self.fontes.pequena.render("Resumo das Respostas (Role para ver mais):", True, COR_DESTAQUE)
        tela.blit(lbl_gab, (rect_p.x + 40, topo))
        topo += 22

        altura_gabarito = max(100, rect_p.bottom - topo - 35)
        rect_area_gab = pygame.Rect(rect_p.x + 35, topo, rect_p.width - 70, altura_gabarito)

        # Superfície com clipping para rolagem do gabarito
        surf_gab = pygame.Surface((rect_area_gab.width, rect_area_gab.height), pygame.SRCALPHA)
        y_item = 4 - self.offset_scroll_gabarito

        for idx, q in enumerate(QUESTOES_QUIZ):
            resp = self.respostas[idx]
            acertou = resp == q.correta

            ret_item = pygame.Rect(0, y_item, rect_area_gab.width, 42)
            cor_bg_item = (20, 35, 25) if acertou else (38, 20, 20)
            cor_borda_item = COR_SUCESSO if acertou else COR_ERRO

            pygame.draw.rect(surf_gab, cor_bg_item, ret_item, border_radius=6)
            pygame.draw.rect(surf_gab, cor_borda_item, ret_item, width=1, border_radius=6)

            if acertou:
                desenhar_check(surf_gab, (20, y_item + 21), tamanho=16, cor=COR_SUCESSO)
            else:
                desenhar_x(surf_gab, (20, y_item + 21), tamanho=14, cor=COR_ERRO)

            surf_s = self.fontes.pequena.render(f"Q{idx+1}:", True, cor_borda_item)
            surf_gab.blit(surf_s, (36, y_item + 12))

            resp_str = q.opcoes[resp] if resp is not None else "Nenhuma"
            if acertou:
                txt_item = f"{resp_str} (Correto)"
            else:
                txt_item = f"Sua resposta: {resp_str}  |  Certa: {q.opcoes[q.correta]}"

            surf_txt = self.fontes.mini.render(txt_item, True, COR_TEXTO)
            surf_gab.blit(surf_txt, (82, y_item + 14))

            y_item += 48

        tela.blit(surf_gab, rect_area_gab.topleft)

        # Barra de Rolagem Visual (Scrollbar)
        altura_total_conteudo = len(QUESTOES_QUIZ) * 48
        if altura_total_conteudo > altura_gabarito:
            x_scroll = rect_area_gab.right - 8
            ret_trilho = pygame.Rect(x_scroll, rect_area_gab.y, 6, altura_gabarito)
            pygame.draw.rect(tela, (25, 30, 50), ret_trilho, border_radius=3)

            tam_polegar = max(24, int(altura_gabarito * (altura_gabarito / altura_total_conteudo)))
            max_offset = altura_total_conteudo - altura_gabarito
            progresso_scroll = self.offset_scroll_gabarito / max(1, max_offset)
            y_polegar = rect_area_gab.y + int((altura_gabarito - tam_polegar) * progresso_scroll)
            ret_polegar = pygame.Rect(x_scroll, y_polegar, 6, tam_polegar)
            pygame.draw.rect(tela, COR_DESTAQUE, ret_polegar, border_radius=3)

        # Dica final
        surf_dica = self.fontes.mini.render(
            "Pressione ESC para voltar ao Simulador do Sistema Solar", True, COR_TEXTO_SECUNDARIO
        )
        tela.blit(surf_dica, surf_dica.get_rect(center=(cx, rect_p.bottom - 16)))

    def _quebrar_texto(
        self, texto: str, fonte: pygame.font.Font, largura_max: int
    ) -> list[str]:
        """Divide uma string longa em múltiplas linhas para não ultrapassar a largura."""
        palavras = texto.split(" ")
        linhas: list[str] = []
        linha_atual = ""

        for p in palavras:
            teste = f"{linha_atual} {p}".strip()
            if fonte.size(teste)[0] <= largura_max:
                linha_atual = teste
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = p
        if linha_atual:
            linhas.append(linha_atual)
        return linhas
