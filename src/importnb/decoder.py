import json
import linecache
import textwrap
from functools import partial


def quote(object, *, quotes="'''"):
    if quotes in object:
        quotes = '"""'
    return quotes + object + "\n" + quotes


from ._json_parser import Lark_StandAlone, Transformer, Tree


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

    def string(self, s):
        return s[0].line, json.loads(s[0])

    def item(self, s):
        key = s[0][-1]
        if key == "cells":
            if not isinstance(s[-1], Tree):
                return self.render(list(map(dict, s[-1])))
        elif key in {"source", "text"}:
            return key, s[-1]
        elif key == "cell_type":
            if isinstance(s[-1], tuple):
                return key, s[-1][-1]

    def array(self, s):
        if s:
            return s
        return []

    def object(self, s):
        return [x for x in s if x is not None]

    def render_one(self, kind, lines):
        s = "".join(lines)
        if not s.endswith(("\n",)):
            s += "\n"
        return getattr(self, f"transform_{kind}")(s)

    def render(self, x):
        body = []
        for token in x:
            t = token.get("cell_type")
            try:
                s = token["source"]
            except KeyError:
                s = token.get("text")
            if s:
                if not isinstance(s, list):
                    s = [s]
                l, lines = s[0][0], [x[1] for x in s]
                body.extend([""] * (l - len(body)))
                lines = self.render_one(t, lines)
                body.extend(lines.splitlines())
        return "\n".join(body + [""])


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
        s = self.source_from_json_grammar(object)
        if s:
            source = s[0]
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
