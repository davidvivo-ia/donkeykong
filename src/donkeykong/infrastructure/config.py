"""Configuración del juego con validación Pydantic v2."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DisplayConfig(BaseModel):
    """Configuración de pantalla."""

    width: int = Field(default=800, gt=0)
    height: int = Field(default=650, gt=0)
    fps: int = Field(default=60, gt=0, le=240)
    title: str = Field(default="DONKEY KONG")


class GameConfig(BaseModel):
    """Configuración global del juego.

    Args:
        display: parámetros de pantalla.
        starting_lives: vidas al empezar.
        demo_seed: semilla usada en modo --demo.
        enable_sound: si False desactiva el audio completamente.
    """

    display: DisplayConfig = Field(default_factory=DisplayConfig)
    starting_lives: int = Field(default=3, ge=1, le=9)
    demo_seed: int = Field(default=42)
    enable_sound: bool = Field(default=True)

    @staticmethod
    def default() -> GameConfig:
        """Retorna configuración por defecto."""
        return GameConfig()
