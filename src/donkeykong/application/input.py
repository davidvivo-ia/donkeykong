"""Modelo de entrada del jugador.

Desacopla el hardware (pygame.key) del dominio.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InputState:
    """Estado de controles en un frame dado."""

    left: bool
    right: bool
    up: bool
    down: bool
    jump: bool
    pause: bool

    @staticmethod
    def idle() -> InputState:
        """Sin ninguna tecla pulsada."""
        return InputState(False, False, False, False, False, False)
