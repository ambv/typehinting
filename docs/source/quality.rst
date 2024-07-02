.. _testing:

********************************************
Testing and Ensuring Type Annotation Quality
********************************************

Testing Annotation Accuracy
===========================

When creating a package with type annotations, authors may want to validate
that the annotations they publish meet their expectations.
This is especially important for library authors, for whom the published
annotations are part of the public interface to their package.

There are several approaches to this problem, and this document will show
a few of them.

.. note::

    For simplicity, we will assume that type-checking is done with ``mypy``.
    Many of these strategies can be applied to other type-checkers as well.

Testing Using ``assert_type`` and ``--warn-unused-ignores``
-----------------------------------------------------------

The idea is to write normal Python files, set aside in a dedicated directory like ``typing_tests/``, which assert certain properties
of the type annotations.

``assert_type`` (``mypy`` 0.950 and above) can ensure that the type annotation produces the expected type.

If the following file is under test:

.. code-block:: python

    # foo.py
    def bar(x: int) -> str:
        return str(x)

then the following file tests ``foo.py``:

.. code-block:: python

    from typing_extensions import assert_type

    assert_type(bar(42), str)

Clever use of ``mypy --warn-unused-ignores`` can be used to check that certain
expressions are or are not well-typed. The idea is to have valid expressions along
with invalid expressions annotated with ``type: ignore`` comments. When
``mypy --warn-unused-ignores`` is run on these files, it should pass.

This strategy does not offer strong guarantees about the types under test, but
it requires no additional tooling.

If the following file is under test:

.. code-block:: python

    # foo.py
    def bar(x: int) -> str:
        return str(x)

then the following file tests ``foo.py``:

.. code-block:: python

    bar(42)
    bar("42")  # type: ignore [arg-type]
    bar(y=42)  # type: ignore [call-arg]
    r1: str = bar(42)
    r2: int = bar(42)  # type: ignore [assignment]

Checking ``reveal_type`` output from ``mypy.api.run``
-----------------------------------------------------

``mypy`` provides a subpackage named ``api`` for invoking ``mypy`` from a
python process. In combination with ``reveal_type``, this can be used to write
a function which gets the ``reveal_type`` output from an expression. Once
that's obtained, tests can assert strings and regular expression matches
against it.

This approach requires writing a set of helpers to provide a good testing
experience, and it runs mypy once per test case (which can be slow).
However, it builds only on ``mypy`` and the test framework of your choice.

The following example could be integrated into a testsuite written in
any framework:

.. code-block:: python

    import re
    from mypy import api

    def get_reveal_type_output(filename):
        result = api.run([filename])
        stdout = result[0]
        match = re.search(r'note: Revealed type is "([^"]+)"', stdout)
        assert match is not None
        return match.group(1)


For example, we can use the above to provide a ``run_reveal_type`` pytest
fixture which generates a temporary file and uses it as the input to
``get_reveal_type_output``:

.. code-block:: python

    import os
    import pytest

    @pytest.fixture
    def _in_tmp_path(tmp_path):
        cur = os.getcwd()
        try:
            os.chdir(tmp_path)
            yield
        finally:
            os.chdir(cur)

    @pytest.fixture
    def run_reveal_type(tmp_path, _in_tmp_path):
        content_path = tmp_path / "reveal_type_test.py"

        def func(code_snippet, *, preamble = ""):
            content_path.write_text(preamble + f"reveal_type({code_snippet})")
            return get_reveal_type_output("reveal_type_test.py")

        return func


For more details, see `the documentation on mypy.api
<https://mypy.readthedocs.io/en/stable/extending_mypy.html#integrating-mypy-into-another-python-application>`_.

pytest-mypy-plugins
-------------------

`pytest-mypy-plugins <https://github.com/typeddjango/pytest-mypy-plugins>`_ is
a plugin for ``pytest`` which defines typing test cases as YAML data.
The test cases are run through ``mypy`` and the output of ``reveal_type`` can
be asserted.

This project supports complex typing arrangements like ``pytest`` parametrized
tests and per-test ``mypy`` configuration. It requires that you are using
``pytest`` to run your tests, and runs ``mypy`` in a subprocess per test case.

This is an example of a parametrized test with ``pytest-mypy-plugins``:

.. code-block:: yaml

    - case: with_params
      parametrized:
        - val: 1
          rt: builtins.int
        - val: 1.0
          rt: builtins.float
      main: |
        reveal_type({[ val }})  # N: Revealed type is '{{ rt }}'

pytest-mypy-testing
-------------------

`pytest-mypy-testing <https://github.com/davidfritzsche/pytest-mypy-testing>`_ is another
plugin for ``pytest``. The main difference between :ref:`pytest-mypy-plugins` is that
:ref:`pytest-mypy-testing` allows writing tests inside Python code and/or
mixed with actual tests.

.. warning::

    pytest-mypy-testing uses the Python
    `ast<https://docs.python.org/3/library/ast.html>`_ module to parse
    candidate files and does not import any file, i.e., the decorator must be
    exactly named ``@pytest.mark.mypy_testing``!


These are examples of testing with ``pytest-mypy-testing``:

.. code-block:: python

    @pytest.mark.mypy_testing
    def mypy_use_reveal_type():
        reveal_type(123)  # N: Revealed type is 'Literal[123]?'
        reveal_type(456)  # R: Literal[456]?

.. code-block:: python

    def foo(num: int) -> str:
        return str(num)


    @pytest.mark.mypy_testing
    def test_foo():
        result = foo(1)
        reveal_type(result)  # R: builtins.str

        assert result == "1"


Improving Type Completeness
===========================

One of the goals of many libraries is to ensure that they are "fully type
annotated", meaning that they provide complete and accurate type annotations
for all functions, classes, and objects. Having full annotations is referred to
as "type completeness" or "type coverage".

Here are some tips for increasing the type completeness score for your
library:

-  Make type completeness an output of your testing process. Several type
   checkers have options for generating useful output, warnings, or even
   reports.
-  If your package includes tests or sample code, consider removing them
   from the distribution. If there is good reason to include them,
   consider placing them in a directory that begins with an underscore
   so they are not considered part of your library’s interface.
-  If your package includes submodules that are meant to be
   implementation details, rename those files to begin with an
   underscore.
-  If a symbol is not intended to be part of the library’s interface and
   is considered an implementation detail, rename it such that it begins
   with an underscore. It will then be considered private and excluded
   from the type completeness check.
-  If your package exposes types from other libraries, work with the
   maintainers of these other libraries to achieve type completeness.

.. warning::

    The ways in which different type checkers evaluate and help you achieve
    better type coverage may differ. Some of the above recommendations may or
    may not be helpful to you, depending on which type checking tools you use.

``mypy`` disallow options
-------------------------

``mypy`` offers several options which can detect untyped code.
More details can be found in `the mypy documentation on these options
<https://mypy.readthedocs.io/en/latest/command_line.html#untyped-definitions-and-calls>`_.

Some basic usages which make ``mypy`` error on untyped data are::

    mypy --disallow-untyped-defs
    mypy --disallow-incomplete-defs

``pyright`` type verification
-----------------------------

pyright has a special command line flag, ``--verifytypes``, for verifying
type completeness. You can learn more about it from
`the pyright documentation on verifying type completeness
<https://github.com/microsoft/pyright/blob/main/docs/typed-libraries.md#verifying-type-completeness>`_.

``mypy`` reports
----------------

``mypy`` offers several options options for generating reports on its analysis.
See `the mypy documentation on report generation
<https://mypy.readthedocs.io/en/stable/command_line.html#report-generation>`_ for details.
