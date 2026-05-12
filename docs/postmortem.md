# Postmortem — Donkey Kong Reimaginado

## Qué se ganó

**Testabilidad real.** La separación de la física en funciones puras hizo posible escribir tests unitarios que no requieren pygame. Esto fue el mayor beneficio: el CI corre la suite completa sin display virtual. En el monolito original, testear `mario.update()` exigía inicializar la ventana, los sonidos y el reloj.

**Legibilidad arquitectónica.** Un desarrollador nuevo puede leer `application/game.py` y entender el flujo completo sin conocer pygame. Las capas son fronteras conceptuales que reducen la carga cognitiva de navegar 1 377 líneas dispersas.

**RNG controlado.** El modo `--demo` y los tests deterministas no habrían sido posibles sin inyectar el RNG. Esta decisión, aparentemente menor, desbloqueó tests de propiedad robustos con Hypothesis.

**Puntuación persistente.** Los usuarios no pierden su récord al cerrar el juego. Es una mejora de calidad de vida que costó menos de 50 líneas.

## Qué se perdió

**Espontaneidad del prototipo.** El monolito de 1 377 líneas se puede editar, ejecutar y ver el resultado en segundos. Con la arquitectura en capas, añadir una nueva mecánica requiere pensar en qué capa pertenece, cómo se propaga entre capas y cómo se testea. El scaffolding tiene un coste de fricción real.

**La magia del sprite procedural sin andamiaje.** `draw_dk()` en el original es directamente legible: triángulos, círculos, colores. En la versión refactorizada, la misma función vive en `presentation/sprites.py` e importa constantes de `domain/` y colores de `presentation/palette.py`. La linealidad original se ha distribuido.

## Qué dice sobre 40 años de evolución del oficio

En 1981, un juego arcade cabía en 8 KB de ROM. La limitación era el hardware. Hoy, el mismo juego en Python ocupa 1 377 líneas y depende de cinco bibliotecas externas. Hemos ganado potencia expresiva, type safety, tests automatizados, CI y gestión de dependencias. Hemos perdido la inmediatez de escribir directamente contra el metal.

La arquitectura limpia que aplicamos aquí habría sido impensable en el Z80 del DK original: era un lujo reservado para sistemas con suficiente RAM para mantener abstracciones. Cuarenta años después, la abstracción es barata y la comprensibilidad es cara. El postmortem más honesto es este: pasamos de optimizar para la máquina a optimizar para el siguiente programador. No está claro que siempre sea un progreso neto.
