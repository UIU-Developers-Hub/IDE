"""Extract document symbols for the sidebar OUTLINE view."""

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class OutlineSymbol:
    kind: str
    name: str
    line: int
    parent: str | None = None


def extract_python_outline(source: str) -> list[OutlineSymbol]:
    tree = ast.parse(source)
    symbols: list[OutlineSymbol] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            symbols.append(OutlineSymbol("class", node.name, node.lineno))
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(
                        OutlineSymbol("method", child.name, child.lineno, node.name)
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(OutlineSymbol("function", node.name, node.lineno))

    return symbols


def can_outline_file(path: str | None) -> bool:
    return bool(path) and path.lower().endswith(".py")
