# contributing

thank you for considering contributing to `importnb`.

## building

`importnb` can be built with a PEP 517 front end, such as [`build`](https://pypi.org/project/build):

```bash
pyproject-build .
```

## testing

in a folder with `pyproject.toml` and `docs`, such as a `git` checkout or unpacked
source distribution:

```bash
pytest
```

## project

`importnb` uses [`pixi`][pixi] to `fix`, `lint`, `test`, `build`, build `docs`,
and `check` that it is ready to `release`. run all of them:

```bash
pixi run release
```

## interactive

the `dev` environment, a superset of all the other environments, is available
with extras tools for interactive development.

```bash
pixi run serve-lab
```

## continuous integration

`importnb` uses:

* GitHub Actions, as defined in `.github/workflows`
* ReadTheDocs, as defined in `.readthedocs.yml`

[pixi]: https://pixi.sh
