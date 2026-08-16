## What changed


## Evidence

- Hardware lane:
- GPU model + gfx target (e.g. RX 6900 XT / gfx1030):
- Backend (ROCm/HIP vs Vulkan):
- Power profile (COMPUTE / 3D_FULL_SCREEN / default / unknown):
- Hardware:
- Runtime/model:
- Command/config:
- Benchmark or smoke result:
- KV cache dtype (q8_0 recommended; lower variants are exploratory only):

## Preset/evidence PRs only

- [ ] New/changed preset manifests pass `scripts/validate_presets.py data/presets`.
- [ ] Evidence bundles pass `scripts/validate_evidence.py data/evidence`.
- [ ] Public receipts remove `request_nonce`, `response`, and `reasoning_response`.
- [ ] Evidence is not generalized beyond its exact GPU and backend.

## Public hygiene

- [ ] No API keys, private IPs, private hostnames, or raw secret-bearing logs.
- [ ] Benchmark claims include context length, generated tokens, model, quant, and runtime.
- [ ] Relevant caveats are documented.
