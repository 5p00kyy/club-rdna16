# Project Plan

`club-rdna16` is a public-ready benchmark and recipe repo for local LLMs on 16GB AMD Radeon cards.

## Goals

- Make RX 6900 XT and RX 9070 XT local-model results comparable without pretending the cards are identical.
- Find practical Qwen3.6 27B and 35B-A3B quant/context/KV profiles for daily use.
- Capture reproducible benchmark receipts: hardware, software stack, launch flags, model file, context, KV cache, prompt shape, speed, and caveats.
- Keep a submission path similar to `club-5060ti`: issue template first, structured JSON preferred, static explorer generated from checked-in data.

## Non-Goals

- No global leaderboard claims from one machine.
- No private infrastructure details in public docs or result JSON.
- No ROCm support promises for cards that have not been tested.
- No result promotion from a fit-only check. Long-context profiles need actual long-prompt validation.

## Release Phases

1. Baseline scaffold: docs, schema, validation, report helper, static explorer, and sanitized examples.
2. RX 6900 XT fit matrix: Qwen3.6 27B and 35B-A3B across context and KV cache settings.
3. RX 6900 XT runtime matrix: short-chat, code-generate, agent-tool, and long-retrieval prompts on candidate profiles.
4. Public readiness pass: scrub private paths/hosts, validate data, build site data, review README and issue templates.
5. Community research pass: capture LocalLLaMA AMD/Radeon setup signals and turn them into bounded test axes, not unverified claims.
6. RX 9070 XT intake: document expected ROCm target, collect a contributor stack report, then run the same matrix.

## Public Checklist

- `./scripts/check_repo.sh` passes.
- `rg` finds no private IPs, tokens, hostnames, or local absolute paths in public docs/data.
- Every benchmark JSON validates.
- Every promoted profile has a reproducible launch snippet.
- The README says which results are measured, fit-only, or expected-but-unverified.
- GitHub issue templates ask for the exact fields needed for comparison.
- Community-sourced claims are linked and marked as prompts for testing unless reproduced by a submitted result.
