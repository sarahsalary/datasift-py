"""CSV reader/writer using only the standard library."""

import csv
import io
from typing import IO, Any, Dict, List, Optional


def loads(text: str, **kwargs) -> List[Dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text), **kwargs)
    return [dict(row) for row in reader]


def dumps(
    rows: List[Dict[str, Any]],
    fieldnames: Optional[List[str]] = None,
    **kwargs,
) -> str:
    if not rows:
        return ""
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore", **kwargs)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: ("" if v is None else v) for k, v in row.items()})
    return buf.getvalue()


def read(stream: IO[str], **kwargs) -> List[Dict[str, Any]]:
    return list(csv.DictReader(stream, **kwargs))


def write(
    rows: List[Dict[str, Any]],
    stream: IO[str],
    fieldnames: Optional[List[str]] = None,
    **kwargs,
) -> None:
    stream.write(dumps(rows, fieldnames=fieldnames, **kwargs))
