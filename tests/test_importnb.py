from importlib.util import find_spec
import json
import ast
from shutil import copyfile, rmtree
import sys
import linecache
import inspect
from ast import FunctionType, Not
from pathlib import Path
from attr import has

from importnb import Notebook
from pytest import fixture, raises, mark
from importlib import reload

CLOBBER = ("Untitled42", "my_package")

HERE = locals().get("__file__", None)
HERE = (Path(HERE).parent if HERE else Path()).absolute()

sys.path.insert(0, str(HERE))

try:
    from IPython import get_ipython, InteractiveShell

    InteractiveShell.instance()
except:
    get_ipython = lambda: None

ipy = mark.skipif(not get_ipython(), reason="""Not IPython.""")


@fixture(scope="session")
def ref():
    return Notebook.load_file(HERE / "Untitled42.ipynb")


@fixture
def clean():
    yield
    unimport(CLOBBER)


@fixture
def package(ref):
    package = HERE / "my_package"
    package.mkdir(parents=True, exist_ok=True)
    target = package / "my_module.ipynb"
    copyfile(ref.__file__, package / target)
    yield package
    target.unlink()
    rmtree(package)


@fixture
def minified(ref):
    minified = Path(HERE / "minified.ipynb")
    with open(ref.__file__) as f, open(minified, "w") as o:
        json.dump(json.load(f), o, separators=(",", ":"))

    yield
    minified.unlink()

@fixture
def untitled_py(ref):
    py = Path(ref.__file__).with_suffix(".py")
    py.touch()
    yield
    py.unlink()

def cant_reload(m):
    with raises(ImportError):
        reload(m)


def unimport(ns):
    """unimport a module namespace"""
    from sys import modules, path_importer_cache

    for module in [x for x in modules if x.startswith(ns)]:
        del modules[module]

    path_importer_cache.clear()


def test_ref(ref):
    assert ref.__file__.endswith(".ipynb")


def test_finder():
    assert not find_spec("Untitled42")
    with Notebook():
        assert find_spec("Untitled42")


def test_basic(clean, ref):
    with Notebook():
        import Untitled42

    assert ref is not Untitled42
    assert Untitled42.__file__ == ref.__file__
    assert isinstance(Untitled42.__loader__, Notebook)
    with Notebook():
        assert reload(Untitled42)


def test_load_module(clean, ref):
    m = Notebook.load_module("Untitled42")
    assert m.__file__ == ref.__file__
    cant_reload(m)


def test_load_file(clean, ref):
    m = Notebook.load_file("tests/Untitled42.ipynb")
    assert ref.__file__.endswith(m.__file__)
    cant_reload(m)


def test_load_code(clean):
    assert Notebook.load_code(""), "can't load an empty notebook"
    body = Path("tests/Untitled42.ipynb").read_text()
    m = Notebook.load_code(body)
    cant_reload(m)


def test_package(clean, pytester, package):
    from shutil import copyfile

    with Notebook():
        import my_package.my_module

    assert hasattr(my_package, "__path__")
    with raises(ModuleNotFoundError):
        # we can't find a spec for a notebook without the notebook loader context
        reload(my_package.my_module)

    with Notebook():
        reload(my_package.my_module)


@mark.parametrize("magic", [True, False])
def test_no_magic(capsys, clean, magic, ref):
    with Notebook(no_magic=not magic):
        import Untitled42

        stdout = capsys.readouterr()[0]
        if magic:
            assert ref.magic_slug in stdout
        else:
            assert ref.magic_slug not in stdout


@mark.parametrize("defs", [True, False])
def test_defs_only(defs, ref):
    known_defs = [
        k for k, v in vars(ref).items() if not k[0] == "_" and isinstance(v, (type, FunctionType))
    ]
    not_defs = [k for k, v in vars(ref).items() if not k[0] == "_" and isinstance(v, (str,))]
    with Notebook(defs_only=defs):
        import Untitled42

        assert all(hasattr(Untitled42, k) for k in known_defs)

        if not defs:
            assert not any(hasattr(Untitled42, k) for k in not_defs)


def test_fuzzy_finder(clean, ref):
    with Notebook():
        import __ed42

    assert __ed42.__name__ == Path(ref.__file__).stem


def test_minified_json(ref, minified):

    with Notebook():
        import minified as minned
    example_source = inspect.getsource(minned.function_with_a_markdown_docstring)
    assert example_source


def test_docstrings(clean, ref):
    with Notebook():
        import Untitled42 as nb
    assert nb.function_with_a_markdown_docstring.__doc__
    assert nb.class_with_a_python_docstring.__doc__
    assert nb.function_with_a_markdown_docstring.__doc__

    assert nb.__doc__ == ref.__doc__
    assert nb.function_with_a_markdown_docstring.__doc__ == ref.function_with_a_markdown_docstring.__doc__
    assert nb.class_with_a_python_docstring.__doc__ == ref.class_with_a_python_docstring.__doc__
    assert nb.class_with_a_markdown_docstring.__doc__ == ref.class_with_a_markdown_docstring.__doc__

    assert ast.parse(
        inspect.getsource(nb.function_with_a_markdown_docstring)
    ), """The source is invalid"""

    # the line cache isnt json, it is python
    with raises(getattr(json, "JSONDecodeError", ValueError)):
        json.loads("".join(linecache.cache[nb.__file__][2]))

    assert inspect.getsource(nb).strip() == "".join(linecache.cache[nb.__file__][2]).strip()


def test_python_file_takes_precedent(clean, ref, untitled_py):
    with Notebook():
        import Untitled42
    assert Untitled42.__file__.endswith(".py")


def test_lazy(capsys, clean):
    """Use stdout to test this depsite there probably being a better way"""
    with Notebook(lazy=True):
        import Untitled42 as module
    assert not capsys.readouterr()[0], capsys.readouterr()[0]
    module.slug, "The function gets executed here"
    assert capsys.readouterr()[0]


@ipy
def test_import_ipy():
    """import ipy scripts, this won't really work without ipython."""
    with Notebook():
        import ascript

    assert ascript.msg


@ipy
def test_cli():
    with Notebook():
        import Untitled42 as module
    __import__("subprocess").check_call(
        "ipython -m {}".format(module.__name__).split(), cwd=str(Path(module.__file__).parent)
    )
    __import__("subprocess").check_call(
        "ipython -m importnb -- {}".format(module.__file__).split(),
        cwd=str(Path(module.__file__).parent),
    )
