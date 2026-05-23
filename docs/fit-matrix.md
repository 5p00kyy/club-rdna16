# Fit Matrix

First fit probing was run against the RX 6900 XT seed machine with the two downloaded `UD-IQ3_XXS` MTP GGUF files. The full machine-readable output is stored in `data/fit-matrices/`.

## Summary

| Model | Context | KV | Fit result |
| --- | ---: | --- | --- |
| Qwen3.6 27B | 65536 | `q8_0` | all GPU |
| Qwen3.6 27B | 102400 | `q8_0` | all GPU under current live fit check; earlier explicit `-ngl 99` check was tight |
| Qwen3.6 27B | 131072 | `q8_0` | fit suggested fewer GPU layers |
| Qwen3.6 27B | 131072 | `q5_1` | all GPU |
| Qwen3.6 27B | 131072 | `q4_0` | all GPU |
| Qwen3.6 27B | 204800 | `q4_0` | near wall; fit suggested reduced GPU layers in one pass |
| Qwen3.6 35B-A3B | 131072 | `q8_0` | all GPU |
| Qwen3.6 35B-A3B | 204800 | `q8_0` | needs late MoE CPU offload |
| Qwen3.6 35B-A3B | 204800 | `q5_1` | needs small late MoE CPU offload |
| Qwen3.6 35B-A3B | 204800 | `q4_0` | all GPU |
| Qwen3.6 35B-A3B | 262144 | `q4_0` | needs late MoE CPU offload |

## Interpretation

The all-GPU target for 35B-A3B should be `131072/q8_0` or `204800/q4_0`. The existing local `204800/q8_0/n-gpu-layers=99` preset is not the profile to publish as stable until long-prompt testing proves it, because older logs show ROCm OOM during long prefill.

Fit-only does not include MTP draft-context allocation. Runtime testing showed 35B-A3B `131072/q8_0` no-MTP loads, but the same profile with `draft-mtp` fails to allocate the additional MTP context on the RX 6900 XT.
