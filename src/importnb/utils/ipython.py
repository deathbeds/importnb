# coding: utf-8
import ast
import json
import os
import sys
from pathlib import Path

from IPython import get_ipython, paths
from IPython.core import profiledir


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


def install(project="importnb"):
    """install the importnb extension"""
    config, location = load_config()
    projects = [project]
    if not installed(project):
        config["InteractiveShellApp"]["extensions"].extend(projects)

    with location.open("w") as file:
        json.dump(config, file)

    print("""✅ {}""".format(projects))


def installed(project):
    config, location = load_config()
    return project in config.get("InteractiveShellApp", {}).get("extensions", [])


def uninstall(project="importnb"):
    """uninstall the importnb extension"""
    config, location = load_config()
    projects = [project]
    config["InteractiveShellApp"]["extensions"] = [
        ext for ext in config["InteractiveShellApp"]["extensions"] if ext not in projects
    ]

    with location.open("w") as file:
        json.dump(config, file)
    print("""❌ {}.""".format(projects))
