from asyncUi.window import eventHandler, Window
from asyncUi.display import drawableRenderer, Color
from asyncUi.graphics import ConcentricGroup, Circle
from asyncUi import events
from typing import Never
import pygame

window = Window(pygame.display.set_mode((250, 250), pygame.RESIZABLE), "test")

@eventHandler
def exiter(event: events.Quit) -> Never:
    exit()
exiter.register()

RED = Color(255, 0, 0)
app = ConcentricGroup((0, 0), [
    Circle(..., RED, 100, 5),
    Circle(..., RED, 90, 5),
    Circle(..., RED, 80, 5),
    Circle(..., RED, 70, 5),
    Circle(..., RED, 60, 5),
])

window.startRenderer(10, drawableRenderer(app))
window.run()