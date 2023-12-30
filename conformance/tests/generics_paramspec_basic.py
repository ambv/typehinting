"""
Tests basic usage of ParamSpec.
"""

# Specification: https://typing.readthedocs.io/en/latest/spec/generics.html#paramspec-variables

from typing import Any, Callable, Concatenate, ParamSpec, TypeAlias

P = ParamSpec("P")  # OK
WrongName = ParamSpec("NotIt")  # Type error: name inconsistency


# > Valid use locations

TA1: TypeAlias = P  # Type error

TA2: TypeAlias = Callable[P, None]  # OK
TA3: TypeAlias = Callable[Concatenate[int, P], None]  # OK
TA4: TypeAlias = Callable[..., None]  # OK
TA5: TypeAlias = Callable[..., None]  # OK


def func1(x: P) -> P:  # Type error
    ...


def func2(x: Concatenate[int, P]) -> int:  # Type error
    ...


def func3(x: list[P]) -> None:  # Type error
    ...


def func3(x: Callable[[int, str], P]) -> None:  # Type error
    ...


def func4(*args: P, **kwargs: P) -> None:  # Type error
    ...
