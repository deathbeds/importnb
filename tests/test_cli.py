from fnmatch import fnmatch
import re
from sys import version_info
from functools import wraps, partial
from io import StringIO
from subprocess import check_call, check_output
from sys import executable, path
import sys

from importnb import Notebook, get_ipython

from pathlib import Path

GTE10 = version_info.major == 3 and version_info.minor >= 10

HERE = Path(__file__).parent

path.insert(0, str(HERE))

UNTITLED = HERE / "Untitled42.ipynb"

ref = Notebook.load_file(UNTITLED)
REF = Path(ref.__file__)


def get_prepared_string(x):
    if GTE10:
        x = x.replace("optional arguments:", "options:")
    return x.replace("\r", "")


def cli_test(command):
    def delay(f):
        def wrapper(tmp_path, pytester):
            from shlex import split

            path = tmp_path / "tmp"
            with path.open("w") as file:
                check_call([executable] + split(command), stderr=file, stdout=file)
            out = path.read_text()
            match = get_prepared_string(
                f.__doc__.format(UNTITLED=UNTITLED.as_posix(), SLUG=ref.magic_slug)
            )
            assert out == match

        return wrapper

    return delay


@cli_test("-m importnb")
def test_usage():
    """\
usage: importnb [-h] [-f] [-m] [-c] [-d DIR] ...

run notebooks as python code

positional arguments:
  args               the file [default], module or code to execute

optional arguments:
  -h, --help         show this help message and exit
  -f, --file         load a file
  -m, --module       run args as a module
  -c, --code         run args as code
  -d DIR, --dir DIR  the directory path to run in.
"""


@cli_test(rf"-m importnb -d {UNTITLED.parent.as_posix()} -m {UNTITLED.stem}")
def test_file():
    """\
i was printed from {UNTITLED} and my name is __main__
{SLUG}
the parser namespace is Namespace(args=None)
"""


@cli_test(rf"-m importnb -d {UNTITLED.parent.as_posix()} -m {UNTITLED.stem}")
def test_module():
    """\
i was printed from {UNTITLED} and my name is __main__
{SLUG}
the parser namespace is Namespace(args=None)
"""


@cli_test("-m importnb -c '{}'")
def test_empty_code():
    """"""
