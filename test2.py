from typing import overload, TypeVar, Protocol, Generic, Type, cast, Self
from types import TracebackType

class ContextHandler(Protocol):
    def __enter__(self) -> Self:
        ...
    def __exit__(self, excType: Type[BaseException] | None, excValue: BaseException | None, traceback: TracebackType | None) -> None:
        ...
T = TypeVar('T', bound=ContextHandler)
T2 = TypeVar('T2')
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
        value = cast(T, getattr(instance, self.privateName))
        value.__exit__(None, None, None)
        delattr(instance, self.privateName)

