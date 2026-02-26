from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from coverage.plugin import CoveragePlugin, FileReporter, FileTracer

from importnb.decoder import LineCacheNotebookDecoder
from importnb.loader import Notebook

if TYPE_CHECKING:
    from collections.abc import Iterable

    from coverage.plugin_support import Plugins

START_CODE_C, START_SOURCE, NEWLINE, CLOSE_SOURCE, CLOSE_CODE_C = (
    r'^   "cell_type": "code",$',
    r'^   "source": \[$',
    r'^    "\\n",?',
    r"^   \]$",
    r"^  \},?$",
)


def coverage_init(reg: Plugins, options: Any) -> None:
    plugin = NotebookPlugin()
    reg.add_file_tracer(plugin)


class NotebookPlugin(CoveragePlugin):
    def file_tracer(self, filename: str) -> NotebookTracer | None:
        return NotebookTracer(filename) if Path(filename).name.endswith(".ipynb") else None

    def file_reporter(self, filename: str) -> NotebookReporter:
        return NotebookReporter(filename)

    def find_executable_files(self, src_dir: str) -> Iterable[str]:
        return map(str, Path(src_dir).glob("*.ipynb"))


class NotebookTracer(FileTracer):
    _filename: str

    def __init__(self, filename: str) -> None:
        self._filename = filename

    def source_filename(self) -> str:
        return self._filename


class NotebookReporter(FileReporter):
    def source(self) -> str:
        nb = Notebook(lazy=True)
        dec = LineCacheNotebookDecoder(code=nb.code, raw=nb.raw, markdown=nb.markdown)
        return dec.decode(super().source(), self.filename)

    def lines(self) -> set[int]:
        in_comment = False
        lines = []

        for i, line in enumerate(self.source().splitlines(), 1):
            if not line.strip():
                continue
            if in_comment and line == "'''":
                in_comment = False
                continue
            if line.startswith("'''"):
                in_comment = True
            elif in_comment:
                continue
            else:
                lines += [i]

        return set(lines)
