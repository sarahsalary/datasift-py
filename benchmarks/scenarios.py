"""Individual benchmark scenarios.

Each scenario is a function that takes an ``input_path`` and
``output_path`` and returns a small dict describing what it did.

Run one scenario directly::

    python -m benchmarks.scenarios data_csv_filter_select in.csv out.csv
"""

from __future__ import annotations

import sys
from typing import Any, Dict

from datasift import Data, Stream

# ---------------------------------------------------------------------------
# Data (in-memory) scenarios
# ---------------------------------------------------------------------------

def data_csv_filter_select(in_path: str, out_path: str) -> Dict[str, Any]:
    result = (
        Data(in_path)
        .filter(age__gt=30)
        .select("id", "name", "age", "email")
        .to(out_path)
    )
    return {"rows_out": len(result.data)}


def data_jsonl_filter_select(in_path: str, out_path: str) -> Dict[str, Any]:
    result = (
        Data(in_path)
        .filter(age__gt=30)
        .select("id", "name", "age", "email")
        .to(out_path)
    )
    return {"rows_out": len(result.data)}


def data_csv_count(in_path: str, out_path: str) -> Dict[str, Any]:
    data = Data(in_path)
    return {"rows_out": len(data.data)}


# ---------------------------------------------------------------------------
# Stream scenarios
# ---------------------------------------------------------------------------

def stream_csv_filter_select(in_path: str, out_path: str) -> Dict[str, Any]:
    (
        Stream.from_csv(in_path)
        .filter(age__gt=30)
        .select("id", "name", "age", "email")
        .to_csv(out_path)
    )
    return {"rows_out": "streamed"}


def stream_jsonl_filter_select(in_path: str, out_path: str) -> Dict[str, Any]:
    (
        Stream.from_jsonl(in_path)
        .filter(age__gt=30)
        .select("id", "name", "age", "email")
        .to_jsonl(out_path)
    )
    return {"rows_out": "streamed"}


def stream_csv_count(in_path: str, out_path: str) -> Dict[str, Any]:
    stream = Stream.from_csv(in_path)
    total = stream.count()
    return {"rows_out": total}


SCENARIOS = {
    "data_csv_filter_select": data_csv_filter_select,
    "data_jsonl_filter_select": data_jsonl_filter_select,
    "data_csv_count": data_csv_count,
    "stream_csv_filter_select": stream_csv_filter_select,
    "stream_jsonl_filter_select": stream_jsonl_filter_select,
    "stream_csv_count": stream_csv_count,
}


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: python -m benchmarks.scenarios SCENARIO INPUT OUTPUT",
              file=sys.stderr)
        sys.exit(2)

    name, in_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    if name not in SCENARIOS:
        print(f"Unknown scenario: {name}", file=sys.stderr)
        print(f"Available: {', '.join(sorted(SCENARIOS))}", file=sys.stderr)
        sys.exit(2)

    from .measure import emit, measure

    stats = measure(lambda: SCENARIOS[name](in_path, out_path))
    emit(stats)


if __name__ == "__main__":
    main()
