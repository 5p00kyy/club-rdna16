#!/usr/bin/env bash
set -euo pipefail

LLAMA_CPP_BIN="${LLAMA_CPP_BIN:-$HOME/Llama/llama.cpp/build/bin/llama-server}"
MODELS_DIR="${MODELS_DIR:-models}"
PRESETS_FILE="${PRESETS_FILE:-presets.ini}"
PORT="${PORT:-8088}"
API_KEY="${LLAMA_API_KEY:-test}"

exec "$LLAMA_CPP_BIN" \
  --host 127.0.0.1 \
  --port "$PORT" \
  --models-dir "$MODELS_DIR" \
  --models-preset "$PRESETS_FILE" \
  --api-key "$API_KEY" \
  --models-max 1 \
  --no-mmap \
  --no-warmup
