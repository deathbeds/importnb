"""A `pytest` plugin for importing notebooks as modules and using standard test discovered.

The `AlternativeModule` is reusable.  See `pidgin` for an example.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from importnb import Notebook

if TYPE_CHECKING:
    from collections.abc import Generator
    from types import ModuleType

    from importnb.loader import Loader


def get_file_patterns(
    cls: type[AlternativeModule], parent: pytest.Collector
) -> Generator[str, None, None]:
    for pat in parent.config.getini("python_files"):
        for e in cls.loader().extensions:
            yield f"""*{pat.rstrip(".py")}{e}"""


class AlternativeModule(pytest.Module):
    loader: type[Loader]

    def _getobj(self) -> ModuleType:
        return self.loader.load_file(str(self.path), False)

    @classmethod
    def pytest_collect_file(
        cls, parent: pytest.Collector, file_path: Path
    ) -> pytest.Collector | None:
        if not parent.session.isinitpath(file_path):
            for pat in get_file_patterns(cls, parent):
                if fnmatch(str(file_path), pat):
                    break
            else:
                return None

        if hasattr(cls, "from_parent"):
            return cls.from_parent(parent=parent, path=Path(file_path))
        return cls(file_path, parent)


class NotebookModule(AlternativeModule):
    loader = Notebook


pytest_collect_file = NotebookModule.pytest_collect_file
