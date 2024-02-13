from __future__ import annotations
from typing import Any, Iterable, Union, cast, Generic, TypeVar, overload, Self, TypeVarTuple, Callable, Protocol, Generator
from types import EllipsisType, TracebackType
from functools import wraps


import asyncio

T = TypeVar('T')
T2 = TypeVar('T2')

__all__ = ('Placeholder')

class Placeholder(Generic[T]):
    def __init__(self, default: T | None = None, name: str | None = None):
        self.name: str | None = name
        self.default = default
    def __set_name__(self, owner: type[T2], name: str) -> None:
        self.name = "_" + name
        self.attr_name = name
    
    @overload
    def __get__(self, instance: None, owner: type[T2]) -> Self: ...
    @overload
    def __get__(self, instance: T2, owner: type[T2]) -> T: ...

    def __get__(self, instance: T2 | None, owner: type[T2]) -> Self | T:
        if instance is None:
            return self
        else:
            assert self.name is not None, "descriptor's name must be set"
            if not hasattr(instance, self.name):
                raise ValueError(f'attribute {self.attr_name} of {instance!r} is not initialized')
            value = cast(T, getattr(instance, self.name))
            return value
    
    def __set__(self, instance: T2, value: T | EllipsisType) -> None:
        assert self.name is not None
        setattr(instance, self.name, value if value is not ... else self.default)
Inferable = Union[T, EllipsisType]

Ts = TypeVarTuple('Ts')
EventCallback = Union[Callable[[*Ts], None], 'EventDispatcher[*Ts]', None] # Union because EventDispatcher isn't defined yet
class EventDispatcher(Generic[*Ts]):
    def __init__(self, default_handler: Callable[[*Ts], None] | EventDispatcher[*Ts] | None = None) -> None:
        self.handlers: set[Callable[[*Ts], None]] = set()
        if isinstance(default_handler, EventDispatcher):
            self.handlers.update(default_handler.handlers) #type: ignore
        elif default_handler is not None:
            self.handlers.add(default_handler)

        self._next_event = asyncio.Future[tuple[*Ts]]()

    def addEventHandler(self, handler: Callable[[*Ts], None]) -> None:
        self.handlers.add(handler)
    def removeEventHandler(self, handler: Callable[[*Ts], None]) -> None:
        self.handlers.remove(handler)
    def getNextEvent(self) -> asyncio.Future[tuple[*Ts]]:
        return self._next_event
    
    def notify(self, *data: *Ts) -> None:
        self._next_event.set_result(data)
        self._next_event = asyncio.Future()
        for handler in {*self.handlers}:
            handler(*data)

    def __await__(self) -> Generator[Any, None, tuple[*Ts]]:
        return self._next_event.__await__()



class Flag:
    def __init__(self) -> None:
        self._state = False
    def __bool__(self) -> bool:
        return self._state
    def set(self, state: bool = True) -> None:
        self._state = state
    def unset(self) -> None:
        self._state = False

Tco = TypeVar('Tco', covariant=True)
Tcon = TypeVar('Tcon', contravariant=True)
class ReadableProperty(Protocol[Tco]):
    def __get__(self, instance: Any, owner: type[Any]) -> Tco:
        ...


def listify(function: Callable[[*Ts], Iterable[T]]) -> Callable[[*Ts], list[T]]:
    @wraps(function)
    def wrapper(*args: *Ts) -> list[T]:
        return [value for value in function(*args)]
    return wrapper


class ContextHandler(Protocol):
    def __enter__(self) -> Self:
        ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None, /) -> None:
        ...
ContextT = TypeVar('ContextT', bound=ContextHandler)

class MutableContextManager(Generic[ContextT]):
    def __init__(self, value: ContextT | None = None) -> None:
        self.context = value
    def changeContext(self, value: ContextT) -> None:
        if self.context is not None:
            self.context.__exit__(None, None, None)
        self.context = value.__enter__()
    def getContext(self) -> ContextT:
        if self.context is None:
            raise ValueError("Context is None")
        return self.context
    
    def clear(self) -> None:
        if self.context is not None:
            self.context.__exit__(None, None, None)
            self.context = None
    
    def __enter__(self) -> Self:
        return self
    def __exit__(self, exception: type[BaseException] | None, exceptionType: BaseException | None, traceback: TracebackType | None) -> None:
        if self.context is not None:
            self.context.__exit__(None, None, None)
            self.context = None

