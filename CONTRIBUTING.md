# Contributing

Good contributions make the setup easier to reproduce.

Please include:

- hardware lane: 1x RDNA16 Radeon, 2x RDNA16 Radeon, 3x/4x+ RDNA16 Radeon, mixed RDNA16 Radeon plus other ROCm/HIP GPUs, or other ROCm/HIP GPU comparison
- GPU model and VRAM, including whether it is one card or multiple cards
- CPU, host RAM, inference/container RAM allocation, motherboard, and PCIe slot/link details if long context or multi-GPU performance matters
- driver version
- runtime and runtime version or commit
- model, quant, and source
- exact launch command or config
- context length and KV cache dtype
- tensor parallel or split settings
- benchmark prompt length and generated token count
- tokens/sec and whether it is prompt, decode, or end-to-end
- caveats and warnings

Do not paste API keys, private IP addresses, private hostnames, full logs with secrets, or benchmark claims without enough setup detail.
