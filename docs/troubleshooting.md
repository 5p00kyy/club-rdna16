# Troubleshooting

## ROCm Tooling Is Partial

Some Arch setups have working HIP libraries but no `rocm-smi` binary. Check multiple paths:

```bash
command -v rocminfo rocm-smi hipcc vulkaninfo
vulkaninfo --summary
```

`vulkaninfo` proving the card exists does not prove llama.cpp is using HIP. Check llama.cpp startup logs for ROCm/HIP device lines.

## Long-Prompt OOM

A profile can load and answer short prompts but still OOM halfway through a real long prompt. This happened in earlier 35B-A3B long-context logs. Promote profiles only after a long-retrieval prompt reaches the end.

## MTP Not Active

MTP GGUF files still need explicit MTP flags:

```text
--spec-type draft-mtp --spec-draft-n-max 3 --spec-draft-p-min 0.75
```

If logs do not show speculative decoding initialized, the result is no-MTP.

## Fit-Only Is Not Benchmark Evidence

`llama-fit-params` is useful for pruning the matrix, but it is not enough for public performance claims. Fit rows should stay `exploratory` until benchmark prompts pass.
