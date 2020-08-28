import ast
import builtins
import linecache
import textwrap
from functools import partial

builtins.true, builtins.false, builtins.null = True, False, None


def quote(object, *, quotes="'''"):
    if quotes in object:
        quotes = '"""'
    return quotes + object + "\n" + quotes


def find_key(object, key):
    for k, v in zip(object.keys, object.values):
        if k.s == key:
            break
    return v


def get_source(lines):
    if isinstance(lines, ast.List):
        return ast.copy_location(ast.Str(s="".join(x.s for x in lines.elts)), lines)
    if isinstance(lines, ast.Str):
        return lines


class LineCacheNotebookDecoder:
    def __init__(
        self,
        markdown=quote,
        code=textwrap.dedent,
        raw=partial(textwrap.indent, prefix="# "),
        **kwargs
    ):
        super().__init__(**kwargs)

        for key in ("markdown", "code", "raw"):
            setattr(self, "transform_" + key, locals().get(key))

    def decode(self, object, filename):
        source = self.module_to_source(ast.parse(object))
        linecache.updatecache(filename)
        if filename in linecache.cache:
            linecache.cache[filename] = (
                linecache.cache[filename][0],
                linecache.cache[filename][1],
                source,
                filename,
            )
        return "\n".join(source)

    def module_to_source(self, module):
        source = []
        for node in filter(
            bool,
            [self.find_source(x) for x in find_key(module.body[0].value, "cells").elts],
        ):
            # The minified case will have a great length than line number
            if len(source) >= node.lineno:
                source += node.s.splitlines(True)
                continue
            while len(source) < node.lineno:
                source += [""]
            source += node.s.splitlines()
        if not isinstance(source, list):
            return source.splitlines(True)
        return source

    def find_source(self, object):
        type = None
        for k, v in zip(object.keys, object.values):
            if k.s == "source":
                source = get_source(v)
            if k.s == "cell_type":
                type = getattr(self, "transform_%s" % v.s)

        source.s = type(source.s)
        return source

