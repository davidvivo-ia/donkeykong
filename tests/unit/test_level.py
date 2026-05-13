"""Tests del módulo de nivel."""

from __future__ import annotations

from donkeykong.domain.level import CANONICAL_LEVEL, Ladder, Platform, build_level


class TestPlatform:
    def test_contains_x_inside(self) -> None:
        p = Platform(10.0, 790.0, 535.0, +1, 0)
        assert p.contains_x(400.0)

    def test_contains_x_outside(self) -> None:
        p = Platform(10.0, 790.0, 535.0, +1, 0)
        assert not p.contains_x(900.0)

    def test_contains_x_boundary(self) -> None:
        p = Platform(10.0, 790.0, 535.0, +1, 0)
        assert p.contains_x(10.0)
        assert p.contains_x(790.0)


class TestLadder:
    def test_mario_aligned(self) -> None:
        lad = Ladder(160.0, 425.0, 535.0)
        assert lad.mario_aligned(162.0)  # dentro del umbral 12px

    def test_mario_not_aligned(self) -> None:
        lad = Ladder(160.0, 425.0, 535.0)
        assert not lad.mario_aligned(200.0)

    def test_mario_can_grab(self) -> None:
        lad = Ladder(160.0, 425.0, 535.0)
        assert lad.mario_can_grab(162.0, 500.0)

    def test_mario_cannot_grab_outside_y(self) -> None:
        lad = Ladder(160.0, 425.0, 535.0)
        assert not lad.mario_can_grab(160.0, 300.0)

    def test_mario_can_grab_at_y_top(self) -> None:
        """Mario parado ENCIMA de la escalera puede agarrarla para bajar."""
        lad = Ladder(160.0, 425.0, 535.0)
        assert lad.mario_can_grab(160.0, 425.0)  # feet_y == y_top

    def test_mario_can_grab_at_y_bottom(self) -> None:
        """Mario parado en el pie de la escalera puede agarrarla para subir."""
        lad = Ladder(160.0, 425.0, 535.0)
        assert lad.mario_can_grab(160.0, 535.0)  # feet_y == y_bottom




class TestBuildLevel:
    def test_returns_canonical_for_level_1(self) -> None:
        lvl = build_level(1)
        assert lvl.platforms == CANONICAL_LEVEL.platforms
        assert lvl.ladders == CANONICAL_LEVEL.ladders

    def test_has_five_platforms(self) -> None:
        lvl = build_level(1)
        assert len(lvl.platforms) == 5

    def test_has_seven_ladders(self) -> None:
        lvl = build_level(1)
        assert len(lvl.ladders) == 7

    def test_dk_start_on_top_platform(self) -> None:
        lvl = build_level(1)
        top_platform = lvl.platforms[-1]
        # DK debe estar sobre la plataforma superior
        assert lvl.dk_start.y == top_platform.y

    def test_mario_start_on_ground(self) -> None:
        lvl = build_level(1)
        ground = lvl.platforms[0]
        assert lvl.mario_start.y == ground.y
