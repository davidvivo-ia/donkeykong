# ADR 0004 — Síntesis de sonido: PCM procedural vs assets de audio

**Estado:** Aceptado  
**Fecha:** 2026-05-12  
**Autores:** davidvivo-ia

---

## Contexto

El juego necesita 12 efectos de sonido:

| ID | Evento | Descripción perceptiva |
|---|---|---|
| `SND_JUMP` | Mario salta | Glissando ascendente 400→700 Hz |
| `SND_LAND` | Mario aterriza | Golpe sordo 120 Hz |
| `SND_WALK` | Paso de Mario | Click rítmico 130 Hz |
| `SND_CLIMB` | Mario escala | Tono suave 200 Hz |
| `SND_BARREL` | Barril toca plataforma | Impacto grave 140 Hz |
| `SND_DIE` | Mario muere | Glissando descendente 400→80 Hz (saw) |
| `SND_SCORE` | Pickup de puntos | Tono agudo 780 Hz (sine) |
| `SND_WIN` | Victoria de nivel | Acorde mayor C5-E5-G5-C6 |
| `SND_THROW` | DK lanza barril | Tono medio 240 Hz |
| `SND_FLAME` | Llama spawnea | Tono saw 260 Hz |
| `SND_BONUS` | Recogida de bonus | Acorde 660-880-1100 Hz |
| `SND_LVLUP` | Nivel completado | Acorde A4-C#5-E5-A5 |

Se evaluaron dos enfoques:

1. **Assets de audio:** ficheros OGG/WAV incluidos en el repositorio.
2. **Síntesis PCM procedural:** generación de buffers en memoria en el arranque.

---

## Decisión

Usamos **síntesis PCM procedural** con las tres primitivas `_tone()`, `_chord()` y `_slide()` del código original, refactorizadas en `infrastructure/sound.py`.

---

## Razonamiento

### Cero dependencias de assets

Con síntesis procedural, el repositorio no contiene ningún fichero de audio. Esto elimina:

- Problemas de licencia de los efectos de sonido (los originales de Nintendo son propietarios).
- El tamaño del repositorio (12 ficheros OGG de calidad arcade pesan entre 5 y 50 KB cada uno, total ~300 KB; irrelevante, pero evitable).
- La posibilidad de que un fichero de audio esté corrupto o ausente en producción.

### Reproducibilidad total

El sonido se genera con parámetros numéricos fijos. La función `_tone(freq=400, dur=0.16, shape='square')` produce siempre el mismo buffer en cualquier sistema con Python. Un asset OGG puede sonar diferente según el codec del sistema operativo.

### Estética retro PC-speaker

Las ondas cuadradas y dientes de sierra sintetizadas en punto flotante y cuantizadas a int16 suenan deliberadamente como el altavoz interno de PC (PC Speaker) de los años 80. Esta estética es coherente con la dirección artística del proyecto ("píxeles grandes, luz fosforescente"). Un OGG con samples de alta calidad sonaría fuera de lugar.

### Implementación encapsulada

```python
# infrastructure/sound.py

import array
import math

import pygame

def _tone(freq: float, dur: float, vol: float = 0.32,
          shape: str = "square", decay: bool = True,
          attack: float = 0.01) -> pygame.mixer.Sound:
    """Genera un tono monoaural PCM int16."""
    sr = 22050
    n = int(sr * dur)
    buf: array.array[int] = array.array("h", [0] * n)
    for i in range(n):
        t = i / sr
        ph = 2 * math.pi * freq * t
        match shape:
            case "square": v = 1.0 if math.sin(ph) > 0 else -1.0
            case "saw":    v = 2 * (freq * t % 1) - 1
            case "tri":    v = 2 * abs(2 * (freq * t % 1) - 1) - 1
            case _:        v = math.sin(ph)
        att = min(i / max(1, int(sr * attack)), 1.0)
        dec = (1 - i / n) ** 0.6 if decay else 1.0
        buf[i] = int(v * att * dec * vol * 32767)
    return pygame.mixer.Sound(buffer=buf)
```

La función es pura excepto por la llamada final a `pygame.mixer.Sound`. En tests, puede mockearse `pygame.mixer.Sound` para verificar que el buffer tiene la longitud correcta sin inicializar el mixer.

### Por qué no usar un SoundFont / MIDI

Los SoundFonts requieren `fluidsynth` u otra biblioteca externa. MIDI requiere un sintetizador del SO. La síntesis PCM directa con `array.array` + `pygame.mixer.Sound` solo depende de stdlib y pygame.

---

## Consecuencias

- **Positivas:** cero assets externos, estética retro coherente, reproducible en cualquier SO, testeable con mocks.
- **Negativas:** el bucle de generación en Python puro es lento para duraciones largas (>2 s). Para `SND_LVLUP` (1.2 s) el precalculo tarda ~120 ms en CPython 3.13. Este costo se paga una sola vez al arrancar, no en el loop de juego.
- **Neutrales:** si en v1.1 se añade música de fondo, se recomienda un OGG pre-renderizado con `pygame.mixer.music`, sin afectar a esta decisión sobre los efectos de sonido.
