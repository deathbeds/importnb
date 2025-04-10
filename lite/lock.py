from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

import pkginfo
import pyodide_lock
from jupyterlite_pyodide_kernel.constants import PYODIDE_LOCK, PYODIDE_VERSION

PYODIDE_GH = "https://github.com/pyodide/pyodide"
PYODIDE_CORE_URL = (
    f"{PYODIDE_GH}/releases/download/{PYODIDE_VERSION}/pyodide-core-{PYODIDE_VERSION}.tar.bz2"
)
URL_BASE = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full"
HERE = Path(__file__).parent
LOCK = HERE / f"files/{PYODIDE_LOCK}"
DIST = HERE / "../dist"
CORE_TARBALL = HERE / "../build/pyodide-core.tar.bz2"
WHL = next(DIST.glob("*.whl"))
WHL_SHA = sha256(WHL.read_bytes()).hexdigest()
WHL_INFO = pkginfo.Wheel(str(WHL))


def main() -> int:
    with urlopen(PYODIDE_CORE_URL) as req:
        CORE_TARBALL.write_bytes(req.read())

    with urlopen(f"{URL_BASE}/{PYODIDE_LOCK}") as req:
        lock = json.load(req)
    lock["packages"] = {
        pkg: [info.update(file_name=f"{URL_BASE}/{info['file_name']}"), info][1]
        for pkg, info in lock["packages"].items()
    }
    lock["packages"]["importnb"] = {
        "depends": [],
        "file_name": f"../../pypi/{WHL.name}",
        "imports": ["importnb"],
        "install_dir": "site",
        "name": "importnb",
        "package_type": "package",
        "sha256": WHL_SHA,
        "unvendored_tests": False,
        "version": WHL_INFO.version,
    }
    pyodide_lock.PyodideLockSpec.from_json(LOCK)
    LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
