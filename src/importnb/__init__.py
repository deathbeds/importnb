__all__ = 'Notebook', 'Partial', 'reload', 'load_ipython_extension', 'unload_ipython_extension'

from .loader import Notebook, Partial, load_ipython_extension, unload_ipython_extension, reload

try:
    import IPython
    from .utils.ipython import install, uninstall
except: ...