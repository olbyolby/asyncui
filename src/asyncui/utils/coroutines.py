from __future__ import annotations
from typing import ParamSpec, Literal, TypeVar, Generator, TypeVarTuple, Callable, Never, Iterable
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
    """
    A wrapper to convert a generator into a stateful function.    
        
    This essentially wraps the .send method of a generator, exposing it like a normal function.
    Arguments are passed as a tuple thorugh the .send method, and the yield value is used as the function's return value.
    Usecases include data transformations, iteration, and graphics alignment.

    Usage:
        When a stateful function is created, it is initalized with `generator.send(None)`,
        after which the generator is expected to yield `SkipState`. 

        After which, when the function is called, it's arguments will be sent to the generator
        via `generator.send`, and are passed as a tuple of args. 
        >>> `x, y, z, *args = yield SkipState` # Gets the first set of function arguments

        The next return value which the generator yields will be used as the stateful function's return value.
        >>> `*args = yield 4` # Gets the next set of function arguments and returns a value of 4
        SkipState is a special case, if a generator yields it after the first iteration, it will be ran again via
        `next(generator)` until a different value is returned.        
    
    Example:
        @statefulFunction
        def runningAverage() -> Stateful[float, float]:
            """" keep track of an average over time""""
            #Every stateful function should yield SkipState on the first iteration, to get the first arguments to it
            total, = yield SkipState # The first arguments are passed here
            iterations = 0
            while True:
                next_value, = yield total / iterations # The yield value will be the returned value
                total += next_value
                iterations += 1
                
        average = runningAverage() # Creates an instance of the stateful function
        while True:
            #print the average as each grade is entered
            new_grade = int(input("Enter the next grade: "))
            print("Current average: ", average(new_grade)) # Invokes it. It then adds new_grade and returns the new average
    """
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Callable[[*Ts], T]:
        generator = function(*args, **kwargs)

        # Prime the generator
        try: 
            if next(generator) is not SkipState:
                raise ValueError("stateful function must yield SkipState on it's first iteration(Maybe you forgot `yield SkipState`?)")
        except NotImplementedError as e:
            raise RuntimeError("stateful function generator stoped on first iteration(Maybe you forgot a while True?)") from e
        
        def sender(*args: *Ts) -> T:
            try:
                result = generator.send(args)
                while result is Sentinals.SkipState:
                    result = next(generator)
                return result
            except NotImplementedError as e:
                raise RuntimeError("Stateful function generator is not allowed to stop") from e

        return sender
    return wrapper


def feed(coroutine: Callable[[T], T2], values: Iterable[T]) -> Iterable[T2]:
    for value in values:
        yield coroutine(value)



@statefulFunction
def accumulate(value: int) -> Stateful[int, int]:
    """
    Accumulates a value after each iteration, returning the total up to the last iteration.
    
    NOTE: The total is up to the last iteration, NOT including the current iteration. 
          So, if it's intialized to 4, `accumulater(5)` will return 4, and next time return 9

    Example:
        value = accumulate(0)
        print(value(10)) # Since 0 was the initial value, prints '0'
        print(value(50)) # Last time 10 was added, so now it adds that to 0, printing '10'.
        print(value(5))  # Last time 50 was added, so it prints '60', 5 will be added next time.
        print(value(0))  # Now 5 is added, printing '65'. This pattern continues for ever 
    """
    next_value, = yield SkipState
    while True:
        next_value, value = (yield value)[0], value + next_value

@statefulFunction
def total(value: int = 0) -> Stateful[int, int]:
    """
    Keeps a running total

    Very similar to `accumulate`, except it includes the current iteration.
    So `total(0)(5)` returns 5, but `accumulate(0)(10)` returns 0
    """
    value += (yield SkipState)[0]
    while True:
        value += (yield value)[0]

