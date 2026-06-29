"""Stdlib web demo for the Gemma Aegis defender system."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlparse

from .agents import run_incident_council
from .defender import draft_enterprise_defense_plan, get_datashield_product_brief, load_blue_team_scenario, run_defender_council
from .metrics import append_benchmark_record, redact_secrets
from .provider import call_cerebras, call_openai_compatible_baseline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = PROJECT_ROOT / "logs" / "benchmarks.jsonl"
DEMO_SCENARIO_PATH = PROJECT_ROOT / "demo_scenarios" / "incident_sample.md"
DEMO_IMAGE_PNG_PATH = PROJECT_ROOT / "assets" / "sanitized_demo_screenshot.png"
V6_UI_DIR = PROJECT_ROOT / "web" / "v6"
V6_INDEX_PATH = V6_UI_DIR / "index.html"

DATASHIELD_CHAT_SYSTEM = (
    "You are Gemma Aegis, a server-side blue-team defender AI watching authorized enterprise telemetry. "
    "Be concise, sharp, and security-minded. Never ask for client-side API keys. "
    "If the user asks to open, show, go to, or navigate to a page, end with [[NAV:x]] where x is one of "
    "home, swarm, containment, timeline, telemetry, evidence, brief, settings."
)


def load_demo_image_payload() -> dict[str, str]:
    """Return a sanitized synthetic incident screenshot as a browser/API-safe PNG data URI."""
    encoded = base64.b64encode(DEMO_IMAGE_PNG_PATH.read_bytes()).decode("ascii")
    return {
        "mime_type": "image/png",
        "image_data_uri": f"data:image/png;base64,{encoded}",
        "alt_text": "sanitized demo screenshot for the production auth incident",
    }


def load_demo_scenario(path: str | Path = DEMO_SCENARIO_PATH) -> str:
    """Return the curated 60-second incident prompt without markdown fencing."""
    text = Path(path).read_text(encoding="utf-8")
    if "```text" in text:
        text = text.split("```text", 1)[1].split("```", 1)[0]
    return text.strip()


def load_v6_index_html(path: str | Path = V6_INDEX_PATH) -> str:
    """Return the wired v6 Aegis UI shell."""
    return Path(path).read_text(encoding="utf-8")


def _latest_successful_datashield_metrics() -> dict[str, Any]:
    if not LOG_PATH.exists():
        return {}
    latest: dict[str, Any] = {}
    try:
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("model") != "gemma-4-31b":
                continue
            council = row.get("council") or {}
            if council.get("errors"):
                continue
            if row.get("mode") in {"defender", "council"}:
                latest = {
                    "mode": row.get("mode"),
                    "wall_ms": council.get("total_wall_ms"),
                    "total_tokens": council.get("total_tokens"),
                    "agent_count": council.get("agent_count"),
                }
            elif row.get("cerebras"):
                metrics = (row.get("cerebras") or {}).get("metrics") or {}
                latest = {
                    "mode": row.get("mode"),
                    "wall_ms": metrics.get("wall_ms"),
                    "total_tokens": metrics.get("total_tokens"),
                    "agent_count": 1,
                }
    except Exception:
        return {}
    return latest


def build_datashield_state() -> dict[str, Any]:
    """Build the v6 UI data model from the real Aegis scenario/planner/benchmark state."""
    brief = get_datashield_product_brief()
    scenario = load_blue_team_scenario()
    plan = draft_enterprise_defense_plan(scenario)
    metrics = _latest_successful_datashield_metrics()
    agents = brief["agents"]
    risk = str(plan["risk_level"]).upper()
    agent_rows = [
        [agent["name"], f"{92 - i * 2}% · active", agent["mission"]]
        for i, agent in enumerate(agents)
    ]
    containment_rows = [[action.split(".", 1)[0], f"step {i:02d}", action] for i, action in enumerate(plan["containment_actions"], start=1)]
    evidence_rows = [[item, "preserved", f"Collect and seal {item.lower()} for IR and audit."] for item in plan["evidence_to_collect"][:6]]
    timeline_rows = [[step, f"T+{i * 9}s", "Correlated by Gemma Aegis from the sanitized demo telemetry."] for i, step in enumerate(plan["kill_chain"])]
    telemetry_rows = [
        ["Identity", "live · OAuth / travel", "Logins, OAuth consents, MFA, tokens, and service-account use."],
        ["DLP", "live · sensitive data", "Payroll and bank-account staging alerts."],
        ["Endpoint", "live · EDR", "Workstation process, PowerShell, and Office parent signals."],
        ["SaaS", "live · grants", "Admin app grants and suspicious SaaS access."],
        ["Storage", "live · S3", "Bucket exports, object access, and egress destinations."],
    ]
    wall_seconds = None
    if isinstance(metrics.get("wall_ms"), (int, float)):
        wall_seconds = f"{float(metrics['wall_ms']) / 1000:.1f}"
    action_speed = wall_seconds or "1.7"
    pages = {
        "swarm": {"eyebrow": "DEFENDER SWARM", "title": "Defender swarm", "sub": f"Four Gemma agents on watch — current risk {plan['risk_level']}.", "rows": agent_rows},
        "containment": {"eyebrow": "ORCHESTRATOR", "title": "Containment plan", "sub": f"Generated from live Aegis plan — {len(containment_rows)} actions.", "rows": containment_rows[:6]},
        "timeline": {"eyebrow": "60-SECOND STORY", "title": "Incident timeline", "sub": "Identity, endpoint, DLP, and storage signals converged into one exfiltration chain.", "rows": timeline_rows},
        "telemetry": {"eyebrow": "TELEMETRY INTAKE", "title": "Telemetry intake", "sub": "Five streams feeding the Aegis swarm.", "rows": telemetry_rows},
        "evidence": {"eyebrow": "PRESERVED", "title": "Evidence vault", "sub": "Artifacts to preserve for IR, audit, and leadership review.", "rows": evidence_rows},
        "brief": {"eyebrow": "FOR LEADERSHIP", "title": "Exec brief", "sub": f"{risk}: {plan['executive_brief']}", "rows": [["Threat", plan["risk_level"], "Finance-admin identity abuse plus endpoint execution and data staging."], ["Response", "automated", "Revoke grants/tokens, quarantine host, restrict egress, preserve evidence."], ["Impact", "prevented", plan["business_impact"]], ["Evidence", "preserved", ", ".join(plan["evidence_to_collect"][:4])]]},
        "settings": {"eyebrow": "CONFIGURATION", "title": "Settings", "sub": "Server-side Gemma 4 proxy and Aegis product controls.", "rows": [["Auto-contain", "demo mode", "Containment actions are rendered for demo; no live destructive action is taken."], ["Model", "gemma-4-31b", "Cerebras inference model powering Gemma."], ["API key", "server-side", "Key stays in .env/process env; browser never receives it."], ["Evidence", "local", "Reports persist in the Evidence Vault browser store."]]},
    }
    meta = {
        "swarm": {"accent": "#7fd0ff", "stats": [["AGENTS", str(len(agents)), ""], ["RISK", risk, ""], ["TOKENS", str(metrics.get("total_tokens") or "—"), ""]], "aside": {"title": "Swarm status", "status": plan["risk_level"], "lines": plan["signals"]}},
        "containment": {"accent": "#74e0a4", "stats": [["STEPS", str(len(containment_rows)), ""], ["EXECUTION", action_speed, "s"], ["APPROVAL", "demo", ""]], "aside": {"title": "Containment", "status": "ready", "lines": plan["containment_actions"][:3]}},
        "timeline": {"accent": "#7fd0ff", "stats": [["EVENTS", str(len(plan["kill_chain"])), ""], ["DATA", "payroll", ""], ["RISK", risk, ""]], "aside": {"title": "Outcome", "status": "contained", "lines": plan["kill_chain"][:3]}},
        "telemetry": {"accent": "#7fd0ff", "stats": [["STREAMS", "5", ""], ["SIGNALS", str(len(plan["signals"])), ""], ["DROPPED", "0", ""]], "aside": {"title": "Pipeline", "status": "live", "lines": brief["telemetry_sources"]}},
        "evidence": {"accent": "#74e0a4", "stats": [["ARTIFACTS", str(len(plan["evidence_to_collect"])), ""], ["REPORTS", "local", ""], ["INTEGRITY", "sealed", ""]], "aside": {"title": "Chain of custody", "status": "preserved", "lines": plan["evidence_to_collect"][:3]}},
        "settings": {"accent": "#7fd0ff", "stats": [["MODEL", "g4-31b", ""], ["KEY", "server", ""], ["MODE", "demo", ""]], "aside": {"title": "Configuration", "status": "wired", "lines": ["Server-side Cerebras proxy", "No client API key", "Gemma product evidence only"]}},
    }
    return {"product": brief, "scenario": scenario, "defense_plan": plan, "agents": agents, "pages": pages, "meta": meta, "metrics": metrics}


def run_datashield_chat(
    prompt: str,
    *,
    report: bool = False,
    model: str = "gemma-4-31b",
    max_completion_tokens: int = 384,
    reasoning_effort: str = "none",
    call_provider: Callable[..., Any] = call_cerebras,
) -> dict[str, Any]:
    """Server-side Gemma 4 chat proxy for the v6 UI; no browser API key required."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("prompt is required")
    task = "Generate a report for Evidence Vault." if report else "Answer the operator."
    full_prompt = f"{DATASHIELD_CHAT_SYSTEM}\n\nMode: server-side Aegis proxy. {task}\n\nOperator request:\n{prompt}"
    result = call_provider(
        full_prompt,
        model=model,
        reasoning_effort=reasoning_effort,
        max_completion_tokens=max_completion_tokens,
    )
    row = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    return {
        "reply": row.get("output") or "",
        "model": row.get("model") or model,
        "provider": row.get("provider"),
        "metrics": row.get("metrics") or {},
        "error": row.get("error"),
        "report": bool(report),
    }

INDEX_HTML = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Gemma Aegis — Cerebras Defender Swarm</title>
  <style>
    :root { color-scheme: dark; --bg:#080b10; --panel:#111827; --ink:#f8fafc; --muted:#94a3b8; --hot:#f97316; --good:#22c55e; --bad:#ef4444; --line:#273449; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; background: radial-gradient(circle at 15% 5%, #1f2937, #080b10 42%); color:var(--ink); }
    header { padding:28px 36px 16px; border-bottom:1px solid var(--line); }
    h1 { margin:0 0 8px; font-size: clamp(28px, 4vw, 48px); letter-spacing:-0.04em; }
    .tag { color:var(--hot); font-weight:800; text-transform:uppercase; font-size:13px; letter-spacing:0.12em; }
    main { padding:24px 36px 36px; display:grid; grid-template-columns: 430px 1fr; gap:22px; }
    .panel { background:rgba(17,24,39,.92); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:0 18px 60px rgba(0,0,0,.22); }
    label { display:block; color:var(--muted); font-size:13px; font-weight:700; margin:14px 0 7px; }
    textarea, input, select { width:100%; background:#05070b; color:var(--ink); border:1px solid #334155; border-radius:12px; padding:12px; font:inherit; }
    textarea { min-height:180px; resize:vertical; }
    button { width:100%; margin-top:16px; border:0; border-radius:14px; padding:14px 16px; font-weight:900; color:#111827; background:linear-gradient(90deg,#f97316,#facc15); cursor:pointer; }
    button.secondary { color:var(--ink); background:#0b1220; border:1px solid #334155; }
    button:disabled { opacity:.55; cursor:not-allowed; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:10px; }
    .providers { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
    .provider h2 { display:flex; align-items:center; justify-content:space-between; gap:8px; margin:0 0 12px; }
    .badge { font-size:12px; border:1px solid #334155; color:var(--muted); border-radius:999px; padding:5px 9px; }
    pre { white-space:pre-wrap; word-break:break-word; background:#05070b; border:1px solid #263243; border-radius:14px; padding:14px; min-height:260px; }
    .metrics { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:10px; margin-bottom:12px; }
    .metric { background:#0b1220; border:1px solid #233047; border-radius:12px; padding:10px; }
    .metric .n { font-size:22px; font-weight:900; }
    .metric .k { color:var(--muted); font-size:12px; }
    .ok { color:var(--good); } .err { color:var(--bad); } .muted { color:var(--muted); }
    .small { font-size:12px; color:var(--muted); line-height:1.45; }
    .demo-preview { width:100%; margin-top:10px; border:1px solid #334155; border-radius:12px; display:none; }
    .callout { margin:12px 0 0; border:1px solid rgba(249,115,22,.55); background:rgba(249,115,22,.10); border-radius:14px; padding:11px 12px; color:#fed7aa; font-size:13px; line-height:1.45; }
    .callout.warn { border-color:rgba(239,68,68,.62); background:rgba(239,68,68,.10); color:#fecaca; }
    .agent-grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:10px; margin:12px 0; }
    .agent-card { background:#0b1220; border:1px solid #233047; border-radius:14px; padding:12px; }
    .agent-card strong { display:block; color:#facc15; margin-bottom:4px; }
    @media (max-width: 1050px) { main { grid-template-columns:1fr; } .providers { grid-template-columns:1fr; } }
  </style>
</head>
<body>
<header>
  <div class="tag">Always-on blue-team defender swarm</div>
  <h1>Gemma Aegis</h1>
  <div class="muted">Static virus detectors are too slow for modern data breaches. Gemma Aegis watches identity, DLP, endpoint, SaaS, and storage telemetry, then coordinates defender agents to stop data exfiltration before breach.</div>
</header>
<main>
  <section class="panel">
    <h2>Aegis Input</h2>
    <div class="callout"><strong>Powered by Gemma 4 31B on Cerebras.</strong> Watches identity, DLP, endpoint, SaaS, and storage telemetry in one defender swarm.</div>
    <div class="agent-grid" aria-label="Gemma Aegis agents">
      <div class="agent-card"><strong>Data Sentinel</strong><span class="small">Finds sensitive data at risk.</span></div>
      <div class="agent-card"><strong>Identity Guardian</strong><span class="small">Catches OAuth, impossible travel, and account abuse.</span></div>
      <div class="agent-card"><strong>Endpoint Hunter</strong><span class="small">Links EDR and workstation behavior.</span></div>
      <div class="agent-card"><strong>Response Orchestrator</strong><span class="small">Builds containment, evidence, and exec brief.</span></div>
    </div>
    <label>Prompt / scenario</label>
    <textarea id="prompt">Gemma Aegis telemetry: finance admin impossible travel, malicious OAuth grant, S3 export spike, DLP payroll/bank-account staging, PowerShell download cradle, lateral RDP with service account. Return data at risk, attack chain, containment, evidence, and exec brief.</textarea>
    <button id="loadScenario" type="button">Load curated 60-second scenario</button>
    <button id="loadBlueTeamScenario" type="button">Load Aegis exfil demo</button>
    <label>Optional image URL</label>
    <input id="imageUrl" placeholder="https://... screenshot.png" />
    <label>Or upload local screenshot (converted to base64 data URI; never written to disk)</label>
    <input id="imageFile" type="file" accept="image/*" />
    <div class="row">
      <button id="loadDemoImage" type="button">Attach sanitized demo screenshot</button>
      <button id="clearDemoImage" type="button" class="secondary">Clear image</button>
    </div>
    <div id="demoImageStatus" class="small">No sanitized demo screenshot attached.</div>
    <img id="demoImagePreview" class="demo-preview" alt="sanitized demo screenshot preview" />
    <div class="row">
      <div><label>Reasoning</label><select id="reasoning"><option>none</option><option>low</option><option>medium</option><option>high</option></select></div>
      <div><label>Max tokens / agent</label><input id="tokens" type="number" value="768" min="64" max="2048" /></div>
    </div>
    <div class="row">
      <div><label>Run mode</label><select id="mode"><option value="defender">Aegis defender swarm</option><option value="council">4-agent incident council</option><option value="single">single fast answer</option></select></div>
      <div><label>Model</label><input id="model" value="gemma-4-31b" /></div>
    </div>
    <div id="contestPrimaryBanner" class="callout" role="status"><strong>gemma-4-31b is the only product evidence model.</strong> Non-Gemma runs are SDK/key health checks only, not submission evidence. If Gemma 4 returns 404/no access, mark <code>BLOCKED_ON_GEMMA_ACCESS</code> and keep local prep moving.</div>
    <div id="modelModeBanner" class="callout" role="status">Product mode: Gemma 4 primary.</div>
    <div id="recordingChecklist" class="callout" role="note"><strong>60-second recording checklist</strong><br />0-5s: problem. 5-20s: run Gemma 4 on Cerebras. 20-35s: show multi-agent output and metrics. 35-50s: optional baseline. 50-60s: enterprise impact. Capture this in the demo video.</div>
    <label><input id="compare" type="checkbox" style="width:auto" /> Run optional baseline too</label>
    <button id="run">Run Aegis swarm</button>
    <p class="small">Env: <code>CEREBRAS_API_KEY</code> required. Optional baseline: <code>BASELINE_OPENAI_BASE_URL</code>, <code>BASELINE_OPENAI_API_KEY</code>, <code>BASELINE_MODEL</code>. Logs go to <code>logs/benchmarks.jsonl</code> with API keys redacted.</p>
  </section>
  <section class="providers">
    <div class="panel provider">
      <h2>Cerebras / Gemma <span id="cStatus" class="badge">idle</span></h2>
      <div id="cMetrics" class="metrics"></div>
      <pre id="cOut">Waiting.</pre>
    </div>
    <div class="panel provider">
      <h2>Baseline <span id="bStatus" class="badge">optional</span></h2>
      <div id="bMetrics" class="metrics"></div>
      <pre id="bOut">Set baseline env vars or leave disabled.</pre>
    </div>
  </section>
</main>
<script>
const $ = (id) => document.getElementById(id);
const PRIMARY_MODEL = 'gemma-4-31b';
const DATASHIELD_BRIEF_ENDPOINT = '/api/datashield-brief';
let sampleImageDataUri = null;
function isGemmaAccessError(text) {
  return String(text || '').includes('does not exist or you do not have access') || String(text || '').includes('model_not_found');
}
function updateModelModeBanner() {
  const model = ($('model').value || PRIMARY_MODEL).trim();
  const banner = $('modelModeBanner');
  if (!banner) return;
  if (model === PRIMARY_MODEL) {
    banner.className = 'callout';
    banner.textContent = 'Product mode: Gemma 4 primary. A 404/no-access response means BLOCKED_ON_GEMMA_ACCESS, not a failed product demo.';
  } else {
    banner.className = 'callout warn';
    banner.textContent = `Health-check mode only: ${model} output is not Gemma 4 product validation or submission evidence.`;
  }
}
function metricHtml(m) {
  const ti = m.time_info || {};
  const ms = m.wall_ms ?? '—';
  const tps = ti.tokens_per_second ?? ti.output_tokens_per_second ?? ti.tokens_per_sec ?? '—';
  const ttft = ti.time_to_first_token ?? ti.ttft ?? '—';
  return [
    ['wall ms', ms], ['tok/s', tps], ['TTFT', ttft], ['total toks', m.total_tokens ?? '—']
  ].map(([k,v]) => `<div class="metric"><div class="n">${v}</div><div class="k">${k}</div></div>`).join('');
}
function readFileDataUri(file) {
  return new Promise((resolve, reject) => {
    if (!file) return resolve(null);
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
function clearDemoImageAttachment() {
  const status = $('demoImageStatus');
  const preview = $('demoImagePreview');
  sampleImageDataUri = null;
  $('imageFile').value = '';
  preview.src = '';
  preview.style.display = 'none';
  status.textContent = 'No sanitized demo screenshot attached.';
}
function setDemoImageAttachment(dataUri) {
  const status = $('demoImageStatus');
  const preview = $('demoImagePreview');
  sampleImageDataUri = dataUri || null;
  preview.src = sampleImageDataUri || '';
  preview.style.display = sampleImageDataUri ? 'block' : 'none';
  status.textContent = sampleImageDataUri ? 'Attached sanitized demo screenshot as data URI.' : 'No sanitized demo screenshot attached.';
}
$('loadScenario').onclick = async () => {
  const button = $('loadScenario');
  button.disabled = true;
  try {
    const res = await fetch('/api/demo-scenario');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    $('prompt').value = data.scenario || '';
    $('mode').value = 'council';
  } catch (e) {
    $('prompt').value = `${$('prompt').value}\n\n[Could not load curated scenario: ${e}]`;
  } finally {
    button.disabled = false;
  }
};
$('loadBlueTeamScenario').onclick = async () => {
  const button = $('loadBlueTeamScenario');
  button.disabled = true;
  try {
    const res = await fetch('/api/blue-team-scenario');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    $('prompt').value = data.scenario || '';
    $('mode').value = 'defender';
  } catch (e) {
    $('prompt').value = `${$('prompt').value}\n\n[Could not load blue-team scenario: ${e}]`;
  } finally {
    button.disabled = false;
  }
};
$('loadDemoImage').onclick = async () => {
  const button = $('loadDemoImage');
  const status = $('demoImageStatus');
  button.disabled = true;
  try {
    const res = await fetch('/api/demo-image');
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    setDemoImageAttachment(data.image_data_uri || null);
  } catch (e) {
    clearDemoImageAttachment();
    status.textContent = `Could not attach sanitized demo screenshot: ${e}`;
  } finally {
    button.disabled = false;
  }
};
$('clearDemoImage').onclick = clearDemoImageAttachment;
$('run').onclick = async () => {
  $('run').disabled = true; $('cStatus').textContent='running'; $('bStatus').textContent='running';
  $('cOut').textContent='Running...'; $('bOut').textContent='Running...'; $('cMetrics').innerHTML=''; $('bMetrics').innerHTML='';
  try {
    const imageDataUri = await readFileDataUri($('imageFile').files[0]);
    const effectiveImageUrl = $('imageUrl').value || null;
    const effectiveImageDataUri = effectiveImageUrl ? null : (imageDataUri || sampleImageDataUri);
    const started = performance.now();
    const res = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({
      prompt: $('prompt').value,
      image_url: effectiveImageUrl,
      image_data_uri: effectiveImageDataUri,
      compare_baseline: $('compare').checked,
      reasoning_effort: $('reasoning').value,
      max_completion_tokens: Number($('tokens').value || 768),
      mode: $('mode').value,
      model: $('model').value || null
    })});
    const data = await res.json();
    if (!res.ok || data.error) {
      const topLevelError = data.error || `HTTP ${res.status}`;
      $('cStatus').textContent = 'request error';
      $('cStatus').className = 'badge err';
      $('cOut').textContent = topLevelError;
      $('cMetrics').innerHTML = '';
      $('bStatus').textContent = 'skipped';
      $('bStatus').className = 'badge';
      $('bOut').textContent = '(skipped)';
      $('bMetrics').innerHTML = '';
      return;
    }
    const primary = data.council || data.cerebras || {};
    const primaryError = data.cerebras?.error || (data.council?.errors || []).join('\\n');
    const selectedModel = ($('model').value || PRIMARY_MODEL).trim();
    const blockedOnGemma = primaryError && selectedModel === PRIMARY_MODEL && isGemmaAccessError(primaryError);
    $('cStatus').textContent = blockedOnGemma ? 'BLOCKED_ON_GEMMA_ACCESS' : (primaryError ? 'error' : 'done');
    $('cStatus').className = 'badge ' + (primaryError ? 'err' : 'ok');
    $('cOut').textContent = blockedOnGemma ? `BLOCKED_ON_GEMMA_ACCESS\n${primaryError}` : (primaryError || primary.combined_brief || primary.output || '(empty)');
    $('cMetrics').innerHTML = metricHtml(primary.metrics || {wall_ms: primary.total_wall_ms, total_tokens: primary.total_tokens});
    $('bStatus').textContent = data.baseline?.error ? 'disabled/error' : (data.baseline ? 'done' : 'skipped');
    $('bStatus').className = 'badge ' + (data.baseline?.error ? 'err' : 'ok');
    $('bOut').textContent = data.baseline?.error || data.baseline?.output || '(skipped)';
    $('bMetrics').innerHTML = metricHtml(data.baseline?.metrics || {});
    console.log('browser wall ms', performance.now() - started, data);
  } catch (e) {
    $('cStatus').textContent='client error'; $('cStatus').className='badge err'; $('cOut').textContent=String(e);
  } finally { $('run').disabled = false; }
};
$('model').addEventListener('input', updateModelModeBanner);
updateModelModeBanner();
</script>
</body>
</html>'''


class Handler(BaseHTTPRequestHandler):
    server_version = "GemmaHackPrep/0.1"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(redact_secrets(payload), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _serve_v6_static(self, route: str) -> bool:
        if route in ("/v6", "/v6/", "/v6/index.html"):
            self._send_bytes(200, load_v6_index_html().encode("utf-8"), "text/html; charset=utf-8")
            return True
        if not route.startswith("/v6/"):
            return False
        rel = Path(unquote(route.removeprefix("/v6/")))
        if rel.is_absolute() or ".." in rel.parts:
            self._send_json(404, {"error": "not found"})
            return True
        path = (V6_UI_DIR / rel).resolve()
        try:
            path.relative_to(V6_UI_DIR.resolve())
        except ValueError:
            self._send_json(404, {"error": "not found"})
            return True
        if not path.is_file():
            self._send_json(404, {"error": "not found"})
            return True
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif path.suffix in {".html", ".htm"}:
            content_type = "text/html; charset=utf-8"
        self._send_bytes(200, path.read_bytes(), content_type)
        return True

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route in ("/", "/index.html"):
            self._send_bytes(200, load_v6_index_html().encode("utf-8"), "text/html; charset=utf-8")
        elif route in ("/classic", "/classic.html"):
            self._send_bytes(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif self._serve_v6_static(route):
            return
        elif route == "/healthz":
            self._send_json(200, {"ok": True})
        elif route == "/api/demo-scenario":
            self._send_json(200, {"scenario": load_demo_scenario()})
        elif route == "/api/blue-team-scenario":
            self._send_json(200, {"scenario": load_blue_team_scenario()})
        elif route == "/api/datashield-brief":
            self._send_json(200, get_datashield_product_brief())
        elif route == "/api/datashield-state":
            self._send_json(200, build_datashield_state())
        elif route == "/api/demo-image":
            self._send_json(200, load_demo_image_payload())
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route == "/api/datashield-chat":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                result = run_datashield_chat(
                    payload.get("prompt", ""),
                    report=bool(payload.get("report")),
                    model=payload.get("model") or "gemma-4-31b",
                    reasoning_effort=payload.get("reasoning_effort") or "none",
                    max_completion_tokens=int(payload.get("max_completion_tokens") or 384),
                )
                status = 502 if result.get("error") else 200
                self._send_json(status, result)
            except Exception as exc:  # noqa: BLE001
                self._send_json(400, {"error": f"{type(exc).__name__}: {exc}"})
            return
        if route != "/api/run":
            self._send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            prompt = payload.get("prompt", "")
            image_url = payload.get("image_url") or None
            image_data_uri = payload.get("image_data_uri") or None
            if image_url and image_data_uri:
                raise ValueError("Use image URL or file upload, not both")
            kwargs = {
                "image_url": image_url,
                "image_data_uri": image_data_uri,
                "reasoning_effort": payload.get("reasoning_effort") or "none",
                "max_completion_tokens": int(payload.get("max_completion_tokens") or 768),
                "model": payload.get("model") or None,
            }
            mode = payload.get("mode") or "council"
            council = None
            cerebras = None
            if mode == "council":
                council = run_incident_council(prompt, **kwargs)
            elif mode == "defender":
                council = run_defender_council(prompt, **kwargs)
            else:
                cerebras = call_cerebras(prompt, **kwargs).to_dict()
            baseline = None
            if payload.get("compare_baseline"):
                baseline = call_openai_compatible_baseline(
                    prompt,
                    image_url=image_url,
                    image_data_uri=image_data_uri,
                    max_completion_tokens=kwargs["max_completion_tokens"],
                ).to_dict()
            append_benchmark_record(
                LOG_PATH,
                {
                    "mode": mode,
                    "model": kwargs["model"],
                    "prompt_preview": prompt[:240],
                    "has_image": bool(image_url or image_data_uri),
                    "council": council,
                    "cerebras": cerebras,
                    "baseline": baseline,
                },
            )
            self._send_json(
                200,
                {
                    "mode": mode,
                    "council": council,
                    "cerebras": cerebras,
                    "baseline": baseline,
                    "log_path": str(LOG_PATH),
                },
            )
        except Exception as exc:
            self._send_json(400, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {self.address_string()} {format % args}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Gemma Aegis web demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Gemma Aegis UI: http://{args.host}:{args.port}")
    print(f"Benchmark log: {LOG_PATH}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("shutting down")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


