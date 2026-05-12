"""Tests unitarios del sistema de colisiones."""

from __future__ import annotations

from dataclasses import replace

import pytest

from donkeykong.domain.collision import (
    mario_collects_bonus,
    mario_hit_by_barrel,
    mario_hit_by_flame,
    mario_jumps_over_barrel,
    mario_reaches_pauline,
)
from donkeykong.domain.entities import (
    Barrel,
    BonusItem,
    BonusKind,
    Flame,
    Mario,
    MarioState,
    Pauline,
    Position,
    Velocity,
)


def _mario(x: float = 100.0, y: float = 200.0, inv: int = 0) -> Mario:
    return replace(Mario.initial(Position(x, y)), invincible_frames=inv)


def _barrel(x: float = 100.0, y: float = 200.0) -> Barrel:
    return Barrel(0, Position(x, y), Velocity.zero(), 0, 0, True)


def _flame(x: float = 100.0, y: float = 200.0) -> Flame:
    return Flame(0, Position(x, y), Velocity.zero(), False, 0, None, 0, True)


def _pauline(x: float = 100.0, y: float = 200.0) -> Pauline:
    return Pauline(Position(x, y), 0)


def _bonus(x: float = 100.0, y: float = 200.0) -> BonusItem:
    return BonusItem(0, Position(x, y), BonusKind.PURSE, 0, 600)


class TestMarioHitByBarrel:
    def test_hits_when_overlapping(self) -> None:
        mario = _mario(100.0, 200.0)
        barrel = _barrel(100.0, 200.0)
        assert mario_hit_by_barrel(mario, barrel)

    def test_no_hit_when_far(self) -> None:
        mario = _mario(100.0, 200.0)
        barrel = _barrel(500.0, 200.0)
        assert not mario_hit_by_barrel(mario, barrel)

    def test_invincible_mario_not_hit(self) -> None:
        mario = _mario(100.0, 200.0, inv=30)
        barrel = _barrel(100.0, 200.0)
        assert not mario_hit_by_barrel(mario, barrel)


class TestMarioHitByFlame:
    def test_hits_when_overlapping(self) -> None:
        mario = _mario(100.0, 200.0)
        flame = _flame(100.0, 200.0)
        assert mario_hit_by_flame(mario, flame)

    def test_no_hit_when_far(self) -> None:
        mario = _mario(100.0, 200.0)
        flame = _flame(500.0, 200.0)
        assert not mario_hit_by_flame(mario, flame)

    def test_invincible_mario_not_hit(self) -> None:
        mario = _mario(100.0, 200.0, inv=10)
        flame = _flame(100.0, 200.0)
        assert not mario_hit_by_flame(mario, flame)


class TestMarioReachesPauline:
    def test_reaches_when_overlapping(self) -> None:
        mario = _mario(620.0, 95.0)
        pauline = _pauline(620.0, 95.0)
        assert mario_reaches_pauline(mario, pauline)

    def test_does_not_reach_when_far(self) -> None:
        mario = _mario(100.0, 535.0)
        pauline = _pauline(620.0, 95.0)
        assert not mario_reaches_pauline(mario, pauline)


class TestMarioCollectsBonus:
    def test_collects_when_touching(self) -> None:
        mario = _mario(100.0, 200.0)
        bonus = _bonus(100.0, 200.0)
        assert mario_collects_bonus(mario, bonus)

    def test_does_not_collect_when_far(self) -> None:
        mario = _mario(100.0, 200.0)
        bonus = _bonus(400.0, 200.0)
        assert not mario_collects_bonus(mario, bonus)


class TestMarioJumpsOverBarrel:
    def test_detects_jump_over(self) -> None:
        # Mario saltando sobre barril (vy negativo previo, encima del barril)
        mario = replace(_mario(100.0, 185.0), climbing=False)
        barrel = _barrel(100.0, 200.0)
        assert mario_jumps_over_barrel(mario, barrel, prev_mario_vy=-5.0)

    def test_no_jump_when_climbing(self) -> None:
        mario = replace(_mario(100.0, 185.0), climbing=True)
        barrel = _barrel(100.0, 200.0)
        assert not mario_jumps_over_barrel(mario, barrel, prev_mario_vy=-5.0)

    def test_no_jump_when_falling(self) -> None:
        mario = replace(_mario(100.0, 185.0), climbing=False)
        barrel = _barrel(100.0, 200.0)
        assert not mario_jumps_over_barrel(mario, barrel, prev_mario_vy=5.0)

    def test_no_jump_when_too_far_horizontal(self) -> None:
        mario = replace(_mario(200.0, 185.0), climbing=False)
        barrel = _barrel(100.0, 200.0)
        assert not mario_jumps_over_barrel(mario, barrel, prev_mario_vy=-5.0)

    def test_no_jump_when_below_barrel(self) -> None:
        mario = replace(_mario(100.0, 210.0), climbing=False)
        barrel = _barrel(100.0, 200.0)
        assert not mario_jumps_over_barrel(mario, barrel, prev_mario_vy=-5.0)
