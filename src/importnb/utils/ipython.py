from IPython import paths, get_ipython

from pathlib import Path
import json


def get_config():
    ip = get_ipython()
    return Path(ip.profile_dir.location if ip else paths.locate_profile()) / "ipython_config.json"


def load_config():
    location = get_config()
    with open(location) as file:
        try:
            config = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

    if "InteractiveShellApp" not in config:
        config["InteractiveShellApp"] = {}

    if "extensions" not in config["InteractiveShellApp"]:
        config["InteractiveShellApp"]["extensions"] = []

    return config, location


def load_ipython_extension(ip=None):
    config, location = load_config()

    if "importnb" not in config["InteractiveShellApp"]["extensions"]:
        config["InteractiveShellApp"]["extensions"].append("importnb")

    with open(location, "w") as file:
        json.dump(config, file)


def unload_ipython_extension(ip=None):
    config, location = load_config()

    config["InteractiveShellApp"]["extensions"] = [
        ext for ext in config["InteractiveShellApp"]["extensions"] if ext != "importnb"
    ]

    with open(location, "w") as file:
        json.dump(config, file)


if __name__ == "__main__":
    try:
        from .compiler_python import ScriptExporter
    except:
        from importnb.compiler_python import ScriptExporter
    from pathlib import Path

    Path("../../importnb/utils/ipython.py").write_text(
        ScriptExporter().from_filename("ipython.ipynb")[0]
    )
