# Hardware Lanes

The repo groups results by practical comparability, not marketing generation.

| Lane | Meaning |
| --- | --- |
| `1x-rdna16` | One 16GB Radeon card in the main target class, such as RX 6900 XT or RX 9070 XT. |
| `2x-rdna16` | Two comparable 16GB Radeon cards. Not assumed until tested. |
| `multi-rdna16` | Three or more 16GB Radeon cards. |
| `other-radeon-16gb` | 16GB Radeon card outside the first target set, or unclear RDNA generation. |
| `other-amd` | AMD GPU that does not fit the 16GB Radeon lane. |
| `unknown` | Incomplete report. |

## Seed Lane

The seed lane is `1x-rdna16` on RX 6900 XT. RX 9070 XT submissions should also use `1x-rdna16`, but should be filtered separately by exact `gpu_model` until the data shows how close the results are.

## RX 9070 XT Intake Notes

Expected contributor target:

- GPU target: `gfx1201`
- VRAM: 16GB
- Memory bandwidth: up to 640 GB/s on AMD's RX 9000 quick reference
- Runtime fields to record: ROCm version, OS, whether the backend is ROCm/HIP or Vulkan, flash attention state, HIP graph flags, and exact llama.cpp commit

## Why This Matters

16GB VRAM controls fit. Memory bandwidth, ROCm maturity, and architecture generation control speed. The RX 9070 XT should fit the same single-card profiles as the RX 6900 XT, but performance must be measured instead of inferred.
