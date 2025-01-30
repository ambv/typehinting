.. _`overload`:

``Overloads``
=============

In Python, it is common for callable objects to be polymorphic, meaning
they accept different types of arguments. It is also common for such
callables to return different types depending on the arguments passed to
them. Overloads provide a way to describe the accepted input signatures
and corresponding return types.


Overload definitions
^^^^^^^^^^^^^^^^^^^^

The ``@overload`` decorator allows describing functions and methods
that support multiple different combinations of argument types. This
pattern is used frequently in builtin modules and types. For example,
the ``__getitem__()`` method of the ``bytes`` type can be described as
follows::

  from typing import overload

  class bytes:
      ...
      @overload
      def __getitem__(self, i: int) -> int: ...
      @overload
      def __getitem__(self, s: slice) -> bytes: ...

This description is more precise than would be possible using unions,
which cannot express the relationship between the argument and return
types::

  class bytes:
      ...
      def __getitem__(self, a: int | slice) -> int | bytes: ...

Another example where ``@overload`` comes in handy is the type of the
builtin ``map()`` function, which takes a different number of
arguments depending on the type of the callable::

  from typing import TypeVar, overload
  from collections.abc import Callable, Iterable, Iterator

  T1 = TypeVar('T1')
  T2 = TypeVar('T2')
  S = TypeVar('S')

  @overload
  def map(func: Callable[[T1], S], iter1: Iterable[T1]) -> Iterator[S]: ...
  @overload
  def map(func: Callable[[T1, T2], S],
          iter1: Iterable[T1], iter2: Iterable[T2]) -> Iterator[S]: ...
  # ... and we could add more items to support more than two iterables

Note that we could also easily add items to support ``map(None, ...)``::

  @overload
  def map(func: None, iter1: Iterable[T1]) -> Iterable[T1]: ...
  @overload
  def map(func: None,
          iter1: Iterable[T1],
          iter2: Iterable[T2]) -> Iterable[tuple[T1, T2]]: ...

Uses of the ``@overload`` decorator as shown above are suitable for
stub files. In regular modules, a series of ``@overload``-decorated
definitions must be followed by exactly one
non-``@overload``-decorated definition (for the same function/method).
The ``@overload``-decorated definitions are for the benefit of the
type checker only, since they will be overwritten by the
non-``@overload``-decorated definition, while the latter is used at
runtime but should be ignored by a type checker. At runtime, calling
an ``@overload``-decorated function directly will raise
``NotImplementedError``. Here's an example of a non-stub overload
that can't easily be expressed using a union or a type variable::

  @overload
  def utf8(value: None) -> None:
      pass
  @overload
  def utf8(value: bytes) -> bytes:
      pass
  @overload
  def utf8(value: unicode) -> bytes:
      pass
  def utf8(value):
      <actual implementation>

A constrained ``TypeVar`` type can sometimes be used instead of
using the ``@overload`` decorator. For example, the definitions
of ``concat1`` and ``concat2`` in this stub file are equivalent::

  from typing import TypeVar

  AnyStr = TypeVar('AnyStr', str, bytes)

  def concat1(x: AnyStr, y: AnyStr) -> AnyStr: ...

  @overload
  def concat2(x: str, y: str) -> str: ...
  @overload
  def concat2(x: bytes, y: bytes) -> bytes: ...

Some functions, such as ``map`` or ``bytes.__getitem__`` above, can't
be represented precisely using type variables. We
recommend that ``@overload`` is only used in cases where a type
variable is not sufficient.

Another important difference between type variables such as ``AnyStr``
and using ``@overload`` is that the prior can also be used to define
constraints for generic class type parameters. For example, the type
parameter of the generic class ``typing.IO`` is constrained (only
``IO[str]``, ``IO[bytes]`` and ``IO[Any]`` are valid)::

  class IO(Generic[AnyStr]): ...


Invalid overload definitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Type checkers should enforce the following rules for overload definitions.

At least two ``@overload``-decorated definitions must be present. If only
one is present, an error should be reported.

The ``@overload``-decorated definitions must be followed by an overload
implementation, which does not include an ``@overload`` decorator. Type
checkers should report an error or warning if an implementation is missing.
Overload definitions within stub files, protocols, and on abstract methods
within abstract base classes are exempt from this check.

If one overload signature is decorated with ``@staticmethod`` or
``@classmethod``, all overload signatures must be similarly decorated. The
implementation, if present, must also have a consistent decorator. Type
checkers should report an error if these conditions are not met.

If a ``@final`` or ``@override`` decorator is supplied for a function with
overloads, the decorator should be applied only to the overload implementation
if it is present. If an overload implementation isn't present (for example, in
a stub file), the ``@final`` or ``@override`` decorator should be applied only
to the first overload. Type checkers should enforce these rules and generate
an error when they are violated. If a ``@final`` or ``@override`` decorator
follows these rules, a type checker should treat the decorator as if it is
present on all overloads.

Overloads are allowed to use a mixture of ``async def`` and ``def`` statements
within the same overload definition. Type checkers should convert
``async def`` statements to a non-async signature (wrapping the return
type in a ``Coroutine``) before testing for implementation consistency
and overlapping overloads (described below).


Implementation consistency
^^^^^^^^^^^^^^^^^^^^^^^^^^

If an overload implementation is defined, type checkers should validate
that it is consistent with all of its associated overload signatures.
The implementation should accept all potential sets of arguments
that are accepted by the overloads and should produce all potential return
types produced by the overloads. In typing terms, this means the input
signature of the implementation should be :term:<assignable> to the input
signatures of all overloads, and the return type of all overloads should be
assignable to the return type of the implementation.

If the implementation is inconsistent with its overloads, a type checker
should report an error::

  @overload
  def func(x: str, /) -> str: ...
  @overload
  def func(x: int) -> int: ...

  # This implementation is inconsistent with the second overload
  # because it does not accept a keyword argument ``x`` and the
  # the overload's return type ``int`` is not assignable to the
  implementation's return type ``str``.
  def func(x: int | str, /) -> str:
    return str(x)

When a type checker checks the implementation for consistency with overloads,
it should first apply any transforms that change the effective type of the
implementation including the presence of a ``yield`` statement in the
implementation body, the use of ``async def``, and the presence of additional
decorators.


Overlapping overloads
^^^^^^^^^^^^^^^^^^^^^

If two overloads can accept the same set of arguments, they are said
to "partially overlap". If two overloads partially overlap, the return type
of the former overload should be assignable to the return type of the
latter overload. If this condition doesn't hold, it is indicative of a
programming error and should be reported by type checkers. The purpose of
this check is to prevent unsoundness of this form::

  @overload
  def is_one(x: Literal[1]) -> Literal[True]: ...
  @overload
  def is_one(x: int) -> Literal[False]: ...

  reveal_type(is_one(int(1)))  # Reveals Literal[False], but True at runtime

Type checkers may exempt certain magic methods from the above check
for conditions that are mandated by their usage in the runtime. For example,
the ``__get__`` method of a descriptor is often defined using overloads
that would partially overlap if the above rule is enforced.

Type checkers may ignore the possibility of multiple inheritance or
intersections involving structural types for purposes of computing overlap.
In the following example, classes ``A`` and ``B`` could theoretically overlap
because there could be a common type ``C`` that derives from both ``A`` and
``B``, but type checkers may choose not to flag this as an overlapping
overload::

  class A: ...
  class B: ...

  @overload
  def func(x: A) -> int: ...
  @overload
  def func(x: B) -> str: ...

If all possible sets of arguments accepted by an overload are also always
accepted by an earlier overload, the two overloads are said to "fully overlap".
In this case, the latter overload will never be used. This condition
is indicative of a programming error and should be reported by type
checkers::

  # These overloads fully overlap because the first overload
  # accepts all arguments accepted by the second overload.

  @overload
  def func[T](x: T) -> T: ...
  @overload
  def func(x: int) -> int: ...


Overload call evaluation
^^^^^^^^^^^^^^^^^^^^^^^^

When a type checker evaluates the call of an overloaded function, it
attempts to "match" the supplied arguments with one or more overloads.
This section describes the algorithm that type checkers should use
for overload matching. This algorithm should be applied even in the
presence of :ref:<overlapping overloads>.

Only the overloads (the ``@overload``-decorated signatures) should be
considered for matching purposes. The implementation, if provided,
should be ignored for purposes of overload matching.


Step 1: Examine the argument list to determine the number of
positional and keyword arguments. Use this information to eliminate any
overload candidates that are not plausible based on their
input signatures.

- If no candidate overloads remain, generate an error and stop.
- If only one candidate overload remains, it is the winning match. Evaluate
  it as if it were a non-overloaded function call and stop.
- If two or more candidate overloads remain, proceed to step 2.


Step 2: Evaluate each remaining overload as a regular (non-overloaded)
call to determine whether it is compatible with the supplied
argument list. Unlike step 1, this step considers the types of the parameters
and arguments. During this step, do not generate any user-visible errors.
Simply record which of the overloads result in evaluation errors.

- If all overloads result in errors, proceed to step 3.
- If only one overload evaluates without error, it is the winning match.
  Evaluate it as if it were a non-overloaded function call and stop.
- If two or more candidate overloads remain, proceed to step 4.


Step 3: If step 2 produces errors for all overloads, perform
"argument type expansion". Union types can be expanded
into their constituent subtypes. For example, the type ``int | str`` can
be expanded into ``int`` and ``str``.

Type expansion should be performed one argument at a time from left to
right. Each expansion results in sets of effective argument types.
For example, if there are two arguments whose types evaluate to
``int | str`` and ``int | bytes``, expanding the first argument type
results in two sets of argument types: ``(int, int | bytes)`` and
``(str, int | bytes)``. If type expansion for the second argument is required,
four sets of argument types are produced: ``(int, int)``, ``(int, bytes)``,
``(str, int)``, and ``(str, bytes)``.

After each argument's expansion, return to step 2 and evaluate all
expanded argument lists.

- If all argument lists evaluate successfully, combine their
  respective return types by union to determine the final return type
  for the call, and stop.
- If argument expansion has been applied to all arguments and one or
  more of the expanded argument lists cannot be evaluated successfully,
  generate an error and stop.


For additional details about argument type expansion, see
`argument-type-expansion`_ below.


Step 4: If the argument list is compatible with two or more overloads,
determine whether one or more of the overloads has a variadic parameter
(either ``*args`` or ``**kwargs``) that maps to a corresponding argument
that supplies an indeterminate number of positional or keyword arguments.
If so, eliminate overloads that do not have a variadic parameter.

- If this results in only one remaining candidate overload, it is
  the winning match. Evaluate it as if it were a non-overloaded function
  call and stop.
- If two or more candidate overloads remain, proceed to step 5.


Step 5: For each argument, determine whether all possible
:term:`materializations <materialize>` of the argument's type are assignable to
the corresponding parameter type for each of the remaining overloads. If so,
eliminate all of the subsequent remaining overloads.

For example, if the argument type is ``list[Any]`` and there are three remaining
overloads with corresponding parameter types of ``list[int]``, ``list[Any]``
and ``Any``. We can eliminate the third of the remaining overloads because
all materializations of ``list[Any]`` are assignable to ``list[Any]``, the
parameter in the second overload. We cannot eliminate the second overload
because there are possible materializations of ``list[Any]`` (for example,
``list[str]``) that are not assignable to ``list[int]``.

Once this filtering process is applied for all arguments, examine the return
types of the remaining overloads. If these return types include type variables,
they should be replaced with their solved types. If the resulting return types
for all remaining overloads are :term:<equivalent>, proceed to step 6.

If the return types are not equivalent, overload matching is ambiguous. In
this case, assume a return type of ``Any`` and stop.


Step 6: Choose the first remaining candidate overload as the winning
match. Evaluate it as if it were a non-overloaded function call and stop.

Example 1::

  @overload
  def example1(x: int, y: str) -> int: ...
  @overload
  def example1(x: str) -> str: ...

  example1()  # Error in step 1: no plausible overloads
  example1(1, "")  # Step 1 eliminates second overload
  example1("")  # Step 1 eliminates first overload

  example1("", "")  # Error in step 2: no compatible overloads
  example1(1)  # Error in step 2: no compatible overloads


Example 2::

  @overload
  def example2(x: int, y: str, z: int) -> str: ...
  @overload
  def example2(x: int, y: int, z: int) -> int: ...

  def test(values: list[str | int]):
      # In this example, argument type expansion is
      # performed on the first two arguments. Expansion
      # of the third is unnecessary.
      r1 = example2(1, values[0], 1)
      reveal_type(r1)  # Should reveal str | int

      # Here, the types of all three arguments are expanded
      # without success.
      example2(values[0], values[1], values[2])  # Error in step 3


Example 3::

  @overload
  def example3(x: int, /) -> tuple[int]: ...
  @overload
  def example3(x: int, y: int, /) -> tuple[int, int]: ...
  @overload
  def example3(*args: int) -> tuple[int, ...]: ...

  def test(val: list[int]):
      # Step 1 eliminates second overload. Step 4 and
      # step 5 do not apply. Step 6 picks the first
      # overload.
      r1 = example3(1)
      reveal_type(r1)  # Should reveal tuple[int]

      # Step 1 eliminates first overload. Step 4 and
      # step 5 do not apply. Step 6 picks the second
      # overload.
      r2 = example3(1, 2)
      reveal_type(r2)  # Should reveal tuple[int, int]

      # Step 1 doesn't eliminate any overloads. Step 4
      # picks the third overload.
      r3 = example3(*val)
      reveal_type(r3)  # Should reveal tuple[int, ...]


Example 4::

  @overload
  def example4(x: list[int], y: int) -> int: ...
  @overload
  def example4(x: list[str], y: str) -> int: ...
  @overload
  def example4(x: int, y: int) -> list[int]: ...

  def test(v1: list[Any], v2: Any):
      # Step 2 eliminates the third overload. Step 5
      # determines that first and second overloads
      # both apply and are ambiguous due to Any, but
      # return types are consistent.
      r1 = example4(v1, v2)
      reveal_type(r1)  # Reveals int

      # Step 2 eliminates the second overload. Step 5
      # determines that first and third overloads
      # both apply and are ambiguous due to Any, and
      # the return types are inconsistent.
      r2 = example4(v2, 1)
      reveal_type(r2)  # Should reveal Any


.. _argument-type-expansion:

Argument type expansion
^^^^^^^^^^^^^^^^^^^^^^^

When performing argument type expansion, a type that is equivalent to
a union of a finite set of subtypes should be expanded into its constituent
subtypes. This includes the following cases.

1. Explicit unions: Each subtype of the union should be considered as a
separate argument type. For example, the type ``int | str`` should be expanded
into ``int`` and ``str``.

2. ``bool`` should be expanded into ``Literal[True]`` and ``Literal[False]``.

3. ``Enum`` types (other than those that derive from ``enum.Flag``) should
be expanded into their literal members.

4. ``type[A | B]`` should be expanded into ``type[A]`` and ``type[B]``.

5. Tuples of known length that contain expandable types should be expanded
into all possible combinations of their element types. For example, the type
``tuple[int | str, bool]`` should be expanded into ``(int, Literal[True])``,
``(int, Literal[False])``, ``(str, Literal[True])``, and
``(str, Literal[False])``.

The above list may not be exhaustive, and additional cases may be added in
the future as the type system evolves.
