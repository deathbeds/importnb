from __future__ import annotations

import sys

from . import Notebook


def main(argv: list[str] | None = None) -> int:
    """A convenience function for running importnb as an application"""
    Notebook.load_argv(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
