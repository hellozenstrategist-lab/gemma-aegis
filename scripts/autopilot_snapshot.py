#!/usr/bin/env python3
"""Fast local snapshot for cron agents before/after edits."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=60)
    return p.returncode, (p.stdout + p.stderr).strip()

code, tests = run(["python3", "-m", "unittest", "discover", "-s", "tests", "-v"])
files = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".env" not in p.name and "__pycache__" not in str(p))
packet = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "test_exit_code": code,
    "test_tail": "\n".join(tests.splitlines()[-18:]),
    "file_count": len(files),
    "key_files": [f for f in files if f.endswith((".py", ".md", ".html", ".txt", ".example"))][:80],
}
print(json.dumps(packet, indent=2))
raise SystemExit(code)
