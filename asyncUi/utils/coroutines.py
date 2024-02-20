from typing import ParamSpec, Literal, TypeVar, Generator, TypeVarTuple, Callable, Never, Sequence, Iterable
from functools import wraps
from enum import Enum, auto
from numbers import Real
T = TypeVar('T')
T2 = TypeVar('T2')
T3 = TypeVar('T3')
Ts = TypeVarTuple('Ts')
P = ParamSpec('P')

class Sentinals(Enum):
    SkipState = auto()
SkipState = Sentinals.SkipState

def statefulFunction(function: Callable[P, Generator[T | Literal[Sentinals.SkipState], tuple[*Ts], Never]]) -> Callable[P, Callable[[*Ts], T]]:
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Callable[[*Ts], T]:
        generator = function(*args, **kwargs)

        # Prime the generator
        next(generator)
        
        def sender(*args: *Ts) -> T:
            result = generator.send(args)
            while result is Sentinals.SkipState:
                result = next(generator)
            return result

        return sender
    return wrapper
Stateful = Generator[T | Literal[Sentinals.SkipState], tuple[*Ts], Never]

def feed(coroutine: Callable[[T], T2], values: Sequence[T]) -> Iterable[T2]:
    for value in values:
        yield coroutine(value)

NumT = TypeVar("NumT", bound=complex)
@statefulFunction
def accumulate(value: NumT) -> Stateful[NumT, NumT]:
    while True:
        value += (yield value)[0]