#!/usr/bin/env python3
"""Print paste-ready benchmark summary copy from sanitized JSONL logs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gemma_hack.summary import format_submission_benchmark_summary, load_jsonl_records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Format benchmark logs into concise hackathon submission copy")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[ROOT / "logs" / "eval_demo.jsonl", ROOT / "logs" / "benchmarks.jsonl"],
        help="JSONL benchmark log paths; defaults to eval_demo and web benchmark logs",
    )
    parser.add_argument("--limit", type=int, default=3, help="Recent successful rows to include")
    args = parser.parse_args(argv)

    records = []
    for path in args.paths:
        records.extend(load_jsonl_records(path))
    print(format_submission_benchmark_summary(records, limit=args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
