# Arquitectura del proyecto Donkey Kong

## Diagrama de capas

```
┌─────────────────────────────────────────────────────────────────┐
│                        presentation/                            │
│  (pygame-ce: ventana, sprites, HUD, efectos phosphor glow)      │
└──────────────────────────────┬──────────────────────────────────┘
                               │  llama a (→)
┌──────────────────────────────▼──────────────────────────────────┐
│                        application/                             │
│  (casos de uso: game loop, state machine, scoring, CLI con      │
│   typer + rich, logging con structlog)                          │
└──────────┬───────────────────────────────────────┬──────────────┘
           │  llama a (→)                          │  llama a (→)
┌──────────▼──────────┐               ┌────────────▼──────────────┐
│       domain/       │               │      infrastructure/       │
│  (entidades puras:  │               │  (persistencia JSON/XDG,  │
│   Mario, Barrel,    │               │   síntesis PCM, RNG,      │
│   Flame, DK,        │               │   clock, settings)        │
│   Platform, Ladder, │               │                           │
│   Physics, Score)   │               │                           │
└─────────────────────┘               └───────────────────────────┘
```

**Regla de dependencias (Dependency Rule):** las flechas apuntan siempre hacia adentro. `presentation` depende de `application`. `application` depende de `domain` y de `infrastructure`. `domain` no depende de nadie. `infrastructure` solo depende de `domain` (para implementar sus protocolos).

---

## Capa `domain/`

**Responsabilidades.**
- Definir las entidades inmutables del juego: `Mario`, `Barrel`, `Flame`, `DonkeyKong`, `Pauline`, `Platform`, `Ladder`, `BonusItem`, `ScorePopup`.
- Codificar toda la física por integración de Euler (gravedad, colisión AABB, escalada de escaleras).
- Definir los protocolos de extensión: `RNGProtocol`, `ClockProtocol`.
- No importar pygame, typer, structlog ni ninguna dependencia externa.

**Tecnología.** Frozen dataclasses con `__slots__` (Python 3.13 nativo). Pattern matching para transiciones de estado. Únicamente stdlib.

**Módulos internos propuestos.**

```
domain/
├── __init__.py
├── entities.py        # Mario, Barrel, Flame, DK, Pauline, Platform, Ladder
├── physics.py         # integrate_euler(), resolve_platform_collision(), aabb_check()
├── level.py           # LevelBlueprint, PLATFORMS_L1, LADDERS_L1
├── scoring.py         # Score, HighScore, ScorePopup
└── protocols.py       # RNGProtocol, ClockProtocol
```

---

## Capa `application/`

**Responsabilidades.**
- Implementar la máquina de estados del juego: `MENU → INTRO → PLAYING → PAUSED / LEVELUP / GAMEOVER / WIN`.
- Coordinar el bucle de actualización: input → domain update → collision → state transition.
- Exponer el CLI con typer (`donkeykong`, `donkeykong --demo`, `donkeykong --seed N`).
- Configurar structlog y emitir eventos de juego (death, level_up, score_milestone).

**Módulos internos propuestos.**

```
application/
├── __init__.py
├── game.py            # GameApp: orquesta domain + presentation + infrastructure
├── state_machine.py   # GameState enum, transitions
├── use_cases.py       # start_game(), next_level(), respawn(), compute_score()
└── cli.py             # typer app, --demo, --seed, --fullscreen
```

---

## Capa `infrastructure/`

**Responsabilidades.**
- Persistencia de `HighScore` en `~/.local/share/donkeykong/scores.json` (XDG Base Directory).
- Síntesis PCM procedural (`SoundSynthesizer`): `_tone()`, `_chord()`, `_slide()`.
- Implementación de `RNGProtocol` con `random.Random` (inyectable, seedable).
- Implementación de `ClockProtocol` con `pygame.time.Clock`.
- Carga y validación de `Settings` (pydantic v2) desde `~/.config/donkeykong/settings.toml`.

**Módulos internos propuestos.**

```
infrastructure/
├── __init__.py
├── persistence.py     # ScoreRepository: load_high_score(), save_high_score()
├── sound.py           # SoundSynthesizer, todos los SND_* generados
├── rng.py             # SeededRNG(RNGProtocol), DemoRNG (seed fijo)
├── clock.py           # PygameClock(ClockProtocol)
└── settings.py        # Settings (pydantic BaseSettings), xdg_data_dir()
```

---

## Capa `presentation/`

**Responsabilidades.**
- Inicializar la ventana pygame-ce y gestionar el display loop.
- Renderizar todos los sprites de forma procedural con `pygame.draw.*`.
- Implementar el efecto phosphor glow (surface alpha overlay sobre sprites).
- Dibujar el HUD, los overlays de pausa/gameover/levelup y el background animado.
- Traducir eventos pygame (`KEYDOWN`, `QUIT`) a comandos para `application`.

**Módulos internos propuestos.**

```
presentation/
├── __init__.py
├── window.py          # PygameWindow: init, event_loop, flip
├── sprites.py         # draw_mario(), draw_dk(), draw_barrel(), draw_flame(), draw_pauline()
├── background.py      # draw_background(), draw_city_silhouette(), draw_stars()
├── hud.py             # draw_hud(), draw_score_popup()
├── screens.py         # draw_menu(), draw_intro(), draw_game_over(), draw_paused(), etc.
└── effects.py         # phosphor_glow(), apply_scanlines()
```

---

## Diagrama de módulos completo

```
src/donkeykong/
│
├── __main__.py                  ← entry point: `uv run donkeykong`
│
├── domain/
│   ├── __init__.py
│   ├── entities.py
│   ├── physics.py
│   ├── level.py
│   ├── scoring.py
│   └── protocols.py
│
├── application/
│   ├── __init__.py
│   ├── game.py
│   ├── state_machine.py
│   ├── use_cases.py
│   └── cli.py
│
├── infrastructure/
│   ├── __init__.py
│   ├── persistence.py
│   ├── sound.py
│   ├── rng.py
│   ├── clock.py
│   └── settings.py
│
└── presentation/
    ├── __init__.py
    ├── window.py
    ├── sprites.py
    ├── background.py
    ├── hud.py
    ├── screens.py
    └── effects.py
```

---

## Flujo de datos en el bucle de juego

```
PygameWindow.event_loop()
    │
    ├─► [KEYDOWN] ──► application.game.GameApp.handle_input()
    │                   │
    │                   └─► domain.entities.Mario.apply_input(cmd)
    │                         └─► domain.physics.integrate_euler()
    │
    ├─► application.game.GameApp.update()
    │     ├─► domain.entities.DonkeyKong.tick() → spawn Barrel?
    │     ├─► domain.entities.Barrel.update() × N
    │     ├─► domain.entities.Flame.update(mario_pos) × N
    │     ├─► domain.physics.aabb_check(mario, barrels+flames)
    │     └─► application.use_cases.compute_score() → infrastructure.persistence.save()
    │
    └─► presentation.window.render()
          ├─► presentation.background.draw_background()
          ├─► presentation.sprites.draw_* (entities)
          ├─► presentation.effects.phosphor_glow()
          └─► presentation.hud.draw_hud()
```
