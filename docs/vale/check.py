from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__)
DOCS = HERE.parent.parent
ROOT = DOCS.parent
SITE = ROOT / "site"
SRC = ROOT / "src"

VALE_ARGS: list[str | Path] = [
    "vale",
    SITE / "index.html",
    SITE / "contributing/index.html",
    *sorted(p for p in SRC.rglob("*.py")),
    "--output=JSON",
]

TValeResults = dict[str, list[dict[str, Any]]]


def report(raw: TValeResults) -> list[str]:
    """Filter and report vale findings."""
    raw = {k: v for k, v in raw.items() if "ipynb_checkpoints" not in k}
    if not raw:
        return []
    lines: list[str] = []
    widths = [
        ":" + ("-" * (1 + max(len(r) for r in raw))),
        (5 * "-") + ":",
        (7 * "-") + ":",
        ":" + ("-" * (1 + max(len(line["Match"]) for line in sum(raw.values(), [])))),
    ]

    def line(*c: str) -> str:
        return "|".join([
            "",
            *[
                f" {c[i]} ".ljust(len(w)) if w.startswith(":") else f" {c[i]} ".rjust(len(w))
                for i, w in enumerate(widths)
            ],
            "",
        ])

    lines += [
        line("file", "line", "column", "message"),
        "|".join(["", *widths, ""]),
    ]

    for path, findings in raw.items():
        for found in findings:
            lines += [line(path, found["Line"], found["Span"][0], found["Match"])]

    print("\n".join(lines))
    return lines


def main() -> int:
    str_args = [a if isinstance(a, str) else f"{a.relative_to(ROOT)}" for a in VALE_ARGS]
    print(">>>", " \\\n\t".join(str_args), flush=True)
    proc = subprocess.Popen(
        str_args, encoding="utf-8", cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out = proc.communicate()[0]
    raw: TValeResults = json.loads(out)
    if raw:
        return proc.returncode or len(report(raw))
    return 0


if __name__ == "__main__":
    sys.exit(main())
