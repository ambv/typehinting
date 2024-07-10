.. _libraries:

***********************
Typing Python Libraries
***********************

Much of Python's popularity can be attributed to the rich collection of
Python libraries available to developers. Authors of these libraries
play an important role in improving the experience for Python
developers. This document provides some recommendations and guidance for
Python library authors.

Why provide type annotations?
=============================

Providing type annotations has the following benefits:

1. Type annotations help provide users of libraries a better coding
   experience by enabling fast and accurate completion suggestions, class and
   function documentation, signature help, hover text, auto-imports, etc.
2. Users of libraries are able to use static type checkers to detect issues
   with their use of libraries.
3. Type annotations allow library authors to specify an interface contract that
   is enforced by tools. This lets the library implementation evolve with less
   fear that users are depending on implementation details. In the event of
   changes to the library interface, type checkers are able to warn users when
   their code is affected.
4. Library authors are able to use static type checking themselves to help
   produce high-quality, bug-free implementations.

.. _providing-type-annotations:

How to provide type annotations?
================================

:pep:`561` documents several ways type information can be provided for a
library:

- inline type annotations (preferred)
- type stub files included in the package
- a separate companion type stub package
- type stubs in the typeshed repository

Inline type annotations simply refers to the use of annotations within your
``.py`` files. In contrast, with type stub files, type information lives in
separate ``.pyi`` files; see :ref:`stubs` and :ref:`writing_stubs` for more
details.

We recommend using the inline type annotations approach, since it has the
following benefits:

- Typically requires the least effort to add and maintain
- Users don't have to download additional packages
- Always remains consistent with the implementation
- Allows library authors to type check their own code
- Allows language servers to show users relevant details about the
  implementation, such as docstrings and default parameter values

However, there are cases where inlined type annotations are not possible — most
notably when a library's functionality is implemented in a language
other than Python.

If you are not interested in providing type annotations for your library, you
could suggest users to contribute type stubs to the
`typeshed <https://github.com/python/typeshed>`__ project.

Marking a package as providing type information
-----------------------------------------------

As specified in :pep:`561`, tools will not treat your package as providing type
information unless it includes a special ``py.typed`` marker file.

.. note::
   Before marking a package as providing type information, it is best to ensure
   that the library's interface is fully annotated. See :ref:`type_completeness`
   for more details.

Inline type annotations
^^^^^^^^^^^^^^^^^^^^^^^

A typical directory structure would look like:

.. code-block:: text

   setup.py
   my_great_package/
      __init__.py
      stuff.py
      py.typed

It's important to ensure that the ``py.typed`` marker file is included in the
distributed package. If using ``setuptools``, this can be achieved like so:

.. code-block:: python

   from setuptools import setup

   setup(
      name="my_great_distribution",
      version="0.1",
      package_data={"my_great_package": ["py.typed"]},
      packages=["my_great_package"],
   )


Type stub files included in the package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It's possible to include a mix of type stub files (``.pyi``) and inline type
annotations (``.py``). One use case for including type stub files in your
package is to provide types for extension modules in your library. A typical
directory structure would look like:

.. code-block:: text

   setup.py
   my_great_package/
      __init__.py
      stuff.py
      stuff.pyi
      py.typed

If using ``setuptools``, we can ensure the ``.pyi`` and ``py.typed`` files are
included like so:

.. code-block:: python

   from setuptools import setup

   setup(
      name="my_great_distribution",
      version="0.1",
      package_data={"my_great_package": ["py.typed", "stuff.pyi"]},
      packages=["my_great_package"],
   )

The presence of ``.pyi`` files does not affect the Python interpreter at runtime
in any way. However, static type checkers will only look at the ``.pyi`` file and
ignore the corresponding ``.py`` file.

Companion type stub package
^^^^^^^^^^^^^^^^^^^^^^^^^^^

These are often referred to as "stub-only" packages. The name of the stub package
should be the name of the runtime package suffixed with ``-stubs``. The ``py.typed``
marker file is not necessary for stub-only packages. This approach can be useful
to develop type stubs independently from your library.

For example:

.. code-block:: text

   setup.py
   my_great_package-stubs/
      __init__.pyi
      stuff.pyi


.. code-block:: python

   from setuptools import setup

   setup(
      name="my_great_package-stubs",
      version="0.1",
      package_data={"my_great_package-stubs": ["__init__.pyi", "stuff.pyi"]},
      packages=["my_great_package-stubs"]
   )


Users are then able to install the stubs-only package separately to provide
types for the original library.

Inclusion in sdist
^^^^^^^^^^^^^^^^^^

Note that to ensure inclusion of ``.pyi`` and ``py.typed`` files in an sdist
(.tar.gz archive), you may also need to modify the inclusion rules in your
``MANIFEST.in`` (see the
`packaging guide <https://packaging.python.org/en/latest/guides/using-manifest-in/>`__
for more details on ``MANIFEST.in``). For example:

.. code-block:: text

   global-include *.pyi
   global-include py.typed

.. _type_completeness:

How much of my library needs types?
===================================

A "py.typed" library should aim to be type complete so that type
checking and inspection can work to their full extent. Here we say that a
library is “type complete” if all of the symbols
that comprise its interface have type annotations that refer to types
that are fully known. Private symbols are exempt.

Library interface (public and private symbols)
----------------------------------------------

If a ``py.typed`` module is present, a type checker will treat all modules
within that package (i.e. all files that end in ``.py`` or ``.pyi``) as
importable unless the file name begins with an underscore. These modules
comprise the supported interface for the library.

Each module exposes a set of symbols. Some of these symbols are
considered "private” — implementation details that are not part of the
library’s interface. Type checkers can use the following rules
to determine which symbols are visible outside of the package.

-  Symbols whose names begin with an underscore (but are not dunder
   names) are considered private.
-  Imported symbols are considered private by default. If they use the
   ``import A as A`` (a redundant module alias), ``from X import A as A`` (a
   redundant symbol alias), or ``from . import A`` forms, symbol ``A`` is
   not private unless the name begins with an underscore. If a file
   ``__init__.py`` uses form ``from .A import X``, symbol ``A`` is treated
   likewise. If a wildcard import (of the form ``from X import *``) is
   used, all symbols referenced by the wildcard are not private.
-  A module can expose an ``__all__`` symbol at the module level that
   provides a list of names that are considered part of the interface.
   This overrides all other rules above, allowing imported symbols or
   symbols whose names begin with an underscore to be included in the
   interface.
-  Local variables within a function (including nested functions) are
   always considered private.

The following idioms are supported for defining the values contained
within ``__all__``. These restrictions allow type checkers to statically
determine the value of ``__all__``.

-  ``__all__ = ('a', b')``
-  ``__all__ = ['a', b']``
-  ``__all__ += ['a', b']``
-  ``__all__ += submodule.__all__``
-  ``__all__.extend(['a', b'])``
-  ``__all__.extend(submodule.__all__)``
-  ``__all__.append('a')``
-  ``__all__.remove('a')``

Type Completeness
-----------------

The following are best practice recommendations for how to define “type complete”:

Classes:

-  All class variables, instance variables, and methods that are
   “visible” (not overridden) are annotated and refer to known types
-  If a class is a subclass of a generic class, type arguments are
   provided for each generic type parameter, and these type arguments
   are known types

Functions and Methods:

-  All input parameters have type annotations that refer to known types
-  The return parameter is annotated and refers to a known type
-  The result of applying one or more decorators results in a known type

Type Aliases:

-  All of the types referenced by the type alias are known

Variables:

-  All variables have type annotations that refer to known types

Type annotations can be omitted in a few specific cases where the type
is obvious from the context:

-  Constants that are assigned simple literal values
   (e.g. ``RED = '#F00'`` or ``MAX_TIMEOUT = 50`` or
   ``room_temperature: Final = 20``). A constant is a symbol that is
   assigned only once and is either annotated with ``Final`` or is named
   in all-caps. A constant that is not assigned a simple literal value
   requires explicit annotations, preferably with a ``Final`` annotation
   (e.g. ``WOODWINDS: Final[List[str]] = ['Oboe', 'Bassoon']``).
-  Enum values within an Enum class do not require annotations because
   they take on the type of the Enum class.
-  Type aliases do not require annotations. A type alias is a symbol
   that is defined at a module level with a single assignment where the
   assigned value is an instantiable type, as opposed to a class
   instance
   (e.g. ``Foo = Callable[[Literal["a", "b"]], Union[int, str]]`` or
   ``Bar = Optional[MyGenericClass[int]]``).
-  The “self” parameter in an instance method and the “cls” parameter in
   a class method do not require an explicit annotation.
-  The return type for an ``__init__`` method does not need to be
   specified, since it is always ``None``.
-  The following module-level symbols do not require type annotations:
   ``__all__``,\ ``__author__``, ``__copyright__``, ``__email__``,
   ``__license__``, ``__title__``, ``__uri__``, ``__version__``.
-  The following class-level symbols do not require type annotations:
   ``__class__``, ``__dict__``, ``__doc__``, ``__module__``,
   ``__slots__``.

Examples of known and unknown types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python


   # Variable with unknown type
   a = [3, 4, 5]

   # Variable with known type
   a: List[int] = [3, 4, 5]

   # Type alias with partially unknown type (because type
   # arguments are missing for list and dict)
   DictOrList = Union[list, dict]

   # Type alias with known type
   DictOrList = Union[List[Any], Dict[str, Any]]

   # Generic type alias with known type
   _T = TypeVar("_T")
   DictOrList = Union[List[_T], Dict[str, _T]]

   # Function with known type
   def func(a: Optional[int], b: Dict[str, float] = {}) -> None:
       pass

   # Function with partially unknown type (because type annotations
   # are missing for input parameters and return type)
   def func(a, b):
       pass

   # Function with partially unknown type (because of missing
   # type args on Dict)
   def func(a: int, b: Dict) -> None:
       pass

   # Function with partially unknown type (because return type
   # annotation is missing)
   def func(a: int, b: Dict[str, float]):
       pass

   # Decorator with partially unknown type (because type annotations
   # are missing for input parameters and return type)
   def my_decorator(func):
       return func

   # Function with partially unknown type (because type is obscured
   # by untyped decorator)
   @my_decorator
   def func(a: int) -> str:
       pass


   # Class with known type
   class MyClass:
       height: float = 2.0

       def __init__(self, name: str, age: int):
           self.age: int = age

       @property
       def name(self) -> str:
           ...

   # Class with partially unknown type
   class MyClass:
       # Missing type annotation for class variable
       height = 2.0

       # Missing input parameter annotations
       def __init__(self, name, age):
           # Missing type annotation for instance variable
           self.age = age

       # Missing return type annotation
       @property
       def name(self):
           ...

   # Class with partially unknown type
   class BaseClass:
       # Missing type annotation
       height = 2.0

       # Missing type annotation
       def get_stuff(self):
           ...

   # Class with known type (because it overrides all symbols
   # exposed by BaseClass that have incomplete types)
   class DerivedClass(BaseClass):
       height: float

       def get_stuff(self) -> str:
           ...

   # Class with partially unknown type because base class
   # (dict) is generic, and type arguments are not specified.
   class DictSubclass(dict):
       pass

..
   TODO: consider moving best practices to their own page?

Best Practices for Inlined Types
================================

Wide vs. Narrow Types
---------------------

In type theory, when comparing two types that are related to each other,
the “wider” type is the one that is more general, and the “narrower”
type is more specific. For example, ``Sequence[str]`` is a wider type
than ``List[str]`` because all ``List`` objects are also ``Sequence``
objects, but the converse is not true. A subclass is narrower than a
class it derives from. A union of types is wider than the individual
types that comprise the union.

In general, a function input parameter should be annotated with the
widest possible type supported by the implementation. For example, if
the implementation requires the caller to provide an iterable collection
of strings, the parameter should be annotated as ``Iterable[str]``, not
as ``List[str]``. The latter type is narrower than necessary, so if a
user attempts to pass a tuple of strings (which is supported by the
implementation), a type checker will complain about a type
incompatibility.

As a specific application of the “use the widest type possible” rule,
libraries should generally use immutable forms of container types
instead of mutable forms (unless the function needs to modify the
container). Use ``Sequence`` rather than ``List``, ``Mapping`` rather
than ``Dict``, etc. Immutable containers allow for more flexibility
because their type parameters are covariant rather than invariant. A
parameter that is typed as ``Sequence[Union[str, int]]`` can accept a
``List[int]``, ``Sequence[str]``, and a ``Sequence[int]``. But a
parameter typed as ``List[Union[str, int]]`` is much more restrictive
and accepts only a ``List[Union[str, int]]``.

Overloads
---------

If a function or method can return multiple different types and those
types can be determined based on the presence or types of certain
parameters, use the ``@overload`` mechanism defined in `PEP
484 <https://www.python.org/dev/peps/pep-0484/#id45>`__. When overloads
are used within a “.py” file, they must appear prior to the function
implementation, which should not have an ``@overload`` decorator.

Keyword-only Parameters
-----------------------

If a function or method is intended to take parameters that are
specified only by name, use the keyword-only separator (``*``).

.. code:: python

   def create_user(age: int, *, dob: Optional[date] = None):
       ...

.. _annotating-decorators:

Annotating Decorators
---------------------

Decorators modify the behavior of a class or a function. Providing
annotations for decorators is straightforward if the decorator retains
the original signature of the decorated function.

.. code:: python

   _F = TypeVar("_F", bound=Callable[..., Any])

   def simple_decorator(_func: _F) -> _F:
       """
        Simple decorators are invoked without parentheses like this:
          @simple_decorator
          def my_function(): ...
        """
      ...

   def complex_decorator(*, mode: str) -> Callable[[_F], _F]:
       """
        Complex decorators are invoked with arguments like this:
          @complex_decorator(mode="easy")
          def my_function(): ...
        """
      ...

Decorators that mutate the signature of the decorated function present
challenges for type annotations. The ``ParamSpec`` and ``Concatenate``
mechanisms described in :pep:`612` provide some help
here, but these are available only in Python 3.10 and newer. More
complex signature mutations may require type annotations that erase the
original signature, thus blinding type checkers and other tools that
provide signature assistance. As such, library authors are discouraged
from creating decorators that mutate function signatures in this manner.

.. _aliasing-decorators:

Aliasing Decorators
-------------------

When writing a library with a couple of decorator factories 
(i.e. functions returning decorators, like ``complex_decorator`` from 
:ref:`annotating-decorators` section) it may be tempting to create a shortcut 
for a decorator. 

Different type checkers handle ``TypeAlias`` involving ``Callable`` in a 
different manner, so the most portable and easy way to create a shortcut 
is to define a callable ``Protocol`` as described in `PEP 
544 <https://peps.python.org/pep-0544/#callback-protocols>`_.

There is already a ``Protocol`` called ``IdentityFunction`` defined in `_typeshed <https://github.com/python/typeshed/blob/master/stdlib/_typeshed/README.md>`_:

.. code:: python

   if TYPE_CHECKING:
       from _typeshed import IdentityFunction

   def decorator_factory(*, mode: str) -> "IdentityFunction":
      """
       Decorator factory is invoked with arguments like this:
         @decorator_factory(mode="easy")
         def my_function(): ...
      """
        ...

For non-trivial decorators with custom logic, it is still possible 
to define a custom protocol using ``ParamSpec`` and ``Concatenate``
mechanisms described in `PEP 612 
<https://www.python.org/dev/peps/pep-0612/>`__:

.. code:: python

   class Client: ...
   
   P = ParamSpec("P")
   R = TypeVar("R")
  
   class PClientInjector(Protocol):
       def __call__(self, _: Callable[Concatenate[Client, P], R], /) -> Callable[P, R]:
           ...

   def inject_client(service: str) -> PClientInjector:
      """
       Decorator factory is invoked with arguments like this:
         @inject_client("testing")
         def my_function(client: Client, value: int): ...
         
         my_function then takes only value
      """


Generic Classes and Functions
-----------------------------

Classes and functions that can operate in a generic manner on various
types should declare themselves as generic using the mechanisms
described in :pep:`484`.
This includes the use of ``TypeVar`` symbols. Typically, a ``TypeVar``
should be private to the file that declares it, and should therefore
begin with an underscore.

Type Aliases
------------

Type aliases are symbols that refer to other types. Generic type aliases
(those that refer to unspecialized generic classes) are supported by
most type checkers.

:pep:`613` provides a way
to explicitly designate a symbol as a type alias using the new TypeAlias
annotation.

.. code:: python

   # Simple type alias
   FamilyPet = Union[Cat, Dog, GoldFish]

   # Generic type alias
   ListOrTuple = Union[List[_T], Tuple[_T, ...]]

   # Recursive type alias
   TreeNode = Union[LeafNode, List["TreeNode"]]

   # Explicit type alias using PEP 613 syntax
   StrOrInt: TypeAlias = Union[str, int]

Abstract Classes and Methods
----------------------------

Classes that must be subclassed should derive from ``ABC``, and methods
or properties that must be overridden should be decorated with the
``@abstractmethod`` decorator. This allows type checkers to validate
that the required methods have been overridden and provide developers
with useful error messages when they are not. It is customary to
implement an abstract method by raising a ``NotImplementedError``
exception.

.. code:: python

   from abc import ABC, abstractmethod

   class Hashable(ABC):
      @property
      @abstractmethod
      def hash_value(self) -> int:
         """Subclasses must override"""
         raise NotImplementedError()

      @abstractmethod
      def print(self) -> str:
         """Subclasses must override"""
         raise NotImplementedError()

Final Classes and Methods
-------------------------

Classes that are not intended to be subclassed should be decorated as
``@final`` as described in :pep:`591`. The same decorator
can also be used to specify methods that cannot be overridden by
subclasses.

Literals
--------

Type annotations should make use of the Literal type where appropriate,
as described in :pep:`586`.
Literals allow for more type specificity than their non-literal
counterparts.

Constants
---------

Constant values (those that are read-only) can be specified using the
Final annotation as described in :pep:`591`.

Type checkers will also typically treat variables that are named using
all upper-case characters as constants.

In both cases, it is OK to omit the declared type of a constant if it is
assigned a literal str, int, float, bool or None value. In such cases,
the type inference rules are clear and unambiguous, and adding a literal
type annotation would be redundant.

.. code:: python

   # All-caps constant with inferred type
   COLOR_FORMAT_RGB = "rgb"

   # All-caps constant with explicit type
   COLOR_FORMAT_RGB: Literal["rgb"] = "rgb"
   LATEST_VERSION: Tuple[int, int] = (4, 5)

   # Final variable with inferred type
   ColorFormatRgb: Final = "rgb"

   # Final variable with explicit type
   ColorFormatRgb: Final[Literal["rgb"]] = "rgb"
   LATEST_VERSION: Final[Tuple[int, int]] = (4, 5)

Typed Dictionaries, Data Classes, and Named Tuples
--------------------------------------------------

If your library runs only on newer versions of Python, you are
encouraged to use some of the new type-friendly classes.

NamedTuple (described in :pep:`484`) is preferred over
namedtuple.

Data classes (described in :pep:`557`) are preferred over
untyped dictionaries.

TypedDict (described in :pep:`589`) is preferred over
untyped dictionaries.

Compatibility with Older Python Versions
========================================

Each new version of Python from 3.5 onward has introduced new typing
constructs. This presents a challenge for library authors who want to
maintain runtime compatibility with older versions of Python. This
section documents several techniques that can be used to add types while
maintaining backward compatibility.

Quoted Annotations
------------------

Type annotations for variables, parameters, and return types can be
placed in quotes. The Python interpreter will then ignore them, whereas
a type checker will interpret them as type annotations.

.. code:: python

   # Older versions of Python do not support subscripting
   # for the OrderedDict type, so the annotation must be
   # enclosed in quotes.
   def get_config(self) -> "OrderedDict[str, str]":
      return self._config

Type Comment Annotations
------------------------

Python 3.0 introduced syntax for parameter and return type annotations,
as specified in :pep:`484`.
Python 3.6 introduced support for variable type annotations, as
specified in :pep:`526`.

If you need to support older versions of Python, type annotations can
still be provided as “type comments”. These comments take the form
``# type:``.

.. code:: python

   class Foo:
      # Variable type comments go at the end of the line
      # where the variable is assigned.
      timeout = None # type: Optional[int]

      # Function type comments can be specified on the
      # line after the function signature.
      def send_message(self, name, length):
         # type: (str, int) -> None
         ...

      # Function type comments can also specify the type
      # of each parameter on its own line.
      def receive_message(
         self,
         name, # type: str
         length # type: int
      ):
         # type: () -> Message
         ...

typing_extensions
-----------------

New type features that require runtime support are typically included in
the stdlib ``typing`` module. Where possible, these new features are
back-ported to a runtime library called ``typing_extensions`` that works
with older Python runtimes.

TYPE_CHECKING
-------------

The ``typing`` module exposes a variable called ``TYPE_CHECKING`` which
has a value of False within the Python runtime but a value of True when
the type checker is performing its analysis. This allows type checking
statements to be conditionalized.

Care should be taken when using ``TYPE_CHECKING`` because behavioral
changes between type checking and runtime could mask problems that the
type checker would otherwise catch.

Non-Standard Type Behaviors
===========================

Type annotations provide a way to annotate typical type behaviors, but
some classes implement specialized, non-standard behaviors that cannot
be described using standard type annotations. For now, such types need
to be annotated as Any, which is unfortunate because the benefits of
static typing are lost.

Docstrings
==========

Docstrings should be provided for all classes, functions, and methods in
the interface. They should be formatted according to :pep:`257`.

There is currently no single agreed-upon standard for function and
method docstrings, but several common variants have emerged. We
recommend using one of these variants.
