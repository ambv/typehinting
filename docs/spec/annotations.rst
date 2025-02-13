.. _`type-annotations`:

Type annotations
================

The meaning of annotations
--------------------------

The type system leverages :pep:`3107`-style annotations with a number of
extensions described in sections below.  In its basic form, type
hinting is used by filling function annotation slots with classes::

  def greeting(name: str) -> str:
      return 'Hello ' + name

This states that the expected type of the ``name`` argument is
``str``.  Analogically, the expected return type is ``str``.

Expressions whose type is :term:`assignable` to a specific argument type are
also accepted for that argument. Similarly, an expression whose type is
assignable to the annotated return type can be returned from the function.

.. _`missing-annotations`:

Any function without annotations can be treated as having :ref:`Any`
annotations on all arguments and the return type. Type checkers may also
optionally infer more precise types for missing annotations.

Type checkers may choose to entirely ignore (not type check) the bodies of
functions with no annotations, but this behavior is not required.

It is recommended but not required that checked functions have
annotations for all arguments and the return type.  For a checked
function, the default annotation for arguments and for the return type
is ``Any``. An exception to the above is the first argument of
instance and class methods (conventionally named ``self`` or ``cls``),
which type checkers should assume to have an appropriate type, as per
:ref:`annotating-methods`.

(Note that the return type of ``__init__`` ought to be annotated with
``-> None``.  The reason for this is subtle.  If ``__init__`` assumed
a return annotation of ``-> None``, would that mean that an
argument-less, un-annotated ``__init__`` method should still be
type-checked?  Rather than leaving this ambiguous or introducing an
exception to the exception, we simply say that ``__init__`` ought to
have a return annotation; the default behavior is thus the same as for
other methods.)

A type checker is expected to check the body of a checked function for
consistency with the given annotations.  The annotations may also be
used to check correctness of calls appearing in other checked functions.

Type checkers are expected to attempt to infer as much information as
necessary.  The minimum requirement is to handle the builtin
decorators ``@property``, ``@staticmethod`` and ``@classmethod``.

.. _valid-types:

Type and annotation expressions
-------------------------------

The terms *type expression* and *annotation expression* denote specific
subsets of Python expressions that are used in the type system.  All
type expressions are also annotation expressions, but not all annotation
expressions are type expressions.

.. _`type-expression`:

A *type expression* is any expression that validly expresses a type. Type
expressions are always acceptable in annotations and also in various other
places. Specifically, type expressions are used in the following locations:

* In a type annotation (always as part of an annotation expression)
* The first argument to :ref:`cast() <cast>`
* The second argument to :ref:`assert_type() <assert-type>`
* The bounds and constraints of a ``TypeVar`` (whether created through the
  old syntax or the native syntax in Python 3.12)
* The definition of a type alias (whether created through the ``type`` statement,
  the old assignment syntax, or the ``TypeAliasType`` constructor)
* The type arguments of a generic class (which may appear in a base class
  or in a constructor call)
* The definitions of fields in the functional forms for creating
  :ref:`TypedDict <typeddict>` and :ref:`NamedTuple <namedtuple>` types
* The base type in the definition of a :ref:`NewType <newtype>`

.. _`annotation-expression`:

An *annotation expression* is an expression that is acceptable to use in
an annotation context (a function parameter annotation, function return
annotation, or variable annotation). Generally, an annotation expression
is a type expression, optionally surrounded by one or more :term:`type qualifiers <type qualifier>`
or by `Annotated`. Each type qualifier is valid only in some contexts. Note
that while annotation expressions are the only expressions valid as type
annotations in the type system, the Python language itself makes no such
restriction: any expression is allowed.

Annotations must be valid expressions that evaluate without raising
exceptions at the time the function is defined (but see :ref:`forward-references`).

.. _`expression-grammar`:

The following grammar describes the allowed elements of type and annotation expressions:

.. productionlist:: expression-grammar
    annotation_expression: <Required> '[' `annotation_expression` ']'
                         : | <NotRequired> '[' `annotation_expression` ']'
                         : | <ReadOnly> '[' `annotation_expression`']'
                         : | <ClassVar> '[' `annotation_expression`']'
                         : | <Final> ('[' `annotation_expression`']')?
                         : | <InitVar> '[' `annotation_expression` ']'
                         : | <Annotated> '[' `annotation_expression` ','
                         :               expression (',' expression)* ']'
                         : | <TypeAlias>
                         :       (valid only in variable annotations)
                         : | `unpacked`
                         :       (valid only for *args annotations)
                         : | <Unpack> '[' name ']'
                         :       (where name refers to an in-scope TypedDict;
                         :        valid only in **kwargs annotations)
                         : | `string_annotation`
                         :       (must evaluate to a valid `annotation_expression`)
                         : | name '.' 'args'
                         :      (where name must be an in-scope ParamSpec;
                         :       valid only in *args annotations)
                         : | name '.' 'kwargs'
                         :       (where name must be an in-scope ParamSpec;
                         :        valid only in **kwargs annotations)
                         : | `type_expression`
    type_expression: <Any>
                   : | <Self>
                   :       (valid only in some contexts)
                   : | <LiteralString>
                   : | <NoReturn>
                   : | <Never>
                   : | <None>
                   : | name
                   :       (where name must refer to a valid in-scope class,
                   :        type alias, or TypeVar)
                   : | name '[' (`maybe_unpacked` | `type_expression_list`)
                   :        (',' (`maybe_unpacked` | `type_expression_list`))* ']'
                   :       (the `type_expression_list` form is valid only when
                   :        specializing a ParamSpec)
                   : | name '[' '(' ')' ']'
                   :       (denoting specialization with an empty TypeVarTuple)
                   : | <Literal> '[' expression (',' expression) ']'
                   :       (see documentation for Literal for restrictions)
                   : | `type_expression` '|' `type_expression`
                   : | <Optional> '[' `type_expression` ']'
                   : | <Union> '[' `type_expression` (',' `type_expression`)* ']'
                   : | <type> '[' <Any> ']'
                   : | <type> '[' name ']'
                   :       (where name must refer to a valid in-scope class
                   :        or TypeVar)
                   : | <Callable> '[' '...' ',' `type_expression` ']'
                   : | <Callable> '[' name ',' `type_expression` ']'
                   :       (where name must be a valid in-scope ParamSpec)
                   : | <Callable> '[' <Concatenate> '[' (`type_expression` ',')+
                   :              (name | '...') ']' ',' `type_expression` ']'
                   :       (where name must be a valid in-scope ParamSpec)
                   : | <Callable> '[' '[' `maybe_unpacked` (',' `maybe_unpacked`)*
                   :              ']' ',' `type_expression` ']'
                   : | `tuple_type_expression`
                   : | <Annotated> '[' `type_expression` ','
                   :               expression (',' expression)* ']'
                   : | <TypeGuard> '[' `type_expression` ']'
                   :       (valid only in some contexts)
                   : | <TypeIs> '[' `type_expression` ']'
                   :       (valid only in some contexts)
                   : | `string_annotation`
                   :       (must evaluate to a valid `type_expression`)
    maybe_unpacked: `type_expression` | `unpacked`
    unpacked: '*' `unpackable`
            : | <Unpack> '[' `unpackable` ']'
    unpackable: `tuple_type_expression``
              : | name
              :       (where name must refer to an in-scope TypeVarTuple)
    tuple_type_expression: <tuple> '[' '(' ')' ']'
                         :      (representing an empty tuple)
                         : | <tuple> '[' `type_expression` ',' '...' ']'
                         :       (representing an arbitrary-length tuple)
                         : | <tuple> '[' `maybe_unpacked` (',' `maybe_unpacked`)* ']'
    string_annotation: string
                     :     (must be a string literal that is parsable
                     :      as Python code; see "String annotations")
    type_expression_list: '[' `type_expression` (',' `type_expression`)* ']'
                        : | '[' ']'

Notes:

* The grammar assumes the code has already been parsed as Python code, and
  loosely follows the structure of the AST. Syntactic details like comments
  and whitespace are ignored.

* ``<Name>`` refers to a :term:`special form`. Most special forms must be imported
  from :py:mod:`typing` or ``typing_extensions``, except for ``None``,  ``InitVar``,
  ``type``, and ``tuple``. The latter two have aliases in :py:mod:`typing`: :py:class:`typing.Type`
  and :py:class:`typing.Tuple`.  ``InitVar`` must be imported from :py:mod:`dataclasses`.
  ``Callable`` may be imported from either :py:mod:`typing` or :py:mod:`collections.abc`.
  Special forms may be aliased
  (e.g., ``from typing import Literal as L``), and they may be referred to by a
  qualified name (e.g., ``typing.Literal``). There are other special forms that are not
  acceptable in any annotation or type expression, including ``Generic``, ``Protocol``,
  and ``TypedDict``.

* Any leaf denoted as ``name`` may also be a qualified name (i.e., ``module '.' name``
  or ``package '.' module '.' name``, with any level of nesting).

* Comments in parentheses denote additional restrictions not expressed in the
  grammar, or brief descriptions of the meaning of a construct.

.. _ `string-annotations`:

.. _`forward-references`:

String annotations
------------------

When a type hint cannot be evaluated at runtime, that
definition may be expressed as a string literal, to be resolved later.

A situation where this occurs commonly is the definition of a
container class, where the class being defined occurs in the signature
of some of the methods.  For example, the following code (the start of
a simple binary tree implementation) does not work::

  class Tree:
      def __init__(self, left: Tree, right: Tree):
          self.left = left
          self.right = right

To address this, we write::

  class Tree:
      def __init__(self, left: 'Tree', right: 'Tree'):
          self.left = left
          self.right = right

The string literal should contain a valid Python expression (i.e.,
``compile(lit, '', 'eval')`` should be a valid code object) and it
should evaluate without errors once the module has been fully loaded.
The local and global namespace in which it is evaluated should be the
same namespaces in which default arguments to the same function would
be evaluated.

Moreover, the expression should be parseable as a valid type hint, i.e.,
it is constrained by the rules from :ref:`the expression grammar <expression-grammar>`.

If a triple quote is used, the string should be parsed as though it is
implicitly surrounded by parentheses. This allows newline characters to be
used within the string literal::

    value: """
        int |
        str |
        list[Any]
    """

It is allowable to use string literals as *part* of a type hint, for
example::

    class Tree:
        ...
        def leaves(self) -> list['Tree']:
            ...

A common use for forward references is when e.g. Django models are
needed in the signatures.  Typically, each model is in a separate
file, and has methods taking arguments whose type involves other models.
Because of the way circular imports work in Python, it is often not
possible to import all the needed models directly::

    # File models/a.py
    from models.b import B
    class A(Model):
        def foo(self, b: B): ...

    # File models/b.py
    from models.a import A
    class B(Model):
        def bar(self, a: A): ...

    # File main.py
    from models.a import A
    from models.b import B

Assuming main is imported first, this will fail with an ImportError at
the line ``from models.a import A`` in models/b.py, which is being
imported from models/a.py before a has defined class A.  The solution
is to switch to module-only imports and reference the models by their
_module_._class_ name::

    # File models/a.py
    from models import b
    class A(Model):
        def foo(self, b: 'b.B'): ...

    # File models/b.py
    from models import a
    class B(Model):
        def bar(self, a: 'a.A'): ...

    # File main.py
    from models.a import A
    from models.b import B

Annotating generator functions and coroutines
---------------------------------------------

The return type of generator functions can be annotated by
the generic type ``Generator[yield_type, send_type,
return_type]`` provided by ``typing.py`` module::

  def echo_round() -> Generator[int, float, str]:
      res = yield 0
      while res:
          res = yield round(res)
      return 'OK'

Coroutines introduced in :pep:`492` are annotated with the same syntax as
ordinary functions. However, the return type annotation corresponds to the
type of ``await`` expression, not to the coroutine type::

  async def spam(ignored: int) -> str:
      return 'spam'

  async def foo() -> None:
      bar = await spam(42)  # type is str

The generic ABC ``collections.abc.Coroutine`` can be used
to specify awaitables that also support
``send()`` and ``throw()`` methods. The variance and order of type variables
correspond to those of ``Generator``, namely ``Coroutine[T_co, T_contra, V_co]``,
for example::

  from collections.abc import Coroutine
  c: Coroutine[list[str], str, int]
  ...
  x = c.send('hi')  # type is list[str]
  async def bar() -> None:
      x = await c  # type is int

The generic ABCs ``Awaitable``,
``AsyncIterable``, and ``AsyncIterator`` can be used for situations where more precise
types cannot be specified::

  def op() -> collections.abc.Awaitable[str]:
      if cond:
          return spam(42)
      else:
          return asyncio.Future(...)

.. _`annotating-methods`:

Annotating instance and class methods
-------------------------------------

In most cases the first argument of instance and class methods
(conventionally named ``self`` or ``cls``) does not need to be annotated.

If the argument is not annotated, then for instance methods it is
assumed to have the type of the containing class or :ref:`Self
<self>`, and for class methods the type object type corresponding to
the containing class object or ``type[Self]``.

In addition, the first argument in an instance method can be annotated
with a type variable. In this case the return type may use the same
type variable, thus making that method a generic function. For example::

  T = TypeVar('T', bound='Copyable')
  class Copyable:
      def copy(self: T) -> T:
          # return a copy of self

  class C(Copyable): ...
  c = C()
  c2 = c.copy()  # type here should be C

The same applies to class methods using ``type[]`` in an annotation
of the first argument::

  T = TypeVar('T', bound='C')
  class C:
      @classmethod
      def factory(cls: type[T]) -> T:
          # make a new instance of cls

  class D(C): ...
  d = D.factory()  # type here should be D

Note that some type checkers may apply restrictions on this use, such as
requiring an appropriate upper bound for the type variable used
(see examples).
