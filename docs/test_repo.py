from __future__ import annotations

import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import pytest

from importnb.loader import Interface

if TYPE_CHECKING:
    T = TypeVar("T")

    class TFixtureRequest(pytest.FixtureRequest, Generic[T]):
        param: T


UTF8: Any = {"encoding": "utf-8"}
HERE = Path(__file__).parent
ROOT = HERE.parent
README = ROOT / "README.md"

INTERFACE_FIELDS = Interface.__dataclass_fields__


@pytest.fixture
def the_readme() -> str | None:
    if not README.exists():
        return pytest.skip("not running in the importnb repo")
    return README.read_text(**UTF8)


@pytest.fixture(params=[f for f in INTERFACE_FIELDS if not f.startswith("_")])
def an_interface_param(request: TFixtureRequest[str]) -> str:
    return request.param


@pytest.fixture
def the_loader_source() -> list[str]:
    return inspect.getsource(Interface).splitlines()


def test_readme_params(
    the_readme: str, an_interface_param: str, the_loader_source: list[str]
) -> None:
    field = INTERFACE_FIELDS[an_interface_param]
    spec = Interface.__annotations__[an_interface_param]
    doc = ""
    in_readme = ""
    for line in the_readme.splitlines():
        if line.strip().startswith(f"- `{an_interface_param}:"):
            in_readme = line
            break
    assert in_readme, f"Interface.{an_interface_param} is not in README"
    print(in_readme)
    for i, line in enumerate(the_loader_source):
        if not line.strip().startswith(f"{an_interface_param}: "):
            continue
        doc = the_loader_source[i - 1].strip()
        assert doc.startswith("#: "), (
            f"`Interface.{an_interface_param}` should have a `#:` above it"
        )
        doc = doc[3:]
        break
    assert doc, f"Interface.{an_interface_param} has no docstring"
    from_src = f"- `{an_interface_param}:{spec}={field.default}` {doc}"
    print(from_src)
    assert in_readme == from_src
