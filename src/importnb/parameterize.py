# coding: utf-8
from .loader import Notebook
import argparse, ast, inspect
from functools import partial
from copy import deepcopy
from inspect import Signature, Parameter
from pathlib import Path
from functools import partialmethod
from inspect import signature
import sys
from importlib.util import find_spec, module_from_spec, spec_from_loader
from importlib._bootstrap import _installed_safely


class FindReplace(ast.NodeTransformer):
    def __init__(self, globals, parser):
        self.globals = globals
        self.parser = parser
        self.argv = sys.argv[1:]
        self.parameters = []

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target, parameter = node.targets[0].id, node.value
            try:
                parameter = ast.literal_eval(parameter)
            except:
                return node

            if target[0].lower():
                try:
                    self.parser.add_argument(
                        "--%s" % target,
                        default=parameter,
                        help="{} : {} = {}".format(target, type(parameter).__name__, parameter),
                    )
                except argparse.ArgumentError:
                    ...
                self.parameters.append(Parameter(target, Parameter.KEYWORD_ONLY, default=parameter))
                if ("-h" not in self.argv) and ("--help" not in self.argv):
                    ns, self.argv = self.parser.parse_known_args(self.argv)
                    if target in self.globals:
                        node = ast.Expr(ast.Str("Skipped"))
                    elif getattr(ns, target) != parameter:
                        node.value = ast.parse(str(getattr(ns, target))).body[0].value
        return node

    @property
    def signature(self):
        return Signature(self.parameters)

    def visit_Module(self, node):
        node.body = list(map(self.visit, node.body))
        self.parser.description = ast.get_docstring(node)
        self.parser.parse_known_args(self.argv)  # run in case there is a help arugment
        return node

    def generic_visit(self, node):
        return node


def copy_(module):
    new = type(module)(module.__name__)
    return new.__dict__.update(**vars(module)) or new


class Parameterize(Notebook):
    __slots__ = Notebook.__slots__ + ("globals",)

    def __init__(
        self,
        fullname=None,
        path=None,
        *,
        _lazy=False,
        _shell=False,
        _fuzzy=True,
        _markdown_docstring=True,
        _position=0,
        globals=None,
        **_globals
    ):
        super().__init__(
            fullname, path, _lazy=_lazy, _fuzzy=_fuzzy, _shell=_shell, _position=_position
        )
        self.globals = globals or {}
        self.globals.update(**_globals)
        self._visitor = FindReplace(self.globals, argparse.ArgumentParser(prog=self.name))

    def exec_module(self, module):
        self._visitor = FindReplace(self.globals, self._visitor.parser)
        module.__dict__.update(**self.globals)
        return super().exec_module(module)

    def visit(self, node):
        return super().visit(self._visitor.visit(node))

    @classmethod
    def load(cls, object, **globals):
        return parameterize(super().load(object), **globals)


"""    with Parameterize(): 
        reload(foo)

    with Parameterize(a=1234123): 
        reload(foo)

    with Parameterize(a="🤘"): 
        reload(foo)
"""

"""    import foo
"""


def parameterize(object, **globals):
    with Parameterize(**globals):
        if isinstance(object, str):
            object = module_from_spec(find_spec(object))

    object.__loader__ = Parameterize(object.__loader__.name, object.__loader__.path, **globals)

    def call(**parameters):
        nonlocal object, globals
        object = copy_(object)
        keywords = {}
        keywords.update(**globals), keywords.update(**parameter)
        with _installed_safely(object):
            Parameterize(object.__name__, object.__file__, **keywords).exec_module(object)
        return object

    object.__loader__.get_code(object.__name__)
    call.__doc__ = object.__doc__ or object.__loader__._visitor.parser.format_help()
    call.__signature__ = object.__loader__._visitor.signature
    return call


"""    f = parameterize('foo', a=20)
"""

if __name__ == "__main__":
    f = Parameterize().load("parameterize.ipynb")
    from importnb.utils.export import export

    export("parameterize.ipynb", "../parameterize.py")
    # m = f.__loader__(a_variable_to_parameterize=10)

"""# Developer
"""

"""    class Main(Parameterize):
        __init__ = partialmethod(Parameterize.__init__, '__main__')
        def exec_module(self, module, **globals):
            globals.update(vars(self.parser.parse_args()))
            super().exec_module(module, **globals)
"""

"""    def main(): Main().from_filename(sys.argv.pop(1))()
"""

"""    if __name__ == '__main__':
        if sys.argv[0] == globals().get('__file__', None):
            main()
        else:
            from importnb.utils.export import export
            export('parameterize.ipynb', '../parameterize.py')
            module = Execute(shell=True).from_filename('parameterize.ipynb')
            __import__('doctest').testmod(module, verbose=2)
"""
