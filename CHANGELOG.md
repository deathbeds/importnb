# changelog

## unreleased

- the minimum supported version of python is now 3.9
- CLI arguments to a notebook that conflict with `importnb`, such as `-m` and
  `-h` can be provided after a `--` token

  ```bash
  importnb -m MyNotebook -- -h
  ```

- discovering tests in `.ipynb` files under `pytest` requires enabling the
  plugin:

  ```bash
  pytest -p=importnb.utils.pytest_importnb
  ```
- imported notebooks can be instrumented with a `coverage` plugin: this must be
  enabled in a `coverage` configuration file, such as `pyproject.toml`:

  ```toml
  [tool.coverage.run]
  plugins = ["importnb.utils.coverage"]
  ```
