from __future__ import annotations
import sys
from functools import partial
from io import StringIO
import re
from pathlib import Path
import subprocess
from typing import Any
from hashlib import sha256
import shutil

from lark.tools.standalone import (  # type: ignore[attr-defined]
    build_lalr,
    gen_standalone,
    lalr_argparser,
)

UTF8 = {"encoding": "utf-8"}
HERE = Path(__file__).parent
GRAMMAR = HERE / "src/importnb/json.g"
PARSER = HERE / "src/importnb/_json_parser.py"
HEADER_STEM = f"# importnb sha256="
G_HASH = sha256(GRAMMAR.read_bytes()).hexdigest()
HEADER = HEADER_STEM + G_HASH
RE_HEADER = rf"^{HEADER_STEM}(.*)"
RUFF = shutil.which("ruff")

def get_lark() -> Any:
    ns = lalr_argparser.parse_args(["--propagate_positions", f"{GRAMMAR}"])
    return build_lalr(ns)[0]  # type: ignore[no-untyped-call]


def get_standalone() -> str:
    lark = get_lark()
    python = StringIO()
    gen_standalone(lark, partial(print, file=python))  # type: ignore[no-untyped-call]
    return python.getvalue()

def main() -> int:
    if "--update" in sys.argv and PARSER.exists():
        parser_text = PARSER.read_text(encoding="utf-8")
        match = re.findall(RE_HEADER, parser_text)
        sys.stderr.write(f"""... grammar: {G_HASH}\n... parser: {match}\n""")
        if match and match[0] == G_HASH:
            sys.stderr.write("... no change\n")
            return 0

    raw = get_standalone()
    sys.stderr.write(f"... writing {PARSER}\n")
    PARSER.write_text("\n".join([HEADER, raw]), **UTF8)
    if RUFF:
        sys.stderr.write(f"... formatting with {RUFF}\n")
        return subprocess.call([*map(str, [RUFF, "format", PARSER])])
    return 0

if __name__ == "__main__":
    sys.exit(main())
