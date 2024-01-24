from typing import no_type_check,TypeVarTuple, overload, LiteralString, ContextManager, Self, Generic, TypeVar, Callable, Type, Any, cast, Protocol, Mapping, Iterable, Awaitable, Generator, Final
from types import EllipsisType
import asyncio
from abc import *

T = TypeVar('T')
T2 = TypeVar('T2')
Ts = TypeVarTuple('Ts')

class Placeholder(Generic[T]):
    def __init__(self, name: LiteralString | None = None):
        self.name: str | None = name
    def __set_name__(self, name: str, owner: Type[T2]) -> None:
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
            value = cast(EllipsisType | T, getattr(instance, self.name))
            if value is ...:
                raise ValueError(f'attribute {self.attrName} of {instance!r} is not valid(it is a placeholder)')
            return value
    
    def __set__(self, instance: T2, value: T | EllipsisType) -> None:
        assert self.name is not None
        setattr(instance, self.name, value)


@no_type_check
def partial(func, *args):
    args = list(args)
    if ... not in args:
        return func(*args)
    def _inner(*newargs):
        oldI = len(args)
        for i, arg in enumerate(newargs):
            if arg is ...:
                args.append(arg)
            elif ... in args[0:oldI]:
                args[args.index(...)] = arg
            else:
                args.append(arg)
        return partial(func, *args)
    return _inner

class Test(ABC):
    @abstractmethod
    @property
    def test(self) -> int: pass

class Test2(Test):
    test: int

print(Test2())