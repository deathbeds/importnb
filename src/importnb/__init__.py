"""Import jupyter notebooks as python modules and scripts."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

__all__ = "Notebook", "__version__", "imports", "reload"

if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell


def is_ipython() -> bool:
    return "IPython" in sys.modules


def get_ipython(force: bool | None = True) -> InteractiveShell | None:
    shell: InteractiveShell | None = None
    if force or is_ipython():
        try:
            from IPython.core import getipython
        except ModuleNotFoundError:
            return None
        shell = getipython.get_ipython()  # type: ignore[no-untyped-call]
        if shell is None:
            from IPython.core.interactiveshell import InteractiveShell

            shell = InteractiveShell.instance()

    if TYPE_CHECKING:
        assert isinstance(shell, InteractiveShell)

    return shell


import builtins

from ._version import __version__
from .entry_points import imports
from .loader import Notebook, reload

builtins.true, builtins.false, builtins.null = True, False, None  # type: ignore[attr-defined]
