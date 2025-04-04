"""# Special handling of markdown cells as docstrings.

Modify the Python `ast` to assign docstrings to functions when they are preceded by a Markdown cell.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, TypeVar

A = TypeVar("A", bound=ast.AST)

"""# Modifying the `ast`

    >>> assert isinstance(create_test, ast.Assign)
    >>> assert isinstance(test_update, ast.Attribute)
"""

create_test = ast.parse("""__test__ = globals().get('__test__', {})""", mode="single").body[0]
test_update = ast.parse("""__test__.update""", mode="single").body[0].value  # type: ignore[attr-defined]

# concrete type references
str_nodes = (ast.Constant,)
docstring_ast_types = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

"""`TestStrings` is an `ast.NodeTransformer` that captures `str_nodes` in the `TestStrings.strings` object.

```ipython
>>> assert isinstance(ast.parse(TestStrings().visit(ast.parse('"Test me"'))), ast.Module)

```
"""


class TestStrings(ast.NodeTransformer):
    strings: list[ast.expr]

    def __init__(self) -> None:
        super().__init__()
        self.strings = []

    def visit_Module(self, module: ast.Module) -> ast.Module:
        """`TestStrings.visit_Module` initializes the capture.

        After all the nodes are visited we append `create_test` and `test_update`
        to populate the `"__test__"` attribute.
        """
        module = self.visit_body(module)

        module.body += (
            [
                create_test,
                *[
                    ast.copy_location(
                        ast.Expr(
                            ast.Call(
                                func=test_update,
                                args=[
                                    ast.Dict(
                                        keys=[ast.Constant(f"string-{node.lineno}")],
                                        values=[node],
                                    ),
                                ],
                                keywords=[],
                            ),
                        ),
                        node,
                    )
                    for node in self.strings
                ],
            ]
            if self.strings
            else []
        )

        return module

    def visit_body(self, node: A) -> A:
        """`TestStrings.visit_body` visits nodes with a `body` attribute and extracts potential string tests."""
        body: list[ast.stmt] = []

        if TYPE_CHECKING:
            assert hasattr(node, "body")

        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, str_nodes)
        ):
            body.append(node.body.pop(0))

        node.body = body + [
            self.visit_body(object) if hasattr(object, "body") else self.visit(object)
            for object in node.body
        ]

        return node

    def visit_Expr(self, node: ast.Expr) -> ast.Expr:
        """`TestStrings.visit_Expr` appends the `str_nodes` to `TestStrings.strings` to append to the `ast.Module`."""
        if isinstance(node.value, str_nodes):
            self.strings.append(
                ast.copy_location(
                    ast.Constant(node.value.value.replace("\n```", "\n")),
                    node,
                ),
            )
        return node


def update_docstring(module: ast.Module) -> ast.Module:
    from functools import reduce

    module.body = reduce(markdown_docstring, module.body, [])
    return TestStrings().visit_Module(module)


def markdown_docstring(nodes: list[ast.stmt], node: ast.stmt) -> list[ast.stmt]:
    if (
        len(nodes) > 1
        and str_expr(nodes[-1])
        and isinstance(node, docstring_ast_types)
        and not str_expr(node.body[0])
    ):
        node.body.insert(0, nodes.pop())
    nodes.append(node)
    return nodes


def str_expr(node: ast.AST) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
