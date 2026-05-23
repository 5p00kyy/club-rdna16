# Benchmarks

Seed RX 6900 XT benchmark JSON is checked in under `data/results/`. Long-context needle receipts are under `data/long-context/`.

The current evidence is:

## Current Seed Results

| profile | prompt | tokens | result |
| --- | --- | ---: | --- |
| 35B-A3B `131k/q8` no-MTP | short-chat | 256 generated | 79.48 decode tok/s |
| 35B-A3B `131k/q8` no-MTP | agent-tool | 512 generated | 79.61 decode tok/s |
| 35B-A3B `131k/q8` no-MTP | cold 300k-character needle | 70,992 prompt | passed, 192.9s wall, 373.4 prompt tok/s |
| 35B-A3B `100k/q8` MTP `b512/ub256` | short-chat | 256 generated | 79.87 decode tok/s |
| 35B-A3B `100k/q8` MTP `b512/ub256` | agent-tool | 512 generated | 69.20 decode tok/s |
| 35B-A3B `100k/q8` MTP `b512/ub256` | cold 300k-character needle | 71,010 prompt | passed, 205.4s wall, 353.5 prompt tok/s |
| 35B-A3B `131k/q8` MTP `b256/ub128` | short-chat | 256 generated | 82.25 decode tok/s |
| 35B-A3B `131k/q8` MTP `b256/ub128` | agent-tool | 512 generated | 70.73 decode tok/s |
| 27B `64k/q8` MTP `b512/ub256` | short-chat | 256 generated | 34.09 decode tok/s |
| 27B `100k/q8` MTP `b256/ub128` | short-chat | 256 generated | 33.94 decode tok/s |

## Caveats

- These seed rows used LACT/amdgpu `3D_FULL_SCREEN`, not `COMPUTE`.
- Compute-mode reruns need local sudo or a LACT profile change on the desktop; the SSH user cannot switch `pp_power_profile_mode` without a password.
- Q8 KV is the preferred public target. Q4 KV was explored as a fit fallback and then removed from promoted result data.
- MTP needs `parallel=1` on this RX 6900 XT. Without it, router child processes can start with four slots and produce false OOMs.
- 35B-A3B `131k/q8` MTP is short-prompt stable but failed a 300k-character long prompt during prefill.
- 27B q8 MTP loads, but seed short-prompt speed is materially worse than 35B-A3B and long-context behavior is not promoted.
- Short-prompt decode speed is not a long-context decode guarantee.

Once result JSON exists under `data/results/`, run:

```bash
python3 scripts/build_site_data.py
```

The static explorer reads `site/data/results.json`.
