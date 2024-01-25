from .util import Placeholder, Inferable
from .display import Color, Size, Point, Drawable
from typing import Final, Self
from functools import cached_property as cachedProperty
import pygame


class Box(Drawable):
    def __init__(self, position: Inferable[Point], size: Size, color: Color):
        self.position = position
        self.size = size
        self.color = color
    
    @cachedProperty
    def body(self) -> pygame.Rect:
        return pygame.Rect(*self.position, *self.size)
    
    def draw(self, window: pygame.Surface, scale: tuple[float, float]) -> None:
        pygame.draw.rect(window, self.color, self.body)       

    def reposition(self, position: Point) -> 'Box':
        return Box(position, self.size, self.color)

    
