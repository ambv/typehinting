import abc
import sys
import typing
from typing import (
    ClassVar, Type, Generic, Callable, GenericMeta, TypingMeta,
    Counter, DefaultDict, Deque, TypeVar, Tuple, Final, final,
    NewType, overload, Text, TYPE_CHECKING, Literal,
    # We use internal typing helpers here, but this significantly reduces
    # code duplication. (Also this is only until Protocol is in typing.)
    _generic_new, _type_vars, _next_in_mro, _tp_cache, _type_check,
    _TypingEllipsis, _TypingEmpty, _check_generic
)

# Please keep __all__ alphabetized within each category.
__all__ = [
    # Super-special typing primitives.
    'ClassVar',
    'Final',
    'Protocol',
    'Type',
    'TypedDict',

    # Concrete collection types.
    'ContextManager',
    'Counter',
    'Deque',
    'DefaultDict',

    # One-off things.
    'final',
    'IntVar',
    'Literal',
    'NewType',
    'overload',
    'runtime',
    'Text',
    'TYPE_CHECKING',
]


if hasattr(typing, 'NoReturn'):
    NoReturn = typing.NoReturn
else:
    # TODO: Remove once typing.py has been updated
    class _NoReturnMeta(typing.TypingMeta):
        """Metaclass for NoReturn."""

        def __new__(cls, name, bases, namespace):
            cls.assert_no_subclassing(bases)
            self = super(_NoReturnMeta, cls).__new__(cls, name, bases, namespace)
            return self

    class _NoReturn(typing._FinalTypingBase):
        """Special type indicating functions that never return.
        Example::
          from typing import NoReturn
          def stop() -> NoReturn:
              raise Exception('no way')
        This type is invalid in other positions, e.g., ``List[NoReturn]``
        will fail in static type checkers.
        """
        __metaclass__ = _NoReturnMeta
        __slots__ = ()

        def __instancecheck__(self, obj):
            raise TypeError("NoReturn cannot be used with isinstance().")

        def __subclasscheck__(self, cls):
            raise TypeError("NoReturn cannot be used with issubclass().")

    NoReturn = _NoReturn(_root=True)


T_co = typing.TypeVar('T_co', covariant=True)

if hasattr(typing, 'ContextManager'):
    ContextManager = typing.ContextManager
else:
    # TODO: Remove once typing.py has been updated
    class ContextManager(typing.Generic[T_co]):
        __slots__ = ()

        def __enter__(self):
            return self

        @abc.abstractmethod
        def __exit__(self, exc_type, exc_value, traceback):
            return None

        @classmethod
        def __subclasshook__(cls, C):
            if cls is ContextManager:
                # In Python 3.6+, it is possible to set a method to None to
                # explicitly indicate that the class does not implement an ABC
                # (https://bugs.python.org/issue25958), but we do not support
                # that pattern here because this fallback class is only used
                # in Python 3.5 and earlier.
                if (any("__enter__" in B.__dict__ for B in C.__mro__) and
                    any("__exit__" in B.__dict__ for B in C.__mro__)):
                    return True
            return NotImplemented


def _gorg(cls):
    """This function exists for compatibility with old typing versions."""
    assert isinstance(cls, GenericMeta)
    if hasattr(cls, '_gorg'):
        return cls._gorg
    while cls.__origin__ is not None:
        cls = cls.__origin__
    return cls


def IntVar(name):
    return TypeVar(name)


class _ProtocolMeta(GenericMeta):
    """Internal metaclass for Protocol.

    This exists so Protocol classes can be generic without deriving
    from Generic.
    """

    def __new__(cls, name, bases, namespace,
                tvars=None, args=None, origin=None, extra=None, orig_bases=None):
        # This is just a version copied from GenericMeta.__new__ that
        # includes "Protocol" special treatment. (Comments removed for brevity.)
        assert extra is None  # Protocols should not have extra
        if tvars is not None:
            assert origin is not None
            assert all(isinstance(t, TypeVar) for t in tvars), tvars
        else:
            tvars = _type_vars(bases)
            gvars = None
            for base in bases:
                if base is Generic:
                    raise TypeError("Cannot inherit from plain Generic")
                if (isinstance(base, GenericMeta) and
                        base.__origin__ in (Generic, Protocol)):
                    if gvars is not None:
                        raise TypeError(
                            "Cannot inherit from Generic[...] or"
                            " Protocol[...] multiple times.")
                    gvars = base.__parameters__
            if gvars is None:
                gvars = tvars
            else:
                tvarset = set(tvars)
                gvarset = set(gvars)
                if not tvarset <= gvarset:
                    raise TypeError(
                        "Some type variables (%s) "
                        "are not listed in %s[%s]" %
                        (", ".join(str(t) for t in tvars if t not in gvarset),
                         "Generic" if any(b.__origin__ is Generic
                                          for b in bases) else "Protocol",
                         ", ".join(str(g) for g in gvars)))
                tvars = gvars

        initial_bases = bases
        if extra is None:
            extra = namespace.get('__extra__')
        if extra is not None and type(extra) is abc.ABCMeta and extra not in bases:
            bases = (extra,) + bases
        bases = tuple(_gorg(b) if isinstance(b, GenericMeta) else b for b in bases)

        if any(isinstance(b, GenericMeta) and b is not Generic for b in bases):
            bases = tuple(b for b in bases if b is not Generic)
        namespace.update({'__origin__': origin, '__extra__': extra})
        self = abc.ABCMeta.__new__(cls, name, bases, namespace)
        abc.ABCMeta.__setattr__(self, '_gorg', self if not origin else _gorg(origin))

        self.__parameters__ = tvars
        self.__args__ = tuple(Ellipsis if a is _TypingEllipsis else
                              () if a is _TypingEmpty else
                              a for a in args) if args else None
        self.__next_in_mro__ = _next_in_mro(self)
        if orig_bases is None:
            self.__orig_bases__ = initial_bases
        self.__tree_hash__ = (hash(self._subs_tree()) if origin else
                              abc.ABCMeta.__hash__(self))
        return self

    def __init__(cls, *args, **kwargs):
        super(_ProtocolMeta, cls).__init__(*args, **kwargs)
        if not cls.__dict__.get('_is_protocol', None):
            cls._is_protocol = any(b is Protocol or
                                   isinstance(b, _ProtocolMeta) and
                                   b.__origin__ is Protocol
                                   for b in cls.__bases__)
        if cls._is_protocol:
            for base in cls.__mro__[1:]:
                if not (base in (object, Generic, Callable) or
                        isinstance(base, TypingMeta) and base._is_protocol or
                        isinstance(base, GenericMeta) and base.__origin__ is Generic):
                    raise TypeError('Protocols can only inherit from other protocols,'
                                    ' got %r' % base)
            cls._callable_members_only = all(callable(getattr(cls, attr))
                                             for attr in cls._get_protocol_attrs())

            def _no_init(self, *args, **kwargs):
                if type(self)._is_protocol:
                    raise TypeError('Protocols cannot be instantiated')
            cls.__init__ = _no_init

        def _proto_hook(cls, other):
            if not cls.__dict__.get('_is_protocol', None):
                return NotImplemented
            if not isinstance(other, type):
                # Similar error as for issubclass(1, int)
                # (also not a chance for old-style classes)
                raise TypeError('issubclass() arg 1 must be a new-style class')
            for attr in cls._get_protocol_attrs():
                for base in other.__mro__:
                    if attr in base.__dict__:
                        if base.__dict__[attr] is None:
                            return NotImplemented
                        break
                else:
                    return NotImplemented
            return True
        if '__subclasshook__' not in cls.__dict__:
            cls.__subclasshook__ = classmethod(_proto_hook)

    def __instancecheck__(self, instance):
        # We need this method for situations where attributes are assigned in __init__
        if isinstance(instance, type):
            # This looks like a fundamental limitation of Python 2.
            # It cannot support runtime protocol metaclasses, On Python 2 classes
            # cannot be correctly inspected as instances of protocols.
            return False
        if ((not getattr(self, '_is_protocol', False) or
                self._callable_members_only) and
                issubclass(instance.__class__, self)):
            return True
        if self._is_protocol:
            if all(hasattr(instance, attr) and
                    (not callable(getattr(self, attr)) or
                     getattr(instance, attr) is not None)
                    for attr in self._get_protocol_attrs()):
                return True
        return super(GenericMeta, self).__instancecheck__(instance)

    def __subclasscheck__(self, cls):
        if (self.__dict__.get('_is_protocol', None) and
                not self.__dict__.get('_is_runtime_protocol', None)):
            if sys._getframe(1).f_globals['__name__'] in ['abc', 'functools', 'typing']:
                return False
            raise TypeError("Instance and class checks can only be used with"
                            " @runtime protocols")
        if (self.__dict__.get('_is_runtime_protocol', None) and
                not self._callable_members_only):
            if sys._getframe(1).f_globals['__name__'] in ['abc', 'functools', 'typing']:
                return super(GenericMeta, self).__subclasscheck__(cls)
            raise TypeError("Protocols with non-method members"
                            " don't support issubclass()")
        return super(_ProtocolMeta, self).__subclasscheck__(cls)

    def _get_protocol_attrs(self):
        attrs = set()
        for base in self.__mro__[:-1]:  # without object
            if base.__name__ in ('Protocol', 'Generic'):
                continue
            annotations = getattr(base, '__annotations__', {})
            for attr in list(base.__dict__.keys()) + list(annotations.keys()):
                if (not attr.startswith('_abc_') and attr not in (
                        '__abstractmethods__', '__annotations__', '__weakref__',
                        '_is_protocol', '_is_runtime_protocol', '__dict__',
                        '__args__', '__slots__', '_get_protocol_attrs',
                        '__next_in_mro__', '__parameters__', '__origin__',
                        '__orig_bases__', '__extra__', '__tree_hash__',
                        '__doc__', '__subclasshook__', '__init__', '__new__',
                        '__module__', '_MutableMapping__marker',
                        '__metaclass__', '_gorg', '_callable_members_only')):
                    attrs.add(attr)
        return attrs

    @_tp_cache
    def __getitem__(self, params):
        # We also need to copy this from GenericMeta.__getitem__ to get
        # special treatment of "Protocol". (Comments removed for brevity.)
        if not isinstance(params, tuple):
            params = (params,)
        if not params and _gorg(self) is not Tuple:
            raise TypeError(
                "Parameter list to %s[...] cannot be empty" % self.__qualname__)
        msg = "Parameters to generic types must be types."
        params = tuple(_type_check(p, msg) for p in params)
        if self in (Generic, Protocol):
            if not all(isinstance(p, TypeVar) for p in params):
                raise TypeError(
                    "Parameters to %r[...] must all be type variables", self)
            if len(set(params)) != len(params):
                raise TypeError(
                    "Parameters to %r[...] must all be unique", self)
            tvars = params
            args = params
        elif self in (Tuple, Callable):
            tvars = _type_vars(params)
            args = params
        elif self.__origin__ in (Generic, Protocol):
            raise TypeError("Cannot subscript already-subscripted %s" %
                            repr(self))
        else:
            _check_generic(self, params)
            tvars = _type_vars(params)
            args = params

        prepend = (self,) if self.__origin__ is None else ()
        return self.__class__(self.__name__,
                              prepend + self.__bases__,
                              dict(self.__dict__),
                              tvars=tvars,
                              args=args,
                              origin=self,
                              extra=self.__extra__,
                              orig_bases=self.__orig_bases__)


class Protocol(object):
    """Base class for protocol classes. Protocol classes are defined as::

      class Proto(Protocol):
          def meth(self):
              # type: () -> int
              pass

    Such classes are primarily used with static type checkers that recognize
    structural subtyping (static duck-typing), for example::

      class C:
          def meth(self):
              # type: () -> int
              return 0

      def func(x):
          # type: (Proto) -> int
          return x.meth()

      func(C())  # Passes static type check

    See PEP 544 for details. Protocol classes decorated with @typing_extensions.runtime
    act as simple-minded runtime protocols that checks only the presence of
    given attributes, ignoring their type signatures.

    Protocol classes can be generic, they are defined as::

      class GenProto(Protocol[T]):
          def meth(self):
              # type: () -> T
              pass
    """

    __metaclass__ = _ProtocolMeta
    __slots__ = ()
    _is_protocol = True

    def __new__(cls, *args, **kwds):
        if _gorg(cls) is Protocol:
            raise TypeError("Type Protocol cannot be instantiated; "
                            "it can be used only as a base class")
        return _generic_new(cls.__next_in_mro__, cls, *args, **kwds)


def runtime(cls):
    """Mark a protocol class as a runtime protocol, so that it
    can be used with isinstance() and issubclass(). Raise TypeError
    if applied to a non-protocol class.

    This allows a simple-minded structural check very similar to the
    one-offs in collections.abc such as Hashable.
    """
    if not isinstance(cls, _ProtocolMeta) or not cls._is_protocol:
        raise TypeError('@runtime can be only applied to protocol classes,'
                        ' got %r' % cls)
    cls._is_runtime_protocol = True
    return cls


def _check_fails(cls, other):
    try:
        if sys._getframe(1).f_globals['__name__'] not in ['abc', 'functools', 'typing']:
            # Typed dicts are only for static structural subtyping.
            raise TypeError('TypedDict does not support instance and class checks')
    except (AttributeError, ValueError):
        pass
    return False


def _dict_new(cls, *args, **kwargs):
    return dict(*args, **kwargs)


def _typeddict_new(cls, _typename, _fields=None, **kwargs):
    total = kwargs.pop('total', True)
    if _fields is None:
        _fields = kwargs
    elif kwargs:
        raise TypeError("TypedDict takes either a dict or keyword arguments,"
                        " but not both")

    ns = {'__annotations__': dict(_fields), '__total__': total}
    try:
        # Setting correct module is necessary to make typed dict classes pickleable.
        ns['__module__'] = sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return _TypedDictMeta(_typename, (), ns)


class _TypedDictMeta(type):
    def __new__(cls, name, bases, ns, total=True):
        # Create new typed dict class object.
        # This method is called directly when TypedDict is subclassed,
        # or via _typeddict_new when TypedDict is instantiated. This way
        # TypedDict supports all three syntaxes described in its docstring.
        # Subclasses and instances of TypedDict return actual dictionaries
        # via _dict_new.
        ns['__new__'] = _typeddict_new if name == 'TypedDict' else _dict_new
        tp_dict = super(_TypedDictMeta, cls).__new__(cls, name, (dict,), ns)

        anns = ns.get('__annotations__', {})
        msg = "TypedDict('Name', {f0: t0, f1: t1, ...}); each t must be a type"
        anns = {n: _type_check(tp, msg) for n, tp in anns.items()}
        for base in bases:
            anns.update(base.__dict__.get('__annotations__', {}))
        tp_dict.__annotations__ = anns
        if not hasattr(tp_dict, '__total__'):
            tp_dict.__total__ = total
        return tp_dict

    __instancecheck__ = __subclasscheck__ = _check_fails


TypedDict = _TypedDictMeta('TypedDict', (dict,), {})
TypedDict.__module__ = __name__
TypedDict.__doc__ = \
    """A simple typed name space. At runtime it is equivalent to a plain dict.

    TypedDict creates a dictionary type that expects all of its
    instances to have a certain set of keys, with each key
    associated with a value of a consistent type. This expectation
    is not checked at runtime but is only enforced by type checkers.
    Usage::

        Point2D = TypedDict('Point2D', {'x': int, 'y': int, 'label': str})

        a: Point2D = {'x': 1, 'y': 2, 'label': 'good'}  # OK
        b: Point2D = {'z': 3, 'label': 'bad'}           # Fails type check

        assert Point2D(x=1, y=2, label='first') == dict(x=1, y=2, label='first')

    The type info could be accessed via Point2D.__annotations__. TypedDict
    supports an additional equivalent form::

        Point2D = TypedDict('Point2D', x=int, y=int, label=str)
    """

def _is_dunder(name):
    """Returns True if name is a __dunder_variable_name__."""
    return len(name) > 4 and name.startswith('__') and name.endswith('__')

class AnnotatedMeta(GenericMeta):
    """Metaclass for Annotated"""

    def __new__(cls, name, bases, namespace, **kwargs):
        if any(b is not object for b in bases):
            raise TypeError("Cannot subclass %s" % Annotated)
        return super(AnnotatedMeta, cls).__new__(cls, name, bases, namespace, **kwargs)

    @property
    def __metadata__(self):
        return self._subs_tree()[2]

    def _tree_repr(self, tree):
        cls, origin, metadata = tree
        if not isinstance(origin, tuple):
            tp_repr = typing._type_repr(origin)
        else:
            tp_repr = origin[0]._tree_repr(origin)
        metadata_reprs = ", ".join(repr(arg) for arg in metadata)
        return '%s[%s, %s]' % (cls, tp_repr, metadata_reprs)

    def _subs_tree(self, tvars=None, args=None):
        if self is Annotated:
            return Annotated
        res = super(AnnotatedMeta, self)._subs_tree(tvars=tvars, args=args)
        # Flatten nested Annotated
        if isinstance(res[1], tuple) and res[1][0] is Annotated:
            sub_tp = res[1][1]
            sub_annot = res[1][2]
            return (Annotated, sub_tp, sub_annot + res[2])
        return res

    def _get_cons(self):
        """Return the class used to create instance of this type."""
        if self.__origin__ is None:
            raise TypeError("Cannot get the underlying type of a non-specialized "
                            "Annotated type.")
        tree = self._subs_tree()
        while isinstance(tree, tuple) and tree[0] is Annotated:
            tree = tree[1]
        if isinstance(tree, tuple):
            return tree[0]
        else:
            return tree

    @_tp_cache
    def __getitem__(self, params):
        if not isinstance(params, tuple):
            params = (params,)
        if self.__origin__ is not None:  # specializing an instantiated type
            return super(AnnotatedMeta, self).__getitem__(params)
        elif not isinstance(params, tuple) or len(params) < 2:
            raise TypeError("Annotated[...] should be instantiated with at "
                            "least two arguments (a type and an annotation).")
        else:
            msg = "Annotated[t, ...]: t must be a type."
            tp = typing._type_check(params[0], msg)
            metadata = tuple(params[1:])
        return self.__class__(
            self.__name__,
            self.__bases__,
            dict(self.__dict__),
            tvars=_type_vars((tp,)),
            # Metadata is a tuple so it won't be touched by _replace_args et al.
            args=(tp, metadata),
            origin=self,
        )

    def __call__(self, *args, **kwargs):
        cons = self._get_cons()
        result = cons(*args, **kwargs)
        try:
            result.__orig_class__ = self
        except AttributeError:
            pass
        return result

    def __getattr__(self, attr):
        # For simplicity we just don't relay all dunder names
        if self.__origin__ is not None and not _is_dunder(attr):
            return getattr(self._get_cons(), attr)
        raise AttributeError(attr)

    def __setattr__(self, attr, value):
        if _is_dunder(attr) or attr.startswith('_abc_'):
            super(AnnotatedMeta, self).__setattr__(attr, value)
        elif self.__origin__ is None:
            raise AttributeError(attr)
        else:
            setattr(self._get_cons(), attr, value)


class Annotated(object):
    """Add context specific metadata to a type.

    Example: Annotated[int, runtime_check.Unsigned] indicates to the
    hypothetical runtime_check module that this type is an unsigned int.
    Every other consumer of this type can ignore this metadata and treat
    this type as int.

    The first argument to Annotated must be a valid type, the remaining
    arguments are kept as a tuple in the __metadata__ field.

    Details:

    - It's an error to call `Annotated` with less than two arguments.
    - Nested Annotated are flattened::

        Annotated[Annotated[int, Ann1, Ann2], Ann3] == Annotated[int, Ann1, Ann2, Ann3]

    - Instantiating an annotated type is equivalent to instantiating the
    underlying type::

        Annotated[C, Ann1](5) == C(5)

    - Annotated can be used as a generic type alias::

        Optimized = Annotated[T, runtime.Optimize()]
        Optimized[int] == Annotated[int, runtime.Optimize()]

        OptimizedList = Annotated[List[T], runtime.Optimize()]
        OptimizedList[int] == Annotated[List[int], runtime.Optimize()]
    """
    __metaclass__ = AnnotatedMeta
    __slots__ = ()
