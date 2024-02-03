from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, EventHandler
from asyncUi.graphics import Box, Text, Clickable, Hoverable, Focusable, InputBoxDisplay, InputBox
from asyncUi.display import Color
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
inputter = InputBox(InputBoxDisplay((0, 0), Text(..., arial, 16, Color(255, 255, 255), "Hello world!"), Box(..., (100, 25), Color(255, 0, 0)), 2), lambda text: print('you entered ', text)).__enter__()
async def renderer() -> Never:
    while True:
        start = asyncio.get_event_loop().time()
        inputter.draw(window.window, window.scaleFactor)
        pygame.display.flip()
        end = asyncio.get_event_loop().time()
        await asyncio.sleep(1/30 - end - start)

asyncio.create_task(renderer())




@EventHandler
def keyPrinter(event: events.KeyDown) -> None:
    print(event.unicode)



window.run()