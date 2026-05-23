#!/usr/bin/env bash
set -euo pipefail

URL=""
MODEL=""
INCLUDE_BENCH=1

sanitize_stream() {
  sed -E \
    -e 's/(Bearer )[A-Za-z0-9._-]{10,}/\1<redacted>/g' \
    -e 's/(hf_|sk-)[A-Za-z0-9._-]{10,}/\1<redacted>/g' \
    -e 's#(https?://)[^/ ]+#\1<redacted-host>#g' \
    -e 's#/(home|Users|root)/[^[:space:]'"'"'"\\]+#/<redacted-path>#g' \
    -e 's/\b(192\.168|10\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1]))(\.[0-9]{1,3}){2}\b/<private-ip>/g'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      URL="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --no-bench)
      INCLUDE_BENCH=0
      shift
      ;;
    -h|--help)
      echo "Usage: bash scripts/report.sh [--url http://127.0.0.1:8000] [--model model-name] [--no-bench]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

BASE_URL=$(printf '%s' "$URL" | sed 's#/*$##')
if [[ "$BASE_URL" == */v1 ]]; then
  API_BASE="$BASE_URL"
  HEALTH_BASE=$(printf '%s' "$BASE_URL" | sed 's#/v1$##')
else
  API_BASE="$BASE_URL/v1"
  HEALTH_BASE="$BASE_URL"
fi

echo "# club-rdna16 result report"
echo
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
echo "## Hardware"
echo
if command -v rocm-smi >/dev/null 2>&1; then
  echo '~~~text'
  rocm-smi --showproductname --showmeminfo vram --showuse --showpower --showclocks || true
  echo '~~~'
elif command -v rocminfo >/dev/null 2>&1; then
  echo '~~~text'
  rocminfo | grep -E 'Name:|Marketing Name|gfx|Uuid' | head -80 || true
  echo '~~~'
elif command -v vulkaninfo >/dev/null 2>&1; then
  echo '~~~text'
  vulkaninfo --summary | sed -n '/Devices:/,$p' | head -80 || true
  echo '~~~'
else
  echo "No ROCm/Vulkan GPU inventory tool found."
fi
echo
if [[ -r /sys/class/dmi/id/product_name ]]; then
  echo "System: $(cat /sys/class/dmi/id/product_name)"
fi
if [[ -r /sys/class/dmi/id/board_vendor && -r /sys/class/dmi/id/board_name ]]; then
  echo "Motherboard: $(cat /sys/class/dmi/id/board_vendor) $(cat /sys/class/dmi/id/board_name)"
fi
if command -v lscpu >/dev/null 2>&1; then
  CPU_MODEL=$(lscpu | awk -F: '/Model name/ {gsub(/^[ \t]+/, "", $2); print $2; exit}')
  if [[ -n "$CPU_MODEL" ]]; then
    echo "CPU: $CPU_MODEL"
  else
    echo "CPU: $(uname -m)"
  fi
else
  echo "CPU: $(uname -m)"
fi
echo "Kernel: $(uname -sr)"
if command -v free >/dev/null 2>&1; then
  echo "RAM: $(free -h | awk '/^Mem:/ {print $2}')"
fi
echo
echo "## Endpoint"
echo
if [[ -n "$URL" ]]; then
  echo "- Endpoint provided: yes"
else
  echo "- Endpoint provided: no"
fi
if [[ -n "$MODEL" ]]; then
  echo "- Model: $MODEL"
else
  echo "- Model: not provided"
fi
echo
if [[ -n "$URL" ]]; then
  echo "### Health"
  echo
  if HEALTH_HTTP_CODE=$(curl -sS --max-time 10 -o /tmp/clubrdna16-health.$$ -w "%{http_code}" "$HEALTH_BASE/health" 2>/tmp/clubrdna16-health-err.$$); then
    if [[ "$HEALTH_HTTP_CODE" == "200" ]]; then
      echo "- Health check: ok (HTTP 200)"
    else
      echo "- Health check: unexpected status (HTTP $HEALTH_HTTP_CODE)"
    fi
  else
    echo "- Health check: failed"
    if [[ -s /tmp/clubrdna16-health-err.$$ ]]; then
      echo "- Error:"
      echo '~~~text'
      sanitize_stream < /tmp/clubrdna16-health-err.$$
      echo '~~~'
    fi
  fi
  rm -f /tmp/clubrdna16-health.$$ /tmp/clubrdna16-health-err.$$
fi
echo
if [[ -n "$URL" && -n "$MODEL" && "$INCLUDE_BENCH" -eq 1 ]]; then
  echo "### Smoke"
  echo
  echo '~~~json'
  if python3 scripts/openai_compat_smoke.py --base-url "$API_BASE" --model "$MODEL" >/tmp/clubrdna16-smoke.$$ 2>/tmp/clubrdna16-smoke-err.$$; then
    sanitize_stream < /tmp/clubrdna16-smoke.$$
  else
    sanitize_stream < /tmp/clubrdna16-smoke.$$
    sanitize_stream < /tmp/clubrdna16-smoke-err.$$ || true
  fi
  echo '~~~'
  echo
  echo "### Decode Bench"
  echo
  echo '~~~json'
  if python3 scripts/simple_decode_bench.py --base-url "$API_BASE" --model "$MODEL" --max-tokens 256 >/tmp/clubrdna16-decode.$$ 2>/tmp/clubrdna16-decode-err.$$; then
    sanitize_stream < /tmp/clubrdna16-decode.$$
  else
    sanitize_stream < /tmp/clubrdna16-decode.$$
    sanitize_stream < /tmp/clubrdna16-decode-err.$$ || true
  fi
  echo '~~~'
  rm -f /tmp/clubrdna16-smoke.$$ /tmp/clubrdna16-smoke-err.$$ /tmp/clubrdna16-decode.$$ /tmp/clubrdna16-decode-err.$$
fi
echo
echo "## Launch Config"
echo
echo "Paste sanitized launch command/config here (remove private IPs, local hostnames, tokens, and absolute home paths)."
echo
echo "## Notes"
echo
echo "- Context length:"
echo "- KV cache:"
echo "- GPU layers / split mode:"
echo "- PCIe layout / link width:"
echo "- Thinking enabled:"
echo "- Warnings/caveats:"
