"""Multi-agent incident council helpers for the Gemma 4 hackathon demo."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .provider import ProviderResult, call_cerebras

AGENT_ROLES: dict[str, str] = {
    "triage": "Security triage lead: classify the incident, severity, user-visible impact, and first decision.",
    "blast_radius": "Blast-radius analyst: identify affected systems, customers, data, and downtime risk.",
    "remediation": "Remediation commander: propose rollback, mitigation, owner actions, and safe verification steps.",
    "evidence": "Evidence and reporting clerk: list exact logs, screenshots, metrics, and timeline artifacts to collect.",
}

OUTPUT_CONTRACT = """Return exactly these five short bullet lines, no markdown bold:
- Finding:
- Why it matters:
- Immediate action:
- Evidence:
- Demo soundbite:
Maximum 95 words total. Be concrete."""


def build_agent_prompt(role: str, scenario: str) -> str:
    """Wrap a shared incident scenario with one agent role and demo-safe output contract."""
    if role not in AGENT_ROLES:
        raise ValueError(f"unknown agent role: {role}")
    scenario = (scenario or "").strip()
    if not scenario:
        raise ValueError("scenario is required")
    return f"""Agent role: {role}
Mission: {AGENT_ROLES[role]}

Scenario:
{scenario}

{OUTPUT_CONTRACT}"""


def summarize_agent_results(results: Iterable[ProviderResult]) -> dict[str, Any]:
    """Combine agent outputs and benchmark metrics for UI/submission copy."""
    rows = [result.to_dict() for result in results]
    total_wall_ms = 0.0
    total_tokens = 0
    briefs: list[str] = []
    errors: list[str] = []
    for row in rows:
        metrics = row.get("metrics") or {}
        wall = metrics.get("wall_ms")
        tokens = metrics.get("total_tokens")
        if isinstance(wall, (int, float)):
            total_wall_ms += float(wall)
        if isinstance(tokens, int):
            total_tokens += tokens
        output = row.get("output") or ""
        if isinstance(output, str) and output.strip():
            briefs.append(output.strip())
        elif not row.get("error"):
            provider = row.get("provider") or "unknown-provider"
            model = row.get("model") or "unknown-model"
            errors.append(f"Empty visible output from {provider}/{model}; not valid council evidence")
        if row.get("error"):
            errors.append(str(row["error"]))
    return {
        "agent_count": len(rows),
        "total_wall_ms": round(total_wall_ms, 3),
        "total_tokens": total_tokens,
        "combined_brief": "\n\n---\n\n".join(briefs),
        "errors": errors,
        "agents": rows,
    }


def run_incident_council(
    scenario: str,
    *,
    roles: Iterable[str] | None = None,
    model: str | None = None,
    reasoning_effort: str = "none",
    max_completion_tokens: int = 384,
    image_url: str | None = None,
    image_data_uri: str | None = None,
) -> dict[str, Any]:
    """Run one Cerebras completion per role and return a combined council packet."""
    selected_roles = list(roles or AGENT_ROLES.keys())
    results: list[ProviderResult] = []
    for role in selected_roles:
        prompt = build_agent_prompt(role, scenario)
        result = call_cerebras(
            prompt,
            image_url=image_url,
            image_data_uri=image_data_uri,
            model=model,
            reasoning_effort=reasoning_effort,
            max_completion_tokens=max_completion_tokens,
        )
        result.provider = f"cerebras:{role}"
        results.append(result)
    return summarize_agent_results(results)
