#!/usr/bin/env python3
"""Check if any benchmark scenario exceeded the regression threshold.

Exit code 0: no regression above threshold.
Exit code 1: regression detected.
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pr-json", required=True)
    p.add_argument("--base-json", required=True)
    p.add_argument("--threshold", type=float, default=25.0)
    args = p.parse_args()

    if not os.path.exists(args.pr_json) or not os.path.exists(args.base_json):
        print("Missing benchmark JSON files", file=sys.stderr)
        return 0

    with open(args.pr_json, encoding="utf-8") as f:
        pr_data = {item["name"]: item for item in json.load(f) if "name" in item}
    with open(args.base_json, encoding="utf-8") as f:
        base_data = {item["name"]: item for item in json.load(f) if "name" in item}

    regressions = []
    for name, pr in pr_data.items():
        base = base_data.get(name)
        if not base:
            continue
        if "error" in pr or "error" in base:
            continue
        pr_time = pr.get("seconds")
        base_time = base.get("seconds")
        if pr_time is None or base_time in (None, 0):
            continue
        delta_pct = (pr_time - base_time) / base_time * 100
        if delta_pct > args.threshold:
            regressions.append((name, delta_pct))

    if regressions:
        print("Performance regressions detected:", file=sys.stderr)
        for name, pct in regressions:
            print(f"  {name}: +{pct:.1f}% slower", file=sys.stderr)
        return 1

    print("No regressions above threshold.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
