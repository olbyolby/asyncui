from typing import Any, Type, Callable, Protocol, Literal, Generic, TypeVar, Annotated
from . import keyboard, mouse
from inspect import get_annotations as getAnnotations
from dataclasses import dataclass
import pygame


class EventTypeMeta(type):
    type: int
    def __init__(self, name: str, bases: tuple['EventTypeMeta', ...], attrs: dict[str, object]):
        if 'type' not in attrs:
            self.type = pygame.event.custom_type()
        if not isinstance(self.type, int):
            raise RuntimeError(f'Event type {name} has an invalid ".type" attribute(it must be an integer)') 
        
        super().__init__(name, bases, attrs)

    def __instancecheck__(self, instance: object) -> bool:
        if isinstance(instance, pygame.event.Event) and (instance.type == self.type or self is Event):
            return True
            
        return super().__instancecheck__(instance)




class Event(metaclass = EventTypeMeta):
    type: int = -1

def toPygameEvent(event: Event | pygame.event.Event) -> pygame.event.Event:
    if isinstance(event, pygame.event.Event):
        return event
    return pygame.event.Event(event.type, vars(event))

class KeyDown(Event):
    type: int = pygame.KEYDOWN
    key: keyboard.Key
    mod: keyboard.ModifierKey
    unicode: str

class KeyUp(Event):
    type: int = pygame.KEYUP
    key: keyboard.Key
    mod: keyboard.ModifierKey
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
    button: mouse.Button
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