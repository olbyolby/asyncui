from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, EventHandler
from asyncUi.graphics import SimpleButton, Group, Box, Text, Clickable, Hoverable, Focusable, InputBoxDisplay, InputBox, ToolBar, centered, VirticalMenu
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

bar = ToolBar((0,0), [
    SimpleButton(..., Text(..., arial, 16*2, Color(255, 255, 255), "Tool 1"), Box(..., (100, 50), Color(255, 0, 0)), lambda: print("clicked")),
    Text(..., arial, 16*2, Color(255, 255, 255), "Tool 2"),
    Text(..., arial, 16*2, Color(255, 255, 255), "Tool 3"),
    Text(..., arial, 16*2, Color(255, 255, 255), "Tool 4"),
])

box = Box((50, 50), (100, 50), Color(255, 0, 0))
text = centered(box, Text(..., arial, 16, Color(255, 255, 255), "hello"))

menu = VirticalMenu((100,50), [
    Text(..., arial, 16*2, Color(255, 255, 255), "Tool 1"),
    Text(..., arial, 16*2, Color(255, 255, 255), "Tool 2"),
    Text(..., arial, 16*2, Color(255, 255, 255), "Tool 3"),
    Text(..., arial, 16*2, Color(255, 255, 255), "Tool 4"),
])

objects = Group((0,0), [box, text, bar, menu]).__enter__()

window.startRenderer(30, drawableRenderer(objects))


window.run()