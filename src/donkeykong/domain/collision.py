"""Detección de colisiones pura del dominio.

Todas las funciones son puras (sin efectos secundarios).
Trabajan sobre los tipos inmutables del dominio.
"""

from __future__ import annotations

from donkeykong.domain.entities import Barrel, BonusItem, Flame, Mario, Pauline, Rect


def rects_overlap(a: Rect, b: Rect) -> bool:
    """Colisión AABB estándar entre dos rectángulos.

    Args:
        a: primer rectángulo.
        b: segundo rectángulo.

    Returns:
        True si los rectángulos se solapan.
    """
    return a.collides_with(b)


def mario_hit_by_barrel(mario: Mario, barrel: Barrel) -> bool:
    """Determina si un barril golpea a Mario.

    Ignora la colisión si Mario es invulnerable.

    Args:
        mario: estado actual del jugador.
        barrel: barril a comprobar.

    Returns:
        True si el barril mata a Mario.
    """
    if mario.is_invincible:
        return False
    return rects_overlap(mario.rect, barrel.rect)


def mario_hit_by_flame(mario: Mario, flame: Flame) -> bool:
    """Determina si una llama golpea a Mario.

    Ignora la colisión si Mario es invulnerable.

    Args:
        mario: estado actual del jugador.
        flame: llama a comprobar.

    Returns:
        True si la llama mata a Mario.
    """
    if mario.is_invincible:
        return False
    return rects_overlap(mario.rect, flame.rect)


def mario_reaches_pauline(mario: Mario, pauline: Pauline) -> bool:
    """Comprueba si Mario alcanza a Pauline (condición de victoria).

    Args:
        mario: estado actual del jugador.
        pauline: posición de Pauline.

    Returns:
        True si Mario toca a Pauline.
    """
    return rects_overlap(mario.rect, pauline.rect)


def mario_collects_bonus(mario: Mario, bonus: BonusItem) -> bool:
    """Comprueba si Mario recoge un objeto bonus.

    Args:
        mario: estado actual del jugador.
        bonus: objeto bonus.

    Returns:
        True si Mario colisiona con el bonus.
    """
    return rects_overlap(mario.rect, bonus.rect)


def mario_jumps_over_barrel(
    mario: Mario,
    barrel: Barrel,
    prev_mario_vy: float,
) -> bool:
    """Detecta si Mario ha saltado por encima de un barril (bonus de puntos).

    Se cumple cuando:
    - Mario estaba subiendo (vy < 0) en el frame anterior.
    - Mario está por encima del barril.
    - La distancia horizontal es menor a 28px.

    Args:
        mario: estado actual del jugador.
        barrel: barril a evaluar.
        prev_mario_vy: VY de Mario en el frame anterior.

    Returns:
        True si Mario acaba de saltar sobre el barril.
    """
    if mario.climbing:
        return False
    if prev_mario_vy >= 0:
        return False
    horizontal_dist = abs(mario.position.x - barrel.position.x)
    if horizontal_dist > 28.0:
        return False
    return mario.position.y < barrel.position.y - 4.0
