"""Tests unitarios de las entidades del dominio."""

from __future__ import annotations

import pytest

from donkeykong.domain.entities import (
    BonusItem,
    BonusKind,
    Mario,
    MarioState,
    PlayerFacing,
    Position,
    Rect,
    Score,
    ScorePopup,
    Velocity,
)


class TestPosition:
    def test_move(self) -> None:
        p = Position(10.0, 20.0)
        assert p.move(5.0, -3.0) == Position(15.0, 17.0)

    def test_distance_to_self(self) -> None:
        p = Position(0.0, 0.0)
        assert p.distance_to(p) == pytest.approx(0.0)

    def test_distance_to_other(self) -> None:
        p = Position(0.0, 0.0)
        q = Position(3.0, 4.0)
        assert p.distance_to(q) == pytest.approx(5.0)

    def test_with_x(self) -> None:
        p = Position(1.0, 2.0)
        assert p.with_x(99.0) == Position(99.0, 2.0)

    def test_with_y(self) -> None:
        p = Position(1.0, 2.0)
        assert p.with_y(99.0) == Position(1.0, 99.0)

    def test_frozen(self) -> None:
        p = Position(1.0, 2.0)
        with pytest.raises(AttributeError):
            p.x = 999.0  # type: ignore[misc]


class TestVelocity:
    def test_add_gravity(self) -> None:
        v = Velocity(0.0, 0.0)
        v2 = v.add_gravity(0.55)
        assert v2.vy == pytest.approx(0.55)
        assert v2.vx == pytest.approx(0.0)

    def test_zero_y(self) -> None:
        v = Velocity(3.0, -5.0)
        assert v.zero_y() == Velocity(3.0, 0.0)

    def test_zero_x(self) -> None:
        v = Velocity(3.0, -5.0)
        assert v.zero_x() == Velocity(0.0, -5.0)

    def test_with_vy(self) -> None:
        v = Velocity(2.0, 0.0)
        assert v.with_vy(-13.0).vy == pytest.approx(-13.0)

    def test_zero_static(self) -> None:
        assert Velocity.zero() == Velocity(0.0, 0.0)


class TestRect:
    def test_collides_overlapping(self) -> None:
        a = Rect(0.0, 0.0, 10.0, 10.0)
        b = Rect(5.0, 5.0, 10.0, 10.0)
        assert a.collides_with(b)

    def test_not_collides_separated(self) -> None:
        a = Rect(0.0, 0.0, 10.0, 10.0)
        b = Rect(20.0, 0.0, 10.0, 10.0)
        assert not a.collides_with(b)

    def test_not_collides_touching_edge(self) -> None:
        a = Rect(0.0, 0.0, 10.0, 10.0)
        b = Rect(10.0, 0.0, 10.0, 10.0)
        assert not a.collides_with(b)

    def test_properties(self) -> None:
        r = Rect(2.0, 3.0, 10.0, 6.0)
        assert r.right == pytest.approx(12.0)
        assert r.bottom == pytest.approx(9.0)
        assert r.cx == pytest.approx(7.0)
        assert r.cy == pytest.approx(6.0)

    def test_inflated(self) -> None:
        r = Rect(10.0, 10.0, 20.0, 10.0)
        r2 = r.inflated(2.0, 3.0)
        assert r2.x == pytest.approx(8.0)
        assert r2.y == pytest.approx(7.0)
        assert r2.width == pytest.approx(24.0)
        assert r2.height == pytest.approx(16.0)


class TestScore:
    def test_add_no_record(self) -> None:
        s = Score(100, 200)
        s2 = s.add(50)
        assert s2.current == 150
        assert s2.high == 200

    def test_add_beats_record(self) -> None:
        s = Score(180, 200)
        s2 = s.add(50)
        assert s2.current == 230
        assert s2.high == 230

    def test_zero(self) -> None:
        s = Score.zero(high=999)
        assert s.current == 0
        assert s.high == 999


class TestMario:
    def test_initial_state(self) -> None:
        mario = Mario.initial(Position(60.0, 535.0))
        assert mario.state == MarioState.IDLE
        assert mario.facing == PlayerFacing.RIGHT
        assert mario.invincible_frames == 90
        assert not mario.climbing
        assert mario.ladder_cx is None

    def test_rect_size(self) -> None:
        mario = Mario.initial(Position(100.0, 200.0))
        r = mario.rect
        assert r.width == pytest.approx(28.0)  # HALF_W * 2
        assert r.height == pytest.approx(42.0)

    def test_feet_y(self) -> None:
        mario = Mario.initial(Position(0.0, 535.0))
        assert mario.feet_y == pytest.approx(535.0)

    def test_is_invincible(self) -> None:
        mario = Mario.initial(Position(0.0, 0.0))
        assert mario.is_invincible  # starts with 90 invincible frames

    def test_dead_anim_not_done_initially(self) -> None:
        mario = Mario.initial(Position(0.0, 0.0))
        assert not mario.is_dead_anim_done


class TestBonusItem:
    def test_value_purse(self) -> None:
        b = BonusItem(0, Position(0.0, 0.0), BonusKind.PURSE, 0, 600)
        assert b.value == 300

    def test_value_hat(self) -> None:
        b = BonusItem(0, Position(0.0, 0.0), BonusKind.HAT, 0, 600)
        assert b.value == 500

    def test_value_umbrella(self) -> None:
        b = BonusItem(0, Position(0.0, 0.0), BonusKind.UMBRELLA, 0, 600)
        assert b.value == 800


class TestScorePopup:
    def test_tick_decrements_life(self) -> None:
        pop = ScorePopup(100.0, 200.0, 500, (255, 255, 0), 60)
        pop2 = pop.tick()
        assert pop2.life == 59

    def test_tick_moves_up(self) -> None:
        pop = ScorePopup(100.0, 200.0, 500, (255, 255, 0), 60)
        pop2 = pop.tick()
        assert pop2.y < pop.y

    def test_alive_when_life_positive(self) -> None:
        pop = ScorePopup(0.0, 0.0, 0, (0, 0, 0), 1)
        assert pop.alive

    def test_not_alive_when_life_zero(self) -> None:
        pop = ScorePopup(0.0, 0.0, 0, (0, 0, 0), 0)
        assert not pop.alive
