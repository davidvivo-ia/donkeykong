# ADR 0003 — Estrategia de RNG: inyectable vía Protocol

**Estado:** Aceptado  
**Fecha:** 2026-05-12  
**Autores:** davidvivo-ia

---

## Contexto

El juego usa aleatoriedad en varios puntos:

- Generación de estrellas del fondo (posición, brillo, velocidad de parpadeo).
- Dirección inicial de las llamas (`random.choice([-1, 1])`).
- Intervalo entre bonus items (`random.randint(240, 600)`).
- Posición X y tipo de cada bonus item.
- Velocidad de lanzamiento de barriles (indirectamente, vía `throw_cd`).

En el código original, todos estos usos llaman al módulo `random` global sin semilla, produciendo runs no reproducibles. Esto tiene dos consecuencias:

1. **Los tests de comportamiento son no deterministas.** Un test que verifique que una llama persigue a Mario puede fallar si la dirección inicial aleatoria es desfavorable.
2. **No existe modo demo.** El modo de atracción (attract mode) del arcade original requiere un comportamiento reproducible con semilla fija.

---

## Decisión

Definimos un **`RNGProtocol`** en `domain/protocols.py` e inyectamos la implementación en todas las entidades y funciones del dominio que necesiten aleatoriedad.

```python
# domain/protocols.py
from typing import Protocol, Sequence, TypeVar

T = TypeVar("T")

class RNGProtocol(Protocol):
    def randint(self, a: int, b: int) -> int: ...
    def choice(self, seq: Sequence[T]) -> T: ...
    def uniform(self, a: float, b: float) -> float: ...
    def random(self) -> float: ...
```

### Implementaciones

```python
# infrastructure/rng.py
import random

class SeededRNG:
    """RNG inyectable, reproducible. Para tests y modo --demo."""
    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, seq):
        return self._rng.choice(seq)

    def uniform(self, a: float, b: float) -> float:
        return self._rng.uniform(a, b)

    def random(self) -> float:
        return self._rng.random()


class SystemRNG:
    """Wrapper del módulo random global. Para partidas normales."""
    def randint(self, a: int, b: int) -> int:
        return random.randint(a, b)

    def choice(self, seq):
        return random.choice(seq)

    def uniform(self, a: float, b: float) -> float:
        return random.uniform(a, b)

    def random(self) -> float:
        return random.random()
```

### Semilla para modo --demo

```python
DEMO_SEED = 20250101   # Constante pública, documentada, fija entre versiones
```

### CLI

```
donkeykong                 # SystemRNG (aleatorio)
donkeykong --demo          # SeededRNG(DEMO_SEED)
donkeykong --seed 42       # SeededRNG(42)
```

---

## Razonamiento

### Testabilidad determinista

Con `SeededRNG(seed=0)`, los tests de property-based testing con Hypothesis siempre producen la misma secuencia de valores aleatorios para una semilla dada, lo que permite reproducir fallos exactos:

```python
# tests/property/test_flame_ai.py
def test_flame_always_moves_toward_mario():
    rng = SeededRNG(seed=42)
    flame = Flame(x=100.0, y=535.0, rng=rng, ...)
    # Con seed fijo, la dirección inicial es determinista
    assert abs(flame.vx) == FLAME_SPEED
```

### Modo demo reproducible

El modo `--demo` ejecuta una partida con `SeededRNG(DEMO_SEED)`. El juego siempre muestra la misma secuencia de eventos, lo que permite usar el modo demo como test de regresión visual: si algo cambia en la física o en la IA, la demo diverge.

### Por qué Protocol y no clase base abstracta (ABC)

`typing.Protocol` permite **duck typing estructural**: `SystemRNG` y `SeededRNG` no necesitan heredar de una clase común. Esto simplifica la jerarquía y permite envolver cualquier objeto con la interfaz correcta (por ejemplo, un mock de tests) sin boilerplate.

Con `mypy --strict`, el type checker verifica en tiempo de análisis estático que toda implementación satisface el Protocol.

---

## Consecuencias

- **Positivas:** los tests son deterministas. El modo demo es reproducible. mypy verifica la compatibilidad de las implementaciones en CI.
- **Negativas:** se añade un argumento `rng` a los constructores de `Flame`, `BonusItem` y `Background`. Esto aumenta la firma de las funciones, pero es un costo aceptable.
- **Neutrales:** `SystemRNG` es un wrapper fino alrededor del módulo `random`, sin overhead apreciable.
