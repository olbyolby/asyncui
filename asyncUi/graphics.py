from __future__ import annotations
from asyncUi.display import Point
from .util import Placeholder, Inferable
from .display import Color, Size, Point, Drawable, Scale, AutomaticStack, stackEnabler
from typing import Final, Self, Callable, TypeVar, TypeVarTuple, Annotated, Type
from functools import cached_property as cachedProperty, wraps
from .resources.fonts import Font
from contextlib import ExitStack
import pygame


T = TypeVar('T')
def renderer(function: Callable[[T, pygame.Surface, Scale], None]) -> Callable[[T, pygame.Surface, float], None]:
    @wraps(function)
    def wrapper(self: T, window: pygame.Surface, scale: float) -> None:
        return function(self, window, Scale(scale))
    return wrapper


class Box(Drawable):
    filledBox: Final = 0

    size = Placeholder[Size]()
    color = Placeholder[Color]()
    def __init__(self, position: Inferable[Point], size: Inferable[Size], color: Inferable[Color], thinkness: int = filledBox):
        self.position = position
        self.size = size
        self.color = color
        self.thinkness = thinkness
    
    @cachedProperty
    def body(self) -> pygame.Rect:
        return pygame.Rect(*self.position, *self.size)
    
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        pygame.draw.rect(window, self.color, scale.rect(self.body), self.thinkness)       

    def reposition(self, position: Point) -> 'Box':
        return Box(position, self.size, self.color)     

class Image(Drawable):
    def __init__(self, position: Inferable[Point], surface: pygame.Surface, size: Size | None = None) -> None:
        self.position = position
        self.surface = surface
        self.size = size if size is not None else surface.get_size()

        # Scaling images so slow, so cache it and update the cache when the scale is changed
        # This prevents rescaling each frame, which is slow
        self._cachedSurface = surface
        self._cachedScale: float = 1
    
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        if self._cachedScale != scale.scaleFactor:
            self._cachedSurface = pygame.transform.scale_by(self.surface, scale.scaleFactor)
            self._cachedScale = scale.scaleFactor
        
        window.blit(self._cachedSurface, scale.point(self.position))

    def reposition(self, position: Point) -> 'Image':
        return Image(position, self.surface, self.size)
    def resize(self, size: Size) -> 'Image':
        return Image(self.position, self.surface, size)

class Text(Drawable):
    text = Placeholder[str]()
    def __init__(self, position: Inferable[Point], font: Font, size: int, color: Color, text: Inferable[str]) -> None:
        self.position = position
        self.font = font
        self.fontSize = size
        self.color = color
        self.text = text

        # Dirty, evil, mutable state
        # This exits for speed, rendering the text each frame is slow, we cache it
        # Then, if the scale changes, rerender the text only then
        self._cachedScale = 1.
        self._cachedText: pygame.Surface | None = None

    @cachedProperty
    def size(self) -> Size:
        return self.font[self.fontSize].size(self.text)
    @cachedProperty
    def body(self) -> pygame.Rect:
        return pygame.Rect(*self.position, *self.size)

    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        #Check if the scale has changed, if yes, rerender the text
        if self._cachedText is None or self._cachedScale != scale.scaleFactor:
            self._cachedScale = scale.scaleFactor
            self._cachedText = self.font[scale.fontSize(self.fontSize)].render(self.text, True, self.color)
        
        window.blit(self._cachedText, scale.point(self.position))

    def reposition(self, position: Point) -> 'Text':
        return Text(position, self.font, self.fontSize, self.color, self.text)
    def changeText(self, text: str) -> 'Text':
        return Text(self.position, self.font, self.fontSize, self.color, text)



from . import events
from . window import eventHandlerMethod, Window

class Clickable(AutomaticStack):
    def __init__(self, area: pygame.rect.Rect, onClick: Callable[[events.MouseButtonUp], None]) -> None:
        self.area = area
        self.onClick = onClick
    
        self.debounce = False
        self._stack = ExitStack()
    @eventHandlerMethod
    def _clickDownHandler(self, event: events.MouseButtonDown) -> None:
        scale = Scale(Window().scaleFactor)
        if self.debounce is False and  scale.rect(self.area).collidepoint(event.pos):
            self.debounce = True
    @eventHandlerMethod
    def _clickUpHandler(self, event: events.MouseButtonUp) -> None:
        scale = Scale(Window().scaleFactor)
        if self.debounce is True:
            self.debounce = False
            if scale.rect(self.area).collidepoint(event.pos):
                self.onClick(event)

    def enable(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(self._clickDownHandler)
            stack.enter_context(self._clickUpHandler)
            self._stack = stack.pop_all()

class Hoverable(AutomaticStack): 
    def __init__(self, area: pygame.rect.Rect, startHover: Callable[[events.MouseMove], None] | None, endHover: Callable[[events.MouseMove], None] | None) -> None:
        self.area = area
        self.startHover = startHover
        self.endHover = endHover

        self._hovered = False
    @eventHandlerMethod
    def _hoverHandler(self, event: events.MouseMove) -> None:
        scale = Scale(Window().scaleFactor)
        if self._hovered is False and scale.rect(self.area).collidepoint(event.pos):
            self._hovered = True
            if self.startHover is not None:
                self.startHover(event)
        elif self._hovered is True and not scale.rect(self.area).collidepoint(event.pos):
            self._hovered = False
            if self.endHover is not None:
                self.endHover(event)

    def enable(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(self._hoverHandler)

            self._stack = stack.pop_all()

class Focusable(AutomaticStack):
    def __init__(self, area: pygame.rect.Rect, onFocus: Callable[[], None], onUnfocus: Callable[[], None]) -> None:
        self.area = area
        self.onFocus = onFocus
        self.onUnfocus = onUnfocus
    
        self._selected = False
    @eventHandlerMethod
    def _clickHandler(self, event: events.MouseButtonDown) -> None:
        scale = Scale(Window().scaleFactor)
        if self._selected is True and not scale.rect(self.area).collidepoint(event.pos):
            self._selected = False
            self.onUnfocus()
        elif self._selected is False and scale.rect(self.area).collidepoint(event.pos):
            self._selected = True
            self.onFocus()

    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self._clickHandler)