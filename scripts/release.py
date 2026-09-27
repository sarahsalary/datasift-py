#!/usr/bin/env python3
"""Release automation for datasift-py.

Bumps the version across all files, updates the changelog, creates a
git commit and tag, and optionally pushes to the remote.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT_PY = ROOT / "src" / "datasift" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"

SEMVER_RE = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?P<pre>[-+].+)?$"
)


def parse_version(version: str) -> Tuple[int, int, int, str]:
    match = SEMVER_RE.match(version.strip())
    if not match:
        raise ValueError(f"Invalid semantic version: {version!r}")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        match.group("pre") or "",
    )


def bump_version(current: str, kind: str) -> str:
    major, minor, patch, _ = parse_version(current)
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump kind: {kind!r}")


def read_current_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Cannot find version in {PYPROJECT}")
    return match.group(1)


def update_pyproject(new_version: str, dry_run: bool) -> bool:
    text = PYPROJECT.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count == 0:
        raise RuntimeError(f"No version line found in {PYPROJECT}")
    if new_text == text:
        return False
    if not dry_run:
        PYPROJECT.write_text(new_text, encoding="utf-8")
    return True


def update_init_py(new_version: str, dry_run: bool) -> bool:
    if not INIT_PY.exists():
        return False
    text = INIT_PY.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r'^__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count == 0 or new_text == text:
        return False
    if not dry_run:
        INIT_PY.write_text(new_text, encoding="utf-8")
    return True


def update_changelog(new_version: str, dry_run: bool) -> bool:
    if not CHANGELOG.exists():
        return False

    text = CHANGELOG.read_text(encoding="utf-8")
    today = dt.date.today().isoformat()

    if f"## [{new_version}]" in text:
        return False

    unreleased_re = re.compile(
        r"## \[Unreleased\][^\n]*\n(.*?)(?=\n## \[)",
        re.DOTALL,
    )
    match = unreleased_re.search(text)
    if not match:
        return False

    body = match.group(1).rstrip()
    new_section = (
        "## [Unreleased]\n\n"
        "### Added\n\n"
        "- (Add new features here)\n\n"
        "---\n\n"
        f"## [{new_version}] — {today}\n"
        f"{body}\n"
    )

    new_text = text[: match.start()] + new_section + text[match.end():]
    new_text = re.sub(
        r"^\[Unreleased\]:.*$",
        f"[Unreleased]: https://github.com/YOUR_USERNAME/datasift-py/compare/v{new_version}...HEAD",
        new_text,
        count=1,
        flags=re.MULTILINE,
    )
    if f"[{new_version}]:" not in new_text:
        link = (
            f"[{new_version}]: "
            f"https://github.com/YOUR_USERNAME/datasift-py/releases/tag/v{new_version}"
        )
        new_text = re.sub(
            r"^\[Unreleased\]:",
            f"{link}\n[Unreleased]:",
            new_text,
            count=1,
            flags=re.MULTILINE,
        )

    if new_text == text:
        return False
    if not dry_run:
        CHANGELOG.write_text(new_text, encoding="utf-8")
    return True


def run_git(*args: str, dry_run: bool = False) -> subprocess.CompletedProcess:
    cmd = ["git", *args]
    print(f"  $ {' '.join(cmd)}")
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def is_git_repo() -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip() == "true"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def git_status_is_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    )
    return not result.stdout.strip()


def git_tag_exists(tag: str) -> bool:
    result = subprocess.run(
        ["git", "tag", "--list", tag],
        capture_output=True, text=True, check=True,
    )
    return bool(result.stdout.strip())


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="release.py")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("bump", nargs="?", choices=["major", "minor", "patch"])
    group.add_argument("--set", metavar="VERSION")

    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-git", action="store_true")
    p.add_argument("--no-changelog", action="store_true")
    p.add_argument("--push", action="store_true")
    p.add_argument("--remote", default="origin")
    p.add_argument("--allow-dirty", action="store_true")
    p.add_argument("--yes", "-y", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()

    if not PYPROJECT.exists():
        print(f"error: {PYPROJECT} not found", file=sys.stderr)
        return 1

    if not is_git_repo() and not args.no_git:
        print("error: not inside a git repository", file=sys.stderr)
        return 1

    if not args.no_git and not args.allow_dirty and not git_status_is_clean():
        print("error: working tree is dirty", file=sys.stderr)
        return 1

    current = read_current_version()
    print(f"Current version:  {current}")

    if args.set:
        new_version = args.set.strip().lstrip("v")
        parse_version(new_version)
    else:
        new_version = bump_version(current, args.bump)

    tag = f"v{new_version}"
    print(f"New version:      {new_version}")
    print(f"Tag:              {tag}")
    print()

    if not args.no_git and git_tag_exists(tag):
        print(f"error: tag {tag!r} already exists", file=sys.stderr)
        return 1

    if not args.yes and not args.dry_run:
        answer = input(f"Proceed with release {new_version}? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            return 1

    changed = []
    print("Updating files...")
    if update_pyproject(new_version, args.dry_run):
        print("  ✓ pyproject.toml")
        changed.append(PYPROJECT)
    if update_init_py(new_version, args.dry_run):
        print("  ✓ src/datasift/__init__.py")
        changed.append(INIT_PY)
    if not args.no_changelog and update_changelog(new_version, args.dry_run):
        print("  ✓ CHANGELOG.md")
        changed.append(CHANGELOG)

    if not changed:
        print("\nNo files changed.")
        return 0

    if args.dry_run:
        print("\n[dry-run] No changes were written.")
        return 0

    if args.no_git:
        print("\nSkipping git (--no-git).")
        return 0

    print("\nCommitting and tagging...")
    run_git("add", *[str(p.relative_to(ROOT)) for p in changed])
    run_git("commit", "-m", f"chore: release {tag}")
    run_git("tag", "-a", tag, "-m", f"Release {tag}")

    if args.push:
        print(f"\nPushing to {args.remote}...")
        run_git("push", args.remote, "HEAD")
        run_git("push", args.remote, tag)
        print(f"\n✓ Released {tag} and pushed.")
    else:
        print(f"\n✓ Released {tag} locally.")
        print(f"  To publish: git push {args.remote} HEAD --tags")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
