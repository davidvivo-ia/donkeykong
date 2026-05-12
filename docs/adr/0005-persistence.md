# ADR 0005 — Persistencia: JSON en XDG con pydantic v2

**Estado:** Aceptado  
**Fecha:** 2026-05-12  
**Autores:** davidvivo-ia

---

## Contexto

El juego necesita persistir exactamente un dato entre sesiones: la puntuación máxima (`high_score`). En el original, este dato se pierde al cerrar la ventana porque vive únicamente en el atributo `Game.high_score`.

En v1.1 se añadirá un leaderboard con las 10 mejores puntuaciones con fecha y nombre de jugador, lo que amplía el modelo de persistencia pero no cambia la estrategia de almacenamiento.

Se evaluaron tres opciones:

1. **JSON en `~/.local/share/donkeykong/`** (XDG Base Directory Specification).
2. **SQLite** con la biblioteca `sqlite3` de stdlib.
3. **Fichero de texto plano** (un número por línea).

---

## Decisión

Usamos **JSON en el directorio XDG Data Home**, con **pydantic v2** para serialización y validación.

```
~/.local/share/donkeykong/
└── scores.json
```

```json
{
  "version": 1,
  "high_score": 42500,
  "sessions": []
}
```

---

## Razonamiento

### Por qué XDG Base Directory

La XDG Base Directory Specification (freedesktop.org) define rutas estándar para datos de aplicaciones en Linux y macOS:

- `$XDG_DATA_HOME` (por defecto `~/.local/share/`) — datos persistentes del usuario.
- `$XDG_CONFIG_HOME` (por defecto `~/.config/`) — configuración.

Usar estas rutas garantiza que:

1. Los datos del juego no polucionen el directorio HOME.
2. Las herramientas de backup estándar (rsync de `~/.local/share/`) incluyan los datos automáticamente.
3. El path es portable a macOS (`~/.local/share/` funciona igual con el fallback XDG).

En Windows se usaría `%APPDATA%\donkeykong\` con `platformdirs` como abstracción opcional.

```python
# infrastructure/settings.py
import os
from pathlib import Path

def xdg_data_dir() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    d = base / "donkeykong"
    d.mkdir(parents=True, exist_ok=True)
    return d
```

### Por qué JSON y no SQLite

SQLite es adecuado cuando hay múltiples tablas, queries complejas o acceso concurrente. Para un único documento con un campo entero, el overhead de SQLite (driver, esquema, conexión) no está justificado.

JSON es:
- Legible y editable por el usuario con cualquier editor de texto.
- Nativo en Python (stdlib `json`).
- Suficientemente rápido para un write-once-per-game-session.

### Por qué pydantic v2 para serialización

pydantic v2 ya es una dependencia del proyecto (para `Settings`). Usarlo también para el modelo de persistencia no añade dependencias nuevas y aporta:

- **Validación en carga:** si el fichero `scores.json` está corrupto o tiene un esquema incorrecto (edición manual, cambio de versión), pydantic lanza `ValidationError` con un mensaje claro en vez de un `KeyError` críptico.
- **Serialización tipada:** `model.model_dump_json()` garantiza que los tipos Python se serialicen correctamente (enteros como enteros, no como strings).
- **Migración de versión:** el campo `version` permite detectar esquemas antiguos y migrarlos.

```python
# infrastructure/persistence.py
from pydantic import BaseModel, Field
from pathlib import Path

class ScoreRecord(BaseModel):
    version: int = Field(default=1, ge=1)
    high_score: int = Field(default=0, ge=0)

class ScoreRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> ScoreRecord:
        if not self._path.exists():
            return ScoreRecord()
        try:
            return ScoreRecord.model_validate_json(self._path.read_text())
        except Exception:
            return ScoreRecord()   # fichero corrupto → empezar de cero

    def save(self, record: ScoreRecord) -> None:
        self._path.write_text(record.model_dump_json(indent=2))
```

### Por qué no fichero de texto plano

Un fichero con un número entero sería más simple, pero:
- No es extensible: añadir el nombre del jugador o la fecha requiere cambiar el formato y romper la compatibilidad.
- No tiene validación: un `int("abc")` de un fichero corrupto provoca una excepción sin mensaje útil.
- No documenta el esquema a simple vista.

---

## Consecuencias

- **Positivas:** datos persistentes entre sesiones, validación robusta con pydantic, extensible a leaderboard en v1.1, legible por el usuario, path estándar en Linux/macOS.
- **Negativas:** requiere permisos de escritura en `~/.local/share/`. En entornos de sandboxing estricto (Flatpak, snap) puede ser necesario solicitar el permiso explícitamente.
- **Neutrales:** en modo `--demo` o tests, la ruta puede sobreescribirse con `XDG_DATA_HOME=/tmp/test-dk` sin modificar el código.
