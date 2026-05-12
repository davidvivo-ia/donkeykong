"""Bucle principal del juego.

Coordina el motor, el renderer, el sonido y el input.
Es el único lugar del proyecto con estado mutable (referencia al mundo actual).
"""

from __future__ import annotations

import sys

import pygame
import structlog

from donkeykong.application.demo_ai import compute_demo_input
from donkeykong.application.engine_output import EngineOutput
from donkeykong.application.game_engine import GameEngine
from donkeykong.domain.entities import GamePhase
from donkeykong.domain.world import GameWorld
from donkeykong.infrastructure.config import GameConfig
from donkeykong.infrastructure.persistence import HighScoreRepository
from donkeykong.infrastructure.rng import RNG, SeededRNG, StdRNG
from donkeykong.infrastructure.sound import SoundManager
from donkeykong.presentation.input_handler import read_input
from donkeykong.presentation.renderer import Renderer

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


def run(
    config: GameConfig,
    demo: bool = False,
    seed: int | None = None,
) -> None:
    """Inicia y ejecuta el bucle principal del juego.

    Args:
        config: configuración del juego.
        demo: si True usa la IA demo y semilla fija.
        seed: semilla RNG opcional (anula config.demo_seed en modo demo).
    """
    pygame.init()
    screen = pygame.display.set_mode((config.display.width, config.display.height))
    pygame.display.set_caption(config.display.title)
    clock = pygame.time.Clock()

    rng: RNG
    if demo or seed is not None:
        rng = SeededRNG(seed if seed is not None else config.demo_seed)
        logger.info("demo_mode", seed=seed or config.demo_seed)
    else:
        rng = StdRNG()

    repo = HighScoreRepository()
    high_score = repo.load()

    engine = GameEngine(rng)
    sound = SoundManager() if config.enable_sound else SoundManager.__new__(SoundManager)

    renderer = Renderer(screen)

    world = _make_menu_world(engine, high_score)
    menu_tick = 0

    logger.info("game_started", demo=demo)

    while True:
        # ── Eventos pygame ────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _shutdown(repo, world)
                sys.exit(0)

            if event.type == pygame.KEYDOWN:
                world = _handle_keydown(event.key, world, engine, high_score)

        # ── Input ─────────────────────────────────────────────────────────────
        if demo:
            inp = compute_demo_input(world)
        else:
            inp = read_input()

        # ── Tick del motor ────────────────────────────────────────────────────
        output: EngineOutput = engine.tick(world, inp)
        world = output.world
        sound.play_all(output.sound_events)

        # Guardar récord si mejoró
        if world.score.current > high_score:
            high_score = world.score.current
            repo.save(high_score)

        # ── Demo: salir automáticamente cuando se alcanza game_over o win ─────
        if demo and world.phase in (GamePhase.GAME_OVER, GamePhase.WIN):
            logger.info("demo_finished", score=world.score.current, phase=world.phase.name)
            _shutdown(repo, world)
            sys.exit(0)

        # ── Render ────────────────────────────────────────────────────────────
        menu_tick += 1
        renderer.render(world, menu_tick)
        pygame.display.flip()
        clock.tick(config.display.fps)


def _make_menu_world(engine: GameEngine, high_score: int) -> GameWorld:
    """Crea el mundo en fase MENU (sin lógica activa).

    Reutiliza la estructura de GameWorld pero con fase MENU.
    """
    from dataclasses import replace

    world = engine.new_game(high_score)
    return replace(world, phase=GamePhase.MENU)


def _handle_keydown(
    key: int,
    world: GameWorld,
    engine: GameEngine,
    high_score: int,
) -> GameWorld:
    """Gestiona pulsaciones de tecla que afectan al flujo de pantallas.

    Args:
        key: código de tecla pygame.
        world: estado actual.
        engine: motor de juego.
        high_score: récord actual.

    Returns:
        Nuevo estado del mundo tras procesar la tecla.
    """
    from dataclasses import replace

    match key:
        case pygame.K_ESCAPE:
            if world.phase in (
                GamePhase.PLAYING,
                GamePhase.PAUSED,
                GamePhase.GAME_OVER,
                GamePhase.LEVEL_UP,
                GamePhase.WIN,
            ):
                return _make_menu_world(engine, high_score)

        case pygame.K_p:
            if world.phase == GamePhase.PLAYING:
                return replace(world, phase=GamePhase.PAUSED, state_tick=0)
            if world.phase == GamePhase.PAUSED:
                return replace(world, phase=GamePhase.PLAYING, state_tick=0)

        case pygame.K_RETURN | pygame.K_KP_ENTER:
            match world.phase:
                case GamePhase.MENU:
                    return engine.new_game(high_score)
                case GamePhase.GAME_OVER:
                    return engine.new_game(high_score)
                case GamePhase.WIN:
                    return engine.new_game(high_score)
                case GamePhase.LEVEL_UP:
                    if world.state_tick > 90:
                        return engine.new_level(world)

    return world


def _shutdown(repo: HighScoreRepository, world: GameWorld) -> None:
    """Guarda récord y cierra pygame limpiamente."""
    repo.save(world.score.high)
    pygame.quit()
    logger.info("game_stopped", high_score=world.score.high)
