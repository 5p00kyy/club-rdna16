# LocalLLaMA Research Notes

Research date: 2026-05-23

These notes summarize public community signals that shaped the initial `club-rdna16` benchmark plan. Treat Reddit posts as anecdotal setup reports, not authoritative documentation. Use them to decide what to test, then promote only reproducible local or submitted benchmark receipts.

## Main Takeaways

- Keep `q8_0` KV as the public recommendation floor for this repo unless a lower-KV experiment is explicitly marked exploratory. Community posts often use lower KV to make context fit, but the initial `club-rdna16` target is q8-first quality.
- Benchmark MTP by workload and draft depth. Multiple LocalLLaMA reports show MTP can help coding or predictable outputs, but can lose or flatten out on creative/free-form prompts. This matches our seed data: 35B-A3B MTP is useful at `100k/q8`, while the 27B dense-model lane needs broader long-context and thinking-on coverage before drawing stronger guidance.
- Sweep `--spec-draft-n-max` rather than assuming bigger is faster. The RX 6800 XT MTP thread had a concrete case where reducing draft depth from 6 to 2 or 3 fixed a slowdown.
- Record flash attention and build flags. RX 9070 reports repeatedly point to flash attention and HIP build flags as the difference between poor and useful ROCm behavior.
- Treat ROCm/HIP vs Vulkan as a real axis. RX 6900 XT and RX 7800 XT posts report Vulkan often winning token generation, while ROCm can win prompt processing or become better with newer builds. `club-rdna16` now has both ROCm/HIP and exploratory Vulkan seed rows, and public submissions should always report backend.
- Measure non-empty context. Several community benchmarks are short `llama-bench` rows or low-context chat tests. For local-agent use, this repo should prefer short prompt, medium-context, and cold long-retrieval receipts.

## Sources Reviewed

| Topic | What It Suggests | Link |
| --- | --- | --- |
| RX 9070 ROCm llama.cpp | ROCm 7.x plus flash attention/build flags can materially change prompt processing; default ROCm paths may underperform. | <https://www.reddit.com/r/LocalLLaMA/comments/1s55b0r/rx_9070_rdna4gfx1201_rocm_721_llamacpp_benchmarks/> |
| RX 9070 XT Vulkan/HIP issue | On RDNA4, backend choice can flip results by model/runtime; HIP can beat Vulkan for some Qwen 3.5 cases. | <https://www.reddit.com/r/LocalLLaMA/comments/1rkky2n/bad_performance_with_vulkan_and_qwen35_using_a_rx/> |
| RX 9070 XT ubatch tuning | `--ubatch-size` needs empirical sweeping; community explanation points at VRAM/fit behavior rather than a simple cache-size rule. | <https://www.reddit.com/r/LocalLLaMA/comments/1rnrxsv/llamacpp_in_case_people_are_struggling_with/> |
| RX 6900 XT ROCm vs Vulkan | On RX 6900 XT, one report showed ROCm stronger for prompt processing in some Qwen/Gemma rows while Vulkan was faster for token generation. Comments argue non-zero context must be tested. | <https://www.reddit.com/r/LocalLLaMA/comments/1sxwszr/amd_radeon_rx_6900_xt_rocm_vs_vulkan_gemma_4_and/> |
| RX 7800 XT ROCm vs Vulkan | 16GB RDNA3 users report backend differences and occasional ROCm full-offload failures. | <https://www.reddit.com/r/LocalLLaMA/comments/1mpqtyo/rocm_vs_vulkan_for_amd_gpu_rx7800xt/> |
| RX 6800 XT MTP | MTP speedup depends on workload and draft depth; lowering draft depth to 2 or 3 can help. | <https://www.reddit.com/r/LocalLLaMA/comments/1th28d4/no_tg_speedup_with_mtp_on_rx_6800_xt/> |
| Qwen3.6 27B on 16GB | Other 16GB users are specifically chasing Qwen3.6 27B around 100k context, often with custom quants or experimental KV. | <https://www.reddit.com/r/LocalLLaMA/comments/1svnmgo/quant_qwen3627b_on_16gb_vram_with_100k_context/> |
| Qwen3.6 quant quality | Quant choice matters; public profiles should avoid presenting a pure speed result as a quality recommendation. | <https://www.reddit.com/r/LocalLLaMA/comments/1t53dhp/quality_comparison_between_qwen_36_27b/> |
| Qwen3.6 35B-A3B MTP | 35B-A3B MTP can reach strong generation speed on constrained VRAM, but launch shape and context must be recorded. | <https://www.reddit.com/r/LocalLLaMA/comments/1t82zxv/80_toksec_and_128k_context_on_12gb_vram_with/> |
| Strix Halo MTP | AMD-adjacent MTP tests show large speed gains are possible, but not automatically transferable to discrete 16GB cards. | <https://www.reddit.com/r/LocalLLaMA/comments/1t4uj9h/mtp_on_strix_halo_with_llamacpp_pr_22673/> |

## Official References

- AMD RX 9070 XT product page: <https://www.amd.com/en/products/graphics/desktops/radeon/9000-series/amd-radeon-rx-9070xt.html>
- AMD RX 9000 quick reference lists RX 9070 XT as 16GB GDDR6, 256-bit, up to 640 GB/s bandwidth: <https://www.amd.com/content/dam/amd/en/documents/partner-hub/radeon/radeon-rx-9000-series-quick-reference-guide-non-competitive.pdf>
- ROCm compatibility matrix lists RX 9070 XT as `gfx1201` on supported OS combinations: <https://rocm.docs.amd.com/en/docs-7.0.2/compatibility/compatibility-matrix.html>
- llama.cpp AMD HIP build docs use `-DGGML_HIP=ON` and GPU targets such as `gfx1030`: <https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md>

## Tests Added To The Repo Plan

1. `q8_0` KV-only promoted profiles unless the result is explicitly marked exploratory.
2. Compute power profile is recorded and matched against the old `3D_FULL_SCREEN` seed rows.
3. MTP profiles use `parallel=1` and draft depth 3 first; future AMD submissions should test draft depth 2 and 3 before claiming MTP benefit.
4. RX 9070 XT intake should record ROCm version, `gfx1201`, flash attention state, HIP graph flags, and whether the runtime is ROCm/HIP or Vulkan.
5. Future backend comparison should run the same prompts under ROCm/HIP and Vulkan, including at non-empty context, before recommending one backend for Radeon generally.
