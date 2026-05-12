"""Donkey Kong — Classic arcade recreation in Python with pygame-ce.

This package implements a clean layered architecture:

- domain: pure game entities and physics (no external dependencies).
- application: game loop, state machine, CLI (typer + rich).
- infrastructure: persistence, sound synthesis, RNG, settings.
- presentation: pygame-ce window, procedural sprites, HUD.

Example:
    Run the game::

        uv run donkeykong

    Run in demo mode with a fixed RNG seed::

        uv run donkeykong --demo

    Run with a custom seed to reproduce a specific session::

        uv run donkeykong --seed 42
"""

__version__ = "1.0.0"
__author__ = "davidvivo-ia"
__license__ = "MIT"
