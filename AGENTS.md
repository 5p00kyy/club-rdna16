# AGENTS.md

This repo is a public-facing community guide for 16GB AMD Radeon local LLM setups.

## Rules

- Keep claims evidence-backed. If a number came from one machine, say that.
- Do not include private IPs, API keys, bearer tokens, SSH hostnames, or personal infrastructure details.
- Prefer short reproducible commands over long narrative.
- Keep docs in `docs/`, scripts in `scripts/`, sanitized snippets in `examples/`, result data in `data/`.
- Keep RX 6900 XT, RX 9070 XT, and other Radeon results separated by hardware lane.
- When adding benchmark data, include hardware, ROCm/Mesa/runtime versions, model, quant, context, KV cache, launch shape, and caveats.
- Backend is first-class: record ROCm/HIP or Vulkan explicitly, plus the exact gfx target (gfx1030, gfx1201, ...).
- Power profile is first-class evidence metadata: record `COMPUTE`, `3D_FULL_SCREEN`, `default`, or `unknown` for every evidence-bearing run.
- Never generalize RX 6900 XT evidence to all 16GB Radeon cards; each GPU/architecture target needs its own measurements.
- `q8_0` KV is the recommendation floor for 16GB Radeon presets; lower KV variants are exploratory and must be marked `experimental`.
- Preset promotion is manual. Presets stay `candidate` until a maintainer publishes a reviewed evidence bundle; raw receipts stay in the ignored `.local/bench/` tree.
- Public receipts must remove `request_nonce`, `response`, and `reasoning_response`.
- Scripts must use standard-library Python or clearly document dependencies.

## Verification

```bash
python3 -m py_compile scripts/*.py scripts/tests/*.py
bash -n scripts/*.sh examples/*.sh
python3 scripts/validate_results.py data/results
python3 scripts/validate_presets.py data/presets
python3 scripts/validate_evidence.py data/evidence
python3 scripts/tests/test_high_context_profile.py
python3 scripts/tests/test_context_ladder.py
python3 scripts/tests/test_validate_presets.py
python3 scripts/tests/test_validate_evidence.py
python3 scripts/tests/test_review_context_fit.py
python3 scripts/build_preset_data.py
python3 scripts/build_site_data.py
./scripts/check_repo.sh
```
