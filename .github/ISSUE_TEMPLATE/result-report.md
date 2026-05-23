---
name: Result report
about: Share a reproducible 16GB AMD Radeon local LLM result
title: "[result] "
labels: result
---

## Privacy Checklist

- [ ] I removed private IPs, hostnames, tokens, and personal paths.
- [ ] I validated my JSON with python3 scripts/validate_results.py PATH_TO_RESULT_JSON.
- [ ] I attached or linked the result JSON file.

## Hardware

- Hardware lane:
- GPU(s):
- GPU architecture(s), if mixed:
- VRAM per GPU:
- Driver:
- CPU:
- Host RAM:
- Inference/container RAM:
- Motherboard/system:
- PCIe layout/link width:
- OS/container:

## Runtime

- Runtime:
- Version/commit:
- Model:
- Quant:
- Launch command/config:

## Settings

- Context length:
- KV cache:
- GPU layers / split mode:
- MTP/speculative settings:
- Thinking/reasoning enabled:

## Result

- Prompt tokens:
- Generated tokens:
- Decode tok/s:
- End-to-end tok/s if measured:
- Notes/warnings:

## Optional Report Output

You can generate a starter report with:

Paste reviewed output from:

~~~bash
python3 scripts/run_openai_bench.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model your-model-name \
  --prompt-set short-chat \
  --prompt-set code-generate \
  --prompt-set agent-tool \
  --runs 1 \
  --no-thinking \
  --output data/results/community-your-run.json \
  --report-output my-result.md
bash scripts/report.sh --url http://127.0.0.1:8000 --model your-model-name >> my-result.md
~~~
