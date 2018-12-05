# coding: utf-8
"""Utility functions to test the quality of a source notebook.
"""

import json, pathlib


class UnexecutedCell(BaseException):
    ...


class OutOfOrder(BaseException):
    ...


class MissingMarkdownDocstring(BaseException):
    ...


def assert_execution_order(nb, file=None):
    shift = 1
    for id, object in enumerate(object for object in nb["cells"] if object["cell_type"] == "code"):
        id += shift
        source = "".join(object["source"])
        if object["execution_count"] is None:
            if source.strip():
                raise UnexecutedCell(f"""{file} has an unexecuted with the source:\n{source}.""")
            shift -= 1
        else:
            if object["execution_count"] != id:
                raise OutOfOrder(f"""{file} has been executed out of order.""")

    return True


def assert_markdown_docstring(nb, name=None):
    if nb["cells"][0]["cell_type"] != "markdown":
        raise MissingMarkdownDocstring(f"""{name} is a missing a Markdown doc cell.""")
    return True


if __name__ == "__main__":
    from importnb.utils.export import export

    export("testing.ipynb", "../../utils/testing.py")


def test_assert_monotonic_execution_order():
    __file__ = globals().get("__file__", "testing.ipynb")
    nb = json.loads(pathlib.Path(__file__).read_text())
    assert assert_execution_order(nb, __file__)
    assert assert_markdown_docstring(nb, __file__)
