from json import dumps
from pathlib import Path
from hypothesis_jsonschema import from_schema
from hypothesis import given
from pytest import mark, raises
from importnb.decoder import InvalidNotebook, parse_nbformat

HERE = Path(__file__).parent


@mark.parametrize("file", [HERE / "test_in_notebook.ipynb"])
def test_parse_notebook(file):
    parse_nbformat(file.read_text())


@mark.parametrize("file", [HERE / "ascript.ipy"])
def test_parse_notebook_fail(file):
    with raises(InvalidNotebook):
        parse_nbformat(file.read_text())


@given(from_schema(dict(dict(type=["object", "string"]))))
def test_random_objects_fail(object):
    with raises(InvalidNotebook):
        return parse_nbformat(dumps(object))


@given(
    from_schema(
        dict(
            properties=dict(
                cells=dict(
                    type="array",
                    items=dict(dict(type=["object", "string"])),
                ),
                additionalProperties=False,
            )
        )
    )
)
def test_random_cells_fail(object):
    with raises(InvalidNotebook):
        return parse_nbformat(dumps(object))
