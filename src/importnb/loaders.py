from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from .loader import Loader, SourceModule

if TYPE_CHECKING:
    from types import ModuleType


class DataLoaderGetter(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...


class DataModule(SourceModule):
    data: dict[str, Any]

    def _repr_json_(self) -> tuple[dict[str, Any], dict[str, Any]]:
        return self.data, dict(root=repr(self), expanded=False)


@dataclass
class DataStreamLoader(Loader):
    """an import loader for data streams"""

    module_type: type[DataModule] = field(default=DataModule)

    def exec_module(self, module: ModuleType) -> None:
        if TYPE_CHECKING:
            assert isinstance(module, DataModule)
            assert module.__file__

        with open(module.__file__, "rb") as file:
            module.data = self.get_data_loader()(file)

    def get_data_loader(self) -> DataLoaderGetter:
        raise NotImplementedError("load_data not implemented.")


@dataclass
class Json(DataStreamLoader):
    """an import loader for ``.json`` files."""

    extensions: tuple[str, ...] = field(default_factory=lambda: (".json",))

    def get_data_loader(self) -> DataLoaderGetter:
        from json import load

        return load


@dataclass
class Yaml(DataStreamLoader):
    """an import loader for ``.yml`` and ``.yaml`` files."""

    extensions: tuple[str, ...] = field(default_factory=lambda: (".yml", ".yaml"))

    def get_data_loader(self) -> DataLoaderGetter:
        try:
            from ruamel.yaml import YAML

            yaml = YAML(typ="safe", pure=True)
            return yaml.load
        except ModuleNotFoundError:
            from yaml import safe_load as safe_load_pyyaml

            return safe_load_pyyaml


@dataclass
class Toml(DataStreamLoader):
    """an import loader for ``.toml`` files."""

    extensions: tuple[str, ...] = field(default_factory=lambda: (".toml",))

    def get_data_loader(self) -> DataLoaderGetter:
        try:
            from tomllib import load

            return load  # type: ignore[no-any-return]
        except ModuleNotFoundError:
            from tomli import load as load_tomli

            return load_tomli
