from logging import shutdown
from pathlib import Path
import os
import shlex
from subprocess import call
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class LarkStandAloneBuildHook(BuildHookInterface):
    PLUGIN_NAME = "lark_standalone"

    def initialize(self, version, build_data):
        L = get_logger()
        WIN = os.name == "nt"
        L.info("converting json grammar to python")
        python_parser = Path("src/importnb/_json_parser.py")
        if not python_parser.exists():
            with python_parser.open("w") as file:
                call(
                    shlex.split(
                        "python -m lark.tools.standalone --propagate_positions src/nb.g",
                        posix=~WIN,
                    ),
                    stdout=file,
                    shell=WIN,
                )


def get_logger():
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    return logger
