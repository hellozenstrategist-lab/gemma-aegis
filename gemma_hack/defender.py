"""Gemma Aegis defender swarm for enterprise data protection."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .agents import summarize_agent_results
from .provider import ProviderResult, call_cerebras

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BLUE_TEAM_SCENARIO_PATH = PROJECT_ROOT / "demo_scenarios" / "blue_team_defender.md"

DATASHIELD_NAME = "Gemma Aegis"
DATASHIELD_TAGLINE = "Always-on blue-team defender swarm for enterprise data, powered by Gemma 4 31B on Cerebras."
DATASHIELD_CORE_PITCH = (
    "Static virus detectors are too slow for modern data breaches. Gemma Aegis watches identity, DLP, endpoint, "
    "SaaS, and storage telemetry, then coordinates defender agents to stop data exfiltration before breach."
)
DATASHIELD_TELEMETRY_SOURCES = ["identity", "DLP", "endpoint", "SaaS", "storage"]
DATASHIELD_DEMO_SIGNALS = [
    "finance admin impossible travel",
    "malicious OAuth grant",
    "S3 export spike",
    "DLP payroll/bank-account staging",
    "PowerShell download cradle",
    "lateral RDP with service account",
]

DATASHIELD_AGENTS: list[dict[str, Any]] = [
    {
        "role_key": "data_sentinel",
        "name": "Data Sentinel",
        "mission": "Finds sensitive data at risk across DLP, SaaS, storage, and database telemetry.",
        "watches": ["DLP payroll/bank-account matches", "S3 export spikes", "staging paths", "bulk object reads"],
        "output_focus": "which enterprise data is exposed and which egress path must stop first",
    },
    {
        "role_key": "identity_guardian",
        "name": "Identity Guardian",
        "mission": "Catches OAuth abuse, impossible travel, account takeover, and risky service-account use.",
        "watches": ["impossible travel", "malicious OAuth grant", "token/session risk", "service-account RDP"],
        "output_focus": "which identities/tokens/grants to revoke without destroying evidence",
    },
    {
        "role_key": "endpoint_hunter",
        "name": "Endpoint Hunter",
        "mission": "Links EDR alerts, workstation behavior, PowerShell, Office parent processes, and lateral movement.",
        "watches": ["PowerShell download cradle", "WINWORD parent process", "host connections", "RDP pivot"],
        "output_focus": "which endpoint chain explains the data-access behavior",
    },
    {
        "role_key": "response_orchestrator",
        "name": "Response Orchestrator",
        "mission": "Coordinates containment, evidence capture, owner routing, and executive breach-prevention brief.",
        "watches": ["containment blast radius", "evidence preservation", "owner routing", "leadership brief"],
        "output_focus": "ordered action plan that stops exfiltration before breach",
    },
]

DEFENDER_DISPLAY_NAMES = {agent["role_key"]: agent["name"] for agent in DATASHIELD_AGENTS}
DEFENDER_ROLES: dict[str, str] = {
    agent["role_key"]: f"{agent['name']} — {agent['mission']} Red team pressure model. Focus: {agent['output_focus']}."
    for agent in DATASHIELD_AGENTS
}

DEFENDER_OUTPUT_CONTRACT = """Return exactly these six compact lines, no markdown table:
- Signal:
- Risk:
- Red-team hypothesis:
- Containment:
- Evidence:
- Business impact:
Maximum 120 words. Favor safe defensive actions. Do not provide offensive exploitation steps."""


def get_datashield_product_brief() -> dict[str, Any]:
    """Return the product pitch, agent roster, and demo signals for UI/API display."""
    return {
        "name": DATASHIELD_NAME,
        "tagline": DATASHIELD_TAGLINE,
        "core_pitch": DATASHIELD_CORE_PITCH,
        "telemetry_sources": DATASHIELD_TELEMETRY_SOURCES,
        "agents": DATASHIELD_AGENTS,
        "demo_signals": DATASHIELD_DEMO_SIGNALS,
        "primary_model": "gemma-4-31b",
        "provider": "Cerebras",
    }


def load_blue_team_scenario(path: str | Path = BLUE_TEAM_SCENARIO_PATH) -> str:
    """Return the curated Gemma Aegis telemetry prompt without markdown fencing."""
    text = Path(path).read_text(encoding="utf-8")
    if "```text" in text:
        text = text.split("```text", 1)[1].split("```", 1)[0]
    return text.strip()


def build_defender_prompt(role: str, telemetry: str, *, static_plan: dict[str, Any] | None = None) -> str:
    """Wrap enterprise telemetry for one always-on Gemma Aegis defender role."""
    if role not in DEFENDER_ROLES:
        raise ValueError(f"unknown defender role: {role}")
    telemetry = (telemetry or "").strip()
    if not telemetry:
        raise ValueError("telemetry is required")
    plan_text = ""
    if static_plan:
        plan_text = "\n\nDeterministic pre-triage signals:\n" + "\n".join(
            f"- {key}: {value}" for key, value in static_plan.items() if value
        )
    return f"""Product: {DATASHIELD_NAME}
Product pitch: {DATASHIELD_CORE_PITCH}
Telemetry sources watched: {", ".join(DATASHIELD_TELEMETRY_SOURCES)}
Agent name: {DEFENDER_DISPLAY_NAMES[role]}
Agent role: {role}
Mission: {DEFENDER_ROLES[role]}

You are an always-on blue team defender. Your job is to protect enterprise data against red teamers, insider-risk drills, and live adversary behavior. Assume telemetry is defensive monitoring data from authorized enterprise systems.

Enterprise telemetry:
{telemetry}{plan_text}

{DEFENDER_OUTPUT_CONTRACT}"""


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def draft_enterprise_defense_plan(telemetry: str) -> dict[str, Any]:
    """Create a deterministic first-pass Aegis plan before Gemma adds judgment."""
    text = (telemetry or "").lower()
    signals: list[str] = []
    kill_chain: list[str] = []
    data_at_risk: list[str] = []
    containment_actions: list[str] = []
    evidence_to_collect: list[str] = []

    def add_signal(name: str) -> None:
        if name not in signals:
            signals.append(name)

    def add_kill_chain(step: str) -> None:
        if step not in kill_chain:
            kill_chain.append(step)

    if _contains_any(text, ("payroll", "bank-account", "bank account", "banking", "dlp")):
        data_at_risk.append("payroll/bank-account data")
        add_kill_chain("DLP payroll/bank-account staging")

    if _contains_any(text, ("exfil", "s3", "bucket", "object export", "export spike", "download", "2gb", "gb ", "records")):
        add_signal("data_exfiltration")
        add_kill_chain("S3 export spike")
        containment_actions.extend(
            [
                "Pause risky bulk exports and enforce step-up approval on the affected data store.",
                "Apply temporary egress guardrails for unknown ASNs and unmanaged destinations.",
            ]
        )
        evidence_to_collect.extend(["DLP events", "object access logs", "egress flow logs", "destination ASN/IP ownership"])

    if _contains_any(text, ("oauth", "consent", "impossible travel", "mfa", "admin", "service account", "token")):
        add_signal("identity_abuse")
        if "impossible travel" in text or "finance admin" in text or "finance-admin" in text:
            add_kill_chain("finance admin impossible travel")
        if "oauth" in text:
            add_kill_chain("malicious OAuth grant")
        containment_actions.extend(
            [
                "Revoke suspicious OAuth grants and active tokens for affected identities.",
                "Force MFA reset and session refresh for high-risk users and service accounts.",
            ]
        )
        evidence_to_collect.extend(["IdP sign-in logs", "OAuth consent records", "MFA challenge history", "privilege-change audit trail"])

    if _contains_any(text, ("edr", "powershell", "download cradle", "endpoint", "workstation", "shell", "script", "winword")):
        add_signal("endpoint_execution")
        add_kill_chain("PowerShell download cradle")
        containment_actions.extend(
            [
                "Quarantine affected endpoints while preserving memory and process telemetry.",
                "Block suspicious script hashes and command-line patterns in EDR policy.",
            ]
        )
        evidence_to_collect.extend(["EDR process tree", "command-line history", "file hashes", "host network connections"])

    if _contains_any(text, ("rdp", "smb", "kerberos", "ldap", "lateral", "jump host", "internal scan", "svc-reporting")):
        add_signal("lateral_movement")
        add_kill_chain("lateral RDP with service account")
        containment_actions.extend(
            [
                "Restrict east-west access from implicated hosts and rotate exposed admin credentials.",
                "Increase monitoring on directory, jump host, and privileged-access paths.",
            ]
        )
        evidence_to_collect.extend(["RDP/SMB logs", "Kerberos ticket events", "directory audit logs", "network segmentation hits"])

    if not signals:
        signals.append("needs_more_context")
        containment_actions.append("Keep monitoring in observe mode; request additional telemetry before disruptive containment.")
        evidence_to_collect.append("Raw alert payload and surrounding timeline")

    unique_actions = list(dict.fromkeys(containment_actions))
    unique_evidence = list(dict.fromkeys(evidence_to_collect))
    unique_data = list(dict.fromkeys(data_at_risk)) or ["enterprise data pending classification"]
    if len(signals) >= 3 or ("data_exfiltration" in signals and "identity_abuse" in signals):
        risk_level = "critical"
    elif len(signals) == 2:
        risk_level = "high"
    elif signals == ["needs_more_context"]:
        risk_level = "low"
    else:
        risk_level = "medium"

    return {
        "product": DATASHIELD_NAME,
        "risk_level": risk_level,
        "signals": signals,
        "telemetry_sources": DATASHIELD_TELEMETRY_SOURCES,
        "data_at_risk": unique_data,
        "kill_chain": kill_chain,
        "containment_actions": unique_actions,
        "evidence_to_collect": unique_evidence,
        "business_impact": (
            "Enterprise data exposure, account takeover, regulatory reporting, and downtime risk increase "
            "if containment waits for static signature verdicts."
        ),
        "executive_brief": (
            f"{DATASHIELD_NAME} correlates identity, DLP, endpoint, SaaS, and storage telemetry to stop "
            f"data exfiltration before breach. Current risk: {risk_level}."
        ),
    }


def run_defender_council(
    telemetry: str,
    *,
    roles: Iterable[str] | None = None,
    model: str | None = None,
    reasoning_effort: str = "none",
    max_completion_tokens: int = 768,
    image_url: str | None = None,
    image_data_uri: str | None = None,
) -> dict[str, Any]:
    """Run one Cerebras completion per Aegis defender role and attach deterministic pre-triage."""
    defense_plan = draft_enterprise_defense_plan(telemetry)
    selected_roles = list(roles or DEFENDER_ROLES.keys())
    results: list[ProviderResult] = []
    for role in selected_roles:
        prompt = build_defender_prompt(role, telemetry, static_plan=defense_plan)
        result = call_cerebras(
            prompt,
            image_url=image_url,
            image_data_uri=image_data_uri,
            model=model,
            reasoning_effort=reasoning_effort,
            max_completion_tokens=max_completion_tokens,
        )
        result.provider = f"cerebras:defender:{role}"
        results.append(result)
    packet = summarize_agent_results(results)
    packet["defense_plan"] = defense_plan
    packet["defender_roles"] = selected_roles
    packet["product_brief"] = get_datashield_product_brief()
    return packet


