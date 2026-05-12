"""Punto de entrada CLI del juego.

Invocable como:
    uv run donkeykong
    python -m donkeykong
    uv run donkeykong --demo
    uv run donkeykong --seed 42
"""

from __future__ import annotations

import logging

import structlog
import typer
from rich.console import Console

from donkeykong.infrastructure.config import GameConfig

app = typer.Typer(
    name="donkeykong",
    help="Donkey Kong — recreación arcade clásico en Python/pygame-ce.",
    add_completion=False,
)
console = Console()


def _setup_logging(dev: bool) -> None:
    """Configura structlog con render bonito en dev, JSON en prod."""
    level = logging.DEBUG if dev else logging.INFO
    processors: list[structlog.types.Processor]
    if dev:
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = [
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logging.basicConfig(level=level)


@app.command()
def main(
    demo: bool = typer.Option(False, "--demo", help="Modo demo: IA juega automáticamente."),
    seed: int | None = typer.Option(None, "--seed", help="Semilla RNG para partida reproducible."),
    no_sound: bool = typer.Option(False, "--no-sound", help="Desactiva el audio."),
    dev: bool = typer.Option(False, "--dev", help="Activa logging detallado."),
) -> None:
    """Inicia el juego Donkey Kong.

    Args:
        demo: activa la IA que juega sola (determinista con semilla fija).
        seed: semilla para RNG reproducible; implica --demo si se combina.
        no_sound: desactiva todos los sonidos.
        dev: logging verbose.
    """
    _setup_logging(dev)

    config = GameConfig()
    if no_sound:
        config = config.model_copy(update={"enable_sound": False})

    # Importación diferida para que typer --help no requiera pygame
    from donkeykong.presentation.game_loop import run

    run(config=config, demo=demo, seed=seed)


if __name__ == "__main__":
    app()
