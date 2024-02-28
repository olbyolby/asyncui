from typing import ContextManager, TypeVar, Generic
from types import TracebackType

T = TypeVar('T')

__all__ = ['MutableContextManager']
class MutableContextManager(Generic[T]):
    def __init__(self, inital_context: ContextManager[T]):
        self.context = inital_context
        self.value = inital_context.__enter__()


    def changeContext(self, context: ContextManager[T]) -> None:
        self.context.__exit__(None, None, None)
        self.context = context
        self.value = context.__enter__()
    def get_value(self) -> T:
        return self.value


    def __enter__(self) -> None:
        return None
    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None) -> None:
        if self.context is not None:
            self.context.__exit__(exc_type, exc, traceback)