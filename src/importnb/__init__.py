"""Import jupyter notebooks as python modules and scripts."""
__all__ = "Notebook", "reload", "imports", "__version__"


def is_ipython():
    from sys import modules

    return "IPython" in modules


def get_ipython(force=True):
    if force or is_ipython():
        try:
            from IPython import get_ipython
        except ModuleNotFoundError:
            return None
        shell = get_ipython()
        if shell is None:
            from IPython import InteractiveShell

            shell = InteractiveShell.instance()
        return shell
    return None


from ._version import __version__
from .entry_points import imports
from .loader import Notebook, reload
from .entry_points import imports
