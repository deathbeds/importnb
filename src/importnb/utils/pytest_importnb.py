"""A `pytest` plugin for importing notebooks as modules and using standard test discovered.

The `AlternativeModule` is reusable.  See `pidgin` for an example.
"""

from pathlib import Path

import pytest

from importnb import Notebook


def get_file_patterns(cls, parent):
    for pat in parent.config.getini("python_files"):
        for e in cls.loader().extensions:
            yield "*" + pat.rstrip(".py") + e


class AlternativeModule(pytest.Module):
    def _getobj(self):
        return self.loader.load_file(str(self.path), False)

    @classmethod
    def pytest_collect_file(cls, parent, path):
        if not parent.session.isinitpath(path):
            for pat in get_file_patterns(cls, parent):
                if path.fnmatch(pat):
                    break
            else:
                return None

        if hasattr(cls, "from_parent"):
            return cls.from_parent(parent, path=Path(path))
        return cls(path, parent)


class NotebookModule(AlternativeModule):
    loader = Notebook


pytest_collect_file = NotebookModule.pytest_collect_file
