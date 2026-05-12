"""Dominio puro del juego Donkey Kong.

Contiene las entidades del juego (frozen dataclasses con __slots__),
la física de plataformas (integración de Euler, colisión AABB) y los
protocolos de extensión (RNGProtocol, ClockProtocol).

Esta capa no importa pygame, typer, structlog, pydantic ni ninguna
dependencia externa. Solo usa la librería estándar de Python 3.13.

Modules:
    entities: Mario, Barrel, Flame, DonkeyKong, Pauline, BonusItem.
    physics: integrate_euler(), resolve_platform_collision(), aabb_check().
    level: LevelBlueprint, PLATFORMS_L1, LADDERS_L1.
    world: World — snapshot inmutable del estado completo del juego.
    events: GameEvent — eventos de dominio (death, level_up, score).
    collision: Detección de colisiones AABB entre entidades.

Note:
    Todas las entidades son inmutables. Las funciones de física devuelven
    nuevas instancias en vez de mutar el estado existente. Esto permite
    tests unitarios puramente funcionales sin setup/teardown.
"""
