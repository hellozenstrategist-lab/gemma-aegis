# Gemma Aegis — Gemma 4 x Cerebras Hackathon Build

Always-on blue-team defender swarm for enterprise data, powered by Gemma 4 31B on Cerebras.

Core pitch: **Static virus detectors are too slow/dumb.** Gemma Aegis watches identity, DLP, endpoint, SaaS, and storage telemetry, then coordinates defender agents to stop data exfiltration before breach.

Built to win the useful parts of judging:

- **Track 1:** multi-agent/multimodal shape: screenshot/log input -> agent-style triage sections.
- **Track 3:** enterprise impact: incident response / cyber triage / knowledge workflow.
- **Blue-team product thesis:** Gemma 4 as an always-on defender swarm for enterprise data, replacing static virus-detector thinking with live reasoning over identity, DLP, endpoint, and data-store telemetry.
- **Speed proof:** UI exposes wall-clock latency, token stats, and optional baseline panel.

## Critical hackathon facts

- Model ID: `gemma-4-31b`
- Preview/elevated access requires Org ID form by **Sat Jun 27, 7:00 PM PT**.
- Event: **Sun Jun 28 10:00 AM PT -> Mon Jun 29 10:00 AM PT**.
- Submission: Discord track channel(s), 60s demo video, project description.

## Run

```bash
cd /home/jinjin/kitsune-security/hackathons/gemma4-cerebras-20260628-prep
python3 -m pip install -r requirements.txt
# .env is auto-loaded if present; export also works.
PYTHONPATH=. python3 -m gemma_hack.server --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

CLI smoke:

```bash
# .env is auto-loaded if present; export also works.
PYTHONPATH=. python3 scripts/smoke.py --reasoning none
```

Gemma 4 council eval:

```bash
PYTHONPATH=. python3 scripts/eval_demo.py --model gemma-4-31b --roles triage,blast_radius,remediation,evidence --reasoning none
```

Gemma Aegis defender swarm:

```bash
# In the UI, click "Load Aegis exfil demo", then run mode "Aegis defender swarm".
# The product brief is available at /api/datashield-brief.
# The deterministic pre-triage plan is also available from Python:
python3 - <<'PY'
from gemma_hack.defender import draft_enterprise_defense_plan, load_blue_team_scenario
print(draft_enterprise_defense_plan(load_blue_team_scenario()))
PY
```

If this returns `Model gemma-4-31b does not exist or you do not have access to it`, the key is not yet on Gemma preview. Do not treat fallback-model output as submission evidence.

Benchmark summary for submission copy (Gemma 4 product evidence only; non-Gemma rows are labeled SDK/key health checks, not submission proof):

```bash
PYTHONPATH=. python3 scripts/benchmark_summary.py --limit 3
```

After Gemma preview opens:

```bash
PYTHONPATH=. python3 scripts/eval_demo.py --model gemma-4-31b --roles triage,blast_radius,remediation,evidence
```

## Optional baseline panel

Use any OpenAI-compatible provider for side-by-side latency:

```bash
export BASELINE_OPENAI_BASE_URL='https://api.openai.com/v1'
export BASELINE_OPENAI_API_KEY='***'
export BASELINE_MODEL='gpt-4o-mini'
```

Then check **Run optional baseline too** in the UI.

## Privacy / recording discipline

- API keys are read from env only.
- Logs redact `csk-*` and `sk-*` shaped secrets.
- Uploaded image files are converted in-browser to a data URI and sent to the API; the local file is not written to disk by this app.
- Before recording, close Discord notifications, browser tabs with secrets, email, and terminals showing keys.

## What is already prepared

- Vanilla Python stdlib web UI, no JS build step.
- Cerebras SDK wrapper.
- OpenAI-compatible multimodal message builder.
- 4-agent incident council: triage, blast radius, remediation, evidence.
- Gemma Aegis product shell: pitch, four named defender agents, product brief endpoint, v6 UI/UX shell, and Aegis UI copy.
- v6 UI/UX handoff wired as the default route: `/` and `/v6/` serve the boxless Aegis/Gemma interface; `/classic` keeps the previous form UI available.
- Server-side Gemma chat proxy: `/api/datashield-chat` keeps the Cerebras key out of browser code while preserving chat-driven navigation and Evidence Vault report generation.
- Live v6 data endpoint: `/api/datashield-state` feeds defender pages, exec brief, containment, telemetry, evidence, and metric strips from the Aegis planner/benchmark state.
- Defender swarm agents: Data Sentinel, Identity Guardian, Endpoint Hunter, Response Orchestrator.
- Deterministic pre-triage planner for enterprise data risk before Gemma adds live judgment.
- Demo scenario: `demo_scenarios/blue_team_defender.md` with finance admin impossible travel, malicious OAuth, S3 export spike, DLP payroll/bank-account staging, PowerShell download cradle, and lateral RDP with service account.
- Model selector defaults to contest model `gemma-4-31b`; non-Gemma models are SDK/key health checks only, not submission evidence.
- Benchmark JSONL logger: `logs/benchmarks.jsonl`.
- Submission-ready benchmark summary formatter: `scripts/benchmark_summary.py`.
- Optional baseline wrapper.
- Demo scenario: `demo_scenarios/incident_sample.md`.
- One-click sanitized synthetic screenshot/data-URI asset in the UI via `/api/demo-image` for Track 1 multimodal demos without customer screenshots.
- Autopilot scripts: `scripts/eval_demo.py`, `scripts/benchmark_summary.py`, `scripts/heartbeat.py`, `scripts/autopilot_snapshot.py`.
- Tests: `python3 -m unittest discover -s tests -v`.

## 24h launch checklist

1. Confirm Org ID form submitted for each teammate.
2. At 10:30 PT, verify `gemma-4-31b` works with the approved key:
   ```bash
   PYTHONPATH=. python3 scripts/smoke.py 'Say ready in one sentence.'
   ```
3. Record 2-3 benchmark rows with the final demo prompt.
4. Add real multimodal screenshot input if available.
5. Add visible agent roles in the UI or project copy:
   - Triage agent
   - Blast-radius agent
   - Remediation agent
   - Evidence/reporting agent
6. Record 60s video:
   - 0-5s: problem / enterprise incident
   - 5-20s: run Gemma 4 on Cerebras
   - 20-35s: show multi-agent sections and metrics
   - 35-50s: optional baseline latency comparison
   - 50-60s: impact: faster response, fewer downtime minutes, clearer action
7. Submit separate Discord posts for Track 1 and Track 3.

## Suggested submission copy

**Title:** Gemma Aegis: Always-On Blue Team Defender Agents on Cerebras

**Description:**
Gemma Aegis is an always-on blue-team defender swarm for enterprise data. Instead of static virus-detector signatures, Gemma 4 watches identity, DLP, endpoint, SaaS, and storage telemetry, then coordinates four defender agents: data sentinel, identity guardian, endpoint hunter, and response orchestrator. The system turns red-team pressure into immediate containment, evidence capture, and business-impact briefings while Cerebras makes the workflow fast enough to stay in the incident loop.

**Tracks:**
- Track 1: Multiverse Agents — agent-style collaboration + multimodal input.
- Track 3: Enterprise Impact — incident response / cybersecurity / knowledge management.


