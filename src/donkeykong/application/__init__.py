"""Capa de aplicación — casos de uso que orquestan el dominio.

Esta capa coordina el bucle de juego, la máquina de estados (MENU →
INTRO → PLAYING → PAUSED / LEVELUP / GAMEOVER / WIN) y expone la
interfaz de línea de comandos via typer.

No debe importar pygame directamente. Toda interacción con el display
se delega a la capa de presentación mediante callbacks o retornando
objetos de datos neutros.

Modules:
    game_engine: Coordinador principal del loop de juego.
    input: Traducción de eventos de teclado a comandos del dominio.
    demo_ai: IA de demostración para el modo --demo.
    engine_output: Tipos de datos de salida del motor hacia el renderer.
"""
