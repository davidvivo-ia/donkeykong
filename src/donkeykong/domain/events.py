"""Eventos de dominio emitidos por el motor de juego.

Los eventos son inmutables y sirven como canal de comunicación
entre el dominio y la capa de infraestructura (sonido, log).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from donkeykong.domain.entities import Position


class SoundEvent(Enum):
    """Eventos de audio solicitados por el dominio."""

    JUMP = auto()
    LAND = auto()
    WALK = auto()
    CLIMB = auto()
    BARREL_LAND = auto()
    DIE = auto()
    SCORE = auto()
    WIN = auto()
    BONUS = auto()
    THROW = auto()
    FLAME_SPAWN = auto()
    LEVEL_UP = auto()
    BARREL_JUMP = auto()  # Mario salta por encima de un barril


@dataclass(frozen=True, slots=True)
class ScoreEvent:
    """Solicitud de mostrar un popup de puntuación."""

    value: int
    position: Position
    color: tuple[int, int, int]
