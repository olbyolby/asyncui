from __future__ import annotations
from types import EllipsisType
from asyncUi.display import Point
from .util import Placeholder, Inferable, Flag, EventDispatcher
from .display import Color, Size, Point, Drawable, Scale, AutomaticStack, stackEnabler, renderer, Clip, rescaler, Rectangular
from typing import Iterable, Final, Self, Callable, Protocol, Sequence, final
from functools import cached_property as cachedProperty, wraps
from .resources.fonts import Font
from contextlib import ExitStack
import pygame



def renderAll(window: pygame.Surface, scale: float, *targets: Drawable) -> None:
    for target in targets:
        target.draw(window, scale)

class Box(Drawable):
    filledBox: Final = 0

    color = Placeholder[Color]()
    size = Placeholder[Size]()
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

    def reposition(self, position: Inferable[Point]) -> 'Box':
        return Box(position, self.size, self.color)   

    @rescaler
    def rescale(self, scale: Scale) -> 'Box':
        return Box(scale.point(self.position), scale.size(self.size), self.color, self.thinkness)

class Image(Drawable):
    size = Placeholder[Size]((0,0))
    def __init__(self, position: Inferable[Point], surface: pygame.Surface, size: Size | None = None) -> None:
        self.position = position
        self.surface = pygame.transform.scale(surface, size) if size is not None else surface
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

    def reposition(self, position: Inferable[Point]) -> 'Image':
        return Image(position, self.surface, self.size)
    def resize(self, size: Size) -> 'Image':
        return Image(self.position, self.surface, size)
    
    @rescaler
    def rescale(self, scale: Scale) -> 'Image':
        return Image(scale.point(self.position), self.surface, scale.size(self.size))

    @cachedProperty
    def body(self) -> pygame.Rect:
        return pygame.Rect(self.position, self.size)
    

class Text(Drawable):
    text = Placeholder[str]('')
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

    
    
    size = cachedProperty(lambda self: self.font[self.fontSize].size(self.text))


    @cachedProperty
    def body(self) -> pygame.Rect:
        return pygame.Rect(*self.position, *self.size)
    
    def characterPosition(self, index: int) -> Point:
        return self.font[self.fontSize].size(self.text[:index])[0] + self.position[0], self.position[1]

    @cachedProperty
    def height(self) -> int:
        return self.font[self.fontSize].get_linesize()

    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        #Check if the scale has changed, if yes, rerender the text
        if self._cachedText is None or self._cachedScale != scale.scaleFactor:
            self._cachedScale = scale.scaleFactor
            self._cachedText = self.font[scale.fontSize(self.fontSize)].render(self.text, True, self.color)
        
        window.blit(self._cachedText, scale.point(self.position))

    def reposition(self, position: Inferable[Point]) -> 'Text':
        return Text(position, self.font, self.fontSize, self.color, self.text)
    def changeText(self, text: str) -> 'Text':
        return Text(self.position, self.font, self.fontSize, self.color, text)
    
    @rescaler
    def rescale(self, scale: Scale) -> 'Text':
        return Text(scale.point(self.position), self.font, scale.fontSize(self.fontSize), self.color, self.text)

from . import events
from . window import eventHandlerMethod, Window

class Clickable(AutomaticStack):
    position = Placeholder[Point]()
    def __init__(self, position: Inferable[Point], size: Size, onClick: Callable[[events.MouseButtonUp], None]) -> None:
        self.position = position
        self.size = size
        self.onClick = onClick
    
        self.debounce = False
        self._stack = ExitStack()

    @cachedProperty
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
    
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
    position = Placeholder[Point]()
    def __init__(self, position: Inferable[Point], size: Size, startHover: Callable[[events.MouseMove], None] | None, endHover: Callable[[events.MouseMove], None] | None) -> None:
        self.position = position
        self.size = size
        self.startHover = startHover
        self.endHover = endHover

        self._hovered = False
    @cachedProperty
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
    
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
    position = Placeholder[Point]()
    def __init__(self, position: Inferable[Point], size: Size, onFocus: Callable[[], None], onUnfocus: Callable[[], None]) -> None:
        self.position = position
        self.size = size
        self.onFocus = onFocus
        self.onUnfocus = onUnfocus
    
        self._selected = False

    @cachedProperty
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
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

class InputBoxDisplay(Drawable):
    """
    A box containing text and a cursor.

    everything you need to render a basic text input box, 
    and to make changes to cursor position or text conent(Inserting text, backspace, left/right arrow, etc).

    Does not do any event handling, either implement that yourself
    or use `InputBox`.
    """
    def __init__(self, position: Inferable[Point], text: Text, background: Box, cursorPosition: int, showCursor: bool = True) -> None:
        self.position = position
        self.background = background.reposition(position)

        if position is not ...:
            height = (background.size[1] - text.height) // 2
            self.text = text.reposition((position[0], position[1] + height))
        else:
            self.text = text

        self.showCursor = showCursor
        self.cursorBox = Box(self.text.characterPosition(cursorPosition), (2, self.text.height), self.text.color)
        self.cursorPosition  = cursorPosition

    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        with Clip(window, scale.rect(self.background.body)):
            self.background.draw(window, scale.scaleFactor)
            self.text.draw(window, scale.scaleFactor)
            if self.showCursor:
                self.cursorBox.draw(window, scale.scaleFactor)
    
    def reposition(self, position: Point | EllipsisType) -> 'InputBoxDisplay':
        return InputBoxDisplay(position, self.text, self.background, self.cursorPosition, self.showCursor)

    def appendText(self, text: str) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text.changeText(self.text.text+text), self.background, self.cursorPosition, self.showCursor)
    def changeText(self, text: str) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text.changeText(text), self.background, self.cursorPosition, self.showCursor)
    def changeCursorPosition(self, position: int) -> 'InputBoxDisplay':
        position = max(min(position, len(self.text.text)), 0)
        return InputBoxDisplay(self.position, self.text, self.background, position, self.showCursor)
    def insertText(self, text: str) -> 'InputBoxDisplay':
        return self.changeText(self.text.text[:self.cursorPosition] + text + self.text.text[self.cursorPosition:]).changeCursorPosition(self.cursorPosition+len(text))
    def backspace(self) -> 'InputBoxDisplay':
        if self.cursorPosition == 0:
            return self
        return self.changeText(self.text.text[:self.cursorPosition-1] + self.text.text[self.cursorPosition:]).changeCursorPosition(self.cursorPosition-1)
    def delete(self) -> 'InputBoxDisplay':
        if self.cursorPosition == len(self.text.text):
            return self
        return self.changeText(self.text.text[:self.cursorPosition] + self.text.text[self.cursorPosition+1:])
    def changeCursorShown(self, state: bool) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text, self.background, self.cursorPosition, state)
    
    @rescaler
    def rescale(self, scale: Scale) -> 'InputBoxDisplay':
        return InputBoxDisplay(scale.point(self.position), self.text.rescale(scale.scaleFactor), self.background.rescale(scale.scaleFactor), self.cursorPosition, self.showCursor)

    @cachedProperty
    def body(self) -> pygame.Rect:
        return self.background.body
    
    size = cachedProperty[Size](lambda s: s.background.size)

class InputBox(Drawable, AutomaticStack):
    """
    Basic text input box, wraps `InputBoxDisplay` to allow reacting to user input

    'hydrates' the InputBoxDisplay, allowing input via the keyboard and detecting when enter is pressed.
    Supported input:
        - Arrow keys for moving around in the text
        - Enter for submitting the text
        - Keyboard input(including modifier keys)
        - Focusing with the mouse(unfouced by default)
        - `onEnter` callback function
    Planned:
        - Copy & paste
        - Scrolling when text is too long
    
    """
    def __init__(self, textBox: InputBoxDisplay, onEnter: Callable[[str], None] | None) -> None:
        self.textBox = textBox.changeCursorShown(False)
        self.onEnter = onEnter


        self._focused = False
        self._focuser = Focusable(textBox.position, textBox.size, self._onFocus, self._onUnfocus)
    
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.textBox.draw(window, scale)
    def reposition(self, position: Point | EllipsisType) -> 'InputBox':
        return InputBox(self.textBox.reposition(position), self.onEnter)
    def rescale(self, factor: float) -> 'InputBox':
        return InputBox(self.textBox.rescale(factor), self.onEnter)

    def _onFocus(self) -> None:
        self.textBox = self.textBox.changeCursorShown(True)
        self._focused = True
    def _onUnfocus(self) -> None:
        self.textBox = self.textBox.changeCursorShown(False)
        self._focused = False
    @eventHandlerMethod
    def _textInput(self, event: events.TextInput) -> None:
        if self._focused:
            self.textBox = self.textBox.insertText(event.text)
    @eventHandlerMethod
    def _keyDown(self, event: events.KeyDown) -> None:
        if self._focused:
            match event.key:
                case events.keyboard.Keys.Backspace:
                    self.textBox = self.textBox.backspace()
                case events.keyboard.Keys.Delete:
                    self.textBox = self.textBox.delete()
                case events.keyboard.Keys.Left:
                    self.textBox = self.textBox.changeCursorPosition(self.textBox.cursorPosition-1)
                case events.keyboard.Keys.Right:
                    self.textBox = self.textBox.changeCursorPosition(self.textBox.cursorPosition+1)
                case events.keyboard.Keys.Return:
                    if self.onEnter is not None:
                        self.onEnter(self.textBox.text.text)
    
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        """Enable the handling of events(Should be done from context manager)"""
        stack.enter_context(self._textInput)
        stack.enter_context(self._keyDown)
        stack.enter_context(self._focuser)


def addPoint(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return a[0] + b[0], a[1] + b[1]
class Group(Drawable, AutomaticStack):
    
    def __init__(self, position: Inferable[Point], widgets: Sequence[Drawable], widgetPositions: Inferable[Sequence[Point]] = ...) -> None:
        self.position = position
  
        if widgetPositions is ...:
            self.orignalPositions: Sequence[Point] = [widget.position for widget in widgets]
        else:
            self.orignalPositions = widgetPositions
        if position is not ...:
            self._widgets: Sequence[Drawable] = [widget.reposition(addPoint(widgetPosition, position)) for widget, widgetPosition in zip(widgets, self.orignalPositions)]
        else:
            self._widgets = widgets
    
    def draw(self, window: pygame.Surface, scale: float) -> None:
        for widget in self._widgets:
            widget.draw(window, scale)
    
    def reposition(self, position: Point | EllipsisType) -> 'Group':
        return Group(position, self._widgets, self.orignalPositions)
    
    @staticmethod
    def _boundingRect(rects: Iterable[pygame.Rect]) -> pygame.Rect:
        minX, minY, maxH, maxW = 0, 0, 0, 0
        for rect in rects:
            minX = min(minX, rect.x)
            minY = min(minY, rect.y)
            maxH = max(maxH, rect.height)
            maxW = max(maxW, rect.width)
        return pygame.Rect(minX, minY, maxW, maxH)
    
    @cachedProperty
    def body(self) -> pygame.Rect:
        return self._boundingRect((widget.body for widget in self._widgets))
    
    @cachedProperty
    def size(self) -> Size:
        return self.body.width, self.body.height

    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        for widget in self._widgets:
            if isinstance(widget, AutomaticStack):
                stack.enter_context(widget)





    