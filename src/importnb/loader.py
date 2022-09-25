# coding: utf-8
"""# `loader`

Combine the __import__ finder with the loader.
"""


import ast
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
import re
import textwrap
from types import ModuleType
from functools import partial
from importlib import reload
from importlib.machinery import ModuleSpec, SourceFileLoader

from .decoder import LineCacheNotebookDecoder, quote
from .docstrings import update_docstring
from .finder import FuzzyFinder, FuzzySpec, get_loader_details

from importlib._bootstrap import _requires_builtin
from importlib._bootstrap_external import decode_source, FileFinder
from importlib._bootstrap import _init_module_attrs
from importlib.util import LazyLoader, find_spec


_GTE38 = sys.version_info.major == 3 and sys.version_info.minor >= 8

try:
    import IPython
    from IPython.core.inputsplitter import IPythonInputSplitter

    dedent = IPythonInputSplitter(
        line_input_checker=False,
        physical_line_transforms=[
            IPython.core.inputsplitter.leading_indent(),
            IPython.core.inputsplitter.ipy_prompt(),
            IPython.core.inputsplitter.cellmagic(end_on_blank_line=False),
        ],
    ).transform_cell
except:
    from textwrap import dedent

__all__ = "Notebook", "reload"


MAGIC = re.compile("^.*%{2}")


class FinderContextManager:
    """
    FinderContextManager is the base class for the notebook loader.  It provides
    a context manager that replaces `FileFinder` in the `sys.path_hooks` to include
    an instance of the class in the python findering system.

    >>> with FinderContextManager() as f:
    ...      id, ((loader_cls, _), *_) = get_loader_details()
    ...      assert issubclass(loader_cls, FinderContextManager)
    >>> id, ((loader_cls, _), *_) = get_loader_details()
    >>> loader_cls = __import__("inspect").unwrap(loader_cls)
    >>> assert not (isinstance(loader_cls, type) and issubclass(loader_cls, FinderContextManager))
    """

    extensions = tuple()
    _position = 0

    finder = FileFinder

    @property
    def loader(self):
        return type(self)

    def __enter__(self):
        id, details = get_loader_details()
        details.insert(self._position, (self.loader, self.extensions))
        sys.path_hooks[id] = self.finder.path_hook(*details)
        sys.path_importer_cache.clear()
        return self

    def __exit__(self, *excepts):
        id, details = get_loader_details()
        details.pop(self._position)
        sys.path_hooks[id] = self.finder.path_hook(*details)
        sys.path_importer_cache.clear()


@dataclass
class Interface:
    name: str = None
    path: str = None
    lazy: bool = False
    position: int = 0
    fuzzy: bool = True
    markdown_docstring: bool = True
    defs_only: bool = False
    no_magic: bool = False

    def __new__(cls, name=None, path=None, **kwargs):
        kwargs.update(name=name, path=path)
        self = super().__new__(cls)
        self.__init__(**kwargs)
        return self


class NotebookBaseLoader(Interface, SourceFileLoader, FinderContextManager):
    """The simplest implementation of a Notebook Source File Loader."""

    extensions = (".ipy", ".ipynb")

    @property
    def loader(self):
        """Create a lazy loader source file loader."""
        loader = super().loader
        if self.lazy and (sys.version_info.major, sys.version_info.minor) != (3, 4):
            loader = LazyLoader.factory(loader)
        # Strip the leading underscore from slots
        params = asdict(self)
        params.pop("name")
        params.pop("path")
        return partial(loader, **params)

    @property
    def finder(self):
        """Permit fuzzy finding of files with special characters."""
        return self.fuzzy and FuzzyFinder or super().finder

    def translate(self, source):
        if self.path and self.path.endswith(".ipynb"):
            return LineCacheNotebookDecoder(
                code=self.code, raw=self.raw, markdown=self.markdown
            ).decode(source, self.path)
        return self.code(source)

    def get_data(self, path):
        """Needs to return the string source for the module."""

        return self.translate(self.decode())

    def create_module(self, spec):
        module = ModuleType(str(spec.name))
        _init_module_attrs(spec, module)
        if isinstance(spec, FuzzySpec):
            sys.modules[spec.alias] = module
        if self.name:
            module.__name__ = self.name
        return module

    def decode(self):
        return decode_source(super().get_data(self.path))

    def code(self, str):
        return dedent(str)

    def markdown(self, str):
        return quote(str)

    def raw(self, str):
        return comment(str)

    def visit(self, node):
        return node

    @classmethod
    @_requires_builtin
    def is_package(cls, fullname):
        """Return False as built-in modules are never packages."""
        if "." not in fullname:
            return True
        return super().is_package(fullname)

    get_source = get_data


class FileModuleSpec(ModuleSpec):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_fileattr = True


def comment(str):
    return textwrap.indent(str, "# ")


class DefsOnly(ast.NodeTransformer):
    INCLUDE = ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef

    def visit_Module(self, node):
        args = ([x for x in node.body if isinstance(x, self.INCLUDE)],)
        if _GTE38:
            args += (node.type_ignores,)
        return ast.Module(*args)


class Notebook(NotebookBaseLoader):
    """Notebook is a user friendly file finder and module loader for notebook source code.

    > Remember, restart and run all or it didn't happen.

    Notebook provides several useful options.

    * Lazy module loading.  A module is executed the first time it is used in a script.
    """

    def parse(self, nodes):
        return ast.parse(nodes, self.path)

    def visit(self, nodes):
        if self.defs_only:
            nodes = DefsOnly().visit(nodes)
        return nodes

    def code(self, str):
        if self.no_magic:
            if MAGIC.match(str):
                return comment(str)
        return super().code(str)

    def source_to_code(self, nodes, path, *, _optimize=-1):
        """* Convert the current source to ast
        * Apply ast transformers.
        * Compile the code."""
        if not isinstance(nodes, ast.Module):
            nodes = self.parse(nodes)
        if self.markdown_docstring:
            nodes = update_docstring(nodes)
        return super().source_to_code(
            ast.fix_missing_locations(self.visit(nodes)), path, _optimize=_optimize
        )

    @classmethod
    def load_file(cls, filename, main=True, **kwargs):
        """Import a notebook as a module from a filename.

        dir: The directory to load the file from.
        main: Load the module in the __main__ context.

        > assert Notebook.load('loader.ipynb')
        """
        name = main and "__main__" or filename
        loader = cls(name, str(filename), **kwargs)
        spec = FileModuleSpec(name, loader, origin=loader.path)
        module = loader.create_module(spec)
        loader.exec_module(module)
        return module

    @classmethod
    def load_module(cls, module, main=False, **kwargs):
        """Import a notebook as a module.

        dir: The directory to load the file from.
        main: Load the module in the __main__ context.

        > assert Notebook.load('loader.ipynb')
        """
        from runpy import _run_module_as_main, run_module

        with cls() as loader:
            if main:
                return _dict_module(_run_module_as_main(module))
            else:
                spec = find_spec(module)
                m = spec.loader.create_module(spec)
                spec.loader.exec_module(m)
                return m

    @classmethod
    def load_argv(cls, argv=None, *, parser=None):
        from sys import path

        if parser is None:
            parser = cls.get_argparser()

        if argv is None:
            from sys import argv

            argv = argv[1:]

        if isinstance(argv, str):
            from shlex import split

            argv = split(argv)

        known, unknown = parser.parse_known_args(argv)
        ns = vars(known)

        m, n, c, wd = ns.pop("module"), ns.pop("name"), ns.pop("code"), ns.pop("dir") or ""

        path.insert(0, wd)

        sys.argv = [n] + unknown
        if m:
            return cls.load_module(n, main=True)
        elif c:
            return cls.load_code(c, n)
        else:
            return cls.load_file(n)

    @classmethod
    def load_code(cls, code, mod_name=None, script_name=None, main=False):
        from runpy import _run_module_code

        self = cls()
        name = main and "__main__" or mod_name or "<markdown code>"

        return _dict_module(
            _run_module_code(self.translate(code), mod_name=name, script_name=script_name)
        )

    @staticmethod
    def get_argparser(parser=None):
        from argparse import ArgumentParser, REMAINDER

        if parser is None:
            parser = ArgumentParser()
        parser.add_argument("name")
        parser.add_argument("-m", "--module", action="store_true")
        parser.add_argument("-d", "--dir")
        parser.add_argument("-c", "--code")
        return parser

def _dict_module(ns):
    m = ModuleType(ns.get("__name__"), ns.get("__doc__"))
    m.__dict__.update(ns)
    return m
