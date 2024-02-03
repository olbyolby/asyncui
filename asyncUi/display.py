import pygame
from abc import ABC, abstractmethod
from typing import Self, NamedTuple, Iterable, Type, Callable, TypeVar
from .util import Placeholder
from .resources import fonts
from .window import Window
from contextlib import ExitStack
from abc import abstractmethod
from types import TracebackType, EllipsisType
from functools import wraps

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

class Color(NamedTuple):
    red: int
    green: int
    blue: int

Point = tuple[int, int]

Size = tuple[int, int]

class Drawable(ABC):
    @abstractmethod
    def draw(self, window: pygame.Surface, scale: float, /) -> None:
        ...

    @abstractmethod
    def reposition(self, position: Point | EllipsisType, /) -> Self:
        ...
    position = Placeholder[Point]((0, 0))
    
class Scale:
    def __init__(self, scale: float) -> None:
        self.scaleFactor = scale
    def rect(self, rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(*self.point((rect.x, rect.y)), *self.size((rect.width, rect.height)))
    def point(self, point: Point) -> Point:
        return (int(point[0] * self.scaleFactor), int(point[1] * self.scaleFactor))
    def size(self, size: Size) -> Size:
        return self.point(size)
    def fontSize(self, size: int) -> int:
        return int(self.scaleFactor * size)
    def polygon(self, polygon: Iterable[Point]) -> list[Point]:
        return [self.point(point) for point in polygon]


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

T = TypeVar('T')
def renderer(function: Callable[[T, pygame.Surface, Scale], None]) -> Callable[[T, pygame.Surface, float], None]:
    @wraps(function)
    def wrapper(self: T, window: pygame.Surface, scale: float) -> None:
        return function(self, window, Scale(scale))
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