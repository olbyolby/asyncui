from __future__ import annotations
from types import EllipsisType
from .display import Color, Size, Point, Drawable, Scale, AutomaticStack, stack_enabler, renderer, Clip, rescaler
from typing import TypeVar, Iterable, Final, Callable, Sequence, cast, Generic, Iterator
from functools import cached_property
from .resources.fonts import Font
from contextlib import ExitStack
from .import events
from .window import event_handler_method, Window
from .utils import coroutines, transformers
from .utils.callbacks import Callback, CallbackWrapper
from .utils.descriptors import Placeholder, Inferable
from .utils.context import MutableContextManager
import itertools
import pygame

DrawableT = TypeVar('DrawableT', bound=Drawable)
DrawableT2 = TypeVar('DrawableT2', bound=Drawable)

def render_all(window: pygame.Surface, scale: float, *targets: Drawable) -> None:
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
    
    @cached_property[pygame.Rect]
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

    @cached_property[pygame.Rect]
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

    
    
    size = cached_property(lambda self: self.font[self.font_size].size(self.text))


    @cached_property[pygame.Rect]
    def body(self) -> pygame.Rect:
        return pygame.Rect(*self.position, *self.size)
    
    def character_position(self, index: int) -> Point:
        return self.font[self.font_size].size(self.text[:index])[0] + self.position[0], self.position[1]

    @cached_property
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

    @cached_property
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
    
    @event_handler_method
    def _click_down_handler(self, event: events.MouseButtonDown) -> None:
        scale = Scale(Window().scale_factor)
        if self.debounce is False and  scale.rect(self.area).collidepoint(event.pos):
            self.debounce = True
    @event_handler_method
    def _click_up_handler(self, event: events.MouseButtonUp) -> None:
        scale = Scale(Window().scale_factor)
        if self.debounce is True:
            self.debounce = False
            if scale.rect(self.area).collidepoint(event.pos):
                self.on_click.invoke(event)

    def enable(self) -> None:
        with ExitStack() as stack:
            stack.enter_context(self._click_down_handler)
            stack.enter_context(self._click_up_handler)
            self._stack = stack.pop_all()

class Hoverable(AutomaticStack): 
    position = Placeholder[Point]((0,0))
    def __init__(self, position: Inferable[Point], size: Size, start_hover: Callback[events.MouseMove], end_hover: Callback[events.MouseMove]) -> None:
        self.position = position
        self.size = size
        self.on_hover_start = CallbackWrapper(start_hover)
        self.on_hover_end = CallbackWrapper(end_hover)

        self._hovered = False
    @cached_property
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
    
    @event_handler_method
    def _hover_handler(self, event: events.MouseMove) -> None:
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
            stack.enter_context(self._hover_handler)

            self._stack = stack.pop_all()

class Focusable(AutomaticStack):
    position = Placeholder[Point]((0,0))
    def __init__(self, position: Inferable[Point], size: Size, on_focus: Callback[()], on_unfocus: Callback[()]) -> None:
        self.position = position
        self.size = size
        self.on_focus = CallbackWrapper(on_focus)
        self.on_unfocus = CallbackWrapper(on_unfocus)
    
        self._selected = False

    @cached_property
    def area(self) -> pygame.rect.Rect:
        return pygame.Rect(*self.position, *self.size) 
    @event_handler_method
    def _click_handler(self, event: events.MouseButtonDown) -> None:
        scale = Scale(Window().scale_factor)
        if self._selected is True and not scale.rect(self.area).collidepoint(event.pos):
            self._selected = False
            self.on_unfocus.invoke()
        elif self._selected is False and scale.rect(self.area).collidepoint(event.pos):
            self._selected = True
            self.on_focus.invoke()

    @stack_enabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self._click_handler)

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
        self.cursor_box = Box(self.text.character_position(cursor_position), (2, self.text.height), self.text.color)
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

    def append_text(self, text: str) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text.changeText(self.text.text+text), self.background, self.cursor_position, self.show_cursor)
    def change_text(self, text: str) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text.changeText(text), self.background, self.cursor_position, self.show_cursor)
    def change_cursor_position(self, position: int) -> 'InputBoxDisplay':
        position = max(min(position, len(self.text.text)), 0)
        return InputBoxDisplay(self.position, self.text, self.background, position, self.show_cursor)
    def insert_text(self, text: str) -> 'InputBoxDisplay':
        return self.change_text(self.text.text[:self.cursor_position] + text + self.text.text[self.cursor_position:]).change_cursor_position(self.cursor_position+len(text))
    def backspace(self) -> 'InputBoxDisplay':
        if self.cursor_position == 0:
            return self
        return self.change_text(self.text.text[:self.cursor_position-1] + self.text.text[self.cursor_position:]).change_cursor_position(self.cursor_position-1)
    def delete(self) -> 'InputBoxDisplay':
        if self.cursor_position == len(self.text.text):
            return self
        return self.change_text(self.text.text[:self.cursor_position] + self.text.text[self.cursor_position+1:])
    def change_cursor_shown(self, state: bool) -> 'InputBoxDisplay':
        return InputBoxDisplay(self.position, self.text, self.background, self.cursor_position, state)
    
    @rescaler
    def rescale(self, scale: Scale) -> 'InputBoxDisplay':
        return InputBoxDisplay(scale.point(self.position), self.text.rescale(scale.scale_factor), self.background.rescale(scale.scale_factor), self.cursor_position, self.show_cursor)

    @cached_property[pygame.Rect]
    def body(self) -> pygame.Rect:
        return self.background.body
    
    size = cached_property[Size](lambda s: s.background.size)

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
    def __init__(self, text_box: InputBoxDisplay, on_enter: Callback[str], on_change: Callback[str], input_validater: Callable[[str], bool] = lambda s: True, focused: bool = False) -> None:
        self.position = text_box.position
        self.__textBox = text_box.change_cursor_shown(False)
        self.on_enter = CallbackWrapper(on_enter)
        self.on_change = CallbackWrapper(on_change)
        self.input_validater = input_validater

        self._focused = focused
        self._focuser = Focusable(text_box.position, text_box.size, self._on_focus, self._on_unfocus)
    
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.text_box.draw(window, scale)
    def reposition(self, position: Point | EllipsisType) -> 'InputBox':
        return InputBox(self.text_box.reposition(position), self.on_enter, self.on_change, self.input_validater, self._focused)

    
    def get_size(self) -> Size:
        return self.text_box.size
    size = cached_property[Size](get_size)

    @property
    def text_box(self) -> InputBoxDisplay:
        return self.__textBox
    @text_box.setter
    def text_box(self, value: InputBoxDisplay) -> None:
        if self.input_validater(value.text.text):
            self.__textBox = value
            self.on_change.invoke(value.text.text)    

    def _on_focus(self) -> None:
        self.text_box = self.text_box.change_cursor_shown(True)
        self._focused = True
    def _on_unfocus(self) -> None:
        self.text_box = self.text_box.change_cursor_shown(False)
        self._focused = False
    @event_handler_method
    def _text_input(self, event: events.TextInput) -> None:
        if self._focused:
            self.text_box = self.text_box.insert_text(event.text)
    @event_handler_method
    def _key_down(self, event: events.KeyDown) -> None:
        if self._focused:
            match event.key:
                case events.keyboard.Keys.Backspace:
                    self.text_box = self.text_box.backspace()
                case events.keyboard.Keys.Delete:
                    self.text_box = self.text_box.delete()
                case events.keyboard.Keys.Left:
                    self.text_box = self.text_box.change_cursor_position(self.text_box.cursor_position-1)
                case events.keyboard.Keys.Right:
                    self.text_box = self.text_box.change_cursor_position(self.text_box.cursor_position+1)
                case events.keyboard.Keys.Return:
                    if self.on_enter is not None:
                        self.on_enter.invoke(self.text_box.text.text)
    
    @stack_enabler
    def enable(self, stack: ExitStack) -> None:
        """Enable the handling of events(Should be done from context manager)"""
        stack.enter_context(self._text_input)
        stack.enter_context(self._key_down)
        stack.enter_context(self._focuser)

def add_point(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
    return a[0] + b[0], a[1] + b[1]
class Polygon(Drawable):
    def __init__(self, position: Inferable[Point], color: Color, points: Sequence[Point], thickness: int = 0) -> None:
        self.position = position
        self.color = color
        self.points = points
        self.thickness = thickness
    
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        pygame.draw.polygon(window, self.color, [scale.point(point) for point in self.absolute_points], scale.length(self.thickness))

    @cached_property[list[Point]]
    def absolute_points(self) -> list[Point]:
        return [add_point(self.position, point) for point in self.points]
    
    
    def get_size(self) -> Size:
        minX, maxX = 0, 0
        minY, maxY = 0, 0
        for (x, y) in self.points:
            minX, maxX = min(minX, x), max(maxX, x)
            minY, maxY = min(minY, y), max(maxY, y)
        
        return (maxX - minX), (maxY - minY)
    size = cached_property[Size](get_size)

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
            scale.point(add_point(add_point(self.start, self.position), line_offset)), 
            scale.point(add_point(add_point(self.end, self.position), line_offset)), 
            int(self.thickness*scale.scale_factor)
            )

    def reposition(self, position: Inferable[Point]) -> 'Line':
        return Line(position, self.color, self.thickness, self.start, self.end)
    
    def change_point(self, start: Inferable[Point], end: Inferable[Point]) -> Line:
        return Line(self.position, self.color, self.thickness, self.start if start is ... else start, self.end if end is ... else end)

class Group(Drawable, AutomaticStack, Generic[DrawableT]):
    def __init__(self, position: Inferable[Point], widgets: Iterable[DrawableT]) -> None:
        self.position = position
        self.widgets = [widget.reposition(add_point(self.position,widget.position)) for widget in widgets]
    def draw(self, window: pygame.Surface, scale: float) -> None:
        for widget in self.widgets:
            widget.draw(window, scale)
    def reposition(self, position: Inferable[Point]) -> 'Group[DrawableT]':
        return Group(position, (widget.reposition((widget.position[0] - self.position[0], widget.position[1] - self.position[1])) for widget in self.widgets))
    @stack_enabler
    def enable(self, stack: ExitStack) -> None:
        for widget in self.widgets:
            if isinstance(widget, AutomaticStack):
                stack.enter_context(widget)

    def get_size(self) -> Size:
        max_x = max_y = 0
        for widget in self.widgets:
            max_x = max(widget.position[0] + widget.size[0], max_x)
            max_y = max(widget.position[1] + widget.size[1], max_y)
        return max_x - self.position[0], max_y - self.position[1]
    size = cached_property(get_size)

    def __iter__(self) -> Iterator[DrawableT]:
        return iter(self.widgets)
    def __len__(self) -> int:
        return len(self.widgets)
    

class Circle(Drawable):
    def __init__(self, position: Inferable[Point], color: Color, radius: int, thickness: int = 0) -> None:
        self.position = position
        self.color = color
        self.radius = radius
        self.thickness = thickness
    
    @renderer
    def draw(self, window: pygame.Surface, scale: Scale) -> None:
        scaled_radius = scale.length(self.radius)
        position = scale.point(self.position)
        center = add_point(position, (scaled_radius//2, scaled_radius//2))
        pygame.draw.circle(window, self.color, center, scaled_radius, scale.length(self.thickness))

    def reposition(self, position: Point | EllipsisType) -> Circle:
        return Circle(position, self.color, self.radius, self.thickness)
    
    def get_size(self) -> Size:
        return (self.radius*2, self.radius*2)
    size = cached_property[Size](get_size)

class Button(Drawable, AutomaticStack, Generic[DrawableT]):
    size = Placeholder[Size]((0,0))
    def __init__(self, position: Inferable[Point], widget: DrawableT, on_click: Inferable[Callback[()]]) -> None:
        self.position = position
        self.widget = widget.reposition(position)
        self.size = widget.size
        self.clicked = CallbackWrapper(on_click if on_click is not ... else None)

    @cached_property[Clickable]
    def _clicker(self) -> Clickable:
        return Clickable(self.position, self.size, lambda e: self.clicked.invoke())
    
    @stack_enabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self._clicker)

    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.widget.draw(window, scale)

    def reposition(self, position: Point | EllipsisType) -> 'Button[DrawableT]':
        return Button(position, self.widget, self.clicked)
    def change_widget(self, widget: DrawableT) -> 'Button[DrawableT]':
        return Button(self.position, widget, self.clicked)
    def change_callback(self, on_click: Inferable[Callback[()]]) -> 'Button[DrawableT]':
        return Button(self.position, self.widget, on_click)

class OptionBar(Drawable, AutomaticStack, Generic[DrawableT]):
    size = Placeholder[Size]((0,0))
    def __init__(self, position: Inferable[Point], size: Size, options: Sequence[DrawableT]):
        self.position = position
        self.size = size
        if position is ...:
            self.options = options
        else:
            self.options = cast(Sequence[DrawableT], list(horizontal() @ match_y(position[1]) @ options))
    
    def draw(self, window: pygame.Surface, scale: float) -> None:
        for option in self.options:
            option.draw(window, scale)
    
    @stack_enabler
    def enable(self, stack: ExitStack) -> None:
        for option in self.options:
            if isinstance(option, AutomaticStack):
                option.enable()
        
    def reposition(self, position: Inferable[Point]) -> 'OptionBar[DrawableT]':
        return OptionBar(position, self.size, self.options)
    def change_options(self, options: Sequence[DrawableT]) -> 'OptionBar[DrawableT]':
        return OptionBar(self.position, self.size, self.options)

class OptionMenu(Drawable, AutomaticStack, Generic[DrawableT]):
    size = Placeholder[Size]((0,0))
    def __init__(self, position: Inferable[Point], size: Size, switch: Button[DrawableT], options: Sequence[Drawable], open: bool = False):
        self.position = position
        self.size = size

        align = vertical()
        self.switch = cast(Button[DrawableT], align(switch.reposition(self.position))).change_callback(self._close_or_open)
        if position is ...:
            self.options = options
        else:
            self.options = list(align @ match_x(position[0]) @ options)
        self.open = open

    def _close_or_open(self) -> None:
        for option in self.options:
            if isinstance(option, AutomaticStack):
                if self.open is True:
                    option.disable()
                else:
                    option.enable()
        self.open = not self.open

    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.switch.draw(window, scale)
        if self.open is True:
            for option in self.options:
                option.draw(window, scale)
    @stack_enabler
    def enable(self, stack: ExitStack) -> None:
        self.switch.enable()

    def reposition(self, position: Inferable[Point]) -> 'OptionMenu[DrawableT]':
        return OptionMenu(position, self.size, self.switch, self.options)

class Visable(Drawable, AutomaticStack, Generic[DrawableT]):
    size = Placeholder[Size]((0,0))
    def __init__(self, position: Inferable[Point], widget: DrawableT, shown: bool) -> None:
        self.position = position
        self.widget = widget.reposition(position)
        self.size = self.widget.size

        self.is_shown = shown
    
    def draw(self, window: pygame.Surface, scale: float) -> None:
        if self.is_shown:
            self.widget.draw(window, scale)
    def reposition(self, position: Inferable[Point]) -> 'Visable[DrawableT]':
        return Visable(position, self.widget, self.is_shown)
    def change_widget(self, widget: DrawableT) -> 'Visable[DrawableT]':
        return Visable(self.position, self.widget, self.is_shown)
    def set_visability(self, shown: bool) -> "Visable[DrawableT]":
        return Visable(self.position, self.widget, shown) 
    def shown(self) -> 'Visable[DrawableT]':
        return self.set_visability(True)
    def hidden(self) -> 'Visable[DrawableT]':
        return self.set_visability(False)
    def swap_visibility(self) -> 'Visable[DrawableT]':
        return self.set_visability(not self.is_shown)
    
    @stack_enabler
    def enable(self, stack: ExitStack) -> None:
        if self.is_shown and isinstance(self.widget, AutomaticStack):
            stack.enter_context(self.widget)
# Some useful positioner functions

def centered(outter: Drawable, inner: DrawableT) -> DrawableT:
    outter_center = (outter.position[0] + (outter.size[0]//2), outter.position[1] + (outter.size[1]//2))
    inner_position = (outter_center[0] - inner.size[0]//2, outter_center[1] - inner.size[1]//2)
    return inner.reposition(inner_position)    


    
@transformers.transformer_factory
@coroutines.statefulFunction
def match_x(x: int) -> coroutines.Stateful[Drawable, Drawable]:
    widget, = yield coroutines.SkipState
    while True:
        widget, = yield widget.reposition((x, widget.position[1]))
@transformers.transformer_factory
@coroutines.statefulFunction
def match_y(y: int) -> coroutines.Stateful[Drawable, Drawable]:
    widget, = yield coroutines.SkipState
    while True:
        widget, = yield widget.reposition((widget.position[0], y))
@transformers.transformer_factory
@coroutines.statefulFunction
def overlap() -> coroutines.Stateful[Drawable, Drawable]:
    widget, = base, = yield coroutines.SkipState
    while True:
        widget, = yield widget.reposition(base.position)
@transformers.transformer_factory
@coroutines.statefulFunction
def horizontal() -> coroutines.Stateful[Drawable, Drawable]:
    widget, = yield coroutines.SkipState
    x_offset = coroutines.accumulate(widget.position[0])
    while True:
        widget, = yield widget.reposition((x_offset(widget.size[0]),widget.position[1]))

@transformers.transformer_factory
@coroutines.statefulFunction
def vertical() -> coroutines.Stateful[Drawable, Drawable]:
    widget, = yield coroutines.SkipState
    y_offset = coroutines.accumulate(widget.position[1])
    while True:
        widget, = yield widget.reposition((widget.position[0], y_offset(widget.size[1])))

@transformers.transformer_factory
@coroutines.statefulFunction
def concentric() -> coroutines.Stateful[Drawable, Drawable]:
    widget, = base, =  yield coroutines.SkipState
    while True:
        widget, = yield centered(base, widget)


