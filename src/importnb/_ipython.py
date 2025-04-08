from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell


def is_ipython() -> bool:
    if "IPython" in sys.modules:
        from IPython.core.interactiveshell import InteractiveShell

        return InteractiveShell._instance is not None
    return False


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
