#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; echo "Created .env — edit CEREBRAS_API_KEY before running Gemma calls."; fi
PYTHONPATH=. python3 -m gemma_hack.server --host "${HOST:-127.0.0.1}" --port "${PORT:-8765}"

