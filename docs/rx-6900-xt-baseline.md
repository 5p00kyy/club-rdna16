# RX 6900 XT Baseline

Observed seed machine:

- GPU: AMD Radeon RX 6900 XT
- VRAM: 16GB
- Architecture target: `gfx1030`
- Host CPU: Intel i9-10900K
- Host RAM: 64GB DDR4-3200
- OS: Arch Linux
- Runtime: upstream llama.cpp HIP build
- llama.cpp version observed: `9293`, commit `1acee6bf8`
- Build: `GGML_HIP=ON`, `GGML_VULKAN=OFF`, `GGML_HIP_NO_VMM=ON`, `AMDGPU_TARGETS=gfx1030`
- Models present: Unsloth `Qwen3.6-27B-MTP-GGUF` and `Qwen3.6-35B-A3B-MTP-GGUF`, both `UD-IQ3_XXS`

## Current Setup Notes

The local desktop setup lives under `~/Llama` and has:

- `llama.cpp/` source checkout
- `models/unsloth/` GGUF model directories
- `presets.ini`
- `llama-server.sh`
- `bench.sh`

Public docs should not include private LAN addresses, API keys, local hostnames, or absolute private paths from that setup.
