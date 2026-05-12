# Donkey Kong

[![CI](https://github.com/davidvivo-ia/donkeykong/actions/workflows/ci.yml/badge.svg)](https://github.com/davidvivo-ia/donkeykong/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Recreación del arcade clásico Donkey Kong (Nintendo, 1981) en Python 3.13 con pygame-ce. Arquitectura limpia por capas, física de plataformas, IA de persecución, sprites procedurales y síntesis de audio PCM retro.

---

## Descripción

Mario debe escalar una estructura de vigas de acero para rescatar a Pauline de las garras de Donkey Kong. En el camino deberá saltar sobre barriles que ruedan por las vigas y esquivar llamas que suben escaleras persiguiéndole. Cada nivel completado aumenta la velocidad de los enemigos.

---

## Screenshot ASCII

```
┌─────────────────────────────────────────────────────────────────────┐
│ SCORE 042500    BEST 042500    LVL 3   ❤❤❤              BONUS ████░ │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DK ~~          ════════════════════════════════  Pauline           │
│         |                                                    |      │
│  ═══════╪══════════════════════════════════════════╪═════════       │
│         |           ○ barrel                       |                │
│  ═══════╪═══════════════╪═══════════════════════════════════        │
│                         |                                           │
│  ═══════════════════════╪════════════════╪══════════════════        │
│                         |                |                          │
│  ══════════════════╪════════════════════════════════════════        │
│  ▓▓▓ oildrum       |          Mario →                               │
│  ════════════════════════════════════════════════════════════       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Instalación

**Requisitos:** Python 3.13+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/davidvivo-ia/donkeykong.git
cd donkeykong
uv sync
```

---

## Uso

```bash
# Partida normal
uv run donkeykong

# Modo demo (semilla fija, comportamiento reproducible)
uv run donkeykong --demo

# Semilla personalizada (para reproducir una partida)
uv run donkeykong --seed 42

# Pantalla completa
uv run donkeykong --fullscreen
```

---

## Controles

| Acción | Tecla principal | Tecla alternativa |
|---|---|---|
| Mover izquierda | `←` | `A` |
| Mover derecha | `→` | `D` |
| Saltar | `Espacio` | `↑` / `W` |
| Subir escalera | `↑` | `W` |
| Bajar escalera | `↓` | `S` |
| Pausar / Reanudar | `P` | — |
| Volver al menú | `Escape` | — |
| Iniciar partida | `Enter` | — |

---

## Modos de juego

### Normal
Aleatoriedad real: posición de bonus, dirección de llamas y tiempo entre lanzamientos varían cada partida. La puntuación máxima se guarda en `~/.local/share/donkeykong/scores.json`.

### `--demo`
Usa una semilla RNG fija (`DEMO_SEED = 20250101`). El juego siempre se comporta igual. Útil como modo de atracción en kioscos y como test de regresión visual.

### `--seed N`
Usa la semilla entera `N`. Permite reproducir exactamente una partida anotando la semilla usada.

---

## Arquitectura

El proyecto sigue una **arquitectura por capas inspirada en Clean Architecture**. El `domain/` contiene las entidades del juego como frozen dataclasses con `__slots__`: `Mario`, `Barrel`, `Flame`, `DonkeyKong`, `Platform`, `Ladder`. Las funciones de física en `domain/physics.py` son transformaciones puras `(state, inputs) → new_state`, testables sin pygame. La capa `application/` orquesta el bucle de juego, la máquina de estados y el CLI (typer + rich). La capa `infrastructure/` implementa la síntesis PCM, la persistencia JSON en XDG y el RNG inyectable. La capa `presentation/` encapsula todo el código pygame-ce: ventana, sprites procedurales y el efecto phosphor glow.

La **Dependency Rule** se aplica estrictamente: `presentation` depende de `application`, `application` depende de `domain` e `infrastructure`, `domain` no depende de nadie. Esto permite ejecutar los tests del dominio y la aplicación sin inicializar pygame, reduciendo el tiempo de CI y eliminando la necesidad de un display virtual para las pruebas de lógica.

---

## Estructura del proyecto

```
donkeykong/
├── src/donkeykong/
│   ├── domain/          # Entidades, física, protocolos
│   ├── application/     # Game loop, state machine, CLI
│   ├── infrastructure/  # Sonido, persistencia, RNG, settings
│   └── presentation/    # Ventana pygame, sprites, HUD
├── tests/
│   ├── unit/            # Tests unitarios de dominio
│   ├── integration/     # Tests de integración (app + infra)
│   └── property/        # Tests de propiedad con Hypothesis
├── legacy/
│   └── donkeykong.py    # Código original monolítico (referencia)
└── docs/
    ├── original_program_analysis.md
    ├── architecture.md
    ├── design.md
    ├── postmortem.md
    └── adr/             # Architecture Decision Records
```

---

## Créditos

Donkey Kong es una marca registrada de Nintendo Co., Ltd. (1981). Esta recreación es un proyecto educativo y de preservación, desarrollado desde cero en Python sin uso de assets originales. Todos los sprites se generan proceduralmente con `pygame.draw`. Los efectos de sonido son síntesis PCM original.

Código por **davidvivo-ia** (2026). Basado en el análisis del arcade original de 1981.
