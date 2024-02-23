from __future__ import annotations
from types import EllipsisType
from .util import Placeholder, Inferable, CallbackWrapper, Callback
from .display import Color, Size, Point, Drawable, Scale, AutomaticStack, stackEnabler, renderer, Clip, rescaler, widgetRenderer
from typing import TypeVar, Iterable, Final, Callable, Sequence, Generic
from functools import cached_property as cachedProperty
from .resources.fonts import Font
from contextlib import ExitStack
from .import events
from .window import eventHandlerMethod, Window
from .utils import coroutines, transformers
import pygame

DrawableT = TypeVar('DrawableT', bound=Drawable)

def renderAll(window: pygame.Surface, scale: float, *targets: Drawable) -> None:
    for target in targets:
        target.draw(window, scale)

class Box(Drawable):
    filledBox: Final = 0

    color = Placeholder[Color](Color(255, 255, 255))
    size = Placeholder[Size]((0, 0))
    def __init__(self, position: Inferable[Point], size: Inferable[Size], color: Inferable[Color], thinkness: int = filledBox):
        self.position = position
        self.size = size
        self.color = color
        self.thinkness = thinkness
    
    @cachedProperty[pygame.Rect]
    def body(self) -> pygame.Rect:
        return pygame.Rect(*self.position, *self.size)
    
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        pygame.draw.rect(window, self.color, scale.rect(self.body), scale.length(self.thinkness))     

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
        self._cached_surface = surface
        self._cached_scale: float = 1
    
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        if self._cached_scale != scale.scale_factor:
            self._cached_surface = pygame.transform.scale_by(self.surface, scale.scale_factor)
            self._cached_scale = scale.scale_factor
        
        window.blit(self._cached_surface, scale.point(self.position))

    def reposition(self, position: Inferable[Point]) -> 'Image':
        return Image(position, self.surface, self.size)
    def resize(self, size: Size) -> 'Image':
        return Image(self.position, self.surface, size)
    
    @rescaler
    def rescale(self, scale: Scale) -> 'Image':
        return Image(scale.point(self.position), self.surface, scale.size(self.size))

    @cachedProperty[pygame.Rect]
    def body(self) -> pygame.Rect:
        return pygame.Rect(self.position, self.size)
    

class Text(Drawable):
    text = Placeholder[str]('')
    def __init__(self, position: Inferable[Point], font: Font, size: int, color: Color, text: Inferable[str]) -> None:
        self.position = position
        self.font = font
        self.font_size = size
        self.color = color
        self.text = text

        # Dirty, evil, mutable state
        # This exits for speed, rendering the text each frame is slow, we cache it
        # Then, if the scale changes, rerender the text only then
        self._cached_scale = 1.
        self._cached_text: pygame.Surface | None = None

    
    
    size = cachedProperty(lambda self: self.font[self.font_size].size(self.text))


    @cachedProperty[pygame.Rect]
    def body(self) -> pygame.Rect:
        return pygame.Rect(*self.position, *self.size)
    
    def characterPosition(self, index: int) -> Point:
        return self.font[self.font_size].size(self.text[:index])[0] + self.position[0], self.position[1]

    @cachedProperty
    def height(self) -> int:
        return self.font[self.font_size].get_linesize()

    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        #Check if the scale has changed, if yes, rerender the text
        if self._cached_text is None or self._cached_scale != scale.scale_factor:
            self._cached_scale = scale.scale_factor
            self._cached_text = self.font[scale.font(self.font_size)].render(self.text, True, self.color)
        
        window.blit(self._cached_text, scale.point(self.position))

    def reposition(self, position: Inferable[Point]) -> 'Text':
        return Text(position, self.font, self.font_size, self.color, self.text)
    def changeText(self, text: str) -> 'Text':
        return Text(self.position, self.font, self.font_size, self.color, text)
    
    @rescaler
    def rescale(self, scale: Scale) -> 'Text':
        return Text(scale.point(self.position), self.font, scale.font(self.font_size), self.color, self.text)



class Clickable(AutomaticStack):
    position = Placeholder[Point]((0,0))
    def __init__(self, position: Inferable[Point], size: Size, on_click: Callback[events.MouseButtonUp]) -> None:
        self.position = position
        self.size = size
        self.on_click = CallbackWrapper(on_click)
    
        self.debounce = False
        self._stack = ExitStack()

    @cachedProperty
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
    
    @eventHandlerMethod
    def _clickDownHandler(self, event: events.MouseButtonDown) -> None:
        scale = Scale(Window().scale_factor)
        if self.debounce is False and  scale.rect(self.area).collidepoint(event.pos):
            self.debounce = True
    @eventHandlerMethod
    def _clickUpHandler(self, event: events.MouseButtonUp) -> None:
        scale = Scale(Window().scale_factor)
        if self.debounce is True:
            self.debounce = False
            if scale.rect(self.area).collidepoint(event.pos):
                self.on_click.invoke(event)

    def enable(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(self._clickDownHandler)
            stack.enter_context(self._clickUpHandler)
            self._stack = stack.pop_all()

class Hoverable(AutomaticStack): 
    position = Placeholder[Point]((0,0))
    def __init__(self, position: Inferable[Point], size: Size, start_hover: Callback[events.MouseMove], end_hover: Callback[events.MouseMove]) -> None:
        self.position = position
        self.size = size
        self.on_hover_start = CallbackWrapper(start_hover)
        self.on_hover_end = CallbackWrapper(end_hover)

        self._hovered = False
    @cachedProperty
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
    
    @eventHandlerMethod
    def _hoverHandler(self, event: events.MouseMove) -> None:
        scale = Scale(Window().scale_factor)
        if self._hovered is False and scale.rect(self.area).collidepoint(event.pos):
            self._hovered = True
            if self.on_hover_start is not None:
                self.on_hover_start.invoke(event)
        elif self._hovered is True and not scale.rect(self.area).collidepoint(event.pos):
            self._hovered = False
            if self.on_hover_end is not None:
                self.on_hover_end.invoke(event)

    def enable(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(self._hoverHandler)

            self._stack = stack.pop_all()

class Focusable(AutomaticStack):
    position = Placeholder[Point]((0,0))
    def __init__(self, position: Inferable[Point], size: Size, on_focus: Callback[()], on_unfocus: Callback[()]) -> None:
        self.position = position
        self.size = size
        self.on_focus = CallbackWrapper(on_focus)
        self.on_unfocus = CallbackWrapper(on_unfocus)
    
        self._selected = False

    @cachedProperty
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
    @eventHandlerMethod
    def _clickHandler(self, event: events.MouseButtonDown) -> None:
        scale = Scale(Window().scale_factor)
        if self._selected is True and not scale.rect(self.area).collidepoint(event.pos):
            self._selected = False
            self.on_unfocus.invoke()
        elif self._selected is False and scale.rect(self.area).collidepoint(event.pos):
            self._selected = True
            self.on_focus.invoke()

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
    def __init__(self, position: Inferable[Point], text: Text, background: Box, cursor_position: int, show_cursor: bool = True) -> None:
        self.position = position
        self.background = background.reposition(position)

        if position is not ...:
            self.text = text.reposition((position[0], position[1]))
        else:
            self.text = text

        self.show_cursor = show_cursor
        self.cursor_box = Box(self.text.characterPosition(cursor_position), (2, self.text.height), self.text.color)
        self.cursor_position  = cursor_position

    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        with Clip(window, scale.rect(self.background.body)):
            self.background.draw(window, scale.scale_factor)
            self.text.draw(window, scale.scale_factor)
            if self.show_cursor:
                self.cursor_box.draw(window, scale.scale_factor)
    
    def reposition(self, position: Point | EllipsisType) -> 'InputBoxDisplay':
        return InputBoxDisplay(position, self.text, self.background, self.cursor_position, self.show_cursor)

    def appendText(self, text: str) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text.changeText(self.text.text+text), self.background, self.cursor_position, self.show_cursor)
    def changeText(self, text: str) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text.changeText(text), self.background, self.cursor_position, self.show_cursor)
    def changeCursorPosition(self, position: int) -> 'InputBoxDisplay':
        position = max(min(position, len(self.text.text)), 0)
        return InputBoxDisplay(self.position, self.text, self.background, position, self.show_cursor)
    def insertText(self, text: str) -> 'InputBoxDisplay':
        return self.changeText(self.text.text[:self.cursor_position] + text + self.text.text[self.cursor_position:]).changeCursorPosition(self.cursor_position+len(text))
    def backspace(self) -> 'InputBoxDisplay':
        if self.cursor_position == 0:
            return self
        return self.changeText(self.text.text[:self.cursor_position-1] + self.text.text[self.cursor_position:]).changeCursorPosition(self.cursor_position-1)
    def delete(self) -> 'InputBoxDisplay':
        if self.cursor_position == len(self.text.text):
            return self
        return self.changeText(self.text.text[:self.cursor_position] + self.text.text[self.cursor_position+1:])
    def changeCursorShown(self, state: bool) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text, self.background, self.cursor_position, state)
    
    @rescaler
    def rescale(self, scale: Scale) -> 'InputBoxDisplay':
        return InputBoxDisplay(scale.point(self.position), self.text.rescale(scale.scale_factor), self.background.rescale(scale.scale_factor), self.cursor_position, self.show_cursor)

    @cachedProperty[pygame.Rect]
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
    def __init__(self, textBox: InputBoxDisplay, on_enter: Callback[str], on_change: Callback[str], input_validater: Callable[[str], bool] = lambda s: True) -> None:
        self.position = textBox.position
        self.__textBox = textBox.changeCursorShown(False)
        self.on_enter = CallbackWrapper(on_enter)
        self.on_change = CallbackWrapper(on_change)
        self.input_validater = input_validater

        self._focused = False
        self._focuser = Focusable(textBox.position, textBox.size, self._onFocus, self._onUnfocus)
    
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.text_box.draw(window, scale)
    def reposition(self, position: Point | EllipsisType) -> 'InputBox':
        return InputBox(self.text_box.reposition(position), self.on_enter, self.on_change)
    def rescale(self, factor: float) -> 'InputBox':
        return InputBox(self.text_box.rescale(factor), self.on_enter, self.on_change)

    
    def getSize(self) -> Size:
        return self.text_box.size
    size = cachedProperty[Size](getSize)

    @property
    def text_box(self) -> InputBoxDisplay:
        return self.__textBox
    @text_box.setter
    def text_box(self, value: InputBoxDisplay) -> None:
        if self.input_validater(value.text.text):
            self.__textBox = value
            self.on_change.invoke(value.text.text)    

    def _onFocus(self) -> None:
        self.text_box = self.text_box.changeCursorShown(True)
        self._focused = True
    def _onUnfocus(self) -> None:
        self.text_box = self.text_box.changeCursorShown(False)
        self._focused = False
    @eventHandlerMethod
    def _textInput(self, event: events.TextInput) -> None:
        if self._focused:
            self.text_box = self.text_box.insertText(event.text)
    @eventHandlerMethod
    def _keyDown(self, event: events.KeyDown) -> None:
        if self._focused:
            match event.key:
                case events.keyboard.Keys.Backspace:
                    self.text_box = self.text_box.backspace()
                case events.keyboard.Keys.Delete:
                    self.text_box = self.text_box.delete()
                case events.keyboard.Keys.Left:
                    self.text_box = self.text_box.changeCursorPosition(self.text_box.cursor_position-1)
                case events.keyboard.Keys.Right:
                    self.text_box = self.text_box.changeCursorPosition(self.text_box.cursor_position+1)
                case events.keyboard.Keys.Return:
                    if self.on_enter is not None:
                        self.on_enter.invoke(self.text_box.text.text)
    
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        """Enable the handling of events(Should be done from context manager)"""
        stack.enter_context(self._textInput)
        stack.enter_context(self._keyDown)
        stack.enter_context(self._focuser)

def addPoint(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return a[0] + b[0], a[1] + b[1]
class Polygon(Drawable):
    def __init__(self, position: Inferable[Point], color: Color, points: Sequence[Point], thickness: int = 0) -> None:
        self.position = position
        self.color = color
        self.points = points
        self.thickness = thickness
    
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        pygame.draw.polygon(window, self.color, [scale.point(point) for point in self.absolutePoints], scale.length(self.thickness))

    @cachedProperty[list[Point]]
    def absolutePoints(self) -> list[Point]:
        return [addPoint(self.position, point) for point in self.points]
    
    
    def getSize(self) -> Size:
        minX, maxX = 0, 0
        minY, maxY = 0, 0
        for (x, y) in self.points:
            minX, maxX = min(minX, x), max(maxX, x)
            minY, maxY = min(minY, y), max(maxY, y)
        
        return (maxX - minX), (maxY - minY)
    size = cachedProperty[Size](getSize)

    def reposition(self, position: Point | EllipsisType) -> 'Polygon':
        return Polygon(position, self.color, self.points)

class Line(Drawable):
    def __init__(self, position: Inferable[Point], color: Color, thickness: int, start: Point, end: Point) -> None:
        self.position = position
        self.color = color
        self.start = start
        self.end = end
        self.thickness = thickness
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        line_offset = (-self.thickness//2, 0)
        pygame.draw.line(
            window, 
            self.color, 
            scale.point(addPoint(addPoint(self.start, self.position), line_offset)), 
            scale.point(addPoint(addPoint(self.end, self.position), line_offset)), 
            int(self.thickness*scale.scale_factor)
            )

    def reposition(self, position: Inferable[Point]) -> 'Line':
        return Line(position, self.color, self.thickness, self.start, self.end)
    
    def changePoint(self, start: Inferable[Point], end: Inferable[Point]) -> Line:
        return Line(self.position, self.color, self.thickness, self.start if start is ... else start, self.end if end is ... else end)

class Group(Drawable, AutomaticStack):
    def __init__(self, position: Inferable[Point], widgets: Iterable[Drawable]) -> None:
        self.position = position
        self.widgets = [widget.reposition(addPoint(self.position,widget.position)) for widget in widgets]
    def draw(self, window: pygame.Surface, scale: float) -> None:
        for widget in self.widgets:
            widget.draw(window, scale)
    def reposition(self, position: Inferable[Point]) -> 'Group':
        return Group(position, (widget.reposition((widget.position[0] - self.position[0], widget.position[1] - self.position[1])) for widget in self.widgets))
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        for widget in self.widgets:
            if isinstance(widget, AutomaticStack):
                stack.enter_context(widget)

    def getSize(self) -> Size:
        max_x = max_y = 0
        for widget in self.widgets:
            max_x = max(widget.position[0] + widget.size[0], max_x)
            max_y = max(widget.position[1] + widget.size[1], max_y)
        return max_x - self.position[0], max_y - self.position[1]
    size = cachedProperty(getSize)
   
class Circle(Drawable):
    def __init__(self, position: Inferable[Point], color: Color, radius: int, thickness: int = 0) -> None:
        self.position = position
        self.color = color
        self.radius = radius
        self.thickness = thickness
    
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        pygame.draw.circle(window, self.color, scale.point(addPoint(self.position, (self.radius, self.radius))), self.radius*scale.scale_factor, int(self.thickness*scale.scale_factor))

    def reposition(self, position: Point | EllipsisType) -> Circle:
        return Circle(position, self.color, self.radius, self.thickness)
    
    def getSize(self) -> Size:
        return (self.radius, self.radius)
    size = cachedProperty[Size](getSize)

class Button(Drawable, AutomaticStack):
    size = Placeholder[Size]((0,0))
    def __init__(self, position: Inferable[Point], widget: Drawable, on_click: Callback[()]) -> None:
        self.position = position
        self.widget = widget.reposition(position)
        self.size = widget.size
        self.clicked = CallbackWrapper(on_click)

    @cachedProperty[Clickable]
    def _clicker(self) -> Clickable:
        return Clickable(self.position, self.size, lambda e: self.clicked.invoke())
    
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self._clicker)

    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.widget.draw(window, scale)

    def reposition(self, position: Point | EllipsisType) -> 'Button':
        return Button(position, self.widget, self.clicked)
    
class MenuWindow(Drawable, AutomaticStack, Generic[DrawableT]):
    size = Placeholder[Size]((0,0))
    def __init__(self, position: Inferable[Point], size: Size, color: Color, title: Text, close: Callback[()], inside: DrawableT) -> None:
        self.position = position
        self.size = size

        self.background = Box(position, size, color)
        self.title = title.reposition(position)
        self.screen = inside.reposition(... if position is ... else addPoint(position, (0,self.title.height)))
        self.close = CallbackWrapper(close)
    
    @cachedProperty
    def exitButton(self) -> Button:
        size = self.size
        return Button(addPoint(self.position, (size[0]-size[0]//8, 0)), Box(..., (size[0]//8, self.title.height), Color(255, 0, 0)), self.close)
   
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self.exitButton)
        if isinstance(self.screen, AutomaticStack):
            stack.enter_context(self.screen)

    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.background.draw(window, scale)
        self.title.draw(window, scale)
        self.exitButton.draw(window, scale)
        self.screen.draw(window, scale)

    def reposition(self, position: Inferable[Point]) -> 'MenuWindow[DrawableT]':
        return MenuWindow(position, self.size, self.background.color, self.title, self.close, self.screen)



# Some useful positioner functions

def centered(outter: Drawable, inner: DrawableT) -> DrawableT:
    outter_center = (outter.position[0] + (outter.size[0]//2), outter.position[1] + (outter.size[1]//2))
    inner_position = (outter_center[0] - inner.size[0]//2, outter_center[1] - inner.size[1]//2)
    return inner.reposition(inner_position)    

@transformers.transformerFactory
@coroutines.statefulFunction
def overlap() -> coroutines.Stateful[Drawable, Drawable]:
    widget, = base, = yield coroutines.SkipState
    while True:
        widget, = yield widget.reposition(base.position)
@transformers.transformerFactory
@coroutines.statefulFunction
def horizontalAligned() -> coroutines.Stateful[Drawable, Drawable]:
    widget, = yield coroutines.SkipState
    x_offset = coroutines.accumulate(widget.position[0])
    while True:
        widget, = yield widget.reposition((x_offset(widget.size[0]),widget.position[1]))

@transformers.transformerFactory
@coroutines.statefulFunction
def verticalAligned() -> coroutines.Stateful[Drawable, Drawable]:
    widget, = yield coroutines.SkipState
    y_offset = coroutines.accumulate(widget.position[1])
    while True:
        widget, = yield widget.reposition((widget.position[0], y_offset(widget.size[1])))

@transformers.transformerFactory
@coroutines.statefulFunction
def concentric() -> coroutines.Stateful[Drawable, Drawable]:
    widget, = base, =  yield coroutines.SkipState
    while True:
        widget, = yield centered(base, widget)
