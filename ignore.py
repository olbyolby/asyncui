
from typing import Any, Callable, Type, cast, Protocol

class Test:
    def __init__(self, value: int) -> None:
        self.value = value

class Test2(Protocol):
    value: int
    def __new__(cls, value: int) -> Test:
        return Test(value)

