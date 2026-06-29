# Gemma Aegis

Gemma Aegis is an always-on blue-team defender swarm for enterprise data, powered by Gemma 4 31B on Cerebras.

Static security tools are good at matching known signatures. Gemma Aegis is built for the messier moment in an incident: identity abuse, suspicious SaaS grants, endpoint activity, DLP alerts, and storage exports all arriving at once. It turns those signals into a coordinated containment plan, evidence checklist, and executive brief fast enough to stay in the response loop.

## What Judges Should Try

1. Run the app and open `http://127.0.0.1:8765`.
2. Click the floating Aegis core or type anywhere to open chat.
3. Ask a normal question, such as `What are you watching right now?`.
4. Ask for a page only when intentional, such as `go to telemetry` or `open evidence`.
5. Open `/classic`, click **Load Aegis exfil demo**, and run the **Aegis defender swarm** mode.
6. Review the defender output, latency metrics, Evidence Vault, and executive brief.

## Demo Pitch

**Problem:** enterprise breaches are rarely one clean alert. They are a messy chain across identity, endpoint, SaaS, DLP, and storage.

**Solution:** Gemma Aegis runs four defender agents:

- **Data Sentinel:** identifies sensitive data at risk.
- **Identity Guardian:** catches impossible travel, OAuth abuse, and session risk.
- **Endpoint Hunter:** links workstation, PowerShell, EDR, and lateral movement.
- **Response Orchestrator:** produces containment steps, evidence collection, and leadership summary.

**Impact:** faster containment, clearer evidence preservation, and a briefing that security and leadership can both act on.

## Quick Start

### Windows

```cmd
copy .env.example .env
REM Edit .env and set CEREBRAS_API_KEY
RUN_WINDOWS.cmd
```

### macOS / Linux

```bash
cp .env.example .env
# Edit .env and set CEREBRAS_API_KEY
./RUN_LINUX_MAC.sh
```

Open:

```text
http://127.0.0.1:8765
```

To expose the demo to another machine on the same LAN, run the server with `--host 0.0.0.0` and open `http://YOUR-LAN-IP:8765` from the second machine. `127.0.0.1` is localhost only.

## Configuration

Required:

```text
CEREBRAS_API_KEY=your-key
CEREBRAS_MODEL=gemma-4-31b
```

Optional baseline comparison:

```text
BASELINE_OPENAI_BASE_URL=https://api.openai.com/v1
BASELINE_OPENAI_API_KEY=your-baseline-key
BASELINE_MODEL=gpt-4o-mini
```

The browser never receives the Cerebras API key. All Gemma calls go through the local Python server.

## Useful Routes

- `/` - polished Gemma Aegis judge demo.
- `/classic` - benchmark/control panel with scenario loader and latency metrics.
- `/api/datashield-chat` - server-side Gemma chat proxy.
- `/api/datashield-state` - live UI data model for defender pages.
- `/api/datashield-brief` - product and agent brief.
- `/api/blue-team-scenario` - sanitized exfiltration demo scenario.
- `/api/demo-image` - sanitized synthetic screenshot for multimodal demos.

The `datashield` route names are kept for compatibility with earlier demo agents.

## Safety And Privacy

- Real API keys belong in `.env`, which is ignored by git.
- `.env.example` is safe to commit and contains placeholders only.
- Logs redact `csk-*` and `sk-*` shaped secrets.
- Uploaded screenshots are converted in-browser to a data URI for the request; this app does not write the uploaded file to disk.
- Demo telemetry is synthetic and sanitized.
- Containment steps are recommendations for the demo; the app does not execute destructive actions against real services.

## Validation

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

Run a smoke test:

```bash
PYTHONPATH=. python scripts/smoke.py "Say ready in one sentence."
```

If Cerebras returns a model-access error for `gemma-4-31b`, the key is not attached to an account with Gemma 4 access. That is an account/model access issue, not a browser or localhost issue.

## 60-Second Demo Flow

0-5 seconds: show the problem: enterprise data breach signals across identity, endpoint, SaaS, DLP, and storage.

5-20 seconds: run Gemma 4 on Cerebras through the Aegis defender swarm.

20-35 seconds: show the four agent findings and latency/token metrics.

35-50 seconds: open containment, evidence, and executive brief pages.

50-60 seconds: close with the business impact: faster containment, preserved evidence, and clearer leadership action.

## Suggested Submission Copy

**Title:** Gemma Aegis: Always-On Blue-Team Defender Agents on Cerebras

**Description:** Gemma Aegis is an always-on defender swarm for enterprise data. Gemma 4 watches identity, DLP, endpoint, SaaS, and storage telemetry, then coordinates four defender agents to identify data at risk, connect the attack chain, recommend containment, preserve evidence, and brief leadership. Cerebras makes the loop fast enough for incident response instead of after-action reporting.

**Tracks:** agent collaboration, multimodal incident triage, cybersecurity, enterprise impact.
