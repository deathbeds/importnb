def task_build():
    return dict(
        actions=["hatch build"],
        file_dep=["pyproject.toml", "src/nb.g"],
        targets=["src/importnb/_json_parser.py", "src/importnb/_version.py"],
        clean=True,
    )
