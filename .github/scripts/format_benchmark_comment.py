#!/usr/bin/env python3
"""Format benchmark results into a PR comment.

Reads two JSON files (PR branch and base branch), compares them,
and writes a Markdown comment to the output path.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

COMMENT_MARKER = "<!-- datasift-benchmark -->"
MAX_ROWS = 20


def load_results(path: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"]: item for item in data if "name" in item}


def format_value(value: Optional[float], decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f}"


def format_delta(pr: Optional[float], base: Optional[float]) -> str:
    if pr is None or base is None or base == 0:
        return "—"
    delta_pct = (pr - base) / base * 100
    if abs(delta_pct) < 5:
        icon = "⚪"
    elif delta_pct > 0:
        icon = "🔴"
    else:
        icon = "🟢"
    sign = "+" if delta_pct >= 0 else ""
    return f"{icon} {sign}{delta_pct:.1f}%"


def build_table(
    pr_results: Dict[str, Dict[str, Any]],
    base_results: Dict[str, Dict[str, Any]],
) -> List[str]:
    lines = []
    lines.append(
        "| Scenario | Base Time (s) | PR Time (s) | Δ Time "
        "| Base Peak MB | PR Peak MB | Δ Peak |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    all_names = sorted(set(pr_results) | set(base_results))
    for name in all_names[:MAX_ROWS]:
        pr = pr_results.get(name, {})
        base = base_results.get(name, {})

        if "error" in pr and "error" in base:
            continue

        pr_time = pr.get("seconds")
        base_time = base.get("seconds")
        pr_mem = pr.get("peak_python_mb")
        base_mem = base.get("peak_python_mb")

        lines.append(
            f"| `{name}` "
            f"| {format_value(base_time)} "
            f"| {format_value(pr_time)} "
            f"| {format_delta(pr_time, base_time)} "
            f"| {format_value(base_mem)} "
            f"| {format_value(pr_mem)} "
            f"| {format_delta(pr_mem, base_mem)} |"
        )
    return lines


def build_summary(
    pr_results: Dict[str, Dict[str, Any]],
) -> List[str]:
    lines = []
    pairs = [
        ("data_csv_filter_select", "stream_csv_filter_select", "CSV filter+select"),
        ("data_jsonl_filter_select", "stream_jsonl_filter_select", "JSONL filter+select"),
    ]
    for data_name, stream_name, label in pairs:
        d = pr_results.get(data_name, {})
        s = pr_results.get(stream_name, {})
        if "error" in d or "error" in s:
            continue
        d_mem = d.get("peak_python_mb")
        s_mem = s.get("peak_python_mb")
        if d_mem and s_mem and s_mem > 0:
            ratio = d_mem / s_mem
            lines.append(
                f"- **{label}**: Stream uses **{ratio:.0f}× less memory** than Data"
            )
    return lines


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pr-json", required=True)
    p.add_argument("--base-json", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--pr-number", type=int, required=True)
    p.add_argument("--threshold", type=float, default=25.0)
    args = p.parse_args()

    pr_results = load_results(args.pr_json)
    base_results = load_results(args.base_json)

    lines = [COMMENT_MARKER, "", "## ⚡ Benchmark Report", ""]

    if not pr_results and not base_results:
        lines.append("⚠️ No benchmark results were produced.")
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return 0

    lines.append(
        f"Comparing **PR #{args.pr_number}** against the base branch. "
        f"Regression threshold: **{args.threshold:.0f}%**."
    )
    lines.append("")

    summary = build_summary(pr_results)
    if summary:
        lines.append("### Key findings")
        lines.extend(summary)
        lines.append("")

    lines.append("### Detailed results")
    lines.append("")
    lines.extend(build_table(pr_results, base_results))
    lines.append("")
    lines.append("**Legend:** 🟢 faster | 🔴 slower | ⚪ no significant change")
    lines.append("")
    lines.append(
        "<sub>Benchmarks run on GitHub Actions `ubuntu-latest`. "
        "Results may vary between runs.</sub>"
    )
    lines.append("")

    body = "\n".join(lines)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(body)
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
