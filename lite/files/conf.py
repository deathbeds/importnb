# see ``pyproject.toml`` for declarative configuration
with open("pyproject.toml", "rb") as ppt:
    globals().update(__import__("tomllib").load(ppt)["tool"]["sphinx"])
