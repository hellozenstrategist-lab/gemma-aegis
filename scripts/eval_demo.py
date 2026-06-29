#!/usr/bin/env python3
"""Small live eval for the hackathon demo path.

Default is the contest model: Gemma 4 on Cerebras.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gemma_hack.agents import run_incident_council
from gemma_hack.metrics import append_benchmark_record

SCENARIO = """Production auth incident, 09:42 PT:
- Login error rate rose from 0.2% to 18% after deploy api-gateway:2026.06.28-rc2.
- Enterprise SSO customers report redirect loops.
- WAF volume normal; no clear credential stuffing spike.
- p95 auth latency 210ms -> 3.8s; OAuth callback 500s rising.
Triage severity, blast radius, immediate action, and evidence to collect next.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemma-4-31b", help="Contest model. Use only explicit fallback models for SDK/key health checks.")
    parser.add_argument("--roles", default="triage,remediation", help="Comma roles; keep small for cheap smoke")
    parser.add_argument("--tokens", type=int, default=768)
    parser.add_argument("--reasoning", default="none", choices=["none", "low", "medium", "high"], help="Use none for Gemma speed demo unless the model requires explicit reasoning.")
    args = parser.parse_args()
    roles = [r.strip() for r in args.roles.split(",") if r.strip()]
    packet = run_incident_council(
        SCENARIO,
        roles=roles,
        model=args.model,
        max_completion_tokens=args.tokens,
        reasoning_effort=args.reasoning,
    )
    append_benchmark_record(ROOT / "logs" / "eval_demo.jsonl", {"model": args.model, "eval_packet": packet})
    print(json.dumps(packet, indent=2, ensure_ascii=False))
    return 1 if packet.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
