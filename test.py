from asyncUi.window import eventHandler, Window
from asyncUi.display import drawableRenderer, Color
from asyncUi.graphics import ConcentricGroup, Circle, Text, Group
from asyncUi.resources import fonts
from asyncUi import events
from typing import Never
import pygame
pygame.init()

window = Window(pygame.display.set_mode((250, 250), pygame.RESIZABLE), "test")

@eventHandler
def exiter(event: events.Quit) -> Never:
    exit()
exiter.register()

CIRCLE_COUNT = 100
RED = Color(255, 0, 0)
arial = fonts.fontManager.loadSystemFont("arial")
circles = ConcentricGroup((0, 0), [Circle(..., Color((i*(255//CIRCLE_COUNT)) % 255, 0, 0), 250//2-i*(250//CIRCLE_COUNT//2), 10) for i in range(0, CIRCLE_COUNT)])
widgets = Text((0, 0), arial, 16, Color(255, 255, 255), f"{len(circles._widgets)}")
app = Group((0, 0), [circles, widgets])

window.startRenderer(10, drawableRenderer(app))
window.run()