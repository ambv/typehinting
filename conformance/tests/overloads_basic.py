"""
Tests the behavior of typing.overload.
"""

# Specification: https://typing.readthedocs.io/en/latest/spec/overload.html#overload

from abc import ABC
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Protocol,
    TypeVar,
    assert_type,
    overload,
)


class Bytes:
    ...

    @overload
    def __getitem__(self, __i: int) -> int:
        ...

    @overload
    def __getitem__(self, __s: slice) -> bytes:
        ...

    def __getitem__(self, __i_or_s: int | slice) -> int | bytes:
        if isinstance(__i_or_s, int):
            return 0
        else:
            return b""


b = Bytes()
assert_type(b[0], int)
assert_type(b[0:1], bytes)
b[""]  # E: no matching overload


T1 = TypeVar("T1")
T2 = TypeVar("T2")
S = TypeVar("S")


@overload
def map(func: Callable[[T1], S], iter1: Iterable[T1]) -> Iterator[S]:
    ...


@overload
def map(
    func: Callable[[T1, T2], S], iter1: Iterable[T1], iter2: Iterable[T2]
) -> Iterator[S]:
    ...


def map(func: Any, iter1: Any, iter2: Any = ...) -> Any:
    pass


# > At least two @overload-decorated definitions must be present.
@overload  # E[func1]
def func1() -> None:  # E[func1]: At least two overloads must be present
    ...


def func1() -> None:
    pass


# > The ``@overload``-decorated definitions must be followed by an overload
# > implementation, which does not include an ``@overload`` decorator. Type
# > checkers should report an error or warning if an implementation is missing.
@overload  # E[func2]
def func2(x: int) -> int:  # E[func2]: no implementation
    ...


@overload
def func2(x: str) -> str:
    ...


# > Overload definitions within stub files, protocols, and abstract base classes
# > are exempt from this check.
class MyProto(Protocol):
    @overload
    def func3(self, x: int) -> int:
        ...


    @overload
    def func3(self, x: str) -> str:
        ...

class MyAbstractBase(ABC):
    @overload
    def func4(self, x: int) -> int:
        ...


    @overload
    def func4(self, x: str) -> str:
        ...


# > If one overload signature is decorated with ``@staticmethod`` or
# > ``@classmethod``, all overload signatures must be similarly decorated. The
# > implementation, if present, must also have a consistent decorator. Type
# > checkers should report an error if these conditions are not met.
class C:
    @overload  # E[func5]
    @staticmethod
    def func5(x: int) -> int:  # E[func5]
        ...

    @overload
    @staticmethod
    def func5(x: str) -> str:  # E[func5]
        ...

    def func5(self, x: int | str) -> int | str:  # E[func5]
        return 1

    @overload  # E[func6]
    @classmethod
    def func6(cls, x: int) -> int:  # E[func6]
        ...

    @overload
    @classmethod
    def func6(cls, x: str) -> str:  # E[func6]
        ...

    def func6(cls, x: int | str) -> int | str:  # E[func6]
        return 1
