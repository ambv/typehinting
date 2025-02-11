**************
Type Narrowing
**************

Python programs often contain symbols that take on multiple types within a
single given scope and that are distinguished by a conditional check at
runtime. For example, here the variable *name* can be either a ``str`` or
``None``, and the ``if name is not None`` narrows it down to just ``str``::

    def maybe_greet(name: str | None) -> None:
        if name is not None:
            print("Hello, " + name)

This technique is called *type narrowing*.
To avoid false positives on such code, type checkers understand
various kinds of conditional checks that are used to narrow types in Python code.
The exact set of type narrowing constructs that a type checker understands
is not specified and varies across type checkers. Commonly understood
patterns include:

* ``if x is not None``
* ``if x``
* ``if isinstance(x, SomeType)``
* ``if callable(x)``

In addition to narrowing local variables, type checkers usually also support
narrowing instance attributes and sequence members, such as
``if x.some_attribute is not None`` or ``if x[0] is not None``, though the exact
conditions for this behavior differ between type checkers.

Consult your type checker's documentation for more information on the type
narrowing constructs it supports.

The type system also includes two ways to create *user-defined* type narrowing
functions: :py:data:`typing.TypeIs` and :py:data:`typing.TypeGuard`. These
are useful if you want to reuse a more complicated check in multiple places, or
you use a check that the type checker doesn't understand. In these cases, you
can define a ``TypeIs`` or ``TypeGuard`` function to perform the check and allow type checkers
to use it to narrow the type of a variable. Between the two, ``TypeIs`` usually
has the more intuitive behavior, so we'll talk about it more; see
:ref:`below <guide-type-narrowing-typeis-typeguard>` for a comparison.

How to use ``TypeIs`` and ``TypeGuard``
---------------------------------------

A ``TypeIs`` function takes a single argument and is annotated as returning
``TypeIs[T]``, where ``T`` is the type that you want to narrow to. The function
must return ``True`` if the argument is of type ``T``, and ``False`` otherwise.
The function can then be used in ``if`` checks, just like you would use ``isinstance()``.
For example::

    from typing import Literal, TypeIs

    type Direction = Literal["N", "E", "S", "W"]

    def is_direction(x: str) -> TypeIs[Direction]:
        return x in {"N", "E", "S", "W"}

    def maybe_direction(x: str) -> None:
        if is_direction(x):
            print(f"{x} is a cardinal direction")
        else:
            print(f"{x} is not a cardinal direction")

A ``TypeGuard`` function looks similar and is used in the same way, but the
type narrowing behavior is different, as dicussed in :ref:`the section below <guide-type-narrowing-typeis-typeguard>`.

Depending on the version of Python you are running, you will be able to
import ``TypeIs`` and ``TypeGuard`` either from the standard library :py:mod:`typing`
module or from the third-party ``typing_extensions`` module:

* ``TypeIs`` is in ``typing`` starting from Python 3.13 and in ``typing_extensions``
  starting from version 4.10.0.
* ``TypeGuard`` is in ``typing`` starting from Python 3.10 and in ``typing_extensions``
  starting from version 3.10.0.0.


Writing a correct ``TypeIs`` function
-------------------------------------

A ``TypeIs`` function allows you to override your type checker's type narrowing
behavior. This is a powerful tool, but it can be dangerous because an incorrectly
written ``TypeIs`` function can lead to unsound type checking, and type checkers
cannot detect such errors.

For a function returning ``TypeIs[T]`` to be correct, it must return ``True`` if and only if
the argument is of type ``T``, and ``False`` otherwise. If this condition is
not met, the type checker may infer incorrect types.

Below are some examples of correct and incorrect ``TypeIs`` functions::

    from typing import TypeIs

    # Correct
    def is_int(x: object) -> TypeIs[int]:
        return isinstance(x, int)

    # Incorrect: does not return True for all ints
    def is_positive_int(x: object) -> TypeIs[int]:
        return isinstance(x, int) and x > 0

    # Incorrect: returns True for some non-ints
    def is_real_number(x: object) -> TypeIs[int]:
        return isinstance(x, (int, float))

This function demonstrates some errors that can occur when using a poorly written
``TypeIs`` function. These errors are not detected by type checkers::

    def caller(x: int | str, y: int | float) -> None:
        if is_positive_int(x):  # narrowed to int
            print(x + 1)
        else:  # narrowed to str (incorrectly)
            print("Hello " + x)  # runtime error if x is a negative int

        if is_real_number(y):  # narrowed to int
            # Because of the incorrect TypeIs, this branch is taken at runtime if
            # y is a float.
            print(y.bit_count())  # runtime error: this method exists only on int, not float
        else:  # narrowed to float (though never executed at runtime)
            pass

Here is an example of a correct ``TypeIs`` function for a more complicated type::

    from typing import TypedDict, TypeIs

    class Point(TypedDict):
        x: int
        y: int

    def is_point(obj: object) -> TypeIs[Point]:
        return (
            isinstance(obj, dict)
            and all(isinstance(key, str) for key in obj)
            and isinstance(obj.get("x"), int)
            and isinstance(obj.get("y"), int)
        )

.. _`guide-type-narrowing-typeis-typeguard`:

``TypeIs`` and ``TypeGuard``
----------------------------

:py:data:`typing.TypeIs` and :py:data:`typing.TypeGuard` are both tools for narrowing the type of a variable
based on a user-defined function. Both can be used to annotate functions that take an
argument and return a boolean depending on whether the input argument is compatible with
the narrowed type. These function can then be used in ``if`` checks to narrow the type
of a variable.

``TypeIs`` usually has the more intuitive behavior, but it
introduces more restrictions. ``TypeGuard`` is the right tool to use if:

* You want to narrow to a type that is not :term:`assignable` to the input type, for example
  from ``list[object]`` to ``list[int]``.  ``TypeIs`` only allows narrowing between
  compatible types.
* Your function does not return ``True`` for all input values that are members of
  the narrowed type. For example, you could have a ``TypeGuard[int]`` that returns ``True``
  only for positive integers.

``TypeIs`` and ``TypeGuard`` differ in the following ways:

* ``TypeIs`` requires the narrowed type to be :term:`assignable` to the input type, while
  ``TypeGuard`` does not.
* When a ``TypeGuard`` function returns ``True``, type checkers narrow the type of the
  variable to exactly the ``TypeGuard`` type. When a ``TypeIs`` function returns ``True``,
  type checkers can infer a more precise type combining the previously known type of the
  variable with the ``TypeIs`` type. (This is known as an "intersection type".)
* When a ``TypeGuard`` function returns ``False``, type checkers cannot narrow the type of
  the variable at all. When a ``TypeIs`` function returns ``False``, type checkers can narrow
  the type of the variable to exclude the ``TypeIs`` type.

This behavior can be seen in the following example::

    from typing import TypeGuard, TypeIs, reveal_type, final

    class Base: ...
    class Child(Base): ...
    @final
    class Unrelated: ...

    def is_base_typeguard(x: object) -> TypeGuard[Base]:
        return isinstance(x, Base)

    def is_base_typeis(x: object) -> TypeIs[Base]:
        return isinstance(x, Base)

    def use_typeguard(x: Child | Unrelated) -> None:
        if is_base_typeguard(x):
            reveal_type(x)  # Base
        else:
            reveal_type(x)  # Child | Unrelated

    def use_typeis(x: Child | Unrelated) -> None:
        if is_base_typeis(x):
            reveal_type(x)  # Child
        else:
            reveal_type(x)  # Unrelated

There are also cases beyond just mutability. In some cases, it may not be
possible to narrow a type fully from information available to the ``TypeIs``
function. In such cases, raising an error is the only possible option, as you
have neither enough information to confirm or deny a type narrowing operation.
(Note: returning false (denying) results in unsafe negative narrowing in this
case) This is most likely to occur with narrowing of generics.

To see why, we can look at the following example::

    from typing_extensions import TypeVar, TypeIs
    from typing import Generic

    X = TypeVar("X", str, int, str | int, covariant=True, default=str | int)

    class A(Generic[X]):
        def __init__(self, i: X, /):
            self._i: X = i

        @property
        def i(self) -> X:
            return self._i


    class B(A[X], Generic[X]):
        def __init__(self, i: X, j: X, /):
            super().__init__(i)
            self._j: X = j

        @property
        def j(self) -> X:
            return self._j

    def possible_problem(x: A) -> TypeIs[A[int]]:
        return isinstance(x.i, int)

    def possible_correction(x: A) -> TypeIs[A[int]]:
        if type(x) is A:
            # only narrow cases we know about
            return isinstance(x.i, int)
        raise TypeError(
            f"Refusing to narrow Genenric type {type(x)!r}"
            f"from function that only knows about {A!r}"
        )

Because it is possible to attempt to narrow B,
but A does not have appropriate information about B
(or any other unknown subclass of A!) it's not possible to safely narrow
in either direction. The general rule for generics is that if you do not know
all the places a generic class is generic and do not check enough of them to be
absolutely certain, you cannot return True, and if you do not have a definitive
counter example to the type to be narrowed to you cannot return False.
In practice, if soundness is prioritized over an unsafe narrowing,
not knowing what you don't know is solvable by either
erroring out when neither return option is safe, or by making the class to be
narrowed final to avoid such a situation.

Safety and soundness
--------------------

While type narrowing is important for typing real-world Python code, many
forms of type narrowing are unsafe. Type checkers
attempt to limit type narrowing in a way that minimizes unsafety while remaining
useful, but not all safety violations can be detected.

One example of this tradeoff building off of TypeIs

If you trust that users implementing the Sequence Protocol are doing so in a
way that is safe to iterate over, and will not be mutated for the duration
you are relying on it; then while the following function can never be fully
sound, full soundness is not necessarily easier or better for your use::

    def useful_unsoundness(s: Sequence[object]) -> TypeIs[Sequence[int]]:
        return all(isinstance(i, int) for i in s)

However, many cases of this sort can be extracted for safe use with an
alternative construction if soundness is of a high priority,
and the cost of a copy is acceptable::

    def safer(s: Sequence[object]) -> Sequence[int]:
        ret = tuple(i for i in s if isinstance(i, int))
        if len(ret) != len(s):
            raise TypeError
        return ret


``isinstance()`` and ``issubclass()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While the exact behavior is not standardized, type checkers usually support
narrowing terms based on calls to ``isinstance()`` and ``issubclass()``. However,
these functions have complex runtime behavior that type checkers cannot fully
capture: they call the :py:meth:`__instancecheck__` and :py:meth:`__subclasscheck__`
special methods, which may include arbitrarily complex logic.

This affects some parts of the standard library that rely on these methods.
:py:class:`abc.ABC` allows registration of subclasses using the ``.register()`` method,
but type checkers usually will not recognize this method. :ref:`Runtime-checkable
protocols <runtime-checkable>` support runtime ``isinstance()`` checks, but their
behavior does not exactly match the type system (for example, the types of method
parameters are not checked).

Incorrect ``TypeIs`` and ``TypeGuard`` functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both ``TypeIs`` and ``TypeGuard`` rely on the user writing a function that
returns whether an object is of a particular type. However, the type checker
does not validate whether the function actually behaves as expected. If it
does not, the type checker's narrowing behavior will not match what happens
at runtime.::

    from typing import TypeIs

    def is_str(x: object) -> TypeIs[str]:
        return True

    def takes_str_or_int(x: str | int) -> None:
        if is_str(x):
            print(x + " is a string")  # runtime error

To avoid this problem, every ``TypeIs`` and ``TypeGuard`` function should be
carefully reviewed and tested.

Unsound ``TypeGuard`` narrowing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unlike ``TypeIs``, ``TypeGuard`` can narrow to a type that is not a subtype of the
original type. This allows for unsafe behavior with invariant data structures::

    from typing import Any, TypeGuard

    def is_int_list(x: list[Any]) -> TypeGuard[list[int]]:
        return all(isinstance(i, int) for i in x)

    def maybe_mutate_list(x: list[Any]) -> None:
        if is_int_list(x):
            x.append(0)  # OK, x is narrowed to list[int]

    def takes_bool_list(x: list[bool]) -> None:
        maybe_mutate_list(x)
        reveal_type(x)  # list[bool]
        assert all(isinstance(i, bool) for i in x)  # fails at runtime

    takes_bool_list([True, False])

To avoid this problem, use ``TypeIs`` instead of ``TypeGuard`` where possible.
If you must use ``TypeGuard``, avoid narrowing across incompatible types.
Prefer using covariant, immutable types in parameter annotations (e.g.,
``Sequence`` or ``Iterable`` instead of ``list``). If you do this, it is more likely
that you'll be able to use ``TypeIs`` to implement your type narrowing functions.

Invalidated assumptions
~~~~~~~~~~~~~~~~~~~~~~~

One category of safety issues relates to the fact that type narrowing relies
on a condition that was established at one point in the code and is then relied
on later: we first check ``if x is not None``, then rely on ``x`` not being ``None``.
However, in the meantime other code may have run (for example, in another thread,
another coroutine, or simply some code that was invoked by a function call) and
invalidated the earlier condition.

Such problems are most likely when narrowing is performed on elements of mutable
objects, but it is possible to construct unsafe examples even using only narrowing
of local variables::

    def maybe_greet(name: str | None) -> None:
        def set_it_to_none():
            nonlocal name
            name = None

        if name is not None:
            set_it_to_none()
            # fails at runtime, no error in current type checkers
            print("Hello " + name)

    maybe_greet("Guido")

A more realistic example might involve multiple coroutines mutating a list::

    import asyncio
    from typing import Sequence, TypeIs

    def is_int_sequence(x: Sequence[object]) -> TypeIs[Sequence[int]]:
        return all(isinstance(i, int) for i in x)

    async def takes_seq(x: Sequence[int | None]):
        if is_int_sequence(x):
            await asyncio.sleep(2)
            print("The total is", sum(x))  # fails at runtime

    async def takes_list(x: list[int | None]):
        t = asyncio.create_task(takes_seq(x))
        await asyncio.sleep(1)
        x.append(None)
        await t

    if __name__ == "__main__":
        lst: list[int | None] = [1, 2, 3]
        asyncio.run(takes_list(lst))

These issues unfortunately cannot be fully detected by the current
Python type system. (An example of a different programming language that
does solve this problem is Rust, which uses a system called
`ownership <https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html>`__.)
To avoid such issues, avoid using type narrowing on objects that are mutated
from other parts of the code.


See also
--------

* Type checker documentation on type narrowing

  * `Mypy <https://mypy.readthedocs.io/en/stable/type_narrowing.html>`__
  * `Pyright <https://microsoft.github.io/pyright/#/type-concepts-advanced?id=type-narrowing>`__

* PEPs related to type narrowing. These contain additional discussion
  and motivation for current type checker behaviors.

  * :pep:`647` (introduced ``TypeGuard``)
  * (*withdrawn*) :pep:`724` (proposed change to ``TypeGuard`` behavior)
  * :pep:`742` (introduced ``TypeIs``)
