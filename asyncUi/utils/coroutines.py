from __future__ import annotations
from typing import ParamSpec, Literal, TypeVar, Generator, TypeVarTuple, Callable, Never, Iterable, Generic, overload
from functools import wraps
from enum import Enum, auto

T = TypeVar('T')
T2 = TypeVar('T2')
T3 = TypeVar('T3')
Ts = TypeVarTuple('Ts')
P = ParamSpec('P')

class Sentinals(Enum):
    SkipState = auto()
SkipState = Sentinals.SkipState

Stateful = Generator[T | Literal[Sentinals.SkipState], tuple[*Ts], Never]
def statefulFunction(function: Callable[P, Generator[T | Literal[Sentinals.SkipState], tuple[*Ts], Never]]) -> Callable[P, Callable[[*Ts], T]]:
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Callable[[*Ts], T]:
        generator = function(*args, **kwargs)

        # Prime the generator
        if next(generator) is not SkipState:
            raise ValueError("stateful function must yield SkipState on it's first iteration!")
        
        def sender(*args: *Ts) -> T:
            result = generator.send(args)
            while result is Sentinals.SkipState:
                result = next(generator)
            return result

        return sender
    return wrapper


def feed(coroutine: Callable[[T], T2], values: Iterable[T]) -> Iterable[T2]:
    for value in values:
        yield coroutine(value)



@statefulFunction
def accumulate(value: int) -> Stateful[int, int]:
    next_value, = yield SkipState
    while True:
        next_value, value = (yield value)[0], value + next_value