from argparse import ArgumentParser
from pathlib import Path
import runpy
from shlex import split
import sys


PARSER = ArgumentParser(
    prog="importnb", usage="a command line interface for executing notebooks as scripts."
)
COMMANDS = PARSER.add_subparsers(dest="f")
COMMANDS.add_parser(
    "install",
    help="install the importnb extension",
)
COMMANDS.add_parser("uninstall", help="uninstall the importnb extension")
RUN = COMMANDS.add_parser("run", help="run files and modules as scripts")
RUN.add_argument("file", nargs="*")
RUN.add_argument("-m", "--module", nargs="*")


def run(ns):
    from importnb import Notebook

    sys.path.insert(0, str(Path().absolute()))
    with Parameterize():
        for file in ns.file:
            Parameterize.load(file)

        for module in ns.module or []:
            runpy.run_module(module)


def main(argv=None):
    from .utils.ipython import install, uninstall

    argv = argv or sys.argv[1:]
    if isinstance(argv, str):
        argv = split(argv)

    ns = PARSER.parse_args(argv)

    if ns.f == "run":
        return run(ns)

    return dict(install=install, uninstall=uninstall)[ns.f]()


from .parameterize import Parameterize

file = sys.argv[1] if len(sys.argv) > 1 else None

if file == __file__:
    main()
