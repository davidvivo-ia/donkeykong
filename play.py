"""Lanzador directo — ejecuta con: python play.py

No requiere uv ni instalación previa. Instala las dependencias
automáticamente si no están disponibles.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

_DEPS_MAP = {
    "pygame-ce": "pygame",
    "pydantic": "pydantic",
    "typer": "typer",
    "rich": "rich",
    "structlog": "structlog",
}

sys.path.insert(0, str(Path(__file__).parent / "src"))


def _ensure_deps() -> None:
    missing = [
        pkg for pkg, mod in _DEPS_MAP.items()
        if importlib.util.find_spec(mod) is None
    ]
    if missing:
        print(f"Instalando dependencias: {', '.join(missing)} ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", *missing]
        )


if __name__ == "__main__":
    _ensure_deps()
    from donkeykong.__main__ import app

    app(standalone_mode=True)
