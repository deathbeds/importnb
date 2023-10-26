import collections
import json
import linecache
import operator
import textwrap
from io import StringIO
from functools import partial


def quote(object, *, quotes="'''"):
    if quotes in object:
        quotes = '"""'
    return quotes + object + "\n" + quotes


from ._json_parser import Lark_StandAlone, Transformer, Tree

Cell = collections.namedtuple("cell", "lineno cell_type source")
Cell_getter = operator.itemgetter(*Cell._fields)


class Transformer(Transformer):
    """a lark transformer for a grammar specifically designed for the nbformat.

    tokenizes notebook documents parsed with nbformat specific grammar.
    features of the notebook are captured as nodes in the lexical analysis.
    they are further massaged to return a line for line representation of the
    json document as code.
    """

    def __init__(
        self,
        markdown=quote,
        code=textwrap.dedent,
        raw=partial(textwrap.indent, prefix="# "),
        **kwargs,
    ):
        super().__init__(**kwargs)

        for key in ("markdown", "code", "raw"):
            setattr(self, "transform_" + key, locals().get(key))

    def nb(self, s):
        # hide the nb node from the tree.
        return s[0]

    def cells(self, s):
        # recombine the tokenized json document as line for line source code.
        line, buffer = 0, StringIO()
        for t in filter(bool, s):
            # write any missing preceding lines
            buffer.write("\n" * (t.lineno - 2 - line))

            # transform the source based on the cell_type.
            body = getattr(self, f"transform_{t.cell_type}")("".join(t.source))
            buffer.write(body)

            if not body.endswith("\n"):
                buffer.write("\n")
                line += 1

            # increment the line numbers that have been visited.
            line += body.count("\n")
        return buffer.getvalue()

    def cell(self, s):
        # we can't know the order of the cell type and the source.
        # we tokenize the cell parts as a dictionary IFF there is source.
        data = dict(collections.ChainMap(*s))
        if "source" in data:
            return Cell(*Cell_getter(data))
        # the none result will get filtered out before combining.
        return None

    def cell_type(self, s):
        # every cell needs to have this to dispatch the transformers.
        # remove the quotes around the string
        return dict(cell_type=s[0][1][1:-1])

    def source(self, s):
        # return the line number and source lines.
        return dict(lineno=s[0][0], source=[json.loads(x) for _, x in s]) if s else {}

    def string(self, s):
        # capture the line number of string values
        return s[0].line, str(s[0])


class LineCacheNotebookDecoder(Transformer):
    def __init__(
        self,
        markdown=quote,
        code=textwrap.dedent,
        raw=partial(textwrap.indent, prefix="# "),
        **kwargs,
    ):
        super().__init__(**kwargs)

        for key in ("markdown", "code", "raw"):
            setattr(self, "transform_" + key, locals().get(key))

    def source_from_json_grammar(self, object):
        return Lark_StandAlone(transformer=self).parse(object)

    def decode(self, object, filename):
        source = self.source_from_json_grammar(object)
        if source:
            linecache.updatecache(filename)
            if filename in linecache.cache:
                linecache.cache[filename] = (
                    linecache.cache[filename][0],
                    linecache.cache[filename][1],
                    source.splitlines(True),
                    filename,
                )
            return source
        return ""
