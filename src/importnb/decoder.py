import collections
import json
import linecache
import operator
import textwrap
from functools import partial


def quote(object, *, quotes="'''"):
    if quotes in object:
        quotes = '"""'
    return quotes + object + "\n" + quotes


from ._json_parser import Lark_StandAlone, Transformer, Tree

Cell = collections.namedtuple("cell", "lineno cell_type source")
Cell_getter = operator.itemgetter(*Cell._fields)


class Transformer(Transformer):
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
        return s[0]

    def cells(self, s):
        line, buffer = 0, __import__("io").StringIO()
        for t in filter(bool, s):
            # write any missing preceding lines
            buffer.write("\n" * (t.lineno - 2 - line))

            # transform the source based on the cell_type.
            body = getattr(self, f"transform_{t.cell_type[1:-1]}")("".join(t.source))

            if not body.endswith("\n"):
                # append a new line if there isn't one.
                body += "\n"
            buffer.write(body)

            # increment the line numbers that have been visited.
            line += body.count("\n")
        return buffer.getvalue()

    def cell(self, s):
        #  we can't know the order of the cell type and the source
        data = dict(collections.ChainMap(*s))
        if "source" in data:
            return Cell(*Cell_getter(data))
        # the none result will get filtered out before combining.
        return None

    def cell_type(self, s):
        # every cell needs to have this to dispatch the transformers.
        return dict(cell_type=s[0][1])

    def source(self, s):
        # return the line number and source lines.
        return dict(lineno=s[0][0], source=[json.loads(x) for _, x in s]) if s else {}

    def string(self, s):
        # capture the line number of string values
        return s[0].line, str(s[0])

    def _cell_default(self, s, default={}):
        # cell_default need to return a dictionary so it can be used in a change map.
        return default

    outputs = metadata = attachments = execution_count = _cell_default


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
