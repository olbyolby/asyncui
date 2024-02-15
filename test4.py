# ruff: noqa
import asyncio

import inspect
import ctypes
from types import FrameType
from typing import cast, TypeVar, Any, Iterable, Awaitable
T2 = TypeVar('T2')

def neverNone(var: T2 | None) -> T2:
    if var is None:
        raise ValueError("Unexpected None")
    else:
        return var

class Locals:
    def __init__(self, frame: FrameType | None = None) -> None:
        if frame is None:
            frame = neverNone(neverNone(inspect.currentframe()).f_back)
        super().__setattr__('frame', frame)
    def __getattribute__(self, name: str) -> Any:
        frame = cast(FrameType,super().__getattribute__('frame'))
        if name in frame.f_locals:
            return frame.f_locals[name]
        raise AttributeError(name = name, obj = self)
    def __setattr__(self, name: str, value: Any) -> None:
        frame = cast(FrameType,super().__getattribute__('frame'))
        frame.f_locals[name] = value
        ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(frame), ctypes.c_int(0))
    def __dir__(self) -> set[str]:
        frame = cast(FrameType,super().__getattribute__('frame'))
        return set(frame.f_locals.keys())


async def printLater(f: Awaitable[Any], what: str) -> None:
    await f
    print(what)
def deffer(later: Awaitable[T2]) -> asyncio.Task[T2]:
    return asyncio.ensure_future(later)

async def main() -> None:
    sleeper = asyncio.sleep(1000)
    deffer(printLater(sleeper, "DONE"))

    sleeper_locals = Locals(sleeper.cr_frame)
    sleeper_locals.future.set_value(None)
asyncio.run(main())