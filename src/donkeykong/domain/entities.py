"""Entidades inmutables del dominio Donkey Kong.

Todos los modelos son frozen dataclasses con slots para máximo rendimiento
e inmutabilidad garantizada por el runtime.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto

# ---------------------------------------------------------------------------
# Primitivos de valor
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Position:
    """Posición bidimensional en píxeles."""

    x: float
    y: float

    def move(self, dx: float, dy: float) -> Position:
        """Retorna nueva posición desplazada."""
        return Position(self.x + dx, self.y + dy)

    def distance_to(self, other: Position) -> float:
        """Distancia euclidiana a otra posición."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def with_x(self, x: float) -> Position:
        """Retorna posición con X reemplazada."""
        return Position(x, self.y)

    def with_y(self, y: float) -> Position:
        """Retorna posición con Y reemplazada."""
        return Position(self.x, y)


@dataclass(frozen=True, slots=True)
class Velocity:
    """Velocidad en píxeles por frame."""

    vx: float
    vy: float

    def add_gravity(self, gravity: float) -> Velocity:
        """Aplica aceleración gravitatoria al eje Y."""
        return Velocity(self.vx, self.vy + gravity)

    def with_vx(self, vx: float) -> Velocity:
        """Retorna velocidad con VX reemplazado."""
        return Velocity(vx, self.vy)

    def with_vy(self, vy: float) -> Velocity:
        """Retorna velocidad con VY reemplazado."""
        return Velocity(self.vx, vy)

    def zero_y(self) -> Velocity:
        """Elimina componente vertical."""
        return Velocity(self.vx, 0.0)

    def zero_x(self) -> Velocity:
        """Elimina componente horizontal."""
        return Velocity(0.0, self.vy)

    @staticmethod
    def zero() -> Velocity:
        """Velocidad nula."""
        return Velocity(0.0, 0.0)


@dataclass(frozen=True, slots=True)
class Rect:
    """Rectángulo AABB para colisiones."""

    x: float  # esquina superior izquierda
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def cx(self) -> float:
        return self.x + self.width / 2

    @property
    def cy(self) -> float:
        return self.y + self.height / 2

    def collides_with(self, other: Rect) -> bool:
        """Detecta solapamiento AABB."""
        return (
            self.x < other.right
            and self.right > other.x
            and self.y < other.bottom
            and self.bottom > other.y
        )

    def inflated(self, dx: float, dy: float) -> Rect:
        """Expande el rectángulo simétricamente."""
        return Rect(self.x - dx, self.y - dy, self.width + 2 * dx, self.height + 2 * dy)


# ---------------------------------------------------------------------------
# Enumeraciones de estado
# ---------------------------------------------------------------------------


class GamePhase(Enum):
    """Fase global del juego."""

    MENU = auto()
    INTRO = auto()
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_UP = auto()
    GAME_OVER = auto()
    WIN = auto()


class MarioState(Enum):
    """Estado de animación/física de Mario."""

    IDLE = auto()
    WALK = auto()
    JUMP = auto()
    CLIMB = auto()
    DEAD = auto()


class PlayerFacing(Enum):
    """Dirección a la que mira Mario."""

    LEFT = -1
    RIGHT = 1


class BonusKind(Enum):
    """Tipo de objeto bonus coleccionable."""

    PURSE = "purse"
    HAT = "hat"
    UMBRELLA = "umbrella"


# ---------------------------------------------------------------------------
# Entidades de juego
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Mario:
    """Estado completo del jugador."""

    position: Position
    velocity: Velocity
    state: MarioState
    facing: PlayerFacing
    on_ground: bool
    climbing: bool
    # X central de la escalera que está subiendo/bajando (None si no sube)
    ladder_cx: float | None
    frame: int  # frame de animación actual
    anim_tick: int  # acumulador de ticks para animación
    invincible_frames: int  # frames de invulnerabilidad tras daño
    dead_anim_tick: int  # tick de animación de muerte
    step_sound_tick: int  # acumulador para cadencia de sonido de pasos

    # Geometría (constantes de diseño)
    HALF_W: float = field(default=14.0, compare=False)
    HEIGHT: float = field(default=42.0, compare=False)

    @property
    def rect(self) -> Rect:
        """Hitbox del jugador."""
        return Rect(
            self.position.x - self.HALF_W,
            self.position.y - self.HEIGHT,
            self.HALF_W * 2,
            self.HEIGHT,
        )

    @property
    def feet_y(self) -> float:
        """Y de los pies (punto de aterrizaje)."""
        return self.position.y

    @property
    def is_dead_anim_done(self) -> bool:
        """True cuando la animación de muerte ha terminado."""
        return self.state == MarioState.DEAD and self.dead_anim_tick > 80

    @property
    def is_invincible(self) -> bool:
        return self.invincible_frames > 0

    @staticmethod
    def initial(position: Position) -> Mario:
        """Crea Mario en posición inicial con estado por defecto."""
        return Mario(
            position=position,
            velocity=Velocity.zero(),
            state=MarioState.IDLE,
            facing=PlayerFacing.RIGHT,
            on_ground=False,
            climbing=False,
            ladder_cx=None,
            frame=0,
            anim_tick=0,
            invincible_frames=90,
            dead_anim_tick=0,
            step_sound_tick=0,
        )


@dataclass(frozen=True, slots=True)
class Barrel:
    """Barril lanzado por Donkey Kong."""

    barrel_id: int
    position: Position
    velocity: Velocity
    current_pid: int  # id de la plataforma sobre la que rueda
    roll_frame: int  # contador de rotación visual
    alive: bool
    on_ladder: bool = field(default=False)
    ladder_cx: float | None = field(default=None)

    HALF_W: float = field(default=9.0, compare=False)
    HEIGHT: float = field(default=14.0, compare=False)

    @property
    def rect(self) -> Rect:
        return Rect(
            self.position.x - self.HALF_W,
            self.position.y - self.HEIGHT,
            self.HALF_W * 2,
            self.HEIGHT,
        )


@dataclass(frozen=True, slots=True)
class Flame:
    """Enemigo de fuego que persigue a Mario."""

    flame_id: int
    position: Position
    velocity: Velocity
    climbing: bool
    climb_direction: int  # -1 subir, 0 no escala, +1 bajar
    climb_ladder_cx: float | None
    frame_tick: int
    alive: bool

    HALF_W: float = field(default=8.0, compare=False)
    HEIGHT: float = field(default=18.0, compare=False)

    @property
    def rect(self) -> Rect:
        return Rect(
            self.position.x - self.HALF_W,
            self.position.y - self.HEIGHT,
            self.HALF_W * 2,
            self.HEIGHT,
        )


@dataclass(frozen=True, slots=True)
class DonkeyKong:
    """Estado del antagonista principal."""

    position: Position  # centro-x, pies-y
    frame_tick: int
    throw_timer: int
    throwing: bool
    throw_flash: int  # frames de destello de ojos en ira

    @staticmethod
    def initial(position: Position) -> DonkeyKong:
        return DonkeyKong(
            position=position,
            frame_tick=0,
            throw_timer=0,
            throwing=False,
            throw_flash=0,
        )


@dataclass(frozen=True, slots=True)
class Pauline:
    """La princesa — objetivo de rescate."""

    position: Position  # centro-x, pies-y
    frame_tick: int

    @property
    def rect(self) -> Rect:
        return Rect(self.position.x - 14, self.position.y - 48, 28, 48)


@dataclass(frozen=True, slots=True)
class BonusItem:
    """Objeto bonus coleccionable."""

    bonus_id: int
    position: Position
    kind: BonusKind
    frame_tick: int
    life_remaining: int  # frames hasta desaparecer

    BONUS_LIFE: int = field(default=600, compare=False)

    @property
    def rect(self) -> Rect:
        return Rect(self.position.x - 10, self.position.y - 22, 20, 22)

    @property
    def value(self) -> int:
        """Puntos otorgados al recoger."""
        return {BonusKind.PURSE: 300, BonusKind.HAT: 500, BonusKind.UMBRELLA: 800}[self.kind]


@dataclass(frozen=True, slots=True)
class Score:
    """Puntuación actual y récord."""

    current: int
    high: int

    def add(self, points: int) -> Score:
        """Suma puntos y actualiza récord si procede."""
        new_current = self.current + points
        return Score(current=new_current, high=max(self.high, new_current))

    @staticmethod
    def zero(high: int = 0) -> Score:
        return Score(current=0, high=high)


@dataclass(frozen=True, slots=True)
class ScorePopup:
    """Popup flotante de puntuación."""

    x: float
    y: float
    value: int
    color: tuple[int, int, int]
    life: int  # frames de vida restantes

    def tick(self) -> ScorePopup:
        """Avanza un frame."""
        return ScorePopup(self.x, self.y - 1.2, self.value, self.color, self.life - 1)

    @property
    def alive(self) -> bool:
        return self.life > 0

    @property
    def alpha(self) -> int:
        return max(0, min(255, self.life * 4))
