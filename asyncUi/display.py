import pygame
import asyncio
from abc import ABC, abstractmethod
from typing import Self, NamedTuple, Iterable, Type, Callable, TypeVar, Generic, Protocol, Final, ClassVar
from .util import Placeholder
from .resources import fonts
from .window import Window
from contextlib import ExitStack
from abc import abstractmethod
from types import TracebackType, EllipsisType
from functools import wraps, cached_property as cachedProperty

__all__ = [
    'Color',
    'Point',
    'Size',
    'Drawable',
    'Scale',
    'AutomaticStack',
    'stackEnabler',
    'renderer'
]

T = TypeVar('T')

class Color(NamedTuple):
    red: int
    green: int
    blue: int

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

    position: Placeholder[Point] = Placeholder[Point]((0, 0))
    size: cachedProperty[Size] | Placeholder[Size]

    body: cachedProperty[Rect] = cachedProperty[Rect](lambda s: Rect(s.position, s.size))

class Scale: 
    def __init__(self, scale: float) -> None:
        self.scale_factor = scale
    def rect(self, rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(*self.point((rect.x, rect.y)), *self.size((rect.width, rect.height)))
    def point(self, point: Point) -> Point:
        return (int(point[0] * self.scale_factor), int(point[1] * self.scale_factor))
    def size(self, size: Size) -> Size:
        return self.point(size)
    def fontSize(self, size: int) -> int:
        return int(self.scale_factor * size)
    def polygon(self, polygon: Iterable[Point]) -> list[Point]:
        return [self.point(point) for point in polygon]
    def length(self, length: int) -> int:
        return int(length*self.scale_factor)


class AutomaticStack:
    _stack: ExitStack
    
    @abstractmethod
    def enable(self) -> None:
        ...

    def disable(self) -> None:
        self.__exit__(None, None, None)
    
    def __exit__(self, exceptionType: Type[BaseException] | None, exception: BaseException | None, traceback: TracebackType | None,/) -> None:
        self._stack.__exit__(exceptionType, exception, traceback)
    def __enter__(self) -> Self:
        self.enable()
        return self
    
_AutoStackT = TypeVar('_AutoStackT', bound=AutomaticStack)
def stackEnabler(function: Callable[[_AutoStackT, ExitStack], None]) -> Callable[[_AutoStackT], None]:
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
        self.oldClip = self.target.get_clip()
        self.target.set_clip(self.area)
        return self
    def __exit__(self, exceptionType: Type[BaseException] | None, exception: BaseException | None, traceback: TracebackType | None,/) -> None:
        self.target.set_clip(self.oldClip)

def drawableRenderer(target: Drawable) -> Callable[[Window], None]:
    def wrapper(window: Window) -> None:
        target.draw(window.window, window.scaleFactor)
    return wrapper



class Rectangular(Protocol):
    @property
    @abstractmethod
    def body(self) -> pygame.Rect:
        ...

    @property
    @abstractmethod
    def size(self) -> Size:
        ...