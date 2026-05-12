"""Tests de integración del motor de juego de donkeykong.

Verifica la correcta interacción entre la capa de aplicación y la capa
de infraestructura: persistencia de scores, carga de settings, síntesis
de sonido y flujo completo de estados de juego.

Estos tests pueden inicializar pygame en modo headless usando las
variables de entorno SDL_VIDEODRIVER=dummy y SDL_AUDIODRIVER=dummy.

Example:
    Ejecutar tests de integración::

        SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy uv run pytest tests/integration/ -v
"""
