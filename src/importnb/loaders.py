from dataclasses import dataclass, field
from types import ModuleType

from .loader import Loader, SourceModule


class DataModule(SourceModule):
    def _repr_json_(self):
        return self.data, dict(root=repr(self), expanded=False)


@dataclass
class DataStreamLoader(Loader):
    """an import loader for data streams"""

    module_type: ModuleType = field(default=DataModule)

    def exec_module(self, module):
        with open(module.__file__, "rb") as file:
            module.data = self.get_data_loader()(file)
        return module

    def get_data_loader(self):
        raise NotImplementedError("load_data not implemented.")


@dataclass
class Json(DataStreamLoader):
    """an import loader for json files"""

    extensions: tuple = field(default_factory=[".json"].copy)

    def get_data_loader(self):
        from json import load

        return load


@dataclass
class Yaml(DataStreamLoader):
    """an import loader for yml and yaml"""

    extensions: tuple = field(default_factory=[".yml", ".yaml"].copy)

    def get_data_loader(self):
        try:
            from ruamel.yaml import YAML

            yaml = YAML(typ="safe", pure=True)
            safe_load = yaml.load
        except ModuleNotFoundError:
            from yaml import safe_load
        # probably want an error message about how to fix this if we cant find yamls
        return safe_load


@dataclass
class Toml(DataStreamLoader):
    """an import loader for toml"""

    extensions: tuple = field(default_factory=[".toml"].copy)

    def get_data_loader(self):
        try:
            from tomllib import load
        except ModuleNotFoundError:
            from tomli import load
        return load
