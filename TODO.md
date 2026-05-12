# TODO — Mejoras para v1.1

Este fichero recoge las mejoras planificadas para la versión 1.1. Las tareas están ordenadas por prioridad decreciente.

---

## Alta prioridad

### Sprites cargados desde PNG assets
- Añadir directorio `src/donkeykong/assets/sprites/` con PNGs en pixel art (escala 2×).
- Implementar `SpriteLoader` en `infrastructure/` que cargue y escale los PNG con `pygame.image.load()`.
- Mantener los sprites procedurales como fallback si los PNG no están presentes.
- Requerirá actualizar el `pyproject.toml` para incluir los assets en el wheel (`[tool.hatch.build.targets.wheel] include = ["src/donkeykong/assets/sprites/**"]`).

### Música de fondo con pygame mixer
- Componer o licenciar libremente una pieza MIDI/OGG con estética 8-bit inspirada en el tema original.
- Implementar `BackgroundMusic` en `infrastructure/sound.py` usando `pygame.mixer.music.load()` y `play(-1)` (loop).
- Control de volumen independiente de los efectos de sonido vía settings.

### Niveles 2 y 3 con layouts diferentes
- Definir `PLATFORMS_L2`, `LADDERS_L2` en `domain/level.py` con un layout de vigas inclinadas (como el nivel de "Rivets" del arcade original).
- Definir `PLATFORMS_L3`, `LADDERS_L3` con un layout de barril con elevadores.
- La `Game` seleccionará el blueprint de nivel según `self.level % 3`.

---

## Prioridad media

### Modo multijugador local
- Añadir soporte para un segundo jugador controlado por teclado (teclas IJKL).
- El segundo jugador controla a Luigi (sprite variante de Mario en verde).
- La puntuación es compartida; las vidas se mantienen separadas.
- Requiere adaptar `domain/entities.py` para soportar múltiples jugadores.

### Leaderboard online (opcional, experimental)
- Endpoint REST mínimo (`POST /scores`) alojado en un VPS o en un servicio gratuito (Railway, Render).
- El cliente envía `{ "name": str, "score": int, "seed": int }` al cerrar la partida.
- `GET /scores?limit=10` devuelve el top 10 global.
- La petición es best-effort: si falla, no interrumpe el juego.
- Requiere añadir `httpx>=0.27` a las dependencias.

### Controles remapeables
- Añadir sección `[controls]` en `~/.config/donkeykong/settings.toml`.
- La CLI expondrá `donkeykong config --edit-controls` para abrir el fichero en `$EDITOR`.
- El módulo `presentation/input.py` leerá el mapa de teclas desde `Settings`.

---

## Prioridad baja

### Port a WebAssembly / Pyodide
- Investigar la viabilidad de compilar `donkeykong` con Pyodide (Python en WebAssembly).
- pygame-ce tiene soporte experimental para Emscripten/WASM desde la versión 2.5.
- El objetivo es ofrecer una versión jugable en el navegador sin instalación.
- Requiere eliminar las dependencias de XDG (persistencia en `localStorage` del navegador).

### Modo accesibilidad `--slow`
- Añadir flag `--slow` que reduce el `speed_mult` global a 0.5.
- Útil para usuarios con menor tiempo de reacción.

### Soporte de gamepad
- Usar `pygame.joystick` para detectar controladores USB/Bluetooth.
- Mapear: analógico izquierdo → movimiento, A/B → saltar.

### Tests de regresión visual
- Capturar el estado del framebuffer en el frame 300 de una partida `--demo` y guardarlo como PNG de referencia.
- El test compara el frame actual con el PNG de referencia usando hash SHA-256.
- Si el hash difiere, el test falla e imprime un diff visual.

### Documentación de la API de dominio
- Generar documentación HTML desde docstrings con `pdoc3` o `mkdocs`.
- Publicar automáticamente en GitHub Pages desde el workflow de CI.
