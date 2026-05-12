"""IA determinista para el modo --demo.

Juega automáticamente una partida usando heurísticas simples:
1. Si hay un barril cerca en la misma plataforma → saltar.
2. Si no, moverse hacia la escalera más cercana que lleve hacia Pauline.
3. Al llegar a Pauline → victoria.

[SUPUESTO] La IA no es óptima; está diseñada para ser legible y
determinista con semilla fija, no para jugar perfecto.
"""

from __future__ import annotations

from donkeykong.application.input import InputState
from donkeykong.domain.entities import GamePhase, MarioState
from donkeykong.domain.world import GameWorld

_BARREL_DANGER_DIST: float = 80.0
_LADDER_ALIGN_DIST: float = 12.0


def compute_demo_input(world: GameWorld) -> InputState:
    """Calcula el input del frame actual para el modo demo.

    Args:
        world: estado actual del juego.

    Returns:
        InputState que el motor de juego interpretará como input del jugador.
    """
    if world.phase != GamePhase.PLAYING:
        return InputState.idle()

    mario = world.mario
    if mario.state in (MarioState.DEAD,):
        return InputState.idle()

    # ── Peligro de barril ────────────────────────────────────────────────────
    should_jump = _should_jump(world)

    # ── Moverse hacia Pauline ────────────────────────────────────────────────
    target_x = world.pauline.position.x
    target_y = world.pauline.position.y

    # Buscar escalera que lleve hacia arriba si Pauline está más alta
    left = right = up = down = False

    if mario.climbing:
        # Seguir subiendo si Pauline está más arriba
        if mario.position.y > target_y + 10:
            up = True
        elif mario.position.y > target_y - 10:
            # Ya en el nivel correcto, salir de la escalera
            up = True
    else:
        # Buscar escalera hacia arriba si Pauline está más alta
        nearest_ladder = _find_nearest_ladder_upward(world)
        if nearest_ladder is not None and mario.position.y > target_y + 30:
            # Moverse hacia la escalera
            lx = nearest_ladder
            if abs(mario.position.x - lx) < _LADDER_ALIGN_DIST:
                up = True
            elif mario.position.x < lx:
                right = True
            else:
                left = True
        else:
            # Misma altura o ya llegó: ir hacia Pauline
            if mario.position.x < target_x - 8:
                right = True
            elif mario.position.x > target_x + 8:
                left = True

    return InputState(
        left=left,
        right=right,
        up=up,
        down=down,
        jump=should_jump,
        pause=False,
    )


def _should_jump(world: GameWorld) -> bool:
    """Decide si Mario debe saltar para esquivar un barril."""
    mario = world.mario
    if not mario.on_ground:
        return False
    for barrel in world.barrels:
        if abs(barrel.position.y - mario.position.y) > 30:
            continue
        dist = barrel.position.x - mario.position.x
        # Barril se acerca desde la derecha (vel negativa = va a la izquierda)
        if barrel.velocity.vx < 0 and -_BARREL_DANGER_DIST < dist < 0:
            return True
        # Barril se acerca desde la izquierda (vel positiva = va a la derecha)
        if barrel.velocity.vx > 0 and 0 < dist < _BARREL_DANGER_DIST:
            return True
    return False


def _find_nearest_ladder_upward(world: GameWorld) -> float | None:
    """Busca la X del centro de la escalera más cercana que suba."""
    mario = world.mario
    best_dist: float | None = None
    best_cx: float | None = None

    for lad in world.level.ladders:
        # Solo escaleras cuyo tope esté más arriba que los pies de Mario
        if lad.y_top >= mario.position.y:
            continue
        # Solo si Mario está en el rango vertical de la escalera (puede usarla)
        if not (lad.y_top < mario.position.y <= lad.y_bottom + 20):
            continue
        dist = abs(lad.cx - mario.position.x)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_cx = lad.cx

    return best_cx
