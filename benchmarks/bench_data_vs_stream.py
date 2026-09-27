"""Benchmark: Data (in-memory) vs Stream (lazy).

Runs each scenario in a fresh subprocess so that peak memory is
measured in isolation. Prints a comparison table and a Markdown
summary suitable for a README.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

SCENARIOS = [
    ("data_csv_count", "Data: count CSV", "Data"),
    ("stream_csv_count", "Stream: count CSV", "Stream"),
    ("data_csv_filter_select", "Data: filter+select CSV → CSV", "Data"),
    ("stream_csv_filter_select", "Stream: filter+select CSV → CSV", "Stream"),
    ("data_jsonl_filter_select", "Data: filter+select JSONL → JSONL", "Data"),
    ("stream_jsonl_filter_select", "Stream: filter+select JSONL → JSONL", "Stream"),
]


def run_scenario(
    name: str, input_path: str, output_path: str, timeout: int = 600
) -> Dict[str, Any]:
    cmd = [sys.executable, "-m", "benchmarks.scenarios", name, input_path, output_path]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    wall = time.perf_counter() - t0

    if proc.returncode != 0:
        return {
            "name": name,
            "error": proc.stderr.strip() or f"exit code {proc.returncode}",
            "wall_seconds": wall,
        }

    for line in proc.stdout.splitlines():
        if line.startswith("__BENCH_RESULT__"):
            stats = json.loads(line[len("__BENCH_RESULT__"):])
            stats["name"] = name
            stats["wall_seconds"] = wall
            return stats

    return {
        "name": name,
        "error": "no result line found",
        "wall_seconds": wall,
    }


def format_table(results: List[Dict[str, Any]]) -> str:
    header = (
        f"{'Scenario':<42} "
        f"{'Time (s)':>10} "
        f"{'Peak Python (MB)':>18} "
        f"{'RSS Delta (MB)':>15}"
    )
    lines = [header, "-" * len(header)]
    for r in results:
        if "error" in r:
            lines.append(f"{r['name']:<42} ERROR: {r['error'][:60]}")
            continue
        lines.append(
            f"{r['name']:<42} "
            f"{r['seconds']:>10.2f} "
            f"{r['peak_python_mb']:>18.1f} "
            f"{r['rss_delta_mb']:>15.1f}"
        )
    return "\n".join(lines)


def format_markdown(
    results: List[Dict[str, Any]],
    rows: Optional[int],
    sizes: Dict[str, float],
) -> str:
    lines = ["## Benchmark: Data vs Stream", ""]
    if rows:
        lines.append(f"**Dataset:** {rows:,} rows")
        for name, size in sizes.items():
            lines.append(f"- {name}: {size:.1f} MB")
        lines.append("")

    lines.append("| Scenario | Time (s) | Peak Python (MB) | RSS Δ (MB) |")
    lines.append("|---|---:|---:|---:|")
    for r in results:
        if "error" in r:
            lines.append(f"| {r['name']} | ❌ | — | — |")
            continue
        lines.append(
            f"| {r['name']} | {r['seconds']:.2f} | "
            f"{r['peak_python_mb']:.1f} | {r['rss_delta_mb']:.1f} |"
        )
    lines.append("")

    by_name = {r["name"]: r for r in results if "error" not in r}
    for pair in [
        ("data_csv_filter_select", "stream_csv_filter_select"),
        ("data_jsonl_filter_select", "stream_jsonl_filter_select"),
        ("data_csv_count", "stream_csv_count"),
    ]:
        d = by_name.get(pair[0])
        s = by_name.get(pair[1])
        if d and s:
            mem_ratio = d["peak_python_mb"] / max(s["peak_python_mb"], 0.01)
            time_ratio = d["seconds"] / max(s["seconds"], 0.01)
            lines.append(
                f"- **{d['name']}** vs **{s['name']}**: "
                f"{mem_ratio:.1f}× more Python memory, "
                f"{time_ratio:.1f}× slower"
            )
    lines.append("")
    return "\n".join(lines)


def file_sizes(data_dir: str) -> Dict[str, float]:
    sizes: Dict[str, float] = {}
    for name in ("users.csv", "users.jsonl"):
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            sizes[name] = os.path.getsize(path) / 1e6
    return sizes


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="/tmp/datasift-bench")
    p.add_argument("--rows", type=int, default=None)
    p.add_argument("--markdown", default=None)
    p.add_argument("--json", default=None)
    p.add_argument("--only", default=None)
    args = p.parse_args()

    csv_path = os.path.join(args.data_dir, "users.csv")
    jsonl_path = os.path.join(args.data_dir, "users.jsonl")

    if not os.path.exists(csv_path):
        print(
            f"Missing {csv_path}. Run:\n"
            f"  python -m benchmarks.generate_data "
            f"--rows 1000000 --out {args.data_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    only = set(args.only.split(",")) if args.only else None
    scenarios = [s for s in SCENARIOS if only is None or s[0] in only]

    def input_for(name: str) -> str:
        return jsonl_path if "jsonl" in name else csv_path

    out_dir = os.path.join(args.data_dir, "out")
    os.makedirs(out_dir, exist_ok=True)

    results: List[Dict[str, Any]] = []
    for name, label, _category in scenarios:
        in_path = input_for(name)
        if not os.path.exists(in_path):
            print(f"Skipping {name}: missing {in_path}", file=sys.stderr)
            continue
        out_path = os.path.join(out_dir, f"{name}.out")

        print(f"Running {label}...", file=sys.stderr)
        stats = run_scenario(name, in_path, out_path)
        stats["label"] = label
        results.append(stats)

    print()
    print(format_table(results))
    print()

    sizes = file_sizes(args.data_dir)
    md = format_markdown(results, args.rows, sizes)
    print(md)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Wrote JSON results to {args.json}", file=sys.stderr)

    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Wrote Markdown summary to {args.markdown}", file=sys.stderr)


if __name__ == "__main__":
    main()
