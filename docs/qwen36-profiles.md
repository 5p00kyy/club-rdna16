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
| MTP q8 short | 65536 | `q8_0` | runtime validated for short prompts | Loads with MTP but decode is only around 31-34 tok/s in seed tests. |
| MTP q8 short | 102400 | `q8_0` | runtime validated for short prompts | Loads with `b256/ub128`; 300k-character long prompt failed, and 64k long prefill was too slow to promote. |
| no-MTP q8 | 102400 | `q8_0` | still needs q8-only long validation | Prefer this over dropping KV precision if 27B is needed. |

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
- Do not promote 27B MTP yet; q8 loads, but speed and long-context behavior are not competitive in the seed tests.

If `llama-fit-params` recommends fewer GPU layers or CPU tensor overrides, record that result as a separate profile. Do not hide CPU offload inside a headline all-GPU result.
