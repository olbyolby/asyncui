import pygame
from abc import ABC, abstractmethod
from typing import Self, NamedTuple, Iterable
from .util import Placeholder
from .resources import fonts

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
    def reposition(self, position: Point, /) -> Self:
        ...
    position = Placeholder[Point]()
    
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
