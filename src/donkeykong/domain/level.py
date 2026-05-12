"""Definición de niveles y estructura de plataformas/escaleras.

[DATO] Layout extraído directamente de legacy/donkeykong.py PLATFORMS/LADDERS.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from donkeykong.domain.entities import Position

# ---------------------------------------------------------------------------
# Elementos estáticos del nivel
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Platform:
    """Viga horizontal sobre la que caminan los personajes.

    Args:
        x_left: píxel izquierdo de la viga.
        x_right: píxel derecho de la viga.
        y: superficie superior (Y donde quedan los pies al aterrizar).
        direction: dirección de rodado de barriles (+1 derecha, -1 izquierda).
        pid: identificador único de plataforma.
    """

    x_left: float
    x_right: float
    y: float
    direction: int  # +1 derecha, -1 izquierda
    pid: int

    HEIGHT: int = field(default=14, compare=False)

    def contains_x(self, x: float) -> bool:
        """True si la X cae dentro del ancho de la plataforma."""
        return self.x_left <= x <= self.x_right

    def surface_rect_y(self) -> float:
        """Y de la superficie superior."""
        return self.y


@dataclass(frozen=True, slots=True)
class Ladder:
    """Escalera vertical que conecta dos plataformas.

    Args:
        cx: centro X de la escalera.
        y_top: Y del borde superior (plataforma superior).
        y_bottom: Y del borde inferior (plataforma inferior).
    """

    cx: float
    y_top: float
    y_bottom: float

    WIDTH: int = field(default=16, compare=False)

    def mario_aligned(self, mario_cx: float) -> bool:
        """True si Mario está alineado horizontalmente con la escalera."""
        return abs(mario_cx - self.cx) < 12

    def mario_can_grab(self, mario_cx: float, mario_feet_y: float) -> bool:
        """True si Mario puede agarrar/usar la escalera."""
        return self.mario_aligned(mario_cx) and self.y_top < mario_feet_y < self.y_bottom + 4


# ---------------------------------------------------------------------------
# Nivel completo
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Level:
    """Descripción completa de un nivel de juego.

    Contiene todos los elementos estáticos (plataformas, escaleras) y las
    posiciones iniciales de los personajes.
    """

    platforms: tuple[Platform, ...]
    ladders: tuple[Ladder, ...]
    dk_start: Position  # centro-X, pies-Y de DK
    pauline_start: Position  # centro-X, pies-Y de Pauline
    mario_start: Position  # centro-X, pies-Y de Mario


# ---------------------------------------------------------------------------
# Constructor del nivel canónico
# ---------------------------------------------------------------------------

# [DATO] Valores tomados directamente de legacy/donkeykong.py
_PLATFORMS: tuple[Platform, ...] = (
    Platform(10, 790, 535, +1, 0),  # Suelo
    Platform(30, 760, 425, -1, 1),  # Plataforma 2
    Platform(30, 760, 315, +1, 2),  # Plataforma 3
    Platform(30, 760, 205, -1, 3),  # Plataforma 4
    Platform(10, 760, 95, +1, 4),  # Cima (zona DK)
)

_LADDERS: tuple[Ladder, ...] = (
    Ladder(160, 425, 535),
    Ladder(580, 425, 535),
    Ladder(250, 315, 425),
    Ladder(645, 315, 425),
    Ladder(185, 205, 315),
    Ladder(605, 205, 315),
    Ladder(370, 95, 205),
)

CANONICAL_LEVEL = Level(
    platforms=_PLATFORMS,
    ladders=_LADDERS,
    dk_start=Position(115.0, 95.0),
    pauline_start=Position(620.0, 95.0),
    mario_start=Position(60.0, 535.0),
)


def build_level(level_num: int = 1) -> Level:
    """Retorna el nivel para el número dado.

    [SUPUESTO: v1.0] Todos los niveles usan el mismo layout; la dificultad
    se incrementa vía velocidad/frecuencia de barriles.

    Args:
        level_num: número de nivel (1-based).

    Returns:
        Level configurado para ese número.
    """
    # v1.0: layout único, dificultad escalada en GameEngine
    _ = level_num  # preparado para layouts alternativos en v1.1
    return CANONICAL_LEVEL
