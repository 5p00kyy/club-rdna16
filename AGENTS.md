# AGENTS.md

This repo is a public-facing community guide for 16GB AMD Radeon local LLM setups.

## Rules

- Keep claims evidence-backed. If a number came from one machine, say that.
- Do not include private IPs, API keys, bearer tokens, SSH hostnames, or personal infrastructure details.
- Prefer short reproducible commands over long narrative.
- Keep docs in `docs/`, scripts in `scripts/`, sanitized snippets in `examples/`, result data in `data/`.
- Keep RX 6900 XT, RX 9070 XT, and other Radeon results separated by hardware lane.
- When adding benchmark data, include hardware, ROCm/Mesa/runtime versions, model, quant, context, KV cache, launch shape, and caveats.
- Scripts must use standard-library Python or clearly document dependencies.

## Verification

```bash
python3 -m py_compile scripts/*.py
bash -n scripts/*.sh examples/*.sh
python3 scripts/validate_results.py data/results
python3 scripts/build_site_data.py
./scripts/check_repo.sh
```
