# Contributing

Good contributions make the setup easier to reproduce.

Please include:

- hardware lane: 1x RDNA16 Radeon, 2x RDNA16 Radeon, 3x/4x+ RDNA16 Radeon, mixed RDNA16 Radeon plus other ROCm/HIP GPUs, or other ROCm/HIP GPU comparison
- GPU model and VRAM, including whether it is one card or multiple cards
- exact architecture target (gfx1030 for RX 6900 XT, gfx1201 for RX 9070 XT, etc.)
- backend: ROCm/HIP or Vulkan, plus driver version
- power profile used for the run: COMPUTE, 3D_FULL_SCREEN, default, or unknown
- CPU, host RAM, inference/container RAM allocation, motherboard, and PCIe slot/link details if long context or multi-GPU performance matters
- runtime and runtime version or commit
- model, quant, and source
- exact launch command or config
- context length and KV cache dtype (q8_0 is the recommendation floor; lower KV variants are exploratory only)
- tensor parallel or split settings
- benchmark prompt length and generated token count
- tokens/sec and whether it is prompt, decode, or end-to-end
- caveats and warnings

Do not paste API keys, private IP addresses, private hostnames, full logs with secrets, or benchmark claims without enough setup detail.

## Preset And Evidence Submissions

- Never claim a preset is validated without an evidence bundle; status stays
  `candidate` until a maintainer publishes reviewed evidence.
- New preset manifests go in `data/presets/` and must pass
  `scripts/validate_presets.py` (exact GPU, gfx target, backend, power profile,
  q8_0 KV, preset file, profile file).
- Raw receipts stay in the ignored `.local/bench/` tree. Public evidence bundles
  and receipts must remove `request_nonce`, `response`, and `reasoning_response`
  and pass `scripts/validate_evidence.py`.
- Do not generalize RX 6900 XT evidence to RX 9070 XT or other 16GB Radeon cards.
- Promotion is a maintainer decision: see `docs/preset-evidence-workflow.md`.
