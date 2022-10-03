# coding: utf-8
"""# `sys.path_hook` modifiers

Many suggestions for importing notebooks use `sys.meta_paths`, but `importnb` relies on the `sys.path_hooks` to load any notebook in the path. `PathHooksContext` is a base class for the `importnb.Notebook` `SourceFileLoader`.
"""

import inspect
import sys
from importlib._bootstrap_external import FileFinder
from importlib.machinery import ModuleSpec
from pathlib import Path


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


def fuzzy_query(str):
    new = ""
    for chr in str:
        new += (not new.endswith("__") or chr != "_") and chr or ""
    return new.replace("__", "*").replace("_", "?")


def fuzzy_file_search(path, fullname):
    results = []
    id, details = get_loader_details()
    for ext in sum((list(object[1]) for object in details), []):
        results.extend(Path(path).glob(fullname + ext))
        "_" in fullname and results.extend(Path(path).glob(fuzzy_query(fullname) + ext))
    return results


class FuzzyFinder(FileFinder):
    """Adds the ability to open file names with special characters using underscores."""

    def find_spec(self, fullname, target=None):
        """Try to finder the spec and if it cannot be found, use the underscore starring syntax
        to identify potential matches.
        """
        spec = super().find_spec(fullname, target=target)
        raw = fullname
        if spec is None:
            original = fullname

            if "." in fullname:
                original, fullname = fullname.rsplit(".", 1)
            else:
                original, fullname = "", original

            if "_" in fullname:
                # find any files using the fuzzy convention
                files = fuzzy_file_search(self.path, fullname)
                if files:
                    # sort and create of a path of the chosen file
                    file = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
                    name = file.stem
                    if original:
                        name = ".".join((original, name))
                    name = (original + "." + file.stem).lstrip(".")
                    spec = super().find_spec(name, target=target)
                    spec = spec and FuzzySpec(
                        spec.name,
                        spec.loader,
                        origin=spec.origin,
                        loader_state=spec.loader_state,
                        alias=raw,
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


def get_loader_index(ext):
    path_id, details = get_loader_details()
    for i, (loader, exts) in enumerate(details):
        if ext in exts:
            return path_id, i, details
