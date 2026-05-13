"""Sprites procedurales dibujados con pygame.draw.

Cada función draw_* acepta una superficie pygame y coordenadas,
y dibuja el sprite en ella. Sin imports de dominio — solo pygame y paleta.

Todas las funciones son puras respecto al estado del juego.
La escala y posición son responsabilidad del llamador.
"""

from __future__ import annotations

import math

import pygame

from donkeykong.presentation import palette as P  # noqa: N812

# Alias locales para brevedad
_r = pygame.draw.rect
_c = pygame.draw.circle
_p = pygame.draw.polygon
_l = pygame.draw.line


def _rect(
    surf: pygame.Surface,
    color: tuple[int, int, int],
    x: int,
    y: int,
    w: int,
    h: int,
    radius: int = 0,
) -> None:
    pygame.draw.rect(surf, color, (x, y, w, h), border_radius=radius)


def draw_girder(
    surf: pygame.Surface,
    x_left: float,
    x_right: float,
    y: float,
    height: int = 14,
) -> None:
    """Dibuja una viga horizontal con highlight, sombra y remaches.

    Args:
        surf: superficie destino.
        x_left, x_right: extremos de la viga.
        y: Y de la superficie superior de la viga.
        height: altura visual de la viga en píxeles.
    """
    xl, xr, yi, h = int(x_left), int(x_right), int(y), height
    _rect(surf, P.GIRDER_SH, xl, yi + 3, xr - xl, h)
    _rect(surf, P.GIRDER, xl, yi, xr - xl, h - 2)
    _rect(surf, P.GIRDER_HI, xl, yi, xr - xl, 3)
    for rx in range(xl + 14, xr - 10, 28):
        _c(surf, P.GIRDER_HI, (rx, yi + h // 2), 3)
        _c(surf, P.GIRDER_SH, (rx + 1, yi + h // 2 + 1), 2)


def draw_ladder(
    surf: pygame.Surface,
    cx: float,
    y_top: float,
    y_bottom: float,
    width: int = 16,
) -> None:
    """Dibuja una escalera con peldaños y sombra.

    Args:
        surf: superficie destino.
        cx: centro X de la escalera.
        y_top, y_bottom: límites verticales.
        width: ancho total en píxeles.
    """
    cxi, yt, yb = int(cx), int(y_top), int(y_bottom)
    hw = width // 2
    # Montantes
    _rect(surf, P.LADDER_S, cxi - hw - 1, yt, 5, yb - yt)
    _rect(surf, P.LADDER_S, cxi + hw - 3, yt, 5, yb - yt)
    _rect(surf, P.LADDER_C, cxi - hw, yt, 4, yb - yt)
    _rect(surf, P.LADDER_C, cxi + hw - 2, yt, 4, yb - yt)
    # Peldaños
    for ry in range(yt + 4, yb, 14):
        _rect(surf, P.LADDER_S, cxi - hw, ry + 1, width, 3)
        _rect(surf, P.LADDER_C, cxi - hw, ry, width, 3)


def draw_mario(
    surf: pygame.Surface,
    cx: float,
    by: float,
    frame: int = 0,
    facing: int = 1,
    state: str = "walk",
    dead_anim: int = 0,
    scale: float = 1.0,
) -> None:
    """Dibuja a Mario (32x44 px nativos, escalable).

    Args:
        surf: superficie destino.
        cx: centro X (píxeles).
        by: pies Y (píxeles).
        frame: frame de animación actual.
        facing: +1 derecha, -1 izquierda.
        state: 'walk' | 'jump' | 'climb' | 'dead' | 'idle'.
        dead_anim: tick de animación de muerte (para rotación).
        scale: escala del sprite (1.0 = tamaño completo).
    """
    sw, sh = 32, 44

    s = pygame.Surface((sw, sh), pygame.SRCALPHA)
    _draw_mario_on(s, frame, facing, state, dead_anim)

    if state == "dead":
        angle = dead_anim * 18
        rs = pygame.transform.rotate(s, float(angle))
        surf.blit(rs, (int(cx) - rs.get_width() // 2, int(by) - rs.get_height() // 2))
        return

    if facing == -1:
        s = pygame.transform.flip(s, True, False)

    if scale != 1.0:
        ns = (int(sw * scale), int(sh * scale))
        s = pygame.transform.scale(s, ns)
        surf.blit(s, (int(cx) - ns[0] // 2, int(by) - ns[1]))
    else:
        surf.blit(s, (int(cx) - sw // 2, int(by) - sh))


def _draw_mario_on(
    s: pygame.Surface,
    frame: int,
    facing: int,
    state: str,
    dead_anim: int,
) -> None:
    """Dibuja Mario dentro del surface interno (32x44)."""
    # Sombrero
    _rect(s, P.RED_HAT, 5, 0, 22, 8)
    _rect(s, P.RED_HAT, 1, 6, 30, 5)
    # Cabeza
    _rect(s, P.SKIN, 7, 9, 18, 14)
    ex = 21 if facing == 1 else 7
    _rect(s, P.BLACK, ex, 12, 4, 5)
    _rect(s, P.WHITE, ex + 1, 13, 2, 2)
    _rect(s, P.SKIN, 13, 19, 6, 4)
    _rect(s, P.BROWN, 7, 19, 7, 3)
    _rect(s, P.BROWN, 18, 19, 7, 3)

    match state:
        case "climb":
            cf = frame % 2
            if cf == 0:
                _rect(s, P.RED, 0, 22, 10, 7)
                _rect(s, P.RED, 22, 28, 10, 7)
            else:
                _rect(s, P.RED, 0, 28, 10, 7)
                _rect(s, P.RED, 22, 22, 10, 7)
            _rect(s, P.RED, 6, 22, 20, 13)
            _rect(s, P.BLUE, 9, 22, 14, 13)
            _rect(s, P.RED, 6, 22, 4, 8)
            _rect(s, P.RED, 22, 22, 4, 8)
            _rect(s, P.BLUE, 5, 34, 10, 8)
            _rect(s, P.BLUE, 17, 34, 10, 8)
            _rect(s, P.BROWN, 3, 40, 13, 4)
            _rect(s, P.BROWN, 16, 40, 13, 4)

        case "jump":
            _rect(s, P.RED, 0, 20, 10, 8)
            _rect(s, P.RED, 22, 20, 10, 8)
            _rect(s, P.RED, 6, 22, 20, 12)
            _rect(s, P.BLUE, 9, 22, 14, 12)
            _rect(s, P.RED, 6, 22, 4, 8)
            _rect(s, P.RED, 22, 22, 4, 8)
            _rect(s, P.BLUE, 3, 33, 12, 8)
            _rect(s, P.BLUE, 17, 33, 12, 8)
            _rect(s, P.BROWN, 1, 39, 13, 5)
            _rect(s, P.BROWN, 18, 39, 13, 5)

        case _:  # walk / idle
            wf = frame % 2
            if wf == 0:
                _rect(s, P.RED, 0, 23, 10, 8)
                _rect(s, P.RED, 22, 27, 10, 8)
            else:
                _rect(s, P.RED, 0, 27, 10, 8)
                _rect(s, P.RED, 22, 23, 10, 8)
            _rect(s, P.RED, 6, 22, 20, 12)
            _rect(s, P.BLUE, 9, 22, 14, 12)
            _rect(s, P.RED, 6, 22, 4, 8)
            _rect(s, P.RED, 22, 22, 4, 8)
            _rect(s, P.GOLD, 10, 23, 4, 3)
            _rect(s, P.GOLD, 18, 23, 4, 3)
            if wf == 0:
                _rect(s, P.BLUE, 6, 33, 11, 10)
                _rect(s, P.BLUE, 15, 31, 11, 10)
                _rect(s, P.BROWN, 4, 41, 14, 4)
                _rect(s, P.BROWN, 14, 39, 14, 4)
            else:
                _rect(s, P.BLUE, 6, 31, 11, 10)
                _rect(s, P.BLUE, 15, 33, 11, 10)
                _rect(s, P.BROWN, 4, 39, 14, 4)
                _rect(s, P.BROWN, 14, 41, 14, 4)


def draw_dk(
    surf: pygame.Surface,
    cx: float,
    by: float,
    frame: int = 0,
    throwing: bool = False,
) -> None:
    """Dibuja a Donkey Kong (72x90 px).

    Orden de capas: brazos → cuerpo → piernas → cuello → cabeza → cara.
    La cara siempre se dibuja al final para que nada la tape.

    Args:
        surf: superficie destino.
        cx: centro X de DK.
        by: pies Y de DK.
        frame: frame de animación.
        throwing: True cuando lanza un barril.
    """
    sw, sh = 72, 90
    s = pygame.Surface((sw, sh), pygame.SRCALPHA)

    # Coordenadas fijas: cabeza centrada en (36, 20), cuerpo bajo ella
    HX, HY, HR = 36, 20, 18  # centro y radio de la cabeza
    BX, BY, BW, BH = 10, 34, 52, 38  # rect del cuerpo

    # ── 1. Brazos ────────────────────────────────────────────────────────────
    tf = frame % 2
    if throwing:
        # Brazo izquierdo abajo, derecho arriba con barril
        pygame.draw.ellipse(s, P.DK_FUR, (1, 42, 14, 28))
        pygame.draw.ellipse(s, P.DK_FUR, (57, 10, 14, 28))
        # Barril en mano derecha
        pygame.draw.ellipse(s, P.BARREL_D, (56, 4, 18, 11))
        pygame.draw.ellipse(s, P.BARREL_L, (58, 5, 14, 8))
        _rect(s, P.BARREL_D, 56, 9, 18, 3)
    else:
        ay = 30 if tf == 0 else 26
        ah = 30 if tf == 0 else 34
        pygame.draw.ellipse(s, P.DK_FUR, (1, ay, 13, ah))
        pygame.draw.ellipse(s, P.DK_FUR, (58, ay, 13, ah))

    # ── 2. Cuerpo ────────────────────────────────────────────────────────────
    pygame.draw.ellipse(s, P.DK_FUR, (BX, BY, BW, BH))
    # Panza / pecho más claro
    pygame.draw.ellipse(s, P.DK_FACE, (BX + 8, BY + 4, BW - 16, BH - 6))

    # ── 3. Piernas ───────────────────────────────────────────────────────────
    pygame.draw.ellipse(s, P.DK_FUR, (11, 62, 22, 26))
    pygame.draw.ellipse(s, P.DK_FUR, (39, 62, 22, 26))
    # Pies
    pygame.draw.ellipse(s, P.DK_INNER, (7, 78, 24, 12))
    pygame.draw.ellipse(s, P.DK_INNER, (41, 78, 24, 12))

    # ── 4. Cuello (tapa la union cuerpo-cabeza) ──────────────────────────────
    pygame.draw.ellipse(s, P.DK_FUR, (24, 26, 24, 16))

    # ── 5. Cabeza (círculo grande de piel) ────────────────────────────────────
    # Orejas primero (quedan detrás de la cabeza)
    _c(s, P.DK_FUR, (HX - 20, HY - 4), 10)
    _c(s, P.DK_INNER, (HX - 20, HY - 4), 6)
    _c(s, P.DK_FUR, (HX + 20, HY - 4), 10)
    _c(s, P.DK_INNER, (HX + 20, HY - 4), 6)
    # Cabeza
    _c(s, P.DK_FUR, (HX, HY), HR)

    # ── 6. CARA (siempre encima de todo) ─────────────────────────────────────
    # Hocico/morro grande y claro — ocupa la mitad inferior de la cabeza
    pygame.draw.ellipse(s, P.DK_FACE, (HX - 14, HY - 2, 28, 24))

    # Ojos — blancos grandes bien arriba del hocico
    EY = HY - 10  # y del borde superior de los ojos
    pygame.draw.ellipse(s, P.WHITE, (HX - 16, EY, 12, 10))
    pygame.draw.ellipse(s, P.WHITE, (HX + 4, EY, 12, 10))
    # Pupilas negras
    _c(s, P.BLACK, (HX - 10, EY + 5), 4)
    _c(s, P.BLACK, (HX + 10, EY + 5), 4)
    # Destellos blancos de vida
    _c(s, P.WHITE, (HX - 11, EY + 3), 1)
    _c(s, P.WHITE, (HX + 9, EY + 3), 1)

    # Cejas enojadas
    _l(s, P.DK_INNER, (HX - 16, EY - 2), (HX - 6, EY + 2), 3)
    _l(s, P.DK_INNER, (HX + 6, EY + 2), (HX + 16, EY - 2), 3)

    # Nariz — dos agujeros en el hocico
    _c(s, P.DK_INNER, (HX - 5, HY + 7), 3)
    _c(s, P.DK_INNER, (HX + 5, HY + 7), 3)

    # Boca y dientes blancos
    _rect(s, P.DK_INNER, HX - 11, HY + 11, 22, 5, 2)
    _rect(s, P.TOOTH, HX - 10, HY + 11, 9, 4)
    _rect(s, P.TOOTH, HX + 1, HY + 11, 9, 4)

    # Ojos rojos si está lanzando (enojado extra)
    if throwing:
        _c(s, P.RED, (HX - 10, EY + 5), 4)
        _c(s, P.RED, (HX + 10, EY + 5), 4)

    surf.blit(s, (int(cx) - sw // 2, int(by) - sh + 2))


def draw_barrel(
    surf: pygame.Surface,
    cx: float,
    by: float,
    roll_frame: int = 0,
) -> None:
    """Dibuja un barril rodando.

    Args:
        surf: superficie destino.
        cx: centro X.
        by: pies Y.
        roll_frame: contador de rotación visual.
    """
    bw, bh = 18, 14
    s = pygame.Surface((bw, bh), pygame.SRCALPHA)
    pygame.draw.rect(s, P.BARREL_D, (0, 0, bw, bh), border_radius=3)
    pygame.draw.rect(s, P.BARREL_L, (2, 1, bw - 4, bh - 2), border_radius=2)
    band_y = (roll_frame * 2) % bh
    for ky in range(-bh, bh * 2, 5):
        ry = (band_y + ky) % bh
        if 0 <= ry < bh:
            pygame.draw.rect(s, P.BARREL_D, (1, ry, bw - 2, 2))
    surf.blit(s, (int(cx) - bw // 2, int(by) - bh))


def draw_flame(
    surf: pygame.Surface,
    cx: float,
    by: float,
    frame: int = 0,
) -> None:
    """Dibuja una llama enemiga animada.

    Args:
        surf: superficie destino.
        cx: centro X.
        by: pies Y.
        frame: frame de animación para parpadeo.
    """
    x, y = int(cx), int(by)
    f = frame % 2
    _p(
        surf,
        P.FLAME_RED,
        [
            (x - 8, y),
            (x + 8, y),
            (x + 5, y - 10),
            (x, y - 16),
            (x - 5, y - 10),
        ],
    )
    _p(
        surf,
        P.FLAME_ORG,
        [
            (x - 5, y),
            (x + 5, y),
            (x + 3, y - 8 + f * 2),
            (x, y - 13 + f * 2),
            (x - 3, y - 8 + f * 2),
        ],
    )
    _p(surf, P.FLAME_YEL, [(x - 3, y), (x + 3, y), (x, y - 7 + f)])
    _rect(surf, P.BLACK, x - 5, y - 12, 3, 3)
    _rect(surf, P.BLACK, x + 2, y - 12, 3, 3)
    _rect(surf, P.WHITE, x - 4, y - 11, 1, 1)
    _rect(surf, P.WHITE, x + 3, y - 11, 1, 1)


def draw_pauline(
    surf: pygame.Surface,
    cx: float,
    by: float,
    frame: int = 0,
) -> None:
    """Dibuja a Pauline saludando (28x48 px).

    Args:
        surf: superficie destino.
        cx: centro X.
        by: pies Y.
        frame: frame de animación.
    """
    sw, sh = 28, 48
    f = frame % 2
    s = pygame.Surface((sw, sh), pygame.SRCALPHA)

    # Pelo dorado
    _c(s, P.GOLD, (14, 6), 10)
    _rect(s, P.GOLD, 4, 4, 20, 12)
    _c(s, P.GOLD, (5, 14), 5)
    _c(s, P.GOLD, (23, 14), 5)
    # Cabeza
    _rect(s, P.SKIN, 7, 8, 14, 15)
    # Ojos y sonrisa
    _rect(s, P.BLACK, 9, 12, 3, 3)
    _rect(s, P.BLACK, 16, 12, 3, 3)
    _rect(s, P.WHITE, 10, 13, 1, 1)
    _rect(s, P.WHITE, 17, 13, 1, 1)
    _rect(s, P.RED, 10, 20, 8, 2)
    # Brazos saludando
    if f == 0:
        _rect(s, P.SKIN, 0, 22, 6, 10)
        _rect(s, P.SKIN, 22, 26, 6, 10)
    else:
        _rect(s, P.SKIN, 0, 26, 6, 10)
        _rect(s, P.SKIN, 22, 22, 6, 10)
    # Vestido
    _rect(s, P.PINK, 6, 22, 16, 16)
    _p(s, P.PINK, [(3, 36), (25, 36), (27, 48), (1, 48)])
    _rect(s, P.RED, 6, 28, 16, 3)
    # Zapatos
    _rect(s, P.RED, 5, 44, 8, 4)
    _rect(s, P.RED, 15, 44, 8, 4)

    surf.blit(s, (int(cx) - sw // 2, int(by) - sh))


def draw_bonus_item(
    surf: pygame.Surface,
    cx: float,
    by: float,
    kind: str,
    frame: int = 0,
) -> None:
    """Dibuja un objeto bonus coleccionable con efecto de flotación.

    Args:
        surf: superficie destino.
        cx: centro X.
        by: pies Y.
        kind: 'purse' | 'hat' | 'umbrella'.
        frame: frame para animación de flotación.
    """
    x = int(cx)
    y = int(by) + int(math.sin(frame * 0.15) * 3)

    match kind:
        case "purse":
            _c(surf, P.PINK, (x, y - 10), 8)
            pygame.draw.rect(surf, P.BROWN, (x - 4, y - 20, 8, 6), border_radius=2)
            _c(surf, P.GOLD, (x, y - 10), 5)
            _c(surf, P.YELLOW, (x, y - 10), 3)
        case "hat":
            pygame.draw.rect(surf, P.RED, (x - 8, y - 8, 16, 6))
            pygame.draw.rect(surf, P.RED, (x - 5, y - 16, 10, 9))
            pygame.draw.rect(surf, P.YELLOW, (x - 8, y - 9, 16, 2))
        case _:  # umbrella
            pygame.draw.arc(surf, P.PINK, (x - 10, y - 20, 20, 14), 0.0, math.pi, 4)
            _l(surf, P.BROWN, (x, y - 14), (x, y - 2), 2)
            pygame.draw.arc(surf, P.BROWN, (x - 4, y - 4, 8, 6), math.pi, 2 * math.pi, 2)


def draw_oil_drum(surf: pygame.Surface, cx: float, by: float) -> None:
    """Dibuja el bidón de aceite que genera llamas.

    Args:
        surf: superficie destino.
        cx: centro X.
        by: base Y del bidón.
    """
    x, y = int(cx - 12), int(by - 26)
    pygame.draw.rect(surf, (70, 70, 70), (x, y, 24, 26), border_radius=2)
    pygame.draw.rect(surf, (140, 140, 140), (x + 2, y + 2, 20, 22), border_radius=2)
    pygame.draw.rect(surf, P.ORANGE, (x + 2, y + 16, 20, 8), border_radius=2)
    # Llama encima
    fx = int(cx)
    _c(surf, P.FLAME_YEL, (fx, y - 7), 7)
    _c(surf, P.FLAME_ORG, (fx, y - 7), 4)
