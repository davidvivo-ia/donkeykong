"""Tests unitarios del sistema de física."""

from __future__ import annotations

import pytest

from donkeykong.domain.entities import Position, Velocity
from donkeykong.domain.level import Ladder, Platform
from donkeykong.domain.physics import (
    GRAVITY,
    JUMP_VELOCITY,
    WALK_SPEED,
    apply_gravity,
    barrel_roll_velocity,
    clamp_to_screen,
    find_ladder_at,
    integrate,
    jump_velocity,
    resolve_ladder_movement,
    resolve_platform_collision_full,
)


class TestApplyGravity:
    def test_increases_vy(self) -> None:
        v = Velocity(0.0, 0.0)
        v2 = apply_gravity(v)
        assert v2.vy == pytest.approx(GRAVITY)

    def test_does_not_change_vx(self) -> None:
        v = Velocity(5.0, 0.0)
        v2 = apply_gravity(v)
        assert v2.vx == pytest.approx(5.0)

    def test_multiplier(self) -> None:
        v = Velocity(0.0, 0.0)
        v2 = apply_gravity(v, multiplier=2.0)
        assert v2.vy == pytest.approx(GRAVITY * 2.0)

    def test_accumulates(self) -> None:
        v = Velocity(0.0, 0.0)
        for _ in range(10):
            v = apply_gravity(v)
        assert v.vy == pytest.approx(GRAVITY * 10)


class TestIntegrate:
    def test_adds_velocity_to_position(self) -> None:
        p = Position(0.0, 0.0)
        v = Velocity(3.0, -2.0)
        p2 = integrate(p, v)
        assert p2.x == pytest.approx(3.0)
        assert p2.y == pytest.approx(-2.0)

    def test_zero_velocity_no_change(self) -> None:
        p = Position(5.0, 10.0)
        v = Velocity.zero()
        assert integrate(p, v) == p


class TestClampToScreen:
    def test_clamps_left(self) -> None:
        p = Position(-100.0, 100.0)
        p2 = clamp_to_screen(p, half_width=14.0, screen_w=800.0)
        assert p2.x >= 14.0 + 2.0

    def test_clamps_right(self) -> None:
        p = Position(900.0, 100.0)
        p2 = clamp_to_screen(p, half_width=14.0, screen_w=800.0)
        assert p2.x <= 800.0 - 14.0 - 2.0

    def test_no_clamp_when_inside(self) -> None:
        p = Position(400.0, 300.0)
        assert clamp_to_screen(p, half_width=14.0, screen_w=800.0) == p


class TestPlatformCollision:
    def _platform(self, y: float = 100.0) -> Platform:
        return Platform(0.0, 800.0, y, +1, 0)

    def test_lands_on_platform(self) -> None:
        p = Position(100.0, 102.0)   # 2px debajo de la superficie
        v = Velocity(0.0, 5.0)       # cayendo
        plat = self._platform(100.0)
        p2, v2, on_ground, landed = resolve_platform_collision_full(p, v, (plat,))
        assert on_ground
        assert v2.vy == pytest.approx(0.0)
        assert p2.y == pytest.approx(100.0)

    def test_no_collision_going_up(self) -> None:
        p = Position(100.0, 102.0)
        v = Velocity(0.0, -5.0)      # subiendo
        plat = self._platform(100.0)
        _, _, on_ground, _ = resolve_platform_collision_full(p, v, (plat,))
        assert not on_ground

    def test_no_collision_outside_x(self) -> None:
        p = Position(900.0, 102.0)   # fuera del ancho de la plataforma (0..800)
        v = Velocity(0.0, 5.0)
        plat = Platform(0.0, 500.0, 100.0, +1, 0)
        _, _, on_ground, _ = resolve_platform_collision_full(p, v, (plat,))
        assert not on_ground

    def test_no_collision_far_above(self) -> None:
        p = Position(100.0, 60.0)    # 40px encima — fuera de ventana
        v = Velocity(0.0, 5.0)
        plat = self._platform(100.0)
        _, _, on_ground, _ = resolve_platform_collision_full(p, v, (plat,))
        assert not on_ground


class TestLadderMovement:
    def _ladder(self) -> Ladder:
        return Ladder(200.0, 100.0, 300.0)

    def test_climb_up(self) -> None:
        lad = self._ladder()
        p = Position(200.0, 250.0)
        p2, _, exited = resolve_ladder_movement(p, Velocity.zero(), lad, -1)
        assert p2.y < 250.0
        assert not exited

    def test_climb_down(self) -> None:
        lad = self._ladder()
        p = Position(200.0, 150.0)
        p2, _, exited = resolve_ladder_movement(p, Velocity.zero(), lad, +1)
        assert p2.y > 150.0
        assert not exited

    def test_exit_top(self) -> None:
        lad = self._ladder()
        p = Position(200.0, 101.0)
        _, _, exited = resolve_ladder_movement(p, Velocity.zero(), lad, -1)
        assert exited

    def test_exit_bottom(self) -> None:
        lad = self._ladder()
        p = Position(200.0, 299.0)
        _, _, exited = resolve_ladder_movement(p, Velocity.zero(), lad, +1)
        assert exited

    def test_clamps_to_ladder_cx(self) -> None:
        lad = self._ladder()
        p = Position(210.0, 200.0)   # desplazado
        p2, _, _ = resolve_ladder_movement(p, Velocity.zero(), lad, -1)
        assert p2.x == pytest.approx(200.0)


class TestFindLadder:
    def _ladders(self) -> tuple[Ladder, ...]:
        return (
            Ladder(160.0, 425.0, 535.0),
            Ladder(580.0, 425.0, 535.0),
        )

    def test_finds_aligned_ladder(self) -> None:
        lads = self._ladders()
        result = find_ladder_at(162.0, 500.0, lads)
        assert result is not None
        assert result.cx == pytest.approx(160.0)

    def test_returns_none_when_not_aligned(self) -> None:
        lads = self._ladders()
        result = find_ladder_at(400.0, 500.0, lads)
        assert result is None

    def test_returns_none_outside_y_range(self) -> None:
        lads = self._ladders()
        result = find_ladder_at(160.0, 200.0, lads)
        assert result is None


class TestJumpVelocity:
    def test_sets_vy_to_jump_velocity(self) -> None:
        v = Velocity(3.0, 5.0)
        v2 = jump_velocity(v)
        assert v2.vy == pytest.approx(JUMP_VELOCITY)

    def test_preserves_vx(self) -> None:
        v = Velocity(3.0, 0.0)
        v2 = jump_velocity(v)
        assert v2.vx == pytest.approx(3.0)


class TestBarrelRollVelocity:
    def test_positive_direction(self) -> None:
        v = barrel_roll_velocity(+1)
        assert v.vx > 0

    def test_negative_direction(self) -> None:
        v = barrel_roll_velocity(-1)
        assert v.vx < 0

    def test_speed_multiplier(self) -> None:
        v1 = barrel_roll_velocity(+1, 1.0)
        v2 = barrel_roll_velocity(+1, 2.0)
        assert v2.vx == pytest.approx(v1.vx * 2.0)
