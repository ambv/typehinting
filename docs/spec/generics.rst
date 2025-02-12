.. _`generics`:

Generics
========

Introduction
------------

Since type information about objects kept in containers cannot be
statically inferred in a generic way, abstract base classes have been
extended to support subscription to denote expected types for container
elements.  Example::

  from collections.abc import Mapping

  def notify_by_email(employees: set[Employee], overrides: Mapping[str, str]) -> None: ...

Generics can be parameterized by using a factory available in
``typing`` called ``TypeVar``.  Example::

  from collections.abc import Sequence
  from typing import TypeVar

  T = TypeVar('T')      # Declare type variable

  def first(l: Sequence[T]) -> T:   # Generic function
      return l[0]

Or, since Python 3.12 (:pep:`695`), by using the new syntax for
generic functions::

  from collections.abc import Sequence

  def first[T](l: Sequence[T]) -> T:   # Generic function
      return l[0]

The two syntaxes are equivalent.
In either case the contract is that the returned value is consistent with
the elements held by the collection.

A ``TypeVar()`` expression must always directly be assigned to a
variable (it should not be used as part of a larger expression).  The
argument to ``TypeVar()`` must be a string equal to the variable name
to which it is assigned.  Type variables must not be redefined.

``TypeVar`` supports constraining parametric types to a fixed set of possible
types (note: those types cannot be parameterized by type variables). For
example, we can define a type variable that ranges over just ``str`` and
``bytes``. By default, a type variable ranges over all possible types.
Example of constraining a type variable::

  from typing import TypeVar

  AnyStr = TypeVar('AnyStr', str, bytes)

  def concat(x: AnyStr, y: AnyStr) -> AnyStr:
      return x + y

Or using the built-in syntax (3.12 and higher)::

  def concat[AnyStr: (str, bytes)](x: AnyStr, y: AnyStr) -> AnyStr:
      return x + y

The function ``concat`` can be called with either two ``str`` arguments
or two ``bytes`` arguments, but not with a mix of ``str`` and ``bytes``
arguments.

There should be at least two constraints, if any; specifying a single
constraint is disallowed.

Subtypes of types constrained by a type variable should be treated
as their respective explicitly listed base types in the context of the
type variable.  Consider this example::

  class MyStr(str): ...

  x = concat(MyStr('apple'), MyStr('pie'))

The call is valid but the type variable ``AnyStr`` will be set to
``str`` and not ``MyStr``. In effect, the inferred type of the return
value assigned to ``x`` will also be ``str``.

Additionally, ``Any`` is a valid value for every type variable.
Consider the following::

  def count_truthy(elements: list[Any]) -> int:
      return sum(1 for elem in elements if elem)

This is equivalent to omitting the generic notation and just saying
``elements: list``.


User-defined generic types
--------------------------

There are several ways to define a user-defined class as generic:

* Include a ``Generic`` base class.
* Use the new generic class syntax in Python 3.12 and higher.
* Include a ``Protocol`` base class parameterized with type variables. This
  approach also marks the class as a protocol - see
  :ref:`generic protocols<generic-protocols>` for more information.
* Include a generic base class parameterized with type variables.

Example using ``Generic``::

  from typing import TypeVar, Generic
  from logging import Logger

  T = TypeVar('T')

  class LoggedVar(Generic[T]):
      def __init__(self, value: T, name: str, logger: Logger) -> None:
          self.name = name
          self.logger = logger
          self.value = value

      def set(self, new: T) -> None:
          self.log('Set ' + repr(self.value))
          self.value = new

      def get(self) -> T:
          self.log('Get ' + repr(self.value))
          return self.value

      def log(self, message: str) -> None:
          self.logger.info('{}: {}'.format(self.name, message))

Or, using the new generic class syntax::

  class LoggedVar[T]:
      # methods as in previous example

This implicitly adds ``Generic[T]`` as a base class, and type checkers
should treat the two definitions of ``LoggedVar`` largely equivalently (except
for variance, see below).

``Generic[T]`` as a base class defines that the class ``LoggedVar``
takes a single type parameter ``T``. This also makes ``T`` valid as
a type within the class body.

The ``Generic`` base class uses a metaclass that defines ``__getitem__``
so that ``LoggedVar[t]`` is valid as a type::

  from collections.abc import Iterable

  def zero_all_vars(vars: Iterable[LoggedVar[int]]) -> None:
      for var in vars:
          var.set(0)

A generic type can have any number of type variables, and type variables
may be constrained. This is valid::

  from typing import TypeVar, Generic

  T = TypeVar('T')
  S = TypeVar('S')

  class Pair(Generic[T, S]):
      ...

Each type variable argument to ``Generic`` must be distinct. This is
thus invalid::

  from typing import TypeVar, Generic

  T = TypeVar('T')

  class Pair(Generic[T, T]):   # INVALID
      ...

All arguments to ``Generic`` or ``Protocol`` must be type variables::

  from typing import Generic, Protocol

  class Bad1(Generic[int]):   # INVALID
      ...
  class Bad2(Protocol[int]):   # INVALID
      ...

When a ``Generic`` or parameterized ``Protocol`` base class is present, all type
parameters for the class must appear within the ``Generic`` or
``Protocol`` type argument list, respectively. A type checker should report an
error if a type variable that is not included in the type argument list appears
elsewhere in the base class list::

  from typing import Generic, Protocol, TypeVar
  from collections.abc import Iterable

  T = TypeVar('T')
  S = TypeVar('S')

  class Bad1(Iterable[T], Generic[S]):   # INVALID
      ...
  class Bad2(Iterable[T], Protocol[S]):   # INVALID
      ...

Note that the above rule does not apply to a bare ``Protocol`` base class. This
is valid (see below)::

  from typing import Protocol, TypeVar
  from collections.abc import Iterator

  T = TypeVar('T')

  class MyIterator(Iterator[T], Protocol): ...

When no ``Generic`` or parameterized ``Protocol`` base class is present, a
defined class is generic if you subclass one or more other generic classes and
specify type variables for their parameters. See :ref:`generic-base-classes`
for details.

You can use multiple inheritance with ``Generic``::

  from typing import TypeVar, Generic
  from collections.abc import Sized, Iterable, Container

  T = TypeVar('T')

  class LinkedList(Sized, Generic[T]):
      ...

  K = TypeVar('K')
  V = TypeVar('V')

  class MyMapping(Iterable[tuple[K, V]],
                  Container[tuple[K, V]],
                  Generic[K, V]):
      ...

Subclassing a generic class without specifying type parameters assumes
``Any`` for each position unless the type parameter has a default value.
In the following example, ``MyIterable`` is not generic but implicitly inherits
from ``Iterable[Any]``::

  from collections.abc import Iterable

  class MyIterable(Iterable):  # Same as Iterable[Any]
      ...

Generic metaclasses are not supported.

.. _`typevar-scoping`:

Scoping rules for type variables
--------------------------------

Type variables follow normal name resolution rules.
However, there are some special cases in the static typechecking context:

* A type variable used in a generic function could be inferred to represent
  different types in the same code block. Example::

    from typing import TypeVar, Generic

    T = TypeVar('T')

    def fun_1(x: T) -> T: ...  # T here
    def fun_2(x: T) -> T: ...  # and here could be different

    fun_1(1)                   # This is OK, T is inferred to be int
    fun_2('a')                 # This is also OK, now T is str

* A type variable used in a method of a generic class that coincides
  with one of the variables that parameterize this class is always bound
  to that variable. Example::

    from typing import TypeVar, Generic

    T = TypeVar('T')

    class MyClass(Generic[T]):
        def meth_1(self, x: T) -> T: ...  # T here
        def meth_2(self, x: T) -> T: ...  # and here are always the same

    a: MyClass[int] = MyClass()
    a.meth_1(1)    # OK
    a.meth_2('a')  # This is an error!

* A type variable used in a method that does not match any of the variables
  that parameterize the class makes this method a generic function in that
  variable::

    T = TypeVar('T')
    S = TypeVar('S')
    class Foo(Generic[T]):
        def method(self, x: T, y: S) -> S:
            ...

    x: Foo[int] = Foo()
    y = x.method(0, "abc")  # inferred type of y is str

* Unbound type variables should not appear in the bodies of generic functions,
  or in the class bodies apart from method definitions::

    T = TypeVar('T')
    S = TypeVar('S')

    def a_fun(x: T) -> None:
        # this is OK
        y: list[T] = []
        # but below is an error!
        y: list[S] = []

    class Bar(Generic[T]):
        # this is also an error
        an_attr: list[S] = []

        def do_something(self, x: S) -> S:  # this is OK though
            ...

* A generic class definition that appears inside a generic function
  should not use type variables that parameterize the generic function::

    def a_fun(x: T) -> None:

        # This is OK
        a_list: list[T] = []
        ...

        # This is however illegal
        class MyGeneric(Generic[T]):
            ...

* A generic class nested in another generic class cannot use the same type
  variables. The scope of the type variables of the outer class
  doesn't cover the inner one::

    T = TypeVar('T')
    S = TypeVar('S')

    class Outer(Generic[T]):
        class Bad(Iterable[T]):       # Error
            ...
        class AlsoBad:
            x: list[T]  # Also an error

        class Inner(Iterable[S]):     # OK
            ...
        attr: Inner[T]  # Also OK


Instantiating generic classes and type erasure
----------------------------------------------

User-defined generic classes can be instantiated. Suppose we write
a ``Node`` class inheriting from ``Generic[T]``::

  from typing import TypeVar, Generic

  T = TypeVar('T')

  class Node(Generic[T]):
      ...

To create ``Node`` instances you call ``Node()`` just as for a regular
class.  At runtime the type (class) of the instance will be ``Node``.
But what type does it have to the type checker?  The answer depends on
how much information is available in the call.  If the constructor
(``__init__`` or ``__new__``) uses ``T`` in its signature, and a
corresponding argument value is passed, the type of the corresponding
argument(s) is substituted.  Otherwise, the default value for the type
parameter (or ``Any``, if no default is provided) is assumed.  Example::

  from typing import TypeVar, Generic

  T = TypeVar('T')

  class Node(Generic[T]):
      x: T # Instance attribute (see below)
      def __init__(self, label: T | None = None) -> None:
          ...

  x = Node('')  # Inferred type is Node[str]
  y = Node(0)   # Inferred type is Node[int]
  z = Node()    # Inferred type is Node[Any]

In case the inferred type uses ``[Any]`` but the intended type is more
specific, you can use an annotation (see below) to force the type of
the variable, e.g.::

  # (continued from previous example)
  a: Node[int] = Node()
  b: Node[str] = Node()

Alternatively, you can instantiate a specific concrete type, e.g.::

  # (continued from previous example)
  p = Node[int]()
  q = Node[str]()
  r = Node[int]('')  # Error
  s = Node[str](0)   # Error

Note that the runtime type (class) of ``p`` and ``q`` is still just ``Node``
-- ``Node[int]`` and ``Node[str]`` are distinguishable class objects, but
the runtime class of the objects created by instantiating them doesn't
record the distinction. This behavior is called "type erasure"; it is
common practice in languages with generics (e.g. Java, TypeScript).

Using generic classes (parameterized or not) to access attributes will result
in type check failure. Outside the class definition body, a class attribute
cannot be assigned, and can only be looked up by accessing it through a
class instance that does not have an instance attribute with the same name::

  # (continued from previous example)
  Node[int].x = 1  # Error
  Node[int].x      # Error
  Node.x = 1       # Error
  Node.x           # Error
  type(p).x        # Error
  p.x              # Ok (evaluates to int)
  Node[int]().x    # Ok (evaluates to int)
  p.x = 1          # Ok, but assigning to instance attribute

Generic versions of abstract collections like ``Mapping`` or ``Sequence``
and generic versions of built-in classes -- ``List``, ``Dict``, ``Set``,
and ``FrozenSet`` -- cannot be instantiated. However, concrete user-defined
subclasses thereof and generic versions of concrete collections can be
instantiated::

  data = DefaultDict[int, bytes]()

Note that one should not confuse static types and runtime classes.
The type is still erased in this case and the above expression is
just a shorthand for::

  data: DefaultDict[int, bytes] = collections.defaultdict()

It is not recommended to use the subscripted class (e.g. ``Node[int]``)
directly in an expression -- using a type alias (e.g. ``IntNode = Node[int]``)
instead is preferred. (First, creating the subscripted class,
e.g. ``Node[int]``, has a runtime cost. Second, using a type alias
is more readable.)

.. _`generic-base-classes`:

Arbitrary generic types as base classes
---------------------------------------

``Generic[T]`` is only valid as a base class -- it's not a proper type.
However, user-defined generic types such as ``LinkedList[T]`` from the
above example and built-in generic types and ABCs such as ``list[T]``
and ``Iterable[T]`` are valid both as types and as base classes. For
example, we can define a subclass of ``dict`` that specializes type
arguments::

  class Node:
      ...

  class SymbolTable(dict[str, list[Node]]):
      def push(self, name: str, node: Node) -> None:
          self.setdefault(name, []).append(node)

      def pop(self, name: str) -> Node:
          return self[name].pop()

      def lookup(self, name: str) -> Node | None:
          nodes = self.get(name)
          if nodes:
              return nodes[-1]
          return None

``SymbolTable`` is a subclass of ``dict`` and a subtype of ``dict[str,
list[Node]]``.

If a generic base class has a type variable as a type argument, this
makes the defined class generic. For example, we can define a generic
``LinkedList`` class that is iterable and a container::

  from typing import TypeVar
  from collections.abc import Iterable, Container

  T = TypeVar('T')

  class LinkedList(Iterable[T], Container[T]):
      ...

Now ``LinkedList[int]`` is a valid type. Note that we can use ``T``
multiple times in the base class list, as long as we don't use the
same type variable ``T`` multiple times within ``Generic[...]``.

Also consider the following example::

  from typing import TypeVar
  from collections.abc import Mapping

  T = TypeVar('T')

  class MyDict(Mapping[str, T]):
      ...

In this case ``MyDict`` has a single type parameter, ``T``.

Type variables are applied to the defined class in the order in which
they first appear in any generic base classes::

  from typing import Generic, TypeVar

  T1 = TypeVar('T1')
  T2 = TypeVar('T2')
  T3 = TypeVar('T3')

  class Parent1(Generic[T1, T2]):
      ...
  class Parent2(Generic[T1, T2]):
      ...
  class Child(Parent1[T1, T3], Parent2[T2, T3]):
      ...

That ``Child`` definition is equivalent to::

  class Child(Parent1[T1, T3], Parent2[T2, T3], Generic[T1, T3, T2]):
      ...

A type checker should report an error when the type variable order is
inconsistent::

  from typing import Generic, TypeVar

  T1 = TypeVar('T1')
  T2 = TypeVar('T2')
  T3 = TypeVar('T3')

  class Grandparent(Generic[T1, T2]):
      ...
  class Parent(Grandparent[T1, T2]):
      ...
  class Child(Parent[T1, T2], Grandparent[T2, T1]):   # INVALID
      ...

Abstract generic types
----------------------

The metaclass used by ``Generic`` is a subclass of ``abc.ABCMeta``.
A generic class can be an ABC by including abstract methods
or properties, and generic classes can also have ABCs as base
classes without a metaclass conflict.

.. _`typevar-bound`:

Type variables with an upper bound
----------------------------------

A type variable may specify an upper bound using ``bound=<type>`` (when using
the ``TypeVar`` constructor) or using ``: <type>`` (when using the native
syntax for generics). The bound itself cannot be parameterized by type
variables. This means that an actual type substituted (explicitly or
implicitly) for the type variable must be :term:`assignable` to the bound.
Example::

  from typing import TypeVar
  from collections.abc import Sized

  ST = TypeVar('ST', bound=Sized)

  def longer(x: ST, y: ST) -> ST:
      if len(x) > len(y):
          return x
      else:
          return y

  longer([1], [1, 2])  # ok, return type list[int]
  longer({1}, {1, 2})  # ok, return type set[int]
  longer([1], {1, 2})  # ok, return type a supertype of list[int] and set[int]

An upper bound cannot be combined with type constraints (as used in ``AnyStr``,
see the example earlier); type constraints cause the inferred type to be
*exactly* one of the constraint types, while an upper bound just requires that
the actual type is :term:`assignable` to the bound.

.. _`variance`:

Variance
--------

Consider a class ``Employee`` with a subclass ``Manager``.  Now
suppose we have a function with an argument annotated with
``list[Employee]``.  Should we be allowed to call this function with a
variable of type ``list[Manager]`` as its argument?  Many people would
answer "yes, of course" without even considering the consequences.
But unless we know more about the function, a type checker should
reject such a call: the function might append an ``Employee`` instance
to the list, which would violate the variable's type in the caller.

It turns out such an argument acts *contravariantly*, whereas the
intuitive answer (which is correct in case the function doesn't mutate
its argument!) requires the argument to act *covariantly*.  A longer
introduction to these concepts can be found on `Wikipedia
<https://en.wikipedia.org/wiki/Covariance_and_contravariance_%28computer_science%29>`_ and in :pep:`483`; here we just show how to control
a type checker's behavior.

By default generic types declared using the old ``TypeVar`` syntax are
considered *invariant* in all type variables, which means that e.g.
``list[Manager]`` is neither a supertype nor a subtype of ``list[Employee]``.

See below for the behavior when using the built-in generic syntax in Python
3.12 and higher.

To facilitate the declaration of container types where covariant or
contravariant type checking is acceptable, type variables accept keyword
arguments ``covariant=True`` or ``contravariant=True``. At most one of these
may be passed. Generic types defined with such variables are considered
covariant or contravariant in the corresponding variable. By convention,
it is recommended to use names ending in ``_co`` for type variables
defined with ``covariant=True`` and names ending in ``_contra`` for that
defined with ``contravariant=True``.

A typical example involves defining an immutable (or read-only)
container class::

  from typing import TypeVar, Generic
  from collections.abc import Iterable, Iterator

  T_co = TypeVar('T_co', covariant=True)

  class ImmutableList(Generic[T_co]):
      def __init__(self, items: Iterable[T_co]) -> None: ...
      def __iter__(self) -> Iterator[T_co]: ...
      ...

  class Employee: ...

  class Manager(Employee): ...

  def dump_employees(emps: ImmutableList[Employee]) -> None:
      for emp in emps:
          ...

  mgrs: ImmutableList[Manager] = ImmutableList([Manager()])
  dump_employees(mgrs)  # OK

The read-only collection classes in ``typing`` are all declared
covariant in their type variable (e.g. ``Mapping`` and ``Sequence``). The
mutable collection classes (e.g. ``MutableMapping`` and
``MutableSequence``) are declared invariant. The one example of
a contravariant type is the ``Generator`` type, which is contravariant
in the ``send()`` argument type (see below).

Variance is meaningful only when a type variable is bound to a generic class.
If a type variable declared as covariant or contravariant is bound to a generic
function or type alias, type checkers may warn users about this. However, any
subsequent type analysis involving such functions or aliases should ignore the
declared variance::

  T = TypeVar('T', covariant=True)

  class A(Generic[T]):  # T is covariant in this context
    ...

  def f(x: T) -> None:  # Variance of T is meaningless in this context
    ...

  Alias = list[T] | set[T]  # Variance of T is meaningless in this context

.. _`paramspec`:

ParamSpec
---------

(Originally specified by :pep:`612`.)

``ParamSpec`` Variables
^^^^^^^^^^^^^^^^^^^^^^^

Declaration
""""""""""""

A parameter specification variable is defined in a similar manner to how a
normal type variable is defined with ``typing.TypeVar``.

.. code-block::

   from typing import ParamSpec
   P = ParamSpec("P")         # Accepted
   P = ParamSpec("WrongName") # Rejected because P =/= WrongName

The runtime should accept ``bound``\ s and ``covariant`` and ``contravariant``
arguments in the declaration just as ``typing.TypeVar`` does, but for now we
will defer the standardization of the semantics of those options to a later PEP.

.. _`paramspec_valid_use_locations`:

Valid use locations
"""""""""""""""""""

Previously only a list of parameter arguments (``[A, B, C]``) or an ellipsis
(signifying "undefined parameters") were acceptable as the first "argument" to
``typing.Callable`` .  We now augment that with two new options: a parameter
specification variable (``Callable[P, int]``\ ) or a concatenation on a
parameter specification variable (``Callable[Concatenate[int, P], int]``\ ).

.. code-block::

   callable ::= Callable "[" parameters_expression, type_expression "]"

   parameters_expression ::=
     | "..."
     | "[" [ type_expression ("," type_expression)* ] "]"
     | parameter_specification_variable
     | concatenate "["
                      type_expression ("," type_expression)* ","
                      parameter_specification_variable
                   "]"

where ``parameter_specification_variable`` is a ``typing.ParamSpec`` variable,
declared in the manner as defined above, and ``concatenate`` is
``typing.Concatenate``.

As before, ``parameters_expression``\ s by themselves are not acceptable in
places where a type is expected

.. code-block::

   def foo(x: P) -> P: ...                           # Rejected
   def foo(x: Concatenate[int, P]) -> int: ...       # Rejected
   def foo(x: list[P]) -> None: ...                  # Rejected
   def foo(x: Callable[[int, str], P]) -> None: ...  # Rejected


User-Defined Generic Classes
""""""""""""""""""""""""""""

Just as defining a class as inheriting from ``Generic[T]`` makes a class generic
for a single parameter (when ``T`` is a ``TypeVar``\ ), defining a class as
inheriting from ``Generic[P]`` makes a class generic on
``parameters_expression``\ s (when ``P`` is a ``ParamSpec``).

.. code-block::

   T = TypeVar("T")
   P_2 = ParamSpec("P_2")

   class X(Generic[T, P]):
     f: Callable[P, int]
     x: T

   def f(x: X[int, P_2]) -> str: ...                    # Accepted
   def f(x: X[int, Concatenate[int, P_2]]) -> str: ...  # Accepted
   def f(x: X[int, [int, bool]]) -> str: ...            # Accepted
   def f(x: X[int, ...]) -> str: ...                    # Accepted
   def f(x: X[int, int]) -> str: ...                    # Rejected

Or, equivalently, using the built-in syntax for generics in Python 3.12
and higher::

  class X[T, **P]:
    f: Callable[P, int]
    x: T

By the rules defined above, spelling a concrete instance of a class generic
with respect to only a single ``ParamSpec`` would require unsightly double
brackets.  For aesthetic purposes we allow these to be omitted.

.. code-block::

   class Z(Generic[P]):
     f: Callable[P, int]

   def f(x: Z[[int, str, bool]]) -> str: ...   # Accepted
   def f(x: Z[int, str, bool]) -> str: ...     # Equivalent

   # Both Z[[int, str, bool]] and Z[int, str, bool] express this:
   class Z_instantiated:
     f: Callable[[int, str, bool], int]

Semantics
"""""""""

The inference rules for the return type of a function invocation whose signature
contains a ``ParamSpec`` variable are analogous to those around
evaluating ones with ``TypeVar``\ s.

.. code-block::

   def changes_return_type_to_str(x: Callable[P, int]) -> Callable[P, str]: ...

   def returns_int(a: str, b: bool) -> int: ...

   f = changes_return_type_to_str(returns_int) # f should have the type:
                                               # (a: str, b: bool) -> str

   f("A", True)               # Accepted
   f(a="A", b=True)           # Accepted
   f("A", "A")                # Rejected

   expects_str(f("A", True))  # Accepted
   expects_int(f("A", True))  # Rejected

Just as with traditional ``TypeVars``\ , a user may include the same
``ParamSpec`` multiple times in the arguments of the same function,
to indicate a dependency between multiple arguments.  In these cases a type
checker may choose to solve to a common behavioral supertype (i.e. a set of
parameters for which all of the valid calls are valid in both of the subtypes),
but is not obligated to do so.

.. code-block::

   P = ParamSpec("P")

   def foo(x: Callable[P, int], y: Callable[P, int]) -> Callable[P, bool]: ...

   def x_y(x: int, y: str) -> int: ...
   def y_x(y: int, x: str) -> int: ...

   foo(x_y, x_y)  # Should return (x: int, y: str) -> bool
                  # (a callable with two positional-or-keyword parameters)

   foo(x_y, y_x)  # Could return (a: int, b: str, /) -> bool
                  # (a callable with two positional-only parameters)
                  # This works because both callables have types that are
                  # behavioral subtypes of Callable[[int, str], int]


   def keyword_only_x(*, x: int) -> int: ...
   def keyword_only_y(*, y: int) -> int: ...
   foo(keyword_only_x, keyword_only_y) # Rejected

The constructors of user-defined classes generic on ``ParamSpec``\ s should be
evaluated in the same way.

.. code-block::

   U = TypeVar("U")

   class Y(Generic[U, P]):
     f: Callable[P, str]
     prop: U

     def __init__(self, f: Callable[P, str], prop: U) -> None:
       self.f = f
       self.prop = prop

   def a(q: int) -> str: ...

   Y(a, 1)   # Should resolve to Y[int, (q: int)]
   Y(a, 1).f # Should resolve to (q: int) -> str

The semantics of ``Concatenate[X, Y, P]`` are that it represents the parameters
represented by ``P`` with two positional-only parameters prepended.  This means
that we can use it to represent higher order functions that add, remove or
transform a finite number of parameters of a callable.

.. code-block::

   def bar(x: int, *args: bool) -> int: ...

   def add(x: Callable[P, int]) -> Callable[Concatenate[str, P], bool]: ...

   add(bar)       # Should return (a: str, /, x: int, *args: bool) -> bool

   def remove(x: Callable[Concatenate[int, P], int]) -> Callable[P, bool]: ...

   remove(bar)    # Should return (*args: bool) -> bool

   def transform(
     x: Callable[Concatenate[int, P], int]
   ) -> Callable[Concatenate[str, P], bool]: ...

   transform(bar) # Should return (a: str, /, *args: bool) -> bool

This also means that while any function that returns an ``R`` can satisfy
``typing.Callable[P, R]``, only functions that can be called positionally in
their first position with a ``X`` can satisfy
``typing.Callable[Concatenate[X, P], R]``.

.. code-block::

   def expects_int_first(x: Callable[Concatenate[int, P], int]) -> None: ...

   @expects_int_first # Rejected
   def one(x: str) -> int: ...

   @expects_int_first # Rejected
   def two(*, x: int) -> int: ...

   @expects_int_first # Rejected
   def three(**kwargs: int) -> int: ...

   @expects_int_first # Accepted
   def four(*args: int) -> int: ...

There are still some classes of decorators still not supported with these
features:

* those that add/remove/change a **variable** number of parameters (for
  example, ``functools.partial`` remains untypable even using ``ParamSpec``)
* those that add/remove/change keyword-only parameters.

The components of a ``ParamSpec``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``ParamSpec`` captures both positional and keyword accessible
parameters, but there unfortunately is no object in the runtime that captures
both of these together. Instead, we are forced to separate them into ``*args``
and ``**kwargs``\ , respectively. This means we need to be able to split apart
a single ``ParamSpec`` into these two components, and then bring
them back together into a call.  To do this, we introduce ``P.args`` to
represent the tuple of positional arguments in a given call and
``P.kwargs`` to represent the corresponding ``Mapping`` of keywords to
values.

Valid use locations
"""""""""""""""""""

These "properties" can only be used as the annotated types for
``*args`` and ``**kwargs``\ , accessed from a ParamSpec already in scope.

.. code-block::

   def puts_p_into_scope(f: Callable[P, int]) -> None:

     def inner(*args: P.args, **kwargs: P.kwargs) -> None:      # Accepted
       pass

     def mixed_up(*args: P.kwargs, **kwargs: P.args) -> None:   # Rejected
       pass

     def misplaced(x: P.args) -> None:                          # Rejected
       pass

   def out_of_scope(*args: P.args, **kwargs: P.kwargs) -> None: # Rejected
     pass


Furthermore, because the default kind of parameter in Python (\ ``(x: int)``\ )
may be addressed both positionally and through its name, two valid invocations
of a ``(*args: P.args, **kwargs: P.kwargs)`` function may give different
partitions of the same set of parameters. Therefore, we need to make sure that
these special types are only brought into the world together, and are used
together, so that our usage is valid for all possible partitions.

.. code-block::

   def puts_p_into_scope(f: Callable[P, int]) -> None:

     stored_args: P.args                           # Rejected

     stored_kwargs: P.kwargs                       # Rejected

     def just_args(*args: P.args) -> None:         # Rejected
       pass

     def just_kwargs(**kwargs: P.kwargs) -> None:  # Rejected
       pass


Semantics
"""""""""

With those requirements met, we can now take advantage of the unique properties
afforded to us by this set up:


* Inside the function, ``args`` has the type ``P.args``\ , not
  ``tuple[P.args, ...]`` as would be with a normal annotation
  (and likewise with the ``**kwargs``\ )

  * This special case is necessary to encapsulate the heterogeneous contents
    of the ``args``/``kwargs`` of a given call, which cannot be expressed
    by an indefinite tuple/dictionary type.

* A function of type ``Callable[P, R]`` can be called with ``(*args, **kwargs)``
  if and only if ``args`` has the type ``P.args`` and ``kwargs`` has the type
  ``P.kwargs``\ , and that those types both originated from the same function
  declaration.
* A function declared as ``def inner(*args: P.args, **kwargs: P.kwargs) -> X``
  has type ``Callable[P, X]``.

With these three properties, we now have the ability to fully type check
parameter preserving decorators.

.. code-block::

   def decorator(f: Callable[P, int]) -> Callable[P, None]:

     def foo(*args: P.args, **kwargs: P.kwargs) -> None:

       f(*args, **kwargs)    # Accepted, should resolve to int

       f(*kwargs, **args)    # Rejected

       f(1, *args, **kwargs) # Rejected

     return foo              # Accepted

To extend this to include ``Concatenate``, we declare the following properties:

* A function of type ``Callable[Concatenate[A, B, P], R]`` can only be
  called with ``(a, b, *args, **kwargs)`` when ``args`` and ``kwargs`` are the
  respective components of ``P``, ``a`` is of type ``A`` and ``b`` is of
  type ``B``.
* A function declared as
  ``def inner(a: A, b: B, *args: P.args, **kwargs: P.kwargs) -> R``
  has type ``Callable[Concatenate[A, B, P], R]``. Placing keyword-only
  parameters between the ``*args`` and ``**kwargs`` is forbidden.

.. code-block::

   def add(f: Callable[P, int]) -> Callable[Concatenate[str, P], None]:

     def foo(s: str, *args: P.args, **kwargs: P.kwargs) -> None:  # Accepted
       pass

     def bar(*args: P.args, s: str, **kwargs: P.kwargs) -> None:  # Rejected
       pass

     return foo                                                   # Accepted


   def remove(f: Callable[Concatenate[int, P], int]) -> Callable[P, None]:

     def foo(*args: P.args, **kwargs: P.kwargs) -> None:
       f(1, *args, **kwargs) # Accepted

       f(*args, 1, **kwargs) # Rejected

       f(*args, **kwargs)    # Rejected

     return foo

Note that the names of the parameters preceding the ``ParamSpec``
components are not mentioned in the resulting ``Concatenate``.  This means that
these parameters can not be addressed via a named argument:

.. code-block::

   def outer(f: Callable[P, None]) -> Callable[P, None]:
     def foo(x: int, *args: P.args, **kwargs: P.kwargs) -> None:
       f(*args, **kwargs)

     def bar(*args: P.args, **kwargs: P.kwargs) -> None:
       foo(1, *args, **kwargs)   # Accepted
       foo(x=1, *args, **kwargs) # Rejected

     return bar

.. _above:

This is not an implementation convenience, but a soundness requirement.  If we
were to allow that second calling style, then the following snippet would be
problematic.

.. code-block::

   @outer
   def problem(*, x: object) -> None:
     pass

   problem(x="uh-oh")

Inside of ``bar``, we would get
``TypeError: foo() got multiple values for argument 'x'``.  Requiring these
concatenated arguments to be addressed positionally avoids this kind of problem,
and simplifies the syntax for spelling these types. Note that this also why we
have to reject signatures of the form
``(*args: P.args, s: str, **kwargs: P.kwargs)``.

If one of these prepended positional parameters contains a free ``ParamSpec``\ ,
we consider that variable in scope for the purposes of extracting the components
of that ``ParamSpec``.  That allows us to spell things like this:

.. code-block::

   def twice(f: Callable[P, int], *args: P.args, **kwargs: P.kwargs) -> int:
     return f(*args, **kwargs) + f(*args, **kwargs)

The type of ``twice`` in the above example is
``Callable[Concatenate[Callable[P, int], P], int]``, where ``P`` is bound by the
outer ``Callable``.  This has the following semantics:

.. code-block::

   def a_int_b_str(a: int, b: str) -> int:
     return a

   twice(a_int_b_str, 1, "A")       # Accepted

   twice(a_int_b_str, b="A", a=1)   # Accepted

   twice(a_int_b_str, "A", 1)       # Rejected

.. _`typevartuple`:

TypeVarTuple
------------

(Originally specified in :pep:`646`.)

A ``TypeVarTuple`` serves as a placeholder not for a single type
but for a *tuple* of types.

In addition, we introduce a new use for the star operator: to 'unpack'
``TypeVarTuple`` instances and tuple types such as ``tuple[int,
str]``. Unpacking a ``TypeVarTuple`` or tuple type is the typing
equivalent of unpacking a variable or a tuple of values.

Type Variable Tuples
^^^^^^^^^^^^^^^^^^^^

In the same way that a normal type variable is a stand-in for a single
type such as ``int``, a type variable *tuple* is a stand-in for a *tuple* type such as
``tuple[int, str]``.

Type variable tuples are created and used with:

::

    from typing import TypeVarTuple

    Ts = TypeVarTuple('Ts')

    class Array(Generic[*Ts]):
      ...

    def foo(*args: *Ts):
      ...

Or when using the built-in syntax for generics in Python 3.12 and higher::

    class Array[*Ts]:
      ...

    def foo[*Ts](*args: *Ts):
      ...

Using Type Variable Tuples in Generic Classes
"""""""""""""""""""""""""""""""""""""""""""""

Type variable tuples behave like a number of individual type variables packed in a
``tuple``. To understand this, consider the following example:

::

  Shape = TypeVarTuple('Shape')

  class Array(Generic[*Shape]): ...

  Height = NewType('Height', int)
  Width = NewType('Width', int)
  x: Array[Height, Width] = Array()

The ``Shape`` type variable tuple here behaves like ``tuple[T1, T2]``,
where ``T1`` and ``T2`` are type variables. To use these type variables
as type parameters of ``Array``, we must *unpack* the type variable tuple using
the star operator: ``*Shape``. The signature of ``Array`` then behaves
as if we had simply written ``class Array(Generic[T1, T2]): ...``.

In contrast to ``Generic[T1, T2]``, however, ``Generic[*Shape]`` allows
us to parameterize the class with an *arbitrary* number of type parameters.
That is, in addition to being able to define rank-2 arrays such as
``Array[Height, Width]``, we could also define rank-3 arrays, rank-4 arrays,
and so on:

::

  Time = NewType('Time', int)
  Batch = NewType('Batch', int)
  y: Array[Batch, Height, Width] = Array()
  z: Array[Time, Batch, Height, Width] = Array()

Using Type Variable Tuples in Functions
"""""""""""""""""""""""""""""""""""""""

Type variable tuples can be used anywhere a normal ``TypeVar`` can.
This includes class definitions, as shown above, as well as function
signatures and variable annotations:

::

    class Array(Generic[*Shape]):

        def __init__(self, shape: tuple[*Shape]):
            self._shape: tuple[*Shape] = shape

        def get_shape(self) -> tuple[*Shape]:
            return self._shape

    shape = (Height(480), Width(640))
    x: Array[Height, Width] = Array(shape)
    y = abs(x)  # Inferred type is Array[Height, Width]
    z = x + x   #        ...    is Array[Height, Width]

Type Variable Tuples Must Always be Unpacked
""""""""""""""""""""""""""""""""""""""""""""

Note that in the previous example, the ``shape`` argument to ``__init__``
was annotated as ``tuple[*Shape]``. Why is this necessary - if ``Shape``
behaves like ``tuple[T1, T2, ...]``, couldn't we have annotated the ``shape``
argument as ``Shape`` directly?

This is, in fact, deliberately not possible: type variable tuples must
*always* be used unpacked (that is, prefixed by the star operator). This is
for two reasons:

* To avoid potential confusion about whether to use a type variable tuple
  in a packed or unpacked form ("Hmm, should I write '``-> Shape``',
  or '``-> tuple[Shape]``', or '``-> tuple[*Shape]``'...?")
* To improve readability: the star also functions as an explicit visual
  indicator that the type variable tuple is not a normal type variable.

Variance, Type Constraints and Type Bounds: Not (Yet) Supported
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

``TypeVarTuple`` does not yet support specification of:

* Variance (e.g. ``TypeVar('T', covariant=True)``)
* Type constraints (``TypeVar('T', int, float)``)
* Type bounds (``TypeVar('T', bound=ParentClass)``)

We leave the decision of how these arguments should behave to a future PEP, when variadic generics have been tested in the field. As of PEP 646, type variable tuples are
invariant.

Type Variable Tuple Equality
""""""""""""""""""""""""""""

If the same ``TypeVarTuple`` instance is used in multiple places in a signature
or class, a valid type inference might be to bind the ``TypeVarTuple`` to
a ``tuple`` of a union of types:

::

  def foo(arg1: tuple[*Ts], arg2: tuple[*Ts]): ...

  a = (0,)
  b = ('0',)
  foo(a, b)  # Can Ts be bound to tuple[int | str]?

We do *not* allow this; type unions may *not* appear within the ``tuple``.
If a type variable tuple appears in multiple places in a signature,
the types must match exactly (the list of type parameters must be the same
length, and the type parameters themselves must be identical):

::

  def pointwise_multiply(
      x: Array[*Shape],
      y: Array[*Shape]
  ) -> Array[*Shape]: ...

  x: Array[Height]
  y: Array[Width]
  z: Array[Height, Width]
  pointwise_multiply(x, x)  # Valid
  pointwise_multiply(x, y)  # Error
  pointwise_multiply(x, z)  # Error

Multiple Type Variable Tuples: Not Allowed
""""""""""""""""""""""""""""""""""""""""""

Only a single type variable tuple may appear in a type parameter list:

::

    class Array(Generic[*Ts1, *Ts2]): ...  # Error

The reason is that multiple type variable tuples make it ambiguous
which parameters get bound to which type variable tuple: ::

    x: Array[int, str, bool]  # Ts1 = ???, Ts2 = ???

Type Concatenation
^^^^^^^^^^^^^^^^^^

Type variable tuples don't have to be alone; normal types can be
prefixed and/or suffixed:

::

    Shape = TypeVarTuple('Shape')
    Batch = NewType('Batch', int)
    Channels = NewType('Channels', int)

    def add_batch_axis(x: Array[*Shape]) -> Array[Batch, *Shape]: ...
    def del_batch_axis(x: Array[Batch, *Shape]) -> Array[*Shape]: ...
    def add_batch_channels(
      x: Array[*Shape]
    ) -> Array[Batch, *Shape, Channels]: ...

    a: Array[Height, Width]
    b = add_batch_axis(a)      # Inferred type is Array[Batch, Height, Width]
    c = del_batch_axis(b)      # Array[Height, Width]
    d = add_batch_channels(a)  # Array[Batch, Height, Width, Channels]


Normal ``TypeVar`` instances can also be prefixed and/or suffixed:

::

    T = TypeVar('T')
    Ts = TypeVarTuple('Ts')

    def prefix_tuple(
        x: T,
        y: tuple[*Ts]
    ) -> tuple[T, *Ts]: ...

    z = prefix_tuple(x=0, y=(True, 'a'))
    # Inferred type of z is tuple[int, bool, str]

Unpacking Tuple Types
^^^^^^^^^^^^^^^^^^^^^

We mentioned that a ``TypeVarTuple`` stands for a tuple of types.
Since we can unpack a ``TypeVarTuple``, for consistency, we also
allow unpacking a tuple type. As we shall see, this also enables a
number of interesting features.


Unpacking Unbounded Tuple Types
"""""""""""""""""""""""""""""""

Unpacking unbounded tuples is useful in function signatures where
we don't care about the exact elements and don't want to define an
unnecessary ``TypeVarTuple``:

::

    def process_batch_channels(
        x: Array[Batch, *tuple[Any, ...], Channels]
    ) -> None:
        ...


    x: Array[Batch, Height, Width, Channels]
    process_batch_channels(x)  # OK
    y: Array[Batch, Channels]
    process_batch_channels(y)  # OK
    z: Array[Batch]
    process_batch_channels(z)  # Error: Expected Channels.


We can also pass a ``*tuple[Any, ...]`` wherever a ``*Ts`` is
expected. This is useful when we have particularly dynamic code and
cannot state the precise number of dimensions or the precise types for
each of the dimensions. In those cases, we can smoothly fall back to
an unbounded tuple:

::

    y: Array[*tuple[Any, ...]] = read_from_file()

    def expect_variadic_array(
        x: Array[Batch, *Shape]
    ) -> None: ...

    expect_variadic_array(y)  # OK

    def expect_precise_array(
        x: Array[Batch, Height, Width, Channels]
    ) -> None: ...

    expect_precise_array(y)  # OK

``Array[*tuple[Any, ...]]`` stands for an array with an arbitrary
number of dimensions of type ``Any``. This means that, in the call to
``expect_variadic_array``, ``Batch`` is bound to ``Any`` and ``Shape``
is bound to ``tuple[Any, ...]``. In the call to
``expect_precise_array``, the variables ``Batch``, ``Height``,
``Width``, and ``Channels`` are all bound to ``Any``.

This allows users to handle dynamic code gracefully while still
explicitly marking the code as unsafe (by using ``y: Array[*tuple[Any,
...]]``).  Otherwise, users would face noisy errors from the type
checker every time they tried to use the variable ``y``, which would
hinder them when migrating a legacy code base to use ``TypeVarTuple``.

.. _args_as_typevartuple:

``*args`` as a Type Variable Tuple
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:ref:`this specification <annotating-args-kwargs>` states that when a
type annotation is provided for ``*args``, every argument
must be of the type annotated. That is, if we specify ``*args`` to be type ``int``,
then *all* arguments must be of type ``int``. This limits our ability to specify
the type signatures of functions that take heterogeneous argument types.

If ``*args`` is annotated as a type variable tuple, however, the types of the
individual arguments become the types in the type variable tuple:

::

    Ts = TypeVarTuple('Ts')

    def args_to_tuple(*args: *Ts) -> tuple[*Ts]: ...

    args_to_tuple(1, 'a')  # Inferred type is tuple[int, str]

In the above example, ``Ts`` is bound to ``tuple[int, str]``. If no
arguments are passed, the type variable tuple behaves like an empty
tuple, ``tuple[()]``.

As usual, we can unpack any tuple types. For example, by using a type
variable tuple inside a tuple of other types, we can refer to prefixes
or suffixes of the variadic argument list. For example:

::

    # os.execle takes arguments 'path, arg0, arg1, ..., env'
    def execle(path: str, *args: *tuple[*Ts, Env]) -> None: ...

Note that this is different to

::

    def execle(path: str, *args: *Ts, env: Env) -> None: ...

as this would make ``env`` a keyword-only argument.

Using an unpacked unbounded tuple is equivalent to the
:ref:`behavior <annotating-args-kwargs>`
of ``*args: int``, which accepts zero or
more values of type ``int``:

::

    def foo(*args: *tuple[int, ...]) -> None: ...

    # equivalent to:
    def foo(*args: int) -> None: ...

Unpacking tuple types also allows more precise types for heterogeneous
``*args``. The following function expects an ``int`` at the beginning,
zero or more ``str`` values, and a ``str`` at the end:

::

    def foo(*args: *tuple[int, *tuple[str, ...], str]) -> None: ...

For completeness, we mention that unpacking a concrete tuple allows us
to specify ``*args`` of a fixed number of heterogeneous types:

::

    def foo(*args: *tuple[int, str]) -> None: ...

    foo(1, "hello")  # OK

Note that, in keeping with the rule that type variable tuples must always
be used unpacked, annotating ``*args`` as being a plain type variable tuple
instance is *not* allowed:

::

    def foo(*args: Ts): ...  # NOT valid

``*args`` is the only case where an argument can be annotated as ``*Ts`` directly;
other arguments should use ``*Ts`` to parameterize something else, e.g. ``tuple[*Ts]``.
If ``*args`` itself is annotated as ``tuple[*Ts]``, the old behavior still applies:
all arguments must be a ``tuple`` parameterized with the same types.

::

    def foo(*args: tuple[*Ts]): ...

    foo((0,), (1,))    # Valid
    foo((0,), (1, 2))  # Error
    foo((0,), ('1',))  # Error

Finally, note that a type variable tuple may *not* be used as the type of
``**kwargs``. (We do not yet know of a use case for this feature, so we prefer
to leave the ground fresh for a potential future PEP.)

::

    # NOT valid
    def foo(**kwargs: *Ts): ...

Type Variable Tuples with ``Callable``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Type variable tuples can also be used in the arguments section of a
``Callable``:

::

    class Process:
      def __init__(
        self,
        target: Callable[[*Ts], None],
        args: tuple[*Ts],
      ) -> None: ...

    def func(arg1: int, arg2: str) -> None: ...

    Process(target=func, args=(0, 'foo'))  # Valid
    Process(target=func, args=('foo', 0))  # Error

Other types and normal type variables can also be prefixed/suffixed
to the type variable tuple:

::

    T = TypeVar('T')

    def foo(f: Callable[[int, *Ts, T], tuple[T, *Ts]]): ...

The behavior of a Callable containing an unpacked item, whether the
item is a ``TypeVarTuple`` or a tuple type, is to treat the elements
as if they were the type for ``*args``. So, ``Callable[[*Ts], None]``
is treated as the type of the function:

::

    def foo(*args: *Ts) -> None: ...

``Callable[[int, *Ts, T], tuple[T, *Ts]]`` is treated as the type of
the function:

::

    def foo(*args: *tuple[int, *Ts, T]) -> tuple[T, *Ts]: ...

Behavior when Type Parameters are not Specified
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When a generic class parameterized by a type variable tuple is used without
any type parameters and the TypeVarTuple has no default value, it behaves as
if the type variable tuple was substituted with ``tuple[Any, ...]``:

::

    def takes_any_array(arr: Array): ...

    # equivalent to:
    def takes_any_array(arr: Array[*tuple[Any, ...]]): ...

    x: Array[Height, Width]
    takes_any_array(x)  # Valid
    y: Array[Time, Height, Width]
    takes_any_array(y)  # Also valid

This enables gradual typing: existing functions accepting, for example,
a plain TensorFlow ``Tensor`` will still be valid even if ``Tensor`` is made
generic and calling code passes a ``Tensor[Height, Width]``.

This also works in the opposite direction:

::

    def takes_specific_array(arr: Array[Height, Width]): ...

    z: Array
    # equivalent to Array[*tuple[Any, ...]]

    takes_specific_array(z)

(For details, see the section on `Unpacking Unbounded Tuple Types`_.)

This way, even if libraries are updated to use types like ``Array[Height, Width]``,
users of those libraries won't be forced to also apply type annotations to
all of their code; users still have a choice about what parts of their code
to type and which parts to not.

Aliases
^^^^^^^

Generic aliases can be created using a type variable tuple in
a similar way to regular type variables:

::

    IntTuple = tuple[int, *Ts]
    NamedArray = tuple[str, Array[*Ts]]

    IntTuple[float, bool]  # Equivalent to tuple[int, float, bool]
    NamedArray[Height]     # Equivalent to tuple[str, Array[Height]]

As this example shows, all type parameters passed to the alias are
bound to the type variable tuple.

This allows us to define convenience aliases for arrays of a fixed shape
or datatype:

::

    Shape = TypeVarTuple('Shape')
    DType = TypeVar('DType')
    class Array(Generic[DType, *Shape]):

    # E.g. Float32Array[Height, Width, Channels]
    Float32Array = Array[np.float32, *Shape]

    # E.g. Array1D[np.uint8]
    Array1D = Array[DType, Any]

If an explicitly empty type parameter list is given, the type variable
tuple in the alias is set empty:

::

    IntTuple[()]    # Equivalent to tuple[int]
    NamedArray[()]  # Equivalent to tuple[str, Array[()]]

If the type parameter list is omitted entirely, the unspecified type
variable tuples are treated as ``tuple[Any, ...]`` (similar to
`Behavior when Type Parameters are not Specified`_):

::

    def takes_float_array_of_any_shape(x: Float32Array): ...
    x: Float32Array[Height, Width] = Array()
    takes_float_array_of_any_shape(x)  # Valid

    def takes_float_array_with_specific_shape(
        y: Float32Array[Height, Width]
    ): ...
    y: Float32Array = Array()
    takes_float_array_with_specific_shape(y)  # Valid

Normal ``TypeVar`` instances can also be used in such aliases:

::

    T = TypeVar('T')
    Foo = tuple[T, *Ts]

    # T bound to str, Ts to tuple[int]
    Foo[str, int]
    # T bound to float, Ts to tuple[()]
    Foo[float]
    # T bound to Any, Ts to an tuple[Any, ...]
    Foo


Substitution in Aliases
^^^^^^^^^^^^^^^^^^^^^^^

In the previous section, we only discussed simple usage of generic aliases
in which the type arguments were just simple types. However, a number of
more exotic constructions are also possible.


Type Arguments can be Variadic
""""""""""""""""""""""""""""""

First, type arguments to generic aliases can be variadic. For example, a
``TypeVarTuple`` can be used as a type argument:

::

    Ts1 = TypeVarTuple('Ts1')
    Ts2 = TypeVarTuple('Ts2')

    IntTuple = tuple[int, *Ts1]
    IntFloatTuple = IntTuple[float, *Ts2]  # Valid

Here, ``*Ts1`` in the ``IntTuple`` alias is bound to ``tuple[float, *Ts2]``,
resulting in an alias ``IntFloatTuple`` equivalent to
``tuple[int, float, *Ts2]``.

Unpacked arbitrary-length tuples can also be used as type arguments, with
similar effects:

::

    IntFloatsTuple = IntTuple[*tuple[float, ...]]  # Valid

Here, ``*Ts1`` is bound to ``*tuple[float, ...]``, resulting in
``IntFloatsTuple`` being equivalent to ``tuple[int, *tuple[float, ...]]``: a tuple
consisting of an ``int`` then zero or more ``float``\s.


Variadic Arguments Require Variadic Aliases
"""""""""""""""""""""""""""""""""""""""""""

Variadic type arguments can only be used with generic aliases that are
themselves variadic. For example:

::

    T = TypeVar('T')

    IntTuple = tuple[int, T]

    IntTuple[str]                 # Valid
    IntTuple[*Ts]                 # NOT valid
    IntTuple[*tuple[float, ...]]  # NOT valid

Here, ``IntTuple`` is a *non*-variadic generic alias that takes exactly one
type argument. Hence, it cannot accept ``*Ts`` or ``*tuple[float, ...]`` as type
arguments, because they represent an arbitrary number of types.


Aliases with Both TypeVars and TypeVarTuples
""""""""""""""""""""""""""""""""""""""""""""

In `Aliases`_, we briefly mentioned that aliases can be generic in both
``TypeVar``\s and ``TypeVarTuple``\s:

::

    T = TypeVar('T')
    Foo = tuple[T, *Ts]

    Foo[str, int]         # T bound to str, Ts to tuple[int]
    Foo[str, int, float]  # T bound to str, Ts to tuple[int, float]

In accordance with `Multiple Type Variable Tuples: Not Allowed`_, at most one
``TypeVarTuple`` may appear in the type parameters to an alias. However, a
``TypeVarTuple`` can be combined with an arbitrary number of ``TypeVar``\s,
both before and after:

::

    T1 = TypeVar('T1')
    T2 = TypeVar('T2')
    T3 = TypeVar('T3')

    tuple[*Ts, T1, T2]      # Valid
    tuple[T1, T2, *Ts]      # Valid
    tuple[T1, *Ts, T2, T3]  # Valid

In order to substitute these type variables with supplied type arguments,
any type variables at the beginning or end of the type parameter list first
consume type arguments, and then any remaining type arguments are bound
to the ``TypeVarTuple``:

::

    Shrubbery = tuple[*Ts, T1, T2]

    Shrubbery[str, bool]              # T2=bool,  T1=str,   Ts=tuple[()]
    Shrubbery[str, bool, float]       # T2=float, T1=bool,  Ts=tuple[str]
    Shrubbery[str, bool, float, int]  # T2=int,   T1=float, Ts=tuple[str, bool]

    Ptang = tuple[T1, *Ts, T2, T3]

    Ptang[str, bool, float]       # T1=str, T3=float, T2=bool,  Ts=tuple[()]
    Ptang[str, bool, float, int]  # T1=str, T3=int,   T2=float, Ts=tuple[bool]

Note that the minimum number of type arguments in such cases is set by
the number of ``TypeVar``\s:

::

    Shrubbery[int]  # Not valid; Shrubbery needs at least two type arguments


Splitting Arbitrary-Length Tuples
"""""""""""""""""""""""""""""""""

A final complication occurs when an unpacked arbitrary-length tuple is used
as a type argument to an alias consisting of both ``TypeVar``\s and a
``TypeVarTuple``:

::

    Elderberries = tuple[*Ts, T1]
    Hamster = Elderberries[*tuple[int, ...]]  # valid

In such cases, the arbitrary-length tuple is split between the ``TypeVar``\s
and the ``TypeVarTuple``. We assume the arbitrary-length tuple contains
at least as many items as there are ``TypeVar``\s, such that individual
instances of the inner type - here ``int`` - are bound to any ``TypeVar``\s
present. The 'rest' of the arbitrary-length tuple - here ``*tuple[int, ...]``,
since a tuple of arbitrary length minus two items is still arbitrary-length -
is bound to the ``TypeVarTuple``.

Here, therefore, ``Hamster`` is equivalent to ``tuple[*tuple[int, ...], int]``:
a tuple consisting of zero or more ``int``\s, then a final ``int``.

Of course, such splitting only occurs if necessary. For example, if we instead
did:

::

   Elderberries[*tuple[int, ...], str]

Then splitting would not occur; ``T1`` would be bound to ``str``, and
``Ts`` to ``*tuple[int, ...]``.

In particularly awkward cases, a ``TypeVarTuple`` may consume both a type
*and* a part of an arbitrary-length tuple type:

::

    Elderberries[str, *tuple[int, ...]]

Here, ``T1`` is bound to ``int``, and ``Ts`` is bound to
``tuple[str, *tuple[int, ...]]``. This expression is therefore equivalent to
``tuple[str, *tuple[int, ...], int]``: a tuple consisting of a ``str``, then
zero or more ``int``\s, ending with an ``int``.


TypeVarTuples Cannot be Split
"""""""""""""""""""""""""""""

Finally, although any arbitrary-length tuples in the type argument list can be
split between the type variables and the type variable tuple, the same is not
true of ``TypeVarTuple``\s in the argument list:

::

    Ts1 = TypeVarTuple('Ts1')
    Ts2 = TypeVarTuple('Ts2')

    Camelot = tuple[T, *Ts1]
    Camelot[*Ts2]  # NOT valid

This is not possible because, unlike in the case of an unpacked arbitrary-length
tuple, there is no way to 'peer inside' the ``TypeVarTuple`` to see what its
individual types are.


Overloads for Accessing Individual Types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For situations where we require access to each individual type in the type variable tuple,
overloads can be used with individual ``TypeVar`` instances in place of the type variable tuple:

::

    Shape = TypeVarTuple('Shape')
    Axis1 = TypeVar('Axis1')
    Axis2 = TypeVar('Axis2')
    Axis3 = TypeVar('Axis3')

    class Array(Generic[*Shape]):

      @overload
      def transpose(
        self: Array[Axis1, Axis2]
      ) -> Array[Axis2, Axis1]: ...

      @overload
      def transpose(
        self: Array[Axis1, Axis2, Axis3]
      ) -> Array[Axis3, Axis2, Axis1]: ...

(For array shape operations in particular, having to specify
overloads for each possible rank is, of course, a rather cumbersome
solution. However, it's the best we can do without additional type
manipulation mechanisms.)

.. _`type_parameter_defaults`:

Defaults for Type Parameters
----------------------------

(Originally specified in :pep:`696`.)

Default values can be provided for a TypeVar, ParamSpec, or TypeVarTuple.

Default Ordering and Subscription Rules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The order for defaults should follow the standard function parameter
rules, so a type parameter with no ``default`` cannot follow one with
a ``default`` value. Doing so may raise a ``TypeError`` at runtime,
and a type checker should flag this as an error.

::

   DefaultStrT = TypeVar("DefaultStrT", default=str)
   DefaultIntT = TypeVar("DefaultIntT", default=int)
   DefaultBoolT = TypeVar("DefaultBoolT", default=bool)
   T = TypeVar("T")
   T2 = TypeVar("T2")

   class NonDefaultFollowsDefault(Generic[DefaultStrT, T]): ...  # Invalid: non-default TypeVars cannot follow ones with defaults


   class NoNonDefaults(Generic[DefaultStrT, DefaultIntT]): ...

   (
       NoNonDefaults ==
       NoNonDefaults[str] ==
       NoNonDefaults[str, int]
   )  # All valid


   class OneDefault(Generic[T, DefaultBoolT]): ...

   OneDefault[float] == OneDefault[float, bool]  # Valid
   reveal_type(OneDefault)          # type is type[OneDefault[T, DefaultBoolT = bool]]
   reveal_type(OneDefault[float]()) # type is OneDefault[float, bool]


   class AllTheDefaults(Generic[T1, T2, DefaultStrT, DefaultIntT, DefaultBoolT]): ...

   reveal_type(AllTheDefaults)                  # type is type[AllTheDefaults[T1, T2, DefaultStrT = str, DefaultIntT = int, DefaultBoolT = bool]]
   reveal_type(AllTheDefaults[int, complex]())  # type is AllTheDefaults[int, complex, str, int, bool]
   AllTheDefaults[int]  # Invalid: expected 2 arguments to AllTheDefaults
   (
       AllTheDefaults[int, complex] ==
       AllTheDefaults[int, complex, str] ==
       AllTheDefaults[int, complex, str, int] ==
       AllTheDefaults[int, complex, str, int, bool]
   )  # All valid

With the new Python 3.12 syntax for generics (introduced by :pep:`695`), this can
be enforced at compile time::

   type Alias[DefaultT = int, T] = tuple[DefaultT, T]  # SyntaxError: non-default TypeVars cannot follow ones with defaults

   def generic_func[DefaultT = int, T](x: DefaultT, y: T) -> None: ...  # SyntaxError: non-default TypeVars cannot follow ones with defaults

   class GenericClass[DefaultT = int, T]: ...  # SyntaxError: non-default TypeVars cannot follow ones with defaults

``ParamSpec`` Defaults
^^^^^^^^^^^^^^^^^^^^^^

``ParamSpec`` defaults are defined using the same syntax as
``TypeVar`` \ s but use a ``list`` of types or an ellipsis
literal "``...``" or another in-scope ``ParamSpec`` (see `Scoping Rules`_).

::

   DefaultP = ParamSpec("DefaultP", default=[str, int])

   class Foo(Generic[DefaultP]): ...

   reveal_type(Foo)                  # type is type[Foo[DefaultP = [str, int]]]
   reveal_type(Foo())                # type is Foo[[str, int]]
   reveal_type(Foo[[bool, bool]]())  # type is Foo[[bool, bool]]

``TypeVarTuple`` Defaults
^^^^^^^^^^^^^^^^^^^^^^^^^

``TypeVarTuple`` defaults are defined using the same syntax as
``TypeVar`` \ s but use an unpacked tuple of types instead of a single type
or another in-scope ``TypeVarTuple`` (see `Scoping Rules`_).

::

   DefaultTs = TypeVarTuple("DefaultTs", default=Unpack[tuple[str, int]])

   class Foo(Generic[*DefaultTs]): ...

   reveal_type(Foo)               # type is type[Foo[DefaultTs = *tuple[str, int]]]
   reveal_type(Foo())             # type is Foo[str, int]
   reveal_type(Foo[int, bool]())  # type is Foo[int, bool]

Using Another Type Parameter as ``default``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This allows for a value to be used again when the type parameter to a
generic is missing but another type parameter is specified.

To use another type parameter as a default the ``default`` and the
type parameter must be the same type (a ``TypeVar``'s default must be
a ``TypeVar``, etc.).

::

   StartT = TypeVar("StartT", default=int)
   StopT = TypeVar("StopT", default=StartT)
   StepT = TypeVar("StepT", default=int | None)

   class slice(Generic[StartT, StopT, StepT]): ...

   reveal_type(slice)  # type is type[slice[StartT = int, StopT = StartT, StepT = int | None]]
   reveal_type(slice())                        # type is slice[int, int, int | None]
   reveal_type(slice[str]())                   # type is slice[str, str, int | None]
   reveal_type(slice[str, bool, timedelta]())  # type is slice[str, bool, timedelta]

   T2 = TypeVar("T2", default=DefaultStrT)

   class Foo(Generic[DefaultStrT, T2]):
       def __init__(self, a: DefaultStrT, b: T2) -> None: ...

   reveal_type(Foo(1, ""))  # type is Foo[int, str]
   Foo[int](1, "")          # Invalid: Foo[int, str] cannot be assigned to self: Foo[int, int] in Foo.__init__
   Foo[int]("", 1)          # Invalid: Foo[str, int] cannot be assigned to self: Foo[int, int] in Foo.__init__

When using a type parameter as the default to another type parameter, the
following rules apply, where ``T1`` is the default for ``T2``.

Scoping Rules
^^^^^^^^^^^^^

``T1`` must be used before ``T2`` in the parameter list of the generic.

::

   T2 = TypeVar("T2", default=T1)

   class Foo(Generic[T1, T2]): ...   # Valid

   StartT = TypeVar("StartT", default="StopT")  # Swapped defaults around from previous example
   StopT = TypeVar("StopT", default=int)
   class slice(Generic[StartT, StopT, StepT]): ...
                     # ^^^^^^ Invalid: ordering does not allow StopT to be bound

Using a type parameter from an outer scope as a default is not supported.

::

   class Foo(Generic[T1]):
       class Bar(Generic[T2]): ...   # Type Error

Bound Rules
^^^^^^^^^^^

``T1``'s bound must be :term:`assignable` to ``T2``'s bound.

::

   T1 = TypeVar("T1", bound=int)
   TypeVar("Ok", default=T1, bound=float)     # Valid
   TypeVar("AlsoOk", default=T1, bound=int)   # Valid
   TypeVar("Invalid", default=T1, bound=str)  # Invalid: int is not a subtype of str

Constraint Rules
^^^^^^^^^^^^^^^^

The constraints of ``T2`` must be a superset of the constraints of ``T1``.

::

   T1 = TypeVar("T1", bound=int)
   TypeVar("Invalid", float, str, default=T1)         # Invalid: upper bound int is incompatible with constraints float or str

   T1 = TypeVar("T1", int, str)
   TypeVar("AlsoOk", int, str, bool, default=T1)      # Valid
   TypeVar("AlsoInvalid", bool, complex, default=T1)  # Invalid: {bool, complex} is not a superset of {int, str}


Type Parameters as Parameters to Generics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Type parameters are valid as parameters to generics inside of a
``default`` when the first parameter is in scope as determined by the
`previous section <scoping rules_>`_.

::

   T = TypeVar("T")
   ListDefaultT = TypeVar("ListDefaultT", default=list[T])

   class Bar(Generic[T, ListDefaultT]):
       def __init__(self, x: T, y: ListDefaultT): ...

   reveal_type(Bar)                         # type is type[Bar[T, ListDefaultT = list[T]]]
   reveal_type(Bar[int])                    # type is type[Bar[int, list[int]]]
   reveal_type(Bar[int](0, []))             # type is Bar[int, list[int]]
   reveal_type(Bar[int, list[str]](0, []))  # type is Bar[int, list[str]]
   reveal_type(Bar[int, str](0, ""))        # type is Bar[int, str]

Specialization Rules
^^^^^^^^^^^^^^^^^^^^

Generic Type Aliases
""""""""""""""""""""

A generic type alias can be further subscripted following normal subscription
rules. If a type parameter has a default that hasn't been overridden, it should
be treated like it was substituted into the type alias.

::

   class SomethingWithNoDefaults(Generic[T, T2]): ...

   MyAlias: TypeAlias = SomethingWithNoDefaults[int, DefaultStrT]  # Valid
   reveal_type(MyAlias)          # type is type[SomethingWithNoDefaults[int, DefaultStrT]]
   reveal_type(MyAlias[bool]())  # type is SomethingWithNoDefaults[int, bool]

   MyAlias[bool, int]  # Invalid: too many arguments passed to MyAlias

Subclassing
"""""""""""

Generic classes with type parameters that have defaults behave similarly
to generic type aliases. That is, subclasses can be further subscripted following
normal subscription rules, non-overridden defaults should be substituted.

::

   class SubclassMe(Generic[T, DefaultStrT]):
       x: DefaultStrT

   class Bar(SubclassMe[int, DefaultStrT]): ...
   reveal_type(Bar)          # type is type[Bar[DefaultStrT = str]]
   reveal_type(Bar())        # type is Bar[str]
   reveal_type(Bar[bool]())  # type is Bar[bool]

   class Foo(SubclassMe[float]): ...

   reveal_type(Foo().x)  # type is str

   Foo[str]  # Invalid: Foo cannot be further subscripted

   class Baz(Generic[DefaultIntT, DefaultStrT]): ...

   class Spam(Baz): ...
   reveal_type(Spam())  # type is <subclass of Baz[int, str]>

Using ``bound`` and ``default``
"""""""""""""""""""""""""""""""

If both ``bound`` and ``default`` are passed, ``default`` must be
:term:`assignable` to ``bound``. If not, the type checker should generate an
error.

::

   TypeVar("Ok", bound=float, default=int)     # Valid
   TypeVar("Invalid", bound=str, default=int)  # Invalid: the bound and default are incompatible

Constraints
"""""""""""

For constrained ``TypeVar``\ s, the default needs to be one of the
constraints. A type checker should generate an error even if it is a
subtype of one of the constraints.

::

   TypeVar("Ok", float, str, default=float)     # Valid
   TypeVar("Invalid", float, str, default=int)  # Invalid: expected one of float or str got int

Function Defaults
"""""""""""""""""

In generic functions, type checkers may use a type parameter's default when the
type parameter cannot be solved to anything. We leave the semantics of this
usage unspecified, as ensuring the ``default`` is returned in every code path
where the type parameter can go unsolved may be too hard to implement. Type
checkers are free to either disallow this case or experiment with implementing
support.

::

   T = TypeVar('T', default=int)
   def func(x: int | set[T]) -> T: ...
   reveal_type(func(0))  # a type checker may reveal T's default of int here

Defaults following ``TypeVarTuple``
"""""""""""""""""""""""""""""""""""

A ``TypeVar`` that immediately follows a ``TypeVarTuple`` is not allowed
to have a default, because it would be ambiguous whether a type argument
should be bound to the ``TypeVarTuple`` or the defaulted ``TypeVar``.

::

   Ts = TypeVarTuple("Ts")
   T = TypeVar("T", default=bool)

   class Foo(Generic[*Ts, T]): ...  # Type checker error

   # Could be reasonably interpreted as either Ts = (int, str, float), T = bool
   # or Ts = (int, str), T = float
   Foo[int, str, float]

It is allowed to have a ``ParamSpec`` with a default following a
``TypeVarTuple`` with a default, as there can be no ambiguity between a type argument
for the ``ParamSpec`` and one for the ``TypeVarTuple``.

::

   Ts = TypeVarTuple("Ts")
   P = ParamSpec("P", default=[float, bool])

   class Foo(Generic[*Ts, P]): ...  # Valid

   Foo[int, str]  # Ts = (int, str), P = [float, bool]
   Foo[int, str, [bytes]]  # Ts = (int, str), P = [bytes]

Binding rules
"""""""""""""

Type parameter defaults should be bound by attribute access
(including call and subscript).

::

   class Foo[T = int]:
       def meth(self) -> Self:
           return self

   reveal_type(Foo.meth)  # type is (self: Foo[int]) -> Foo[int]


.. _`self`:

``Self``
--------

(Originally specified in :pep:`673`.)

Use in Method Signatures
^^^^^^^^^^^^^^^^^^^^^^^^

``Self`` used in the signature of a method is treated as if it were a
``TypeVar`` bound to the class.

::

    from typing import Self

    class Shape:
        def set_scale(self, scale: float) -> Self:
            self.scale = scale
            return self

is treated equivalently to:

::

    from typing import TypeVar

    SelfShape = TypeVar("SelfShape", bound="Shape")

    class Shape:
        def set_scale(self: SelfShape, scale: float) -> SelfShape:
            self.scale = scale
            return self

This works the same for a subclass too:

::

    class Circle(Shape):
        def set_radius(self, radius: float) -> Self:
            self.radius = radius
            return self

which is treated equivalently to:

::

    SelfCircle = TypeVar("SelfCircle", bound="Circle")

    class Circle(Shape):
        def set_radius(self: SelfCircle, radius: float) -> SelfCircle:
            self.radius = radius
            return self

One implementation strategy is to simply desugar the former to the latter in a
preprocessing step. If a method uses ``Self`` in its signature, the type of
``self`` within a method will be ``Self``. In other cases, the type of
``self`` will remain the enclosing class.


Use in Classmethod Signatures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``Self`` type annotation is also useful for classmethods that return
an instance of the class that they operate on. For example, ``from_config`` in
the following snippet builds a ``Shape`` object from a given ``config``.

::

    class Shape:
        def __init__(self, scale: float) -> None: ...

        @classmethod
        def from_config(cls, config: dict[str, float]) -> Shape:
            return cls(config["scale"])


However, this means that ``Circle.from_config(...)`` is inferred to return a
value of type ``Shape``, when in fact it should be ``Circle``:

::

    class Circle(Shape):
        def circumference(self) -> float: ...

    shape = Shape.from_config({"scale": 7.0})
    # => Shape

    circle = Circle.from_config({"scale": 7.0})
    # => *Shape*, not Circle

    circle.circumference()
    # Error: `Shape` has no attribute `circumference`


The current workaround for this is unintuitive and error-prone:

::

    Self = TypeVar("Self", bound="Shape")

    class Shape:
        @classmethod
        def from_config(
            cls: type[Self], config: dict[str, float]
        ) -> Self:
            return cls(config["scale"])

Instead, ``Self`` can be used directly:

::

    from typing import Self

    class Shape:
        @classmethod
        def from_config(cls, config: dict[str, float]) -> Self:
            return cls(config["scale"])

This avoids the complicated ``cls: type[Self]`` annotation and the ``TypeVar``
declaration with a ``bound``. Once again, the latter code behaves equivalently
to the former code.

Use in Parameter Types
^^^^^^^^^^^^^^^^^^^^^^

Another use for ``Self`` is to annotate parameters that expect instances of
the current class:

::

    Self = TypeVar("Self", bound="Shape")

    class Shape:
        def difference(self: Self, other: Self) -> float: ...

        def apply(self: Self, f: Callable[[Self], None]) -> None: ...

``Self`` can be used directly to achieve the same behavior:

::

    from typing import Self

    class Shape:
        def difference(self, other: Self) -> float: ...

        def apply(self, f: Callable[[Self], None]) -> None: ...

Note that specifying ``self: Self`` is harmless, so some users may find it
more readable to write the above as:

::

    class Shape:
        def difference(self: Self, other: Self) -> float: ...

Use in Attribute Annotations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another use for ``Self`` is to annotate attributes. One example is where we
have a ``LinkedList`` whose elements must be :term:`assignable` to the current
class.

::

    from dataclasses import dataclass
    from typing import Generic, TypeVar

    T = TypeVar("T")

    @dataclass
    class LinkedList(Generic[T]):
        value: T
        next: LinkedList[T] | None = None

    # OK
    LinkedList[int](value=1, next=LinkedList[int](value=2))
    # Not OK
    LinkedList[int](value=1, next=LinkedList[str](value="hello"))


However, annotating the ``next`` attribute as ``LinkedList[T]`` allows invalid
constructions with subclasses:

::

    @dataclass
    class OrdinalLinkedList(LinkedList[int]):
        def ordinal_value(self) -> str:
            return as_ordinal(self.value)

    # Should not be OK because LinkedList[int] is not assignable to
    # OrdinalLinkedList, but the type checker allows it.
    xs = OrdinalLinkedList(value=1, next=LinkedList[int](value=2))

    if xs.next:
        print(xs.next.ordinal_value())  # Runtime Error.


This constraint can be expressed using ``next: Self | None``:

::

    from typing import Self

    @dataclass
    class LinkedList(Generic[T]):
        value: T
        next: Self | None = None

    @dataclass
    class OrdinalLinkedList(LinkedList[int]):
        def ordinal_value(self) -> str:
            return as_ordinal(self.value)

    xs = OrdinalLinkedList(value=1, next=LinkedList[int](value=2))
    # Type error: Expected OrdinalLinkedList, got LinkedList[int].

    if xs.next is not None:
        xs.next = OrdinalLinkedList(value=3, next=None)  # OK
        xs.next = LinkedList[int](value=3, next=None)  # Not OK



The code above is semantically equivalent to treating each attribute
containing a ``Self`` type as a ``property`` that returns that type:

::

    from dataclasses import dataclass
    from typing import Any, Generic, TypeVar

    T = TypeVar("T")
    Self = TypeVar("Self", bound="LinkedList")


    class LinkedList(Generic[T]):
        value: T

        @property
        def next(self: Self) -> Self | None:
            return self._next

        @next.setter
        def next(self: Self, next: Self | None) -> None:
            self._next = next

    class OrdinalLinkedList(LinkedList[int]):
        def ordinal_value(self) -> str:
            return str(self.value)

Use in Generic Classes
^^^^^^^^^^^^^^^^^^^^^^

``Self`` can also be used in generic class methods:

::

    class Container(Generic[T]):
        value: T
        def set_value(self, value: T) -> Self: ...


This is equivalent to writing:

::

    Self = TypeVar("Self", bound="Container[Any]")

    class Container(Generic[T]):
        value: T
        def set_value(self: Self, value: T) -> Self: ...


The behavior is to preserve the type argument of the object on which the
method was called. When called on an object with concrete type
``Container[int]``, ``Self`` is bound to ``Container[int]``. When called with
an object of generic type ``Container[T]``, ``Self`` is bound to
``Container[T]``:

::

    def object_with_concrete_type() -> None:
        int_container: Container[int]
        str_container: Container[str]
        reveal_type(int_container.set_value(42))  # => Container[int]
        reveal_type(str_container.set_value("hello"))  # => Container[str]

    def object_with_generic_type(
        container: Container[T], value: T,
    ) -> Container[T]:
        return container.set_value(value)  # => Container[T]


The PEP doesn’t specify the exact type of ``self.value`` within the method
``set_value``. Some type checkers may choose to implement ``Self`` types using
class-local type variables with ``Self = TypeVar(“Self”,
bound=Container[T])``, which will infer a precise type ``T``. However, given
that class-local type variables are not a standardized type system feature, it
is also acceptable to infer ``Any`` for ``self.value``. We leave this up to
the type checker.

Note that we reject using ``Self`` with type arguments, such as ``Self[int]``.
This is because it creates ambiguity about the type of the ``self`` parameter
and introduces unnecessary complexity:

::

    class Container(Generic[T]):
        def foo(
            self, other: Self[int], other2: Self,
        ) -> Self[str]:  # Rejected
            ...

In such cases, we recommend using an explicit type for ``self``:

::

    class Container(Generic[T]):
        def foo(
            self: Container[T],
            other: Container[int],
            other2: Container[T]
        ) -> Container[str]: ...


Use in Protocols
^^^^^^^^^^^^^^^^

``Self`` is valid within Protocols, similar to its use in classes:

::

    from typing import Protocol, Self

    class ShapeProtocol(Protocol):
        scale: float

        def set_scale(self, scale: float) -> Self:
            self.scale = scale
            return self

is treated equivalently to:

::

    from typing import TypeVar

    SelfShape = TypeVar("SelfShape", bound="ShapeProtocol")

    class ShapeProtocol(Protocol):
        scale: float

        def set_scale(self: SelfShape, scale: float) -> SelfShape:
            self.scale = scale
            return self


See :pep:`PEP 544
<544#self-types-in-protocols>` for
details on the behavior of TypeVars bound to protocols.

Checking a class for assignability to a protocol: If a protocol uses ``Self``
in methods or attribute annotations, then a class ``Foo`` is :term:`assignable`
to the protocol if its corresponding methods and attribute annotations use
either ``Self`` or ``Foo`` or any of ``Foo``’s subclasses. See the examples
below:

::

    from typing import Protocol

    class ShapeProtocol(Protocol):
        def set_scale(self, scale: float) -> Self: ...

    class ReturnSelf:
        scale: float = 1.0

        def set_scale(self, scale: float) -> Self:
            self.scale = scale
            return self

    class ReturnConcreteShape:
        scale: float = 1.0

        def set_scale(self, scale: float) -> ReturnConcreteShape:
            self.scale = scale
            return self

    class BadReturnType:
        scale: float = 1.0

        def set_scale(self, scale: float) -> int:
            self.scale = scale
            return 42

    class ReturnDifferentClass:
        scale: float = 1.0

        def set_scale(self, scale: float) -> ReturnConcreteShape:
            return ReturnConcreteShape(...)

    def accepts_shape(shape: ShapeProtocol) -> None:
        y = shape.set_scale(0.5)
        reveal_type(y)

    def main() -> None:
        return_self_shape: ReturnSelf
        return_concrete_shape: ReturnConcreteShape
        bad_return_type: BadReturnType
        return_different_class: ReturnDifferentClass

        accepts_shape(return_self_shape)  # OK
        accepts_shape(return_concrete_shape)  # OK
        accepts_shape(bad_return_type)  # Not OK
        # Not OK because it returns a non-subclass.
        accepts_shape(return_different_class)


Valid Locations for ``Self``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``Self`` annotation is only valid in class contexts, and will always refer
to the encapsulating class. In contexts involving nested classes, ``Self``
will always refer to the innermost class.

The following uses of ``Self`` are accepted:

::

    class ReturnsSelf:
        def foo(self) -> Self: ... # Accepted

        @classmethod
        def bar(cls) -> Self:  # Accepted
            return cls()

        def __new__(cls, value: int) -> Self: ...  # Accepted

        def explicitly_use_self(self: Self) -> Self: ...  # Accepted

        # Accepted (Self can be nested within other types)
        def returns_list(self) -> list[Self]: ...

        # Accepted (Self can be nested within other types)
        @classmethod
        def return_cls(cls) -> type[Self]:
            return cls

    class Child(ReturnsSelf):
        # Accepted (we can override a method that uses Self annotations)
        def foo(self) -> Self: ...

    class TakesSelf:
        def foo(self, other: Self) -> bool: ...  # Accepted

    class Recursive:
        # Accepted (treated as an @property returning ``Self | None``)
        next: Self | None

    class CallableAttribute:
        def foo(self) -> int: ...

        # Accepted (treated as an @property returning the Callable type)
        bar: Callable[[Self], int] = foo

    class HasNestedFunction:
        x: int = 42

        def foo(self) -> None:

            # Accepted (Self is bound to HasNestedFunction).
            def nested(z: int, inner_self: Self) -> Self:
                print(z)
                print(inner_self.x)
                return inner_self

            nested(42, self)  # OK


    class Outer:
        class Inner:
            def foo(self) -> Self: ...  # Accepted (Self is bound to Inner)


The following uses of ``Self`` are rejected.

::

    def foo(bar: Self) -> Self: ...  # Rejected (not within a class)

    bar: Self  # Rejected (not within a class)

    class Foo:
        # Rejected (Self is treated as unknown).
        def has_existing_self_annotation(self: T) -> Self: ...

    class Foo:
        def return_concrete_type(self) -> Self:
            return Foo()  # Rejected (see FooChild below for rationale)

    class FooChild(Foo):
        child_value: int = 42

        def child_method(self) -> None:
            # At runtime, this would be Foo, not FooChild.
            y = self.return_concrete_type()

            y.child_value
            # Runtime error: Foo has no attribute child_value

    class Bar(Generic[T]):
        def bar(self) -> T: ...

    class Baz(Bar[Self]): ...  # Rejected

We reject type aliases containing ``Self``. Supporting ``Self``
outside class definitions can require a lot of special-handling in
type checkers. Given that it also goes against the rest of the PEP to
use ``Self`` outside a class definition, we believe the added
convenience of aliases is not worth it:

::

    TupleSelf = Tuple[Self, Self]  # Rejected

    class Alias:
        def return_tuple(self) -> TupleSelf:  # Rejected
            return (self, self)

Note that we reject ``Self`` in staticmethods. ``Self`` does not add much
value since there is no ``self`` or ``cls`` to return. The only possible use
cases would be to return a parameter itself or some element from a container
passed in as a parameter. These don’t seem worth the additional complexity.

::

    class Base:
        @staticmethod
        def make() -> Self:  # Rejected
            ...

        @staticmethod
        def return_parameter(foo: Self) -> Self:  # Rejected
            ...

Likewise, we reject ``Self`` in metaclasses. ``Self`` consistently refers to the
same type (that of ``self``). But in metaclasses, it would have to refer to
different types in different method signatures. For example, in ``__mul__``,
``Self`` in the return type would refer to the implementing class
``Foo``, not the enclosing class ``MyMetaclass``. But, in ``__new__``, ``Self``
in the return type would refer to the enclosing class ``MyMetaclass``. To
avoid confusion, we reject this edge case.

::

    class MyMetaclass(type):
        def __new__(cls, *args: Any) -> Self:  # Rejected
            return super().__new__(cls, *args)

        def __mul__(cls, count: int) -> list[Self]:  # Rejected
            return [cls()] * count

    class Foo(metaclass=MyMetaclass): ...

.. _`variance-inference`:

Variance Inference
------------------

(Originally specified by :pep:`695`.)

The introduction of explicit syntax for generic classes in Python 3.12
eliminates the need for variance to be specified for type
parameters. Instead, type checkers will infer the variance of type parameters
based on their usage within a class. Type parameters are inferred to be
invariant, covariant, or contravariant depending on how they are used.

Python type checkers already include the ability to determine the variance of
type parameters for the purpose of validating variance within a generic
protocol class. This capability can be used for all classes (whether or not
they are protocols) to calculate the variance of each type parameter.

The algorithm for computing the variance of a type parameter is as follows.

For each type parameter in a generic class:

1. If the type parameter is variadic (``TypeVarTuple``) or a parameter
specification (``ParamSpec``), it is always considered invariant. No further
inference is needed.

2. If the type parameter comes from a traditional ``TypeVar`` declaration and
is not specified as ``infer_variance`` (see below), its variance is specified
by the ``TypeVar`` constructor call. No further inference is needed.

3. Create two specialized versions of the class. We'll refer to these as
``upper`` and ``lower`` specializations. In both of these specializations,
replace all type parameters other than the one being inferred by a dummy type
instance (a concrete anonymous class that is assumed to meet the bounds or
constraints of the type parameter). In the ``upper`` specialized class,
specialize the target type parameter with an ``object`` instance. This
specialization ignores the type parameter's upper bound or constraints. In the
``lower`` specialized class, specialize the target type parameter with itself
(i.e. the corresponding type argument is the type parameter itself).

4. Determine whether ``lower`` can be assigned to ``upper`` using normal
assignability rules. If so, the target type parameter is covariant. If not,
determine whether ``upper`` can be assigned to ``lower``. If so, the target
type parameter is contravariant. If neither of these combinations are
assignable, the target type parameter is invariant.

Here is an example.

::

    class ClassA[T1, T2, T3](list[T1]):
        def method1(self, a: T2) -> None:
            ...

        def method2(self) -> T3:
            ...

To determine the variance of ``T1``, we specialize ``ClassA`` as follows:

::

    upper = ClassA[object, Dummy, Dummy]
    lower = ClassA[T1, Dummy, Dummy]

We find that ``upper`` is not assignable to ``lower``. Likewise, ``lower`` is
not assignable to ``upper``, so we conclude that ``T1`` is invariant.

To determine the variance of ``T2``, we specialize ``ClassA`` as follows:

::

    upper = ClassA[Dummy, object, Dummy]
    lower = ClassA[Dummy, T2, Dummy]

Since ``upper`` is assignable to ``lower``, ``T2`` is contravariant.

To determine the variance of ``T3``, we specialize ``ClassA`` as follows:

::

    upper = ClassA[Dummy, Dummy, object]
    lower = ClassA[Dummy, Dummy, T3]

Since ``lower`` is assignable to ``upper``, ``T3`` is covariant.


Auto Variance For TypeVar
^^^^^^^^^^^^^^^^^^^^^^^^^

The existing ``TypeVar`` class constructor accepts keyword parameters named
``covariant`` and ``contravariant``. If both of these are ``False``, the
type variable is assumed to be invariant. PEP 695 adds another keyword
parameter named ``infer_variance`` indicating that a type checker should use
inference to determine whether the type variable is invariant, covariant or
contravariant. A corresponding instance variable ``__infer_variance__`` can be
accessed at runtime to determine whether the variance is inferred. Type
variables that are implicitly allocated using the new syntax will always
have ``__infer_variance__`` set to ``True``.

A generic class that uses the traditional syntax may include combinations of
type variables with explicit and inferred variance.

::

    T1 = TypeVar("T1", infer_variance=True)  # Inferred variance
    T2 = TypeVar("T2")  # Invariant
    T3 = TypeVar("T3", covariant=True)  # Covariant

    # A type checker should infer the variance for T1 but use the
    # specified variance for T2 and T3.
    class ClassA(Generic[T1, T2, T3]): ...


Compatibility with Traditional TypeVars
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The existing mechanism for allocating ``TypeVar``, ``TypeVarTuple``, and
``ParamSpec`` is retained for backward compatibility. However, these
"traditional" type variables should not be combined with type parameters
allocated using the new syntax. Such a combination should be flagged as
an error by type checkers. This is necessary because the type parameter
order is ambiguous.

It is OK to combine traditional type variables with new-style type parameters
if the class, function, or type alias does not use the new syntax. The
new-style type parameters must come from an outer scope in this case.

::

    K = TypeVar("K")

    class ClassA[V](dict[K, V]): ...  # Type checker error

    class ClassB[K, V](dict[K, V]): ...  # OK

    class ClassC[V]:
        # The use of K and V for "method1" is OK because it uses the
        # "traditional" generic function mechanism where type parameters
        # are implicit. In this case V comes from an outer scope (ClassC)
        # and K is introduced implicitly as a type parameter for "method1".
        def method1(self, a: V, b: K) -> V | K: ...

        # The use of M and K are not allowed for "method2". A type checker
        # should generate an error in this case because this method uses the
        # new syntax for type parameters, and all type parameters associated
        # with the method must be explicitly declared. In this case, ``K``
        # is not declared by "method2", nor is it supplied by a new-style
        # type parameter defined in an outer scope.
        def method2[M](self, a: M, b: K) -> M | K: ...
