# ruff: noqa
from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, eventHandler, eventHandlerMethod
from asyncUi.graphics import MenuWindow, Line, Polygon, Circle, Button, Group, Box, Text, Clickable, Hoverable, Focusable, InputBoxDisplay, InputBox, HorizontalGroup, centered, VirticalGroup, renderAll
from asyncUi.display import Size, stackEnabler, AutomaticStack, Drawable, Color, drawableRenderer, Point, Color
from asyncUi.resources import fonts
from asyncUi.util import MutableContextManager, Flag, Placeholder
from asyncUi import events
from math import sin, cos, radians
from contextlib import ExitStack
from dataclasses import dataclass, InitVar
from functools import cached_property
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
GREEN = Color(0, 255, 0)

def clockPosition(angle: float, length: int) -> Point:
    angle = radians(180-angle)
    return int(sin(angle) * length), int(cos(angle) * length)

async def waitForTime(minutes: int) -> None:
    now = datetime.datetime.now()
    sinceMidnight = now.minute + now.hour * 60

    timeUntil = minutes - sinceMidnight

    if timeUntil < 0:

        # Wait until next day
        return await asyncio.sleep((24*60 - sinceMidnight + minutes)*60)
    else:

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
    def __init__(self, position: Point | EllipsisType, size: Size, alarm: AlarmData) -> None:
        self.position = position
        self.size = size
        self.alarm = alarm



    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        pass
        
    
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
        return Alarm(position, self.size, self.alarm)
    
class AlarmInput(Drawable, AutomaticStack):
    size = Placeholder[Size]()
    def __init__(self, position: Point, size: Size, addAlarm: Callable[[int, int, str], None]) -> None:
        self.position = position
        self.size = size
        self.addAlarm = addAlarm

        self.accept = Button(position, Box(position, (25, 25), GREEN), self._addAlarm)
        self.name = InputBox(InputBoxDisplay((position[0]+25, position[1]), Text(..., arial, 16, BLACK, " name "), Box(..., (90, 25), WHITE), 0), None, lambda s: None)
        self.hour = InputBox(InputBoxDisplay((position[0]+115, position[1]), Text(..., arial, 16, BLACK, "00"), Box(..., (25, 25), WHITE), 0), None, None, self._acceptHour)
        self.minute = InputBox(InputBoxDisplay((position[0]+140, position[1]), Text(..., arial, 16, BLACK, "00"), Box(..., (25, 25), WHITE), 0), None, None, self._acceptMinute)
        self.seperator = Text((position[0]+135, position[1]), arial, 16, BLACK, ":")

    def _acceptHour(self, text: str) -> bool:
        return all(char in string.digits for char in text) and len(text)<=2
    def _acceptMinute(self, text: str) -> bool:
        return all(char in string.digits for char in text) and len(text)<=2
    
    def _addAlarm(self) -> None:
        hourText = self.hour.text_box.text.text
        minuteText = self.minute.text_box.text.text


        if hourText == '' or (hour:=int(hourText)) > 24:
            return
        if minuteText == '' or (minute:=int(minuteText)) > 60:
            return
        self.addAlarm(hour, minute, self.name.text_box.text.text)

    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self.name)
        stack.enter_context(self.hour)
        stack.enter_context(self.minute)
        stack.enter_context(self.accept)

    

    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.accept.draw(window, scale)
        self.name.draw(window, scale)
        self.hour.draw(window, scale)
        self.minute.draw(window, scale)
        self.seperator.draw(window, scale)

    def reposition(self, position: tuple[int, int] | EllipsisType) -> Self:
        raise NotImplementedError()
    
class AlarmsMenu(Drawable, AutomaticStack):
    size = Placeholder[Size]()
    def __init__(self, position: Point | EllipsisType, size: Size, addAlarm: Callable[[AlarmData], None]) -> None:
        if position is ...:
            position = (0,0)
        self.position = position
        self.size = size
        self.addAlarm = addAlarm

        self.title = HorizontalGroup(position, [
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


        self.alarmState = MutableContextManager[VirticalGroup](None)
        self.alarms: VirticalGroup = VirticalGroup((position[0], position[1] + self.title.size[1]), [
            ])
        
        

        self.input = AlarmInput((position[0], 150), (size[0], 25), self._addAlarm)

    @property
    def alarms(self) -> VirticalGroup:
        return self._alarms
    @alarms.setter
    def alarms(self, value: VirticalGroup) -> None:
        self.alarmState.changeContext(value)
        self._alarms = value
    def _addAlarm(self, hour: int, minute: int, name: str) -> None:
        data = AlarmData(len(self.alarms._widgets), hour, minute, name)
        self.addAlarm(data)
        self.alarms = self.alarms.appendWidgets([Alarm(..., (100, 25), data), ])


    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.title.draw(window, scale)
        self.alarms.draw(window, scale)
        self.input.draw(window, scale)

    def disableInput(self) -> None:
        self.input.disable()
    def enableInput(self) -> None:
        self.input.enable()

    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
    
        stack.enter_context(self.alarmState)
        stack.enter_context(self.input)

    def reposition(self, position: Point | EllipsisType) -> 'AlarmsMenu':
        return AlarmsMenu(position, self.size, self.addAlarm)

class App(Drawable, AutomaticStack):
    size = Placeholder[Size]()
    def __init__(self, position: Point, size: Size) -> None:
        self.position = position
        self.size = size

        self.background = Box(position, size, BLACK)
        self.clock = Clock(position, size, 100)
        self.cancelAlarm: Button | None = None
 
        self._alarmMenuOn = Flag()
        self.alarmMenu = MenuWindow((10, 10), (200, 150), WHITE, 
                                   Text(..., arial, 16, BLACK, "Alarms"),
                                   self._closeAlarmMneu,
                                   AlarmsMenu(..., size, self._addAlarm))
        
        self.alarmHandles: list[asyncio.Task[None]] = []
    def _addAlarm(self, alarm: AlarmData) -> None:
        self.alarmHandles.append(asyncio.ensure_future(self._waitToSetOff(alarm)))
    
    def _closeAlarmMneu(self) -> None:
        self._alarmMenuOn.unset()
        self.alarmMenu.screen.disableInput()

    async def _waitToSetOff(self, alarm: AlarmData) -> None:
        await waitForTime(alarm.hour*60+alarm.minute)
        alarmSound = asyncio.ensure_future(self._alarmNoise(alarm.id))
        def _cancel() -> None:
            alarmSound.cancel()
        self._setOffAlarm(alarm, _cancel)
    async def _alarmNoise(self, alarmID: int) -> None:
        while True:
            for i in range(10):
                winsound.Beep(i+100*(alarmID+1), 50)
            await asyncio.sleep(1)

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
            self.alarmMenu.screen.enableInput()

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