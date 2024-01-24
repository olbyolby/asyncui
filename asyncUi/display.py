import pygame
from abc import ABC, abstractmethod
from typing import Self, NamedTuple
from .util import Placeholder

class Color(NamedTuple):
    red: int
    green: int
    blue: int

Point = tuple[int, int]

Size = tuple[int, int]

class Drawable(ABC):
    @abstractmethod
    def draw(self, window: pygame.Surface, scale: tuple[float, float], /) -> None:
        ...

    @abstractmethod
    def reposition(self, position: Point, /) -> Self:
        ...
    position = Placeholder[Point]()
    
