import shutil
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files

ROOT = Path(__file__).parent.parent
LITE = ROOT / "build/lite"
DIST = ROOT / "dist"
CONDA_DIST = DIST / "conda/noarch"


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Copy the schema to the site."""
    site_dir = Path(config.site_dir)
    lite_paths = sorted([p for p in LITE.rglob("*") if not p.is_dir()])
    print(f"\t     - [lite] copying {len(lite_paths)} files")
    for src in lite_paths:
        dest = site_dir / f"lite/{src.relative_to(LITE).as_posix()}"
        if dest.exists():
            dest.unlink()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    for src in [*CONDA_DIST.glob("*.conda"), *CONDA_DIST.glob("*.json")]:
        dest = site_dir / f"conda/{src.relative_to(CONDA_DIST.parent).as_posix()}"
        if dest.exists():
            dest.unlink()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return files
