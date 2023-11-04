from pathlib import Path
from subprocess import check_call
from sys import executable, path, version_info

from pytest import importorskip

from importnb import Notebook
from importnb import __version__ as importnb_version

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
        def wrapper(tmp_path: Path):
            from shlex import split

            path = tmp_path / "tmp"
            with path.open("w") as file:
                check_call(
                    [executable] + split(command), stderr=file, stdout=file, cwd=str(tmp_path)
                )
            out = path.read_text()
            match = get_prepared_string(
                f.__doc__.format(
                    UNTITLED=UNTITLED.as_posix(), SLUG=ref.magic_slug, VERSION=importnb_version
                )
            )

            if "UserWarning: Attempting to work in a virtualenv." in out:
                out = "".join(out.splitlines(True)[2:])
            assert out == match

        return wrapper

    return delay


@cli_test("-m importnb")
def test_usage():
    """\
usage: importnb [-h] [-m MODULE] [-c CODE] [-d DIR] [-t] [--version]
                [file] ...

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


@cli_test("-m importnb --version")
def test_version():
    """\
{VERSION}
"""


@cli_test(rf"-m importnb -d {UNTITLED.parent.as_posix()} -t {UNTITLED.as_posix()} list")
def test_doit():
    """\
i was printed from {UNTITLED} and my name is __main__
{SLUG}
echo   this the docstring for the `echo` task that echos hello.
"""
    importorskip("doit")
