"""
Tests "type promotions" for float and complex when they appear in annotations.
"""

from typing import assert_type

# Specification: https://typing.readthedocs.io/en/latest/spec/special-types.html#special-cases-for-float-and-complex

v1: int = 1
v2: float = 1
v3: float = v1
v4: complex = 1.2
v4 = 1


def func1(f: float) -> int:
    f.numerator  # E: attribute exists on int but not float

    if isinstance(f, float):
        f.hex()  # OK (attribute exists on float but not int)
        return 1
    else:
        assert_type(f, int)
        # Make sure type checkers don't treat this branch as unreachable
        # and skip checking it.
        return "x"  # E


def func2(x: int) -> float:
    if x == 0:
        return 1
    elif x == 1:
        return 1j  # E
    elif x > 10:
        return x
    else:
        return 1.0
