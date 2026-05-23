# Community Goals

The most useful early submissions are:

- RX 9070 XT 16GB results using the same Qwen3.6 profiles as the RX 6900 XT baseline.
- RX 7800 XT, RX 7900 GRE, and other 16GB Radeon results clearly marked as separate hardware models.
- ROCm version differences that change fit, stability, or speed.
- MTP on/off comparisons with the same model, context, KV cache, and prompt set.
- Failed long-context attempts with exact context/KV settings.

Avoid:

- Posting a speed number without the launch shape.
- Mixing Vulkan and HIP results without labeling the backend.
- Treating a short prompt smoke as proof that a 200k context profile is stable.
