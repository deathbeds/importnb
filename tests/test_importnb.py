import json
import ast
import sys
import linecache
import inspect
from ast import Not
from pathlib import Path
from importnb import Notebook
from pytest import fixture, raises, mark
from importlib import reload

CLOBBER = ("foobar", "foobaz", "test_data")

HERE = locals().get("__file__", None)
HERE = (Path(HERE).parent if HERE else Path()).absolute()

sys.path.insert(0, str(HERE))

try:
    from IPython import get_ipython, InteractiveShell

    InteractiveShell.instance()
except:
    get_ipython = lambda: None

ipy = mark.skipif(not get_ipython(), reason="""Not IPython.""")


@fixture
def clean():
    yield
    unimport(CLOBBER)


def cant_reload(m):
    with raises(ImportError):
        reload(m)


def unimport(ns):
    """unimport a module namespace"""
    from sys import modules, path_importer_cache

    for module in [x for x in modules if x.startswith(ns)]:
        del modules[module]

    path_importer_cache.clear()


def test_basic(clean):
    with Notebook():
        import foobar

    assert foobar.__file__.endswith(".ipynb")
    assert isinstance(foobar.__loader__, Notebook)
    with Notebook():
        assert reload(foobar)


def test_load_module(clean):
    m = Notebook.load_module("foobar")
    assert m.__file__.endswith("foobar.ipynb")
    cant_reload(m)


def test_load_file(clean):
    m = Notebook.load_file("tests/foobar.ipynb")
    assert m.__file__.endswith("foobar.ipynb")
    cant_reload(m)


def test_load_code(clean):
    assert Notebook.load_code("")
    body = Path("tests/foobar.ipynb").read_text()
    m = Notebook.load_code(body)
    cant_reload(m)


def test_package(clean):
    with Notebook():
        import foobaz.foobar

    with raises(ModuleNotFoundError):
        # we can't find a spec for a notebook without the notebook loader context
        reload(foobaz.foobar)

    with Notebook():
        reload(foobaz.foobar)


@mark.parametrize("magic", [True, False])
def test_no_magic(capsys, clean, magic):
    with Notebook(no_magic=not magic):
        if magic:
            with raises(BaseException):
                from test_data import cherry_pick
        else:
            from test_data import cherry_pick

            stdout = capsys.readouterr()[0]
            assert stdout if magic else not stdout


@mark.parametrize("defs", [True, False])
def test_defs_only(defs):
    """import ipy scripts, this won't really work without ipython."""
    with Notebook(defs_only=defs):
        if defs:
            from test_data import cherry_pick

            attr = hasattr(cherry_pick, "an_expr")
            assert not attr if defs else attr
            assert hasattr(cherry_pick, "AClass")
        else:
            with raises(BaseException):
                from test_data import cherry_pick
    unimport("test_data")


def test_fuzzy_finder(clean):
    with Notebook():
        import __bar

    assert __bar.__name__ == "foobar"

    with Notebook():
        reload(__bar)


def test_minified_json():
    with (HERE / "foobar.ipynb").open() as f, open("foobarmin.ipynb", "w") as o:
        json.dump(json.load(f), o, separators=(",", ":"))

    with Notebook():
        import foobarmin

    assert inspect.getsource(foobarmin.function_with_markdown_docstring)

    with open(foobarmin.__file__) as file:
        assert json.load(file)


def test_docstrings(clean):
    with Notebook():
        import foobar
    assert foobar.__doc__
    assert foobar.function_with_markdown_docstring.__doc__
    assert foobar.function_with_python_docstring.__doc__

    assert ast.parse(
        inspect.getsource(foobar.function_with_markdown_docstring)
    ), """The source is invalid"""

    with raises(getattr(json, "JSONDecodeError", ValueError)):
        json.loads("".join(linecache.cache[foobar.__file__][2]))
    assert inspect.getsource(foobar).strip() == "".join(linecache.cache[foobar.__file__][2]).strip()


def test_python_file_takes_precedent(clean):
    py = HERE / "foobar.py"
    py.write_text(("name = 'a python file'"))
    with Notebook():
        import foobar
    assert foobar.__file__.endswith(".py")
    py.unlink()


def test_lazy(capsys):
    """Use stdout to test this depsite there probably being a better way"""
    with Notebook(lazy=True):
        module = __import__("lazy_test")
        assert not capsys.readouterr()[0], capsys.readouterr()[0]
        module.foo, "The function gets executed here"
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
        import foobar as module
    __import__("subprocess").check_call(
        "ipython -m {}".format(module.__name__).split(), cwd=str(Path(module.__file__).parent)
    )
    __import__("subprocess").check_call(
        "ipython -m importnb -- {}".format(module.__file__).split(),
        cwd=str(Path(module.__file__).parent),
    )
