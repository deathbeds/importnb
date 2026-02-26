# contributing

thank you for considering contributing to `importnb`.

## building

`importnb` can be built with a PEP 517 front end, such as [`build`](https://pypi.org/project/build):

```bash
pyproject-build .
```

### grammar

a [`lark`](https://pypi.org/project/lark) grammar gives `importnb` line numbers
from json. rebuild the grammar with `lark` installed:

```py
python build_parser.py
```

note that a key section of the generated code is [_not_ reproducible][lark-584],
so the hash of the grammar file gets injected as a header comment.

both the grammar (`json.g`) and generated grammar (`_json_parser.py`, `mpl-2.0`
license) are checked into the repository.

[lark-584]: https://github.com/lark-parser/lark/issues/584

## testing

in a folder with `pyproject.toml` and `docs`, such as a `git` checkout or unpacked
source distribution:

```bash
pytest
```

## project

`importnb` uses [`pixi`][pixi] to `fix`, `lint`, `test`, `build`, build a `lite` demo,
build `docs`, `a`cceptance `test` the demo, and `check` that it is ready to release.

see all of the tasks with:

```bash
pixi task list
```

run `all` of them with:

```bash
pixi run all
```

or _really_ run all of them, including tests of the oldest supported environment
and the firefox-based browser tests:

```bash
pixi run all-epochs
```

## interactive

the `dev` environment, a superset of most other environments, is available
with extras tools for interactive development.

```bash
pixi run dev-lab          # start jupyterlab
pixi run dev-nb           # start notebook
pixi run docs-serve       # serve mkdocs with live reload
pixi run docs-lite-serve  # serve the jupyterlite demo
```

to use another editor in the `dev` environment with an editable install of `importnb`:

```bash
pixi run dev-pip
pixi run --environment dev path-to-your-editor .
```

## continuous integration

`importnb` uses:

- GitHub Actions, defined in `.github/workflows`
- ReadTheDocs, defined in `.readthedocs.yml`

[pixi]: https://pixi.sh
