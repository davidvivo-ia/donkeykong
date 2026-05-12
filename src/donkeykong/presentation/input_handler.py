"""Traduce pygame.key.get_pressed() al modelo de dominio InputState."""

from __future__ import annotations

import pygame

from donkeykong.application.input import InputState


def read_input() -> InputState:
    """Lee el estado actual del teclado y lo convierte a InputState.

    Returns:
        InputState con el estado de cada acción en este frame.
    """
    keys = pygame.key.get_pressed()
    return InputState(
        left=bool(keys[pygame.K_LEFT] or keys[pygame.K_a]),
        right=bool(keys[pygame.K_RIGHT] or keys[pygame.K_d]),
        up=bool(keys[pygame.K_UP] or keys[pygame.K_w]),
        down=bool(keys[pygame.K_DOWN] or keys[pygame.K_s]),
        jump=bool(keys[pygame.K_SPACE]),
        pause=False,  # pause se gestiona vía evento, no polling
    )
