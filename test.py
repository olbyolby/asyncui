from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, eventHandler
from asyncUi.graphics import Line, Polygon, Circle, Button, Group, Box, Text, Clickable, Hoverable, Focusable, InputBoxDisplay, InputBox, ToolBar, centered, VirticalMenu, renderAll
from asyncUi.display import Size, stackEnabler, AutomaticStack, Drawable, Color, drawableRenderer, Point, Color
from asyncUi.resources import fonts
from asyncUi.util import MutableContextManager, Flag, Placeholder
from asyncUi import events
from math import sin, cos, radians
from contextlib import ExitStack
from dataclasses import dataclass, InitVar
import pygame
import datetime
import string
pygame.init()

window = Window(pygame.display.set_mode((250, 250), pygame.RESIZABLE), "test")

@eventHandler
def exiter(event: events.Quit) -> Never:
    exit()
exiter.register()

SIZE_X = 250
SIZE_Y = 250
CLOCK_RADIUS = 100
CENTER = (250//2, 250//2)
arial = fonts.fontManager.loadSystemFont('arial')

BLACK = Color(0, 0, 0)
RED = Color(255, 0, 0)
WHITE = Color(255, 255, 255)

def clockPosition(angle: float, length: int) -> Point:
    angle = radians(180-angle)
    return int(sin(angle) * length), int(cos(angle) * length)

class Clock(Drawable, AutomaticStack):
    size = Placeholder[Size]()
    def __init__(self, position: Point, size: Size):

        self.position = position
        self.size = size
        center = (position[0] + size[0]//2, position[1] + size[1]//2)

        self.background = Box(position, size, RED)
        self.clock_background = Circle((center[0]-CLOCK_RADIUS, center[1]-CLOCK_RADIUS), WHITE, CLOCK_RADIUS)

        axel_radius = CLOCK_RADIUS//19
        self.center_axel = Circle((center[0] - axel_radius, center[1] - axel_radius), BLACK, axel_radius)


        self.clock_border = Circle((center[0]-CLOCK_RADIUS, center[1]-CLOCK_RADIUS), BLACK, CLOCK_RADIUS, 4)
        self.minute_dashes = Group(center, list(self._generateDashes(60, CLOCK_RADIUS*.90, CLOCK_RADIUS*.08)))
        self.hour_dashes = Group(center, list(self._generateDashes(12, CLOCK_RADIUS*.80, CLOCK_RADIUS*.19)))

        self.second_hand = Line((center[0], center[1]), RED, 4, (0, 0), clockPosition(0, CLOCK_RADIUS))
        self.minute_hand = Line(center, BLACK, 4, (0, 0), clockPosition(0, int(CLOCK_RADIUS)))
        self.hour_hand = Line(center, BLACK, 4, (0, 0), clockPosition(0, int(CLOCK_RADIUS*.50)))

        
    def _generateDashes(self, dashNumber: int, distance: float, length: float) -> Iterable[Line]:
        for i in range(dashNumber):
            yield Line(self.position, BLACK, 4, clockPosition(360/dashNumber*i, int(distance)), clockPosition(360/dashNumber*i, int(distance + length)))

    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        self._time_update_handler = asyncio.ensure_future(self._timeUpdater())
        stack.callback(self._time_update_handler.cancel)

    async def _timeUpdater(self) -> Never:
        while True:
            now = datetime.datetime.now()

            self.second_hand = self.second_hand.changePoint(..., clockPosition((360/60)*now.second, CLOCK_RADIUS))
            self.minute_hand = self.minute_hand.changePoint(..., clockPosition((360/60)*now.minute + (360/60/60)*now.second, int(CLOCK_RADIUS*.975)))
            self.hour_hand = self.hour_hand.changePoint(...,  clockPosition((360/12*now.hour) + (360/12/60) * now.minute + (360/12/60/60) * now.second, int(CLOCK_RADIUS * .75)))

            await asyncio.sleep(1)
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.background.draw(window, scale)
        self.clock_background.draw(window, scale)
        self.minute_dashes.draw(window, scale)
        self.hour_dashes.draw(window, scale)


        self.second_hand.draw(window, scale)
        self.minute_hand.draw(window, scale)
        self.hour_hand.draw(window, scale)

        self.center_axel.draw(window, scale)
        self.clock_border.draw(window, scale)
        

    def reposition(self, position: Point | EllipsisType) -> Self:
        raise NotImplementedError("reposition")
window.startRenderer(30, drawableRenderer(Clock((0,0), (250, 250)).__enter__()))

window.run()