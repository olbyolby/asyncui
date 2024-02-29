from asyncui.window import Window, event_handler
from asyncui.events import Quit, MouseButtonUp
from asyncui.resources.fonts import fonts
from asyncui.graphics import Box, Button, Text
from asyncui.display import Color, drawable_renderer
import pygame
pygame.init()

window = Window(pygame.display.set_mode((300, 200)), (300, 200), "Example window")
arial = fonts.load_system_font("arial")

@event_handler
def closer(e: Quit) -> None:
    exit()
closer.register()

def print_click() -> None:
    print("You clicked the box!")

box = Button(..., Text((0,0), arial, 32, Color.WHITE, "Hello world!"), print_click)

window.start_renderer(30, drawable_renderer(box.__enter__()))
window.run()