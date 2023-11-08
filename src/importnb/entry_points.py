import sys
from contextlib import ExitStack, contextmanager

# See compatibility note on `group`
# https://docs.python.org/3/library/importlib.metadata.html#entry-points
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


__all__ = ("imports",)
ENTRY_POINTS = dict()


def get_importnb_entry_points():
    """Discover the known importnb entry points"""
    global ENTRY_POINTS
    for ep in entry_points(group="importnb"):
        ENTRY_POINTS[ep.name] = ep.value
    return ENTRY_POINTS


def loader_from_alias(alias):
    """Load an attribute from a module using the entry points value specificaiton"""
    from importlib import import_module
    from operator import attrgetter

    module, _, member = alias.rpartition(":")
    module = import_module(module)
    return attrgetter(member)(module)


def loader_from_ep(alias):
    """Discover a loader for an importnb alias or vaue"""
    if ":" in alias:
        return loader_from_alias(alias)

    if not ENTRY_POINTS:
        get_importnb_entry_points()

    if alias in ENTRY_POINTS:
        return loader_from_alias(ENTRY_POINTS[alias])

    raise ValueError(f"{alias} is not a valid loader alias.")


@contextmanager
def imports(*names):
    """A shortcut to importnb loaders through entrypoints"""
    types = set()
    with ExitStack() as stack:
        for name in names:
            t = loader_from_ep(name)
            if t not in types:
                stack.enter_context(t())
                types.add(t)
        yield stack


def list_aliases():
    """List the entry points associated with importnb"""
    if not ENTRY_POINTS:
        get_importnb_entry_points()
    return list(ENTRY_POINTS)
