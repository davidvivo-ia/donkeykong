"""Suite de tests para el paquete donkeykong.

Los tests están organizados en tres suites:

- unit/: tests unitarios del dominio puro (sin pygame, sin IO).
- integration/: tests de integración del motor de juego (app + infra).
- property/: tests de propiedad con Hypothesis (invariantes del dominio).

Example:
    Ejecutar todos los tests::

        uv run pytest

    Ejecutar solo los tests unitarios::

        uv run pytest tests/unit/ -v
"""
