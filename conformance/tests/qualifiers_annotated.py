"""
Tests the typing.Annotated special form.
"""

# Specification: https://typing.readthedocs.io/en/latest/spec/qualifiers.html#annotated

# > The first argument to Annotated must be a valid type

from dataclasses import InitVar, dataclass
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    Final,
    Literal,
    NotRequired,
    Required,
    TypeAlias,
    TypeVar,
    TypedDict,
    Union,
)

T = TypeVar("T")


Good1: Annotated[Union[int, str], ""]
Good2: Annotated[int | None, ""]
Good3: Annotated[list[int], ""]
Good4: Annotated[Any, ""]
Good5: Annotated[tuple[int, ...] | list[int], ""]
Good6: Annotated[Callable[..., int], ""]
Good7: Annotated["int | str", ""]
Good8: Annotated[list["int | str"], ""]
Good9: Annotated[Literal[3, 4, 5, None], x := 3]


async def func3() -> None:
    Good10: Annotated[str, await func3()]


Bad1: Annotated[[int, str], ""]  # Type error: invalid type expression
Bad2: Annotated[((int, str),), ""]  # Type error: invalid type expression
Bad3: Annotated[[int for i in range(1)], ""]  # Type error: invalid type expression
Bad4: Annotated[{"a": "b"}, ""]  # Type error: invalid type expression
Bad5: Annotated[(lambda: int)(), ""]  # Type error: invalid type expression
Bad6: Annotated[[int][0], ""]  # Type error: invalid type expression
Bad7: Annotated[int if 1 < 3 else str, ""]  # Type error: invalid type expression
Bad8: Annotated[var1, ""]  # Type error: invalid type expression
Bad9: Annotated[True, ""]  # Type error: invalid type expression
Bad10: Annotated[1, ""]  # Type error: invalid type expression
Bad11: Annotated[list or set, ""]  # Type error: invalid type expression
Bad12: Annotated[f"{'int'}", ""]  # Type error: invalid type expression


# > Multiple type annotations are supported (Annotated supports variadic arguments):

Multi1: Annotated[int | str, 3, ""]
Multi2: Annotated[int | str, 3, "", lambda x: x, max(1, 2)]

# > Annotated must be called with at least two arguments ( Annotated[int] is not valid)

Bad13: Annotated[int]  # Type error: requires at least two arguments


# > Annotated types can be nested

Nested1: list[Annotated[dict[str, Annotated[str, ""]], ""]]
Nested2: Annotated[list[Annotated[dict[str, Annotated[Literal[1, 2, 3], ""]], ""]], ""]


# > Annotated is not type compatible with type or type[T]
SmallInt: TypeAlias = Annotated[int, ""]

not_type1: type[Any] = Annotated[int, ""]  # Type Error
not_type2: type[Any] = SmallInt  # Type error


def func4(x: type[T]) -> T:
    return x()


func4(Annotated[str, ""])  # Type Error
func4(SmallInt)  # Type Error


# > An attempt to call Annotated (whether parameterized or not) should be
# > treated as a type error by type checkers.

Annotated()  # Type Error
Annotated[int, ""]()  # Type Error
SmallInt(1)  # Type Error


class ClassA:
    a: ClassVar[Annotated[int, ""]] = 1
    b: Annotated[ClassVar[int], ""] = 1
    c: Final[Annotated[int, ""]] = 1
    d: Annotated[Final[int], ""] = 1


@dataclass
class ClassB:
    a: InitVar[Annotated[int, ""]]
    b: Annotated[InitVar[int], ""]


class ClassC(TypedDict):
    a: Annotated[Required[int], ""]
    b: Required[Annotated[int, ""]]
    c: Annotated[NotRequired[int], ""]
    d: NotRequired[Annotated[int, ""]]


TA1: TypeAlias = Annotated[int | str, ""]
TA2 = Annotated[Literal[1, 2], ""]

T = TypeVar("T")

TA3 = Annotated[T, ""]
