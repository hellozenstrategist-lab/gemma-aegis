#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="$ROOT/models/gemma-4-E2B-it-q4_0-gguf/gemma-4-E2B_q4_0-it.gguf"
PROMPT="${*:-Triage this enterprise data incident in 5 bullets.}"

exec llama-cli \
  -m "$MODEL" \
  -p "$PROMPT" \
  -n "${LOCAL_GEMMA_TOKENS:-256}" \
  --temp "${LOCAL_GEMMA_TEMP:-0.2}" \
  --ctx-size "${LOCAL_GEMMA_CTX:-2048}" \
  --threads "${LOCAL_GEMMA_THREADS:-8}" \
  --device "${LOCAL_GEMMA_DEVICE:-Vulkan0}" \
  --split-mode none \
  --gpu-layers "${LOCAL_GEMMA_GPU_LAYERS:-99}" \
  -st --reasoning off --no-display-prompt --no-warmup
