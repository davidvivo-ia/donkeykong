"""Renderer: traduce GameWorld a píxeles pygame.

Sin lógica de juego. Solo lee del dominio y dibuja.
"""

from __future__ import annotations

import math
import random

import pygame

from donkeykong.domain.entities import (
    BonusItem,
    DonkeyKong,
    GamePhase,
    Mario,
    MarioState,
    Pauline,
    PlayerFacing,
    ScorePopup,
)
from donkeykong.domain.world import GameWorld
from donkeykong.presentation import palette as P  # noqa: N812
from donkeykong.presentation import sprites as S  # noqa: N812

_FPS_FONT_SIZE = 13

# Estrellas fijas (se generan una sola vez)
_STARS: list[tuple[int, int, int, float]] = [
    (
        random.randint(0, 800),
        random.randint(0, 300),
        random.randint(1, 3),
        random.uniform(0.3, 1.0),
    )
    for _ in range(80)
]


class Renderer:
    """Renderizador principal del juego.

    Args:
        screen: superficie pygame de la ventana.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen
        self._w, self._h = screen.get_size()
        pygame.font.init()
        self._font_xl = pygame.font.SysFont("monospace", 52, bold=True)
        self._font_big = pygame.font.SysFont("monospace", 34, bold=True)
        self._font_med = pygame.font.SysFont("monospace", 22, bold=True)
        self._font_sm = pygame.font.SysFont("monospace", 16)
        self._font_xs = pygame.font.SysFont("monospace", 13)

    # ── Puntos de entrada públicos ────────────────────────────────────────────

    def render(self, world: GameWorld, menu_tick: int = 0) -> None:
        """Renderiza el frame completo según la fase del juego.

        Args:
            world: estado actual del juego.
            menu_tick: tick global usado en pantallas de menú.
        """
        match world.phase:
            case GamePhase.MENU:
                self._draw_menu(menu_tick, world.score.high)
            case GamePhase.INTRO:
                self._draw_game(world)
                self._draw_intro_overlay(world.state_tick)
            case GamePhase.PLAYING | GamePhase.PAUSED:
                self._draw_game(world)
                if world.phase == GamePhase.PAUSED:
                    self._draw_paused()
            case GamePhase.LEVEL_UP:
                self._draw_game(world)
                self._draw_level_up(world.state_tick, world.level_num, world.score.current)
            case GamePhase.GAME_OVER:
                self._draw_game(world)
                self._draw_game_over(world.state_tick, world.score.current)
            case GamePhase.WIN:
                self._draw_win(world.state_tick, world.score.current)

    # ── Fondo ─────────────────────────────────────────────────────────────────

    def _draw_background(self, t: int) -> None:
        surf = self._screen
        # Gradiente vertical nocturno
        for gy in range(self._h):
            ratio = gy / self._h
            r = int(P.NIGHT_TOP[0] + (P.NIGHT_BOT[0] - P.NIGHT_TOP[0]) * ratio)
            g = int(P.NIGHT_TOP[1] + (P.NIGHT_BOT[1] - P.NIGHT_TOP[1]) * ratio)
            b = int(P.NIGHT_TOP[2] + (P.NIGHT_BOT[2] - P.NIGHT_TOP[2]) * ratio)
            pygame.draw.line(surf, (r, g, b), (0, gy), (self._w, gy))
        # Estrellas parpadeantes
        for sx, sy, sr, spd in _STARS:
            bright = int(128 + 127 * math.sin(t * spd * 0.05))
            pygame.draw.circle(surf, (bright, bright, bright), (sx, sy), sr)
        # Silueta de ciudad
        buildings = [
            (0, 70, 50),
            (60, 90, 40),
            (110, 75, 35),
            (155, 85, 45),
            (200, 65, 55),
            (260, 80, 30),
            (300, 70, 50),
            (360, 90, 40),
            (410, 75, 45),
            (460, 85, 35),
            (510, 70, 55),
            (570, 80, 40),
            (620, 65, 50),
            (680, 90, 35),
            (730, 75, 45),
            (770, 80, 30),
        ]
        for bx, bh, bw in buildings:
            by2 = self._h - bh
            pygame.draw.rect(surf, (15, 20, 55), (bx, by2, bw, bh))
            for wy in range(by2 + 5, self._h - 5, 14):
                for wx in range(bx + 5, bx + bw - 8, 10):
                    wc = P.YELLOW if random.random() < 0.6 else (30, 30, 60)
                    pygame.draw.rect(surf, wc, (wx, wy, 5, 7))

    # ── Juego en partida ──────────────────────────────────────────────────────

    def _draw_game(self, world: GameWorld) -> None:
        self._draw_background(world.tick)
        lvl = world.level

        # Escaleras
        for lad in lvl.ladders:
            S.draw_ladder(self._screen, lad.cx, lad.y_top, lad.y_bottom)

        # Vigas
        for plat in lvl.platforms:
            S.draw_girder(self._screen, plat.x_left, plat.x_right, plat.y)

        # Bidón de aceite (suelo izquierda)
        S.draw_oil_drum(self._screen, 40.0, lvl.platforms[0].y)

        # Pauline
        self._draw_pauline(world.pauline)

        # DK
        self._draw_dk(world.dk)

        # Bonus
        for bo in world.bonuses:
            self._draw_bonus(bo)

        # Barriles
        for b in world.barrels:
            S.draw_barrel(self._screen, b.position.x, b.position.y, b.roll_frame // 4)

        # Llamas
        for f in world.flames:
            S.draw_flame(self._screen, f.position.x, f.position.y, f.frame_tick // 8)

        # Mario
        self._draw_mario(world.mario)

        # Popups de puntuación
        for pop in world.popups:
            self._draw_popup(pop)

        # HUD
        self._draw_hud(world)

    def _draw_mario(self, mario: Mario) -> None:
        if mario.is_invincible and mario.state != MarioState.DEAD:
            if (mario.invincible_frames // 4) % 2 == 0:
                return
        facing = 1 if mario.facing == PlayerFacing.RIGHT else -1
        S.draw_mario(
            self._screen,
            mario.position.x,
            mario.position.y,
            mario.frame,
            facing,
            mario.state.name.lower(),
            mario.dead_anim_tick,
        )

    def _draw_dk(self, dk: DonkeyKong) -> None:
        S.draw_dk(
            self._screen,
            dk.position.x,
            dk.position.y,
            dk.frame_tick // 14,
            dk.throwing,
        )

    def _draw_pauline(self, pauline: Pauline) -> None:
        S.draw_pauline(
            self._screen, pauline.position.x, pauline.position.y, pauline.frame_tick // 12
        )

    def _draw_bonus(self, bo: BonusItem) -> None:
        S.draw_bonus_item(self._screen, bo.position.x, bo.position.y, bo.kind.value, bo.frame_tick)

    def _draw_popup(self, pop: ScorePopup) -> None:
        s = self._font_sm.render(f"+{pop.value}", True, pop.color)
        s.set_alpha(pop.alpha)
        self._screen.blit(s, (int(pop.x) - s.get_width() // 2, int(pop.y)))

    # ── HUD ───────────────────────────────────────────────────────────────────

    def _draw_hud(self, world: GameWorld) -> None:
        pygame.draw.rect(self._screen, (10, 10, 30), (0, 0, self._w, 38))
        pygame.draw.line(self._screen, P.GIRDER, (0, 38), (self._w, 38), 2)
        # Score
        self._text_shadow(self._font_sm, f"SCORE  {world.score.current:06d}", P.YELLOW, 10, 8)
        # Best
        hs = self._font_sm.render(f"BEST {world.score.high:06d}", True, P.GOLD)
        self._screen.blit(hs, (self._w // 2 - hs.get_width() // 2, 10))
        # Level
        self._text_shadow(self._font_sm, f"LVL {world.level_num}", P.CYAN, self._w - 90, 8)
        # Vidas
        for i in range(world.lives):
            lx = self._w - 140 - i * 20
            S.draw_mario(self._screen, float(lx), 36.0, scale=0.52)
        # Barra de bonus
        if world.bonus_timer > 0:
            bw = int((world.bonus_timer / 3600) * 200)
            pygame.draw.rect(
                self._screen, P.DARK_GRAY, (self._w // 2 + 90, 14, 202, 12), border_radius=3
            )
            pygame.draw.rect(
                self._screen, P.GREEN, (self._w // 2 + 91, 15, bw, 10), border_radius=3
            )
            self._text_shadow(self._font_xs, "BONUS", P.YELLOW, self._w // 2 + 95, 13)

    # ── Pantallas de estado ───────────────────────────────────────────────────

    def _draw_menu(self, tick: int, high_score: int) -> None:
        self._draw_background(tick)
        # Caja de título
        pygame.draw.rect(
            self._screen, (10, 10, 50, 200), (self._w // 2 - 220, 60, 440, 120), border_radius=12
        )
        pygame.draw.rect(
            self._screen, P.GIRDER, (self._w // 2 - 220, 60, 440, 120), 3, border_radius=12
        )
        self._center_text(self._font_xl, "DONKEY", P.ORANGE, 70)
        self._center_text(self._font_xl, " KONG ", P.YELLOW, 112)

        # DK animado
        dk_x = self._w // 2 + int(math.sin(tick * 0.03) * 30)
        S.draw_dk(self._screen, float(dk_x), 240.0, tick // 14, (tick // 30) % 2 == 0)
        # Mario corriendo
        mario_x = 80.0 + float((tick * 2) % (self._w - 140))
        S.draw_mario(self._screen, mario_x, 270.0, tick // 8, 1, "walk")

        self._center_text(self._font_med, "PULSA  ENTER  PARA  JUGAR", P.WHITE, 300)
        self._center_text(self._font_sm, "← → / A D   Moverse       ↑ / Esp   Saltar", P.GRAY, 345)
        self._center_text(self._font_sm, "↑ ↓ en escalera   Trepar       P   Pausa", P.GRAY, 367)
        if high_score > 0:
            self._center_text(self._font_med, f"MEJOR PUNTUACIÓN: {high_score:06d}", P.GOLD, 400)
        self._center_text(
            self._font_xs, "Python / pygame-ce  —  Recreación arcade clásico", P.GRAY, self._h - 24
        )

    def _draw_intro_overlay(self, tick: int) -> None:
        prog = min(tick / 80.0, 1.0)
        dk_y = int(80 + (self._h // 2 - 80) * (1.0 - prog))
        S.draw_dk(self._screen, float(self._w // 2), float(dk_y), tick // 10)
        S.draw_pauline(self._screen, float(self._w // 2 + 40), float(dk_y), tick // 12)
        self._center_text(
            self._font_big, "¿HASTA DÓNDE PUEDES LLEGAR?", P.YELLOW, self._h // 2 + 60
        )

    def _draw_game_over(self, tick: int, score: int) -> None:
        self._draw_overlay(160)
        self._center_text(self._font_xl, "GAME  OVER", P.RED, self._h // 2 - 60)
        self._center_text(
            self._font_med, f"PUNTUACIÓN FINAL:  {score:06d}", P.WHITE, self._h // 2 + 10
        )
        if tick > 90:
            self._center_text(self._font_sm, "ENTER — nueva partida", P.GRAY, self._h // 2 + 60)
            self._center_text(self._font_sm, "ESC — menú", P.GRAY, self._h // 2 + 88)

    def _draw_level_up(self, tick: int, level_num: int, score: int) -> None:
        self._draw_overlay(140)
        self._center_text(self._font_xl, f"NIVEL {level_num}", P.CYAN, self._h // 2 - 80)
        self._center_text(self._font_med, "¡NIVEL SUPERADO!", P.YELLOW, self._h // 2 - 20)
        self._center_text(self._font_med, f"PUNTUACIÓN:  {score:06d}", P.WHITE, self._h // 2 + 30)
        if tick > 90:
            self._center_text(self._font_sm, "ENTER — siguiente nivel", P.GRAY, self._h // 2 + 88)

    def _draw_win(self, tick: int, score: int) -> None:
        self._draw_background(tick)
        self._center_text(self._font_xl, "¡GANASTE!", P.YELLOW, self._h // 2 - 80)
        self._center_text(self._font_med, "¡Pauline ha sido rescatada!", P.PINK, self._h // 2 - 20)
        self._center_text(self._font_med, f"PUNTUACIÓN:  {score:06d}", P.WHITE, self._h // 2 + 30)
        if tick > 90:
            self._center_text(self._font_sm, "ENTER — nueva partida", P.GRAY, self._h // 2 + 88)

    def _draw_paused(self) -> None:
        self._draw_overlay(140)
        self._center_text(self._font_xl, "PAUSA", P.WHITE, self._h // 2 - 40)
        self._center_text(self._font_sm, "P — continuar   ESC — menú", P.GRAY, self._h // 2 + 30)

    # ── Helpers de dibujado ───────────────────────────────────────────────────

    def _draw_overlay(self, alpha: int) -> None:
        overlay = pygame.Surface((self._w, self._h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self._screen.blit(overlay, (0, 0))

    def _center_text(
        self,
        font: pygame.font.Font,
        msg: str,
        color: tuple[int, int, int],
        cy: int,
    ) -> None:
        sh = font.render(msg, True, P.BLACK)
        x = self._w // 2 - sh.get_width() // 2
        self._screen.blit(sh, (x + 2, cy + 2))
        s = font.render(msg, True, color)
        self._screen.blit(s, (x, cy))

    def _text_shadow(
        self,
        font: pygame.font.Font,
        msg: str,
        color: tuple[int, int, int],
        x: int,
        y: int,
    ) -> None:
        sh = font.render(msg, True, P.BLACK)
        self._screen.blit(sh, (x + 2, y + 2))
        s = font.render(msg, True, color)
        self._screen.blit(s, (x, y))
