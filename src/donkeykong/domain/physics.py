"""Sistema de física pura del dominio.

Todas las funciones son puras: mismo input → mismo output.
Sin efectos secundarios, sin estado global, testeable con pytest directo.
"""

from __future__ import annotations

from donkeykong.domain.entities import Position, Velocity
from donkeykong.domain.level import Ladder, Platform

# Constantes físicas [DATO] tomadas de legacy/donkeykong.py
GRAVITY: float = 0.55
JUMP_VELOCITY: float = -13.0
WALK_SPEED: float = 3.2
CLIMB_SPEED: float = 2.8
BARREL_SPEED: float = 2.8
BARREL_GRAVITY_MULT: float = 1.1
FLAME_SPEED: float = 1.4
SCREEN_WIDTH: float = 800.0
SCREEN_HEIGHT: float = 600.0


# ---------------------------------------------------------------------------
# Funciones de física
# ---------------------------------------------------------------------------


def apply_gravity(vel: Velocity, multiplier: float = 1.0) -> Velocity:
    """Aplica aceleración gravitatoria al eje Y.

    Args:
        vel: velocidad actual.
        multiplier: escala del efecto gravitatorio (>1 cae más rápido).

    Returns:
        Velocidad con VY incrementado.
    """
    return vel.add_gravity(GRAVITY * multiplier)


def integrate(pos: Position, vel: Velocity) -> Position:
    """Mueve la posición en función de la velocidad (integración de Euler).

    Args:
        pos: posición actual.
        vel: velocidad actual.

    Returns:
        Nueva posición.
    """
    return pos.move(vel.vx, vel.vy)


def clamp_to_screen(
    pos: Position,
    half_width: float,
    screen_w: float = SCREEN_WIDTH,
) -> Position:
    """Impide que la posición salga por los bordes laterales de pantalla.

    Args:
        pos: posición a limitar (x es el centro del sprite).
        half_width: semiancho del sprite.
        screen_w: ancho de pantalla.

    Returns:
        Posición acotada.
    """
    min_x = half_width + 2.0
    max_x = screen_w - half_width - 2.0
    return pos.with_x(max(min_x, min(max_x, pos.x)))


def resolve_platform_collision(
    pos: Position,
    vel: Velocity,
    platforms: tuple[Platform, ...],
) -> tuple[Position, Velocity, bool, bool]:
    """Detecta y resuelve colisión con plataformas desde arriba.

    Solo colisiona cuando el sprite cae (vy >= 0) y los pies cruzan
    la superficie de la plataforma dentro de una ventana de 24px.

    Args:
        pos: posición actual (x=centro, y=pies).
        vel: velocidad actual.
        platforms: colección de plataformas del nivel.

    Returns:
        Tupla (nueva_pos, nueva_vel, on_ground, just_landed).
        just_landed es True solo el frame en que toca suelo.
    """
    if vel.vy < 0:
        return pos, vel, False, False

    for plat in platforms:
        if not plat.contains_x(pos.x):
            continue
        delta = pos.y - plat.y
        if 0.0 <= delta <= 24.0:
            return plat.y, vel.zero_y(), True, delta > 0.5  # type: ignore[return-value]

    # Mypy no infiere bien el return type con el ternario, la tupla explícita:
    return pos, vel, False, False


def resolve_platform_collision_full(
    pos: Position,
    vel: Velocity,
    platforms: tuple[Platform, ...],
) -> tuple[Position, Velocity, bool, bool]:
    """Versión completa con tipos explícitos para mypy.

    Args:
        pos: posición actual.
        vel: velocidad actual.
        platforms: plataformas del nivel.

    Returns:
        (posición_resuelta, velocidad_resuelta, en_suelo, acaba_de_aterrizar)
    """
    if vel.vy < 0:
        return pos, vel, False, False

    for plat in platforms:
        if not plat.contains_x(pos.x):
            continue
        delta = pos.y - plat.y
        if 0.0 <= delta <= 24.0:
            new_pos = pos.with_y(plat.y)
            new_vel = vel.zero_y()
            just_landed = delta > 0.5
            return new_pos, new_vel, True, just_landed

    return pos, vel, False, False


def resolve_ladder_movement(
    pos: Position,
    vel: Velocity,
    ladder: Ladder,
    direction: int,
    speed: float = CLIMB_SPEED,
) -> tuple[Position, Velocity, bool]:
    """Mueve al personaje por una escalera y detecta si ha llegado al extremo.

    Args:
        pos: posición actual.
        vel: velocidad actual (solo se usa vy).
        ladder: escalera en uso.
        direction: -1 subir, +1 bajar.
        speed: velocidad de escalada.

    Returns:
        (nueva_pos, nueva_vel, salió_de_escalera)
    """
    new_y = pos.y + direction * speed
    new_pos = Position(ladder.cx, new_y)
    exited = False

    if direction == -1 and new_y <= ladder.y_top:
        new_pos = Position(ladder.cx, ladder.y_top)
        exited = True
    elif direction == 1 and new_y >= ladder.y_bottom:
        new_pos = Position(ladder.cx, ladder.y_bottom)
        exited = True

    return new_pos, vel.zero_y(), exited


def jump_velocity(current_vel: Velocity) -> Velocity:
    """Retorna velocidad con impulso de salto aplicado.

    Args:
        current_vel: velocidad antes del salto.

    Returns:
        Velocidad con VY establecido al impulso de salto.
    """
    return current_vel.with_vy(JUMP_VELOCITY)


def find_ladder_at(
    cx: float,
    feet_y: float,
    ladders: tuple[Ladder, ...],
) -> Ladder | None:
    """Busca la escalera que el personaje puede usar en su posición actual.

    Args:
        cx: centro X del personaje.
        feet_y: Y de los pies del personaje.
        ladders: escaleras del nivel.

    Returns:
        La primera escalera que puede ser usada, o None.
    """
    for lad in ladders:
        if lad.mario_can_grab(cx, feet_y):
            return lad
    return None


def barrel_roll_velocity(
    platform_direction: int,
    speed_multiplier: float = 1.0,
) -> Velocity:
    """Calcula la velocidad de rodado de un barril sobre una plataforma.

    Args:
        platform_direction: dirección de la plataforma (+1 o -1).
        speed_multiplier: escalado por nivel.

    Returns:
        Velocidad horizontal del barril.
    """
    return Velocity(platform_direction * BARREL_SPEED * speed_multiplier, 0.0)
