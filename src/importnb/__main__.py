from pathlib import Path
from shlex import split
import sys


def make_parser():
    from argparse import ArgumentParser

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
    return PARSER


def main(argv=None):
    """a convenience function for running importnb as an application"""
    from .utils.ipython import install, uninstall

    argv = argv or sys.argv[1:]

    if isinstance(argv, str):
        argv = split(argv)

    PARSER = make_parser()
    if not argv:
        # show help when no arguments are supplied
        return PARSER.print_help()
    if argv[0] not in {"install", "uninstall", "run"}:
        # if no command is supplied then we default to the run command
        argv.insert(0, "run")

    ns = PARSER.parse_args(argv)

    ns.f = ns.f or "run"

    if ns.f == "run":
        # execute the run command
        from .loader import Notebook

        Notebook.load_argv(argv[1:])
        return

    # dispatch the ipython extension installations
    return dict(install=install, uninstall=uninstall)[ns.f]()


if __name__ == "__main__":
    main()
