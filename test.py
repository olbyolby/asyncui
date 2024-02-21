from asyncUi.window import eventHandler, Window
from asyncUi.display import drawableRenderer, Color
from asyncUi.graphics import Circle, Text, Group, CollapseableMenu
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
arial = fonts.fontManager.loadSystemFont('arial')

app = CollapseableMenu((0, 0), Text(..., arial, 16, Color.WHITE, "Options"), [
    Text(..., arial, 16, Color.WHITE, "Option 1"),
    Text(..., arial, 16, Color.WHITE, "Option 2"),
    Text(..., arial, 16, Color.WHITE, "Option 3"),
], False)
window.startRenderer(10, drawableRenderer(app.__enter__()))
window.run()