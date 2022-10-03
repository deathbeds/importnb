# coding: utf-8
"""# `loader`

Combine the __import__ finder with the loader.
"""


import ast
import re
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from functools import partial
from importlib import reload
from importlib._bootstrap import _init_module_attrs, _requires_builtin
from importlib._bootstrap_external import FileFinder, decode_source
from importlib.machinery import ModuleSpec, SourceFileLoader
from importlib.util import LazyLoader, find_spec
from pathlib import Path
from types import ModuleType

from . import get_ipython
from .decoder import LineCacheNotebookDecoder, quote
from .docstrings import update_docstring
from .finder import FuzzyFinder, get_loader_details, get_loader_index

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
except ModuleNotFoundError:

    def dedent(body):
        from textwrap import dedent, indent

        if MAGIC.match(body):
            return indent(body, "# ")
        return dedent(body)


__all__ = "Notebook", "reload"


MAGIC = re.compile("^\s*%{2}", re.MULTILINE)


@dataclass
class Interface:
    name: str = None
    path: str = None
    lazy: bool = False
    include_fuzzy_finder: bool = True

    include_markdown_docstring: bool = True
    only_defs: bool = False
    no_magic: bool = False
    _loader_hook_position: int = field(default=0, repr=False)

    def __new__(cls, name=None, path=None, **kwargs):
        kwargs.update(name=name, path=path)
        self = super().__new__(cls)
        self.__init__(**kwargs)
        return self


class BaseLoader(Interface, SourceFileLoader):
    """The simplest implementation of a Notebook Source File Loader."""

    @property
    def loader(self):
        """Create a lazy loader source file loader."""
        loader = type(self)
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
        return self.include_fuzzy_finder and FuzzyFinder or FileFinder

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
        if self.name:
            module.__name__ = self.name
        if getattr(spec, "alias", None):
            # put a fuzzy spec on the modules to avoid re importing it.
            # there is a funky trick you do with the fuzzy finder where you
            # load multiple versions with different finders.

            sys.modules[spec.alias] = module
        module.get_ipython = get_ipython
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

    def __enter__(self):
        path_id, loader_id, details = get_loader_index(".py")
        for _, e in details:
            if all(map(e.__contains__, self.extensions)):
                self._loader_hook_position = None
                return self
        else:
            self._loader_hook_position = loader_id + 1
            details.insert(self._loader_hook_position, (self.loader, self.extensions))
            sys.path_hooks[path_id] = self.finder.path_hook(*details)
            sys.path_importer_cache.clear()
        return self

    def __exit__(self, *excepts):
        if self._loader_hook_position is not None:
            path_id, details = get_loader_details()
            details.pop(self._loader_hook_position)
            sys.path_hooks[path_id] = self.finder.path_hook(*details)
            sys.path_importer_cache.clear()


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


class Notebook(BaseLoader):
    """Notebook is a user friendly file finder and module loader for notebook source code.

    > Remember, restart and run all or it didn't happen.

    Notebook provides several useful options.

    * Lazy module loading.  A module is executed the first time it is used in a script.
    """

    extensions = (".ipy", ".ipynb")

    def parse(self, nodes):
        return ast.parse(nodes, self.path)

    def visit(self, nodes):
        if self.only_defs:
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
        if self.include_markdown_docstring:
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
        import sys
        from sys import path

        if parser is None:
            parser = cls.get_argparser()

        if argv is None:
            from sys import argv

            argv = argv[1:]

        if isinstance(argv, str):
            from shlex import split

            argv = split(argv)

        ns, unknown = parser.parse_known_args(argv)

        if ns.code:
            return cls.load_code(" ".join(ns.args))

        n = ns.args and ns.args[0] or sys.argv[0]

        sys.argv = [n] + unknown
        if ns.module:
            path.insert(0, ns.dir) if ns.dir else ... if "" in path else path.insert(0, "")
            return cls.load_module(n, main=True)
        elif ns.args:
            L = len(ns.args)
            if L > 1:
                raise ValueError(f"Expected one file to execute, but received {L}.")

            if ns.dir:
                n = str(Path(ns.dir) / n)
            return cls.load_file(n)
        else:
            parser.print_help()

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
        from argparse import REMAINDER, ArgumentParser

        if parser is None:
            parser = ArgumentParser("importnb", description="run notebooks as python code")
        parser.add_argument(
            "args", help="the file [default], module or code to execute", nargs=REMAINDER
        )
        parser.add_argument("-f", "--file", action="store_false", help="load a file")
        parser.add_argument("-m", "--module", action="store_true", help="run args as a module")
        parser.add_argument("-c", "--code", action="store_true", help="run args as code")
        parser.add_argument("-d", "--dir", help="the directory path to run in.")
        return parser


def _dict_module(ns):
    m = ModuleType(ns.get("__name__"), ns.get("__doc__"))
    m.__dict__.update(ns)
    return m
