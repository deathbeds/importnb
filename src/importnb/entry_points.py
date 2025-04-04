from __future__ import annotations

import sys
from contextlib import ExitStack, contextmanager
from typing import TYPE_CHECKING, Any

__all__ = ("imports",)

# See compatibility note on `group`
# https://docs.python.org/3/library/importlib.metadata.html#entry-points
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

from .loader import Loader  # noqa: TC001

if TYPE_CHECKING:
    from collections.abc import Generator

ENTRY_POINTS: dict[str, type[Loader] | str] = {}


def get_importnb_entry_points() -> dict[str, type[Loader] | str]:
    """Discover the known importnb entry points"""
    for ep in entry_points(group="importnb"):
        ENTRY_POINTS[ep.name] = ep.value
    return ENTRY_POINTS


def loader_from_alias(alias: str) -> type[Loader]:
    """Load an attribute from a module using the entry points value specification"""
    from importlib import import_module
    from operator import attrgetter

    module, _, member = alias.rpartition(":")
    module = import_module(module)
    loader: type[Loader] = attrgetter(member)(module)
    return loader


def loader_from_ep(alias: str) -> type[Loader]:
    """Discover a loader for an importnb alias or value"""
    if ":" in alias:
        return loader_from_alias(alias)

    if not ENTRY_POINTS:
        get_importnb_entry_points()

    aliased = ENTRY_POINTS.get(alias)

    if isinstance(aliased, str):
        return loader_from_alias(aliased)

    raise ValueError(f"{alias} is not a valid loader alias.")


@contextmanager
def imports(*names: str) -> Generator[Any, None, None]:
    """A shortcut to importnb loaders through entry points"""
    types = set()
    with ExitStack() as stack:
        for name in names:
            t = loader_from_ep(name)
            if t not in types:
                stack.enter_context(t())
                types.add(t)
        yield stack


def list_aliases() -> list[str]:
    """List the entry points associated with importnb"""
    if not ENTRY_POINTS:
        get_importnb_entry_points()
    return list(ENTRY_POINTS)
