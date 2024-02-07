from typing import Any, Type, Callable, Protocol, Literal, Generic, TypeVar, Annotated
from . import keyboard, mouse
from inspect import get_annotations as getAnnotations
from dataclasses import dataclass
from enum import Enum
import pygame


eventTypes: dict[int, type['Event']] = {}
class EventTypeMeta(type):
    type: int
    def __init__(self, name: str, bases: tuple['EventTypeMeta', ...], attrs: dict[str, object]):
        if 'type' not in attrs:
            self.type = pygame.event.custom_type()
        if not isinstance(self.type, int):
            raise RuntimeError(f'Event type {name} has an invalid ".type" attribute(it must be an integer)') 
        eventTypes[self.type] = self #type: ignore

        super().__init__(name, bases, attrs)

    def __instancecheck__(self, instance: object) -> bool:
        if isinstance(instance, pygame.event.Event) and (instance.type == self.type or self is Event):
            return True
            
        return super().__instancecheck__(instance)




class Event(metaclass = EventTypeMeta):
    type: int = -1
    _orginEvent: pygame.event.Event | None = None

def toPygameEvent(event: Event | pygame.event.Event) -> pygame.event.Event:
    if isinstance(event, pygame.event.Event):
        return event
    return pygame.event.Event(event.type, vars(event))

def marshal(event: pygame.event.Event) -> Event | None:
    if event.type not in eventTypes:
        return None
    eventType = eventTypes[event.type]

    newEvent = eventType.__new__(eventType)

    eventData = vars(event)
    eventAnnotations: dict[str, type | object] = getAnnotations(eventType)
    for name, attrType in eventAnnotations.items():
        if name == 'type': #type is a speical case
            continue

        if isinstance(attrType, type) and issubclass(attrType, (Enum, tuple)):
            vars(newEvent)[name] = attrType(eventData[name])
        else:
            vars(newEvent)[name] = eventData[name]
    newEvent._orginEvent = event

    return newEvent

class KeyDown(Event):
    type: int = pygame.KEYDOWN
    key: keyboard.Keys
    mod: keyboard.ModifierKeys
    unicode: str

class KeyUp(Event):
    type: int = pygame.KEYUP
    key: keyboard.Keys
    mod: keyboard.ModifierKeys
    unicode: str
    
class MouseButtonDown(Event):
    type: int = pygame.MOUSEBUTTONDOWN
    pos: tuple[int, int]
    button: mouse.Button
    touch: bool

class MouseButtonUp(Event):
    type: int = pygame.MOUSEBUTTONUP
    pos: tuple[int, int]
    button: mouse.Button
    touch: bool

class MouseWheelScroll(Event):
    type: int = pygame.MOUSEWHEEL
    flipped: bool
    x: int
    y: int
    touch: bool
    precise_x: float
    precise_y: float

class MouseMove(Event):
    type: int = pygame.MOUSEMOTION
    pos: tuple[int, int]
    rel: tuple[int, int]
    buttons: mouse.Buttons
    touch: bool


class TextInput(Event):
    type: int = pygame.TEXTINPUT
    text: str

class Quit(Event):
    type: int = pygame.QUIT


class VideoResize(Event):
    type: int = pygame.VIDEORESIZE
    size: tuple[int, int]
    w: int
    h: int