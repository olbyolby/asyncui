from typing import overload, TypeVar, Protocol, Generic, Type, cast, Self, TypeVarTuple, Callable, Never, Awaitable, Generator
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


import inspect
import ctypes
from types import FrameType
from typing import cast, TypeVar, Any, Iterable


T2 = TypeVar('T2')
def neverNone(var: T2 | None) -> T2:
    if var is None:
        raise ValueError("Unexpected None")
    else:
        return var

class Locals:
    def __init__(self, frame: FrameType | None = None) -> None:
        if frame is None:
            frame = neverNone(neverNone(inspect.currentframe()).f_back)
        super().__setattr__('frame', frame)
    def __getattribute__(self, name: str) -> Any:
        frame = cast(FrameType,super().__getattribute__('frame'))
        if name in frame.f_locals:
            return frame.f_locals[name]
        raise AttributeError(name = name, obj = self)
    def __setattr__(self, name: str, value: Any) -> None:
        frame = cast(FrameType,super().__getattribute__('frame'))
        frame.f_locals[name] = value
        ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))
    def __dir__(self) -> set[str]:
        frame = cast(FrameType,super().__getattribute__('frame'))
        return set(frame.f_locals.keys())

def primesFn() -> Generator[int, None, None]:
    primes: list[int] = []
    yield 2  # Start with the first prime number

    current_number = 3
    while True:
        is_prime = all(current_number % prime != 0 for prime in primes)
        if is_prime:
            primes.append(current_number)
            yield current_number
        current_number += 2  # Skip even numbers

primes = primesFn()
localsPrimes = Locals(primes.gi_frame)

def take(it: Iterable[T2], max: int) -> Generator[T2, None, None]:
    for i, value in enumerate(it):
        yield value
        if i == max:
            return

foundPrimes: list[int] = []
for prime in take(primes,30):
    #print(prime)
    foundPrimes.append(prime)

localsPrimes.primes = []
for prime in take(primes, 30):
    #print(prime)
    foundPrimes.append(prime)

print()
print()
print()
realPrimes: list[int] = []
for prime in take(primesFn(), 60):
    print(prime)
    realPrimes.append(prime)

same = 0
different = 0
for found, real in zip(realPrimes, foundPrimes):
    if found != real:
        print(f"found {found}, epxected {real}")
        different += 1
    else:
        same += 1
        
print(f'{same} primes are correct, {different} are wrong')






class EventDispatcher(Generic[*Ts]):
    def __init__(self, defaultCallback: 'Callable[[*Ts], None | Awaitable[None]] | EventDispatcher[*Ts] | None' = None) -> None:
        if defaultCallback is None:
            self.listeners = set[Callable[[*Ts], None | Awaitable[None]]]()
        elif isinstance(defaultCallback, EventDispatcher):
            defaultCallback = cast(EventDispatcher[*Ts], defaultCallback)
            self.listeners = defaultCallback.listeners.copy()
        else:
            self.listeners = {defaultCallback}
    def addListener(self, listener: Callable[[*Ts], None | Awaitable[None]]) -> None:
        self.listeners.add(listener)
    def removeListener(self, listener: Callable[[*Ts], None | Awaitable[None]]) -> None:
        self.listeners.remove(listener)
    def listen(self) -> Awaitable[tuple[*Ts]]:
        future = asyncio.Future[tuple[*Ts]]()
        @self.addListener
        def resolver(*results: *Ts) -> None:
            self.removeListener(resolver)
            future.set_result(*results)
        return future
    
    async def notify(self, *data: *Ts) -> None:
        for listener in frozenset(self.listeners):
            result = listener(*data)
            if isinstance(result, Awaitable):
                asyncio.ensure_future(result)
CallbackArgument = Callable[[*Ts], None | Awaitable[None]] | EventDispatcher[*Ts] | None


import gc
from typing import TypeVar, Type
T2 = TypeVar('T2')
def unperson(victim: object) -> None:
    """
    "Unperson" an object
    
    Delete every reference to an object, recursively delete any refers which can't be removed
    This elimiates every reference to the object's existance
    """
    for ref in gc.get_referrers(victim):
        for attr in dir(ref):
            try:
                if getattr(ref, attr) is victim:
                    try:
                        setattr(ref, attr, None)
                    except:
                        pass
                    try:
                        delattr(ref, attr)
                    except:
                        pass
            except:
                pass
            try:
                for key in ref.keys():
                    if ref[key] is victim:
                        del ref[key]
            except:
                pass
            try: 
                for i in range(0, len(ref)):
                    if ref[i] is victim:
                        del ref[i]
            except:
                pass
    try: 
        for ref in gc.get_referrers(victim):
            unperson(ref)
    except:
        pass

def genocide(victims: list[object]) -> None:
    """
    "Genocide" and object

    Unperson's every object within a list of victims
    """
    for obj in victims:
        print(obj, len(victims))
        unperson(obj)
        
def createGhetto(group: Type[T2]) -> list[T2]:
    """
    Create's a "ghetto" of objects of a given type,
    
    grabs every object of a given type which exists in the inteperter,
    grabs litterally ALL OF THEM, via gc.get_objects()
    """
    return [x for x in gc.get_objects() if isinstance(x, group)]