from typing import Union, cast, Generic, TypeVar, TypeVar, overload, Type, Self, TypeVarTuple, Awaitable, Callable, Protocol, Never
from types import EllipsisType
from functools import wraps
import asyncio

T = TypeVar('T')
T2 = TypeVar('T2')

__all__ = ('Placeholder')

class Placeholder(Generic[T]):
    def __init__(self, default: T | None = None, name: str | None = None):
        self.name: str | None = name
        self.default = default
    def __set_name__(self, owner: Type[T2], name: str) -> None:
        self.name = "_" + name
        self.attrName = name
    
    @overload
    def __get__(self, instance: None, owner: Type[T2]) -> Self: ...
    @overload
    def __get__(self, instance: T2, owner: Type[T2]) -> T: ...

    def __get__(self, instance: T2 | None, owner: Type[T2]) -> Self | T:
        if instance is None:
            return self
        else:
            assert self.name is not None, "descriptor's name must be set"
            if not hasattr(instance, self.name):
                raise ValueError(f'attribute {self.attrName} of {instance!r} is not initialized')
            value = cast(T, getattr(instance, self.name))
            return value
    
    def __set__(self, instance: T2, value: T | EllipsisType) -> None:
        assert self.name is not None
        setattr(instance, self.name, value if value is not ... else self.default)
Inferable = Union[T, EllipsisType]

Ts = TypeVarTuple('Ts')
Callback = 'Callable[[*Ts], None | Awaitable[None]] | EventDispatcher[*Ts | None]'
class EventDispatcher(Generic[*Ts]):
    """
    Provides a "generalization" of callback functions, supporting both asynchronous and synchronous callbacks.
    In addition, callbacks can take arguments for any associated data with the object.
    This is useful for using callback functions in systems like UIs.

    Example:
        class Button:
            def __init__(self) -> None:
                self.onclick = EventDispatcher[ClickEvent]
            def eventHandler(self, event: Event) -> None:
                #Event handling code here
                ...
                self.onclick.notify(event)
        
        button = Button()

        button.onclick.addListener(lambda e: print(f"You clicked {e.pos} from a synchronous callback"))
        
        async def main():
            event = await button.onclick.listen()
            print(f"You clicked {event.pos} but asynchronously!")

        asyncio.run(main())
    """
    def __init__(self, defaultCallback: 'Callable[[*Ts], None | Awaitable[None]] | EventDispatcher[*Ts] | None' = None) -> None:
        """
        Construct an `EventDispatcher`, takes an optional default callback

        The default callback can be ether None, which will register no callbacks,
        or a callable taking event data, which can be both synchronous or asynchronous,
        or another EventDispatcher, which will copy it's event listeners.
        """
        if defaultCallback is None:
            self.listeners = set[Callable[[*Ts], None | Awaitable[None]]]()
        elif isinstance(defaultCallback, EventDispatcher):
            defaultCallback = cast(EventDispatcher[*Ts], defaultCallback)
            self.listeners = defaultCallback.listeners.copy()
        else:
            self.listeners = {defaultCallback}
    def addListener(self, listener: Callable[[*Ts], None | Awaitable[None]]) -> Callable[[*Ts], None | Awaitable[None]]:
        """
        Add an event listener, will be called when the next event is received

        The provided listener must be a callable taking the event's data.
        Both Async and Synchronous functions are support
        """
        self.listeners.add(listener)
        return listener
    def removeListener(self, listener: Callable[[*Ts], None | Awaitable[None]]) -> None:
        """
        Remove an event listener

        If the provided listener is not registered, it will throw an exception.
        """
        self.listeners.remove(listener)
    def listen(self) -> Awaitable[tuple[*Ts]]:
        """
        Wait for the next event to be recived, returning that event's data.

        Allows for asynchronously awaiting for the next event
        """
        future = asyncio.Future[tuple[*Ts]]()
        @self.addListener
        def resolver(*results: *Ts) -> None:
            self.removeListener(resolver)
            future.set_result(results)
        return future
    
    def notify(self, *data: *Ts) -> None:
        """
        Notify all awaiting coroutines and run all event listeners.
        
        All synchronous calllbacks are executed immediately and all asynchronous ones
        are awaited via asyncio.gather
        """

        for listener in frozenset(self.listeners):
            result = listener(*data)
            if isinstance(result, Awaitable):
                asyncio.ensure_future(result)


    def __contains__(self, handler: Callable[[*Ts], None | Awaitable[None]]) -> bool:
        return handler in self.listeners

class Flag:
    def __init__(self) -> None:
        self._state = False
    def __bool__(self) -> bool:
        return self._state
    def set(self, state: bool = True) -> None:
        self._state = state
    def unset(self) -> None:
        self._state = False

from typing import Any
Tco = TypeVar('Tco', covariant=True)
Tcon = TypeVar('Tcon', contravariant=True)
class ReadableProperty(Protocol[Tco]):
    def __get__(self, instance: Any, owner: type[Any]) -> Tco:
        ...
    def __set__(self, instance: Any, value: Never) -> Never:
        ...
class ReadOnlyProperty(ReadableProperty[Tco]):
    __set__: Never
    
T3 = TypeVar('T3')

class FuckOff():
    x = Placeholder[int]()

reveal_type(FuckOff.x)
reveal_type(FuckOff().x)