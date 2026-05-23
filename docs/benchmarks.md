# Benchmarks

Seed RX 6900 XT benchmark JSON is checked in under `data/results/`. Long-context needle receipts are under `data/long-context/`.

The current evidence is:

## Current Seed Results

| profile | prompt | tokens | result |
| --- | --- | ---: | --- |
| 35B-A3B `131k/q8` no-MTP | short-chat | 256 generated | 79.48 decode tok/s |
| 35B-A3B `131k/q8` no-MTP | agent-tool | 512 generated | 79.61 decode tok/s |
| 35B-A3B `131k/q8` no-MTP | cold 300k-character needle | 70,992 prompt | passed, 192.9s wall, 373.4 prompt tok/s |
| 35B-A3B `200k/q4` no-MTP | short-chat | 256 generated | 78.86 decode tok/s |
| 35B-A3B `200k/q4` no-MTP | cold 500k-character needle | 118,296 prompt | passed, 281.4s wall, 424.6 prompt tok/s |

## Caveats

- These seed rows used LACT/amdgpu `3D_FULL_SCREEN`, not `COMPUTE`.
- These are no-MTP rows. The first 35B-A3B `131k/q8` MTP load failed while allocating the extra MTP draft context.
- Short-prompt decode speed is not a long-context decode guarantee.

Once result JSON exists under `data/results/`, run:

```bash
python3 scripts/build_site_data.py
```

The static explorer reads `site/data/results.json`.
