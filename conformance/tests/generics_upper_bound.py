"""
Tests TypeVars with upper bounds.
"""

# Specification: https://typing.readthedocs.io/en/latest/spec/generics.html#type-variables-with-an-upper-bound

from typing import Sized, TypeVar, assert_type

# > A type variable may specify an upper bound using bound=<type>

T_Good1 = TypeVar("T_Good1", bound=int)  # OK
T_Good2 = TypeVar("T_Good2", bound="ForwardRef | str")  # OK


class ForwardRef: ...


# > <type> itself cannot be parameterized by type variables.

T = TypeVar("T")

T_Bad1 = TypeVar("T_Bad1", bound=list[T])  # Type Error


ST = TypeVar("ST", bound=Sized)


def longer(x: ST, y: ST) -> ST:
    if len(x) > len(y):
        return x
    else:
        return y


assert_type(longer([1], [1, 2]), list[int])
assert_type(longer({1}, {1, 2}), set[int])

# Type checkers that use a join rather than a union (like mypy)
# will produce Collection[int] here instead of list[int] | set[int].
# Both answers are conformant with the spec.
assert_type(longer([1], {1, 2}), list[int] | set[int])

longer(3, 3)  # Type Error


# > An upper bound cannot be combined with type constraints

T_Bad2 = TypeVar("T_Bad2", str, int, bound="int")  # Type Error
