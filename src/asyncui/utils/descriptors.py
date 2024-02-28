from typing import Generic, TypeVar, cast, Self, overload, Union
from types import EllipsisType

T = TypeVar('T')
T2 = TypeVar('T2')

__all__ = ("Inferable", "Placeholder")
class Placeholder(Generic[T]):
    def __init__(self, default: T, name: str | None = None):
        self.name: str | None = name
        self.default = default
    def __set_name__(self, owner: type[T2], name: str) -> None:
        self.name = "_" + name
        self.attr_name = name
    
    @overload
    def __get__(self, instance: None, owner: type[T2]) -> Self: ...
    @overload
    def __get__(self, instance: T2, owner: type[T2]) -> T: ...

    def __get__(self, instance: T2 | None, owner: type[T2]) -> Self | T:
        if instance is None:
            return self
        else:
            assert self.name is not None, "descriptor's name must be set"
            if not hasattr(instance, self.name):
                raise ValueError(f'attribute {self.attr_name} of {instance!r} is not initialized')
            value = cast(T, getattr(instance, self.name))
            return value
    
    def __set__(self, instance: T2, value: T | EllipsisType) -> None:
        assert self.name is not None
        setattr(instance, self.name, value if value is not ... else self.default)
Inferable = Union[T, EllipsisType]