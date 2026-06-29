"""Benchmark and redaction helpers for the Gemma Aegis demo app."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_SECRET_PATTERNS = [
    (re.compile(r"csk-[A-Za-z0-9_\.\-]+"), "[REDACTED_CEREBRAS_KEY]"),
    (re.compile(r"sk-[A-Za-z0-9_\.\-]{12,}"), "[REDACTED_API_KEY]"),
]


def redact_secrets(value: Any) -> Any:
    """Recursively redact API-key-shaped strings from logs/responses."""
    if isinstance(value, str):
        redacted = value
        for pattern, replacement in _SECRET_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted
    if isinstance(value, Mapping):
        return {k: redact_secrets(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secrets(v) for v in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(v) for v in value)
    return value


def _to_plain(value: Any) -> Any:
    """Best-effort conversion from SDK objects to plain Python structures."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in value]
    if is_dataclass(value) and not isinstance(value, type):
        return _to_plain(asdict(value))
    if hasattr(value, "model_dump"):
        try:
            return _to_plain(value.model_dump())
        except Exception:
            pass
    if hasattr(value, "dict"):
        try:
            return _to_plain(value.dict())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return {k: _to_plain(v) for k, v in vars(value).items() if not k.startswith("_")}
    return value


def _get_attr_or_key(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def extract_metrics(completion: Any, wall_ms: float | None = None) -> dict[str, Any]:
    """Extract tokens and timing from a Cerebras/OpenAI-compatible completion object."""
    usage = _get_attr_or_key(completion, "usage", {})
    time_info = _get_attr_or_key(completion, "time_info", {})

    metrics = {
        "prompt_tokens": _get_attr_or_key(usage, "prompt_tokens"),
        "completion_tokens": _get_attr_or_key(usage, "completion_tokens"),
        "total_tokens": _get_attr_or_key(usage, "total_tokens"),
        "wall_ms": round(wall_ms, 3) if isinstance(wall_ms, (int, float)) else wall_ms,
        "time_info": _to_plain(time_info) or {},
    }

    plain = _to_plain(completion)
    if isinstance(plain, dict):
        for key in ("time_info", "timing", "timings"):
            if not metrics["time_info"] and isinstance(plain.get(key), dict):
                metrics["time_info"] = plain[key]
        if isinstance(plain.get("usage"), dict):
            usage_dict = plain["usage"]
            metrics["prompt_tokens"] = metrics["prompt_tokens"] or usage_dict.get("prompt_tokens")
            metrics["completion_tokens"] = metrics["completion_tokens"] or usage_dict.get("completion_tokens")
            metrics["total_tokens"] = metrics["total_tokens"] or usage_dict.get("total_tokens")

    return redact_secrets(metrics)


def append_benchmark_record(path: str | Path, record: Mapping[str, Any]) -> dict[str, Any]:
    """Append one sanitized JSONL benchmark record and return the written row."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **dict(record),
    }
    row = redact_secrets(row)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row
