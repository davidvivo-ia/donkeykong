"""Síntesis procedural de sonidos y gestión del mixer pygame.

Genera tonos PC-speaker sintéticos sin archivos de audio externos.
[LICENCIA CREATIVA] Todos los sonidos son originales, inspirados en
la estética arcade de los años 80.
"""

from __future__ import annotations

import array
import math

import pygame

from donkeykong.domain.events import SoundEvent


def _gen_tone(
    freq: float,
    duration: float,
    volume: float = 0.32,
    shape: str = "square",
    decay: bool = True,
    attack: float = 0.01,
) -> pygame.mixer.Sound:
    """Genera un tono sintético como pygame.mixer.Sound.

    Args:
        freq: frecuencia en Hz.
        duration: duración en segundos.
        volume: amplitud [0, 1].
        shape: forma de onda ('square', 'sine', 'saw', 'tri').
        decay: si True aplica envelope de decaimiento exponencial.
        attack: duración del ataque en segundos.

    Returns:
        pygame.mixer.Sound listo para reproducir.
    """
    sample_rate = 22050
    n = int(sample_rate * duration)
    buf: array.array[int] = array.array("h", [0] * n)
    for i in range(n):
        t = i / sample_rate
        phase = 2.0 * math.pi * freq * t
        match shape:
            case "square":
                v = 1.0 if math.sin(phase) > 0 else -1.0
            case "saw":
                v = 2.0 * (freq * t % 1.0) - 1.0
            case "tri":
                v = 2.0 * abs(2.0 * (freq * t % 1.0) - 1.0) - 1.0
            case _:
                v = math.sin(phase)
        att = min(i / max(1, int(sample_rate * attack)), 1.0)
        dec = (1.0 - i / n) ** 0.6 if decay else 1.0
        buf[i] = int(v * att * dec * volume * 32767)
    return pygame.mixer.Sound(buffer=buf)


def _gen_slide(
    freq_start: float,
    freq_end: float,
    duration: float,
    volume: float = 0.28,
    shape: str = "square",
) -> pygame.mixer.Sound:
    """Genera un glissando (deslizamiento de frecuencia).

    Args:
        freq_start: frecuencia inicial en Hz.
        freq_end: frecuencia final en Hz.
        duration: duración en segundos.
        volume: amplitud.
        shape: forma de onda.

    Returns:
        pygame.mixer.Sound.
    """
    sample_rate = 22050
    n = int(sample_rate * duration)
    buf: array.array[int] = array.array("h", [0] * n)
    phase = 0.0
    for i in range(n):
        freq = freq_start + (freq_end - freq_start) * (i / n)
        phase += 2.0 * math.pi * freq / sample_rate
        v = 1.0 if math.sin(phase) > 0 else -1.0
        if shape != "square":
            v = math.sin(phase)
        env = (1.0 - i / n) ** 0.5
        buf[i] = int(v * env * volume * 32767)
    return pygame.mixer.Sound(buffer=buf)


def _gen_chord(
    freqs: list[float],
    duration: float,
    volume: float = 0.22,
) -> pygame.mixer.Sound:
    """Genera un acorde de sinusoides.

    Args:
        freqs: lista de frecuencias.
        duration: duración en segundos.
        volume: amplitud total.

    Returns:
        pygame.mixer.Sound.
    """
    sample_rate = 22050
    n = int(sample_rate * duration)
    buf: array.array[int] = array.array("h", [0] * n)
    for i in range(n):
        t = i / sample_rate
        v = sum(math.sin(2.0 * math.pi * f * t) for f in freqs) / len(freqs)
        env = (1.0 - i / n) ** 0.4
        buf[i] = int(v * env * volume * 32767)
    return pygame.mixer.Sound(buffer=buf)


class SoundManager:
    """Gestor de sonidos procedurales.

    Pre-genera todos los sonidos al inicializarse para evitar latencia
    en tiempo de ejecución.
    """

    def __init__(self) -> None:
        self._sounds: dict[SoundEvent, pygame.mixer.Sound] = {}
        self._available = False
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._build_sounds()
            self._available = True
        except pygame.error:
            pass

    def _build_sounds(self) -> None:
        self._sounds = {
            SoundEvent.JUMP: _gen_slide(400, 700, 0.16, volume=0.30),
            SoundEvent.LAND: _gen_tone(120, 0.09, shape="square"),
            SoundEvent.WALK: _gen_tone(130, 0.05, volume=0.12, shape="square", decay=False),
            SoundEvent.CLIMB: _gen_tone(200, 0.07, volume=0.15, shape="square", decay=False),
            SoundEvent.BARREL_LAND: _gen_tone(140, 0.13, shape="square"),
            SoundEvent.DIE: _gen_slide(400, 80, 0.55, volume=0.35, shape="saw"),
            SoundEvent.SCORE: _gen_tone(780, 0.09, shape="sine"),
            SoundEvent.WIN: _gen_chord([523.0, 659.0, 784.0, 1047.0], 1.0, volume=0.28),
            SoundEvent.BONUS: _gen_chord([660.0, 880.0, 1100.0], 0.5, volume=0.25),
            SoundEvent.THROW: _gen_tone(240, 0.18, shape="square"),
            SoundEvent.FLAME_SPAWN: _gen_tone(260, 0.18, shape="saw"),
            SoundEvent.LEVEL_UP: _gen_chord([440.0, 550.0, 660.0, 880.0], 1.2, volume=0.30),
            SoundEvent.BARREL_JUMP: _gen_tone(760, 0.09, shape="sine"),
        }

    def play(self, event: SoundEvent) -> None:
        """Reproduce el sonido asociado al evento.

        Args:
            event: evento de sonido a reproducir.
        """
        if not self._available:
            return
        snd = self._sounds.get(event)
        if snd:
            try:
                snd.play()
            except pygame.error:
                pass

    def play_all(self, events: tuple[SoundEvent, ...]) -> None:
        """Reproduce todos los sonidos de una lista de eventos.

        Args:
            events: eventos de sonido del frame actual.
        """
        for ev in events:
            self.play(ev)
