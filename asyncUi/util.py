from typing import Union, cast, Generic, TypeVar, TypeVar, overload, Type, Self
from types import EllipsisType

T = TypeVar('T')
T2 = TypeVar('T2')

__all__ = ('Placeholder')

class Placeholder(Generic[T]):
    def __init__(self, name: str | None = None):
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
Inferable = Union[T, EllipsisType]