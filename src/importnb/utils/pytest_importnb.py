# coding: utf-8
"""A `pytest` plugin for importing notebooks as modules and using standard test discovered.

The `AlternativeModule` is reusable.  See `pidgin` for an example.
"""

with __import__("importnb").Notebook():
    try:
        from . import testing
    except:
        from importnb.utils import testing

import importlib, pytest, abc, pathlib

from importnb import Notebook


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption("--main", action="store_true", help="Run in the main context.")


class AlternativeModule(pytest.Module):
    def _getobj(self):
        return self.loader(self.parent.config.option.main and "__main__" or None).load(
            str(self.fspath)
        )


class NotebookModule(AlternativeModule):
    loader = Notebook


import _pytest.doctest


class AlternativeSourceText(abc.ABCMeta):
    def __call__(self, parent, path):
        for module in self.modules:
            if "".join(pathlib.Path(str(path)).suffixes) in module.loader.extensions:
                if not parent.session.isinitpath(path):
                    for pat in parent.config.getini("python_files"):
                        if path.fnmatch(pat.rstrip(".py") + path.ext):
                            break
                    else:
                        return
                if self.parent.config.option.doctestmodules:
                    classes = list(module.__mro__)
                    classes.insert(
                        classes.index(_pytest.python.Module), _pytest.doctest.DoctestModule
                    )
                    module = type("DocTest" + module.__name__, tuple(classes), {})
                return module(path, parent)


class NotebookTests(metaclass=AlternativeSourceText):
    modules = (NotebookModule,)


pytest_collect_file = NotebookTests.__call__

if __name__ == "__main__":
    from importnb.utils.export import export

    export("pytest_importnb.ipynb", "../../utils/pytest_importnb.py")
