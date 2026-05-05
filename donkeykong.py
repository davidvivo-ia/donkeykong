#!/usr/bin/env python3
"""
Donkey Kong — Classic Arcade Recreation in Python/Pygame

Controls:
  ← → / A D   Move left / right
  ↑ / W / Spc  Jump  (also enter ladder going up)
  ↑ ↓ / W S    Climb ladder
  P            Pause
  Esc          Quit / back to menu
"""

import pygame
import sys
import random
import math
import array

# ── Bootstrap ─────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

# ── Window ────────────────────────────────────────────────────────────────────
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("DONKEY KONG")
clock = pygame.time.Clock()
FPS = 60

# ── Physics ───────────────────────────────────────────────────────────────────
GRAVITY      = 0.55
JUMP_V       = -13.0
WALK         = 3.2
CLIMB        = 2.8
FLAME_SPEED  = 1.4

# ── Palette ───────────────────────────────────────────────────────────────────
BLACK    = (  0,   0,   0);  WHITE    = (255, 255, 255)
RED      = (220,  40,  40);  BLUE     = ( 50, 100, 220)
DKBLUE   = ( 20,  35, 140);  LTBLUE   = (100, 160, 255)
YELLOW   = (255, 220,   0);  GOLD     = (210, 160,   0)
BROWN    = (120,  70,  30);  DKBROWN  = ( 90,  50,  10)
GIRDCOL  = (200, 130,  40);  GIRDHI   = (240, 180,  80)
GIRDSH   = (130,  80,  10);  SKIN     = (255, 195, 145)
PINK     = (255, 140, 160);  GREEN    = ( 30, 160,  30)
GRAY     = (140, 140, 140);  LTGRAY   = (210, 210, 210)
DKGRAY   = ( 50,  50,  50);  ORANGE   = (230, 120,   0)
RHAT     = (200,  20,  20);  CREAM    = (255, 240, 210)
LADDC    = (210, 170,  70);  LADDS    = (150, 110,  30)
FLMYEL   = (255, 235,  80);  FLMORG   = (255, 100,   0)
FLMRED   = (200,  20,   0);  DKMONK   = (100,  60,  20)
NIGHT1   = (  8,  10,  40);  NIGHT2   = ( 18,  25,  80)
BARREL_D = ( 80,  45,  10);  BARREL_L = (180, 130,  50)
PURPLEC  = (140,  50, 180);  CYAN     = (  0, 200, 210)
NEONRED  = (255,  50,  80)

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_XL  = pygame.font.SysFont("monospace", 52, bold=True)
FONT_BIG = pygame.font.SysFont("monospace", 34, bold=True)
FONT_MED = pygame.font.SysFont("monospace", 22, bold=True)
FONT_SM  = pygame.font.SysFont("monospace", 16)
FONT_XS  = pygame.font.SysFont("monospace", 13)

# ── Procedural Sounds ─────────────────────────────────────────────────────────
def _tone(freq, dur, vol=0.32, shape='square', decay=True, attack=0.01):
    sr = 22050
    n  = int(sr * dur)
    buf = array.array('h', [0] * n)
    for i in range(n):
        t  = i / sr
        ph = 2 * math.pi * freq * t
        if   shape == 'square': v = 1.0 if math.sin(ph) > 0 else -1.0
        elif shape == 'saw':    v = 2 * (freq * t % 1) - 1
        elif shape == 'tri':    v = 2 * abs(2 * (freq * t % 1) - 1) - 1
        else:                   v = math.sin(ph)
        att = min(i / max(1, int(sr * attack)), 1.0)
        dec = (1 - i / n) ** 0.6 if decay else 1.0
        buf[i] = int(v * att * dec * vol * 32767)
    return pygame.mixer.Sound(buffer=buf)

def _chord(freqs, dur, vol=0.22):
    sr = 22050; n = int(sr * dur)
    buf = array.array('h', [0] * n)
    for i in range(n):
        t = i / sr
        v = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        env = (1 - i / n) ** 0.4
        buf[i] = int(v * env * vol * 32767)
    return pygame.mixer.Sound(buffer=buf)

def _slide(f0, f1, dur, vol=0.28, shape='square'):
    sr = 22050; n = int(sr * dur)
    buf = array.array('h', [0] * n)
    ph  = 0.0
    for i in range(n):
        freq = f0 + (f1 - f0) * (i / n)
        ph  += 2 * math.pi * freq / sr
        v    = 1.0 if math.sin(ph) > 0 else -1.0
        env  = (1 - i / n) ** 0.5
        buf[i] = int(v * env * vol * 32767)
    return pygame.mixer.Sound(buffer=buf)

try:
    SND_JUMP   = _slide(400, 700, 0.16, vol=0.30)
    SND_LAND   = _tone(120, 0.09, shape='square', decay=True)
    SND_WALK   = _tone(130, 0.05, vol=0.12, shape='square', decay=False)
    SND_CLIMB  = _tone(200, 0.07, vol=0.15, shape='square', decay=False)
    SND_BARREL = _tone(140, 0.13, shape='square', decay=True)
    SND_DIE    = _slide(400, 80, 0.55, vol=0.35, shape='saw')
    SND_SCORE  = _tone(780, 0.09, shape='sine', decay=True)
    SND_WIN    = _chord([523, 659, 784, 1047], 1.0, vol=0.28)
    SND_THROW  = _tone(240, 0.18, shape='square', decay=True)
    SND_FLAME  = _tone(260, 0.18, shape='saw', decay=True)
    SND_BONUS  = _chord([660, 880, 1100], 0.5, vol=0.25)
    SND_LVLUP  = _chord([440, 550, 660, 880], 1.2, vol=0.30)
    _SND_OK    = True
except Exception:
    _SND_OK    = False

def play(snd):
    if _SND_OK:
        try: snd.play()
        except Exception: pass

# ── Level Blueprint ───────────────────────────────────────────────────────────
# (x_left, x_right, y_surface, barrel_direction)
# barrel_direction: +1 → roll right, -1 → roll left
PLATFORMS = [
    #  xl    xr    y   dir  pid
    (  10,  790,  535,  +1,  0),   # Ground
    (  30,  760,  425,  -1,  1),   # P2
    (  30,  760,  315,  +1,  2),   # P3
    (  30,  760,  205,  -1,  3),   # P4
    (  10,  760,   95,  +1,  4),   # Top (DK area)
]

# (x_center, y_top, y_bottom)
LADDERS = [
    (160,  425,  535),
    (580,  425,  535),
    (250,  315,  425),
    (645,  315,  425),
    (185,  205,  315),
    (605,  205,  315),
    (370,   95,  205),
]

DK_CX, DK_BY    = 115,  95   # DK centre-x, bottom-y = top platform surface y
PAULINE_CX       = 620
MARIO_START_CX   = 60
MARIO_START_BY   = 535   # ground platform surface y → starts on ground
PLATFORM_H       = 14
LADDER_W         = 16

# ── Drawing Helpers ───────────────────────────────────────────────────────────
def rect(surf, col, x, y, w, h, r=0):
    pygame.draw.rect(surf, col, (x, y, w, h), border_radius=r)

def circle(surf, col, cx, cy, rad):
    pygame.draw.circle(surf, col, (int(cx), int(cy)), int(rad))

def poly(surf, col, pts):
    pygame.draw.polygon(surf, col, pts)

def text_shadow(surf, font, msg, col, x, y, shadow=BLACK, ox=2, oy=2):
    s = font.render(str(msg), True, shadow)
    surf.blit(s, (x + ox, y + oy))
    s = font.render(str(msg), True, col)
    surf.blit(s, (x, y))

def center_text(surf, font, msg, col, cy, shadow=True):
    s = font.render(str(msg), True, col)
    x = W // 2 - s.get_width() // 2
    if shadow:
        sh = font.render(str(msg), True, BLACK)
        surf.blit(sh, (x + 2, cy + 2))
    surf.blit(s, (x, cy))

# ── Sprite Painters ───────────────────────────────────────────────────────────
def draw_girder(surf, xl, xr, y, h=PLATFORM_H):
    """Draw an orange steel girder beam with highlight/shadow and rivets."""
    rect(surf, GIRDSH,  xl,     y+3,  xr-xl, h)
    rect(surf, GIRDCOL, xl,     y,    xr-xl, h-2)
    rect(surf, GIRDHI,  xl,     y,    xr-xl, 3)
    for rx in range(xl + 14, xr - 10, 28):
        circle(surf, GIRDHI, rx, y + h//2, 3)
        circle(surf, GIRDSH, rx+1, y + h//2+1, 2)

def draw_ladder(surf, cx, yt, yb):
    """Draw a yellow ladder with rungs."""
    hw = LADDER_W // 2
    rect(surf, LADDS,  cx - hw - 1, yt, 5, yb - yt)
    rect(surf, LADDS,  cx + hw - 3, yt, 5, yb - yt)
    rect(surf, LADDC,  cx - hw,     yt, 4, yb - yt)
    rect(surf, LADDC,  cx + hw - 2, yt, 4, yb - yt)
    rung_gap = 14
    for ry in range(yt + 4, yb, rung_gap):
        rect(surf, LADDS, cx - hw,     ry + 1, LADDER_W, 3)
        rect(surf, LADDC, cx - hw,     ry,     LADDER_W, 3)

def draw_mario(surf, cx, by, frame=0, facing=1, state='walk', dead_anim=0, scale=1.0):
    """
    Draw Mario as a 32×44 pixel figure.
    scale: 1.0 for full size, 0.5 for HUD mini-icons, etc.
    state: 'walk' | 'jump' | 'climb' | 'dead'
    """
    SW, SH = 32, 44

    def _build():
        s = pygame.Surface((SW, SH), pygame.SRCALPHA)

        # ── Hat ───────────────────────────────────────────────────────────────
        rect(s, RHAT,  5,  0, 22,  8)    # crown
        rect(s, RHAT,  1,  6, 30,  5)    # brim

        # ── Head ──────────────────────────────────────────────────────────────
        rect(s, SKIN,  7,  9, 18, 14)
        ex = 21 if facing == 1 else 7
        rect(s, BLACK, ex, 12,  4,  5)   # eye
        rect(s, WHITE, ex+1, 13, 2,  2)  # gleam
        rect(s, SKIN,  13, 19,  6,  4)   # nose
        rect(s, BROWN,  7, 19,  7,  3)   # moustache L
        rect(s, BROWN, 18, 19,  7,  3)   # moustache R

        if state == 'climb':
            cf = frame % 2
            if cf == 0:
                rect(s, RED,  0, 22, 10,  7)   # L arm up
                rect(s, RED, 22, 28, 10,  7)   # R arm down
            else:
                rect(s, RED,  0, 28, 10,  7)
                rect(s, RED, 22, 22, 10,  7)
            rect(s, RED,  6, 22, 20, 13)        # shirt body
            rect(s, BLUE, 9, 22, 14, 13)        # overall bib
            rect(s, RED,  6, 22,  4,  8)        # shirt sides
            rect(s, RED, 22, 22,  4,  8)
            rect(s, BLUE, 5, 34, 10,  8)        # L leg
            rect(s, BLUE,17, 34, 10,  8)        # R leg
            rect(s, DKBROWN, 3, 40, 13, 4)
            rect(s, DKBROWN,16, 40, 13, 4)

        elif state == 'jump':
            rect(s, RED,  0, 20, 10,  8)        # L arm up
            rect(s, RED, 22, 20, 10,  8)        # R arm up
            rect(s, RED,  6, 22, 20, 12)
            rect(s, BLUE, 9, 22, 14, 12)
            rect(s, RED,  6, 22,  4,  8)
            rect(s, RED, 22, 22,  4,  8)
            rect(s, BLUE, 3, 33, 12,  8)        # legs spread
            rect(s, BLUE,17, 33, 12,  8)
            rect(s, DKBROWN, 1, 39, 13, 5)
            rect(s, DKBROWN,18, 39, 13, 5)

        else:  # walk
            wf = frame % 2
            if wf == 0:
                rect(s, RED,  0, 23, 10,  8)    # L arm fwd
                rect(s, RED, 22, 27, 10,  8)    # R arm back
            else:
                rect(s, RED,  0, 27, 10,  8)
                rect(s, RED, 22, 23, 10,  8)
            rect(s, RED,  6, 22, 20, 12)
            rect(s, BLUE, 9, 22, 14, 12)
            rect(s, RED,  6, 22,  4,  8)
            rect(s, RED, 22, 22,  4,  8)
            # Suspender buckles
            rect(s, GOLD, 10, 23,  4,  3)
            rect(s, GOLD, 18, 23,  4,  3)
            if wf == 0:
                rect(s, BLUE,  6, 33, 11, 10)   # L leg fwd
                rect(s, BLUE, 15, 31, 11, 10)   # R leg back
                rect(s, DKBROWN, 4, 41, 14, 4)
                rect(s, DKBROWN,14, 39, 14, 4)
            else:
                rect(s, BLUE,  6, 31, 11, 10)
                rect(s, BLUE, 15, 33, 11, 10)
                rect(s, DKBROWN, 4, 39, 14, 4)
                rect(s, DKBROWN,14, 41, 14, 4)
        return s

    if state == 'dead':
        s = _build()
        angle = dead_anim * 18
        rs = pygame.transform.rotate(s, angle)
        surf.blit(rs, (int(cx) - rs.get_width()//2,
                       int(by) - rs.get_height()//2))
        return

    s = _build()
    if facing == -1:
        s = pygame.transform.flip(s, True, False)

    if scale != 1.0:
        ns = (int(SW * scale), int(SH * scale))
        s = pygame.transform.scale(s, ns)
        surf.blit(s, (int(cx) - ns[0]//2, int(by) - ns[1]))
    else:
        surf.blit(s, (int(cx) - SW//2, int(by) - SH))

def draw_dk(surf, cx, by, frame=0, throwing=False):
    """Draw Donkey Kong — 66×84 pixel sprite, all parts overlapping so no gaps."""
    SW, SH = 66, 84
    FUR   = DKMONK                  # (100, 60, 20) dark brown fur
    FACE  = (175, 125, 70)          # lighter tan muzzle/chest
    INNER = (80,  45, 15)           # inner ear / shadow
    TOOTH = (240, 240, 220)

    s = pygame.Surface((SW, SH), pygame.SRCALPHA)

    # ── ARMS (behind body — draw first) ──────────────────────────────────────
    tf = frame % 2
    if throwing:
        # Left arm hangs low
        pygame.draw.ellipse(s, FUR,  ( 0, 36, 14, 26))
        circle(s, FUR,  7, 62, 7)          # left fist
        # Right arm raised high
        pygame.draw.ellipse(s, FUR,  (52,  4, 14, 30))
        circle(s, FUR, 59,  5, 7)          # right fist (top)
        # Tiny barrel in right hand
        pygame.draw.ellipse(s, BARREL_D, (51,  0, 16, 10))
        pygame.draw.ellipse(s, BARREL_L, (53,  1, 12,  7))
        rect(s, BARREL_D, 51,  4,  16,  2)  # band
    else:
        arm_top = 28 if tf == 0 else 24
        arm_h   = 28 if tf == 0 else 32
        # Left arm
        pygame.draw.ellipse(s, FUR,  ( 0, arm_top, 14, arm_h))
        circle(s, FUR,  7, arm_top + arm_h,  7)
        # Right arm
        pygame.draw.ellipse(s, FUR,  (52, arm_top, 14, arm_h))
        circle(s, FUR, 59, arm_top + arm_h,  7)

    # ── BODY (torso) ──────────────────────────────────────────────────────────
    # Main torso blob — fills from neck to hips
    pygame.draw.ellipse(s, FUR,   ( 8, 28, 50, 42))
    # Chest / belly lighter patch
    pygame.draw.ellipse(s, FACE,  (14, 32, 38, 32))

    # ── LEGS ─────────────────────────────────────────────────────────────────
    # Left leg — overlaps body bottom so no gap
    pygame.draw.ellipse(s, FUR,   (10, 60, 20, 26))
    # Right leg
    pygame.draw.ellipse(s, FUR,   (36, 60, 20, 26))
    # Feet (wider ellipses at bottom)
    pygame.draw.ellipse(s, FUR,   ( 4, 74, 26, 10))
    pygame.draw.ellipse(s, FUR,   (36, 74, 26, 10))

    # ── HEAD ─────────────────────────────────────────────────────────────────
    # Skull — center at (33, 17), radius 17 → top=0, bottom=34, overlaps body at 28 ✓
    circle(s, FUR,  33, 17, 17)

    # Ears (outside skull, overlap it)
    circle(s, FUR,  13, 13,  8)
    circle(s, INNER, 13, 13,  5)
    circle(s, FUR,  53, 13,  8)
    circle(s, INNER, 53, 13,  5)

    # Muzzle / face
    pygame.draw.ellipse(s, FACE, (20, 14, 26, 22))

    # Eyes — white sclera then dark pupil then highlight
    pygame.draw.ellipse(s, WHITE, (20,  8,  9,  8))
    pygame.draw.ellipse(s, WHITE, (37,  8,  9,  8))
    circle(s, BLACK, 24, 12,  4)
    circle(s, BLACK, 41, 12,  4)
    circle(s, WHITE, 23, 10,  1)   # gleam
    circle(s, WHITE, 40, 10,  1)

    # Brow ridge (angry)
    pygame.draw.line(s, INNER, (18, 7), (28, 10), 3)
    pygame.draw.line(s, INNER, (38, 10), (48, 7), 3)

    # Nose
    pygame.draw.ellipse(s, FACE, (25, 20, 16, 10))
    circle(s, INNER, 29, 24, 3)   # nostril L
    circle(s, INNER, 37, 24, 3)   # nostril R

    # Mouth
    rect(s, INNER, 22, 30, 22, 4, 1)
    rect(s, TOOTH, 23, 30,  9, 3)   # left teeth
    rect(s, TOOTH, 34, 30,  9, 3)   # right teeth

    # Draw sprite: feet at `by`, horizontally centered
    surf.blit(s, (int(cx) - SW // 2, int(by) - SH + 2))

def draw_barrel(surf, cx, by, roll_frame=0):
    """Draw a rolling barrel."""
    W2, H2 = 18, 14
    x = int(cx - W2 // 2)
    y = int(by - H2)
    s = pygame.Surface((W2, H2), pygame.SRCALPHA)

    rect(s, BARREL_D,  0,  0, W2, H2, 3)
    rect(s, BARREL_L,  2,  1, W2-4, H2-2, 2)
    # Barrel bands (rotate with frame)
    band_y = (roll_frame * 2) % H2
    for ky in range(-H2, H2*2, 5):
        ry = (band_y + ky) % H2
        if 0 <= ry < H2:
            rect(s, BARREL_D, 1, ry, W2-2, 2)

    surf.blit(s, (x, y))

def draw_flame(surf, cx, by, frame=0):
    """Draw an animated flame enemy."""
    x = int(cx)
    y = int(by)
    f = frame % 2
    # Base flame (red)
    poly(surf, FLMRED, [
        (x-8, y), (x+8, y), (x+5, y-10), (x, y-16), (x-5, y-10)
    ])
    # Middle (orange)
    poly(surf, FLMORG, [
        (x-5, y), (x+5, y), (x+3, y-8+f*2), (x, y-13+f*2), (x-3, y-8+f*2)
    ])
    # Core (yellow)
    poly(surf, FLMYEL, [
        (x-3, y), (x+3, y), (x, y-7+f)
    ])
    # Eyes
    rect(surf, BLACK, x-5, y-12, 3, 3)
    rect(surf, BLACK, x+2, y-12, 3, 3)
    rect(surf, WHITE, x-4, y-11, 1, 1)
    rect(surf, WHITE, x+3, y-11, 1, 1)

def draw_pauline(surf, cx, by, frame=0):
    """Draw Pauline waving — 28×48 px, stands on platform at `by`."""
    SW, SH = 28, 48
    f = frame % 2
    s = pygame.Surface((SW, SH), pygame.SRCALPHA)

    # Hair — golden, full top
    circle(s, GOLD,    14,  6, 10)
    rect(s,   GOLD,     4,  4, 20, 12)
    # Side curls
    circle(s, GOLD,     5, 14,  5)
    circle(s, GOLD,    23, 14,  5)

    # Head
    rect(s, SKIN,       7,  8, 14, 15)

    # Eyes
    rect(s, BLACK,      9, 12,  3,  3)
    rect(s, BLACK,     16, 12,  3,  3)
    rect(s, WHITE,     10, 13,  1,  1)
    rect(s, WHITE,     17, 13,  1,  1)
    # Smile
    rect(s, RED,       10, 20,  8,  2)

    # Arms (wave alternating)
    if f == 0:
        rect(s, SKIN,   0, 22,  6, 10)   # L arm raised
        rect(s, SKIN,  22, 26,  6, 10)   # R arm low
    else:
        rect(s, SKIN,   0, 26,  6, 10)
        rect(s, SKIN,  22, 22,  6, 10)

    # Dress body
    rect(s, PINK,       6, 22, 16, 16)
    # Dress flare (trapezoid)
    poly(s, PINK, [(3, 36), (25, 36), (27, 48), (1, 48)])
    # Belt
    rect(s, RED,        6, 28, 16,  3)
    # Shoes
    rect(s, RED,        5, 44,  8,  4)
    rect(s, RED,       15, 44,  8,  4)

    surf.blit(s, (int(cx) - SW//2, int(by) - SH))

def draw_bonus_item(surf, cx, by, kind='purse', frame=0):
    """Draw a collectable bonus item."""
    x, y = int(cx), int(by)
    bob = int(math.sin(frame * 0.15) * 3)
    y += bob
    if kind == 'purse':
        circle(surf, PINK,   x, y-10, 8)
        rect(surf, DKBROWN,  x-4, y-20, 8, 6, 2)
        circle(surf, GOLD,   x, y-10, 5)
        circle(surf, YELLOW, x, y-10, 3)
    elif kind == 'hat':
        rect(surf, RED,     x-8, y-8, 16, 6)
        rect(surf, RED,     x-5, y-16, 10, 9)
        rect(surf, YELLOW,  x-8, y-9,  16,  2)
    elif kind == 'umbrella':
        pygame.draw.arc(surf, PINK,   (x-10, y-20, 20, 14), 0, math.pi, 4)
        pygame.draw.line(surf, BROWN, (x, y-14), (x, y-2), 2)
        pygame.draw.arc(surf, BROWN,  (x-4, y-4, 8, 6), math.pi, 2*math.pi, 2)

# ── Background ────────────────────────────────────────────────────────────────
_stars = [(random.randint(0, W), random.randint(0, H//2),
           random.randint(1, 3), random.uniform(0.3, 1.0))
          for _ in range(80)]

def draw_background(surf, t):
    # Gradient sky
    for gy in range(H):
        ratio = gy / H
        r = int(NIGHT1[0] + (NIGHT2[0] - NIGHT1[0]) * ratio)
        g = int(NIGHT1[1] + (NIGHT2[1] - NIGHT1[1]) * ratio)
        b = int(NIGHT1[2] + (NIGHT2[2] - NIGHT1[2]) * ratio)
        pygame.draw.line(surf, (r, g, b), (0, gy), (W, gy))
    # Twinkling stars
    for sx, sy, sr, spd in _stars:
        bright = int(128 + 127 * math.sin(t * spd * 0.05))
        pygame.draw.circle(surf, (bright, bright, bright), (sx, sy), sr)
    # Distant city silhouette
    buildings = [
        (0, 70, 50), (60, 90, 40), (110, 75, 35), (155, 85, 45),
        (200, 65, 55), (260, 80, 30), (300, 70, 50), (360, 90, 40),
        (410, 75, 45), (460, 85, 35), (510, 70, 55), (570, 80, 40),
        (620, 65, 50), (680, 90, 35), (730, 75, 45), (770, 80, 30),
    ]
    for bx, bh, bw in buildings:
        by = H - bh
        rect(surf, (15, 20, 55), bx, by, bw, bh)
        # Windows
        for wy in range(by + 5, H - 5, 14):
            for wx in range(bx + 5, bx + bw - 8, 10):
                wc = YELLOW if random.random() < 0.6 else (30, 30, 60)
                rect(surf, wc, wx, wy, 5, 7)

# ── Score Popup ───────────────────────────────────────────────────────────────
class ScorePopup:
    def __init__(self, x, y, value, color=YELLOW):
        self.x = x; self.y = y; self.vy = -1.2
        self.text = f"+{value}"
        self.color = color
        self.life = 60  # frames

    def update(self):
        self.y += self.vy
        self.life -= 1

    def draw(self, surf):
        alpha = max(0, min(255, self.life * 4))
        s = FONT_SM.render(self.text, True, self.color)
        s.set_alpha(alpha)
        surf.blit(s, (self.x - s.get_width()//2, int(self.y)))

    @property
    def alive(self):
        return self.life > 0

# ── Platform ─────────────────────────────────────────────────────────────────
class Platform:
    def __init__(self, xl, xr, y, direction, pid):
        self.xl  = xl; self.xr = xr; self.y = y
        self.direction = direction   # +1 or -1
        self.pid = pid
        self.rect = pygame.Rect(xl, y, xr - xl, PLATFORM_H)

    def draw(self, surf):
        draw_girder(surf, self.xl, self.xr, self.y)

    def contains_x(self, x):
        return self.xl <= x <= self.xr

# ── Ladder ────────────────────────────────────────────────────────────────────
class Ladder:
    def __init__(self, cx, yt, yb):
        self.cx = cx; self.yt = yt; self.yb = yb
        self.rect = pygame.Rect(cx - LADDER_W//2, yt, LADDER_W, yb - yt)

    def draw(self, surf):
        draw_ladder(surf, self.cx, self.yt, self.yb)

    def mario_aligned(self, mario_cx):
        return abs(mario_cx - self.cx) < 12

    def mario_can_grab(self, mario_cx, mario_by):
        """True when Mario's feet are inside the ladder range."""
        return (self.mario_aligned(mario_cx)
                and self.yt < mario_by < self.yb + 4)

# ── Barrel ────────────────────────────────────────────────────────────────────
class Barrel:
    W2 = 9; H2 = 14    # half-width, height

    def __init__(self, x, y, direction, platforms, speed_mult=1.0):
        self.x = float(x); self.y = float(y)
        self.vx = direction * 2.8 * speed_mult
        self.vy = 0.0
        self.on_ground = False
        self.platforms = platforms
        self.speed_mult = speed_mult
        self.roll_frame = 0
        self.alive = True
        self._current_pid = 4  # starts on top platform

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - self.W2, int(self.y) - self.H2,
                           self.W2 * 2, self.H2)

    def update(self):
        self.vy += GRAVITY * 1.1
        self.x  += self.vx
        self.y  += self.vy

        self.on_ground = False

        # Platform collision
        for plat in self.platforms:
            if (plat.xl - 2 <= self.x <= plat.xr + 2
                    and 0 < self.y - plat.y < 24
                    and self.vy >= 0):
                self.y = plat.y
                self.vy = 0
                self.on_ground = True
                # Adopt this platform's roll direction
                if self._current_pid != plat.pid:
                    self._current_pid = plat.pid
                    self.vx = plat.direction * 2.8 * self.speed_mult
                    play(SND_BARREL)
                break

        # Fell off screen → disappear
        if self.y > H + 40:
            self.alive = False

        # Roll off left/right edges → keep falling
        self.roll_frame += 1 if self.vx != 0 else 0

    def draw(self, surf):
        draw_barrel(surf, self.x, self.y, self.roll_frame // 4)

# ── Flame ─────────────────────────────────────────────────────────────────────
class Flame:
    def __init__(self, x, y, platforms, ladders, speed_mult=1.0):
        self.x = float(x); self.y = float(y)
        self.vx = random.choice([-1, 1]) * FLAME_SPEED * speed_mult
        self.vy = 0.0
        self.on_ground = False
        self.platforms = platforms
        self.ladders = ladders
        self.speed_mult = speed_mult
        self.frame_count = 0
        self.alive = True
        self._climb_ladder = None
        self._climbing = False
        self._climb_dir = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 8, int(self.y) - 18, 16, 18)

    def update(self, mario_x, mario_y):
        self.frame_count += 1

        # Chase Mario roughly
        if not self._climbing:
            target_vx = math.copysign(FLAME_SPEED * self.speed_mult,
                                      mario_x - self.x)
            self.vx += (target_vx - self.vx) * 0.04

            self.vy += GRAVITY
            self.x  += self.vx
            self.y  += self.vy
            self.on_ground = False

            for plat in self.platforms:
                if (plat.xl <= self.x <= plat.xr
                        and 0 < self.y - plat.y < 20
                        and self.vy >= 0):
                    self.y = plat.y
                    self.vy = 0
                    self.on_ground = True
                    break

            # Sometimes try to climb a ladder toward Mario
            if self.on_ground and self.frame_count % 40 == 0:
                for lad in self.ladders:
                    if (abs(self.x - lad.cx) < 14
                            and lad.yt < self.y <= lad.yb):
                        direction = -1 if mario_y < self.y else 1
                        # Only climb if it brings us closer
                        if ((direction == -1 and mario_y < self.y)
                                or (direction == 1 and mario_y > self.y)):
                            self._climbing = True
                            self._climb_ladder = lad
                            self._climb_dir = direction
                            self.x = lad.cx
                            break
        else:
            lad = self._climb_ladder
            self.y += self._climb_dir * CLIMB * self.speed_mult
            self.x = lad.cx
            # Exit ladder
            if self._climb_dir == -1 and self.y <= lad.yt:
                self.y = lad.yt
                self._climbing = False
                self.vy = 0
            elif self._climb_dir == 1 and self.y >= lad.yb:
                self.y = lad.yb
                self._climbing = False
                self.vy = 0

        if self.y > H + 40:
            self.alive = False

    def draw(self, surf):
        draw_flame(surf, self.x, self.y, self.frame_count // 8)

# ── Pauline ───────────────────────────────────────────────────────────────────
class Pauline:
    def __init__(self, cx, by):
        self.cx = cx; self.by = by
        self.frame = 0

    def update(self):
        self.frame += 1

    def draw(self, surf):
        draw_pauline(surf, self.cx, self.by, self.frame // 12)

    @property
    def rect(self):
        return pygame.Rect(int(self.cx) - 14, int(self.by) - 48, 28, 48)

# ── DonkeyKong ────────────────────────────────────────────────────────────────
class DonkeyKong:
    def __init__(self, cx, by):
        self.cx = float(cx); self.by = float(by)
        self.frame = 0
        self.throw_timer  = 0
        self.throw_cd     = 180   # frames between throws
        self.throwing     = False
        self.throw_flash  = 0

    def update(self, speed_mult=1.0, level=1):
        self.frame += 1
        self.throw_timer += 1
        cd = max(90, int(self.throw_cd / (1 + 0.15 * (level - 1))))
        if self.throw_timer >= cd:
            self.throw_timer  = 0
            self.throwing     = True
            self.throw_flash  = 30
            play(SND_THROW)
            return True   # signal: spawn a barrel
        if self.throw_flash > 0:
            self.throw_flash -= 1
        else:
            self.throwing = False
        return False

    def draw(self, surf):
        draw_dk(surf, self.cx, self.by, self.frame // 14, self.throwing)
        if self.throw_flash > 0:
            # Rage eyes glow
            ex1 = int(self.cx - 7); ex2 = int(self.cx + 4)
            ey  = int(self.by - 46)
            pygame.draw.circle(surf, RED, (ex1, ey), 4)
            pygame.draw.circle(surf, RED, (ex2, ey), 4)

# ── Bonus Item ────────────────────────────────────────────────────────────────
BONUS_KINDS = ['purse', 'hat', 'umbrella']
BONUS_VALUES = {'purse': 300, 'hat': 500, 'umbrella': 800}

class BonusItem:
    def __init__(self, x, y, kind):
        self.x = x; self.y = y
        self.kind = kind
        self.value = BONUS_VALUES[kind]
        self.frame = 0
        self.alive = True
        self.life  = 600   # disappears after 10s

    def update(self):
        self.frame += 1
        self.life  -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        draw_bonus_item(surf, self.x, self.y, self.kind, self.frame)

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 10, int(self.y) - 22, 20, 22)

# ── Mario (Player) ────────────────────────────────────────────────────────────
class Mario:
    W2 = 14; H2 = 42   # half-width=14, height=42 matching 32×44 sprite

    def __init__(self, cx, by):
        self.cx = float(cx); self.by = float(by)
        self.vx = 0.0; self.vy = 0.0
        self.on_ground = False
        self.climbing  = False
        self.facing    = 1
        self.state     = 'walk'   # walk | jump | climb | dead
        self.frame     = 0
        self.walk_tick = 0
        self.anim_tick = 0
        self.invincible = 0       # frames of invincibility after hit
        self.dead_anim  = 0
        self._ladder = None
        self._step_snd = 0

    def reset(self, cx=None, by=None):
        self.cx = float(cx or MARIO_START_CX)
        self.by = float(by or MARIO_START_BY)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.climbing  = False
        self.facing    = 1
        self.state     = 'walk'
        self.frame     = 0
        self.dead_anim = 0
        self._ladder   = None
        self.invincible = 90

    @property
    def rect(self):
        return pygame.Rect(int(self.cx) - self.W2, int(self.by) - self.H2,
                           self.W2 * 2, self.H2)

    def feet_y(self):
        return self.by

    def head_y(self):
        return self.by - self.H2

    def handle_input(self, keys, platforms, ladders):
        left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up    = keys[pygame.K_UP]    or keys[pygame.K_w]
        down  = keys[pygame.K_DOWN]  or keys[pygame.K_s]
        jump  = keys[pygame.K_SPACE]

        if self.state == 'dead':
            return

        # ── Ladder logic ─────────────────────────────────────────────────────
        on_ladder = self._on_any_ladder(ladders)

        if on_ladder and (up or down) and not self.climbing:
            lad = on_ladder
            if (up and self.by > lad.yt + 4) or (down and self.by < lad.yb):
                self.climbing = True
                self._ladder  = lad
                self.cx = float(lad.cx)
                self.vx = 0.0

        if self.climbing:
            lad = self._ladder
            if lad is None or not lad.mario_can_grab(self.cx, self.by):
                self.climbing = False
            else:
                if up:
                    self.vy = -CLIMB
                    self.state = 'climb'
                    self._step_snd += 1
                    if self._step_snd % 10 == 0:
                        play(SND_CLIMB)
                elif down:
                    self.vy = CLIMB
                    self.state = 'climb'
                    self._step_snd += 1
                    if self._step_snd % 10 == 0:
                        play(SND_CLIMB)
                else:
                    self.vy = 0
                # Jump off ladder
                if jump and self.on_ground:
                    self.climbing = False
                    self._do_jump()
                return  # skip ground movement while climbing

        # ── Horizontal movement ──────────────────────────────────────────────
        if left:
            self.vx = -WALK; self.facing = -1
        elif right:
            self.vx = WALK;  self.facing = 1
        else:
            self.vx = 0.0

        # ── Jump ─────────────────────────────────────────────────────────────
        if (jump or (up and not on_ladder)) and self.on_ground:
            self._do_jump()

    def _do_jump(self):
        self.vy     = JUMP_V
        self.on_ground = False
        self.state  = 'jump'
        play(SND_JUMP)

    def _on_any_ladder(self, ladders):
        for lad in ladders:
            if lad.mario_can_grab(self.cx, self.by):
                return lad
        return None

    def update(self, platforms, ladders):
        if self.state == 'dead':
            self.dead_anim += 1
            return

        if self.invincible > 0:
            self.invincible -= 1

        if not self.climbing:
            self.vy += GRAVITY
        self.cx += self.vx
        self.by += self.vy

        self.cx = max(self.W2 + 2, min(W - self.W2 - 2, self.cx))

        # ── Platform collision ────────────────────────────────────────────────
        self.on_ground = False
        for plat in platforms:
            if (plat.xl <= self.cx <= plat.xr
                    and 0 < self.by - plat.y < 16
                    and self.vy >= 0):
                self.by = plat.y
                self.vy = 0
                self.on_ground = True
                if self.state == 'jump':
                    play(SND_LAND)
                break

        # At top of ladder
        if self.climbing:
            lad = self._ladder
            if lad and self.by <= lad.yt:
                self.by = lad.yt
                self.vy = 0
                self.climbing = False
                self.on_ground = True
            elif lad and self.by >= lad.yb:
                self.by = lad.yb
                self.vy = 0
                self.climbing = False

        # ── Animation state ───────────────────────────────────────────────────
        self.anim_tick += 1
        if self.climbing:
            self.state = 'climb'
            self.frame = self.anim_tick // 8
        elif not self.on_ground:
            self.state = 'jump'
        elif self.vx != 0:
            self.state = 'walk'
            self._step_snd += 1
            if self._step_snd % 12 == 0:
                play(SND_WALK)
            self.frame = self.anim_tick // 8
        else:
            self.state = 'walk'
            self.frame = 0

    def draw(self, surf):
        if self.invincible > 0 and self.state != 'dead':
            if (self.invincible // 4) % 2 == 0:
                return   # blink when invincible
        draw_mario(surf, self.cx, self.by, self.frame, self.facing,
                   self.state, self.dead_anim)

    def kill(self):
        if self.invincible > 0:
            return False
        self.state = 'dead'
        self.vx = 0; self.vy = 0
        play(SND_DIE)
        return True

    def is_dead_anim_done(self):
        return self.state == 'dead' and self.dead_anim > 80

# ── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud(surf, score, high_score, lives, level, bonus_timer):
    rect(surf, (10, 10, 30), 0, 0, W, 38)
    pygame.draw.line(surf, GIRDCOL, (0, 38), (W, 38), 2)

    # Score
    text_shadow(surf, FONT_SM, f"SCORE  {score:06d}", YELLOW, 10, 8)
    # High score
    hs_str = f"BEST {high_score:06d}"
    s = FONT_SM.render(hs_str, True, GOLD)
    surf.blit(s, (W//2 - s.get_width()//2, 10))
    # Level
    text_shadow(surf, FONT_SM, f"LVL {level}", CYAN, W - 90, 8)
    # Lives (small Mario icons, scaled to fit HUD height)
    for i in range(lives):
        lx = W - 135 - i * 20
        draw_mario(surf, lx, 36, 0, 1, 'walk', scale=0.52)

    # Bonus countdown bar
    if bonus_timer > 0:
        bw = int((bonus_timer / 3600) * 200)
        rect(surf, DKGRAY, W//2 + 90, 14, 202, 12, 3)
        rect(surf, GREEN,  W//2 + 91, 15,  bw,  10, 3)
        text_shadow(surf, FONT_XS, "BONUS", YELLOW, W//2 + 95, 13)

# ── Game ──────────────────────────────────────────────────────────────────────
MENU     = 'menu'
PLAYING  = 'playing'
GAMEOVER = 'gameover'
WIN      = 'win'
PAUSED   = 'paused'
LEVELUP  = 'levelup'
INTRO    = 'intro'

class Game:
    def __init__(self):
        self.state      = MENU
        self.score      = 0
        self.high_score = 0
        self.lives      = 3
        self.level      = 1
        self.tick       = 0
        self.state_tick = 0
        self._build_level()
        self._init_entities()

    def _build_level(self):
        self.platforms = [Platform(*d) for d in PLATFORMS]
        self.ladders   = [Ladder(*d)   for d in LADDERS]

    def _init_entities(self):
        self.mario    = Mario(MARIO_START_CX, MARIO_START_BY)
        self.dk       = DonkeyKong(DK_CX, DK_BY)
        self.pauline  = Pauline(PAULINE_CX, PLATFORMS[-1][2])   # top platform y
        self.barrels  = []
        self.flames   = []
        self.bonuses  = []
        self.popups   = []
        self.bonus_timer   = 3600   # 60-second bonus countdown
        self._barrel_q     = []     # queued barrels to spawn
        self._flame_timer  = 0
        self._bonus_spawn  = random.randint(240, 600)
        self._jmp_barrel_reward = {}  # barrel id → already awarded?

    def start_game(self):
        self.score  = 0
        self.lives  = 3
        self.level  = 1
        self.state  = INTRO
        self.state_tick = 0
        self._build_level()
        self._init_entities()

    def _speed_mult(self):
        return 1.0 + 0.12 * (self.level - 1)

    def _spawn_barrel(self):
        sm = self._speed_mult()
        # Barrel spawns just past DK, moving right
        b = Barrel(DK_CX + 30, PLATFORMS[-1][2], +1,
                   self.platforms, sm)
        self.barrels.append(b)

    def _spawn_flame(self):
        sm = self._speed_mult()
        # Flames spawn from an oil drum at the bottom left
        f = Flame(55, PLATFORMS[0][2], self.platforms,
                  self.ladders, sm)
        self.flames.append(f)

    def add_score(self, pts, x=None, y=None, color=YELLOW):
        self.score += pts
        if self.score > self.high_score:
            self.high_score = self.score
        if x is not None:
            self.popups.append(ScorePopup(x, y or 300, pts, color))
        play(SND_SCORE)

    def update(self):
        if self.state == INTRO:
            self._update_intro()
        elif self.state == PLAYING:
            self._update_playing()
        elif self.state == PAUSED:
            pass
        elif self.state in (GAMEOVER, WIN, MENU, LEVELUP):
            self.state_tick += 1

    def _update_intro(self):
        self.state_tick += 1
        if self.state_tick > 120:
            self.state = PLAYING
            self.state_tick = 0

    def _update_playing(self):
        self.tick += 1
        sm = self._speed_mult()

        # Input
        keys = pygame.key.get_pressed()
        self.mario.handle_input(keys, self.platforms, self.ladders)
        self.mario.update(self.platforms, self.ladders)

        # DK
        if self.dk.update(sm, self.level):
            self._spawn_barrel()

        # Barrels
        for b in self.barrels:
            b.update()
            # Jump-over reward
            bid = id(b)
            if (bid not in self._jmp_barrel_reward
                    and not self.mario.climbing
                    and self.mario.vy < 0                        # rising
                    and abs(self.mario.cx - b.x) < 28
                    and self.mario.by < b.y - 4):
                self._jmp_barrel_reward[bid] = True
                self.add_score(100, int(b.x), int(b.y) - 30, CYAN)

        self.barrels = [b for b in self.barrels if b.alive]

        # Flames
        self._flame_timer += 1
        spawn_interval = max(300, 600 - self.level * 40)
        if self._flame_timer >= spawn_interval and len(self.flames) < 4 + self.level:
            self._flame_timer = 0
            self._spawn_flame()
            play(SND_FLAME)
        for f in self.flames:
            f.update(self.mario.cx, self.mario.by)
        self.flames = [f for f in self.flames if f.alive]

        # Bonus timer
        self.bonus_timer = max(0, self.bonus_timer - 1)

        # Pauline
        self.pauline.update()

        # Bonus items
        self._bonus_spawn -= 1
        if self._bonus_spawn <= 0:
            self._bonus_spawn = random.randint(400, 900)
            kind = random.choice(BONUS_KINDS)
            plat = random.choice(self.platforms[:4])
            bx   = random.randint(plat.xl + 20, plat.xr - 20)
            self.bonuses.append(BonusItem(bx, plat.y, kind))
        for bo in self.bonuses:
            bo.update()
        self.bonuses = [bo for bo in self.bonuses if bo.alive]

        # Popups
        for p in self.popups:
            p.update()
        self.popups = [p for p in self.popups if p.alive]

        # ── Collision Detection ───────────────────────────────────────────────
        if self.mario.state != 'dead':
            mario_r = self.mario.rect

            # Barrel hits
            for b in self.barrels:
                if mario_r.colliderect(b.rect):
                    if self.mario.kill():
                        self.lives -= 1

            # Flame hits
            for f in self.flames:
                if mario_r.colliderect(f.rect):
                    if self.mario.kill():
                        self.lives -= 1

            # Bonus pickup
            for bo in self.bonuses:
                if mario_r.colliderect(bo.rect):
                    self.add_score(bo.value, bo.x, bo.y - 10, GOLD)
                    play(SND_BONUS)
                    bo.alive = False

            # Reach Pauline
            if mario_r.colliderect(self.pauline.rect):
                self._win_level()

        # ── Death resolution ──────────────────────────────────────────────────
        if self.mario.is_dead_anim_done():
            if self.lives <= 0:
                self.state = GAMEOVER
                self.state_tick = 0
            else:
                # Respawn
                self.mario.reset()
                self.barrels.clear()
                self.flames.clear()
                self._jmp_barrel_reward.clear()

    def _win_level(self):
        bonus = (self.bonus_timer // 60) * 100
        self.add_score(5000 + bonus, W//2, H//2 - 40, YELLOW)
        play(SND_WIN)
        self.state = LEVELUP
        self.state_tick = 0

    def next_level(self):
        self.level += 1
        self._init_entities()
        self.mario.reset()
        self.state = INTRO
        self.state_tick = 0

    def draw(self, surf):
        draw_background(surf, self.tick)

        # Girders & ladders
        for lad in self.ladders:
            lad.draw(surf)
        for plat in self.platforms:
            plat.draw(surf)

        # Oil drum (bottom left)
        rect(surf, DKGRAY,  28,  PLATFORMS[0][2] - 26, 24, 26, 2)
        rect(surf, GRAY,    30,  PLATFORMS[0][2] - 24, 20, 22, 2)
        rect(surf, ORANGE,  30,  PLATFORMS[0][2] - 10, 20,  8, 2)
        circle(surf, FLMYEL, 38,  PLATFORMS[0][2] - 30, 7)
        circle(surf, FLMORG, 38,  PLATFORMS[0][2] - 30, 4)

        # Entities
        self.pauline.draw(surf)
        self.dk.draw(surf)
        for bo in self.bonuses:
            bo.draw(surf)
        for b in self.barrels:
            b.draw(surf)
        for f in self.flames:
            f.draw(surf)
        self.mario.draw(surf)

        # Popups
        for p in self.popups:
            p.draw(surf)

        # HUD
        draw_hud(surf, self.score, self.high_score, self.lives,
                 self.level, self.bonus_timer)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and self.state == PLAYING:
                self.state = PAUSED
            elif event.key == pygame.K_p and self.state == PAUSED:
                self.state = PLAYING
            elif event.key == pygame.K_ESCAPE:
                if self.state in (PLAYING, PAUSED, GAMEOVER, WIN, LEVELUP):
                    self.state = MENU
                    self.state_tick = 0

# ── Screens ───────────────────────────────────────────────────────────────────
def draw_menu(surf, tick, high_score):
    draw_background(surf, tick)

    # Title box
    rect(surf, (10, 10, 50, 200), W//2 - 220, 60, 440, 120, 12)
    pygame.draw.rect(surf, GIRDCOL, (W//2 - 220, 60, 440, 120), 3, border_radius=12)

    # DONKEY KONG text
    center_text(surf, FONT_XL, "DONKEY", ORANGE,  70)
    center_text(surf, FONT_XL, " KONG ", YELLOW, 112)

    # Animated DK
    dk_x = W//2 + int(math.sin(tick * 0.03) * 30)
    draw_dk(surf, dk_x, 240, tick // 14, throwing=(tick // 30) % 2 == 0)
    # Animated Mario running
    mario_x = 80 + (tick * 2) % (W - 140)
    draw_mario(surf, mario_x, 270, tick // 8, 1, 'walk')

    center_text(surf, FONT_MED, "PRESS  ENTER  TO  START", WHITE, 300)
    center_text(surf, FONT_SM,  "← → / A D   Move        ↑ / Spc   Jump",
                LTGRAY, 345)
    center_text(surf, FONT_SM,  "↑ ↓ on ladder  Climb       P   Pause",
                LTGRAY, 367)

    if high_score > 0:
        center_text(surf, FONT_MED, f"BEST SCORE: {high_score:06d}", GOLD, 400)

    center_text(surf, FONT_XS, "Python / Pygame  —  Classic Arcade Recreation",
                GRAY, H - 24)

def draw_intro(surf, tick):
    """Brief intro animation: DK carries Pauline up."""
    draw_background(surf, tick)
    prog = min(tick / 80, 1.0)
    dk_y = int(80 + (H // 2 - 80) * (1 - prog))
    draw_dk(surf, W // 2, dk_y, tick // 10)
    draw_pauline(surf, W // 2 + 40, dk_y, tick // 12)
    center_text(surf, FONT_BIG, "HOW HIGH CAN YOU GET?", YELLOW, H//2 + 60)

def draw_game_over(surf, tick, score):
    draw_background(surf, tick)
    center_text(surf, FONT_XL, "GAME  OVER", RED, H//2 - 60)
    center_text(surf, FONT_MED, f"FINAL SCORE:  {score:06d}", WHITE, H//2 + 10)
    if tick > 90:
        center_text(surf, FONT_SM, "PRESS ENTER  to play again", LTGRAY, H//2 + 60)
        center_text(surf, FONT_SM, "ESC to menu", GRAY, H//2 + 90)

def draw_win(surf, tick, score):
    draw_background(surf, tick)
    center_text(surf, FONT_XL, "YOU WIN!", YELLOW, H//2 - 80)
    center_text(surf, FONT_MED, "Pauline is rescued!", PINK,  H//2 - 20)
    center_text(surf, FONT_MED, f"SCORE:  {score:06d}", WHITE, H//2 + 30)
    if tick > 90:
        center_text(surf, FONT_SM, "PRESS ENTER to play again", LTGRAY, H//2 + 90)

def draw_level_up(surf, tick, level, score):
    draw_background(surf, tick)
    center_text(surf, FONT_XL, f"LEVEL {level}", CYAN, H//2 - 80)
    center_text(surf, FONT_MED, "STAGE CLEAR!", YELLOW, H//2 - 20)
    center_text(surf, FONT_MED, f"SCORE:  {score:06d}", WHITE, H//2 + 30)
    if tick > 90:
        center_text(surf, FONT_SM, "PRESS ENTER for next level", LTGRAY, H//2 + 90)

def draw_paused(surf):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    surf.blit(overlay, (0, 0))
    center_text(surf, FONT_XL, "PAUSED", WHITE, H//2 - 40)
    center_text(surf, FONT_SM, "P — resume   ESC — menu", LTGRAY, H//2 + 30)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    game = Game()
    menu_tick = 0

    while True:
        dt = clock.tick(FPS)

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if game.state == MENU:
                        game.start_game()
                    elif game.state == GAMEOVER:
                        game.start_game()
                    elif game.state == WIN:
                        game.start_game()
                    elif game.state == LEVELUP:
                        game.next_level()

                game.handle_event(event)

        menu_tick += 1

        # ── Update ────────────────────────────────────────────────────────────
        game.update()

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(BLACK)

        if game.state == MENU:
            draw_menu(screen, menu_tick, game.high_score)

        elif game.state == INTRO:
            game.draw(screen)
            draw_intro(screen, game.state_tick)

        elif game.state in (PLAYING, PAUSED):
            game.draw(screen)
            if game.state == PAUSED:
                draw_paused(screen)

        elif game.state == GAMEOVER:
            game.draw(screen)
            draw_game_over(screen, game.state_tick, game.score)

        elif game.state == LEVELUP:
            game.draw(screen)
            draw_level_up(screen, game.state_tick, game.level, game.score)

        elif game.state == WIN:
            draw_win(screen, game.state_tick, game.score)

        pygame.display.flip()

if __name__ == "__main__":
    main()
