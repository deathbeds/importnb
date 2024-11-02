from __future__ import annotations

import logging
from functools import partial
from io import StringIO
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from lark.tools.standalone import (  # type: ignore[attr-defined]
    build_lalr,
    gen_standalone,
    lalr_argparser,
)


class LarkStandAloneBuildHook(BuildHookInterface[Any]):
    PLUGIN_NAME = "lark_standalone"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        L = get_logger()
        L.info("converting json grammar to python")
        python_parser = Path(self.root, "src/importnb/_json_parser.py")
        if not python_parser.exists():
            py = get_standalone()
            python_parser.write_text(py)
        # its really important to remember the preceeding /
        build_data["artifacts"].extend([
            "/src/importnb/_json_parser.py",
            "/src/importnb/json.g",
        ])


def get_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    return logger


def get_lark() -> Any:
    ns = lalr_argparser.parse_args(["--propagate_positions", "src/importnb/json.g"])
    return build_lalr(ns)[0]  # type: ignore[no-untyped-call]


def write(buffer: StringIO, *lines: list[str]) -> None:
    buffer.writelines(map(str, lines or ["\n"]))


def get_standalone() -> str:
    lark = get_lark()
    python = StringIO()
    gen_standalone(lark, partial(print, file=python))  # type: ignore[no-untyped-call]
    return python.getvalue()


if __name__ == "__main__":
    print(get_standalone())
