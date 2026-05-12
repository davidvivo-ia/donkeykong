"""Resultado del motor de juego para un frame dado."""

from __future__ import annotations

from dataclasses import dataclass

from donkeykong.domain.events import ScoreEvent, SoundEvent
from donkeykong.domain.world import GameWorld


@dataclass(frozen=True, slots=True)
class EngineOutput:
    """Resultado de un tick del motor de juego.

    Args:
        world: nuevo estado del mundo tras el tick.
        sound_events: sonidos que deben reproducirse este frame.
        score_events: popups de puntuación que deben mostrarse.
    """

    world: GameWorld
    sound_events: tuple[SoundEvent, ...]
    score_events: tuple[ScoreEvent, ...]
