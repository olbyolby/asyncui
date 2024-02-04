from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, EventHandler
from asyncUi.graphics import Box, Text, Clickable, Hoverable, Focusable, InputBoxDisplay, InputBox
from asyncUi.display import Color, drawableRenderer, Point, Color
from asyncUi.resources import fonts
from asyncUi import events
import pygame
pygame.init()

window = Window(pygame.display.set_mode((500, 250), pygame.RESIZABLE), "test")

@EventHandler
def exiter(event: events.Quit) -> Never:
    exit()
exiter.register()

arial = fonts.fontManager.loadSystemFont('arial')

def renderer(window: Window) -> None:
    pass



window.startRenderer(30, renderer)


window.run()