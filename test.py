from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, eventHandler
from asyncUi.graphics import Line, Polygon, Circle, SimpleButton, Group, Box, Text, Clickable, Hoverable, Focusable, InputBoxDisplay, InputBox, ToolBar, centered, VirticalMenu
from asyncUi.display import Size, stackEnabler, AutomaticStack, Drawable, Color, drawableRenderer, Point, Color
from asyncUi.resources import fonts
from asyncUi.util import MutableContextManager
from asyncUi import events
from math import sin, cos, radians
from contextlib import ExitStack
import pygame
import datetime
pygame.init()

window = Window(pygame.display.set_mode((250, 250), pygame.RESIZABLE), "test")

@eventHandler
def exiter(event: events.Quit) -> Never:
    exit()
exiter.register()

CLOCK_RADIUS = 100
CENTER = (250//2, 250//2)
arial = fonts.fontManager.loadSystemFont('arial')

def clockPosition(angle: float, length: int) -> Point:
    angle = radians(angle)
    return int(sin(angle) * length), int(cos(angle) * length)
def scaleSize(size: Size, factor: float) -> Size:
    return int(size[0]*factor), int(size[1]*factor)




class Clock(Drawable, AutomaticStack):
    def __init__(self) -> None:
        self.clockCircle = Circle((250//2-CLOCK_RADIUS, 250//2-CLOCK_RADIUS), Color(255, 255, 255), CLOCK_RADIUS)
        self.clockBounds = Circle((250//2-CLOCK_RADIUS, 250//2-CLOCK_RADIUS), Color(100, 100, 100), CLOCK_RADIUS, 5)
        self.clockOrgin = Circle((250//2-5, 250//2-5), Color(0, 0, 0), 5)
        hourDashes: list[Line] = []
        for angle in range(0, 360, 360//12):
            dash = Line(CENTER, Color(0, 0, 0), 4, clockPosition(angle, 110), clockPosition(angle, 80))
            hourDashes.append(dash)
        self.hourDashes = hourDashes

        minuteDashes: list[Line] = []
        for angle in range(0, 360, 360//60):
            dash = Line(CENTER, Color(0, 0, 0), 4, clockPosition(angle, 110), clockPosition(angle, 90))
            minuteDashes.append(dash)
        self.minuteDashes = minuteDashes

        self.minuteHand = Line(CENTER, Color(0, 0, 0), 5, (0,0), clockPosition(0, 100-5))
        self.secondHand = Line(CENTER, Color(255, 0, 0), 5, (0, 0), clockPosition(0, 100-5))
        self.hourHand = Line(CENTER, Color(255, 0, 0), 5, (0, 0), clockPosition(0, 75))

        self.digitalTime = Text(..., arial, 16, Color(255, 0, 0), "00:00:00")
        self.timeBox = Box((0, 0), scaleSize(self.digitalTime.size, 1.125), Color(255, 255, 255))
        self.digitalTime = centered(self.timeBox, self.digitalTime)



        asyncio.ensure_future(self.timeUpdater())
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.clockCircle.draw(window, scale)
        for dash in self.hourDashes:
            dash.draw(window, scale)
        for dash in self.minuteDashes:
            dash.draw(window, scale)

        self.secondHand.draw(window, scale)
        self.minuteHand.draw(window, scale)
        self.hourHand.draw(window, scale)

        self.clockOrgin.draw(window, scale)
        self.clockBounds.draw(window, scale)

        self.timeBox.draw(window, scale)
        self.digitalTime.draw(window, scale)
    
        
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        pass

    def reposition(self, position: Point | EllipsisType) -> Self:
        raise NotImplementedError()
    
    async def timeUpdater(self) -> None:
        while True:
            now = datetime.datetime.now()
            self.minuteHand = Line(CENTER, Color(0, 0, 0), 5, (0,0), clockPosition(180-(360/60)*now.minute - (360/60/60)*now.second, 100-2))
            self.secondHand = Line(CENTER, Color(255, 0, 0), 5, (0, 0), clockPosition(180-(360/60)*now.second, 100-2))
            self.hourHand = Line(CENTER, Color(0, 0, 0), 5, (0, 0), clockPosition(180 - (360/12)*(now.hour % 12) - (360/12/60)*now.minute, 75))

            self.digitalTime = self.digitalTime.changeText(f'{now.hour}:{now.minute}:{now.second}')
            await asyncio.sleep(1)


async def playAlarm(period: int) -> None:   
    while True:
        for i in range(period):
            print("ALARM")
        await asyncio.sleep(1)             



window.startRenderer(30, drawableRenderer(Clock().__enter__()))

window.run()