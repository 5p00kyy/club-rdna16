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
