from typing import Any, Self
from . import keyboard, mouse
from inspect import get_annotations as getAnnotations
from enum import Enum
import pygame


eventTypes: dict[int, type['Event']] = {}

class Event:
    type: int = -1
    _orgin_event: pygame.event.Event | None = None


    def _marshal(newEvent: Self, event: pygame.event.Event, /) -> Self:
        """
        Base implementation of the event type marshaler

        Reads through the type's annotation's and finds all enumerations,
        it then converts the corasponding event value into the enum, and returns
        a new instance with converted enums

        Subclasses which require custom type marshaling should override this method,
        newEvent will be provided using cls.__new__(cls), and should be initialized with
        data by this function, the 2nd argument, `event`, contains the event being constructed from.
        """

        eventData = vars(event)
        eventAnnotations: dict[str, type | object] = getAnnotations(type(newEvent))
        for name, attrType in eventAnnotations.items():
            if name == 'type': #type is a speical case
                continue

            if isinstance(attrType, type) and issubclass(attrType, Enum):
                vars(newEvent)[name] = attrType(eventData[name])
            else:
                vars(newEvent)[name] = eventData[name]
        newEvent._orgin_event = event

        return newEvent
    def __init_subclass__(cls, **kwargs: Any) -> None:
        if not hasattr(cls, 'type') or cls.type == -1:
            cls.type = pygame.event.custom_type()
        if not isinstance(cls.type, int):
            raise RuntimeError(f'Event type {cls.__name__} has an invalid ".type" attribute(it must be an integer)') 
        
        eventTypes[cls.type] = cls
        super().__init_subclass__(**kwargs)
    def _get_pygame_event(self) -> pygame.event.Event:
        """
        Return a pygame event reperesenting can event object.

        If self._orgin_event is set, returns that, if not, it
        copys the event's `vars` into a pygame event and uses `self.type` as the type
        You probably don't want to override this, but you can if custom pygame event creation is needed.
        """
        if self._orgin_event is not None:
            return self._orgin_event
        else:
            return pygame.event.Event(self.type, vars(self))


def toPygameEvent(event: Event | pygame.event.Event) -> pygame.event.Event:
    if isinstance(event, pygame.event.Event):
        return event
    return event._get_pygame_event()

def marshal(event: pygame.event.Event) -> Event | None:
    if event.type not in eventTypes:
        return None
    eventType = eventTypes[event.type]

    return eventType._marshal(eventType.__new__(eventType), event)

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