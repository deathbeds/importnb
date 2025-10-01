from __future__ import annotations

import ast
import inspect
import json
import linecache
import os
import sys
from importlib import reload
from importlib.util import find_spec
from pathlib import Path
from shutil import copyfile, rmtree
from types import FunctionType, ModuleType
from typing import TYPE_CHECKING, Any

from pytest import fixture, mark, raises, skip

import importnb

if TYPE_CHECKING:
    from collections.abc import Iterator
    from importlib.machinery import ModuleSpec

    from _pytest.pytester import Pytester
    from pytest import CaptureFixture

    from importnb import Notebook
    from importnb.finder import FileModuleSpec

CLOBBER = ("Untitled42", "my_package", "__42", "__ed42", "__d42")

HERE = locals().get("__file__", None)
HERE = (Path(HERE).parent if HERE else Path()).absolute()

sys.path.insert(0, str(HERE))


@fixture(scope="session")
def ref() -> Iterator[ModuleType]:
    from importnb import Notebook

    os.environ["NOT_UNTITLED42_CLI"] = "1"

    nb = Notebook.load_file(HERE / "Untitled42.ipynb")

    yield nb

    os.environ.pop("NOT_UNTITLED42_CLI", None)


@fixture
def clean() -> Iterator[None]:
    yield
    unimport(CLOBBER)


@fixture
def package(ref: ModuleType) -> Iterator[Path]:
    package = HERE / "my_package"
    package.mkdir(parents=True, exist_ok=True)
    target = package / "my_module.ipynb"
    copyfile(f"{ref.__file__}", package / target)
    yield package
    target.unlink()
    rmtree(package)


@fixture
def minified(ref: ModuleType) -> Iterator[None]:
    minified = Path(HERE / "minified.ipynb")
    with open(f"{ref.__file__}") as f, open(minified, "w") as o:
        json.dump(json.load(f), o, separators=(",", ":"))

    yield
    minified.unlink()


@fixture
def untitled_py(ref: ModuleType) -> Iterator[None]:
    assert ref.__file__
    py = Path(ref.__file__).with_suffix(".py")
    py.touch()
    yield
    py.unlink()


def cant_reload(m: ModuleType) -> None:
    with raises(ImportError):
        reload(m)


def unimport(ns: str | tuple[str, ...]) -> None:
    """Remove modules from a namespace"""
    from sys import modules, path_importer_cache

    for module in [x for x in modules if x.startswith(ns)]:
        del modules[module]

    path_importer_cache.clear()


def test_version() -> None:
    assert importnb.__version__


def test_ref(ref: ModuleType) -> None:
    assert ref.__file__
    assert ref.__file__.endswith(".ipynb")


def test_finder() -> None:
    assert not find_spec("Untitled42")
    from importnb import Notebook

    with Notebook():
        assert find_spec("Untitled42")


def test_basic(clean: None, ref: ModuleType) -> None:
    from importnb import Notebook

    with Notebook():
        import Untitled42

    assert ref is not Untitled42
    assert Untitled42.__file__ == ref.__file__
    assert isinstance(Untitled42.__loader__, Notebook)
    with Notebook():
        assert reload(Untitled42)


def test_load_module(clean: None, ref: ModuleType) -> None:
    from importnb import Notebook

    m = Notebook.load_module("Untitled42")
    assert m.__file__ == ref.__file__
    cant_reload(m)


def test_load_module_package(clean: None, package: Path) -> None:
    from importnb import Notebook

    m = Notebook.load_module("my_package.my_module")
    assert m


def test_load_file(clean: None, ref: ModuleType) -> None:
    from importnb import Notebook

    m = Notebook.load_file("docs/Untitled42.ipynb")
    assert m.__file__
    assert ref.__file__
    assert ref.__file__.endswith(str(Path(m.__file__)))
    cant_reload(m)


def test_load_code(clean: None) -> None:
    from importnb import Notebook

    assert Notebook.load_code(""), "can't load an empty notebook"
    body = Path("docs/Untitled42.ipynb").read_text()
    m = Notebook.load_code(body)
    cant_reload(m)


def test_package(clean: None, package: Path) -> None:
    from importnb import Notebook

    with Notebook():
        import my_package.my_module

    assert hasattr(my_package, "__path__")
    with raises(ModuleNotFoundError):
        # we can't find a spec for a notebook without the notebook loader context
        reload(my_package.my_module)

    with Notebook():
        reload(my_package.my_module)


@mark.parametrize("magic", [True, False])
def test_no_magic(capsys: CaptureFixture[str], clean: None, magic: bool, ref: ModuleType) -> None:
    from importnb import Notebook, is_ipython

    ipy = is_ipython()
    expected = ref.SLUG.rstrip()

    with Notebook(no_magic=not magic):
        import Untitled42

        assert Untitled42

        stdout = capsys.readouterr()[0]
        if ipy:
            if magic:
                assert expected
            else:
                assert expected


@mark.parametrize("defs", [True, False])
def test_defs_only(defs: bool, ref: ModuleType) -> None:
    from importnb import Notebook

    known_defs = [
        k for k, v in vars(ref).items() if k[0] != "_" and isinstance(v, (type, FunctionType))
    ]
    not_defs = [k for k, v in vars(ref).items() if k[0] != "_" and isinstance(v, (str,))]
    with Notebook(include_non_defs=not defs):
        import Untitled42

        assert all(hasattr(Untitled42, k) for k in known_defs)

        if defs:
            assert not any(hasattr(Untitled42, k) for k in not_defs)


def test_fuzzy_finder(clean: None, ref: ModuleType, capsys: CaptureFixture[str]) -> None:
    from importnb import Notebook

    outs = []
    with Notebook():
        import __ed42

        assert __ed42

        outs.append(capsys.readouterr())
        import __d42

        assert __d42

        outs.append(capsys.readouterr())
        import __42

        assert __42

        outs.append(capsys.readouterr())
        import __42

        assert __42

        outs.append(capsys.readouterr())
        import __42 as nb

        assert nb

        outs.append(capsys.readouterr())

    assert outs[0] == outs[1] == outs[2]
    assert not any([outs[3].out, outs[3].err] + [outs[4].out, outs[4].err])


def as_file_spec_loader(
    spec: ModuleSpec | None,
) -> tuple[FileModuleSpec, Notebook]:
    from importnb import Notebook
    from importnb.finder import FileModuleSpec

    assert isinstance(spec, FileModuleSpec)
    loader = spec.loader
    assert isinstance(loader, Notebook)
    return spec, loader


def test_fuzzy_finder_conflict(clean: None, ref: ModuleType) -> None:
    from importnb import Notebook

    try:
        with Notebook():
            loader = as_file_spec_loader(find_spec("__d42"))[1]

            assert find_spec("__d42")

            new = HERE / "d42.ipynb"
            new.write_text("{}")
            loader2 = as_file_spec_loader(find_spec("__d42"))[1]
            assert loader.path != loader2.path
    finally:
        with Notebook():
            new.unlink()
            loader3 = as_file_spec_loader(find_spec("__d42"))[1]
            assert loader.path == loader3.path


def test_minified_json(ref: ModuleType, minified: None) -> None:
    from importnb import Notebook

    with Notebook():
        import minified as minned

        example_source = inspect.getsource(minned.function_with_a_markdown_docstring)
        assert example_source


def test_docstrings(clean: None, ref: ModuleType) -> None:
    from importnb import Notebook

    with Notebook():
        import Untitled42 as nb

        assert nb
        assert isinstance(nb.__file__, str)
    assert nb.function_with_a_markdown_docstring.__doc__
    assert nb.class_with_a_python_docstring.__doc__
    assert nb.function_with_a_markdown_docstring.__doc__

    assert nb.__doc__ == ref.__doc__
    assert (
        nb.function_with_a_markdown_docstring.__doc__
        == ref.function_with_a_markdown_docstring.__doc__
    )
    assert nb.class_with_a_python_docstring.__doc__ == ref.class_with_a_python_docstring.__doc__
    assert nb.class_with_a_markdown_docstring.__doc__ == ref.class_with_a_markdown_docstring.__doc__

    assert ast.parse(
        inspect.getsource(nb.function_with_a_markdown_docstring),
    ), """The source is invalid"""

    # the line cache isn't json, it is python
    cached = linecache.cache[nb.__file__]
    assert len(cached) >= 2

    with raises(getattr(json, "JSONDecodeError", ValueError)):
        json.loads("".join(cached[2]))

    assert inspect.getsource(nb).strip() == "".join(cached[2]).strip()


def test_python_file_takes_precedent(clean: None, ref: ModuleType, untitled_py: None) -> None:
    from importnb import Notebook

    with Notebook():
        import Untitled42
    assert f"{Untitled42.__file__}".endswith(".py")


def test_lazy(capsys: CaptureFixture[str], clean: None) -> None:
    """Use ``stdout`` to test this, there probably being a better way"""
    from importnb import Notebook

    with Notebook(lazy=True):
        import Untitled42 as module
    assert not capsys.readouterr()[0], capsys.readouterr()[0]
    module.SLUG, "The function gets executed here"
    assert capsys.readouterr()[0]


def test_import_ipy() -> None:
    """Import ``.ipy`` scripts, this won't really work without ``IPython``."""
    from importnb import Notebook, is_ipython

    if not is_ipython():
        import pytest

        pytest.skip("Not running under IPython")
    with Notebook():
        import ascript

    assert ascript.msg


def test_cli(clean: None) -> None:
    import sys
    from subprocess import CalledProcessError

    from psutil import Popen

    from importnb import Notebook, is_ipython

    if not is_ipython():
        import pytest

        pytest.skip("Not running under IPython")

    with Notebook():
        import Untitled42 as module
    ipym = [sys.executable, "-m", "ipython", "-m"]
    cmd = [*ipym, module.__name__]
    cwd = f"{Path(module.__file__).parent}"
    if not (rc := Popen(cmd, cwd=cwd).wait()):
        raise CalledProcessError(rc, cmd)
    cmd = [*ipym, "importnb", "--", module.__file__]
    if not (rc := Popen(cmd, cwd=cwd).wait()):
        raise CalledProcessError(rc, cmd)


@mark.filterwarnings("ignore::DeprecationWarning")
def test_top_level_async() -> None:
    from importnb import Notebook

    with Notebook():
        import async_cells

    assert async_cells


@mark.parametrize(
    ("data_loader", "data_writer"), [("yaml", "ruamel"), ("toml", "tomli_w"), ("json", "json")]
)
def test_data_loaders(data_loader: str, data_writer: str, pytester: Pytester) -> None:
    import io

    sys.path.insert(0, str(pytester._path))

    from importnb import imports

    some_random_data: dict[str, list[dict[str, Any]]] = {"top": [{}]}

    if not find_spec(data_writer):
        skip(f"{data_writer} not available")

    if data_loader == "json":
        import json

        data_text = json.dumps(some_random_data)

    if data_loader == "toml":
        import tomli_w

        data_text = tomli_w.dumps(some_random_data)

    if data_loader == "yaml":
        from ruamel.yaml import YAML

        yaml = YAML(typ="safe", pure=True)
        y = io.StringIO()
        yaml.dump(some_random_data, y)
        data_text = y.getvalue()

    pytester.makefile(f".{data_loader}", some_data_module=data_text)

    with imports(data_loader):
        import some_data_module  # type: ignore[import-not-found]

    assert f"{some_data_module.__file__}".endswith(f".{data_loader}")
