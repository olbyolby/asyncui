from typing import Any, Self

from . import keyboard, mouse
from inspect import get_annotations as getAnnotations
from enum import Enum, Flag
import pygame


event_types: dict[int, type['Event']] = {}

class Event:
    """
    The base class for all asyncUi event wrappers, wraps pygame events

    Subclassing behavior:
        This class is intended to be subclassed to create custom event types, or for wrapping external event types.
        If an external event type is being wrapped(Like MouseButtonDown), the `type` attribute must be specified, 
        if a new event is wanted, it can be left blank, in which case a new type will be assigned with `pygame.event.custom_type()`.

        Any attributes of that event ('buttons', 'pos', etc) should be specified with a type annotation, 
        because they will be filled by `marshal` when passed to event handlers, in addition, support for
        Enums and Flags comes out of the box, if an attribute is annotated with an Enum or a Flag, `marshal` will
        convert the value from the pygame event to the corresponding enum value.

        If more complex marshaling behavior is desired(say, scaling points or adding attributes), then 
        `_marshal` may be overridden. It takes a pygame event and should construct a new event of that type,
        in addition, `_get_pygame_event` can be overridden for more complex behavior when converting back to a pygame event.

        The subclass will also be added to the `event_types` dictionary, which maps event's .type attribute to the event class.
        
    Marshaling:
        when an event if recieved from pygame, the event loop must convert it to the type event handlers expect, so it maintains 
        a list of event types and if it contains one with a matching 'type', it calls it's `_marshal` function, which copies all
        expceted attributes as well as cast any values form the pygame type, to it's expected type(like int -> Keys in KeyDown).
        This allows events to have more complex and custom behavior(Like, say, method functions), and for better type safety when
        working with event types. 


    Methods:
        _marshal - convert a pygame event into this event, can be subclassed, but not used directly, use `marshal()` for that.
        _get_pygame_event - convert an instance of this class into an equivalent pygame event, is called by `toPygameEvent`
    Attributes:
        type - The type id of the event, same as pygame's type attribute. If one is not specified by a subclass, 
        it will be implicitly set with pygame.event.custom_type()
        _orgin_event - The pygame event this event originated from, set by `_marshal`, and can be recreived by `_get_pygame_event
    """

    type: int = -1
    _orgin_event: pygame.event.Event | None = None


    def _marshal(new_event: Self, event: pygame.event.Event, /) -> None:
        """
        Base implementation of the event type marshaler

        Reads through the type's annotation's and finds all enumerations(Enum | Flag subclasses),
        it then converts the corasponding event value into the enum, and returns
        a new instance with converted enums

        Subclasses which require custom type marshaling should override this method,
        newEvent will be provided using cls.__new__(cls), and should be initialized with
        data by this function, the 2nd argument, `event`, contains the event being constructed from.
        """

        event_data = vars(event)
        event_annotations: dict[str, type | object] = getAnnotations(type(new_event))
        for name, attr_type in event_annotations.items():
            if name == 'type': #type is a speical case
                continue

            if isinstance(attr_type, type) and issubclass(attr_type, Enum | Flag):
                vars(new_event)[name] = attr_type(event_data[name])
            else:
                vars(new_event)[name] = event_data[name]
        new_event._orgin_event = event

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
            clean_vars: dict[str, Any] = {}
            for name, value in vars(self).items():
                if isinstance(value, Enum):
                    clean_vars[name] = value.value
                else:
                    clean_vars[name] = value
            return pygame.event.Event(self.type, vars(self))
        
    def __init_subclass__(cls, **kwargs: Any) -> None:
        # If no type is specified, create a new custom type
        if not hasattr(cls, 'type') or cls.type == -1:
            cls.type = pygame.event.custom_type()

        # Make sure the type is valid
        if not isinstance(cls.type, int):
            raise RuntimeError(f'Event type {cls.__name__} has an invalid ".type" attribute(it must be an integer)') 
        
        # Register the newly created event's type
        event_types[cls.type] = cls

        super().__init_subclass__(**kwargs)


def to_pygame_event(event: Event | pygame.event.Event) -> pygame.event.Event:
    """Convert an asyncUi event to a pygame event"""
    if isinstance(event, pygame.event.Event):
        return event
    return event._get_pygame_event()

def marshal(event: pygame.event.Event) -> Event | None:
    """
    Preform type marshalling to convert a pygame event to the equivalent asyncUi event, returning None if there is no asyncUi equivalent.

    See `Event._marshal` for details.
    """
    if event.type not in event_types:
        return None
    
    event_type = event_types[event.type]
    new_event = event_type.__new__(event_type)
    event_type._marshal(new_event, event)
    return new_event

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
    buttons: tuple[int, int, int]
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