# Qwen3.6 Profiles

These are candidate profiles for RX 6900 XT / 16GB Radeon testing. Treat fit guidance separately from runtime validation.

## Qwen3.6 35B-A3B `UD-IQ3_XXS`

| Profile | Context | KV cache | Expected status | Notes |
| --- | ---: | --- | --- | --- |
| daily | 131072 | `q8_0` | runtime validated without MTP | Cold 300k-character needle passed; short decode around 79 tok/s. |
| long | 204800 | `q4_0` | runtime validated without MTP | Cold 500k-character needle passed; short decode around 79 tok/s. |
| experimental deep | 262144 | `q4_0` | needs late MoE CPU offload in fit probing | Likely slower; record CPU offload clearly. |

## Qwen3.6 27B `UD-IQ3_XXS`

| Profile | Context | KV cache | Expected status | Notes |
| --- | ---: | --- | --- | --- |
| daily | 102400 | `q8_0` | practical target | Good first daily route. |
| long | 131072 | `q5_1` or `q4_0` | fits fully in fit probing | Compare quality/speed. |
| experimental deep | 204800 | `q4_0` | near the wall | Needs real long-prompt testing. |

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

The first runtime test showed that 35B-A3B `131072/q8_0` can fit without MTP but fails to allocate the extra MTP draft context on the RX 6900 XT. Keep MTP profiles experimental until each one is load-tested.

If `llama-fit-params` recommends fewer GPU layers or CPU tensor overrides, record that result as a separate profile. Do not hide CPU offload inside a headline all-GPU result.
