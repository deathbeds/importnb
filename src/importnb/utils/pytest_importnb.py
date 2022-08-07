# coding: utf-8
"""A `pytest` plugin for importing notebooks as modules and using standard test discovered.

The `AlternativeModule` is reusable.  See `pidgin` for an example.
"""

import abc
import functools
import importlib
from pathlib import Path

import _pytest
import pytest

from importnb import Notebook


def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption("--main", action="store_true", help="Run in the main context.")


class AlternativeModule(pytest.Module):
    def _getobj(self):
        return self.loader(
            getattr(self.parent.config.option, "main", None) and "__main__" or self.path
        ).load(str(self.path))


class NotebookModule(AlternativeModule):
    loader = Notebook


class AlternativeSourceText(abc.ABCMeta):
    def __call__(self, parent, path):
        for module in self.modules:
            if "".join(Path(str(path)).suffixes) in module.loader.extensions:
                if not parent.session.isinitpath(path):
                    for pat in parent.config.getini("python_files"):
                        if path.fnmatch(pat.rstrip(".py") + path.ext):
                            break
                    else:
                        return
                if hasattr(module, "from_parent"):
                    return module.from_parent(parent, path=Path(path))
                return module(path, parent)


class NotebookTests(metaclass=AlternativeSourceText):
    modules = (NotebookModule,)


pytest_collect_file = NotebookTests.__call__
