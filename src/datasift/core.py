"""High-level API: load, query, convert, save."""

import io
import os
from typing import Any, Optional, Union

from .exceptions import DataSiftError, FormatError
from .formats import get_handler, supported_formats
from .query import query as _query


def detect_format(path: str) -> str:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if not ext:
        raise FormatError(f"Cannot detect format from path: {path!r}")
    return ext


def load(path_or_text: str, fmt: Optional[str] = None, is_text: bool = False) -> Any:
    if is_text:
        if not fmt:
            raise FormatError("fmt is required when is_text=True")
        handler = get_handler(fmt)
        return handler.loads(path_or_text)

    fmt = fmt or detect_format(path_or_text)
    handler = get_handler(fmt)
    try:
        with open(path_or_text, encoding="utf-8") as f:
            return handler.read(f)
    except OSError as exc:
        raise FormatError(f"Cannot read {path_or_text!r}: {exc}") from exc


def dump(
    data: Any,
    path_or_stream: Union[str, io.IOBase, None] = None,
    fmt: Optional[str] = None,
    **kwargs,
) -> Optional[str]:
    if fmt is None:
        if isinstance(path_or_stream, str):
            fmt = detect_format(path_or_stream)
        else:
            raise FormatError("fmt is required when output is not a file path")

    handler = get_handler(fmt)
    text = handler.dumps(data, **kwargs)

    if path_or_stream is None:
        return text

    if isinstance(path_or_stream, str):
        with open(path_or_stream, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        path_or_stream.write(text)
    return None


def convert(
    input_path: str,
    output_path: str,
    input_fmt: Optional[str] = None,
    output_fmt: Optional[str] = None,
    query_expr: Optional[str] = None,
) -> None:
    data = load(input_path, fmt=input_fmt)
    if query_expr:
        data = _query(data, query_expr)
    dump(data, output_path, fmt=output_fmt)


def query_file(path: str, expr: str, fmt: Optional[str] = None) -> Any:
    data = load(path, fmt=fmt)
    return _query(data, expr)


__all__ = [
    "DataSiftError",
    "FormatError",
    "convert",
    "detect_format",
    "dump",
    "load",
    "query_file",
    "supported_formats",
]
