from functools import partial
from io import StringIO
from logging import shutdown
from pathlib import Path
import os
import shlex
from subprocess import call
import sys
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class LarkStandAloneBuildHook(BuildHookInterface):
    PLUGIN_NAME = "lark_standalone"

    def initialize(self, version, build_data):
        L = get_logger()
        WIN = os.name == "nt"
        L.info("converting json grammar to python")
        python_parser = Path("src/importnb/_json_parser.py")
        if not python_parser.exists():
            py = get_standalone()
            python_parser.write_text(py)
        build_data["artifacts"].append(
            "/src/importnb/_json_parser.py"
        )  # its really important to remember the preceeding /


def get_logger():
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    return logger


def get_lark():
    from lark.tools.standalone import lalr_argparser, build_lalr

    return build_lalr(lalr_argparser.parse_args(["--propagate_positions", "src/json.g"]))[0]


def write(buffer, *lines):
    buffer.writelines(map(str, lines or ["\n"]))


def get_standalone():
    from lark.tools.standalone import gen_standalone

    lark = get_lark()
    python = StringIO()
    gen_standalone(lark, partial(print, file=python))
    return python.getvalue()
