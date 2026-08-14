"""Ícones vetoriais de alta fidelidade estilo Bootstrap Icons para Pygame.

Desenha ícones com antialiasing e geometria precisa, eliminando dependência
de emojis que falham ou viram quadrados pretos (tofu) no Windows.
"""

from __future__ import annotations

import math
import pygame


def desenhar_trofeu(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (255, 215, 0),
) -> None:
    """Desenha o ícone bi-trophy-fill estilo Bootstrap."""
    cx, cy = centro
    raio = tamanho / 2

    surf = pygame.Surface((tamanho * 2, tamanho * 2), pygame.SRCALPHA)
    ox, oy = tamanho, tamanho

    # Taça (Copa superior)
    w_copa = tamanho * 0.7
    h_copa = tamanho * 0.55
    ret_copa = pygame.Rect(ox - w_copa / 2, oy - raio + 2, w_copa, h_copa)
    pygame.draw.rect(
        surf,
        cor,
        ret_copa,
        border_bottom_left_radius=int(w_copa / 2),
        border_bottom_right_radius=int(w_copa / 2),
    )

    # Alças laterais da taça
    w_alca = tamanho * 0.22
    h_alca = tamanho * 0.35
    alca_esq = pygame.Rect(ox - w_copa / 2 - w_alca + 2, oy - raio + 4, w_alca + 2, h_alca)
    alca_dir = pygame.Rect(ox + w_copa / 2 - 4, oy - raio + 4, w_alca + 2, h_alca)
    pygame.draw.arc(surf, cor, alca_esq, math.pi * 0.5, math.pi * 1.5, max(2, int(tamanho * 0.08)))
    pygame.draw.arc(surf, cor, alca_dir, -math.pi * 0.5, math.pi * 0.5, max(2, int(tamanho * 0.08)))

    # Haste central
    w_haste = max(3, int(tamanho * 0.14))
    h_haste = tamanho * 0.25
    ret_haste = pygame.Rect(ox - w_haste / 2, oy - raio + h_copa, w_haste, h_haste)
    pygame.draw.rect(surf, cor, ret_haste)

    # Base do troféu
    w_base = tamanho * 0.65
    h_base = max(3, int(tamanho * 0.15))
    ret_base = pygame.Rect(ox - w_base / 2, oy + raio - h_base - 1, w_base, h_base)
    pygame.draw.rect(surf, cor, ret_base, border_radius=2)

    tela.blit(surf, (cx - ox, cy - oy))


def desenhar_estrela(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (255, 200, 0),
) -> None:
    """Desenha o ícone bi-star-fill (estrela de 5 pontas)."""
    cx, cy = centro
    raio_ext = tamanho * 0.5
    raio_int = tamanho * 0.22
    pontos = []

    for i in range(10):
        angulo = -math.pi / 2 + i * (math.pi / 5)
        raio = raio_ext if i % 2 == 0 else raio_int
        x = cx + math.cos(angulo) * raio
        y = cy + math.sin(angulo) * raio
        pontos.append((x, y))

    pygame.draw.polygon(tela, cor, pontos)


def desenhar_cronometro(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (200, 210, 230),
) -> None:
    """Desenha o ícone bi-stopwatch estilo Bootstrap."""
    cx, cy = centro
    raio = tamanho * 0.38
    cy_corpo = cy + int(tamanho * 0.08)

    # Corpo circular
    pygame.draw.circle(tela, cor, (cx, cy_corpo), int(raio), width=max(2, int(tamanho * 0.09)))

    # Botão superior (topo do cronômetro)
    w_btn = max(4, int(tamanho * 0.28))
    h_btn = max(2, int(tamanho * 0.1))
    pygame.draw.rect(tela, cor, (cx - w_btn // 2, cy - int(tamanho * 0.45), w_btn, h_btn), border_radius=1)
    pygame.draw.line(tela, cor, (cx, cy - int(tamanho * 0.45)), (cx, cy_corpo - int(raio)), max(2, int(tamanho * 0.08)))

    # Ponteiros do relógio
    pygame.draw.line(tela, cor, (cx, cy_corpo), (cx, cy_corpo - int(raio * 0.55)), max(2, int(tamanho * 0.08)))
    pygame.draw.line(tela, cor, (cx, cy_corpo), (cx + int(raio * 0.45), cy_corpo), max(2, int(tamanho * 0.08)))


def desenhar_check(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (74, 222, 128),
) -> None:
    """Desenha o ícone bi-check-lg (símbolo de correto)."""
    cx, cy = centro
    escala = tamanho / 24.0
    espessura = max(2, int(3 * escala))

    p1 = (cx - int(7 * escala), cy)
    p2 = (cx - int(2 * escala), cy + int(6 * escala))
    p3 = (cx + int(8 * escala), cy - int(6 * escala))

    pygame.draw.lines(tela, cor, False, [p1, p2, p3], espessura)


def desenhar_x(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (248, 113, 113),
) -> None:
    """Desenha o ícone bi-x-lg (símbolo de incorreto / fechar)."""
    cx, cy = centro
    d = int(tamanho * 0.3)
    espessura = max(2, int(tamanho * 0.12))

    pygame.draw.line(tela, cor, (cx - d, cy - d), (cx + d, cy + d), espessura)
    pygame.draw.line(tela, cor, (cx + d, cy - d), (cx - d, cy + d), espessura)


def desenhar_usuario(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (255, 255, 255),
) -> None:
    """Desenha o ícone bi-person-fill."""
    cx, cy = centro
    escala = tamanho / 24.0

    # Cabeça
    raio_cabeca = int(4.5 * escala)
    cy_cabeca = cy - int(4 * escala)
    pygame.draw.circle(tela, cor, (cx, cy_cabeca), raio_cabeca)

    # Ombros / Tronco
    w_corpo = int(14 * escala)
    h_corpo = int(8 * escala)
    ret_corpo = pygame.Rect(cx - w_corpo // 2, cy + int(2 * escala), w_corpo, h_corpo)
    pygame.draw.rect(
        tela,
        cor,
        ret_corpo,
        border_top_left_radius=w_corpo // 2,
        border_top_right_radius=w_corpo // 2,
    )


def desenhar_chapeu_formatura(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (255, 255, 255),
) -> None:
    """Desenha o ícone bi-mortarboard-fill (Chapéu de Formatura / Série)."""
    cx, cy = centro
    escala = tamanho / 24.0

    # Losango superior
    p1 = (cx, cy - int(6 * escala))
    p2 = (cx + int(10 * escala), cy - int(1 * escala))
    p3 = (cx, cy + int(4 * escala))
    p4 = (cx - int(10 * escala), cy - int(1 * escala))
    pygame.draw.polygon(tela, cor, [p1, p2, p3, p4])

    # Base do chapéu
    p_b1 = (cx - int(6 * escala), cy + int(2 * escala))
    p_b2 = (cx - int(6 * escala), cy + int(7 * escala))
    p_b3 = (cx + int(6 * escala), cy + int(7 * escala))
    p_b4 = (cx + int(6 * escala), cy + int(2 * escala))
    pygame.draw.polygon(tela, cor, [p_b1, p_b2, p_b3, p_b4])

    # Fita lateral / Pompom
    pygame.draw.line(
        tela,
        cor,
        (cx + int(8 * escala), cy - int(1 * escala)),
        (cx + int(8 * escala), cy + int(6 * escala)),
        max(1, int(2 * escala)),
    )


def desenhar_lapis(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (255, 255, 255),
) -> None:
    """Desenha o ícone bi-pencil-square."""
    cx, cy = centro
    escala = tamanho / 24.0
    esp = max(2, int(2 * escala))

    # Caixa externa
    w_box = int(16 * escala)
    ret_box = pygame.Rect(cx - w_box // 2, cy - w_box // 2, w_box, w_box)
    pygame.draw.rect(tela, cor, ret_box, width=esp, border_radius=int(3 * escala))

    # Linha diagonal do lápis
    p1 = (cx - int(2 * escala), cy + int(2 * escala))
    p2 = (cx + int(5 * escala), cy - int(5 * escala))
    pygame.draw.line(tela, cor, p1, p2, esp + 1)


def desenhar_recarregar(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (255, 255, 255),
) -> None:
    """Desenha o ícone bi-arrow-clockwise (Refazer)."""
    cx, cy = centro
    raio = int(tamanho * 0.38)
    esp = max(2, int(tamanho * 0.09))

    ret = pygame.Rect(cx - raio, cy - raio, raio * 2, raio * 2)
    pygame.draw.arc(tela, cor, ret, 0.5, math.pi * 1.8, esp)

    # Seta no final do arco
    p_topo = (cx + raio - 2, cy - 2)
    p_esq = (p_topo[0] - int(4 * (tamanho / 24.0)), p_topo[1] - int(5 * (tamanho / 24.0)))
    p_dir = (p_topo[0] + int(4 * (tamanho / 24.0)), p_topo[1] - int(5 * (tamanho / 24.0)))
    pygame.draw.polygon(tela, cor, [p_topo, p_esq, p_dir])


def desenhar_nuvem_upload(
    tela: pygame.Surface,
    centro: tuple[int, int],
    tamanho: int = 24,
    cor: tuple[int, int, int] = (255, 255, 255),
) -> None:
    """Desenha o ícone bi-cloud-arrow-up (Salvar no Ranking)."""
    cx, cy = centro
    escala = tamanho / 24.0
    esp = max(2, int(2 * escala))

    # Nuvem base
    w_nuvem = int(16 * escala)
    ret_n = pygame.Rect(cx - w_nuvem // 2, cy - int(3 * escala), w_nuvem, int(9 * escala))
    pygame.draw.rect(tela, cor, ret_n, width=esp, border_radius=int(4 * escala))

    # Seta para cima
    p_topo = (cx, cy - int(6 * escala))
    p_baixo = (cx, cy + int(3 * escala))
    pygame.draw.line(tela, cor, p_topo, p_baixo, esp)

    p_esq = (cx - int(3 * escala), cy - int(3 * escala))
    p_dir = (cx + int(3 * escala), cy - int(3 * escala))
    pygame.draw.line(tela, cor, p_topo, p_esq, esp)
    pygame.draw.line(tela, cor, p_topo, p_dir, esp)
