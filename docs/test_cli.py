from __future__ import annotations

import platform
import re
import sys
import textwrap
from difflib import unified_diff
from pathlib import Path
from shlex import split
from subprocess import STDOUT, call
from typing import Any, Callable

import pytest
from pytest import importorskip

from importnb import Notebook
from importnb import __version__ as importnb_version

HERE = Path(__file__).parent

sys.path.insert(0, str(HERE))

UNTITLED = HERE / "Untitled42.ipynb"
UTF8: Any = {"encoding": "utf-8"}

IS_PYPY = platform.python_implementation() == "PyPy"
IS_WIN = platform.system() == "Windows"

NORMALIZE_PATTERNS = [
    [
        f"""python{".".join(map(str, sys.version_info[:2]))} -m""",
        "",
    ],
    [
        r"UserWarning: Attempting to work in a virtualenv\.",
        "",
    ],
    [
        r"untitled42-parser-[a-f\d\-]+",
        r"untitled42-parser-1-2-3-a-f",
    ],
    [
        r"optional arguments:",
        r"options:",
    ],
    [
        # -c, --code CODE run raw code
        r"(-[a-z]), (--[a-z+]+) ([A-Z]+)",
        # -c CODE, --code CODE run raw code
        r"\1 \3, \2 \3",
    ],
    [r"([A-Z]+)\n\s+", r"\1 "],
    [r"\]\n\s+", r"] "],
    [
        r" +",
        " ",
    ],
    [r"^\s+", ""],
]


def normalize(name: str, raw: str) -> str:
    norm = raw

    for pattern, replacement in NORMALIZE_PATTERNS:
        norm = re.sub(pattern, replacement, norm, flags=re.MULTILINE)

    print("\n##", name, "(raw)\n")
    print(textwrap.indent(raw, "\t"))
    print("\n##", name, "(normalized)\n")
    print(textwrap.indent(norm, "\t"))
    return norm.strip()


@pytest.fixture
def untitled_context() -> dict[str, str]:
    ref = Notebook.load_file(UNTITLED)
    return dict(
        UNTITLED=UNTITLED.as_posix(),
        SLUG=ref.MAGIC_SLUG,
        VERSION=importnb_version,
    )


def cli_test(command: str, expect_rc: int = 0) -> Callable[..., Callable[..., None]]:
    def delay(f: Callable[..., None]) -> Callable[..., None]:
        def wrapper(tmp_path: Path, untitled_context: dict[str, str]) -> None:
            if IS_WIN and IS_PYPY:
                pytest.skip(
                    "subprocesses fail to clean up on win/pypy: "
                    "OSError: [WinError 6] The handle is invalid"
                )
            path = tmp_path / "tmp"
            args = [sys.executable, *split(command)]
            print(">>>", " \\\n\t".join(args))
            with path.open("w", **UTF8) as fp:
                rc = call(args, stdout=fp, stderr=STDOUT, cwd=str(tmp_path))
            assert rc == expect_rc, f"didn't get expected return code {expect_rc}"

            raw_expected = f"{f.__doc__}".format(**untitled_context)
            norm_expected = normalize("expected", raw_expected)

            raw_observed = path.read_text(**UTF8)
            norm_observed = normalize("observed", raw_observed)

            diff = [
                line.rstrip()
                for line in unified_diff(
                    norm_expected.splitlines(),
                    norm_observed.splitlines(),
                    "expected (normalized)",
                    "observed (normalized)",
                )
            ]

            if not diff:
                return
            real_diff = [
                line
                for line in diff
                if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
            ]
            diff_count = len(real_diff)
            print("\n## unexpected diff\n", file=sys.stderr)
            print(textwrap.indent("\n".join(diff), "\t"), file=sys.stderr)
            assert not real_diff[-1], f"{diff_count} unexpected difference(s) in {f.__name__}"

        return wrapper

    return delay


@cli_test("-m importnb")
def test_usage() -> None:
    """usage: importnb [-h] [-m MODULE] [-c CODE] [-d DIR] [-t] [--version] [file] ...

    run notebooks as python code

    positional arguments:
      file                  run a file
      args                  arguments to pass to script

    optional arguments:
      -h, --help            show this help message and exit
      -m MODULE, --module MODULE
                            run a module
      -c CODE, --code CODE  run raw code
      -d DIR, --dir DIR     path to run script in
      -t, --tasks           run doit tasks
      --version             display the importnb version
    """


@cli_test(rf"-m importnb -d {UNTITLED.parent.as_posix()} {UNTITLED.as_posix()}")
def test_file() -> None:
    """\
i was printed from {UNTITLED} and my name is __main__
{SLUG}
the parser namespace is Namespace(args=None)
"""


@cli_test(rf"-m importnb -d {UNTITLED.parent.as_posix()} -m {UNTITLED.stem}")
def test_module() -> None:
    """\
i was printed from {UNTITLED} and my name is __main__
{SLUG}
the parser namespace is Namespace(args=None)
"""


@cli_test(rf"-m importnb -d {UNTITLED.parent.as_posix()} -m {UNTITLED.stem} -- --help")
def test_module_extra_argv() -> None:
    """\
i was printed from {UNTITLED} and my name is __main__
{SLUG}
usage: Untitled42 [-h] [-- ...]

optional arguments:
    -h, --help  show this help message and exit
    -- ...
"""


@cli_test("-m importnb -c '{}'")
def test_empty_code() -> None:
    """"""


@cli_test("-m importnb --version")
def test_version() -> None:
    """{VERSION}"""


@cli_test(rf"-m importnb -d {UNTITLED.parent.as_posix()} -t {UNTITLED.as_posix()} list")
def test_doit() -> None:
    """\
i was printed from {UNTITLED} and my name is __main__
{SLUG}
echo   this the docstring for the `echo` task that echos hello.
"""
    importorskip("doit")
