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

from typing import Never


from typing import Final, Any, Self



GetT = TypeVar('GetT')
SetT = TypeVar('SetT')

class ReadableProperty(Generic[GetT, T]):
    def __init__(self, getter: Callable[[T], GetT]) -> None:
        self.getter = getter

    @overload
    def __get__(self, instance: T, owner: type[T]) -> GetT: ...
    @overload
    def __get__(self, instance: None, owner: type[T]) -> Self: ...

    def __get__(self, instance: T | None, owner: type[T]) -> Self | GetT: 
        if instance is None:
            return self
        return self.getter(instance)

class WritableProperty(Generic[SetT, T]):
    def __init__(self, setter: Callable[[T, SetT], None]) -> None:
        self.setter = setter
    def __set__(self, instance: T, value: SetT) -> None:
        self.setter(instance, value)

class Property(ReadableProperty[GetT, T], WritableProperty[SetT, T], Generic[GetT, SetT, T]):
    def __init__(self, getter: Callable[[T], GetT], setter: Callable[[T, SetT], None]) -> None:
        ReadableProperty.__init__(self, getter)
        WritableProperty.__init__(self, setter)


class Matrix(Generic[T]):
    def __init__(self) -> None:
        self.data: list[list[T]] = []
        self.rowCount = 0
        self.columnCount = 0
    def __getitem__(self, pos: tuple[int, int]) -> T:
        row, column = pos
        return self.data[row][column]
    def __setitem__(self, pos: tuple[int, int], value: T) -> None:
        row, column = pos
        self.data[row][column] = value 
    def appendRow(self, rowData: Iterable[T]) -> None:
        rowData = list(rowData)
        if len(rowData) != self.rowCount:
            raise ValueError(f'Rows must have the same length(expected {self.rowCount}, got {len(rowData)})')

        self.rowCount += 1
        self.data.append(rowData)
    def appendColumn(self, columnData: Iterable[T]) -> None:
        columnData = list(columnData)
        if len(columnData) != self.columnCount:
            raise ValueError(f'Columns must have the same length(expected {self.columnCount}, got {len(columnData)})')
        
        self.columnCount += 1
        for row, data in zip(self.data, columnData):
            row.append(data)
        
    def rows(self) -> Iterable[list[T]]:
        for row in self.data:
            yield row
        
from math import sqrt
from itertools import count
from typing import Iterable, Iterator
class Primes:
    def __init__(self) -> None:
        self.primes: list[int] = []
        self._primeGen = self._primeGenerator()

    def _primeGenerator(self) -> Iterator[int]:
        num = 2

        while True:
            is_prime = all(num % prime != 0 for prime in self.primes)
            if is_prime:
                self.primes.append(num)
                yield num
            num += 1
    
    def isPrime(self, number: int) -> bool:
        if number in self.primes:
            return True

        maxPrime = sqrt(number)
        for trial in self:
            if trial > maxPrime:
                return True
            if number % trial == 0:
                return False
        
        raise AssertionError("Unreachable")
    __contains__ = isPrime
            
    def __iter__(self) -> Iterator[int]:
        for i in count():
            yield self[i]

    @overload
    def __getitem__(self, item: int) -> int: ...
    @overload
    def __getitem__(self, item: slice) -> list[int]: ...
    def __getitem__(self, item: slice | int) -> list[int] | int: 
        if isinstance(item, int):
            while item >= len(self.primes):
                self.primes.append(next(self._primeGen))
            return self.primes[item]
        else:
            return [self[i] for i in range(item.start, item.stop, item.step)]
    
    def index(self, prime: int) -> int:
        if prime not in self:
            raise ValueError(f'{prime} is not a prime number')

        if prime in self.primes:
            return self.primes.index(prime)
        for i, currentPrime in enumerate(self, len(self.primes)):
            if currentPrime == prime:
                return i   
    
        raise AssertionError("Unreachable")
    
primes = Primes()

from typing import get_type_hints as getTypeHints, Annotated

