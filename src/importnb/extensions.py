# coding: utf-8
"""# Jupyter magic extensions
"""

from .loader import Notebook
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic, line_cell_magic


@magics_class
class ImportNbExtension(Magics):

    @line_magic
    def lmagic(self, line):
        "my line magic"
        print("Full access to the main IPython object:", self.shell)
        print("Variables in the user namespace:", list(self.shell.user_ns.keys()))
        return line

    @cell_magic
    def cmagic(self, line, cell):
        "my cell magic"
        return line, cell

    @line_cell_magic
    def lcmagic(self, line, cell=None):
        "Magic that works both as %lcmagic and as %%lcmagic"
        if cell is None:
            print("Called as line magic")
            return line
        else:
            print("Called as cell magic")
            return line, cell


def load_ipython_extension(ip=None):
    add_path_hooks(Notebook(shell=True), Notebook.EXTENSION_SUFFIXES)
    ip.register_magics(ImportNbExtension)


def unload_ipython_extension(ip=None):
    remove_one_path_hook(Notebook)


"""# Developer
"""

if __name__ == "__main__":
    try:
        from utils.export import export
    except:
        from .utils.export import export
    export("extensions.ipynb", "../extensions.py")
    m = Notebook(shell=True).from_filename("extensions.ipynb")
    print(__import__("doctest").testmod(m, verbose=2))
