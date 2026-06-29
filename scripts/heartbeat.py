#!/usr/bin/env python3
"""One-line heartbeat for the Gemma 4 hackathon autopilot cron."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "autopilot"
STATE_DIR.mkdir(exist_ok=True)
HEARTBEAT = STATE_DIR / "heartbeat.json"
STATUS = STATE_DIR / "status.md"

now = datetime.now(timezone.utc).isoformat(timespec="seconds")
state = {"timestamp_utc": now, "project": str(ROOT), "status_file": str(STATUS)}
HEARTBEAT.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

status_line = "status=pending first 20m forge loop"
if STATUS.exists():
    for line in STATUS.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip() and not line.startswith("#"):
            status_line = line.strip()[:180]
            break
print(f"[HEARTBEAT] gemma4-cerebras autopilot alive {now} | {status_line}")
