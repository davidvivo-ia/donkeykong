# Sistema de diseño — Donkey Kong Reimaginado

## Concepto

**"Arcade clásico reimaginado — píxeles grandes, luz fosforescente, ciudad nocturna de fondo"**

La dirección de arte parte de la fidelidad al original de 1981 pero eleva la resolución conceptual: los sprites siguen siendo pixel art construido con primitivas geométricas, pero cada elemento tiene un ligero halo de fósforo que evoca los monitores CRT de los salones arcade. El fondo es una silueta urbana nocturna con ventanas que parpadean, creando profundidad sin desviar la atención del juego.

---

## Paleta de colores

| Token semántico | Hex | RGB | Rol |
|---|---|---|---|
| `COLOR_NIGHT_SKY` | `#08082A` | (8, 10, 42) | Fondo superior del cielo |
| `COLOR_NIGHT_HORIZON` | `#121950` | (18, 25, 80) | Fondo inferior del cielo / gradiente |
| `COLOR_GIRDER` | `#C88228` | (200, 130, 40) | Vigas de la estructura |
| `COLOR_GIRDER_HI` | `#F0B450` | (240, 180, 80) | Resalte superior de viga / remaches |
| `COLOR_MARIO_RED` | `#DC2828` | (220, 40, 40) | Sombrero y camisa de Mario |
| `COLOR_MARIO_BLUE` | `#3264DC` | (50, 100, 220) | Peto de Mario |
| `COLOR_FLAME_CORE` | `#FFEB50` | (255, 235, 80) | Núcleo amarillo de la llama |

**Paleta extendida (uso secundario):** `GOLD(210,160,0)`, `SKIN(255,195,145)`, `PINK(255,140,160)`, `GREEN(30,160,30)`, `CYAN(0,200,210)`, `ORANGE(230,120,0)`, `NEONRED(255,50,80)`.

---

## Tipografía

### HUD y mensajes en juego

**Familia:** `monospace` (SysFont — acepta Courier New, DejaVu Mono o Consolas según el SO).

| Nombre | Tamaño | Peso | Uso |
|---|---|---|---|
| `FONT_XL` | 52 px | Bold | Títulos: "DONKEY KONG", "GAME OVER", "YOU WIN!" |
| `FONT_BIG` | 34 px | Bold | Subtítulos: "STAGE CLEAR!", "HOW HIGH CAN YOU GET?" |
| `FONT_MED` | 22 px | Bold | Mensajes de estado, puntuación final |
| `FONT_SM` | 16 px | Normal | HUD en juego: SCORE, BEST, LVL, instrucciones |
| `FONT_XS` | 13 px | Normal | Notas al pie, créditos |

### CLI (fuera del juego)

`rich` formatea el output de la CLI con colores ANSI. No se usa tipografía personalizada; se hereda la fuente del terminal del usuario.

---

## Espaciado

Todo el espaciado usa múltiplos de **4 px** para mantener la coherencia en la cuadrícula de pixel art.

| Concepto | Valor |
|---|---|
| Unidad base | 4 px |
| Altura de plataforma | 14 px (= 3.5 × 4, redondeado al pixel natural) |
| Anchura de escalera | 16 px (= 4 × 4) |
| Separación entre peldaños | 14 px |
| Separación entre vigas | 110 px (= 27.5 × 4, dictada por la rejilla del nivel) |
| Margen del HUD | 8 px superior + 8 px inferior |
| Separación de texto en menú | 22 px entre líneas |

---

## Sprites (pixel art procedural con `pygame.draw`)

Todos los sprites se generan en tiempo de ejecución sin ficheros de imagen. Se dibujan sobre `pygame.Surface` con `SRCALPHA` y se vuelcan al framebuffer con `blit`.

| Sprite | Dimensión | Técnica principal |
|---|---|---|
| Mario | 32 × 44 px | `rect` + `circle`, 3 estados animados (walk 2f, jump 1f, climb 2f) |
| Donkey Kong | 66 × 84 px | `ellipse` + `circle` + `line`, postura de lanzamiento alterna |
| Barril | 18 × 14 px | `rect` redondeado, bandas que rotan con `roll_frame` |
| Llama | 16 × 18 px | `polygon` de 3 capas concéntricas (rojo/naranja/amarillo), ojos |
| Pauline | 28 × 48 px | `rect` + `circle`, oleada alternante de brazos |
| Viga (girder) | variable × 14 px | `rect` con 3 capas (sombra/cuerpo/resalte) + remaches con `circle` |
| Escalera | 16 × variable px | 2 palos con `rect`, peldaños con `rect` |
| Bonus (bolso) | ~20 × 22 px | `circle` concéntrico + asa con `rect`, bob sinusoidal |
| Bonus (sombrero) | ~16 × 16 px | `rect` apilados |
| Bonus (paraguas) | ~20 × 20 px | `arc` + `line` + `arc` |
| Iconos de vidas | 16 × 23 px | Mario escalado al 52% con `pygame.transform.scale` |

---

## Estados visuales

### `splash` / `menu`
- Fondo: cielo nocturno animado + ciudad parpadeante.
- Centro: caja semitransparente con borde dorado, título "DONKEY KONG" en dos líneas (naranja/amarillo).
- DK animado con movimiento sinusoidal horizontal; Mario corriendo en loop por la parte baja.
- Instrucciones de controles en gris claro.
- High score en dorado si existe.

### `intro`
- DK baja desde la cima cargando a Pauline (animación de 120 frames).
- Texto "HOW HIGH CAN YOU GET?" en amarillo.

### `playing`
- Canvas completo con fondo, plataformas, escaleras, entidades y HUD.
- HUD: franja oscura superior con SCORE (amarillo), BEST (dorado), LVL (cyan), vidas (iconos Mario).
- Barra de bonus en verde que se agota con el tiempo.
- Score popups flotantes coloreados según tipo (amarillo = normal, cyan = salto sobre barril, dorado = bonus).

### `paused`
- El canvas de juego se mantiene debajo con un overlay semitransparente `(0,0,0,140)`.
- Texto "PAUSED" en blanco centrado.

### `game_over`
- Fondo de cielo nocturno.
- "GAME OVER" en rojo, puntuación final en blanco.
- Instrucciones de reinicio aparecen con delay de 90 frames.

### `level_up`
- Fondo de cielo nocturno.
- "LEVEL N" en cyan, "STAGE CLEAR!" en amarillo, puntuación en blanco.

### `win`
- Fondo de cielo nocturno.
- "YOU WIN!" en amarillo, "Pauline is rescued!" en rosa, puntuación en blanco.

---

## Toque distintivo: efecto phosphor glow

Cada sprite principal (Mario, DK, llamas) recibe un halo de luz fosforescente que simula el desgaste del fósforo en los monitores CRT de los salones arcade. La implementación usa una segunda `Surface` con `SRCALPHA` levemente desenfocada (implementado como `pygame.transform.smoothscale` + composición `BLEND_RGBA_ADD`) tintada en el color dominante del sprite.

**Paleta de glow:**
- Mario → halo rojo tenue `(60, 0, 0, 80)`.
- DK → halo marrón cálido `(40, 20, 0, 60)`.
- Llamas → halo naranja brillante `(80, 40, 0, 100)`.
- Bonus → halo amarillo pálido `(60, 50, 0, 70)`.

### Sonidos PC-speaker sintetizados

Los 12 efectos de sonido se generan con síntesis PCM directa (sin ficheros de audio). El estilo intencional es el del altavoz interno de PC de los años 80: ondas cuadradas, dientes de sierra y acordes de senos sin reverb ni compresión. Los parámetros de cada sonido están documentados en `docs/adr/0004-sound-synthesis.md`.

---

## Accesibilidad

- **Control total por teclado.** No se requiere ratón en ningún punto del flujo. Menú, juego, pausa, reinicio: todo es navegable con las flechas, WASD, espacio y ENTER.
- **Controles remapeables** (v1.1): la capa de input admite un mapa de teclas configurable en `settings.toml`.
- **Sin dependencia de color crítica.** Los elementos clave del HUD (score, vidas) usan texto además de color, por lo que son legibles en condiciones de daltonismo.
- **Velocidad ajustable** (v1.1): `--slow` reduce el multiplicador de velocidad global para usuarios que necesiten más tiempo de reacción.
- **Sin flashes rápidos continuos.** El efecto de parpadeo de invencibilidad de Mario tiene una frecuencia de 15 Hz (un ciclo cada 4 frames a 60 FPS), dentro del límite de seguridad epiléptica de la WCAG (< 3 Hz es seguro; > 3 Hz debe evitarse para patrones de alto contraste; 15 Hz en un sprite pequeño sobre fondo complejo no supera el umbral de área).
