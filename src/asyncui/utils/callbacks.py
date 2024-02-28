"""
This module defines utilities to make working with callback functions simpler.

Aliases:
    Callback[*Ts] - Used to annotate callback functions, and can be used as the argument to `CallbackWrapper`
Classes:
    CallbackWrapper[*Ts] - A wrapper around a callback function. It can be called via `invoke` and accepts None or other callbackWrappers.
"""
from typing import Callable, TypeVar, TypeVarTuple,  Union, Generic

T = TypeVar('T')
Ts = TypeVarTuple('Ts')

__all__ = ('Callback', 'CallbackWrapper')
Callback = Union['CallbackWrapper[*Ts]', Callable[[*Ts] , None], None]
class CallbackWrapper(Generic[*Ts]):
    """
    A wrapper around a callback function.

    The function can be called via `invoke`, followed by the callback's arguments(given in *Ts).
    The constructor accepts both a normal function, other callbackWrappers, and None.
    If the callback is None, `invoke` will have no effect, and if the callback is callbackWrapper, 
    it's callback will be extracted and used as the callback.
    """
    def __init__(self, callback: 'Callable[[*Ts], None] | CallbackWrapper[*Ts] | None') -> None:
        if isinstance(callback, CallbackWrapper):
            self.callback = callback.callback #type: ignore
        else:
            self.callback = callback
    def invoke(self, *args: *Ts) -> None:
        if self.callback is not None:
            self.callback(*args)

