"""Motor de juego: orquesta el dominio frame a frame.

Cada llamada a `tick()` consume el estado actual + input y produce
un nuevo EngineOutput. Sin efectos secundarios: la reproducción de
sonidos y el dibujado son responsabilidad de la capa de presentación.
"""

from __future__ import annotations

import math
from dataclasses import replace

from donkeykong.application.engine_output import EngineOutput
from donkeykong.application.input import InputState
from donkeykong.domain import collision as col
from donkeykong.domain import physics as phy
from donkeykong.domain.entities import (
    Barrel,
    BonusItem,
    BonusKind,
    DonkeyKong,
    Flame,
    GamePhase,
    Mario,
    MarioState,
    PlayerFacing,
    Position,
    ScorePopup,
    Velocity,
)
from donkeykong.domain.events import ScoreEvent, SoundEvent
from donkeykong.domain.level import Level, build_level
from donkeykong.domain.world import GameWorld, initial_world
from donkeykong.infrastructure.rng import RNG

# Constantes de gameplay
_THROW_BASE_CD: int = 180  # frames entre lanzamientos (nivel 1)
_THROW_MIN_CD: int = 90  # cooldown mínimo al subir niveles
_FLAME_SPAWN_BASE: int = 600  # frames entre spawns de llama
_FLAME_SPAWN_MIN: int = 300
_FLAME_MAX: int = 4  # máx llamas simultáneas (+ nivel)
_BARREL_JUMP_SCORE: int = 100
_WIN_SCORE: int = 5_000
_PLATFORM_SCORE_PER_LEVEL: int = 0  # [SUPUESTO] sin bonus por subir plataforma
_BONUS_LIFE: int = 600  # frames de vida de un bonus
_POPUP_LIFE: int = 60
_INTRO_DURATION: int = 120
_LEVELUP_MIN_TICKS: int = 90


# ---------------------------------------------------------------------------
# Helpers internos (funciones puras)
# ---------------------------------------------------------------------------


def _speed_mult(level_num: int) -> float:
    return 1.0 + 0.12 * (level_num - 1)


def _throw_cd(level_num: int) -> int:
    raw = int(_THROW_BASE_CD / (1.0 + 0.15 * (level_num - 1)))
    return max(_THROW_MIN_CD, raw)


def _flame_spawn_interval(level_num: int) -> int:
    raw = _FLAME_SPAWN_BASE - level_num * 40
    return max(_FLAME_SPAWN_MIN, raw)


def _flame_max(level_num: int) -> int:
    return _FLAME_MAX + level_num


def _bonus_score(level_num: int, bonus_timer: int) -> int:
    return _WIN_SCORE + (bonus_timer // 60) * 100


# ---------------------------------------------------------------------------
# Actualización de Mario
# ---------------------------------------------------------------------------


def _update_mario(
    mario: Mario,
    inp: InputState,
    level: Level,
    sounds: list[SoundEvent],
) -> Mario:
    """Aplica input + física a Mario y retorna el nuevo estado.

    Función pura excepto por el accumulator `sounds` (lista externa).
    """
    if mario.state == MarioState.DEAD:
        new_tick = mario.dead_anim_tick + 1
        return replace(mario, dead_anim_tick=new_tick)

    inv = max(0, mario.invincible_frames - 1)
    anim_tick = mario.anim_tick + 1
    step_tick = mario.step_sound_tick + 1

    pos = mario.position
    vel = mario.velocity
    on_ground = mario.on_ground
    climbing = mario.climbing
    ladder_cx = mario.ladder_cx
    state = mario.state
    facing = mario.facing
    frame = mario.frame

    # ── Escalera ─────────────────────────────────────────────────────────────
    on_lad = phy.find_ladder_at(pos.x, pos.y, level.ladders)
    if on_lad and not climbing and (inp.up or inp.down):
        go_up = inp.up and pos.y > on_lad.y_top + 4
        go_down = inp.down and pos.y < on_lad.y_bottom
        if go_up or go_down:
            climbing = True
            ladder_cx = on_lad.cx
            pos = pos.with_x(on_lad.cx)
            vel = Velocity.zero()

    if climbing:
        cur_lad = next(
            (
                ldr
                for ldr in level.ladders
                if ldr.cx == ladder_cx and ldr.mario_can_grab(pos.x, pos.y)
            ),
            None,
        )
        if cur_lad is None:
            climbing = False
            ladder_cx = None
        else:
            direction = 0
            if inp.up:
                direction = -1
            elif inp.down:
                direction = 1
            if direction != 0:
                pos, vel, exited = phy.resolve_ladder_movement(pos, vel, cur_lad, direction)
                state = MarioState.CLIMB
                if step_tick % 10 == 0:
                    sounds.append(SoundEvent.CLIMB)
                if exited:
                    climbing = False
                    ladder_cx = None
                    on_ground = True
            else:
                vel = Velocity.zero()
            # Saltar desde escalera
            if inp.jump and on_ground:
                climbing = False
                ladder_cx = None
                vel = phy.jump_velocity(vel)
                on_ground = False
                state = MarioState.JUMP
                sounds.append(SoundEvent.JUMP)
            frame = anim_tick // 8
    else:
        # ── Movimiento horizontal ─────────────────────────────────────────────
        if inp.left:
            vel = vel.with_vx(-phy.WALK_SPEED)
            facing = PlayerFacing.LEFT
        elif inp.right:
            vel = vel.with_vx(phy.WALK_SPEED)
            facing = PlayerFacing.RIGHT
        else:
            vel = vel.with_vx(0.0)

        # ── Salto ─────────────────────────────────────────────────────────────
        if (inp.jump or (inp.up and not on_lad)) and on_ground:
            vel = phy.jump_velocity(vel)
            on_ground = False
            state = MarioState.JUMP
            sounds.append(SoundEvent.JUMP)

        # ── Gravedad + integración ────────────────────────────────────────────
        vel = phy.apply_gravity(vel)
        pos = phy.integrate(pos, vel)
        pos = phy.clamp_to_screen(pos, mario.HALF_W)

        # ── Colisión con plataformas ──────────────────────────────────────────
        pos, vel, on_ground, just_landed = phy.resolve_platform_collision_full(
            pos, vel, level.platforms
        )
        if just_landed and state == MarioState.JUMP:
            sounds.append(SoundEvent.LAND)

        # ── Estado de animación ───────────────────────────────────────────────
        if not on_ground:
            state = MarioState.JUMP
        elif vel.vx != 0:
            state = MarioState.WALK
            if step_tick % 12 == 0:
                sounds.append(SoundEvent.WALK)
            frame = anim_tick // 8
        else:
            state = MarioState.IDLE
            frame = 0

    return replace(
        mario,
        position=pos,
        velocity=vel,
        state=state,
        facing=facing,
        on_ground=on_ground,
        climbing=climbing,
        ladder_cx=ladder_cx,
        frame=frame,
        anim_tick=anim_tick,
        invincible_frames=inv,
        step_sound_tick=step_tick,
    )


# ---------------------------------------------------------------------------
# Actualización de barriles
# ---------------------------------------------------------------------------


def _update_barrel(
    barrel: Barrel,
    level: Level,
    speed_mult: float,
    sounds: list[SoundEvent],
) -> Barrel:
    """Aplica física a un barril y retorna el nuevo estado."""
    vel = phy.apply_gravity(barrel.velocity, phy.BARREL_GRAVITY_MULT)
    pos = phy.integrate(barrel.position, vel)

    current_pid = barrel.current_pid
    new_vel = vel

    for plat in level.platforms:
        if not plat.contains_x(pos.x):
            continue
        delta = pos.y - plat.y
        if 0.0 <= delta <= 24.0 and vel.vy >= 0:
            pos = pos.with_y(plat.y)
            if current_pid != plat.pid:
                current_pid = plat.pid
                new_vel = phy.barrel_roll_velocity(plat.direction, speed_mult)
                sounds.append(SoundEvent.BARREL_LAND)
            else:
                new_vel = vel.zero_y()
            break

    alive = pos.y <= phy.SCREEN_HEIGHT + 40.0
    roll = barrel.roll_frame + (1 if vel.vx != 0 else 0)

    return replace(
        barrel,
        position=pos,
        velocity=new_vel,
        current_pid=current_pid,
        roll_frame=roll,
        alive=alive,
    )


# ---------------------------------------------------------------------------
# Actualización de llamas
# ---------------------------------------------------------------------------


def _update_flame(
    flame: Flame,
    level: Level,
    mario_pos: Position,
    speed_mult: float,
) -> Flame:
    """Actualiza la IA de una llama (persecución + escalada)."""
    tick = flame.frame_tick + 1

    if flame.climbing:
        lad = next(
            (ldr for ldr in level.ladders if ldr.cx == flame.climb_ladder_cx),
            None,
        )
        if lad is None:
            return replace(flame, climbing=False, climb_ladder_cx=None, frame_tick=tick)

        pos, vel, exited = phy.resolve_ladder_movement(
            flame.position,
            flame.velocity,
            lad,
            flame.climb_direction,
            speed=phy.FLAME_SPEED * speed_mult,
        )
        if exited:
            return replace(
                flame,
                position=pos,
                velocity=vel,
                climbing=False,
                climb_ladder_cx=None,
                frame_tick=tick,
            )
        return replace(flame, position=pos, velocity=vel, frame_tick=tick)

    # Persecución horizontal
    dir_sign = math.copysign(1.0, mario_pos.x - flame.position.x)
    target_vx = dir_sign * phy.FLAME_SPEED * speed_mult
    new_vx = flame.velocity.vx + (target_vx - flame.velocity.vx) * 0.04
    vel = replace(flame.velocity, vx=new_vx)
    vel = phy.apply_gravity(vel)
    pos = phy.integrate(flame.position, vel)

    on_ground = False
    for plat in level.platforms:
        if plat.contains_x(pos.x):
            delta = pos.y - plat.y
            if 0.0 <= delta <= 20.0 and vel.vy >= 0:
                pos = pos.with_y(plat.y)
                vel = vel.zero_y()
                on_ground = True
                break

    # Intentar subir escalera hacia Mario
    new_climbing: bool = flame.climbing
    new_lad_cx = flame.climb_ladder_cx
    new_dir = flame.climb_direction
    if on_ground and tick % 40 == 0:
        for lad in level.ladders:
            if abs(flame.position.x - lad.cx) < 14 and lad.y_top < flame.position.y <= lad.y_bottom:
                cdirection = -1 if mario_pos.y < flame.position.y else 1
                if (cdirection == -1 and mario_pos.y < flame.position.y) or (
                    cdirection == 1 and mario_pos.y > flame.position.y
                ):
                    new_climbing = True
                    new_lad_cx = lad.cx
                    new_dir = cdirection
                    pos = pos.with_x(lad.cx)
                    break

    alive = pos.y <= phy.SCREEN_HEIGHT + 40.0

    return replace(
        flame,
        position=pos,
        velocity=vel,
        climbing=new_climbing,
        climb_direction=new_dir,
        climb_ladder_cx=new_lad_cx,
        frame_tick=tick,
        alive=alive,
    )


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------


class GameEngine:
    """Motor de juego que transforma GameWorld + InputState → EngineOutput.

    El RNG es inyectado para hacer el motor determinista con semilla fija.
    """

    def __init__(self, rng: RNG) -> None:
        """Inicializa el motor.

        Args:
            rng: generador de números aleatorios inyectado.
        """
        self._rng = rng

    def new_game(self, high_score: int = 0) -> GameWorld:
        """Crea un nuevo mundo para empezar una partida.

        Args:
            high_score: récord previo a preservar.

        Returns:
            GameWorld inicial con fase INTRO.
        """
        level = build_level(1)
        return initial_world(level=level, level_num=1, lives=3, high_score=high_score)

    def new_level(self, world: GameWorld) -> GameWorld:
        """Avanza al siguiente nivel preservando score y vidas.

        Args:
            world: mundo actual al terminar el nivel.

        Returns:
            GameWorld inicial del nuevo nivel.
        """
        level_num = world.level_num + 1
        level = build_level(level_num)
        return initial_world(
            level=level,
            level_num=level_num,
            lives=world.lives,
            high_score=world.score.high,
        )

    def respawn(self, world: GameWorld) -> GameWorld:
        """Respawnea a Mario tras perder una vida.

        Args:
            world: mundo con Mario muerto.

        Returns:
            GameWorld con Mario reseteado, barriles/llamas limpiados.
        """
        mario = Mario.initial(world.level.mario_start)
        return replace(
            world,
            mario=mario,
            barrels=(),
            flames=(),
            phase=GamePhase.PLAYING,
            jumped_barrel_ids=frozenset(),
            prev_mario_vy=0.0,
            state_tick=0,
            flame_timer=0,
        )

    def tick(self, world: GameWorld, inp: InputState) -> EngineOutput:
        """Ejecuta un frame del juego.

        Args:
            world: estado actual.
            inp: input del jugador en este frame.

        Returns:
            EngineOutput con el nuevo estado y eventos generados.
        """
        sounds: list[SoundEvent] = []
        score_events: list[ScoreEvent] = []

        match world.phase:
            case GamePhase.INTRO:
                return self._tick_intro(world, sounds)
            case GamePhase.PLAYING:
                return self._tick_playing(world, inp, sounds, score_events)
            case GamePhase.PAUSED:
                return EngineOutput(
                    world=replace(world, state_tick=world.state_tick + 1),
                    sound_events=(),
                    score_events=(),
                )
            case _:
                # MENU, LEVEL_UP, GAME_OVER, WIN: solo avanzar state_tick
                return EngineOutput(
                    world=replace(world, state_tick=world.state_tick + 1),
                    sound_events=(),
                    score_events=(),
                )

    def _tick_intro(self, world: GameWorld, sounds: list[SoundEvent]) -> EngineOutput:
        new_tick = world.state_tick + 1
        phase = world.phase
        if new_tick >= _INTRO_DURATION:
            phase = GamePhase.PLAYING
            new_tick = 0
        return EngineOutput(
            world=replace(world, state_tick=new_tick, phase=phase, tick=world.tick + 1),
            sound_events=tuple(sounds),
            score_events=(),
        )

    def _tick_playing(
        self,
        world: GameWorld,
        inp: InputState,
        sounds: list[SoundEvent],
        score_events: list[ScoreEvent],
    ) -> EngineOutput:
        sm = _speed_mult(world.level_num)
        prev_vy = world.mario.velocity.vy

        # ── Mario ─────────────────────────────────────────────────────────────
        mario = _update_mario(world.mario, inp, world.level, sounds)

        # ── Donkey Kong ───────────────────────────────────────────────────────
        dk, spawn_barrel = self._update_dk(world.dk, world.level_num, sounds)

        # ── Barriles ─────────────────────────────────────────────────────────
        barrels: list[Barrel] = []
        next_bid = world.next_barrel_id
        if spawn_barrel:
            barrel_start = world.level.dk_start.move(30.0, 0.0)
            barrels.append(
                Barrel(
                    barrel_id=next_bid,
                    position=barrel_start,
                    velocity=phy.barrel_roll_velocity(+1, sm),
                    current_pid=4,
                    roll_frame=0,
                    alive=True,
                )
            )
            next_bid += 1

        jumped_ids = set(world.jumped_barrel_ids)
        for b in world.barrels:
            nb = _update_barrel(b, world.level, sm, sounds)
            if nb.alive:
                barrels.append(nb)
                # Salto sobre barril
                if nb.barrel_id not in jumped_ids and col.mario_jumps_over_barrel(
                    mario, nb, prev_vy
                ):
                    jumped_ids.add(nb.barrel_id)
                    world = replace(world, score=world.score.add(_BARREL_JUMP_SCORE))
                    sounds.append(SoundEvent.BARREL_JUMP)
                    score_events.append(
                        ScoreEvent(
                            _BARREL_JUMP_SCORE,
                            nb.position,
                            (0, 200, 210),
                        )
                    )

        # ── Llamas ────────────────────────────────────────────────────────────
        flame_timer = world.flame_timer + 1
        spawn_interval = _flame_spawn_interval(world.level_num)
        next_fid = world.next_flame_id
        flames: list[Flame] = []
        if flame_timer >= spawn_interval and len(world.flames) < _flame_max(world.level_num):
            flame_timer = 0
            ground = world.level.platforms[0]
            flame_start = Position(55.0, ground.y)
            sounds.append(SoundEvent.FLAME_SPAWN)
            flames.append(
                Flame(
                    flame_id=next_fid,
                    position=flame_start,
                    velocity=Velocity(
                        vx=self._rng.choice([-1.0, 1.0]) * phy.FLAME_SPEED * sm,
                        vy=0.0,
                    ),
                    climbing=False,
                    climb_direction=0,
                    climb_ladder_cx=None,
                    frame_tick=0,
                    alive=True,
                )
            )
            next_fid += 1

        for f in world.flames:
            nf = _update_flame(f, world.level, mario.position, sm)
            if nf.alive:
                flames.append(nf)

        # ── Bonus items ───────────────────────────────────────────────────────
        bonus_spawn_timer = world.bonus_spawn_timer - 1
        next_boid = world.next_bonus_id
        bonuses: list[BonusItem] = []
        if bonus_spawn_timer <= 0:
            bonus_spawn_timer = self._rng.randint(400, 900)
            kind = self._rng.choice(list(BonusKind))
            plat = self._rng.choice(list(world.level.platforms[:4]))
            bx = float(self._rng.randint(int(plat.x_left) + 20, int(plat.x_right) - 20))
            bonuses.append(
                BonusItem(
                    bonus_id=next_boid,
                    position=Position(bx, plat.y),
                    kind=kind,
                    frame_tick=0,
                    life_remaining=_BONUS_LIFE,
                )
            )
            next_boid += 1

        for bo in world.bonuses:
            nb2 = replace(bo, frame_tick=bo.frame_tick + 1, life_remaining=bo.life_remaining - 1)
            if nb2.life_remaining > 0:
                bonuses.append(nb2)

        # ── Popups ────────────────────────────────────────────────────────────
        popups = [p.tick() for p in world.popups if p.tick().alive]

        # ── Colisiones ────────────────────────────────────────────────────────
        score = world.score
        lives = world.lives
        phase = GamePhase.PLAYING

        if mario.state != MarioState.DEAD:
            # Barriles
            for b in barrels:
                if col.mario_hit_by_barrel(mario, b):
                    mario, lives, sounds = self._kill_mario(mario, lives, sounds)
                    break

            # Llamas
            if mario.state != MarioState.DEAD:
                for f in flames:
                    if col.mario_hit_by_flame(mario, f):
                        mario, lives, sounds = self._kill_mario(mario, lives, sounds)
                        break

            # Bonus
            if mario.state != MarioState.DEAD:
                surviving_bonuses: list[BonusItem] = []
                for bo in bonuses:
                    if col.mario_collects_bonus(mario, bo):
                        score = score.add(bo.value)
                        sounds.append(SoundEvent.BONUS)
                        score_events.append(ScoreEvent(bo.value, bo.position, (210, 160, 0)))
                        popups.append(
                            ScorePopup(
                                bo.position.x,
                                bo.position.y - 10,
                                bo.value,
                                (210, 160, 0),
                                _POPUP_LIFE,
                            )
                        )
                    else:
                        surviving_bonuses.append(bo)
                bonuses = surviving_bonuses

            # Pauline (victoria)
            if mario.state != MarioState.DEAD and col.mario_reaches_pauline(mario, world.pauline):
                bonus_pts = _bonus_score(world.level_num, world.bonus_timer)
                score = score.add(bonus_pts)
                sounds.append(SoundEvent.WIN)
                score_events.append(ScoreEvent(bonus_pts, world.level.pauline_start, (255, 220, 0)))
                phase = GamePhase.LEVEL_UP

        # ── Resolución de muerte ──────────────────────────────────────────────
        if mario.is_dead_anim_done:
            if lives <= 0:
                phase = GamePhase.GAME_OVER
            else:
                # Respawn automático tras animación
                mario = Mario.initial(world.level.mario_start)
                barrels = []
                flames = []
                jumped_ids = set()

        bonus_timer = max(0, world.bonus_timer - 1)

        new_world = replace(
            world,
            mario=mario,
            dk=dk,
            pauline=replace(world.pauline, frame_tick=world.pauline.frame_tick + 1),
            barrels=tuple(barrels),
            flames=tuple(flames),
            bonuses=tuple(bonuses),
            popups=tuple(popups),
            score=score,
            lives=lives,
            bonus_timer=bonus_timer,
            tick=world.tick + 1,
            state_tick=world.state_tick + 1,
            next_barrel_id=next_bid,
            next_flame_id=next_fid,
            next_bonus_id=next_boid,
            flame_timer=flame_timer,
            bonus_spawn_timer=bonus_spawn_timer,
            phase=phase,
            jumped_barrel_ids=frozenset(jumped_ids),
            prev_mario_vy=prev_vy,
        )

        # Score events → popups
        for se in score_events:
            popups.append(
                ScorePopup(se.position.x, se.position.y - 10, se.value, se.color, _POPUP_LIFE)
            )

        return EngineOutput(
            world=replace(new_world, popups=tuple(popups)),
            sound_events=tuple(sounds),
            score_events=tuple(score_events),
        )

    def _update_dk(
        self,
        dk: DonkeyKong,
        level_num: int,
        sounds: list[SoundEvent],
    ) -> tuple[DonkeyKong, bool]:
        """Actualiza DK y devuelve (nuevo_dk, debe_lanzar_barril)."""
        frame_tick = dk.frame_tick + 1
        throw_timer = dk.throw_timer + 1
        cd = _throw_cd(level_num)
        throwing = dk.throwing
        throw_flash = max(0, dk.throw_flash - 1)
        spawn = False

        if throw_timer >= cd:
            throw_timer = 0
            throwing = True
            throw_flash = 30
            sounds.append(SoundEvent.THROW)
            spawn = True

        if throw_flash == 0:
            throwing = False

        return (
            replace(
                dk,
                frame_tick=frame_tick,
                throw_timer=throw_timer,
                throwing=throwing,
                throw_flash=throw_flash,
            ),
            spawn,
        )

    @staticmethod
    def _kill_mario(
        mario: Mario,
        lives: int,
        sounds: list[SoundEvent],
    ) -> tuple[Mario, int, list[SoundEvent]]:
        """Mata a Mario y decrementa vidas."""
        if mario.is_invincible:
            return mario, lives, sounds
        sounds.append(SoundEvent.DIE)
        dead_mario = replace(mario, state=MarioState.DEAD, velocity=Velocity.zero())
        return dead_mario, lives - 1, sounds
