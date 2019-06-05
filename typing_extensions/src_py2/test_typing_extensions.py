import sys
import os
import abc
import contextlib
import collections
import pickle
import subprocess
import types
from unittest import TestCase, main, skipUnless

from typing_extensions import Annotated, NoReturn, ClassVar, Final, IntVar, Literal, TypedDict
from typing_extensions import ContextManager, Counter, Deque, DefaultDict
from typing_extensions import NewType, overload, Protocol, runtime
from typing import Dict, List
import typing
import typing_extensions


T = typing.TypeVar('T')
KT = typing.TypeVar('KT')
VT = typing.TypeVar('VT')


class BaseTestCase(TestCase):

    def assertIsSubclass(self, cls, class_or_tuple, msg=None):
        if not issubclass(cls, class_or_tuple):
            message = '%r is not a subclass of %r' % (cls, class_or_tuple)
            if msg is not None:
                message += ' : %s' % msg
            raise self.failureException(message)

    def assertNotIsSubclass(self, cls, class_or_tuple, msg=None):
        if issubclass(cls, class_or_tuple):
            message = '%r is a subclass of %r' % (cls, class_or_tuple)
            if msg is not None:
                message += ' : %s' % msg
            raise self.failureException(message)


class Employee(object):
    pass


class NoReturnTests(BaseTestCase):

    def test_noreturn_instance_type_error(self):
        with self.assertRaises(TypeError):
            isinstance(42, NoReturn)

    def test_noreturn_subclass_type_error(self):
        with self.assertRaises(TypeError):
            issubclass(Employee, NoReturn)
        with self.assertRaises(TypeError):
            issubclass(NoReturn, Employee)

    def test_repr(self):
        if hasattr(typing, 'NoReturn'):
            self.assertEqual(repr(NoReturn), 'typing.NoReturn')
        else:
            self.assertEqual(repr(NoReturn), 'typing_extensions.NoReturn')

    def test_not_generic(self):
        with self.assertRaises(TypeError):
            NoReturn[int]

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError):
            class A(NoReturn):
                pass
        with self.assertRaises(TypeError):
            class A(type(NoReturn)):
                pass

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            NoReturn()
        with self.assertRaises(TypeError):
            type(NoReturn)()


class ClassVarTests(BaseTestCase):

    def test_basics(self):
        with self.assertRaises(TypeError):
            ClassVar[1]
        with self.assertRaises(TypeError):
            ClassVar[int, str]
        with self.assertRaises(TypeError):
            ClassVar[int][str]

    def test_repr(self):
        self.assertEqual(repr(ClassVar), 'typing.ClassVar')
        cv = ClassVar[int]
        self.assertEqual(repr(cv), 'typing.ClassVar[int]')
        cv = ClassVar[Employee]
        self.assertEqual(repr(cv), 'typing.ClassVar[%s.Employee]' % __name__)

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError):
            class C(type(ClassVar)):
                pass
        with self.assertRaises(TypeError):
            class C(type(ClassVar[int])):
                pass

    def test_cannot_init(self):
        with self.assertRaises(TypeError):
            ClassVar()
        with self.assertRaises(TypeError):
            type(ClassVar)()
        with self.assertRaises(TypeError):
            type(ClassVar[typing.Optional[int]])()

    def test_no_isinstance(self):
        with self.assertRaises(TypeError):
            isinstance(1, ClassVar[int])
        with self.assertRaises(TypeError):
            issubclass(int, ClassVar)


class FinalTests(BaseTestCase):

    def test_basics(self):
        with self.assertRaises(TypeError):
            Final[1]
        with self.assertRaises(TypeError):
            Final[int, str]
        with self.assertRaises(TypeError):
            Final[int][str]

    def test_repr(self):
        self.assertEqual(repr(Final), 'typing_extensions.Final')
        cv = Final[int]
        self.assertEqual(repr(cv), 'typing_extensions.Final[int]')
        cv = Final[Employee]
        self.assertEqual(repr(cv), 'typing_extensions.Final[%s.Employee]' % __name__)

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError):
            class C(type(Final)):
                pass
        with self.assertRaises(TypeError):
            class C(type(Final[int])):
                pass

    def test_cannot_init(self):
        with self.assertRaises(TypeError):
            Final()
        with self.assertRaises(TypeError):
            type(Final)()
        with self.assertRaises(TypeError):
            type(Final[typing.Optional[int]])()

    def test_no_isinstance(self):
        with self.assertRaises(TypeError):
            isinstance(1, Final[int])
        with self.assertRaises(TypeError):
            issubclass(int, Final)


class IntVarTests(BaseTestCase):
    def test_valid(self):
        T_ints = IntVar("T_ints")

    def test_invalid(self):
        with self.assertRaises(TypeError):
            T_ints = IntVar("T_ints", int)
        with self.assertRaises(TypeError):
            T_ints = IntVar("T_ints", bound=int)
        with self.assertRaises(TypeError):
            T_ints = IntVar("T_ints", covariant=True)


class LiteralTests(BaseTestCase):
    def test_basics(self):
        Literal[1]
        Literal[1, 2, 3]
        Literal["x", "y", "z"]
        Literal[None]

    def test_illegal_parameters_do_not_raise_runtime_errors(self):
        # Type checkers should reject these types, but we do not
        # raise errors at runtime to maintain maximium flexibility
        Literal[int]
        Literal[Literal[1, 2], Literal[4, 5]]
        Literal[3j + 2, ..., ()]
        Literal[b"foo", u"bar"]
        Literal[{"foo": 3, "bar": 4}]
        Literal[T]

    def test_literals_inside_other_types(self):
        typing.List[Literal[1, 2, 3]]
        typing.List[Literal[("foo", "bar", "baz")]]

    def test_repr(self):
        self.assertEqual(repr(Literal[1]), "typing_extensions.Literal[1]")
        self.assertEqual(repr(Literal[1, True, "foo"]), "typing_extensions.Literal[1, True, 'foo']")
        self.assertEqual(repr(Literal[int]), "typing_extensions.Literal[int]")
        self.assertEqual(repr(Literal), "typing_extensions.Literal")
        self.assertEqual(repr(Literal[None]), "typing_extensions.Literal[None]")

    def test_cannot_init(self):
        with self.assertRaises(TypeError):
            Literal()
        with self.assertRaises(TypeError):
            Literal[1]()
        with self.assertRaises(TypeError):
            type(Literal)()
        with self.assertRaises(TypeError):
            type(Literal[1])()

    def test_no_isinstance_or_issubclass(self):
        with self.assertRaises(TypeError):
            isinstance(1, Literal[1])
        with self.assertRaises(TypeError):
            isinstance(int, Literal[1])
        with self.assertRaises(TypeError):
            issubclass(1, Literal[1])
        with self.assertRaises(TypeError):
            issubclass(int, Literal[1])

    def test_no_subclassing(self):
        with self.assertRaises(TypeError):
            class Foo(Literal[1]): pass
        with self.assertRaises(TypeError):
            class Bar(Literal): pass

    def test_no_multiple_subscripts(self):
        with self.assertRaises(TypeError):
            Literal[1][1]


class CollectionsAbcTests(BaseTestCase):

    def test_isinstance_collections(self):
        self.assertNotIsInstance(1, collections.Mapping)
        self.assertNotIsInstance(1, collections.Iterable)
        self.assertNotIsInstance(1, collections.Container)
        self.assertNotIsInstance(1, collections.Sized)
        with self.assertRaises(TypeError):
            isinstance(collections.deque(), typing_extensions.Deque[int])
        with self.assertRaises(TypeError):
            issubclass(collections.Counter, typing_extensions.Counter[str])

    def test_contextmanager(self):
        @contextlib.contextmanager
        def manager():
            yield 42

        cm = manager()
        self.assertIsInstance(cm, ContextManager)
        self.assertNotIsInstance(42, ContextManager)

        with self.assertRaises(TypeError):
            isinstance(42, ContextManager[int])
        with self.assertRaises(TypeError):
            isinstance(cm, ContextManager[int])
        with self.assertRaises(TypeError):
            issubclass(type(cm), ContextManager[int])

    def test_counter(self):
        self.assertIsSubclass(collections.Counter, Counter)
        self.assertIs(type(Counter()), collections.Counter)
        self.assertIs(type(Counter[T]()), collections.Counter)
        self.assertIs(type(Counter[int]()), collections.Counter)

        class A(Counter[int]): pass
        class B(Counter[T]): pass

        self.assertIsInstance(A(), collections.Counter)
        self.assertIs(type(B[int]()), B)
        self.assertEqual(B.__bases__, (typing_extensions.Counter,))

    def test_deque(self):
        self.assertIsSubclass(collections.deque, Deque)
        self.assertIs(type(Deque()), collections.deque)
        self.assertIs(type(Deque[T]()), collections.deque)
        self.assertIs(type(Deque[int]()), collections.deque)

        class A(Deque[int]): pass
        class B(Deque[T]): pass

        self.assertIsInstance(A(), collections.deque)
        self.assertIs(type(B[int]()), B)

    def test_defaultdict_instantiation(self):
        self.assertIsSubclass(collections.defaultdict, DefaultDict)
        self.assertIs(type(DefaultDict()), collections.defaultdict)
        self.assertIs(type(DefaultDict[KT, VT]()), collections.defaultdict)
        self.assertIs(type(DefaultDict[str, int]()), collections.defaultdict)

        class A(DefaultDict[str, int]): pass
        class B(DefaultDict[KT, VT]): pass

        self.assertIsInstance(A(), collections.defaultdict)
        self.assertIs(type(B[str, int]()), B)


class NewTypeTests(BaseTestCase):

    def test_basic(self):
        UserId = NewType('UserId', int)
        UserName = NewType('UserName', str)
        self.assertIsInstance(UserId(5), int)
        self.assertIsInstance(UserName('Joe'), type('Joe'))
        self.assertEqual(UserId(5) + 1, 6)

    def test_errors(self):
        UserId = NewType('UserId', int)
        UserName = NewType('UserName', str)
        with self.assertRaises(TypeError):
            issubclass(UserId, int)
        with self.assertRaises(TypeError):
            class D(UserName):
                pass


class OverloadTests(BaseTestCase):

    def test_overload_fails(self):
        with self.assertRaises(RuntimeError):
            @overload
            def blah():
                pass

            blah()

    def test_overload_succeeds(self):
        @overload
        def blah():
            pass

        def blah():
            pass

        blah()


class ProtocolTests(BaseTestCase):

    def test_basic_protocol(self):
        @runtime
        class P(Protocol):
            def meth(self):
                pass
        class C(object): pass
        class D(object):
            def meth(self):
                pass
        def f():
            pass
        self.assertIsSubclass(D, P)
        self.assertIsInstance(D(), P)
        self.assertNotIsSubclass(C, P)
        self.assertNotIsInstance(C(), P)
        self.assertNotIsSubclass(types.FunctionType, P)
        self.assertNotIsInstance(f, P)

    def test_everything_implements_empty_protocol(self):
        @runtime
        class Empty(Protocol): pass
        class C(object): pass
        def f():
            pass
        for thing in (object, type, tuple, C, types.FunctionType):
            self.assertIsSubclass(thing, Empty)
        for thing in (object(), 1, (), typing, f):
            self.assertIsInstance(thing, Empty)

    def test_function_implements_protocol(self):
        @runtime
        class Function(Protocol):
            def __call__(self, *args, **kwargs):
                pass
        def f():
            pass
        self.assertIsInstance(f, Function)

    def test_no_inheritance_from_nominal(self):
        class C(object): pass
        class BP(Protocol): pass
        with self.assertRaises(TypeError):
            class P(C, Protocol):
                pass
        with self.assertRaises(TypeError):
            class P(Protocol, C):
                pass
        with self.assertRaises(TypeError):
            class P(BP, C, Protocol):
                pass
        class D(BP, C): pass
        class E(C, BP): pass
        self.assertNotIsInstance(D(), E)
        self.assertNotIsInstance(E(), D)

    def test_no_instantiation(self):
        class P(Protocol): pass
        with self.assertRaises(TypeError):
            P()
        class C(P): pass
        self.assertIsInstance(C(), C)
        T = typing.TypeVar('T')
        class PG(Protocol[T]): pass
        with self.assertRaises(TypeError):
            PG()
        with self.assertRaises(TypeError):
            PG[int]()
        with self.assertRaises(TypeError):
            PG[T]()
        class CG(PG[T]): pass
        self.assertIsInstance(CG[int](), CG)

    def test_cannot_instantiate_abstract(self):
        @runtime
        class P(Protocol):
            @abc.abstractmethod
            def ameth(self):
                raise NotImplementedError
        class B(P):
            pass
        class C(B):
            def ameth(self):
                return 26
        with self.assertRaises(TypeError):
            B()
        self.assertIsInstance(C(), P)

    def test_subprotocols_extending(self):
        class P1(Protocol):
            def meth1(self):
                pass
        @runtime
        class P2(P1, Protocol):
            def meth2(self):
                pass
        class C(object):
            def meth1(self):
                pass
            def meth2(self):
                pass
        class C1(object):
            def meth1(self):
                pass
        class C2(object):
            def meth2(self):
                pass
        self.assertNotIsInstance(C1(), P2)
        self.assertNotIsInstance(C2(), P2)
        self.assertNotIsSubclass(C1, P2)
        self.assertNotIsSubclass(C2, P2)
        self.assertIsInstance(C(), P2)
        self.assertIsSubclass(C, P2)

    def test_subprotocols_merging(self):
        class P1(Protocol):
            def meth1(self):
                pass
        class P2(Protocol):
            def meth2(self):
                pass
        @runtime
        class P(P1, P2, Protocol):
            pass
        class C(object):
            def meth1(self):
                pass
            def meth2(self):
                pass
        class C1(object):
            def meth1(self):
                pass
        class C2(object):
            def meth2(self):
                pass
        self.assertNotIsInstance(C1(), P)
        self.assertNotIsInstance(C2(), P)
        self.assertNotIsSubclass(C1, P)
        self.assertNotIsSubclass(C2, P)
        self.assertIsInstance(C(), P)
        self.assertIsSubclass(C, P)

    def test_protocols_issubclass(self):
        T = typing.TypeVar('T')
        @runtime
        class P(Protocol):
            def x(self): pass
        @runtime
        class PG(Protocol[T]):
            def x(self): pass
        class BadP(Protocol):
            def x(self): pass
        class BadPG(Protocol[T]):
            def x(self): pass
        class C(object):
            def x(self): pass
        self.assertIsSubclass(C, P)
        self.assertIsSubclass(C, PG)
        self.assertIsSubclass(BadP, PG)
        self.assertIsSubclass(PG[int], PG)
        self.assertIsSubclass(BadPG[int], P)
        self.assertIsSubclass(BadPG[T], PG)
        with self.assertRaises(TypeError):
            issubclass(C, PG[T])
        with self.assertRaises(TypeError):
            issubclass(C, PG[C])
        with self.assertRaises(TypeError):
            issubclass(C, BadP)
        with self.assertRaises(TypeError):
            issubclass(C, BadPG)
        with self.assertRaises(TypeError):
            issubclass(P, PG[T])
        with self.assertRaises(TypeError):
            issubclass(PG, PG[int])

    def test_protocols_issubclass_non_callable(self):
        class C(object):
            x = 1
        @runtime
        class PNonCall(Protocol):
            x = 1
        with self.assertRaises(TypeError):
            issubclass(C, PNonCall)
        self.assertIsInstance(C(), PNonCall)
        PNonCall.register(C)
        with self.assertRaises(TypeError):
            issubclass(C, PNonCall)
        self.assertIsInstance(C(), PNonCall)
        # check that non-protocol subclasses are not affected
        class D(PNonCall): pass
        self.assertNotIsSubclass(C, D)
        self.assertNotIsInstance(C(), D)
        D.register(C)
        self.assertIsSubclass(C, D)
        self.assertIsInstance(C(), D)
        with self.assertRaises(TypeError):
            issubclass(D, PNonCall)

    def test_protocols_isinstance(self):
        T = typing.TypeVar('T')
        @runtime
        class P(Protocol):
            def meth(x): pass
        @runtime
        class PG(Protocol[T]):
            def meth(x): pass
        class BadP(Protocol):
            def meth(x): pass
        class BadPG(Protocol[T]):
            def meth(x): pass
        class C(object):
            def meth(x): pass
        self.assertIsInstance(C(), P)
        self.assertIsInstance(C(), PG)
        with self.assertRaises(TypeError):
            isinstance(C(), PG[T])
        with self.assertRaises(TypeError):
            isinstance(C(), PG[C])
        with self.assertRaises(TypeError):
            isinstance(C(), BadP)
        with self.assertRaises(TypeError):
            isinstance(C(), BadPG)

    def test_protocols_isinstance_init(self):
        T = typing.TypeVar('T')
        @runtime
        class P(Protocol):
            x = 1
        @runtime
        class PG(Protocol[T]):
            x = 1
        class C(object):
            def __init__(self, x):
                self.x = x
        self.assertIsInstance(C(1), P)
        self.assertIsInstance(C(1), PG)

    def test_protocols_support_register(self):
        @runtime
        class P(Protocol):
            x = 1
        class PM(Protocol):
            def meth(self): pass
        class D(PM): pass
        class C(object): pass
        D.register(C)
        P.register(C)
        self.assertIsInstance(C(), P)
        self.assertIsInstance(C(), D)

    def test_none_on_non_callable_doesnt_block_implementation(self):
        @runtime
        class P(Protocol):
            x = 1
        class A(object):
            x = 1
        class B(A):
            x = None
        class C(object):
            def __init__(self):
                self.x = None
        self.assertIsInstance(B(), P)
        self.assertIsInstance(C(), P)

    def test_none_on_callable_blocks_implementation(self):
        @runtime
        class P(Protocol):
            def x(self): pass
        class A(object):
            def x(self): pass
        class B(A):
            x = None
        class C(object):
            def __init__(self):
                self.x = None
        self.assertNotIsInstance(B(), P)
        self.assertNotIsInstance(C(), P)

    def test_non_protocol_subclasses(self):
        class P(Protocol):
            x = 1
        @runtime
        class PR(Protocol):
            def meth(self): pass
        class NonP(P):
            x = 1
        class NonPR(PR): pass
        class C(object):
            x = 1
        class D(object):
            def meth(self): pass
        self.assertNotIsInstance(C(), NonP)
        self.assertNotIsInstance(D(), NonPR)
        self.assertNotIsSubclass(C, NonP)
        self.assertNotIsSubclass(D, NonPR)
        self.assertIsInstance(NonPR(), PR)
        self.assertIsSubclass(NonPR, PR)

    def test_custom_subclasshook(self):
        class P(Protocol):
            x = 1
        class OKClass(object): pass
        class BadClass(object):
            x = 1
        class C(P):
            @classmethod
            def __subclasshook__(cls, other):
                return other.__name__.startswith("OK")
        self.assertIsInstance(OKClass(), C)
        self.assertNotIsInstance(BadClass(), C)
        self.assertIsSubclass(OKClass, C)
        self.assertNotIsSubclass(BadClass, C)

    def test_issubclass_fails_correctly(self):
        @runtime
        class P(Protocol):
            x = 1
        class C: pass
        with self.assertRaises(TypeError):
            issubclass(C(), P)

    def test_defining_generic_protocols(self):
        T = typing.TypeVar('T')
        S = typing.TypeVar('S')
        @runtime
        class PR(Protocol[T, S]):
            def meth(self): pass
        class P(PR[int, T], Protocol[T]):
            y = 1
        self.assertIsSubclass(PR[int, T], PR)
        self.assertIsSubclass(P[str], PR)
        with self.assertRaises(TypeError):
            PR[int]
        with self.assertRaises(TypeError):
            P[int, str]
        with self.assertRaises(TypeError):
            PR[int, 1]
        with self.assertRaises(TypeError):
            PR[int, ClassVar]
        class C(PR[int, T]): pass
        self.assertIsInstance(C[str](), C)

    def test_defining_generic_protocols_old_style(self):
        T = typing.TypeVar('T')
        S = typing.TypeVar('S')
        @runtime
        class PR(Protocol, typing.Generic[T, S]):
            def meth(self): pass
        class P(PR[int, str], Protocol):
            y = 1
        self.assertIsSubclass(PR[int, str], PR)
        self.assertIsSubclass(P, PR)
        with self.assertRaises(TypeError):
            PR[int]
        with self.assertRaises(TypeError):
            PR[int, 1]
        class P1(Protocol, typing.Generic[T]):
            def bar(self, x): pass
        class P2(typing.Generic[T], Protocol):
            def bar(self, x): pass
        @runtime
        class PSub(P1[str], Protocol):
            x = 1
        class Test(object):
            x = 1
            def bar(self, x):
                return x
        self.assertIsInstance(Test(), PSub)
        with self.assertRaises(TypeError):
            PR[int, ClassVar]

    def test_init_called(self):
        T = typing.TypeVar('T')
        class P(Protocol[T]): pass
        class C(P[T]):
            def __init__(self):
                self.test = 'OK'
        self.assertEqual(C[int]().test, 'OK')

    def test_protocols_bad_subscripts(self):
        T = typing.TypeVar('T')
        S = typing.TypeVar('S')
        with self.assertRaises(TypeError):
            class P(Protocol[T, T]): pass
        with self.assertRaises(TypeError):
            class P(Protocol[int]): pass
        with self.assertRaises(TypeError):
            class P(Protocol[T], Protocol[S]): pass
        with self.assertRaises(TypeError):
            class P(Protocol[T], typing.Mapping[T, S]): pass

    def test_generic_protocols_repr(self):
        T = typing.TypeVar('T')
        S = typing.TypeVar('S')
        class P(Protocol[T, S]): pass
        self.assertTrue(repr(P).endswith('P'))
        self.assertTrue(repr(P[T, S]).endswith('P[~T, ~S]'))
        self.assertTrue(repr(P[int, str]).endswith('P[int, str]'))

    def test_generic_protocols_eq(self):
        T = typing.TypeVar('T')
        S = typing.TypeVar('S')
        class P(Protocol[T, S]): pass
        self.assertEqual(P, P)
        self.assertEqual(P[int, T], P[int, T])
        self.assertEqual(P[T, T][typing.Tuple[T, S]][int, str],
                         P[typing.Tuple[int, str], typing.Tuple[int, str]])

    def test_generic_protocols_special_from_generic(self):
        T = typing.TypeVar('T')
        class P(Protocol[T]): pass
        self.assertEqual(P.__parameters__, (T,))
        self.assertIs(P.__args__, None)
        self.assertIs(P.__origin__, None)
        self.assertEqual(P[int].__parameters__, ())
        self.assertEqual(P[int].__args__, (int,))
        self.assertIs(P[int].__origin__, P)

    def test_generic_protocols_special_from_protocol(self):
        @runtime
        class PR(Protocol):
            x = 1
        class P(Protocol):
            def meth(self):
                pass
        T = typing.TypeVar('T')
        class PG(Protocol[T]):
            x = 1
            def meth(self):
                pass
        self.assertTrue(P._is_protocol)
        self.assertTrue(PR._is_protocol)
        self.assertTrue(PG._is_protocol)
        with self.assertRaises(AttributeError):
            self.assertFalse(P._is_runtime_protocol)
        self.assertTrue(PR._is_runtime_protocol)
        self.assertTrue(PG[int]._is_protocol)
        self.assertEqual(P._get_protocol_attrs(), {'meth'})
        self.assertEqual(PR._get_protocol_attrs(), {'x'})
        self.assertEqual(frozenset(PG._get_protocol_attrs()),
                         frozenset({'x', 'meth'}))
        self.assertEqual(frozenset(PG[int]._get_protocol_attrs()),
                         frozenset({'x', 'meth'}))

    def test_no_runtime_deco_on_nominal(self):
        with self.assertRaises(TypeError):
            @runtime
            class C(object): pass
        class Proto(Protocol):
            x = 1
        with self.assertRaises(TypeError):
            @runtime
            class Concrete(Proto):
                pass

    def test_none_treated_correctly(self):
        @runtime
        class P(Protocol):
            x = None  # type: int
        class B(object): pass
        self.assertNotIsInstance(B(), P)
        class C(object):
            x = 1
        class D(object):
            x = None
        self.assertIsInstance(C(), P)
        self.assertIsInstance(D(), P)
        class CI(object):
            def __init__(self):
                self.x = 1
        class DI(object):
            def __init__(self):
                self.x = None
        self.assertIsInstance(C(), P)
        self.assertIsInstance(D(), P)

        def test_protocols_in_unions(self):
            class P(Protocol):
                x = None  # type: int
            Alias = typing.Union[typing.Iterable, P]
            Alias2 = typing.Union[P, typing.Iterable]
            self.assertEqual(Alias, Alias2)

    def test_protocols_pickleable(self):
        global P, CP  # pickle wants to reference the class by name
        T = typing.TypeVar('T')

        @runtime
        class P(Protocol[T]):
            x = 1
        class CP(P[int]):
            pass

        c = CP()
        c.foo = 42
        c.bar = 'abc'
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(c, proto)
            x = pickle.loads(z)
            self.assertEqual(x.foo, 42)
            self.assertEqual(x.bar, 'abc')
            self.assertEqual(x.x, 1)
            self.assertEqual(x.__dict__, {'foo': 42, 'bar': 'abc'})
            s = pickle.dumps(P)
            D = pickle.loads(s)
            class E(object):
                x = 1
            self.assertIsInstance(E(), D)


class TypedDictTests(BaseTestCase):

    def test_basics_iterable_syntax(self):
        Emp = TypedDict('Emp', {'name': str, 'id': int})
        self.assertIsSubclass(Emp, dict)
        self.assertIsSubclass(Emp, typing.MutableMapping)
        if sys.version_info[0] >= 3:
            import collections.abc
            self.assertNotIsSubclass(Emp, collections.abc.Sequence)
        jim = Emp(name='Jim', id=1)
        self.assertIs(type(jim), dict)
        self.assertEqual(jim['name'], 'Jim')
        self.assertEqual(jim['id'], 1)
        self.assertEqual(Emp.__name__, 'Emp')
        self.assertEqual(Emp.__module__, __name__)
        self.assertEqual(Emp.__bases__, (dict,))
        self.assertEqual(Emp.__annotations__, {'name': str, 'id': int})
        self.assertEqual(Emp.__total__, True)

    def test_basics_keywords_syntax(self):
        Emp = TypedDict('Emp', name=str, id=int)
        self.assertIsSubclass(Emp, dict)
        self.assertIsSubclass(Emp, typing.MutableMapping)
        if sys.version_info[0] >= 3:
            import collections.abc
            self.assertNotIsSubclass(Emp, collections.abc.Sequence)
        jim = Emp(name='Jim', id=1)
        self.assertIs(type(jim), dict)
        self.assertEqual(jim['name'], 'Jim')
        self.assertEqual(jim['id'], 1)
        self.assertEqual(Emp.__name__, 'Emp')
        self.assertEqual(Emp.__module__, __name__)
        self.assertEqual(Emp.__bases__, (dict,))
        self.assertEqual(Emp.__annotations__, {'name': str, 'id': int})
        self.assertEqual(Emp.__total__, True)

    def test_typeddict_errors(self):
        Emp = TypedDict('Emp', {'name': str, 'id': int})
        self.assertEqual(TypedDict.__module__, 'typing_extensions')
        jim = Emp(name='Jim', id=1)
        with self.assertRaises(TypeError):
            isinstance({}, Emp)
        with self.assertRaises(TypeError):
            isinstance(jim, Emp)
        with self.assertRaises(TypeError):
            issubclass(dict, Emp)
        with self.assertRaises(TypeError):
            TypedDict('Hi', x=1)
        with self.assertRaises(TypeError):
            TypedDict('Hi', [('x', int), ('y', 1)])
        with self.assertRaises(TypeError):
            TypedDict('Hi', [('x', int)], y=int)

    def test_pickle(self):
        global EmpD  # pickle wants to reference the class by name
        EmpD = TypedDict('EmpD', name=str, id=int)
        jane = EmpD({'name': 'jane', 'id': 37})
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(jane, proto)
            jane2 = pickle.loads(z)
            self.assertEqual(jane2, jane)
            self.assertEqual(jane2, {'name': 'jane', 'id': 37})
            ZZ = pickle.dumps(EmpD, proto)
            EmpDnew = pickle.loads(ZZ)
            self.assertEqual(EmpDnew({'name': 'jane', 'id': 37}), jane)

    def test_optional(self):
        EmpD = TypedDict('EmpD', name=str, id=int)

        self.assertEqual(typing.Optional[EmpD], typing.Union[None, EmpD])
        self.assertNotEqual(typing.List[EmpD], typing.Tuple[EmpD])

    def test_total(self):
        D = TypedDict('D', {'x': int}, total=False)
        self.assertEqual(D(), {})
        self.assertEqual(D(x=1), {'x': 1})
        self.assertEqual(D.__total__, False)


class AnnotatedTests(BaseTestCase):

    def test_repr(self):
        self.assertEqual(
            repr(Annotated[int, 4, 5]),
            "typing_extensions.Annotated[int, 4, 5]"
        )
        self.assertEqual(
            repr(Annotated[List[int], 4, 5]),
            "typing_extensions.Annotated[typing.List[int], 4, 5]"
        )
        self.assertEqual(repr(Annotated), "typing_extensions.Annotated")

    def test_flatten(self):
        A = Annotated[Annotated[int, 4], 5]
        self.assertEqual(A, Annotated[int, 4, 5])
        self.assertEqual(A.__metadata__, (4, 5))

    def test_specialize(self):
        L = Annotated[List[T], "my decoration"]
        LI = Annotated[List[int], "my decoration"]
        self.assertEqual(L[int], Annotated[List[int], "my decoration"])
        self.assertEqual(L[int].__metadata__, ("my decoration",))
        with self.assertRaises(TypeError):
            LI[int]
        with self.assertRaises(TypeError):
            L[int, float]

    def test_hash_eq(self):
        self.assertEqual(len({Annotated[int, 4, 5], Annotated[int, 4, 5]}), 1)
        self.assertNotEqual(Annotated[int, 4, 5], Annotated[int, 5, 4])
        self.assertNotEqual(Annotated[int, 4, 5], Annotated[str, 4, 5])
        self.assertNotEqual(Annotated[int, 4], Annotated[int, 4, 4])
        self.assertEqual(
            {Annotated[int, 4, 5], Annotated[int, 4, 5], Annotated[T, 4, 5]},
            {Annotated[int, 4, 5], Annotated[T, 4, 5]}
        )

    def test_instantiate(self):
        class C:
            classvar = 4

            def __init__(self, x):
                self.x = x

            def __eq__(self, other):
                if not isinstance(other, C):
                    return NotImplemented
                return other.x == self.x

        A = Annotated[C, "a decoration"]
        a = A(5)
        c = C(5)
        self.assertEqual(a, c)
        self.assertEqual(a.x, c.x)
        self.assertEqual(a.classvar, c.classvar)

    def test_instantiate_generic(self):
        MyCount = Annotated[typing_extensions.Counter[T], "my decoration"]
        self.assertEqual(MyCount([4, 4, 5]), {4: 2, 5: 1})
        self.assertEqual(MyCount[int]([4, 4, 5]), {4: 2, 5: 1})

    def test_cannot_instantiate_forward(self):
        A = Annotated["int", (5, 6)]
        with self.assertRaises(TypeError):
            A(5)

    def test_cannot_instantiate_type_var(self):
        A = Annotated[T, (5, 6)]
        with self.assertRaises(TypeError):
            A(5)

    def test_cannot_getattr_typevar(self):
        with self.assertRaises(AttributeError):
            Annotated[T, (5, 7)].x

    def test_attr_passthrough(self):
        class C:
            classvar = 4

        A = Annotated[C, "a decoration"]
        self.assertEqual(A.classvar, 4)
        A.x = 5
        self.assertEqual(C.x, 5)

    def test_hash_eq(self):
        self.assertEqual(len({Annotated[int, 4, 5], Annotated[int, 4, 5]}), 1)
        self.assertNotEqual(Annotated[int, 4, 5], Annotated[int, 5, 4])
        self.assertNotEqual(Annotated[int, 4, 5], Annotated[str, 4, 5])
        self.assertNotEqual(Annotated[int, 4], Annotated[int, 4, 4])
        self.assertEqual(
            {Annotated[int, 4, 5], Annotated[int, 4, 5], Annotated[T, 4, 5]},
            {Annotated[int, 4, 5], Annotated[T, 4, 5]}
        )

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError):
           class C(Annotated):
               pass

    def test_cannot_check_instance(self):
        with self.assertRaises(TypeError):
            isinstance(5, Annotated[int, "positive"])

    def test_cannot_check_subclass(self):
        with self.assertRaises(TypeError):
            issubclass(int, Annotated[int, "positive"])

    def test_subst(self):
        dec = "a decoration"
        dec2 = "another decoration"

        S = Annotated[T, dec2]
        self.assertEqual(S[int], Annotated[int, dec2])

        self.assertEqual(S[Annotated[int, dec]], Annotated[int, dec, dec2])
        L = Annotated[List[T], dec]

        self.assertEqual(L[int], Annotated[List[int], dec])
        with self.assertRaises(TypeError):
            L[int, int]

        self.assertEqual(S[L[int]], Annotated[List[int], dec, dec2])

        D = Annotated[Dict[KT, VT], dec]
        self.assertEqual(D[str, int], Annotated[Dict[str, int], dec])
        with self.assertRaises(TypeError):
            D[int]

        I = Annotated[int, dec]
        with self.assertRaises(TypeError):
            I[None]

        LI = L[int]
        with self.assertRaises(TypeError):
            LI[None]

    def test_annotated_in_other_types(self):
        X = List[Annotated[T, 5]]
        self.assertEqual(X[int], List[Annotated[int, 5]])

class AllTests(BaseTestCase):

    def test_typing_extensions_includes_standard(self):
        a = typing_extensions.__all__
        self.assertIn('ClassVar', a)
        self.assertIn('Type', a)
        self.assertIn('Counter', a)
        self.assertIn('DefaultDict', a)
        self.assertIn('Deque', a)
        self.assertIn('NewType', a)
        self.assertIn('overload', a)
        self.assertIn('Text', a)
        self.assertIn('TYPE_CHECKING', a)

    def test_typing_extensions_defers_when_possible(self):
        exclude = {'overload', 'Text', 'TYPE_CHECKING', 'Final'}
        for item in typing_extensions.__all__:
            if item not in exclude and hasattr(typing, item):
                self.assertIs(
                    getattr(typing_extensions, item),
                    getattr(typing, item))

    def test_typing_extensions_compiles_with_opt(self):
        file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'typing_extensions.py')
        try:
            subprocess.check_output('{} -OO {}'.format(sys.executable,
                                                       file_path),
                                    stderr=subprocess.STDOUT,
                                    shell=True)
        except subprocess.CalledProcessError:
            self.fail('Module does not compile with optimize=2 (-OO flag).')


if __name__ == '__main__':
    main()
