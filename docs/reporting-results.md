# Reporting Results

Preferred submission path:

1. Open a result-report issue.
2. Include a sanitized launch command or preset.
3. Attach schema-valid JSON if possible.
4. Include warnings, failed runs, and OOMs. They are useful data.

## Minimal Result Fields

- GPU model and count
- VRAM per GPU
- ROCm/Mesa/kernel versions
- llama.cpp version and commit
- Build flags, especially `GGML_HIP`, `AMDGPU_TARGETS`, and `GGML_HIP_NO_VMM`
- Model repo and exact GGUF filename
- Quant
- Context
- KV cache K/V types
- Batch and ubatch
- MTP/speculation flags
- Prompt set and token counts
- Prompt tok/s and decode tok/s
- Caveats

## Privacy

Before submitting, remove:

- LAN IPs
- API keys and bearer tokens
- home-directory absolute paths
- private hostnames
- screenshots with unrelated personal content
