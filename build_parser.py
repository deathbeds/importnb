from __future__ import annotations

from functools import partial
from io import StringIO
from pathlib import Path
from typing import Any

from lark.tools.standalone import (  # type: ignore[attr-defined]
    build_lalr,
    gen_standalone,
    lalr_argparser,
)

HERE = Path(__file__).parent
GRAMMAR = HERE / "src/importnb/json.g"


def get_lark() -> Any:
    ns = lalr_argparser.parse_args(["--propagate_positions", f"{GRAMMAR}"])
    return build_lalr(ns)[0]  # type: ignore[no-untyped-call]


def get_standalone() -> str:
    lark = get_lark()
    python = StringIO()
    gen_standalone(lark, partial(print, file=python))  # type: ignore[no-untyped-call]
    return python.getvalue()


if __name__ == "__main__":
    print(get_standalone())
