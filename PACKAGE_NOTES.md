# Gemma Aegis GitHub-Ready Package

Sanitized package for the current Gemma Aegis v6 product.

## Included
- `gemma_hack/` backend and server-side Gemma 4 proxy.
- `web/v6/` UI/UX shell, runtime, Aegis core, and emotes.
- `tests/` unit and route coverage using fake redaction fixtures only.
- `scripts/`, `demo_scenarios/`, sanitized assets, README, requirements.
- `.env.example`, `.gitignore`, `SECURITY.md`, and run helpers.

## Excluded
- `.env`, real API keys, benchmark logs, server logs, model weights, `models/`, `logs/`, `.git/`, caches, virtualenvs.
- Dogfood screenshots/reports and local autopilot state.
- Previous zip files, raw handoff folders, and build artifacts.

## Run on Windows
```cmd
RUN_WINDOWS.cmd
```
Open: `http://127.0.0.1:8765`

## Run on Linux/macOS
```bash
./RUN_LINUX_MAC.sh
```
