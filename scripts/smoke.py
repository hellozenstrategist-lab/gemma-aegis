#!/usr/bin/env python3
"""CLI smoke runner for the Gemma 4 x Cerebras prep scaffold."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gemma_hack.metrics import append_benchmark_record
from gemma_hack.provider import call_cerebras


def run_smoke(
    prompt: str,
    *,
    reasoning: str = "none",
    model: str | None = None,
    log_path: str | Path = ROOT / "logs" / "smoke.jsonl",
    call_provider: Callable[..., Any] = call_cerebras,
    emit: Callable[[str], Any] = print,
) -> int:
    """Run one Cerebras smoke completion and reject empty visible output as failed evidence."""
    result = call_provider(prompt, reasoning_effort=reasoning, model=model)
    record = result.to_dict()
    if result.error:
        append_benchmark_record(log_path, record)
        emit(f"ERROR: {result.error}")
        return 2
    if not str(result.output or "").strip():
        message = f"Empty visible output from {result.model}; not valid product smoke evidence"
        record["error"] = message
        append_benchmark_record(log_path, record)
        emit(f"ERROR: {message}")
        return 3
    row = append_benchmark_record(log_path, record)
    emit(str(result.output))
    emit(f"\nMETRICS: {row.get('metrics')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Triage this production auth failure: repeated 401s, spike in failed logins, and customer support tickets rising.",
    )
    parser.add_argument("--reasoning", default="none", choices=["none", "low", "medium", "high"])
    parser.add_argument("--model", default=None)
    args = parser.parse_args(argv)
    return run_smoke(args.prompt, reasoning=args.reasoning, model=args.model)


if __name__ == "__main__":
    raise SystemExit(main())
