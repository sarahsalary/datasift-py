"""A tiny, dependency-free query language for nested data.

Syntax examples:
    users[0].name
    users[?age > 30].name
    users[?active == true]
    config.db.host
    tags[*]
    items[?price >= 10 && price <= 100]
"""

from __future__ import annotations

import re
from typing import Any, Callable, List, Tuple

from .exceptions import QueryError

_TOKEN_RE = re.compile(
    r"""
    \s*(?:
        (?P<lparen>\() |
        (?P<rparen>\)) |
        (?P<filter>\[\?) |
        (?P<filter_end>\]) |
        (?P<and>&&) |
        (?P<or>\|\|) |
        (?P<op>==|!=|>=|<=|>|<) |
        (?P<star>\[\*\]|\*) |
        (?P<index>\[\d+\]) |
        (?P<string>'[^']*'|"[^"]*") |
        (?P<bool>true|false) |
        (?P<null>null) |
        (?P<number>-?\d+(?:\.\d+)?) |
        (?P<dot>\.) |
        (?P<ident>[A-Za-z_][A-Za-z0-9_-]*) |
        (?P<space>\s+)
    )
    """,
    re.VERBOSE,
)


Token = Tuple[str, Any]


def _tokenize(expr: str) -> List[Token]:
    """Tokenize a query expression."""
    tokens: List[Token] = []
    pos = 0

    while pos < len(expr):
        match = _TOKEN_RE.match(expr, pos)
        if not match:
            raise QueryError(
                f"Unexpected character at position {pos}: {expr[pos]!r}"
            )

        pos = match.end()
        kind = match.lastgroup
        if kind is None:
            raise QueryError(f"Unable to tokenize expression at position {pos}")

        value = match.group().strip()

        if kind == "space":
            continue
        if kind == "index":
            tokens.append(("index", int(value[1:-1])))
        elif kind == "string":
            tokens.append(("string", value[1:-1]))
        elif kind == "bool":
            tokens.append(("bool", value == "true"))
        elif kind == "null":
            tokens.append(("null", None))
        elif kind == "number":
            tokens.append(
                ("number", float(value) if "." in value else int(value))
            )
        else:
            tokens.append((kind, value))

    tokens.append(("eof", None))
    return tokens


class _Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def next(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, kind: str) -> Any:
        token = self.next()
        if token[0] != kind:
            raise QueryError(
                f"Expected {kind}, got {token[0]} ({token[1]!r})"
            )
        return token[1]

    def parse(self) -> Callable[[Any], Any]:
        fn = self.parse_or()
        if self.peek()[0] != "eof":
            raise QueryError(f"Unexpected token: {self.peek()}")
        return fn

    def parse_or(self) -> Callable[[Any], Any]:
        left = self.parse_and()
        while self.peek()[0] == "or":
            self.next()
            right = self.parse_and()
            left = _or(left, right)
        return left

    def parse_and(self) -> Callable[[Any], Any]:
        left = self.parse_comparison()
        while self.peek()[0] == "and":
            self.next()
            right = self.parse_comparison()
            left = _and(left, right)
        return left

    def parse_comparison(self) -> Callable[[Any], Any]:
        left = self.parse_path()
        if self.peek()[0] == "op":
            op = self.next()[1]
            right = self.parse_value()
            return _comparison(op, left, right)
        return left

    def parse_value(self) -> Callable[[Any], Any]:
        kind, value = self.next()
        if kind in ("string", "number", "bool", "null"):
            return lambda _data: value
        raise QueryError(f"Expected a literal value, got {kind}")

    def parse_path(self) -> Callable[[Any], Any]:
        kind, name = self.next()
        if kind != "ident":
            raise QueryError(f"Expected an identifier, got {(kind, name)!r}")

        steps: List[Callable[[Any], Any]] = [_identity_key(name)]

        while True:
            kind, value = self.peek()

            if kind == "dot":
                self.next()
                name = self.expect("ident")
                steps.append(_identity_key(name))
            elif kind == "index":
                self.next()
                steps.append(_identity_index(value))
            elif kind == "star":
                self.next()
                steps.append(_identity_star)
            elif kind == "filter":
                self.next()
                predicate = self.parse_or()
                self.expect("filter_end")
                steps.append(_identity_filter(predicate))
            else:
                break

        return _chain(steps)


def _identity_key(name: str) -> Callable[[Any], Any]:
    def fn(data: Any) -> Any:
        if isinstance(data, dict):
            return data.get(name)
        if isinstance(data, (list, tuple)):
            return [item.get(name) if isinstance(item, dict) else None for item in data]
        raise QueryError(
            f"Cannot get key {name!r} from {type(data).__name__}"
        )

    return fn


def _identity_index(index: int) -> Callable[[Any], Any]:
    def fn(data: Any) -> Any:
        if isinstance(data, (list, tuple)):
            try:
                return data[index]
            except IndexError:
                return None
        raise QueryError(f"Cannot index {type(data).__name__}")

    return fn


def _identity_star(data: Any) -> List[Any]:
    if isinstance(data, (list, tuple)):
        return list(data)
    raise QueryError(f"Cannot expand star on {type(data).__name__}")


def _identity_filter(
    predicate: Callable[[Any], Any],
) -> Callable[[Any], Any]:
    def fn(data: Any) -> List[Any]:
        if not isinstance(data, (list, tuple)):
            raise QueryError("Filter can only be applied to a list")
        return [item for item in data if predicate(item)]

    return fn


def _chain(steps: List[Callable[[Any], Any]]) -> Callable[[Any], Any]:
    def fn(data: Any) -> Any:
        for step in steps:
            data = step(data)
        return data

    return fn


def _comparison(
    op: str,
    left_fn: Callable[[Any], Any],
    right_fn: Callable[[Any], Any],
) -> Callable[[Any], bool]:
    def fn(data: Any) -> bool:
        return _apply_op(op, left_fn(data), right_fn(data))

    return fn


def _apply_op(op: str, a: Any, b: Any) -> bool:
    try:
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == ">":
            return a > b
        if op == ">=":
            return a >= b
        if op == "<":
            return a < b
        if op == "<=":
            return a <= b
    except TypeError as exc:
        raise QueryError(
            f"Cannot compare {a!r} and {b!r} with {op}"
        ) from exc

    raise QueryError(f"Unknown operator: {op}")


def _and(
    left_fn: Callable[[Any], Any],
    right_fn: Callable[[Any], Any],
) -> Callable[[Any], bool]:
    def fn(data: Any) -> bool:
        return bool(left_fn(data)) and bool(right_fn(data))

    return fn


def _or(
    left_fn: Callable[[Any], Any],
    right_fn: Callable[[Any], Any],
) -> Callable[[Any], bool]:
    def fn(data: Any) -> bool:
        return bool(left_fn(data)) or bool(right_fn(data))

    return fn


def compile_query(expr: str) -> Callable[[Any], Any]:
    """Compile a query expression into ``f(data) -> result``."""
    if not isinstance(expr, str) or not expr.strip():
        raise QueryError("Query expression must be a non-empty string")
    return _Parser(_tokenize(expr)).parse()


def query(data: Any, expr: str) -> Any:
    """Compile and evaluate ``expr`` against ``data`` in one call."""
    return compile_query(expr)(data)


__all__ = ["compile_query", "query"]
