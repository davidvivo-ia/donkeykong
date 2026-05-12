"""Capa de presentación — renderer pygame-ce, sprites procedurales y HUD.

Toda interacción con pygame reside en esta capa. Traduce el estado del
dominio (structs inmutables) en píxeles en pantalla y eventos de teclado
en comandos para la capa de aplicación.

Modules:
    game_loop: Loop principal de pygame a 60 FPS.
    renderer: Dibujo de fondo, plataformas, escaleras, entidades y HUD.
    sprites: Funciones de dibujo procedural para cada entidad del juego.
    palette: Constantes de color RGB del sistema de diseño.
    input_handler: Traducción de eventos pygame.KEYDOWN a InputCommand.

Note:
    Esta capa es la única que puede hacer ``import pygame``. Las otras
    capas (domain, application, infrastructure/sound excepto) deben
    permanecer independientes de pygame para permitir tests sin display.
"""
