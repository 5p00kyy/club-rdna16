# Qwen3.6 Profiles

These are candidate profiles for RX 6900 XT / 16GB Radeon testing. Treat fit guidance separately from runtime validation.

## Qwen3.6 35B-A3B `UD-IQ3_XXS`

| Profile | Context | KV cache | Expected status | Notes |
| --- | ---: | --- | --- | --- |
| stable q8 | 131072 | `q8_0` | runtime validated without MTP | Cold 300k-character needle passed; compute profile measured about 81 tok/s short decode and 897 prompt tok/s on the 300k-character needle. |
| MTP q8 | 102400 | `q8_0` | runtime validated with MTP | Cold 300k-character needle passed; compute profile measured about 76-85 tok/s short decode and 675 prompt tok/s on the 300k-character needle with `parallel=1`, `b512/ub256`. |
| MTP q8 short-only | 131072 | `q8_0` | short prompts pass, long prefill fails | Short decode around 76-85 tok/s under compute with `b256/ub128`; 300k-character long prompt OOMed during prefill in earlier testing. |

## Qwen3.6 27B `UD-IQ3_XXS`

| Profile | Context | KV cache | Expected status | Notes |
| --- | ---: | --- | --- | --- |
| MTP q8 short | 65536 | `q8_0` | runtime validated for short prompts | Dense 27B lane that loads cleanly with q8 KV and MTP; current seed coverage is short-prompt only. |
| MTP q8 short | 102400 | `q8_0` | runtime validated for short prompts | Loads with `b256/ub128`; needs more long-context and thinking-on coverage before stronger guidance. |
| no-MTP q8 | 102400 | `q8_0` | still needs q8-only long validation | Useful dense-model fallback to validate before dropping KV precision. |

## Suggested Common Flags For No-MTP Baseline

```text
--flash-attn on
--n-gpu-layers 99
--batch-size 1024
--ubatch-size 512
--jinja on
--reasoning on
--reasoning-budget 8192
```

## MTP Experiment Flags

```text
--spec-type draft-mtp --spec-draft-n-max 3 --spec-draft-p-min 0.75
```

For MTP, add `parallel = 1`. The router-child default can otherwise use four slots and create false OOMs on 16GB cards.

Current MTP guidance:

- Promote 35B-A3B `102400/q8_0`, `parallel=1`, `b512/ub256` when MTP is wanted.
- Treat 35B-A3B `131072/q8_0`, `parallel=1`, `b256/ub128` as short-prompt only until long-prefill OOM is solved.
- Keep 27B MTP as a valid dense-model lane, with current guidance limited by coverage rather than by model quality. Add long-context and thinking-on rows before recommending a specific 27B profile.
- For public recommendations, keep KV at `q8_0` unless a result is explicitly marked exploratory. Lower-KV context-stretching is useful research, but it is not the first `club-rdna16` quality target.
- Sweep `--spec-draft-n-max 2` and `3` for future MTP submissions. Community reports show too much draft depth can slow AMD runs down.

If `llama-fit-params` recommends fewer GPU layers or CPU tensor overrides, record that result as a separate profile. Do not hide CPU offload inside a headline all-GPU result.
