"""# `loader`

the loading machinery for notebooks style documents, and less.
notebooks combine code, markdown, and raw cells to create a complete document.
the importnb loader provides an interface for transforming these objects to valid python.
"""


import ast
import inspect
import re
import shlex
import sys
import textwrap
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from functools import partial
from importlib import _bootstrap as bootstrap
from importlib import reload
from importlib._bootstrap import _init_module_attrs, _requires_builtin
from importlib._bootstrap_external import FileFinder, decode_source
from importlib.machinery import SourceFileLoader
from importlib.util import LazyLoader, find_spec
from pathlib import Path
from types import ModuleType

from . import get_ipython
from .decoder import LineCacheNotebookDecoder, quote
from .docstrings import update_docstring
from .finder import FileModuleSpec, FuzzyFinder, get_loader_details, get_loader_index

__all__ = "Notebook", "reload"

VERSION = sys.version_info.major, sys.version_info.minor

MAGIC = re.compile(r"^\s*%{2}", re.MULTILINE)
ALLOW_TOP_LEVEL_AWAIT = getattr(ast, "PyCF_ALLOW_TOP_LEVEL_AWAIT", 0x0)


def _get_co_flags_set(co_flags):
    """Return a deconstructed set of code flags from a code object."""
    flags = set()
    for i in range(12):
        flag = 1 << i
        if co_flags & flag:
            flags.add(flag)
            co_flags ^= flag
            if not co_flags:
                break
    else:
        flags.intersection_update(flags)
    return flags


class SourceModule(ModuleType):
    def __fspath__(self):
        return self.__file__


@dataclass
class Interface:
    """a configuration python importing interface"""

    name: str = None
    path: str = None
    lazy: bool = False
    extensions: tuple = field(default_factory=[".ipy", ".ipynb"].copy)
    include_fuzzy_finder: bool = True
    include_markdown_docstring: bool = True
    include_non_defs: bool = True
    include_await: bool = True
    module_type: ModuleType = field(default=SourceModule)
    no_magic: bool = False

    _loader_hook_position: int = field(default=0, repr=False)

    def __new__(cls, name=None, path=None, **kwargs):
        kwargs.update(name=name, path=path)
        self = super().__new__(cls)
        self.__init__(**kwargs)
        return self


class Loader(Interface, SourceFileLoader):
    """The simplest implementation of a Notebook Source File Loader.
    This class breaks down the loading process into finer steps.
    """

    extensions: tuple = field(default_factory=[".py"].copy)

    @property
    def loader(self):
        """Generate a new loader based on the state of an existing loader."""
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
        """Generate a new finder based on the state of an existing loader"""
        return self.include_fuzzy_finder and FuzzyFinder or FileFinder

    def raw_to_source(self, source):
        """Transform a string from a raw file to python source."""
        if self.path and self.path.endswith(".ipynb"):
            # when we encounter notebooks we apply different transformers to the diff cell types
            return LineCacheNotebookDecoder(
                code=self.code,
                raw=self.raw,
                markdown=self.markdown,
            ).decode(source, self.path)

        # for a normal file we just apply the code transformer.
        return self.code(source)

    def source_to_nodes(self, source, path="<unknown>", *, _optimize=-1):
        """Parse source string as python ast"""
        flags = ast.PyCF_ONLY_AST
        return bootstrap._call_with_frames_removed(
            compile,
            source,
            path,
            "exec",
            flags=flags,
            dont_inherit=True,
            optimize=_optimize,
        )

    def nodes_to_code(self, nodes, path="<unknown>", *, _optimize=-1):
        """Compile ast nodes to python code object"""
        flags = ALLOW_TOP_LEVEL_AWAIT
        return bootstrap._call_with_frames_removed(
            compile,
            nodes,
            path,
            "exec",
            flags=flags,
            dont_inherit=True,
            optimize=_optimize,
        )

    def source_to_code(self, source, path="<unknown>", *, _optimize=-1):
        """Tangle python source to compiled code by:
        1. parsing the source as ast nodes
        2. compiling the ast nodes as python code
        """
        nodes = self.source_to_nodes(source, path, _optimize=_optimize)
        return self.nodes_to_code(nodes, path, _optimize=_optimize)

    def get_data(self, path):
        """get_data injects an input transformation before the raw text.

        this method allows notebook json to be transformed line for line into vertically sparse python code.
        """
        return self.raw_to_source(decode_source(super().get_data(self.path)))

    def create_module(self, spec):
        """An overloaded create_module method injecting fuzzy finder setup up logic."""
        module = self.module_type(str(spec.name))
        _init_module_attrs(spec, module)
        if self.name:
            module.__name__ = self.name

        if module.__file__.endswith((".ipynb", ".ipy")):
            module.get_ipython = get_ipython

        if getattr(spec, "alias", None):
            # put a fuzzy spec on the modules to avoid re importing it.
            # there is a funky trick you do with the fuzzy finder where you
            # load multiple versions with different finders.

            sys.modules[spec.alias] = module

        return module

    def exec_module(self, module):
        """Execute the module."""
        # importlib uses module.__name__, but when running modules as __main__ name will change.
        # this approach uses the original name on the spec.
        try:
            code = self.get_code(module.__spec__.name)

            # from importlib
            if code is None:
                raise ImportError(
                    f"cannot load module {module.__name__!r} when " "get_code() returns None",
                )

            if inspect.CO_COROUTINE not in _get_co_flags_set(code.co_flags):
                # if there isn't any async non sense then we proceed with convention.
                bootstrap._call_with_frames_removed(exec, code, module.__dict__)
            else:
                self.aexec_module_sync(module)

        except BaseException as e:
            alias = getattr(module.__spec__, "alias", None)
            if alias:
                sys.modules.pop(alias, None)

            raise e

    def aexec_module_sync(self, module):
        if "anyio" in sys.modules:
            __import__("anyio").run(self.aexec_module, module)
        else:
            from asyncio import get_event_loop

            get_event_loop().run_until_complete(self.aexec_module(module))

    async def aexec_module(self, module):
        """An async exec_module method permitting top-level await."""
        # there is so redudancy in this approach, but it starts getting asynchier.
        nodes = self.source_to_nodes(self.get_data(self.path))

        # iterate through the nodes and compile individual statements
        for node in nodes.body:
            co = bootstrap._call_with_frames_removed(
                compile,
                ast.Module([node], []),
                module.__file__,
                "exec",
                flags=ALLOW_TOP_LEVEL_AWAIT,
            )
            if inspect.CO_COROUTINE in _get_co_flags_set(co.co_flags):
                # when something async is encountered we compile it with the single flag
                # this lets us use eval to retreive our coroutine.
                co = bootstrap._call_with_frames_removed(
                    compile,
                    ast.Interactive([node]),
                    module.__file__,
                    "single",
                    flags=ALLOW_TOP_LEVEL_AWAIT,
                )
                await bootstrap._call_with_frames_removed(
                    eval,
                    co,
                    module.__dict__,
                    module.__dict__,
                )
            else:
                bootstrap._call_with_frames_removed(exec, co, module.__dict__, module.__dict__)

    def code(self, str):
        return dedent(str)

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
        with cls() as loader:
            spec = find_spec(module)
            module = spec.loader.create_module(spec)
            if main:
                sys.modules["__main__"] = module
                module.__name__ = "__main__"
            spec.loader.exec_module(module)
            return module

    @classmethod
    def load_argv(cls, argv=None, *, parser=None):
        """Load a module based on python arguments

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

        parsed_args = parser.parse_args(argv)
        module = cls.load_ns(parsed_args)
        if module is None:
            return parser.print_help()

        return module

    @classmethod
    def load_ns(cls, ns):
        """Load a module from a namespace, used when loading module from sys.argv parameters."""
        if ns.tasks:
            # i don't quite why we need to do this here, but we do. so don't move it
            from doit.cmd_base import ModuleTaskLoader
            from doit.doit_cmd import DoitMain

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
            return None
        if ns.tasks:
            DoitMain(ModuleTaskLoader(result)).run(ns.args or ["help"])
        return result

    @classmethod
    def load_code(cls, code, argv=None, mod_name=None, script_name=None, main=False):
        """Load a module from raw source code"""
        from runpy import _run_module_code

        self = cls()
        name = main and "__main__" or mod_name or "<raw code>"

        return _dict_module(
            _run_module_code(self.raw_to_source(code), mod_name=name, script_name=script_name),
        )

    @staticmethod
    def get_argparser(parser=None):
        from argparse import REMAINDER, ArgumentParser

        from importnb import __version__

        if parser is None:
            parser = ArgumentParser("importnb", description="run notebooks as python code")
        parser.add_argument("file", nargs="?", help="run a file")
        parser.add_argument("args", nargs=REMAINDER, help="arguments to pass to script")
        parser.add_argument("-m", "--module", help="run a module")
        parser.add_argument("-c", "--code", help="run raw code")
        parser.add_argument("-d", "--dir", help="path to run script in")
        parser.add_argument("-t", "--tasks", action="store_true", help="run doit tasks")
        parser.add_argument(
            "--version", action="version", version=__version__, help="display the importnb version"
        )
        return parser


def comment(str):
    return textwrap.indent(str, "# ")


class DefsOnly(ast.NodeTransformer):
    INCLUDE = ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef

    def visit_Module(self, node):
        args = ([x for x in node.body if isinstance(x, self.INCLUDE)],)
        if VERSION >= (3, 8):
            args += (node.type_ignores,)
        return ast.Module(*args)


class Notebook(Loader):
    """Notebook is a user friendly file finder and module loader for notebook source code.

    > Remember, restart and run all or it didn't happen.

    Notebook provides several useful options.

    * Lazy module loading.  A module is executed the first time it is used in a script.
    """

    def markdown(self, str):
        return quote(str)

    def raw(self, str):
        return comment(str)

    def visit(self, nodes):
        if self.include_non_defs:
            return nodes
        return DefsOnly().visit(nodes)

    def code(self, str):
        if self.no_magic:
            if MAGIC.match(str):
                return comment(str)
        return super().code(str)

    def source_to_nodes(self, source, path="<unknown>", *, _optimize=-1):
        nodes = super().source_to_nodes(source, path)
        if self.include_markdown_docstring:
            nodes = update_docstring(nodes)
        nodes = self.visit(nodes)
        return ast.fix_missing_locations(nodes)

    def raw_to_source(self, source):
        """Transform a string from a raw file to python source."""
        if self.path and self.path.endswith(".ipynb"):
            # when we encounter notebooks we apply different transformers to the diff cell types
            return LineCacheNotebookDecoder(
                code=self.code,
                raw=self.raw,
                markdown=self.markdown,
            ).decode(source, self.path)

        # for a normal file we just apply the code transformer.
        return self.code(source)


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
