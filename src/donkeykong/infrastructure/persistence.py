"""Persistencia de puntuación máxima usando XDG Base Directory.

Guarda el récord en ~/.local/share/donkeykong/highscore.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog
from pydantic import BaseModel, Field

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

_APP_NAME = "donkeykong"


def _data_dir() -> Path:
    """Retorna el directorio de datos XDG para la aplicación."""
    xdg = Path.home() / ".local" / "share" / _APP_NAME
    xdg.mkdir(parents=True, exist_ok=True)
    return xdg


class HighScoreRecord(BaseModel):
    """Modelo pydantic para la persistencia del récord.

    Args:
        score: puntuación más alta registrada.
        player: nombre del jugador (por defecto "PLAYER").
    """

    score: int = Field(default=0, ge=0)
    player: str = Field(default="PLAYER", max_length=12)


class HighScoreRepository:
    """Repositorio de récord con persistencia JSON.

    Args:
        data_dir: directorio donde guardar el fichero (inyectable para tests).
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._path = (data_dir or _data_dir()) / "highscore.json"

    def load(self) -> int:
        """Carga el récord guardado.

        Returns:
            Puntuación máxima, o 0 si no existe fichero.
        """
        if not self._path.exists():
            return 0
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            record = HighScoreRecord.model_validate(data)
            logger.debug("highscore_loaded", score=record.score, path=str(self._path))
            return record.score
        except Exception:
            logger.warning("highscore_load_failed", path=str(self._path))
            return 0

    def save(self, score: int, player: str = "PLAYER") -> None:
        """Guarda el récord si supera el actual.

        Args:
            score: puntuación a guardar.
            player: nombre del jugador.
        """
        current = self.load()
        if score <= current:
            return
        record = HighScoreRecord(score=score, player=player)
        try:
            self._path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
            logger.info("highscore_saved", score=score, path=str(self._path))
        except OSError:
            logger.warning("highscore_save_failed", path=str(self._path))
