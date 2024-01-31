from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, EventHandler
from asyncUi.graphics import Box, Text, Clickable, Hoverable, Focusable
from asyncUi.display import Color
from asyncUi.resources import fonts
from asyncUi import events
import pygame
pygame.init()

window = Window(pygame.display.set_mode((500, 250), pygame.RESIZABLE))

@EventHandler
def exiter(event: events.Quit) -> Never:
    exit()
exiter.register()

box = Box((250-50, 125-50), (50, 50), Color(255, 255, 0))
clicker = Clickable(box.body, lambda e: print("You clicked it!")).__enter__()
hovererer = Hoverable(box.body, lambda e: print("started hover"), lambda e: print("end hover")).__enter__()

async def renderer() -> Never:
    while True:
        start = asyncio.get_event_loop().time()
        box.draw(window.window, window.window.get_size()[0]/window.orginalSize[0])
        text.draw(window.window, window.window.get_size()[0]/window.orginalSize[0])
        otherBox.draw(window.window, window.window.get_size()[0]/window.orginalSize[0])
        pygame.display.flip()
        end = asyncio.get_event_loop().time()
        await asyncio.sleep(1/30 - end - start)

asyncio.create_task(renderer())

airal = fonts.fontManager.loadSystemFont('arial')
text = Text((0,0), airal, 50, Color(255, 255, 255), "Hello")


@EventHandler
def keyPrinter(event: events.KeyDown) -> None:
    print(event.unicode)

otherBox = Box((100-50, 25), (50, 25), Color(255, 255, 0))
focuser = Focusable(otherBox.body, keyPrinter.register, keyPrinter.unregister).__enter__()

window.run()