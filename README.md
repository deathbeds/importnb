# `importnb` imports notebooks as python modules.

if you're here, then there is a chance you have a notebook (`.ipynb`) in a directory saved as `Untitled.ipynb`. it is just sitting there, but what if it could be used as a python module? `importnb` is here to answer that question.


## basic example 
use `importnb`'s  `Notebook` finder and loader to import notebooks as modules

    from importnb import Notebook
    with Notebook():
        import Untitled

### What does this snippet do?

> the snippet begins `with` a context manager that modifies the files python can discover.
it will find  the `Untitled.ipynb` notebook and import it as a module with `__name__` `Untitled`. 
the `__file__` description will have `.ipynb` as an extension. 

maybe when we give notebooks new life they eventually earn a better name than `Untitled`?

## run a notebook as a script

the `importnb` command line interface mimics python's. it permits running notebooks files, modules, and raw json data. 

the commands below execute a notebook module and file respectively.

    importnb -m Untitled         # call the Untitled module as __main__
    importnb Untitled.ipynb      # call the Untitled file as __main__

## installing `importnb`

use either `pip` or `conda/mamba` 

    pip install importnb
    conda install -cconda-forge importnb
    mamba install -cconda-forge importnb



## `importnb` features

* `importnb.Notebook` offers parameters to customize how modules are imported
* imports Jupyter notebooks as python modules
  * fuzzy finding conventions for finding files that are not valid python names
* integration with `pytest`
* extensible machinery
* translates Jupyter notebook files (ie `.ipynb` files) line-for-line to python source providing natural error messages
* command line interface for running notebooks as python scripts
* has no required dependencies

### customizing parameters

the `Notebook` object has a few features that can be toggled:

* `lazy:bool=False` lazy load the module, the namespace is populated when the module is access the first time.
* `position:int=0` the relative position of the import loader in the `sys.path_hooks`
* `fuzzy:bool=True` use fuzzy searching syntax when underscores are encountered.
* `include_markdown_docstring:bool=True` markdown blocks preceding function/class defs become docstrings.
* `include_magic:bool=True` ignore any ipython magic syntaxes
* `only_defs:bool=False` import only function and class definitions. ignore intermediate * expressions.
* `no_magic:bool=False` execute `IPython` magic statements from the loader.

these features are defined in the `importnb.loader.Interface` class and they can be controlled throught the command line interface.

### importing notebooks

the primary goal of this library is to make it easy to reuse python code in notebooks. below are a few ways to invoke python's import system within the context manager.

    with importnb.Notebook():
        import Untitled100
        import Untitled100 as nb
        __import__("Untitled100")
        from importlib import import_module
        import_module("Untitled100")

#### loading directly from file 

    Untitled100 = Notebook.load("Untitled100.ipynb")


### fuzzy finding

often notebooks have names that are not valid python files names that are restricted alphanumeric characters and an `_`.  the `importnb` fuzzy finder converts python's import convention into globs that will find modules matching specific patters. consider the statement:

    with importnb.Notebook():
        import U_titl__100                        # U*titl**100.ipynb

`importnb` translates `U_titl__100` to a glob format that matches the pattern `U*titl**.ipynb` when searching for the source. that means that `importnb` should fine `Untitled100.ipynb` as the source for the import[^unless].

    with importnb.Notebook():
        import _ntitled100                        # *ntitled100.ipynb
        import __100                        # **100.ipynb
        import U__100                        # U**100.ipynb

a primary motivation for this feature is name notebooks as if they were blog posts using the `YYYY-MM-DD-title-here.ipynb` convention. there are a few ways we could this file explicitly. the fuzzy finder syntax could like any of the following:

    with importnb.Notebook():
        import __title_here
        import YYYY_MM_DD_title_here
        import __MM_DD_title_here

#### fuzzy name ambiguity

it is possible that a fuzzy import may be ambiguous are return multiple files.
the `importnb` fuzzy finder will prefer the most recently changed file.

ambiguity can be avoided by using more explicit fuzzy imports that will reduce collisions.
another option is use python's explicit import functions.


    with importnb.Notebook():
        __import__("YYYY-MM-DD-title-here")
        import_module("YYYY-MM-DD-title-here")


#### importing your most recently changed notebook

an outcome of resolving the most recently changed is that you can import your most recent notebook with:

        import __                        # **.ipynb


    
---


[pip]: #
[conda]: #
[mamba]: #
[pidgy]: #