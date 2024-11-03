# `importnb` imports notebooks as python modules.

if you're here, then there is a chance you have a notebook (`.ipynb`) in a directory saved as `Untitled.ipynb`. it is just sitting there, but what if it could be used as a python module? `importnb` is here to answer that question.


## basic example
use `importnb`'s  `Notebook` finder and loader to import notebooks as modules

```python
import importnb

# with the explicit API

with importnb.Notebook():
    import Untitled

# with the extensible API

with importnb.imports("ipynb"):
    import Untitled
```

### What does this snippet do?

> the snippet begins `with` a context manager that modifies the files python can discover.
> it will find the `Untitled.ipynb` notebook and import it as a module with the `__name__`
> of `Untitled`. the `__file__` description will have `.ipynb` as an extension.

maybe when we give notebooks new life they eventually earn a better name than `Untitled`?

## run a notebook as a script

the `importnb` command line interface mimics python's. it permits running notebook files, modules, and raw `json` data.

the commands below execute a notebook module and file respectively.

```bash
importnb -m Untitled         # call the Untitled module as __main__
importnb Untitled.ipynb      # call the Untitled file as __main__
```

## installing `importnb`

use either `pip` or s`conda/mamba`

```bash
pip install importnb
# or
conda install -c conda-forge importnb
# or
mamba install -c conda-forge importnb
```

## `importnb` features

* `importnb.Notebook` offers parameters to customize how modules are imported
* imports Jupyter notebooks as python modules
  * fuzzy finding conventions for finding files that are not valid python names
* works with top-level await statements
* integration with `pytest`
* extensible machinery and entry points
* translates Jupyter notebook files (i.e. `.ipynb` files) line-for-line to python source providing natural error messages
* command line interface for running notebooks as python scripts
* has no required dependencies

### customizing parameters

the `Notebook` object has a few features that can be toggled:

* `lazy:bool=False` lazy load the module, the namespace is populated when the module is access the first time.
* `position:int=0` the relative position of the import loader in the `sys.path_hooks`
* `fuzzy:bool=True` use fuzzy searching syntax when underscores are encountered.
* `include_markdown_docstring:bool=True` markdown blocks preceding a `class` or `def` become docstrings.
* `include_magic:bool=True` ignore any `IPython` magic syntaxes
* `only_defs:bool=False` import only function and class definitions. ignore intermediate * expressions.
* `no_magic:bool=False` execute `IPython` magic statements from the loader.

these features are defined in the `importnb.loader.Interface` class and they can be controlled through the command line interface.

### importing notebooks

the primary goal of this library is to make it easy to reuse python code in notebooks. below are a few ways to invoke python's import system within the context manager.

```python
import importnb
from importlib import import_module

with importnb.imports("ipynb"):
    import Untitled
    import Untitled as nb
    __import__("Untitled")
    import_module("Untitled")
```

#### import data files

`importnb` can import more than notebooks. `json`-like data from disk can be
loaded and stored on the module with rich representations.

```python
import importnb

with importnb.imports("toml", "json", "yaml"):
    pass
```

all the available entry points are found with:

```python
from importnb.entry_points import list_aliases
list_aliases()
```

#### loading directly from file

```python
from importnb import Notebook

Untitled = Notebook.load("Untitled.ipynb")
```

### fuzzy finding

often notebooks have names that are not valid python files names that are restricted alphanumeric characters and an `_`.  the `importnb` fuzzy finder converts python's import convention into globs that will find modules matching specific patters. consider the statement:

```python
import importnb

with importnb.Notebook():
    import U_titl__d  # U*titl**d.ipynb
```

`importnb` translates `U_titl__d` to a glob format that matches the pattern `U*titl**d.ipynb` when searching for the source. that means that `importnb` should find `Untitled.ipynb` as the source for the import.

```python
import importnb

with importnb.Notebook():
    import _ntitled   # *ntitled.ipynb
    import __d        # **d.ipynb
    import U__        # U**.ipynb
```

a motivation for this feature is naming notebooks as if they were blog posts using the `YYYY-MM-DD-title-here.ipynb` convention. there are a few ways we could this file explicitly. the fuzzy finder syntax means all of the following are equivalent:

```python
import importnb

with importnb.Notebook():
    import __title_here
    import YYYY_MM_DD_title_here
    import __MM_DD_title_here
```

#### fuzzy name ambiguity

it is possible that a fuzzy import may be ambiguous and return multiple files.
the `importnb` fuzzy finder will prefer the **most recently changed** file.

ambiguity can be avoided by using more explicit fuzzy imports to reduce collisions.
another option is to use python's explicit import functions.

```python
from importlib import import_module

import importnb

with importnb.Notebook():
    __import__("YYYY-MM-DD-title-here")
    import_module("YYYY-MM-DD-title-here")
```

#### importing your most recently changed notebook

an outcome of resolving the most recently changed is that you can import your most recent notebook with:

```python
import importnb
with importnb.Notebook():
    import __                        # **.ipynb
```

### integrations

#### `pytest`

since `importnb` transforms notebooks to python documents we can use these as source for tests.
`importnb`s `pytest` extension is not fancy, it only allows for conventional `pytest` test discovery.

`nbval` is alternative testing tools that validates notebook outputs. this style is near to using notebooks as `doctest` while `importnb` primarily adds the ability to write `unittest`s in notebooks. adding tests to notebooks help preserve them over time.

#### extensible

the `importnb.Notebook` machinery is extensible. it allows other file formats to be used. for example, `pidgy` uses `importnb` to import `markdown` files as compiled python code.

```python
import importnb

class MyLoader(importnb.Notebook):
    pass
```

---

## developer

```bash
pixi run release
# or
pixi r release
```

* `importnb` uses [`pixi`][pixi] for testing in python and `IPython`

---

## appendix
### line-for-line translation and natural error messages

a challenge with Jupyter notebooks is that they are `json` data. this poses problems:

1. every valid line of code in a Jupyter notebook is a quoted `json` string
2. `json` parsers don't have a reason to return line numbers.

#### the problem with quoted code

#### line-for-line `json` parser

python's `json` module is not pluggable in the way we need to find line numbers. since `importnb` is meant to be dependency free on installation we couldn't look to any other packages like `ujson` or `json5`.

the need for line numbers is enough that we ship a standalone `json` grammar parser. to do this without extra dependencies we use the `lark` grammar package at build time:

* we've defined a minimal grammar in `json.g`
* we use `hatch` hooks to invoke `lark-standalone` that generates a standalone parser for the grammar.
  * the generated file is shipped with the package.
  * this code is licensed under the Mozilla Public License 2.0

the result of `importnb` is `json` data translated into vertically sparse, valid python code.

#### reproducibility caution with the fuzzy finder

⚠️ fuzzy finding is not reproducible as your system will change over time. in python, "explicit is better than implicit" so defining strong fuzzy strings is best practice if you MUST use esoteric names. an alternative option is to use the `importlib.import_module` machinery

[pixi]: https://pixi.sh
