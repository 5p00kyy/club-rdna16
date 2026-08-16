# Benchmark Protocol

Comparable results must report both the launch shape and the workload shape.

## Required Fields

- GPU model, count, VRAM per GPU, and hardware lane.
- ROCm/HIP or Vulkan stack, driver/Mesa version when known, and kernel.
- Runtime engine, version, commit, and build flags.
- Model repo/file, quant, file size when known, and architecture notes.
- Context length, KV cache type, batch size, ubatch size, GPU layers, split mode, and MTP/speculation flags.
- Prompt set, actual prompt tokens, generated tokens, wall time, prompt tok/s, decode tok/s, and caveats.

## Prompt Sets

The standard script exposes:

- `short-chat`: compact practical answer, 256 visible output tokens.
- `code-generate`: larger code-generation response, 768 visible output tokens.
- `agent-tool`: review-style operational prompt, 512 visible output tokens.
- `long-retrieval`: synthetic filler with a needle; primarily validates context fit/retrieval.

Long-context results with tiny generated-token counts are fit/retrieval evidence, not sustained decode evidence.

## Promotion Levels

- `exploratory`: useful notes, fit checks, or incomplete measurements.
- `recipe`: launch shape is reproducible, but benchmark coverage is limited.
- `benchmark`: schema-valid speed data from the standard protocol.
- `verified`: independently reproduced or repeatedly validated.
- `deprecated`: retained for provenance, not current guidance.

## Context Tiers

- `32k`: quick sanity and low-risk setup checks.
- `64k`: useful agent/context baseline.
- `100k-131k`: daily long-context target for 16GB cards.
- `200k+`: deep-context experiment; must include retrieval and stability notes.

## MTP Rule

MTP GGUF files do not automatically mean MTP is active. Record the exact flags and only claim MTP if the runtime initialized `draft-mtp` successfully.

For 16GB AMD cards, run MTP with `parallel=1` first. Compare `--spec-draft-n-max 2` and `3` before promoting a result; higher draft depth can be slower on some AMD setups.

## Backend And Batch Sweeps

Backend is a first-class benchmark axis. Keep ROCm/HIP and Vulkan rows separate, and do not compare them without matching the model, quant, KV cache, prompts, context depth, generated-token target, and power profile.

The RX 6900 XT seed data currently includes ROCm/HIP rows under `COMPUTE` and `3D_FULL_SCREEN`, plus an exploratory Vulkan `3D_FULL_SCREEN` lane. A fair backend comparison still needs matched Vulkan `COMPUTE` rows.

When tuning batch settings, sweep instead of guessing:

```bash
llama-bench -m "$MODEL" -ngl 99 -fa 1 -ctk q8_0 -ctv q8_0 \
  -p 2048 -n 128 -b 512,1024,2048,4096 -ub 64,128,256,512
```

If a setting is fast only at empty or tiny context, mark it as short-context evidence. Public recommendations need at least one non-empty-context or long-retrieval receipt.

## Preset-First Promotion

Routine benchmark rows live in `data/results/` and stay in the historical explorer.
A preset only reaches the site's "tested presets" grid after a maintainer promotes
a reviewed evidence bundle (`data/evidence/`, status `published`). The uncached
`high-context` profile contract, raw-receipt flow, and manual promotion steps are
documented in `docs/preset-evidence-workflow.md`. Raw receipts are never committed;
they stay in the ignored `.local/bench/` tree until sanitized and promoted.
