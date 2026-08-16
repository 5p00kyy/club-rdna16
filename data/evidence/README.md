# Reviewed evidence bundles

This directory holds **reviewed public evidence bundles** for canonical presets in
`data/presets/`. Nothing here is published automatically.

- `receipts/` – sanitized public copies of raw high-context profile receipts that a
  published bundle points at.
- `candidates/` – local context-fit review summaries produced by
  `scripts/review_context_fit.py --publish`. These are reviewed evidence candidates,
  not bundles; a maintainer turns one into a bundle in this directory and sanitized
  receipts before promotion.

## Rules

- No fabricated numbers. Evidence bundles are only written by a maintainer running
  `scripts/review_context_fit.py --publish` against real raw receipts, or by a
  reviewer consolidating reviewed results.
- A bundle references the preset by `preset: <preset id>` and must link every claim
  to a tracked `source_receipts` file.
- `receipts/` holds the sanitized public copies of raw high-context profile receipts
  that a published bundle points at. Raw, unredacted runs stay in the ignored
  `.local/bench/` tree until a maintainer reviews and sanitizes them.
- **Forbidden in any public file**: `request_nonce`, `response`, `reasoning_response`,
  private IPs, personal paths, host names, API keys, or bearer tokens. The privacy
  grep in `scripts/check_repo.sh` enforces this for the whole repo.
- AMD evidence must record `hardware.gpu_model`, `hardware.architecture_target`,
  `runtime.backend` (ROCm/HIP vs Vulkan), and `hardware.power_profile`. Evidence for
  one card (e.g. RX 6900 XT gfx1030) is never generalized to other 16GB Radeon cards.

## Statuses

- `candidate` – reviewed locally, awaiting promotion.
- `published` – promoted after review; the only status the preset-first site shows.
- `archived` – previously published, superseded.

The first published bundle validates the Qwen3.6 35B-A3B 100K q8 MTP alternative
on one RX 6900 XT through ROCm/HIP under `COMPUTE`. Its passing sanitized receipt
and the preceding 512-token retrieval diagnostic are both tracked for review.
Only bundles with `status: published` appear in the site's "tested presets" grid.
