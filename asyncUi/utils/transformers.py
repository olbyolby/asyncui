from __future__ import annotations
from typing import TypeVar, Generic, Callable, overload, Iterable, TypeVarTuple
from functools import wraps, update_wrapper


__all__ = [
    'Transformer',
    'transformerFactory'
]
T = TypeVar('T')
T2 = TypeVar('T2')
T3 = TypeVar('T3')
Ts = TypeVarTuple('Ts')

class Transformer(Generic[T, T2]):
    """
    A wrapper for functions that transform values in the form y = f(x), adding many useful and mathmatical operations

    Methods:
        compose(other) - compose 2 transformers, f.compose(g) == lambda x: f(g(x))
        feed(values) - feed a sequence of values to the fransformer, f.feed(values) == (f(value) for value in values)

    Operators:
        __call__(x) f(x) - invoke the transformer and return the transformed result
        __matmul__(x) f @ x - either transform every x with self or compose x with self, depending on type of x. f @ g == f.compose(g), f @ [1,2,3] == f.feed([1,2,3])
        __rrshift__(x) x >> f - apply self to x, x >> f == f(x), and x >> g >> f == f(g(x))

    Constructors:
        __init__(f) - create a new transformer, using f as the transform function
    """
    def __init__(self, transformer: Callable[[T], T2]) -> None:
        self.transformer = transformer
        update_wrapper(self, transformer)
    def __call__(self, value: T) -> T2:
        return self.transformer(value)
    
    def feed(self, values: Iterable[T]) -> Iterable[T2]:
        """
        Feed a sequence of values to the transformer, and return them, f.feed(values) == (f(value) for value in values)
        NOTE: returns a lazily evaluated generator, so if you want a list, use list(f.feed(values))
        """
        for value in values:
            yield self(value)
    def compose(self, other: Transformer[T3, T]) -> Transformer[T3, T2]:
        """
        Compose a transformer with another transformer, and return the new transformer, f @ g == lambda x: f(g(x))

        TODO: Add some naming scheme to the returned value
        """
        return Transformer(lambda x: self(other(x)))
    
    @overload
    def __matmul__(self, other: Transformer[T3, T]) -> Transformer[T3, T2]: ...
    @overload
    def __matmul__(self, other: Iterable[T]) -> Iterable[T2]: ...
    
    def __matmul__(self, other: Transformer[T3, T] | Iterable[T]) -> Transformer[T3, T2] | Iterable[T2]:
        """
        The @ operator, or f @ x. If x is an iterable, returns f.feed(x), if x is a transformer, returns f.compose(x)

        Does ether composition or application of a transformer.
        If other is another transformer, they will be coposed together using self.compose(other),
        if other is an iterable, self will be allpied to everything in other via self.feed(other)
        """
        if isinstance(other, Transformer):
            return self.compose(other)
        elif isinstance(other, Iterable):
            return self.feed(other)
        else:
            return NotImplemented
        
    def __rrshift__(self, value: T) -> T2:
        """The >> operator, speficly value >> self. Is equivlent to self(value), also allows chaining via value >> transformA >> transformB >> etc"""
        return self(value)
        
def transformerFactory(function: Callable[[*Ts], Callable[[T], T2]]) -> Callable[[*Ts], Transformer[T, T2]]:
    """
    Convert a function which returns functions into a function which returns transformers, g = f(*xs), y = g(x)

    Primarily created to use with 'utils.coroutines` and stateful functions.
    """
    @wraps(function)
    def wrapper(*args: *Ts) -> Transformer[T, T2]:
        return Transformer(function(*args))
    return wrapper

