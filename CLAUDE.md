# CLAUDE.md — instrucciones del proyecto

## Arrancar el juego

```bash
python donkeykong.py
```

Funciona en Windows, macOS y Linux. Instala las dependencias automáticamente
con pip si no están presentes (pygame-ce, pydantic, typer, rich, structlog).

## Estructura del proyecto

```
src/donkeykong/          # paquete principal
  domain/                # lógica pura (entities, level, physics, collision)
  application/           # motor de juego (game_engine.py)
  presentation/          # render, sprites, sonido, game_loop
  infrastructure/        # config, rng, persistence
tests/                   # pytest (uv run pytest)
persia.py                # lanzador directo
play.py                  # lanzador alternativo
```

## Comandos de desarrollo

```bash
uv run pytest            # pasar todos los tests
uv run ruff check .      # linter
uv run mypy src          # type checker
```

## Convenciones

- Todos los modelos de dominio son `frozen dataclass` con `slots=True`.
- El estado del juego es inmutable; cada frame produce un nuevo `GameWorld`.
- El RNG es inyectado (`RNG` protocol) para mantener determinismo en tests.
- Sin comentarios salvo cuando el "por qué" no es obvio.
