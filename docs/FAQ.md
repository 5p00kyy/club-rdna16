# FAQ

## Why not just call this RX 6900 XT?

Because the useful class is 16GB Radeon local inference. RX 9070 XT should fit many of the same profiles, but speed and driver behavior still need separate measurement.

## Is RX 9070 XT guaranteed to work the same?

No. It has the same VRAM class and higher memory bandwidth, but ROCm support, architecture target, and llama.cpp kernels decide the real result.

## Should I use ROCm/HIP or Vulkan?

The seed path is ROCm/HIP for llama.cpp. Vulkan results are welcome, but report them as separate backend results.

## Are fit checks enough?

No. Fit checks tell us what is worth testing. Public profile recommendations need actual prompt runs, especially long-retrieval prompts for high context.
