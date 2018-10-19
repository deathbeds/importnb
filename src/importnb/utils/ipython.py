# coding: utf-8
from IPython import paths, get_ipython
from IPython.core.profiledir import ProfileDir, ProfileDirError

from pathlib import Path
import json, ast


def load_create_profile(profile="default"):
    try:
        dir = paths.locate_profile(profile)
    except ProfileDirError:
        ip.profile_dir.create_profile_dir_by_name(paths.get_ipython_dir(), profile)
    return paths.locate_profile(profile)


def get_config(profile="default"):
    ip = get_ipython()
    load_create_profile()
    config = (
        Path(ip.profile_dir.location if ip else paths.locate_profile(profile))
        / "ipython_config.json"
    )
    if not config.exists():
        config.write_text("{}")
    return config


def load_config():
    location = get_config()
    try:
        with location.open() as file:
            config = json.load(file)
    except (FileNotFoundError, getattr(json, "JSONDecodeError", ValueError)):
        config = {}

    if "InteractiveShellApp" not in config:
        config["InteractiveShellApp"] = {}

    if "extensions" not in config["InteractiveShellApp"]:
        config["InteractiveShellApp"]["extensions"] = []

    return config, location


def install(project="importnb"):
    config, location = load_config()

    if not installed(project):
        config["InteractiveShellApp"]["extensions"].append(project)

    with location.open("w") as file:
        json.dump(config, file)

    print("""<3 {}""".format(project))


def installed(project):
    config, location = load_config()
    return project in config.get("InteractiveShellApp", {}).get("extensions", [])


def uninstall(project="importnb"):
    config, location = load_config()

    config["InteractiveShellApp"]["extensions"] = [
        ext for ext in config["InteractiveShellApp"]["extensions"] if ext != project
    ]

    with location.open("w") as file:
        json.dump(config, file)
    print("""</3 {}.""".format(project))


if __name__ == "__main__":
    from importnb.utils.export import export

    export("ipython.ipynb", "../../utils/ipython.py")
