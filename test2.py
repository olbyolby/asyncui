from typing import overload, TypeVar, Protocol, Generic, Type, cast, Self, TypeVarTuple, Callable, Never, Awaitable
from types import TracebackType
import asyncio

class ContextHandler(Protocol):
    def __enter__(self) -> Self:
        ...
    def __exit__(self, excType: Type[BaseException] | None, excValue: BaseException | None, traceback: TracebackType | None, /) -> None:
        ...
T = TypeVar('T', bound=ContextHandler)
T2 = TypeVar('T2')
Ts = TypeVarTuple('Ts')
class ManagedAttr(Generic[T, T2]):
    def __init__(self, privateName: str | None = None) -> None:
        self.privateName = privateName if privateName is not None else '?'
    def __set_name__(self, owner: Type[T2], name: str) -> None:
        if self.privateName == '?':
            self.privateName = '_'+name

    @overload
    def __get__(self, instance: T2, owner: Type[T2]) -> T: ...
    @overload
    def __get__(self, instance: None, owner: Type[T2]) -> Self: ...
    def __get__(self, instance: None | T2, owner: Type[T2]) -> Self | T:
        if instance is None:
            return self
        else:
            return cast(T, getattr(instance, self.privateName))
    def __set__(self, instance: T2, value: T) -> None:
        if hasattr(instance, self.privateName):
            oldValue = cast(T, getattr(instance, self.privateName))
            oldValue.__exit__(None, None, None)
        value.__enter__()
        setattr(instance, self.privateName, value)
    def __delete__(self, instance: T2) -> None:
        if hasattr(instance, self.privateName):
            value = cast(T, getattr(instance, self.privateName))
            value.__exit__(None, None, None)
            delattr(instance, self.privateName)



class Inverval:
    def __init__(self, function: Callable[[], None | Awaitable[None]], interval: float) -> None:
        self.function = function
        self.interval = interval
        self._running = False

        asyncio.create_task(self._runner())
    async def _runner(self) -> None:
        assert self._running is False
        self._running = True
        while self._running:
            start = asyncio.get_event_loop().time()

            result = self.function()
            if isinstance(result, Awaitable):
                await result
            
            end = asyncio.get_event_loop().time()
            delta = self.interval - (end - start)
            await asyncio.sleep(delta)

    def cancel(self) -> None:
        self._running = False

class AutomaticBases(Generic[*Ts]):
    def __init__(self, function: Callable[[*Ts], None]) -> None:
        self.function = function
    def __set_name__(self, owner: Type[T2], name: str) -> None:
        
        def wrapper(*args: *Ts) -> None:
            self.function(*args)
            for base in owner.mro():
                if hasattr(base, name):
                    getattr(base, name)(*args)
        setattr(owner, name, wrapper)


class Callback(Generic[*Ts]):
    def __init__(self, callback: Callable[[*Ts], None | Awaitable[None]] | None) -> None:
        self.callback = callback
    def invoke(self, *args: *Ts) -> None:
        if self.callback is None:
            return
        
        result = self.callback(*args)
        if isinstance(result, Awaitable):
            asyncio.ensure_future(result)
        