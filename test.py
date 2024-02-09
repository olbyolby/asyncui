from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, eventHandler, eventHandlerMethod
from asyncUi.graphics import MenuWindow, Line, Polygon, Circle, Button, Group, Box, Text, Clickable, Hoverable, Focusable, InputBoxDisplay, InputBox, ToolBar, centered, VirticalMenu, renderAll
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
import winsound
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

async def waitForTime(minutes: int) -> None:
    now = datetime.datetime.now()
    sinceMidnight = now.minute + now.hour * 60

    timeUntil = minutes - sinceMidnight
    print(minutes, sinceMidnight)
    if timeUntil < 0:
        print("next day")
        # Wait until next day
        return await asyncio.sleep((24*60 - sinceMidnight + minutes)*60)
    else:
        print(f"sleeping for {timeUntil}")
        return await asyncio.sleep(timeUntil*60 - now.second)


@dataclass
class AlarmData:
    id: int
    hour: int
    minute: int
    name: str


def chain(*args: Any) -> None:
    return None
class Clock(Drawable, AutomaticStack):
    size = Placeholder[Size]()
    def __init__(self, position: Point, size: Size, radius: int):

        self.position = position
        self.size = size
        self.radius = radius
        center = (position[0] + size[0]//2, position[1] + size[1]//2)

        self.clock_background = Circle((center[0]-radius, center[1]-radius), WHITE, radius)

        axel_radius = radius//19
        self.center_axel = Circle((center[0] - axel_radius, center[1] - axel_radius), BLACK, axel_radius)


        self.clock_border = Circle((center[0]-radius, center[1]-radius), BLACK, radius, 4)
        self.minute_dashes = Group(center, list(self._generateDashes(60, radius*.90, radius*.08)))
        self.hour_dashes = Group(center, list(self._generateDashes(12, radius*.80, radius*.19)))

        self.second_hand = Line((center[0], center[1]), RED, 4, (0, 0), clockPosition(0, radius))
        self.minute_hand = Line(center, BLACK, 4, (0, 0), clockPosition(0, int(radius)))
        self.hour_hand = Line(center, BLACK, 4, (0, 0), clockPosition(0, int(radius*.50)))

        
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

            self.second_hand = self.second_hand.changePoint(..., clockPosition((360/60)*now.second, self.radius))
            self.minute_hand = self.minute_hand.changePoint(..., clockPosition((360/60)*now.minute + (360/60/60)*now.second, int(self.radius*.975)))
            self.hour_hand = self.hour_hand.changePoint(...,  clockPosition((360/12*now.hour) + (360/12/60) * now.minute + (360/12/60/60) * now.second, int(self.radius * .75)))

            await asyncio.sleep(1)
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.clock_background.draw(window, scale)
        self.minute_dashes.draw(window, scale)
        self.hour_dashes.draw(window, scale)


        self.second_hand.draw(window, scale)
        self.minute_hand.draw(window, scale)
        self.hour_hand.draw(window, scale)

        self.center_axel.draw(window, scale)
        self.clock_border.draw(window, scale)
        

    def reposition(self, position: Point | EllipsisType) -> 'Clock':
        assert position is not ...
        return Clock(position, self.size, self.radius)


class Alarm(Drawable, AutomaticStack):
    size = Placeholder[Size]()
    def __init__(self, position: Point | EllipsisType, size: Size, alarm: AlarmData, setOffAlarm: Callable[[AlarmData, Callable[[], None]], None]) -> None:
        self.position = position
        self.size = size
        self.size = size
        self.alarm = alarm
        self.setOffAlarm = setOffAlarm


    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.callback(asyncio.ensure_future(self._waitToSetOff()).cancel)
        
    
    async def _waitToSetOff(self) -> None:
        await waitForTime(self.alarm.hour*60+self.alarm.minute)
        alarmSound = asyncio.ensure_future(self._alarmNoise())
        def _cancel() -> None:
            alarmSound.cancel()
        self.setOffAlarm(self.alarm, _cancel)
    async def _alarmNoise(self) -> None:
        while True:
            for i in range(10):
                winsound.Beep(i+100, 50)
            await asyncio.sleep(1)
    
    @property
    def alarm(self) -> AlarmData:
        return self._alarm
    @alarm.setter
    def alarm(self, alarm: AlarmData) -> None:
        
        self.alarmId = Text(self.position, arial, 16, BLACK, str(alarm.id))
        self.alarmName = Text((self.position[0] + 25, self.position[1]), arial, 16, BLACK, alarm.name)
        self.alarmTime = Text((self.position[0] + 115, self.position[1]), arial, 16, BLACK, f'{alarm.hour}:{alarm.minute}')
        self._alarm = alarm

    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.alarmId.draw(window, scale)
        self.alarmName.draw(window, scale)
        self.alarmTime.draw(window, scale)

    def reposition(self, position: EllipsisType | Point) -> 'Alarm':
        assert position is not ...
        return Alarm(position, self.size, self.alarm, self.setOffAlarm)
    

class AlarmsMenu(Drawable, AutomaticStack):
    size = Placeholder[Size]()
    def __init__(self, position: Point | EllipsisType, size: Size, setOffAlarm: Callable[[AlarmData, Callable[[], None]], None]) -> None:
        if position is ...:
            position = (0,0)
        self.position = position
        self.size = size
        self.setOffAlarm = setOffAlarm

        self.handles: list[asyncio.Handle] = []

        self.title = ToolBar(position, [
            Group(..., [
                Box(..., (25, 25), WHITE),
                Text(..., arial, 16, BLACK, "#"),
                
            ]),
            Group(..., [
                Box(..., (100, 25), WHITE),
                Text(..., arial, 16, BLACK, "Name"),
                
            ]),
            Group(..., [
                Box(..., (50, 25), WHITE),
                Text(..., arial, 16, BLACK, "Time"),
                
            ]),
        ])


        self.alarms: ToolBar = ToolBar((position[0], position[1] + self.title.size[1]), [
            Alarm(..., (25, 100), AlarmData(1, 14, 53, "Alarm"), setOffAlarm),
            ])


    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.title.draw(window, scale)
        self.alarms.draw(window, scale)


    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self.alarms)

    def reposition(self, position: Point | EllipsisType) -> 'AlarmsMenu':
        return AlarmsMenu(position, self.position, self.setOffAlarm)


class App(Drawable, AutomaticStack):
    size = Placeholder[Size]()
    def __init__(self, position: Point, size: Size) -> None:
        self.position = position
        self.size = size

        self.background = Box(position, size, BLACK)
        self.clock = Clock(position, size, 100)
        self.cancelAlarm: Button | None = None
 
        self._alarmMenuOn = Flag()
        self._alarmMenuOn.set()
        self.alarmMenu = MenuWindow((10, 10), (200, 150), WHITE, 
                                   Text(..., arial, 16, BLACK, "Alarms"),
                                   self._alarmMenuOn.unset,
                                   AlarmsMenu(..., size, self._setOffAlarm))
        


    def _setOffAlarm(self, alarm: AlarmData, cancel: Callable[[], None]) -> None:
        alarmText = Text(..., arial, 16, BLACK, alarm.name)
        alarmBackground = Box(..., (self.size[0], alarmText.size[1]), RED)
        alarmText = centered(alarmBackground, alarmText)

        def _cancel() -> None:
            self.cancelAlarm = None
            cancel()
        self.cancelAlarm = Button((0, 0), Group(..., [alarmBackground, alarmText]), _cancel)

    _cancelAlarm: Button | None = None
    @property
    def cancelAlarm(self) -> Button | None:
        return self._cancelAlarm
    @cancelAlarm.setter
    def cancelAlarm(self, value: Button | None) -> None:
        if self.cancelAlarm is not None:
            self.cancelAlarm.disable()
        if value is not None:
            value.enable()
        self._cancelAlarm = value

    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.background.draw(window, scale)

        self.clock.draw(window, scale)

        if self.cancelAlarm is not None:
            self.cancelAlarm.draw(window, scale)
        if self._alarmMenuOn:
            self.alarmMenu.draw(window, scale)

    @eventHandlerMethod
    def openAlarms(self, e: events.KeyDown) -> None:
        if e.key == events.keyboard.Keys.A:
            self._alarmMenuOn.set()

    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self.clock)
        stack.enter_context(self.alarmMenu)
        stack.enter_context(self.openAlarms)
        stack.callback(lambda: self.cancelAlarm.disable() if self.cancelAlarm else None)
        


    def reposition(self, position: Point | EllipsisType) -> 'App':
        assert position is not ...
        return App(position, self.size)


window.startRenderer(30, drawableRenderer(App((0,0), (250, 250)).__enter__()))





window.run()