try:
    from IPython import InteractiveShell

    InteractiveShell.instance()
except:
    collect_ignore = ["src/importnb/utils/ipython.py", "src/importnb/completer.py", "noxfile.py"]

pytest_plugins = ["pytester"]