"""JSON reader/writer using only the standard library."""

import json
from typing import IO, Any


def loads(text: str) -> Any:
    return json.loads(text)


def dumps(data: Any, indent: int = 2, **kwargs) -> str:
    return json.dumps(data, indent=indent, ensure_ascii=False, **kwargs)


def read(stream: IO[str]) -> Any:
    return json.load(stream)


def write(data: Any, stream: IO[str], indent: int = 2) -> None:
    json.dump(data, stream, indent=indent, ensure_ascii=False)
    stream.write("\n")
