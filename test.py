from asyncUi.window import eventHandler, Window
from asyncUi.display import drawableRenderer, Color
from asyncUi.graphics import Circle, Text, Group
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


#window.startRenderer(10, drawableRenderer(app))
window.run()