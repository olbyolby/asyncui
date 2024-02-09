from typing import Never, no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *
from asyncUi.window import Window, eventHandler
from asyncUi.graphics import Line, Polygon, Circle, Button, Group, Box, Text, Clickable, Hoverable, Focusable, InputBoxDisplay, InputBox, ToolBar, centered, VirticalMenu
from asyncUi.display import Size, stackEnabler, AutomaticStack, Drawable, Color, drawableRenderer, Point, Color
from asyncUi.resources import fonts
from asyncUi.util import MutableContextManager, Flag
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

CLOCK_RADIUS = 100
CENTER = (250//2, 250//2)
arial = fonts.fontManager.loadSystemFont('arial')

def clockPosition(angle: float, length: int) -> Point:
    angle = radians(angle)
    return int(sin(angle) * length), int(cos(angle) * length)
def scaleSize(size: Size, factor: float) -> Size:
    return int(size[0]*factor), int(size[1]*factor)


async def playAlarm(period: int) -> None:   
    while True:
        for i in range(period):
            print("ALARM")
        await asyncio.sleep(1)             


async def waitForTime(when: int) -> None:
    now = datetime.datetime.now()
    nowMinutes = now.minute + now.hour*60
    minutesTo = when - nowMinutes

    print(when - nowMinutes)
    return await asyncio.sleep(minutesTo*60)

async def alarm(when: int, period: int) -> None:
    await waitForTime(when)
    await playAlarm(period)

BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)
@dataclass
class Alarm:
    when: int # Minutes after midnight
    period: int
    name: str
    
    def __post_init__(self) -> None:
        self.handle = asyncio.ensure_future(alarm(self.when, self.period))  


class AlarmUi(Drawable, AutomaticStack):
    def __init__(self, position: Point, exit: Callable[[], None], addAlarm: Callable[[int], None]) -> None:
        self.position = position


        self.background = Box(position, (200, 200), Color(255, 255, 255))
        self.exitButton = Button((position[0]+200-25, position[1]), Box(..., (25, 25), Color(255, 0, 0)), exit)
        self.labels = ToolBar((position[0], position[1]+25), [
            Group(..., [Box(..., (25, 25), WHITE), Text(..., arial, 16, BLACK, "ID")]),
            Group(..., [Box(..., (120, 25), WHITE), Text(..., arial, 16, BLACK, "Name")]),
            Group(..., [Box(..., (50, 25), WHITE), Text(..., arial, 16, BLACK, f'Time')]),
        ])
        self.addAlarmCallback = addAlarm

        self.inputProcess = ToolBar((position[0], position[1]+25*2), [
            Button(..., Group(..., [Box(..., (25, 25), WHITE), Text(..., arial, 16, BLACK, "+")]), self._addTime),
            Group(..., [
                Box(..., (120, 25), WHITE, 2), 
                InputBox(
                    InputBoxDisplay(..., Text(..., arial, 16, BLACK, ""), Box(..., (100, 25), WHITE), 0), 
                    None, 
                    self._acceptName)]),
            Group(..., [
                Box(..., (50, 25), WHITE), 
                InputBox(
                    InputBoxDisplay(..., Text(..., arial, 16, BLACK, ""), Box(..., (100, 25), WHITE), 0), 
                    None, 
                    self._acceptTime)]),
        ])
        self.alarms: VirticalMenu = VirticalMenu((position[0], position[1]+25*3), [])
        self.totalAlarms = 0
        self._timeInput = ""
        self._nameInput = ""

        self.addAlarm("Name", 21, 9)


    def _acceptTime(self, time: str) -> bool:
        if len(time) <= 5 and not any(char not in (*string.digits, ':') for char in time) and time.count(':') <= 1:
            self._timeInput = time
            return True
        else:
            return False
    def _acceptName(self, name: str) -> None:
        self._nameInput = name

    def _addTime(self) -> None:
        timeInput = self._timeInput

        values = timeInput.replace(string.whitespace, '').split(':')
        if len(values) != 2 or values[0] == '' or values[1] == '':
            return print("Invalid time", "\"", timeInput, "\"")
        
        hours, minutes = [int(value) for value in values]
        if not 0 <= hours <= 24:
            return print("Invalid hours(Must be between 0 and 24)")
        if not 0 <= minutes <= 59:
            return print("invalid minutes(Must be between 0 and 59)")

        self.addAlarm(self._nameInput, hours, minutes)

    def addAlarm(self, name: str, hour: int, minute: int) -> None:
        self.alarms = self.alarms.appendWidgets([
            ToolBar((...), [
                Group(..., [Box(..., (25, 25), WHITE), Text(..., arial, 16, BLACK, str(self.totalAlarms+1))]),
                Group(..., [Box(..., (120, 25), WHITE), Text(..., arial, 16, BLACK, name)]),
                Group(..., [Box(..., (50, 25), WHITE), Text(..., arial, 16, BLACK, f'{hour}:{minute}')]),
            ])
        ])   

        self.totalAlarms+=1
        self.addAlarmCallback(hour*60+minute)

    def reposition(self, position: Point | EllipsisType) -> 'AlarmUi':
        assert position is not ...
        return AlarmUi(position, self.exitButton.on_click, self.addAlarmCallback)
    
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.background.draw(window, scale)
        self.exitButton.draw(window, scale)

        self.labels.draw(window, scale)
        self.inputProcess.draw(window, scale)
        self.alarms.draw(window, scale)
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self.exitButton)
        stack.enter_context(self.inputProcess)

class Clock(Drawable, AutomaticStack):
    def __init__(self) -> None:

        self.background = Box((0,0), (250, 250), BLACK)
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

        self.alarmUi = AlarmUi((25, 25), self._closeAlarms, self._addAlarm).__enter__()
        self.alarmUiShown = False
        self.openAlarmUi = Button((200, 0), Group(..., [Box(..., (50, 25), Color(255, 0, 0)), Text(..., arial, 16, BLACK, "Alarms")]), self._openAlarms)

        self.alarms: list[Alarm] = []

        asyncio.ensure_future(self.timeUpdater())

    _alarmUiShown = False
    @property
    def alarmUiShown(self) -> bool:
        return self._alarmUiShown
    @alarmUiShown.setter
    def alarmUiShown(self, value: bool) -> None:
        if self.alarmUiShown is False and value is True:
            self.openAlarmUi.enable()
        elif self.alarmUiShown is True and value is False:
            self.openAlarmUi.disable()
        self._alarmUiShown = value
        
    def _addAlarm(self, when: int) -> None:
        asyncio.ensure_future(alarm(when, 6))
    def _openAlarms(self) -> None:
        self.alarmUiShown = True
        self.openAlarmUi.disable()
    def _closeAlarms(self) -> None:
        self.alarmUiShown = False
        self.openAlarmUi.enable()
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.background.draw(window, scale)
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
    
        
        if self.alarmUiShown is True:
            self.alarmUi.draw(window, scale)
        else:
            self.openAlarmUi.draw(window, scale)
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self.openAlarmUi)

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


  


window.startRenderer(30, drawableRenderer(Clock().__enter__()))

window.run()