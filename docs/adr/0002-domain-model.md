# ADR 0002 — Modelo de dominio: frozen dataclasses con slots

**Estado:** Aceptado  
**Fecha:** 2026-05-12  
**Autores:** davidvivo-ia

---

## Contexto

El dominio del juego contiene entidades con estado que cambia frame a frame: posición, velocidad, flags de animación. En el original monolítico, estas entidades son clases Python con atributos mutables y sin type hints. Al refactorizar a arquitectura por capas necesitamos elegir cómo representar el estado del dominio.

Se consideraron tres opciones:

1. **Clases mutables con `__init__`** (patrón original).
2. **Frozen dataclasses con `__slots__`** (Python 3.13 nativo).
3. **Pydantic BaseModel** (validación en tiempo de ejecución).

---

## Decisión

Usamos **frozen dataclasses con `__slots__`** para las entidades de dominio.

Para las entidades que necesitan actualización por frame (Mario, Barrel, Flame, DK), usamos el patrón **value object update**: la función de física devuelve una nueva instancia en vez de mutar la existente.

```python
@dataclass(frozen=True, slots=True)
class Mario:
    cx: float
    by: float
    vx: float
    vy: float
    on_ground: bool
    climbing: bool
    facing: int   # +1 o -1
    state: MarioState
    frame: int
    invincible: int
    dead_anim: int

# En physics.py:
def apply_gravity(mario: Mario, gravity: float) -> Mario:
    return dataclasses.replace(mario, vy=mario.vy + gravity)
```

---

## Razonamiento

### Inmutabilidad → testabilidad sin mocks

Con entidades frozen, las funciones de física son transformaciones puras: `(state, inputs) → new_state`. Esto permite probarlas sin necesidad de mocks ni de inicializar pygame:

```python
def test_gravity_increases_vy():
    mario = Mario(cx=100.0, by=300.0, vx=0.0, vy=0.0, ...)
    updated = apply_gravity(mario, gravity=0.55)
    assert updated.vy == pytest.approx(0.55)
    assert updated.cx == mario.cx   # inmutabilidad verificada
```

### `__slots__` → performance

Con `slots=True`, Python pre-asigna los atributos de la clase en un array de C en vez de un dict. Para objetos que se crean/destruyen miles de veces por segundo (barriles, popups), esto reduce la presión del GC y el uso de memoria.

Benchmark orientativo en CPython 3.13: la lectura de atributos de una clase con `__slots__` es ~40 % más rápida que con `__dict__`. Para entidades que el motor lee 60 × N veces por segundo, el beneficio es apreciable.

### Python 3.13 pattern matching

Con las entidades como dataclasses, el pattern matching es directo:

```python
match mario.state:
    case MarioState.DEAD:
        return mario  # no update
    case MarioState.CLIMBING:
        return apply_climb_physics(mario)
    case _:
        return apply_ground_physics(mario, platforms)
```

Esto es más legible y exhaustivo que cadenas de `if/elif`.

### Por qué no Pydantic BaseModel para el dominio

Pydantic añade validación en tiempo de ejecución y serialización JSON, que son propiedades valiosas para la capa de infraestructura (settings, persistencia de score). Sin embargo, para el dominio el costo es:

- Cada llamada a `model_validate()` o al validador de campos introduce overhead que, multiplicado por 60 FPS × N entidades, puede introducir jank.
- Pydantic no genera `__slots__` por defecto (requiere `model_config = ConfigDict(slots=True)`).
- El dominio no necesita validación de entrada — los inputs ya fueron validados en la capa de aplicación.

**Pydantic se usa en `infrastructure/settings.py`** para cargar y validar la configuración del usuario, y en `infrastructure/persistence.py` para serializar/deserializar el high score.

### Por qué no clases mutables simples

Las clases mutables hacen que las funciones de física sean imposibles de testar sin efectos secundarios. Un test que llame `mario.update(...)` puede dejar a `mario` en un estado inesperado si el test anterior no hizo cleanup. Con entidades frozen, cada test parte de un estado limpio construido explícitamente.

---

## Consecuencias

- **Positivas:** tests de física puramente funcionales, sin mocks, sin pygame, sin setup/teardown de estado.
- **Negativas:** el patrón de "replace" genera más objetos temporales que la mutación in-place. El GC de CPython 3.13 maneja bien objetos de vida corta, pero se debe monitorear con perfiles si aparece jank.
- **Neutrales:** `dataclasses.replace()` es ligeramente más verboso que `self.x = ...`. La ganancia en testabilidad compensa el overhead de escritura.
