
Load the __importnb__ to import notebooks.

[![Binder](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/deathbeds/importnb/master?filepath=readme.ipynb)

## Jupyter Extension


```python
    if __name__ == '__main__':
        %reload_ext importnb
        import readme
        assert readme.foo is 42
        assert readme.__file__.endswith('.ipynb')
    else: 
        foo = 42
        
```

Notebooks maybe reloaded with the standard Python Import machinery.


```python
    if __name__ == '__main__':
        from importnb import Notebook, reload
        reload(readme)
        %unload_ext importnb
```

## Context Manager


```python
    if __name__ == '__main__':
        try:  
            reload(readme)
            assert None, """Reloading should not work when the extension is unloaded"""
        except AttributeError: 
            with Notebook(): reload(readme)
```

## Developer


```python
    if __name__ == '__main__':
        !jupyter nbconvert --to markdown readme.ipynb
```

    [NbConvertApp] Converting notebook readme.ipynb to markdown
    [NbConvertApp] Writing 1091 bytes to readme.md

