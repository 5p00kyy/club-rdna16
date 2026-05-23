# club-rdna16

Practical llama.cpp presets, tests, and benchmark receipts for 16GB AMD Radeon GPUs.

The first target is a single RX 6900 XT 16GB using ROCm/HIP on Linux. The comparison target is RX 9070 XT 16GB: same VRAM class, newer RDNA generation, higher memory bandwidth, and likely better speed when the ROCm stack supports the card cleanly.

This is not a synthetic leaderboard. A result is only useful when it includes enough context for someone else to reproduce the launch shape, understand the caveats, and decide whether the profile is stable enough for daily local inference.

## Start Here

| Path | Use this when |
| --- | --- |
| `docs/project-plan.md` | You want the repo roadmap and release checklist. |
| `docs/benchmark-protocol.md` | You want comparable-result rules and prompt sets. |
| `docs/hardware-lanes.md` | You want to understand RX 6900 XT vs RX 9070 XT vs other AMD result grouping. |
| `docs/rx-6900-xt-baseline.md` | You want the first tested hardware/software baseline. |
| `docs/qwen36-profiles.md` | You want Qwen3.6 27B and 35B-A3B context/KV recommendations. |
| `docs/gpu-power-profiles.md` | You want LACT/amdgpu power-profile notes for repeatable tests. |
| `docs/reporting-results.md` | You want to submit or review a result. |

## Current Baseline

Seed hardware:

- GPU: AMD Radeon RX 6900 XT 16GB, RDNA2 / `gfx1030`
- VRAM: 16GB GDDR6, 256-bit, up to 512 GB/s memory bandwidth according to AMD
- Host: i9-10900K, 64GB DDR4-3200
- OS: Arch Linux / Hyprland desktop
- Runtime: upstream llama.cpp HIP build
- ROCm packages observed locally: 7.2.x family
- Current models: Unsloth Qwen3.6 27B MTP GGUF and Qwen3.6 35B-A3B MTP GGUF, both `UD-IQ3_XXS`

Important first finding: keep q8 KV as the default target on this card. The best current seed path is Qwen3.6 35B-A3B with q8 KV: 131k no-MTP for stable long prompts, or 100k MTP when native draft-MTP speed is wanted.

## Recommended First Profiles

| Model | Purpose | Context | KV cache | Notes |
| --- | --- | ---: | --- | --- |
| Qwen3.6 35B-A3B `UD-IQ3_XXS` | stable q8 route | 131072 | `q8_0` | No-MTP cold 300k-character needle passed. |
| Qwen3.6 35B-A3B `UD-IQ3_XXS` | MTP q8 route | 102400 | `q8_0` | MTP cold 300k-character needle passed with `parallel=1`, `b512/ub256`. |
| Qwen3.6 35B-A3B `UD-IQ3_XXS` | short-prompt MTP q8 | 131072 | `q8_0` | Short prompts pass; long prefill OOMs, so do not promote for long-context use. |
| Qwen3.6 27B `UD-IQ3_XXS` | short-prompt MTP q8 | 65536-102400 | `q8_0` | Loads and runs, but observed decode is slower than 35B-A3B and long-context testing is not promoted. |

For MTP GGUF models, enable llama.cpp native MTP explicitly:

```bash
--spec-type draft-mtp --spec-draft-n-max 3 --spec-draft-p-min 0.75
```

Also set `parallel = 1` for 16GB Radeon MTP tests. Router-child defaults can otherwise start with four slots and blow VRAM. Do not claim MTP speedup unless logs or benchmark output show that speculation initialized and was active.

## Results And Data

Canonical result files live under `data/results/` and follow `data/schema/benchmark-result.schema.json`.

Validate result JSON:

```bash
python3 scripts/validate_results.py data/results
```

Build the static site data:

```bash
python3 scripts/build_site_data.py
```

Run a protocol-shaped OpenAI-compatible benchmark against a running llama.cpp server:

```bash
python3 scripts/run_openai_bench.py \
  --base-url http://127.0.0.1:8088/v1 \
  --model Qwen3.6-35B-A3B \
  --prompt-set short-chat \
  --prompt-set code-generate \
  --prompt-set agent-tool \
  --runs 1 \
  --output data/results/my-run.json
```

Capture a sanitized report:

```bash
bash scripts/report.sh --url http://127.0.0.1:8088 --model Qwen3.6-35B-A3B
```

## Repo Map

- `docs/project-plan.md` - project phases and public-release checklist
- `docs/benchmark-protocol.md` - prompt sets, context tiers, and promotion levels
- `docs/hardware-lanes.md` - result grouping for RX 6900 XT, RX 9070 XT, and other AMD GPUs
- `docs/rx-6900-xt-baseline.md` - current tested seed machine
- `docs/qwen36-profiles.md` - recommended Qwen3.6 27B and 35B-A3B profile matrix
- `docs/gpu-power-profiles.md` - LACT/amdgpu profile checks and compute-mode comparison plan
- `docs/fit-matrix.md` - first fit-probe findings
- `docs/troubleshooting.md` - ROCm/llama.cpp failure notes
- `docs/reporting-results.md` - community submission rules
- `examples/` - sanitized llama.cpp preset snippets
- `scripts/` - validation, reporting, build, and benchmark helpers
- `site/` - static result explorer

## Verification

```bash
python3 -m py_compile scripts/*.py
bash -n scripts/*.sh examples/*.sh
python3 scripts/validate_results.py data/results
python3 scripts/build_site_data.py
./scripts/check_repo.sh
```
