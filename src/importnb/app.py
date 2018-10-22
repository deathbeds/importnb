# coding: utf-8
from IPython import paths, get_ipython
from IPython.core import profiledir
from pathlib import Path
import json, ast
import os


def get_config(profile="default"):
    profile_dir = profiledir.ProfileDir()
    try:
        profile = profile_dir.find_profile_dir_by_name(paths.get_ipython_dir(), profile)
    except profiledir.ProfileDirError:
        os.makedirs(paths.get_ipython_dir(), exist_ok=True)
        profile = profile_dir.create_profile_dir_by_name(paths.get_ipython_dir(), profile)
    return Path(profile.location, "ipython_config.json")


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


import sys

import argparse


def install(projects, uninstall=None):
    config, location = load_config()
    uninstall = (uninstall or list()) + projects

    _uninstall(projects)

    with location.open("w") as file:
        json.dump(config, file)

    print("""<3 {}""".format(" ".join(projects)))


def installed(project):
    config, location = load_config()
    return project in config.get("InteractiveShellApp", {}).get("extensions", [])


def _uninstall(projects):
    config, location = load_config()
    projects = sys.argv[1:] or [project]
    config["InteractiveShellApp"]["extensions"] = [
        ext for ext in config["InteractiveShellApp"]["extensions"] if ext not in projects
    ]

    with location.open("w") as file:
        json.dump(config, file)


def uninstaller(projects):
    _uninstall(projects)
    print("""</3 {}.""".format("".join(projects)))


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()
installer = subparsers.add_parser("install")
installer.add_argument("projects", nargs="*", default=["importnb"])
installer.add_argument("--uninstall", nargs="*", default=[])
installer.set_defaults(callable=install)
uninstaller = subparsers.add_parser("uninstall")
uninstaller.add_argument("projects", nargs="*", default=["importnb"])
uninstaller.set_defaults(callable=_uninstall)


def main():
    ns = vars(parser.parse_args())
    return ns.pop("callable")(**ns)


if __name__ == "__main__":
    from importnb.utils.export import export

    export("app.ipynb", "../app.py")
