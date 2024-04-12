"""
Tests the evaluation of calls to constructors when the type is type[T].
"""

# Specification: https://typing.readthedocs.io/en/latest/spec/constructors.html#constructor-calls-for-type-t

# > When a value of type type[T] (where T is a concrete class or a type
# > variable) is called, a type checker should evaluate the constructor
# > call as if it is being made on the class T.

from typing import Self, TypeVar


T = TypeVar("T")


class Meta1(type):
    # Ignore possible errors related to incompatible override
    def __call__(cls: type[T], x: int, y: str) -> T:  # type: ignore
        return type.__call__(cls)


class Class1(metaclass=Meta1):
    def __new__(cls, *args, **kwargs) -> Self:
        return super().__new__(*args, **kwargs)


def func1(cls: type[Class1]):
    Class1(x=1, y="")  # OK
    Class1()  # E


class Class2:
    def __new__(cls, x: int, y: str) -> Self:
        return super().__new__(cls)


def func2(cls: type[Class2]):
    Class2(x=1, y="")  # OK
    Class2()  # E


class Class3:
    def __init__(self, x: int, y: str) -> None:
        pass


def func3(cls: type[Class3]):
    Class3(x=1, y="")  # OK
    Class3()  # E
