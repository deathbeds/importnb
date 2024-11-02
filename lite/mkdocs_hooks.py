import shutil
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig  # type: ignore[import-not-found]
from mkdocs.structure.files import Files  # type: ignore[import-not-found]

LITE = Path(__file__).parent.parent / "build/lite"


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Copy the schema to the site."""
    lite_paths = sorted([p for p in LITE.rglob("*") if not p.is_dir()])
    print(f"\t     - [lite] copying {len(lite_paths)} files")
    for src in lite_paths:
        dest = Path(config.site_dir) / f"lite/{src.relative_to(LITE).as_posix()}"
        if dest.exists():
            dest.unlink()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return files
