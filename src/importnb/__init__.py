"""Import jupyter notebooks as python modules and scripts."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

__all__ = "Notebook", "__version__", "imports", "reload"

if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell

_BEAR_ = len(os.environ.get("IMPORTNB_BEARTYPE", ""))

if _BEAR_:
    from beartype import BeartypeConf
    from beartype.claw import beartype_all, beartype_this_package

    beartype_this_package(
        conf=BeartypeConf(
            violation_type=UserWarning,
            claw_skip_package_names=(
                "importnb._json_parser",
                "IPython.core.inputsplitter",
            ),
        )
    )

    if _BEAR_ > 2:
        beartype_all(conf=BeartypeConf(violation_type=UserWarning))


def is_ipython() -> bool:
    from sys import modules

    return "IPython" in modules


def get_ipython(force: bool | None = True) -> InteractiveShell | None:
    shell: InteractiveShell | None = None
    if force or is_ipython():
        try:
            from IPython.core.getipython import get_ipython
        except ModuleNotFoundError:
            return None
        shell = get_ipython()  # type: ignore[no-untyped-call]
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
