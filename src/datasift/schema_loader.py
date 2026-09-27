"""Load schemas from Python files or inline strings for CLI use."""

from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Dict, List, Optional

from .exceptions import DataSiftError


class SchemaLoadError(DataSiftError):
    """Raised when a schema cannot be loaded or parsed."""


# ---------------------------------------------------------------------------
# Load from Python file
# ---------------------------------------------------------------------------

def load_from_file(path: str, attr: str) -> Any:
    if not os.path.isfile(path):
        raise SchemaLoadError(f"Schema file not found: {path!r}")

    directory = os.path.dirname(os.path.abspath(path)) or "."
    added = directory not in sys.path
    if added:
        sys.path.insert(0, directory)

    module_name = "_datasift_user_schema"
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise SchemaLoadError(f"Cannot load schema file: {path!r}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception as exc:
        raise SchemaLoadError(f"Error loading {path!r}: {exc}") from exc
    finally:
        if added:
            try:
                sys.path.remove(directory)
            except ValueError:
                pass

    if not hasattr(module, attr):
        available = [n for n in dir(module) if not n.startswith("_")]
        raise SchemaLoadError(
            f"Attribute {attr!r} not found in {path!r}. "
            f"Available: {', '.join(available) or '(none)'}"
        )
    return getattr(module, attr)


# ---------------------------------------------------------------------------
# Parse inline schema
# ---------------------------------------------------------------------------

_TYPE_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "none": type(None),
    "any": Any,
    "list": list,
    "dict": dict,
}


def parse_inline(spec: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for entry in _split_top_level(spec, ","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            raise SchemaLoadError(
                f"Invalid field spec: {entry!r}. Expected name:type"
            )
        name, _, type_name = entry.partition(":")
        result[name.strip()] = _parse_type(type_name.strip())
    return result


def _parse_type(token: str) -> Any:
    token = token.strip()
    if not token:
        raise SchemaLoadError("Empty type in inline schema")

    lower = token.lower()

    if lower.startswith("optional[") and token.endswith("]"):
        inner = token[len("optional["):-1]
        return Optional[_parse_type(inner)]

    if lower.startswith("list[") and token.endswith("]"):
        inner = token[len("list["):-1]
        return List[_parse_type(inner)]

    if lower.startswith("dict[") and token.endswith("]"):
        inner = token[len("dict["):-1]
        parts = _split_top_level(inner, ",")
        if len(parts) != 2:
            raise SchemaLoadError(
                f"Invalid dict type: {token!r}. Expected dict[K,V]"
            )
        return Dict[_parse_type(parts[0]), _parse_type(parts[1])]

    if lower not in _TYPE_MAP:
        supported = ", ".join(sorted(_TYPE_MAP))
        raise SchemaLoadError(
            f"Unknown type: {token!r}. Supported: {supported} "
            f"(or list[...], dict[K,V], optional[...])"
        )
    return _TYPE_MAP[lower]


def _split_top_level(text: str, separator: str) -> List[str]:
    parts: List[str] = []
    depth = 0
    current: List[str] = []
    for ch in text:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == separator and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


__all__ = ["SchemaLoadError", "load_from_file", "parse_inline"]
