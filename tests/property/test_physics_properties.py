"""Tests de propiedad del sistema de física con Hypothesis."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from donkeykong.domain.entities import Position, Velocity
from donkeykong.domain.level import Platform
from donkeykong.domain.physics import (
    apply_gravity,
    clamp_to_screen,
    integrate,
    resolve_platform_collision_full,
)

_floats = st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
_pos_floats = st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)


@given(_floats, _floats)
def test_gravity_always_increases_vy(vx: float, vy: float) -> None:
    """La gravedad siempre incrementa VY (hacia abajo)."""
    v = Velocity(vx, vy)
    v2 = apply_gravity(v)
    assert v2.vy > v.vy


@given(_floats, _floats, _floats, _floats)
def test_integrate_moves_position(x: float, y: float, vx: float, vy: float) -> None:
    """La integración de Euler suma velocidad a posición."""
    p = Position(x, y)
    v = Velocity(vx, vy)
    p2 = integrate(p, v)
    assert p2.x == x + vx
    assert p2.y == y + vy


@given(
    st.floats(min_value=-200.0, max_value=-1.0, allow_nan=False),
    st.floats(min_value=16.0, max_value=50.0, allow_nan=False),
    st.floats(min_value=400.0, max_value=1200.0, allow_nan=False),
)
def test_clamp_always_within_bounds(x: float, half_w: float, screen_w: float) -> None:
    """Clamp siempre devuelve X dentro de los límites de pantalla."""
    p = Position(x, 0.0)
    p2 = clamp_to_screen(p, half_w, screen_w)
    min_x = half_w + 2.0
    max_x = screen_w - half_w - 2.0
    assert min_x <= p2.x <= max_x


@given(
    st.floats(min_value=0.0, max_value=800.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.1, max_value=20.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50)
def test_gravity_accumulates_monotonically(vx: float, vy: float, steps: float) -> None:
    """La gravedad acumula de forma monótona tras N steps."""
    n = max(1, int(steps))
    v = Velocity(vx, 0.0)
    prev_vy = v.vy
    for _ in range(n):
        v = apply_gravity(v)
        assert v.vy >= prev_vy
        prev_vy = v.vy


@given(
    st.floats(min_value=100.0, max_value=700.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.1, max_value=20.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_platform_collision_stops_fall(platform_y: float, delta: float) -> None:
    """Caer sobre plataforma siempre detiene VY."""
    # Mario a delta píxeles por debajo de la superficie, cayendo
    pos = Position(400.0, platform_y + delta)
    vel = Velocity(0.0, 5.0)
    plat = Platform(0.0, 800.0, platform_y, +1, 0)
    if 0.0 <= delta <= 24.0:
        _, v2, on_ground, _ = resolve_platform_collision_full(pos, vel, (plat,))
        assert on_ground
        assert v2.vy == 0.0
