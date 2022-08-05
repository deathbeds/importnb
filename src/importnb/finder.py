# coding: utf-8
"""# `sys.path_hook` modifiers

Many suggestions for importing notebooks use `sys.meta_paths`, but `importnb` relies on the `sys.path_hooks` to load any notebook in the path. `PathHooksContext` is a base class for the `importnb.Notebook` `SourceFileLoader`.
"""

import inspect
from itertools import chain
import re
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path

from importlib._bootstrap_external import FileFinder


class FileModuleSpec(ModuleSpec):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_fileattr = True


class FuzzySpec(FileModuleSpec):
    def __init__(
        self, name, loader, *, alias=None, origin=None, loader_state=None, is_package=None
    ):
        super().__init__(
            name,
            loader,
            origin=origin,
            loader_state=loader_state,
            is_package=is_package,
        )
        self.alias = alias


FUZZ = re.compile("_{1,}")


def _fuzzy_query_logic(m):
    return "?*"[len(m.group()) >= 2]


def _fuzzy_query(str):
    return re.sub(FUZZ, _fuzzy_query_logic, str)


class FuzzyFinder(FileFinder):
    """Adds the ability to open file names with special characters using underscores."""

    def __class_getitem__(cls, object):
        return type(cls.__name__, (cls,), dict(_extensions=object))

    def find_candidate_files(self, path, name):
        return filter(Path.is_file, Path(path).glob(_fuzzy_query(name)))

    def find_spec(self, fullname, target=None):
        """Try to finder the spec and if it cannot be found, use the underscore starring syntax
        to identify potential matches.
        """
        # look for the spec matching the exact file name
        spec = super().find_spec(fullname, target=target)

        if spec is None:
            # otherwise we follow some heuristics to find other possible matches.
            original = fullname

            original, fullname = "." in fullname and fullname.rsplit(".", 1) or ("", original)
            files = chain.from_iterable(
                self.find_candidate_files(self.path, fullname + x) for x in self._extensions
            )
            sort = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
            if sort:
                file = Path(sort[0])
                spec = super().find_spec(
                    (original + "." + file.stem.split(".", 1)[0]).lstrip("."),
                    target=target,
                )
                fullname = (original + "." + fullname).lstrip(".")
                if spec and fullname != spec.name:
                    spec = FuzzySpec(
                        spec.name,
                        spec.loader,
                        origin=spec.origin,
                        loader_state=spec.loader_state,
                        alias=fullname,
                        is_package=bool(spec.submodule_search_locations),
                    )
        return spec


def get_loader_details():
    for id, path_hook in enumerate(sys.path_hooks):
        try:
            return (
                id,
                list(inspect.getclosurevars(path_hook).nonlocals["loader_details"]),
            )
        except:
            continue
