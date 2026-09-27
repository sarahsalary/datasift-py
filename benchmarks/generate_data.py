"""Generate synthetic test data for benchmarks.

Usage:
    python -m benchmarks.generate_data --rows 1000000 --out /tmp/bench
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import string
from typing import Iterator

NAMES = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi"]
DOMAINS = ["example.com", "test.org", "mail.net", "corp.io"]


def _random_user(i: int) -> dict:
    name = random.choice(NAMES)
    age = random.randint(18, 70)
    return {
        "id": i,
        "name": name,
        "age": age,
        "email": f"{name.lower()}{i}@{random.choice(DOMAINS)}",
        "active": random.choice([True, False]),
        "score": round(random.uniform(0, 100), 2),
        "city": "".join(random.choices(string.ascii_lowercase, k=8)),
    }


def iter_users(n: int) -> Iterator[dict]:
    for i in range(n):
        yield _random_user(i)


def write_csv(path: str, n: int) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        first = True
        writer = None
        for user in iter_users(n):
            if first:
                writer = csv.DictWriter(f, fieldnames=list(user.keys()))
                writer.writeheader()
                first = False
            writer.writerow(user)


def write_jsonl(path: str, n: int) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for user in iter_users(n):
            f.write(json.dumps(user, ensure_ascii=False))
            f.write("\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=1_000_000)
    p.add_argument("--out", default="/tmp/datasift-bench")
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    csv_path = os.path.join(args.out, "users.csv")
    jsonl_path = os.path.join(args.out, "users.jsonl")

    random.seed(42)
    print(f"Generating {args.rows:,} rows...")
    write_csv(csv_path, args.rows)
    print(f"  CSV:   {csv_path} ({os.path.getsize(csv_path) / 1e6:.1f} MB)")

    random.seed(42)
    write_jsonl(jsonl_path, args.rows)
    print(f"  JSONL: {jsonl_path} ({os.path.getsize(jsonl_path) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
