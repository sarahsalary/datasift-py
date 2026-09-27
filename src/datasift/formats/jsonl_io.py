"""JSONL (JSON Lines) reader/writer using only the standard library.

Each line is an independent JSON value. This format is ideal for
streaming because records can be read and written one at a time.
"""

import json
from typing import IO, Any, Iterator, List


def loads(text: str) -> List[Any]:
    """Parse a JSONL string into a list."""
    result: List[Any] = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            result.append(json.loads(line))
    return result


def dumps(data: Any, **kwargs) -> str:
    """Serialize an iterable to JSONL text."""
    lines: List[str] = []
    for item in data:
        lines.append(json.dumps(item, ensure_ascii=False, **kwargs))
    return "\n".join(lines) + ("\n" if lines else "")


def read(stream: IO[str]) -> List[Any]:
    return loads(stream.read())


def write(data: Any, stream: IO[str], **kwargs) -> None:
    for item in data:
        stream.write(json.dumps(item, ensure_ascii=False, **kwargs))
        stream.write("\n")


def iter_read(stream: IO[str]) -> Iterator[Any]:
    """Lazily yield one parsed JSON value per line."""
    for line in stream:
        line = line.strip()
        if line:
            yield json.loads(line)


def iter_write(items: Iterator[Any], stream: IO[str], **kwargs) -> None:
    """Write items to a stream one JSON value per line."""
    for item in items:
        stream.write(json.dumps(item, ensure_ascii=False, **kwargs))
        stream.write("\n")
