"""
This module defines classes and utilities for creating widgets

Classes:
    Color - represents a color, complatable with pygame's color format, and includes constants for common colors
    Point - alais for tuple[int, int]
    Size - alies for tuple[int, int]
    Rect - alies for pygame.Rect
    Drawable - base class for all drawables in asyncui
    Scale - provides simplistic interface for scaling various elements by a scale factor
    AutomaticStack - base class for all drawables which can handle and respond to events
    Clip - context manager for automaticlly handling the application and replacement of a clipping area on a surface
Functions:
    stack_enabler - convince method for AutomaticStack's `enable` method, passes ExitStack as an argument and automatically sets `_stack`
    renderer - convinience method for Drawable's `draw` method, passes a `Scale` object instead of a float scale factor
    drawable_renderer - take a Drawable and return a function compatible with `asyncui.window.Window.start_rendering`
"""
import pygame
from abc import ABC, abstractmethod
from typing import Self, Iterable, Type, Callable, TypeVar, Iterator, Sequence, overload
from .utils.descriptors import Placeholder
from .window import Window
from contextlib import ExitStack
from types import TracebackType, EllipsisType
from functools import wraps, cached_property
__all__ = [
    'Color',
    'Point',
    'Size',
    'Drawable',
    'Scale',
    'AutomaticStack',
    'stack_enabler',
    'renderer'
]

T = TypeVar('T')
class SequenceMixin(Sequence[int]):
    @abstractmethod
    def _sequence(self) -> Sequence[int]:
        ...
    
    def __len__(self) -> int:
        return len(self._sequence())
    def __iter__(self) -> Iterator[int]:
        return iter(self._sequence())
    
    @overload
    def __getitem__(self, item: int) -> int: ...
    @overload
    def __getitem__(self, item: slice) -> Sequence[int]: ...
    def __getitem__(self, item: slice | int) -> int | Sequence[int]:
        return self._sequence()[item]

class Color(SequenceMixin):
    def __init__(self, red: int, green: int, blue: int) -> None:
        self.red = max(0, min(red, 255))
        self.green = max(0, min(green, 255))
        self.blue = max(0, min(blue, 255))

    # Useful constants
    RED: 'Color'
    GREEN: 'Color'
    BLUE: 'Color'
    WHITE: 'Color'
    BLACK: 'Color'

    
    def complementary(self) -> 'Color':
        return self.WHITE - self
    def __add__(self, other: 'Color') -> 'Color':
        if not isinstance(other, Color):
            return NotImplemented
        return Color(self.red + other.red, self.green + other.green, self.blue + other.blue)
    def __sub__(self, other: 'Color') -> 'Color':
        if not isinstance(other, Color):
            return NotImplemented
        return Color(self.red - other.red, self.green - other.green, self.blue - other.blue)       
 
    def _sequence(self) -> Sequence[int]:
        return (self.red, self.green, self.blue)
Color.RED = Color(255, 0, 0)
Color.GREEN = Color(0, 255, 0)
Color.BLUE = Color(0, 0, 255)
Color.WHITE = Color(255, 255, 255)
Color.BLACK = Color(0, 0, 0)

Point = tuple[int, int]

Size = tuple[int, int]

Rect = pygame.Rect
class Drawable(ABC):
    @abstractmethod
    def draw(self, window: pygame.Surface, scale: float, /) -> None:
        ...

    @abstractmethod
    def reposition(self, position: Point | EllipsisType, /) -> Self:
        ...

    position = Placeholder[Point]((0, 0))
    size: cached_property[Size] | Placeholder[Size]

    body: cached_property[Rect] = cached_property[Rect](lambda s: Rect(s.position, s.size))

class Scale: 
    def __init__(self, scale: float) -> None:
        self.scale_factor = scale
    @staticmethod
    def difference(wanted: Size, current: Size) -> 'Scale':
        if current[0] / current[1] != wanted[0] / wanted[1]:
            raise ValueError("Aspect ratio must be equal")
        return Scale(current[0] / wanted[0])
    def rect(self, rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(*self.point((rect.x, rect.y)), *self.size((rect.width, rect.height)))
    def point(self, point: Point) -> Point:
        return (int(point[0] * self.scale_factor), int(point[1] * self.scale_factor))
    def size(self, size: Size) -> Size:
        return self.point(size)
    def font(self, size: int) -> int:
        return int(self.scale_factor * size)
    def polygon(self, polygon: Iterable[Point]) -> list[Point]:
        return [self.point(point) for point in polygon]
    def length(self, length: int) -> int:
        return int(length*self.scale_factor)

    def __float__(self) -> float:
        return self.scale_factor

class AutomaticStack:
    _stack: ExitStack
    
    @abstractmethod
    def enable(self) -> None:
        ...

    def disable(self) -> None:
        self.__exit__(None, None, None)
    
    def __exit__(self, exception_type: Type[BaseException] | None, exception: BaseException | None, traceback: TracebackType | None,/) -> None:
        self._stack.__exit__(exception_type, exception, traceback)
    def __enter__(self) -> Self:
        self.enable()
        return self
    
_AutoStackT = TypeVar('_AutoStackT', bound=AutomaticStack)
def stack_enabler(function: Callable[[_AutoStackT, ExitStack], None]) -> Callable[[_AutoStackT], None]:
    """
    Automaticlly manage the ExitStack for an `AutomaticStack`,

    Example:
    ```
    def enable(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(self.InputProcessor)
            
            self._stack = stack.pop_all()
    ```
    can be replaced with
    ```
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context
    ```

    These 2 are equivalent, however, the 2nd is much shorter,
    making it easier to write, and automaticlly seting _stack
    """

    def wrapper(self: _AutoStackT) -> None:
        with ExitStack() as stack:
            function(self, stack)
            self._stack = stack.pop_all()
    return wrapper


def renderer(function: Callable[[T, pygame.Surface, Scale], None]) -> Callable[[T, pygame.Surface, float], None]:
    @wraps(function)
    def wrapper(self: T, window: pygame.Surface, scale: float) -> None:
        return function(self, window, Scale(scale))
    return wrapper

DrawableT = TypeVar('DrawableT', bound=Drawable)
def rescaler(function: Callable[[T, Scale], T]) -> Callable[[T, float], T]:
    @wraps(function)
    def wrapper(self: T, scale: float) -> T:
        return function(self, Scale(scale))
    return wrapper

class Clip:
    def __init__(self, target: pygame.Surface, area: pygame.Rect) -> None:
        self.target = target
        self.area = area
    def __enter__(self) -> Self:
        self.old_clip = self.target.get_clip()
        self.target.set_clip(self.area)
        return self
    def __exit__(self, exception_type: Type[BaseException] | None, exception: BaseException | None, traceback: TracebackType | None,/) -> None:
        self.target.set_clip(self.old_clip)

def drawable_renderer(target: Drawable) -> Callable[[Window], None]:
    def wrapper(window: Window) -> None:
        target.draw(window.window, window.scale_factor)
    return wrapper

