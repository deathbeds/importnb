from __future__ import annotations

import inspect
from functools import partial
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import pytest

from importnb.loader import Interface
from importnb.loaders import DataStreamLoader, Toml, Yaml

HAS_YAML = find_spec("ruamel")
HAS_TOML = find_spec("tomllib") or find_spec("tomli")


if TYPE_CHECKING:
    T = TypeVar("T")

    class TFixtureRequest(pytest.FixtureRequest, Generic[T]):
        param: T


UTF8: Any = {"encoding": "utf-8"}
HERE = Path(__file__).parent
ROOT = HERE.parent
README = ROOT / "README.md"
PXT = ROOT / "pixi.toml"
PPT = ROOT / "pyproject.toml"
CI = ROOT / ".github/workflows/test.yml"
RTD = ROOT / ".readthedocs.yml"

INTERFACE_FIELDS = Interface.__dataclass_fields__
FIELD_DEFAULTS = {"extensions": """(".ipy", ".ipynb")""", "module_type": "SourceModule"}

TEST_EPOCHS = [
    "test-max",
    "test-prev",
    "test-min",
    "test-min-noipy",
    "test-pypy",
]

SKIP = partial(pytest.skip, "not running in the repo, or missing optional parser")

TDict = dict[str, Any]


@pytest.fixture
def the_readme() -> str | None:
    if not README.exists():
        return pytest.skip("not running in the importnb repo")
    return README.read_text(**UTF8)


def _import_or_skip(path: Path, has_dep: Any, loader: type[DataStreamLoader]) -> TDict | None:
    return dict(loader().load_file(path).data) if path.exists() and has_dep else SKIP()


@pytest.fixture
def the_pixi() -> TDict | None:
    return _import_or_skip(PXT, HAS_TOML, Toml)


@pytest.fixture
def the_pyproject() -> TDict | None:
    return _import_or_skip(PPT, HAS_TOML, Toml)


@pytest.fixture
def the_ci() -> TDict | None:
    return _import_or_skip(CI, HAS_YAML, Yaml)


@pytest.fixture
def the_rtd() -> TDict | None:
    (HAS_YAML and RTD.exists()) or SKIP()
    return dict(Yaml().load_file(RTD).data)


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
    spec = Interface.__annotations__[an_interface_param].strip()
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
        doc = doc[2:].strip()
        break
    assert doc, f"Interface.{an_interface_param} has no docstring"
    default = FIELD_DEFAULTS.get(an_interface_param, field.default)
    from_src = f"- `{an_interface_param}:{spec}={default}` {doc}"
    print(from_src)
    assert in_readme == from_src


def assert_deps_match(label: str, pxt_feat: dict[str, Any], ppt_deps: list[str]) -> None:
    ppt_deps = {line.split(";")[0].replace(" ", "") for line in ppt_deps}
    pxt_deps = {f"{dep}{spec}" for dep, spec in pxt_feat["dependencies"].items()}
    assert ppt_deps == pxt_deps, f"{label} dependencies don't match"


def test_deps(the_pyproject: TDict, the_pixi: TDict) -> None:
    pyproj = the_pyproject["project"]
    optional = pyproj["optional-dependencies"]
    feats = the_pixi["feature"]
    assert_deps_match(
        "run", feats["deps-run"], [f"python{pyproj['requires-python']}", *pyproj["dependencies"]]
    )
    assert_deps_match("interactive", feats["deps-run-interactive"], optional["interactive"])


def test_pixi_versions(the_ci: TDict, the_pixi: TDict, the_rtd: TDict) -> None:
    pxt_version = the_pixi["workspace"]["requires-pixi"].replace(">=", "")
    gha_version = the_ci["env"]["INB_PIXI_VERSION"]
    assert gha_version == pxt_version
    assert any(f"pixi=={gha_version}" in line for line in the_rtd["build"]["commands"])
