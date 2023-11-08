from functools import partial
from io import StringIO
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class LarkStandAloneBuildHook(BuildHookInterface):
    PLUGIN_NAME = "lark_standalone"

    def initialize(self, version, build_data):
        L = get_logger()
        L.info("converting json grammar to python")
        python_parser = Path(self.root, "src/importnb/_json_parser.py")
        if not python_parser.exists():
            py = get_standalone()
            python_parser.write_text(py)
        # its really important to remember the preceeding /
        build_data["artifacts"].extend(
            [
                "/src/importnb/_json_parser.py",
                "/src/importnb/json.g",
            ]
        )


def get_logger():
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    return logger


def get_lark():
    from lark.tools.standalone import build_lalr, lalr_argparser

    return build_lalr(lalr_argparser.parse_args(["--propagate_positions", "src/importnb/json.g"]))[
        0
    ]


def write(buffer, *lines):
    buffer.writelines(map(str, lines or ["\n"]))


def get_standalone():
    from lark.tools.standalone import gen_standalone

    lark = get_lark()
    python = StringIO()
    gen_standalone(lark, partial(print, file=python))
    return python.getvalue()
