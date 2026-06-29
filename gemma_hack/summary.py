"""Benchmark summary helpers for hackathon submission copy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .metrics import redact_secrets

PRIMARY_MODEL = "gemma-4-31b"


def load_jsonl_records(path: str | Path) -> list[dict[str, Any]]:
    """Load JSONL benchmark rows, skipping blank or malformed lines."""
    p = Path(path)
    if not p.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            records.append(redact_secrets(parsed))
    return records


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _int_number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _first_agent_model(packet: Mapping[str, Any]) -> str | None:
    agents = packet.get("agents")
    if isinstance(agents, list):
        for agent in agents:
            if isinstance(agent, Mapping) and agent.get("model"):
                return str(agent["model"])
    return None


def _record_model(record: Mapping[str, Any]) -> str | None:
    """Return the model used by a benchmark row, even when the row failed."""
    if record.get("model"):
        return str(record["model"])
    for key in ("eval_packet", "council"):
        packet = record.get(key)
        if isinstance(packet, Mapping):
            model = _first_agent_model(packet)
            if model:
                return model
    packet = record.get("cerebras")
    if isinstance(packet, Mapping) and packet.get("model"):
        return str(packet["model"])
    return None


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_visible_output(packet: Mapping[str, Any]) -> bool:
    if _has_text(packet.get("combined_brief")) or _has_text(packet.get("output")):
        return True
    agents = packet.get("agents")
    if isinstance(agents, list):
        return any(isinstance(agent, Mapping) and _has_text(agent.get("output")) for agent in agents)
    return False


def _benchmark_view(record: Mapping[str, Any]) -> dict[str, Any] | None:
    if isinstance(record.get("eval_packet"), Mapping):
        packet = record["eval_packet"]
        errors = packet.get("errors") or []
        wall_ms = _number(packet.get("total_wall_ms"))
        tokens = _int_number(packet.get("total_tokens"))
        agent_count = _int_number(packet.get("agent_count"))
        model = str(record.get("model") or _first_agent_model(packet) or "unknown-model")
        label = f"{model} council ({agent_count} agents)" if agent_count else f"{model} council"
    elif isinstance(record.get("council"), Mapping):
        packet = record["council"]
        errors = packet.get("errors") or []
        wall_ms = _number(packet.get("total_wall_ms"))
        tokens = _int_number(packet.get("total_tokens"))
        agent_count = _int_number(packet.get("agent_count"))
        model = str(record.get("model") or _first_agent_model(packet) or "unknown-model")
        label = f"{model} council ({agent_count} agents)" if agent_count else f"{model} council"
    elif isinstance(record.get("cerebras"), Mapping):
        packet = record["cerebras"]
        errors = [packet["error"]] if packet.get("error") else []
        metrics = packet.get("metrics") if isinstance(packet.get("metrics"), Mapping) else {}
        wall_ms = _number(metrics.get("wall_ms"))
        tokens = _int_number(metrics.get("total_tokens"))
        model = str(packet.get("model") or record.get("model") or "unknown-model")
        label = f"{model} {record.get('mode') or 'single'}"
    else:
        return None

    if errors or wall_ms is None or wall_ms <= 0 or not _has_visible_output(packet):
        return None
    return {
        "timestamp_utc": str(record.get("timestamp_utc") or "unknown-time"),
        "label": label,
        "model": model,
        "wall_ms": wall_ms,
        "tokens": tokens,
    }


def _fmt_ms(value: float) -> str:
    return f"{value:.1f}"


def _fmt_tokens(value: int | None) -> str:
    return "unknown" if value is None else f"{value:,}"


def format_submission_benchmark_summary(
    records: Iterable[Mapping[str, Any]], *, limit: int = 3, primary_model: str = PRIMARY_MODEL
) -> str:
    """Format primary-model benchmark rows into concise paste-ready submission copy.

    Non-Gemma rows can prove SDK/key plumbing, but they are not contest product evidence.
    """
    safe_records = [redact_secrets(dict(record)) for record in records]
    views = [view for record in safe_records if (view := _benchmark_view(record)) is not None]
    product_records = [record for record in safe_records if _record_model(record) == primary_model]
    product_views = [view for view in views if view.get("model") == primary_model]
    health_check_views = [view for view in views if view.get("model") != primary_model]
    lines = [
        "Benchmark summary for submission:",
        f"- Product model: {primary_model}",
        f"- Successful Gemma 4 product runs: {len(product_views)}/{len(product_records)}",
    ]
    if health_check_views:
        lines.append(
            f"- Non-Gemma successful SDK/key health checks: {len(health_check_views)} (not submission evidence)"
        )
    if not product_views:
        lines.append("- No successful Gemma 4 benchmark rows with visible output and wall-clock metrics yet.")
        return "\n".join(lines)

    fastest = min(product_views, key=lambda view: view["wall_ms"])
    lines.append(
        f"- Fastest Gemma 4: {fastest['label']} in {_fmt_ms(fastest['wall_ms'])} ms wall "
        f"for {_fmt_tokens(fastest['tokens'])} tokens"
    )
    lines.append("- Recent successful Gemma 4 runs:")
    for view in product_views[-max(1, limit) :]:
        lines.append(
            f"  - {view['timestamp_utc']} | {view['label']} in {_fmt_ms(view['wall_ms'])} ms wall "
            f"for {_fmt_tokens(view['tokens'])} tokens"
        )
    lines.append(
        "- Submission line: Gemma 4 on Cerebras produced incident-response output with visible wall-clock "
        f"metrics; best observed run was {fastest['label']} in {_fmt_ms(fastest['wall_ms'])} ms."
    )
    return redact_secrets("\n".join(lines))
