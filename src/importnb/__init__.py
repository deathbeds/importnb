# coding: utf-8

__all__ = "Notebook", "reload"

def is_ipython():
    from sys import modules
    
    return "IPython" in modules
    
def get_ipython():
    if is_ipython():
        from IPython import get_ipython
        
        return get_ipython()
    return None

from ._version import *
from .ipython_extension import load_ipython_extension, unload_ipython_extension
from .loader import Notebook, reload

import builtins
builtins.true, builtins.false, builtins.null = True, False, None

    