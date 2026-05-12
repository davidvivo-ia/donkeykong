"""Estado completo del mundo del juego en un instante dado.

GameWorld es el contenedor raíz de todo el estado mutable de la partida.
Es reemplazado completo cada frame por el motor de juego.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from donkeykong.domain.entities import (
    Barrel,
    BonusItem,
    DonkeyKong,
    Flame,
    GamePhase,
    Mario,
    Pauline,
    Score,
    ScorePopup,
)
from donkeykong.domain.level import Level


@dataclass(frozen=True, slots=True)
class GameWorld:
    """Snapshot completo del estado del juego.

    Cada frame el motor produce un nuevo GameWorld a partir del anterior.
    Esto garantiza que el estado es siempre consistente y testeable.
    """

    # Personajes
    mario: Mario
    dk: DonkeyKong
    pauline: Pauline

    # Entidades dinámicas
    barrels: tuple[Barrel, ...]
    flames: tuple[Flame, ...]
    bonuses: tuple[BonusItem, ...]
    popups: tuple[ScorePopup, ...]

    # Estructura del nivel
    level: Level
    level_num: int

    # Puntuación y vidas
    score: Score
    lives: int

    # Temporizadores
    bonus_timer: int  # timer de bonus (countdown de 3600 → 0)
    tick: int  # tick global desde inicio del nivel
    state_tick: int  # tick desde el inicio del estado actual

    # Contadores de IDs para entidades nuevas
    next_barrel_id: int
    next_flame_id: int
    next_bonus_id: int

    # Temporizadores de spawn
    flame_timer: int
    bonus_spawn_timer: int

    # Fase del juego
    phase: GamePhase

    # Velocidad de los barriles que saltó Mario (para evitar doble recompensa)
    jumped_barrel_ids: frozenset[int]

    # VY de Mario en el frame anterior (para detectar salto sobre barril)
    prev_mario_vy: float

    BONUS_TIMER_MAX: int = field(default=3600, compare=False)


def initial_world(
    level: Level,
    level_num: int,
    lives: int,
    high_score: int,
) -> GameWorld:
    """Crea el estado inicial de un nivel.

    Args:
        level: definición del nivel a jugar.
        level_num: número de nivel (1-based).
        lives: vidas disponibles al empezar.
        high_score: récord actual (para preservarlo entre niveles).

    Returns:
        GameWorld listo para el primer tick.
    """
    mario = Mario.initial(level.mario_start)
    dk = DonkeyKong.initial(level.dk_start)
    pauline = Pauline(position=level.pauline_start, frame_tick=0)

    return GameWorld(
        mario=mario,
        dk=dk,
        pauline=pauline,
        barrels=(),
        flames=(),
        bonuses=(),
        popups=(),
        level=level,
        level_num=level_num,
        score=Score.zero(high_score),
        lives=lives,
        bonus_timer=3600,
        tick=0,
        state_tick=0,
        next_barrel_id=0,
        next_flame_id=0,
        next_bonus_id=0,
        flame_timer=0,
        bonus_spawn_timer=400,
        phase=GamePhase.INTRO,
        jumped_barrel_ids=frozenset(),
        prev_mario_vy=0.0,
    )
