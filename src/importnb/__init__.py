# coding: utf-8

__all__ = "Notebook", "reload"


def is_ipython():
    from sys import modules

    return "IPython" in modules


def get_ipython(force=True):
    if force or is_ipython():
        try:
            from IPython import get_ipython
        except ModuleNotFoundError:
            return
        shell = get_ipython()
        if shell is None:
            from IPython import InteractiveShell

            shell = InteractiveShell.instance()
        return shell
    return None


import builtins

from ._version import *
from .loader import Notebook, reload

builtins.true, builtins.false, builtins.null = True, False, None
