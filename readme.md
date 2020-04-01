__importnb__ imports notebooks as modules.  Notebooks are reusable as tests, source code, importable modules, and command line utilities.

[![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/deathbeds/importnb/master?urlpath=lab/tree/readme.ipynb)[![Documentation Status](https://readthedocs.org/projects/importnb/badge/?version=latest)](https://importnb.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/deathbeds/importnb.svg?branch=master)](https://travis-ci.org/deathbeds/importnb)[![PyPI version](https://badge.fury.io/py/importnb.svg)](https://badge.fury.io/py/importnb)![PyPI - Python Version](https://img.shields.io/pypi/pyversions/importnb.svg)![PyPI - Format](https://img.shields.io/pypi/format/importnb.svg)![PyPI - Format](https://img.shields.io/pypi/l/importnb.svg)[
![Conda](https://img.shields.io/conda/pn/conda-forge/importnb.svg)](https://anaconda.org/conda-forge/importnb)[
![GitHub tag](https://img.shields.io/github/tag/deathbeds/importnb.svg)](https://github.com/deathbeds/importnb/tree/master/src/importnb) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


##### Installation

    pip install importnb
    
---

    conda install -c conda-forge importnb

---

# `importnb` for testing

After `importnb` is installed, [pytest](https://pytest.readthedocs.io/) will discover and import notebooks as tests.

    pytest index.ipynb

[`importnb`](https://github.com/deathbeds/importnb) imports notebooks as python modules, it does not compare outputs like [`nbval`](https://github.com/computationalmodelling/nbval).  

[`importnb`](https://github.com/deathbeds/importnb) now captures `doctest`s in every __Markdown__ cell & block string expression.  The docstrings are tested with the [__--doctest-modules__ flag](https://doc.pytest.org/en/latest/doctest.html).

    pytest index.ipynb --doctest-modules
    
It is recommended to use `importnb` with [__--nbval__](https://github.com/computationalmodelling/nbval) and the __--monotonic__ flag that checks if has notebook has be restarted and re-run.

    pytest index.ipynb --nbval --monotonic

---

# `importnb` for the commmand line

`importnb` can run notebooks as command line scripts.  Any literal variable in the notebook, may be applied as a parameter from the command line.

    ipython -m importnb -- index.ipynb --foo "A new value"
   

---

# `importnb` for Python and IPython


It is suggested to execute `importnb-install` to make sure that notebooks for each IPython session.

> Restart and run all or it didn't happen.

`importnb` excels in an interactive environment and if a notebook will __Restart and Run All__ then it may reused as python code. The `Notebook` context manager will allow notebooks _with valid names_ to import with Python.


```python
from importnb import Notebook
```

### For brevity


```python
    with __import__('importnb').Notebook(): 
        import readme
```

> [`importnb.loader`](src/notebooks/loader.ipynb) will find notebooks available anywhere along the [`sys.path`](https://docs.python.org/2/library/sys.html#sys.path).

#### or explicity 


```python
    from importnb import Notebook
    with Notebook(): 
        import readme
```


```python
    foo = 42
    with Notebook():
        import readme
    if __name__ == '__main__':
        assert readme.foo == 42
        assert readme.__file__.endswith('.ipynb')
```

[`importnb` readme](readme.ipynb)

### Modules may be reloaded 

The context manager is required to `reload` a module.


```python
    from importlib import reload
    with Notebook(): __name__ == '__main__' and reload(readme)
```

### Lazy imports

The `lazy` option will delay the evaluation of a module until one of its attributes are accessed the first time.


```python
    with Notebook(lazy=True):
        import readme
```

### Fuzzy File Names


```python
    if __name__ == '__main__':
        with Notebook():
            import __a_me
            
        assert __a_me.__file__ == readme.__file__
```

Python does not provide a way to import file names starting with numbers of contains special characters.  `importnb` installs a fuzzy import logic to import files containing these edge cases.

    import __2018__6_01_A_Blog_Post
    
will find the first file matching `*2018*6?01?A?Blog?Post`.  Importing `Untitled314519.ipynb` could be supported with the query below.

    import __314519

### Docstring

The first markdown cell will become the module docstring.


```python
    if __name__ == '__main__':
        print(readme.__doc__.splitlines()[0])
```

    __importnb__ imports notebooks as modules.  Notebooks are reusable as tests, source code, importable modules, and command line utilities.


Meaning non-code blocks can be executeb by [doctest]().


```python
    if __name__ == '__main__':
        __import__('doctest').testmod(readme)
```

# Import notebooks from files

Notebook names may not be valid Python paths.  In this case, use `Notebook.from_filename`.

```python
>>> Notebook.load('changelog.ipynb')
<module 'changelog' from 'changelog.ipynb'>
```
       
Import under the `__main__` context.

```python
>>> Notebook('__main__').load('changelog.ipynb')
<module 'changelog' from 'changelog.ipynb'>
```

# Parameterize Notebooks

Literal ast statements are converted to notebooks parameters.

In `readme`, `foo` is a parameter because it may be evaluated with ast.literal_val


```python
    if __name__ == '__main__':
        from importnb.parameterize import Parameterize
        f = Parameterize.load(readme.__file__)
```

The parameterized module is a callable that evaluates with different literal statements.


```python
    if __name__ == '__main__': 
        assert callable(f)
        f.__signature__

        assert f().foo == 42
        assert f(foo='importnb').foo == 'importnb'
```

# Run Notebooks from the command line

Run any notebook from the command line with importnb.  Any parameterized expressions are available as parameters on the command line.

    

```bash
ipython -m importnb -- index.ipynb --foo "The new value"
```

## Integrations


### IPython

#### [IPython Extension](src/importnb/ipython_extension.py#IPython-Extensions)

Avoid the use of the context manager using loading importnb as IPython extension.

```python
%load_ext importnb
```
    
`%unload_ext importnb` will unload the extension.

#### Default Extension

`importnb` may allow notebooks to import by default with 

```bash
importnb-install
```

> If you'd like to play with source code on binder then you must execute the command above.  Toggle the markdown cell to a code cell and run it.

This extension will install a script into the default IPython profile startup that is called each time an IPython session is created.  

Uninstall the extension with `importnb-uninstall`.

##### Run a notebook as a module

When the default extension is loaded any notebook can be run from the command line. After the `importnb` extension is created notebooks can be execute from the command line.

```bash
ipython -m readme
```
    
In the command line context, `__file__ == sys.argv[0] and __name__ == '__main__'` .
    
> See the [deploy step in the travis build](https://github.com/deathbeds/importnb/blob/docs/.travis.yml#L19).

##### Parameterizable IPython commands

Installing the IPython extension allows notebooks to be computed from the command.  The notebooks are parameterizable from the command line.

```bash
ipython -m readme -- --help
```

### py.test

`importnb` installs a pytest plugin when it is setup.  Any notebook obeying the py.test discovery conventions can be used in to pytest.  _This is great because notebooks are generally your first test._

```bash
ipython -m pytest -- src
```
    
Will find all the test notebooks and configurations as pytest would any Python file.

### Setup

To package notebooks add `recursive-include package_name *.ipynb`

## Developer

* [Python Source](./src/importnb/)
* [Tests](./tests)

### Format and test the Source Code


```python
    if __name__ == '__main__':
        if globals().get('__file__', None) == __import__('sys').argv[0]:
            print(foo, __import__('sys').argv)
        else:
            !ipython -m pytest -- --cov=importnb --flake8 --isort --black tests 
            !jupyter nbconvert --to markdown --stdout index.ipynb > readme.md
```

    [22;0t]0;IPython: deathbeds/importnb[1m========================================== test session starts ==========================================[0m
    platform linux -- Python 3.8.1, pytest-5.3.2, py-1.8.1, pluggy-0.13.1 -- /home/weg/projects/deathbeds/importnb/envs/importnb-dev/bin/python
    cachedir: .pytest_cache
    rootdir: /home/weg/projects/deathbeds/importnb, inifile: tox.ini
    plugins: isort-0.3.1, black-0.3.7, flake8-1.0.4, cov-2.8.1, importnb-0.6.0
    collected 22 items                                                                                      [0m
    
    tests/foobar.py::FLAKE8 [33mSKIPPED[0m[33m                                                                   [  4%][0m
    tests/foobar.py::BLACK [33mSKIPPED[0m[33m                                                                    [  9%][0m
    tests/foobar.py::ISORT [33mSKIPPED[0m[33m                                                                    [ 13%][0m
    tests/test_importnb.ipynb::test_basic [32mPASSED[0m[32m                                                      [ 18%][0m
    tests/test_importnb.ipynb::test_package [32mPASSED[0m[32m                                                    [ 22%][0m
    tests/test_importnb.ipynb::test_reload [32mPASSED[0m[32m                                                     [ 27%][0m
    tests/test_importnb.ipynb::test_docstrings [32mPASSED[0m[32m                                                 [ 31%][0m
    tests/test_importnb.ipynb::test_docstring_opts [32mPASSED[0m[32m                                             [ 36%][0m
    tests/test_importnb.ipynb::test_from_file [32mPASSED[0m[32m                                                  [ 40%][0m
    tests/test_importnb.ipynb::test_lazy [32mPASSED[0m[32m                                                       [ 45%][0m
    tests/test_importnb.ipynb::test_module_source [32mPASSED[0m[32m                                              [ 50%][0m
    tests/test_importnb.ipynb::test_main [32mPASSED[0m[32m                                                       [ 54%][0m
    tests/test_importnb.ipynb::test_object_source [32mPASSED[0m[32m                                              [ 59%][0m
    tests/test_importnb.ipynb::test_python_file [32mPASSED[0m[32m                                                [ 63%][0m
    tests/test_importnb.ipynb::test_cli [32mPASSED[0m[32m                                                        [ 68%][0m
    tests/test_importnb.ipynb::test_parameterize [32mPASSED[0m[32m                                               [ 72%][0m
    tests/test_importnb.ipynb::test_minified_json [32mPASSED[0m[32m                                              [ 77%][0m
    tests/test_importnb.ipynb::test_fuzzy_finder [32mPASSED[0m[32m                                               [ 81%][0m
    tests/test_importnb.ipynb::test_remote [32mPASSED[0m[32m                                                     [ 86%][0m
    tests/foobaz/__init__.py::FLAKE8 [33mSKIPPED[0m[32m                                                          [ 90%][0m
    tests/foobaz/__init__.py::BLACK [33mSKIPPED[0m[32m                                                           [ 95%][0m
    tests/foobaz/__init__.py::ISORT [33mSKIPPED[0m[32m                                                           [100%][0mCoverage.py warning: Module importnb was previously imported, but not measured (module-not-measured)
    
    
    ----------- coverage: platform linux, python 3.8.1-final-0 -----------
    Name                                    Stmts   Miss  Cover
    -----------------------------------------------------------
    src/importnb/__init__.py                    5      0   100%
    src/importnb/__main__.py                    6      2    67%
    src/importnb/_version.py                    1      0   100%
    src/importnb/completer.py                  54     54     0%
    src/importnb/decoder.py                    56      7    88%
    src/importnb/docstrings.py                 43      7    84%
    src/importnb/finder.py                     62      8    87%
    src/importnb/ipython_extension.py          70     39    44%
    src/importnb/loader.py                    159     31    81%
    src/importnb/parameterize.py               95     12    87%
    src/importnb/remote.py                     49      8    84%
    src/importnb/utils/__init__.py              1      1     0%
    src/importnb/utils/export.py               33     33     0%
    src/importnb/utils/ipython.py              47     47     0%
    src/importnb/utils/nbdoctest.py            32     32     0%
    src/importnb/utils/pytest_importnb.py      32     19    41%
    src/importnb/utils/setup.py                52     52     0%
    -----------------------------------------------------------
    TOTAL                                     797    352    56%
    
    
    [32m===================================== [32m[1m16 passed[0m, [33m6 skipped[0m[32m in 1.58s[0m[32m =====================================[0m
    [NbConvertApp] Converting notebook index.ipynb to markdown



```python
    if __name__ == '__main__':
        try:
            from IPython.display import display, Image
            from IPython.utils.capture import capture_output
            from IPython import get_ipython
            with capture_output(): 
                get_ipython().system("cd docs && pyreverse importnb -opng -pimportnb")
            display(Image(url='docs/classes_importnb.png', ))
        except: ...
```


<img src="docs/classes_importnb.png"/>

