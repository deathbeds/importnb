# coding: utf-8
"""# `loader`

the loading machinery for notebooks style documents, and less.
notebooks combine code, markdown, and raw cells to create a complete document.
the importnb loader provides an interface for transforming these objects to valid python.
"""


import ast
from contextlib import contextmanager
import re
import shlex
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
from importlib import _bootstrap as bootstrap

from . import get_ipython
from .decoder import LineCacheNotebookDecoder, quote
from .docstrings import update_docstring
from .finder import FuzzyFinder, get_loader_details, get_loader_index

_GTE38 = sys.version_info.major == 3 and sys.version_info.minor >= 8


__all__ = "Notebook", "reload"


MAGIC = re.compile("^\s*%{2}", re.MULTILINE)


@dataclass
class Interface:
    """a configurable loader interface"""
    name: str = None
    path: str = None
    lazy: bool = False
    extensions: tuple = field(default_factory=[".ipy", ".ipynb"].copy)
    include_fuzzy_finder: bool = True

    include_markdown_docstring: bool = True
    include_non_defs: bool = True
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
        """generate a new loader based on the state of an existing loader."""
        loader = type(self)
        if self.lazy:
            loader = LazyLoader.factory(loader)
        # Strip the leading underscore from slots
        params = asdict(self)
        params.pop("name")
        params.pop("path")
        return partial(loader, **params)

    @property
    def finder(self):
        """generate a new finder based on the state of an existing loader"""
        return self.include_fuzzy_finder and FuzzyFinder or FileFinder

    def raw_to_source(self, source):
        """transform a string from a raw file to python source."""
        if self.path and self.path.endswith(".ipynb"):
            # when we encounter notebooks we apply different transformers to the diff cell types
            return LineCacheNotebookDecoder(
                code=self.code, raw=self.raw, markdown=self.markdown
            ).decode(source, self.path)

        # for a normal file we just apply the code transformer.
        return self.code(source)

    def get_data(self, path):
        """Needs to return the string source for the module."""
        return self.raw_to_source(decode_source(super().get_data(self.path)))

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

    def visit(self, nodes):
        if self.include_non_defs:
            return nodes
        return DefsOnly().visit(nodes)

    def code(self, str):
        if self.no_magic:
            if MAGIC.match(str):
                return comment(str)
        return super().code(str)

    def source_to_nodes(self, source, path="<unknown>"):
        nodes = bootstrap._call_with_frames_removed(ast.parse, source, path)
        if self.include_markdown_docstring:
            nodes = update_docstring(nodes)
        nodes = self.visit(nodes)
        return ast.fix_missing_locations(nodes)

    def nodes_to_code(self, nodes, path="<unknown>", *, _optimize=-1):
        return bootstrap._call_with_frames_removed(
            compile, nodes, path, "exec", dont_inherit=True, optimize=_optimize
        )

    def source_to_code(self, source, path="<unknown>", *, _optimize=-1):
        """* Convert the current source to ast
        * Apply ast transformers.
        * Compile the code."""
        nodes = self.source_to_nodes(source, path)
        return self.nodes_to_code(nodes, path, _optimize=_optimize)

    @classmethod
    def load_file(cls, filename, main=True, **kwargs):
        """Import a notebook as a module from a filename.

        dir: The directory to load the file from.
        main: Load the module in the __main__ context.

        >>> assert Notebook.load_file('foo.ipynb')
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

        main: Load the module in the __main__ context.

        >>> assert Notebook.load_module('foo')
        """
        from runpy import _run_module_as_main, run_module

        with cls() as loader:
            if main:
                return _dict_module(_run_module_as_main(module))
            else:
                spec = find_spec(module)

                module = spec.loader.create_module(spec)
                spec.loader.exec_module(module)
                return module

    @classmethod
    def load_argv(cls, argv=None, *, parser=None):
        """load a module based on python arguments

        load a notebook from its file name
        >>> Notebook.load_argv("foo.ipynb --arg abc")

        load the same notebook from a module alias.
        >>> Notebook.load_argv("-m foo --arg abc")
        """
        if parser is None:
            parser = cls.get_argparser()

        if argv is None:
            from sys import argv

            argv = argv[1:]

        if isinstance(argv, str):
            argv = shlex.split(argv)

        module = cls.load_ns(parser.parse_args(argv))
        if module is None:
            return parser.print_help()

        return module

    @classmethod
    def load_ns(cls, ns):
        """load a module from a namespace, used when loading module from sys.argv parameters."""

        if ns.tasks:
            # i don't quite why we need to do this here, but we do. so don't move it
            from doit.doit_cmd import DoitMain
            from doit.cmd_base import ModuleTaskLoader

        if ns.code:
            with main_argv(sys.argv[0], ns.args):
                result = cls.load_code(ns.code)
        elif ns.module:
            if ns.dir:
                if ns.dir not in sys.path:
                    sys.path.insert(0, ns.dir)
            elif "" in sys.path:
                pass
            else:
                sys.path.insert(0, "")
            with main_argv(ns.module, ns.args):
                result = cls.load_module(ns.module, main=True)
        elif ns.file:
            where = Path(ns.dir, ns.file) if ns.dir else Path(ns.file)
            with main_argv(str(where), ns.args):
                result = cls.load_file(ns.file)
        else:
            return

        if ns.tasks:
            DoitMain(ModuleTaskLoader(result)).run(ns.args)
        return result

    @classmethod
    def load_code(cls, code, argv=None, mod_name=None, script_name=None, main=False):
        """load a module from raw source code"""

        from runpy import _run_module_code

        self = cls()
        name = main and "__main__" or mod_name or "<raw code>"

        return _dict_module(
            _run_module_code(self.raw_to_source(code), mod_name=name, script_name=script_name)
        )

    @staticmethod
    def get_argparser(parser=None):
        from argparse import REMAINDER, ArgumentParser

        if parser is None:
            parser = ArgumentParser("importnb", description="run notebooks as python code")
        parser.add_argument("file", nargs="?", help="run a file")
        parser.add_argument("args", nargs=REMAINDER, help="arguments to pass to script")
        parser.add_argument("-m", "--module", help="run a module")
        parser.add_argument("-c", "--code", help="run raw code")
        parser.add_argument("-d", "--dir", help="path to run script in")
        parser.add_argument("-t", "--tasks", action="store_true", help="run doit tasks")
        return parser


def _dict_module(ns):
    m = ModuleType(ns.get("__name__"), ns.get("__doc__"))
    m.__dict__.update(ns)
    return m


@contextmanager
def main_argv(prog, args=None):
    if args is not None:
        args = [prog] + list(args)
        prior, sys.argv = sys.argv, args
    yield
    if args is not None:
        sys.argv = prior


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
