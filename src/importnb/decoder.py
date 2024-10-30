from __future__ import annotations

import json
import linecache
import textwrap
from functools import partial
from typing import Any, Callable

from ._json_parser import Lark_StandAlone, Token, Tree
from ._json_parser import Transformer as Transformer_

TItem = tuple[tuple[int, str], Token, tuple[int, str]]


def quote(object: str, *, quotes: str = "'''") -> str:
    if quotes in object:
        quotes = '"""'
    return quotes + object + "\n" + quotes


class Transformer(Transformer_[Any, Any]):
    def __init__(
        self,
        markdown: Callable[..., str] | None = quote,
        code: Callable[..., str] | None = textwrap.dedent,
        raw: Callable[..., str] | None = partial(textwrap.indent, prefix="# "),
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        for key in ("markdown", "code", "raw"):
            setattr(self, f"transform_{key}", locals().get(key))

    def string(self, s: list[Token]) -> tuple[int | None, str]:
        return s[0].line, json.loads(s[0])

    def item(self, s: TItem) -> tuple[str, Any] | str | None:
        key = s[0][-1]
        if key == "cells":
            if not isinstance(s[-1], Tree):
                return self.render(list(map(dict, s[-1])))  # type: ignore[arg-type]
        elif key in {"source", "text"}:
            return key, s[-1]
        elif key == "cell_type":
            if isinstance(s[-1], tuple):
                return key, s[-1][-1]
        return None

    def array(self, s: list[Token]) -> list[Token]:
        if s:
            return s
        return []

    def object(self, s: list[Any]) -> list[Any]:
        return [x for x in s if x is not None]

    def render_one(self, kind: str, lines: list[str]) -> str:
        s = "".join(lines)
        if not s.endswith("\n"):
            s += "\n"
        transformed: str = getattr(self, f"transform_{kind}")(s)
        return transformed

    def render(self, x: list[dict[str, Any]]) -> str:
        body: list[str] = []
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
                lines = self.render_one(f"{t}", lines)
                body.extend(lines.splitlines())
        return "\n".join([*body, ""])


class LineCacheNotebookDecoder(Transformer):
    def source_from_json_grammar(self, object: Any) -> Any:
        parsed: Any = Lark_StandAlone(transformer=self).parse(object)  # type: ignore[no-untyped-call]
        return parsed

    def decode(self, object: Any, filename: str) -> str:
        s = self.source_from_json_grammar(object)
        if s:
            source: str = s[0]
            linecache.updatecache(filename)
            cached: Any = linecache.cache.get(filename)
            if cached:
                linecache.cache[filename] = (
                    cached[0],
                    cached[1],
                    source.splitlines(True),
                    filename,
                )
            return source
        return ""
