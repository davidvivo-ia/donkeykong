# Análisis del programa original — `legacy/donkeykong.py`

## Encuadre

| Campo | Valor |
|---|---|
| Lenguaje | Python 3.11 (compatible 3.13) |
| Biblioteca gráfica | Pygame 2.6 / pygame-ce |
| Plataforma objetivo | Escritorio multiplataforma (Linux, macOS, Windows) |
| Año de recreación | 2025 |
| Líneas de código | 1 377 |
| Archivo único | `legacy/donkeykong.py` |

**Sinopsis.** El programa es una recreación del arcade clásico Donkey Kong de Nintendo (1981). Mario debe escalar una estructura de vigas metálicas sorteando barriles lanzados por Donkey Kong y llamas que persiguen al jugador, para rescatar a Pauline en la cima. El código implementa íntegramente en un solo módulo Python: física de plataformas, detección de colisiones, dibujo procedural de todos los sprites con `pygame.draw`, síntesis de audio por PCM, lógica de niveles, HUD y máquina de estados de pantallas.

**Lectura crítica.** La elección de un único archivo facilita el transporte y la comprensión inicial, pero impide escalar el proyecto sin una refactorización profunda. El estado del juego vive en variables globales o en el objeto `Game` como atributos mutables, lo que dificulta las pruebas unitarias. El RNG global no es inyectable, haciendo imposible runs deterministas. A pesar de estas limitaciones, el código es sorprendentemente expresivo para su tamaño: implementa un motor de plataformas funcional, IA de persecución con escalada de escaleras y síntesis PCM retro, todo sin dependencias externas salvo Pygame.

---

## Grafo de flujo (ASCII)

```
                     ┌──────────────┐
                     │     MENU     │◄─────────────────────────┐
                     └──────┬───────┘                          │
                   ENTER    │                                   │
                     ┌──────▼───────┐                          │
                     │    INTRO     │  (120 frames de animación)│
                     └──────┬───────┘                          │
                  auto      │                                   │
                     ┌──────▼───────┐                          │
            ┌───────►│   PLAYING    │◄──────────────┐          │
            │        └──┬──┬──┬─┬──┘               │          │
            │     P     │  │  │ │ reach Pauline     │          │
            │        ┌──▼──┐ │ │ └──────────────────►LEVELUP──►next│
            │        │PAUSED│ │ │                             │  │
            │        └──┬──┘ │ │ lives==0                    │  │
            │     P     │    │ │ └────────────────────────────►GAMEOVER
            └───────────┘    │ │ dead_anim_done + lives>0    │
                             │ │ └──────────────┬────────────┘  │
                          ESC│ │                │respawn         │
                             │ │                └───────────────►┘
                             └─┴────────────────────────────────►MENU
                             ESC desde cualquier estado activo

Bucle principal (60 FPS):
  ┌─ clock.tick(60) ────────────────────────────────────────────┐
  │ 1. pygame.event.get() → QUIT / KEYDOWN (ENTER, ESC, P)      │
  │ 2. game.update()                                             │
  │    ├─ INTRO:    state_tick++; auto-advance a PLAYING         │
  │    ├─ PLAYING:  input → mario → dk → barrels → flames →      │
  │    │            bonus_items → popups → collision → death     │
  │    ├─ PAUSED:   noop                                         │
  │    └─ rest:     state_tick++                                 │
  │ 3. screen.fill(BLACK)                                        │
  │ 4. draw_* / game.draw()                                      │
  │ 5. pygame.display.flip()                                     │
  └──────────────────────────────────────────────────────────────┘
```

---

## Inventario de variables globales

### Constantes de ventana y tiempo

| Variable | Valor | Rol |
|---|---|---|
| `W, H` | 800, 600 | Dimensiones de ventana en píxeles |
| `FPS` | 60 | Tasa de refresco objetivo |
| `screen` | `Surface` | Superficie de render principal |
| `clock` | `pygame.time.Clock` | Regulador de FPS |

### Constantes físicas

| Variable | Valor | Rol |
|---|---|---|
| `GRAVITY` | 0.55 | Aceleración vertical por frame |
| `JUMP_V` | -13.0 | Velocidad inicial del salto (px/frame) |
| `WALK` | 3.2 | Velocidad horizontal de Mario (px/frame) |
| `CLIMB` | 2.8 | Velocidad de escalada (px/frame) |
| `FLAME_SPEED` | 1.4 | Velocidad base de las llamas (px/frame) |

### Paleta de colores (RGB)

`BLACK`, `WHITE`, `RED`, `BLUE`, `DKBLUE`, `LTBLUE`, `YELLOW`, `GOLD`, `BROWN`, `DKBROWN`, `GIRDCOL`, `GIRDHI`, `GIRDSH`, `SKIN`, `PINK`, `GREEN`, `GRAY`, `LTGRAY`, `DKGRAY`, `ORANGE`, `RHAT`, `CREAM`, `LADDC`, `LADDS`, `FLMYEL`, `FLMORG`, `FLMRED`, `DKMONK`, `NIGHT1`, `NIGHT2`, `BARREL_D`, `BARREL_L`, `PURPLEC`, `CYAN`, `NEONRED`

### Fuentes

| Variable | Tamaño | Rol |
|---|---|---|
| `FONT_XL` | 52 bold monospace | Títulos de pantalla |
| `FONT_BIG` | 34 bold monospace | Subtítulos |
| `FONT_MED` | 22 bold monospace | Mensajes de estado |
| `FONT_SM` | 16 monospace | HUD, instrucciones |
| `FONT_XS` | 13 monospace | Notas al pie |

### Sonidos

`SND_JUMP`, `SND_LAND`, `SND_WALK`, `SND_CLIMB`, `SND_BARREL`, `SND_DIE`, `SND_SCORE`, `SND_WIN`, `SND_THROW`, `SND_FLAME`, `SND_BONUS`, `SND_LVLUP`

### Blueprint de nivel

```python
PLATFORMS = [
    (xl, xr, y_surface, barrel_direction, pid),
    ...  # 5 plataformas: Ground (y=535), P2–P4 (y=425,315,205), Top DK (y=95)
]

LADDERS = [
    (x_center, y_top, y_bottom),
    ...  # 7 escaleras interconectando todos los niveles
]
```

Posiciones clave: `DK_CX=115`, `DK_BY=95`, `PAULINE_CX=620`, `MARIO_START_CX=60`, `MARIO_START_BY=535`

### Constantes de bonus

`BONUS_KINDS = ['purse', 'hat', 'umbrella']`
`BONUS_VALUES = {'purse': 300, 'hat': 500, 'umbrella': 800}`

### Estados de máquina de estados

`MENU`, `PLAYING`, `GAMEOVER`, `WIN`, `PAUSED`, `LEVELUP`, `INTRO`

---

## Inventario de clases y funciones

### Funciones auxiliares de dibujo

| Función | Firma | Rol |
|---|---|---|
| `rect()` | `(surf, col, x, y, w, h, r=0)` | Wrapper `pygame.draw.rect` con border_radius |
| `circle()` | `(surf, col, cx, cy, rad)` | Wrapper `pygame.draw.circle` con cast a int |
| `poly()` | `(surf, col, pts)` | Wrapper `pygame.draw.polygon` |
| `text_shadow()` | `(surf, font, msg, col, x, y, shadow, ox, oy)` | Texto con sombra offset |
| `center_text()` | `(surf, font, msg, col, cy, shadow=True)` | Texto centrado horizontalmente |

### Funciones de síntesis de audio

| Función | Firma | Rol |
|---|---|---|
| `_tone()` | `(freq, dur, vol, shape, decay, attack)` | Genera PCM mono de tono simple (square/saw/tri/sine) |
| `_chord()` | `(freqs, dur, vol)` | Genera PCM de acorde de senos |
| `_slide()` | `(f0, f1, dur, vol, shape)` | Genera PCM con glissando lineal de frecuencia |
| `play()` | `(snd)` | Reproduce un `Sound` con manejo de errores |

### Funciones de sprites

| Función | Rol |
|---|---|
| `draw_girder(surf, xl, xr, y, h)` | Viga naranja con resaltes, sombras y remaches |
| `draw_ladder(surf, cx, yt, yb)` | Escalera amarilla con peldaños |
| `draw_mario(surf, cx, by, frame, facing, state, dead_anim, scale)` | Mario 32×44 px, tres estados animados (walk/jump/climb/dead) |
| `draw_dk(surf, cx, by, frame, throwing)` | Donkey Kong 66×84 px, con postura de lanzamiento |
| `draw_barrel(surf, cx, by, roll_frame)` | Barril 18×14 px con bandas animadas |
| `draw_flame(surf, cx, by, frame)` | Llama animada con polígonos escalonados |
| `draw_pauline(surf, cx, by, frame)` | Pauline 28×48 px con oleada alternante |
| `draw_bonus_item(surf, cx, by, kind, frame)` | Ítem de bonus: bolso/sombrero/paraguas con bob sinusoidal |
| `draw_background(surf, t)` | Gradiente de cielo nocturno + estrellas parpadeantes + silueta de ciudad |

### Clases del dominio

#### `ScorePopup`
Popup de puntuación flotante. Campos: `x`, `y`, `vy`, `text`, `color`, `life`. Métodos: `update()`, `draw()`. Propiedad: `alive`.

#### `Platform`
Viga de plataforma. Campos: `xl`, `xr`, `y`, `direction`, `pid`, `rect`. Métodos: `draw()`, `contains_x()`.

#### `Ladder`
Escalera. Campos: `cx`, `yt`, `yb`, `rect`. Métodos: `draw()`, `mario_aligned()`, `mario_can_grab()`.

#### `Barrel`
Barril rodante con física de gravedad. Campos: `x`, `y`, `vx`, `vy`, `on_ground`, `platforms`, `speed_mult`, `roll_frame`, `alive`, `_current_pid`. Propiedad: `rect`. Métodos: `update()`, `draw()`.

#### `Flame`
Enemigo llama con IA de persecución y escalada de escaleras. Campos: `x`, `y`, `vx`, `vy`, `on_ground`, `platforms`, `ladders`, `speed_mult`, `frame_count`, `alive`, `_climb_ladder`, `_climbing`, `_climb_dir`. Propiedad: `rect`. Métodos: `update(mario_x, mario_y)`, `draw()`.

#### `Pauline`
Personaje estático con animación de oleada. Campos: `cx`, `by`, `frame`. Propiedad: `rect`. Métodos: `update()`, `draw()`.

#### `DonkeyKong`
Antagonista principal con temporizador de lanzamiento. Campos: `cx`, `by`, `frame`, `throw_timer`, `throw_cd`, `throwing`, `throw_flash`. Métodos: `update(speed_mult, level) → bool`, `draw()`.

#### `BonusItem`
Ítem coleccionable con tiempo de vida. Campos: `x`, `y`, `kind`, `value`, `frame`, `alive`, `life`. Propiedad: `rect`. Métodos: `update()`, `draw()`.

#### `Mario`
Protagonista controlado por teclado. Campos: `cx`, `by`, `vx`, `vy`, `on_ground`, `climbing`, `facing`, `state`, `frame`, `walk_tick`, `anim_tick`, `invincible`, `dead_anim`, `_ladder`, `_step_snd`. Constantes de clase: `W2=14`, `H2=42`. Propiedades: `rect`, `feet_y()`, `head_y()`. Métodos: `reset()`, `handle_input()`, `_do_jump()`, `_on_any_ladder()`, `update()`, `draw()`, `kill()`, `is_dead_anim_done()`.

#### `Game`
Coordinador central. Campos: `state`, `score`, `high_score`, `lives`, `level`, `tick`, `state_tick`, `platforms`, `ladders`, `mario`, `dk`, `pauline`, `barrels`, `flames`, `bonuses`, `popups`, `bonus_timer`, `_barrel_q`, `_flame_timer`, `_bonus_spawn`, `_jmp_barrel_reward`. Métodos: `_build_level()`, `_init_entities()`, `start_game()`, `_speed_mult()`, `_spawn_barrel()`, `_spawn_flame()`, `add_score()`, `update()`, `_update_intro()`, `_update_playing()`, `_win_level()`, `next_level()`, `draw()`, `handle_event()`.

### Funciones de pantalla

| Función | Pantalla |
|---|---|
| `draw_menu(surf, tick, high_score)` | Menú principal animado |
| `draw_intro(surf, tick)` | Animación introductoria de DK cargando a Pauline |
| `draw_game_over(surf, tick, score)` | Pantalla de fin de juego |
| `draw_win(surf, tick, score)` | Pantalla de victoria |
| `draw_level_up(surf, tick, level, score)` | Pantalla de nivel completado |
| `draw_paused(surf)` | Overlay semitransparente de pausa |
| `draw_hud(surf, score, high_score, lives, level, bonus_timer)` | HUD superior con iconos de vidas |

### Función principal

`main()` — Bucle de juego principal a 60 FPS.

---

## IO y dispositivos

| Dispositivo | Uso |
|---|---|
| `pygame.display` | Ventana 800×600, doble buffer implícito con `display.flip()` |
| `pygame.mixer` | Frecuencia 22 050 Hz, mono 16-bit, buffer 512 samples |
| `pygame.key` | `get_pressed()` para movimiento continuo; `KEYDOWN` para acciones discretas (ENTER, P, ESC) |
| `pygame.time.Clock` | `tick(60)` para regular el bucle |
| `random` (stdlib) | RNG global no inicializado para estrellas de fondo, posición de bonus, dirección inicial de llamas |

---

## Algoritmos identificados

### Física por integración de Euler (semi-implícita)

Cada frame: `vy += GRAVITY`, `y += vy`, `x += vx`. La detección de colisión se realiza a posteriori: si el objeto penetra la plataforma, se snappea a `plat.y` y se resetea `vy=0`. La integración es simple y estable para las velocidades usadas (GRAVITY=0.55, máx caída ~20 px/frame antes del snap).

### Detección de colisión AABB

Se usan `pygame.Rect.colliderect()` para todas las colisiones Mario-Barril, Mario-Llama, Mario-Bonus y Mario-Pauline. Los rects de los objetos se calculan a partir de sus posiciones centrales con half-widths fijos.

### Zigzag de barriles entre plataformas

El barril adopta la dirección (`+1`/`-1`) de cada plataforma en la que aterriza (`plat.direction`). Esto reproduce el zigzag del arcade original sin necesidad de lógica de steering explícita.

### IA de llama: persecución + escalada de escalera

En fase terrestre la llama aplica steering proporcional: `vx += (target_vx - vx) * 0.04`. Cada 40 frames, si está junto a una escalera, evalúa si escalar acerca a Mario en Y: si sí, entra en modo escalada (`_climbing=True`) y sube/baja verticalmente hasta el extremo de la escalera.

### Síntesis PCM procedural

Tres primitivas de síntesis:
- `_tone(freq, dur, shape)` — oscilador de forma de onda (square, saw, tri, sine) con envelope attack/decay.
- `_chord(freqs, dur)` — suma de senos normalizada con decay.
- `_slide(f0, f1, dur, shape)` — glissando con integración de fase acumulada (evita clics de fase).

Los buffers son `array.array('h', ...)` (int16) pasados directamente a `pygame.mixer.Sound`.

---

## Bugs y rarezas

### 1. `DK_BY=60` causaba sprite fuera de pantalla (corregido a 95)
La constante original definía `DK_BY=60`, que con un sprite de 84 px de altura posicionaría la cabeza de DK a `60-84 = -24` px, parcialmente fuera de pantalla. El valor fue corregido a `DK_BY=95` para que el sprite quede completamente visible sobre la plataforma superior (y=95).

### 2. `MARIO_START_BY=505` hacía flotar a Mario (corregido a 535)
Con `MARIO_START_BY=505`, Mario aparecía 30 px por encima de la plataforma del suelo (y=535), provocando que cayera al inicio y sonara `SND_LAND` en el primer frame. Corregido a `535` para que Mario arranque con los pies exactamente en el suelo.

### 3. Superficie de DK demasiado pequeña para el círculo de la cabeza (corregido)
La cabeza de DK se dibuja con `circle(s, FUR, 33, 17, 17)` (radio 17, centro y=17), pero la superficie original era de 66×80 px. La parte superior del círculo queda en y=0, lo que recortaba 2 px superiores. La superficie se amplió a 66×84 px para que los pies y la cabeza quepan sin recorte.

### 4. No hay separación de capas de render
Todo el código de dibujo vive en la misma función `game.draw()` o en funciones `draw_*` globales. No existe separación entre lógica de dominio y presentación, lo que impide cambiar el backend gráfico sin reescribir el juego.

### 5. RNG global no inyectable
Se usa `random` del módulo estándar sin inicializar la semilla, por lo que el comportamiento no es reproducible entre ejecuciones. Esto hace imposible implementar un modo demo determinista o escribir tests basados en propiedades que dependan del RNG.

### 6. Sin persistencia de puntuación máxima
`high_score` vive únicamente en el objeto `Game` y se pierde al cerrar la ventana. No existe serialización a disco.

### 7. Sin modo demo
El juego no tiene un modo de atracción (attract mode) automático que se active tras un timeout en el menú, a diferencia del arcade original.

### 8. Ventanas de colisión de barriles inconsistentes
El barril detecta colisión con plataformas si `0 < self.y - plat.y < 24`, pero el sprite del barril tiene H2=14 px. El margen extra de 10 px provoca que un barril "aterrice" visualmente flotando sobre la viga en casos de caída rápida.

---

## Decisiones de época

**Todo en un archivo.** En 2025, con herramientas modernas (uv, src layout, mypy), lo normal es distribuir la lógica en módulos. El autor eligió deliberadamente un único archivo para maximizar la portabilidad: se puede copiar y ejecutar con `python donkeykong.py` sin instalación.

**Estado global mutable.** Las constantes de nivel (`PLATFORMS`, `LADDERS`) y los objetos de fuentes y sonidos se crean al importar el módulo. Esto es un patrón pre-PEP 20 que facilita el prototipado rápido pero impide la inicialización lazy y complica el testing.

**Dibujo procedural sin assets.** Todos los sprites se generan frame a frame con `pygame.draw.*`. Esta decisión elimina la necesidad de ficheros de imagen externos y garantiza que el juego funcione en cualquier entorno con Pygame instalado, a costa de mayor complejidad en el código de dibujo y de sprites menos detallados que los originales.
