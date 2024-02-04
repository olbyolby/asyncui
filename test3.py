from typing import TypeVar, TypeVarTuple, Generic, Callable, Sequence, Iterable, Generator, no_type_check, Any, overload, Union, Protocol
from types import EllipsisType



T = TypeVar('T')
T2 = TypeVar('T2')
Ts = TypeVarTuple('Ts')

def valueIndex(data: Iterable[T | T2], value: T2) -> Generator[int, None, None]:
    for i, dataValue in enumerate(data):
        if dataValue == value:
            yield i

class PartialCall(Generic[T]):
    def __init__(self, function: Callable[..., T], *args: EllipsisType | Any) -> None:
        self.function = function
        self.args = args
    def __call__(self, *args: Any | EllipsisType) -> 'Any':
        filledArgs = list(self.args)

        for i, arg in zip(valueIndex(self.args, ...), args):
            filledArgs[i] = arg
        
        if ... in filledArgs:
            return PartialCall(self.function, *filledArgs)
        else:
            return self.function(*filledArgs)


PartialCall(print, ..., ..., ..., 4, ...)(..., 2, ..., 5)(1, 3)

class BoundClassInstanceMethod(Generic[T, *Ts, T2]):
    def __init__(self, cls: type[T], instance: T, function: Callable[[type[T], T, *Ts], T2]) -> None:
        self.cls = cls
        self.instance = instance
        self.function = function
    def __call__(self, *args: *Ts) -> T2:
        return self.function(self.cls, self.instance, *args)
class PartallyBoundClassInstanceMethod(Generic[T, *Ts, T2]):
    def __init__(self, cls: type[T], function: Callable[[type[T], T, *Ts], T2]):
        self.cls = cls
        self.function = function
    def __call__(self, instance: T, *args: *Ts) -> T2:
        return self.function(self.cls, instance, *args)
class ClassInstanceMethod(Generic[T, *Ts, T2]):
    def __init__(self, function: Callable[[type[T], T, *Ts], T2]) -> None:
        self.function = function
    @overload
    def __get__(self, instance: T, owner: type[T]) -> Callable[[*Ts], T2]: ...
    @overload
    def __get__(self, instance: None, owner: type[T]) -> Callable[[T, *Ts], T2]: ...

    def __get__(self, instance: None | T, owner: type[T]) -> Callable[[*Ts], T2] | Callable[[T, *Ts], T2]:
        if instance is None:
            return PartallyBoundClassInstanceMethod(owner, self.function)
        else:
            return BoundClassInstanceMethod(owner, instance, self.function)
        

def forceCopy(instance: T) -> T:
    newInstance = object.__new__(type(instance))
    vars(newInstance).update(vars(instance))
    return newInstance

