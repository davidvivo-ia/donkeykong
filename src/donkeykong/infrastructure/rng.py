"""RNG inyectable con Protocol.

Permite usar Random estándar en producción y un stub determinista
en tests y modo --demo, sin cambiar el código del motor.
"""

from __future__ import annotations

import random
from typing import Protocol, TypeVar

T = TypeVar("T")


class RNG(Protocol):
    """Interfaz de generador de números aleatorios."""

    def random(self) -> float:
        """Retorna float en [0, 1)."""
        ...

    def randint(self, a: int, b: int) -> int:
        """Retorna entero en [a, b]."""
        ...

    def choice(self, seq: list[T]) -> T:
        """Elige un elemento aleatorio de la secuencia."""
        ...


class StdRNG:
    """RNG basado en random.Random de la biblioteca estándar.

    Args:
        seed: semilla opcional para reproducibilidad.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def random(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, seq: list[T]) -> T:
        return self._rng.choice(seq)


class SeededRNG(StdRNG):
    """RNG con semilla fija — para modo --demo y tests deterministas.

    Args:
        seed: semilla fija.
    """

    def __init__(self, seed: int = 42) -> None:
        super().__init__(seed=seed)
