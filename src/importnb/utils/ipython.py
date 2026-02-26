from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.core.profiledir import ProfileDir


def get_config(profile: str | None = "default") -> Path:
    from IPython import paths
    from IPython.core import profiledir

    profile_dir = profiledir.ProfileDir()
    find_profile_dir_by_name: Any = profile_dir.find_profile_dir_by_name
    profile_: ProfileDir | None = None

    try:
        profile_ = find_profile_dir_by_name(paths.get_ipython_dir(), profile)
    except profiledir.ProfileDirError:
        os.makedirs(paths.get_ipython_dir(), exist_ok=True)
        profile_ = find_profile_dir_by_name(paths.get_ipython_dir(), profile)

    if profile_ is None:
        raise RuntimeError("IPython profile could not be found or created.")

    return Path(profile_.location, "ipython_config.json")


def get_ipython(force: bool | None = True) -> InteractiveShell | None:
    if force or is_ipython():
        try:
            from IPython.core.interactiveshell import InteractiveShell

            return InteractiveShell.instance()
        except ImportError:
            return None

    return None


def is_ipython() -> bool:
    if "IPython" in sys.modules:
        from IPython.core.interactiveshell import InteractiveShell

        return InteractiveShell._instance is not None
    return False


def load_config() -> tuple[dict[str, Any], Path]:
    location = get_config()
    JSONDecodeError: type[Exception] = getattr(json, "JSONDecodeError", ValueError)
    config = {}
    try:
        with location.open() as file:
            config = json.load(file)
    except FileNotFoundError:
        pass
    except JSONDecodeError:
        pass

    if "InteractiveShellApp" not in config:
        config["InteractiveShellApp"] = {}

    if "extensions" not in config["InteractiveShellApp"]:
        config["InteractiveShellApp"]["extensions"] = []

    return config, location


def install(project: str = "importnb") -> None:
    """Install the importnb extension"""
    config, location = load_config()
    projects = [project]
    if not installed(project):
        config["InteractiveShellApp"]["extensions"].extend(projects)

    with location.open("w", encoding="utf-8") as file:
        json.dump(config, file)

    print(f"""✅ {projects}""")


def installed(project: str) -> bool:
    config = load_config()[0]
    return project in config.get("InteractiveShellApp", {}).get("extensions", [])


def uninstall(project: str = "importnb") -> None:
    """Uninstall the importnb extension"""
    config, location = load_config()
    projects = [project]
    config["InteractiveShellApp"]["extensions"] = [
        ext for ext in config["InteractiveShellApp"]["extensions"] if ext not in projects
    ]

    with location.open("w", encoding="utf-8") as file:
        json.dump(config, file)

    print(f"""❌ {projects}.""")
