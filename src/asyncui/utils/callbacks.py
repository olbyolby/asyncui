from typing import Callable, TypeVar, TypeVarTuple,  Union, Generic

T = TypeVar('T')
Ts = TypeVarTuple('Ts')

Callback = Union['CallbackWrapper[*Ts]', Callable[[*Ts] , None], None]
class CallbackWrapper(Generic[*Ts]):
    def __init__(self, callback: 'Callable[[*Ts], None] | CallbackWrapper[*Ts] | None') -> None:
        if isinstance(callback, CallbackWrapper):
            self.callback = callback.callback #type: ignore
        else:
            self.callback = callback
    def invoke(self, *args: *Ts) -> None:
        if self.callback is not None:
            self.callback(*args)

