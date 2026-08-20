#!/usr/bin/env python3
"""Scan generated text artifacts for likely credentials and private absolute paths."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PATTERNS = {
    "WeRead API key": re.compile(r"wrk-[A-Za-z0-9_-]{12,}"),
    "Bearer credential": re.compile(r"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._-]{12,}", re.I),
    "macOS personal path": re.compile(r"/Users/[^/\s]+/"),
    "Linux personal path": re.compile(r"/home/[^/\s]+/"),
    "Windows personal path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    findings: list[str] = []
    files = [args.path] if args.path.is_file() else sorted(args.path.rglob("*"))
    for path in files:
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".yaml", ".yml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path}: {label}")
    if findings:
        for finding in findings:
            print(f"ERROR: {finding}", file=sys.stderr)
        return 1
    print(f"No likely secrets found in {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
