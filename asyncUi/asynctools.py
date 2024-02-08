import asyncio
from typing import Callable, TypeVar, TypeVarTuple, ParamSpec, Generic

P = ParamSpec('P')
T = TypeVar('T')
Ts = TypeVarTuple('Ts')


class Event(Generic[*Ts]):
    def __init__(self) -> None:
        self.handlers: list[Callable[[*Ts], None]] = []
    
    def notify(self, *data: *Ts) -> None:
        for handler in [*self.handlers]:
            handler(*data)
    
    def registerListener(self, listener: Callable[[*Ts], None]) -> None:
        self.handlers.append(listener)
    def unregisterListener(self, listener: Callable[[*Ts], None]) -> None:
        self.handlers.remove(listener)
    