# coding: utf-8
"""# Fuzzy completion

The fuzzy importer could be confusing and perhaps a completer could help.

    >>> ip = get_ipython(); load_ipython_extension(ip)
    >>> assert ip.complete('deathbeds.__complete', 'import deathbeds.__complete')[0]
    >>> assert ip.complete('__complete', 'import __complete')[0]
    >>> assert ip.complete('req', '\timport req')[0]
    >>> assert ip.complete('__complete', 'from deathbeds import __complete')[0]
"""

from .finder import fuzzy_file_search
from fnmatch import fnmatch
from pathlib import Path
import string

"""To provide the most reliable fuzzy imports `fuzzify_string` replaces the imported with one that complies with the fuzzy finder.
"""


def fuzzify_string(str, *, fuzzified=""):
    return str[0] in string.ascii_letters + "_" and str[0] or "_" + "".join(
        letter if letter in string.ascii_letters + "_" + string.digits else "_"
        for letter in str[1:]
    )


"""`align_match` replaces the the begining of the match with a prefix that matches that completer query name.
"""


def align_match(match, prefix, *, i=0):
    pattern = prefix.replace("__", " *").replace("_", "?").strip()
    for i in range(len(match)):
        if fnmatch(match[:i], pattern):
            break
    return prefix + match[i:]


"""* `predict_fuzzy` will take a fully qualified fuzzy name completions.  This is the main function for the completer.
"""


def predict_fuzzy(fullname):
    package, paths, specs = "", [], []
    if "." in fullname:
        package, fullname = fullname.rsplit(".", 1)
        fullname = fullname.strip()
        try:
            paths.append(Path(__import__("importlib").import_module(package).__file__).parent)
        except:
            ...
    else:
        paths = map(Path, __import__("sys").path)
    query = fullname
    while not query.endswith("__"):
        query += "_"
    for path in paths:
        specs.extend(
            str(object.relative_to(path).with_suffix(""))
            for object in fuzzy_file_search(path, query)
        )

    return set(
        (package and package + "." or "") + align_match(fuzzify_string(spec), fullname)
        for spec in specs
    )


"""* The completion event requires a function with `self` & `event` .
"""


def fuzzy_complete_event(self, event):
    event.line = event.line.lstrip()
    symbol = event.symbol
    if "_" in symbol:
        if event.line.startswith("from"):
            if " import" in event.line:
                package = event.line.split(" import", 1)[0].lstrip().lstrip("from").lstrip()
                return [
                    object.lstrip(package).lstrip(".")
                    for object in predict_fuzzy(".".join((package, symbol)))
                ]
        return predict_fuzzy(symbol)
    return []


"""* The extension adds the new fuzzy completer.  Our completer has a higher priority than the default completers.  Since we stripped the leading whitespace from the completion line event; the extension will permit completion on tabbed lines.
"""


def load_ipython_extension(ip):
    ip.set_hook("complete_command", fuzzy_complete_event, str_key="aimport", priority=25)
    ip.set_hook("complete_command", fuzzy_complete_event, str_key="import", priority=25)
    ip.set_hook("complete_command", fuzzy_complete_event, str_key="%reload_ext", priority=25)
    ip.set_hook("complete_command", fuzzy_complete_event, str_key="%load_ext", priority=25)
    ip.set_hook("complete_command", fuzzy_complete_event, str_key="from", priority=25)


if __name__ == "__main__":
    from .utils.export import export
    from .execute import Interactive

    export("completer.ipynb", "../completer.py")
    m = Interactive().from_filename("completer.ipynb")
    print(__import__("doctest").testmod(m, verbose=2))
