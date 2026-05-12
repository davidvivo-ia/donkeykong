# ADR 0001 — Capa de presentación: pygame-ce

**Estado:** Aceptado  
**Fecha:** 2026-05-12  
**Autores:** davidvivo-ia

---

## Contexto

El proyecto es una recreación de un juego arcade con las siguientes características técnicas:

- Sprites en movimiento continuo a 60 FPS.
- Detección de colisiones pixel-accurate (AABB) entre múltiples entidades.
- Animaciones frame a frame (Mario, DK, llamas, barriles).
- Síntesis de audio PCM en tiempo real mediante `pygame.mixer.Sound`.
- Fondo animado con gradiente de cielo, estrellas parpadeantes y ciudad.
- HUD con actualización cada frame.

Se consideraron tres opciones de presentación:

1. **pygame-ce** (Community Edition de pygame).
2. **Biblioteca TUI** (como `textual` o `curses`).
3. **Motor de juego completo** (como Godot con bindings Python, o Arcade de Python).

---

## Decisión

Usamos **pygame-ce** como backend de presentación.

---

## Razonamiento

### Por qué no TUI

Las bibliotecas TUI (textual, rich-live, curses) trabajan con caracteres de terminal, cuya granularidad mínima es una celda de ~8×16 px. Esto impide:

- **Movimiento sub-pixel:** la física usa `float` para posición (Mario puede estar en x=34.7). En TUI, esto se redondea a celda entera, haciendo el movimiento entrecortado.
- **Animaciones frame a frame:** el loop de refresco de un terminal depende del driver de terminal y puede introducir latencia variable. A 60 FPS la diferencia es apreciable.
- **Síntesis de audio:** los terminales no tienen API de audio. Habría que integrar una biblioteca externa adicional (como `sounddevice`), eliminando la ventaja de simplicidad.
- **Gradientes de color en el fondo:** los gradientes de cielo requieren acceso a píxeles individuales, imposible en TUI.

### Por qué no un motor completo (Godot, Arcade)

- **Godot con Python:** requiere el motor instalado (~600 MB), no es instalable con `uv sync`.
- **Python Arcade:** no tiene síntesis PCM nativa; requiere assets de imagen para sprites de calidad comparable.
- **Sobrecarga conceptual:** el proyecto tiene un dominio acotado y bien definido. Un motor ECS completo añadiría abstracción sin beneficio para 1 377 líneas originales.

### Por qué pygame-ce

| Criterio | pygame-ce |
|---|---|
| Sprites con colisiones pixel | Nativo (`pygame.Rect.colliderect`) |
| Movimiento continuo a 60 FPS | `pygame.time.Clock.tick(60)` |
| Animaciones frame a frame | Loop de dibujo manual, control total |
| Síntesis PCM | `pygame.mixer.Sound(buffer=array)` |
| Instalable con uv | `pip install pygame-ce` — sí |
| Headless para CI | `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` |
| Activamente mantenida | pygame-ce mantiene parity con SDL 2.x y recibe commits regulares |
| Sin assets requeridos | `pygame.draw.*` permite sprites procedurales |

pygame-ce es la bifurcación de pygame con soporte activo para Python 3.12+ y correcciones de bugs críticos que la rama oficial no ha incorporado. Es un drop-in replacement: mismo API, mismos imports.

---

## Consecuencias

- **Positivas:** el código de presentación puede correr sin GPU (solo SDL software renderer). La CI en GitHub Actions no requiere X11 real.
- **Negativas:** pygame-ce no tiene un sistema de escenas nativo. La máquina de estados de pantallas debe implementarse manualmente en `application/state_machine.py`.
- **Neutrales:** los sprites procedurales son más frágiles ante cambios de resolución que los PNG escalables, pero permiten regeneración completa sin dependencias de assets.
