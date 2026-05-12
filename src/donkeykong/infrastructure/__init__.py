"""Capa de infraestructura — IO, RNG, sonido, persistencia y configuración.

Implementa los protocolos definidos en el dominio y proporciona adaptadores
para recursos externos: sistema de ficheros, mezclador de audio de pygame,
generador de números aleatorios y configuración del usuario.

Modules:
    rng: Implementaciones de RNGProtocol (SeededRNG, SystemRNG).
    sound: Síntesis PCM procedural de los 12 efectos de sonido.
    persistence: ScoreRepository — carga y guarda scores.json en XDG.
    config: Settings (pydantic v2) y xdg_data_dir().

Note:
    Esta capa sí puede importar pygame (para el mezclador de sonido),
    pydantic (para settings y persistencia) y pathlib/os (para XDG).
    No debe importar typer ni structlog directamente — esos pertenecen
    a la capa de aplicación.
"""
