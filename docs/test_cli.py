from pathlib import Path
from subprocess import check_call
from sys import executable, path, version_info

from importnb import Notebook

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
        def wrapper(tmp_path):
            from shlex import split

            path = tmp_path / "tmp"
            with path.open("w") as file:
                check_call([executable] + split(command), stderr=file, stdout=file)
            out = path.read_text()
            match = get_prepared_string(
                f.__doc__.format(UNTITLED=UNTITLED.as_posix(), SLUG=ref.magic_slug)
            )

            if "UserWarning: Attempting to work in a virtualenv." in out:
                out = "".join(out.splitlines(True)[2:])
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
