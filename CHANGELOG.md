# Changelog

Todos los cambios notables de este proyecto se documentan en este fichero.  
Formato basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-05-12

### Preservado del original

- **Mecánicas de plataformas:** física por integración de Euler semi-implícita con snap a plataformas, gravitación constante (GRAVITY=0.55), salto con velocidad inicial JUMP_V=-13.0.
- **Sistema de barriles:** los barriles adoptan la dirección de cada plataforma en la que aterrizan, reproduciendo el zigzag del arcade original. Velocidad escalada con el nivel.
- **Sistema de llamas:** IA de persecución proporcional (steering suave) con escalada autónoma de escaleras hacia Mario. Spawn desde el bidón de aceite en la esquina inferior izquierda.
- **Cinco plataformas** interconectadas por siete escaleras, reproduciéndose el layout del nivel 1 del arcade original.
- **Sprites procedurales:** Mario (32×44 px, 3 estados animados), Donkey Kong (66×84 px, postura de lanzamiento), Pauline (28×48 px, oleada de brazos), barriles (18×14 px con bandas animadas), llamas (polígonos concéntricos), vigas con remaches y escaleras con peldaños.
- **Sonidos PC-speaker sintetizados:** 12 efectos de sonido generados con síntesis PCM procedural (`_tone`, `_chord`, `_slide`) a 22 050 Hz mono 16-bit.
- **Fondo animado:** gradiente de cielo nocturno, 80 estrellas parpadeantes, silueta de ciudad con ventanas.
- **Sistema de puntuación:** 100 pts por saltar sobre un barril, 300/500/800 pts por bonus items, 5 000 pts + bonus de tiempo al rescatar a Pauline.
- **Tres vidas** con sprite de vida en el HUD. Invencibilidad de 90 frames tras respawn.
- **Barra de bonus de tiempo** que se agota en 60 segundos por nivel.
- **Múltiples niveles** con escalado de velocidad por nivel (×1.12 por nivel adicional).

### Modernizado

- **Arquitectura por capas:** dominio puro, aplicación, infraestructura y presentación con Dependency Rule estricta.
- **Frozen dataclasses con `__slots__`:** entidades del dominio inmutables y testeables sin pygame.
- **`mypy --strict`** aplicado a todo el código fuente.
- **ruff** como linter y formateador (line-length=100, target-version=py313).
- **uv** como gestor de entornos y dependencias (reemplaza pip + venv).
- **pyproject.toml PEP 621** como único fichero de configuración del proyecto.
- **structlog** para logging estructurado de eventos de juego (death, level_up, score_milestone).
- **typer + rich** como interfaz de línea de comandos con ayuda autogenerada.
- **pre-commit** con ruff y mypy en los hooks de commit.
- **CI en GitHub Actions** con matrix Python 3.13 y 3.14.

### Añadido

- **Modo `--demo`:** partida con semilla RNG fija (DEMO_SEED=20250101), comportamiento completamente reproducible para modo de atracción.
- **Modo `--seed N`:** semilla personalizada para reproducir partidas exactas.
- **Persistencia de puntuación máxima:** `~/.local/share/donkeykong/scores.json` (XDG), serializado con pydantic v2.
- **RNG inyectable:** `RNGProtocol` con implementaciones `SeededRNG` y `SystemRNG`, tests deterministas con Hypothesis.
- **Tests unitarios** de física de plataformas, colisiones AABB y IA de llamas.
- **Tests de propiedad** con Hypothesis para verificar invariantes físicos (Mario no atraviesa plataformas, barril siempre cae).
- **Efecto phosphor glow:** halo de luz fosforescente sobre sprites principales, evocando monitores CRT.
- **CLAUDE.md** con instrucciones del proyecto para el agente de desarrollo.
- **Documentación completa:** análisis del programa original, arquitectura, sistema de diseño, ADRs, postmortem.

### Licencias creativas tomadas

- **Sprites más grandes:** Mario es 32×44 px (el original arcade usaba ~16×24 px en resolución de 224×256). La mayor resolución permite más detalle: bigote, hebillas del peto, dedos implícitos.
- **DK más detallado:** el sprite de 66×84 px incluye pelaje con elipses, orejas con pabellón auricular, ojos con pupila y reflejo, dientes individuales y fruncido del ceño. El DK original tenía ~16×22 px.
- **Ciudad de fondo:** el arcade original no tenía fondo nocturno. Se añade para dar profundidad sin interferir con la jugabilidad.
- **Score popups flotantes:** el arcade original mostraba el score directamente en el HUD. Los popups en color y posición del evento son una mejora de UX propia.

### Bugs corregidos

- **`DK_BY=60` causaba sprite fuera de pantalla:** la cabeza de DK quedaba a y=-24 px. Corregido a `DK_BY=95`.
- **`MARIO_START_BY=505` hacía flotar a Mario:** Mario aparecía 30 px sobre el suelo, cayendo al inicio de cada vida. Corregido a `MARIO_START_BY=535` (surface y del suelo).
- **Superficie de DK demasiado pequeña:** el círculo de la cabeza (radio 17, centro y=17) se recortaba en el borde superior. Superficie ampliada de 66×80 a 66×84 px.
- **Ventana de colisión de barril inconsistente:** el barril detectaba aterrizaje si `y - plat.y < 24` pero el sprite medía 14 px de alto. El margen extra de 10 px causaba aterrizajes visuales flotantes. Corregido al alinear la ventana con el sprite.
- **RNG global no inyectable:** `random` del módulo global sin semilla hacía imposibles los tests deterministas. Reemplazado por `RNGProtocol` inyectable.
- **Sin persistencia de `high_score`:** la puntuación máxima se perdía al cerrar la ventana. Añadida persistencia en `~/.local/share/donkeykong/scores.json`.
- **`draw_background()` recrea ventanas aleatorias cada frame:** las ventanas iluminadas de los edificios se sortean con `random.random()` en cada frame, causando parpadeo caótico incoherente. Corregido a una tabla precomputada en el arranque.
