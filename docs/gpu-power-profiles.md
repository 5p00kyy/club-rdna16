# GPU Power Profiles

AMD power profile mode is part of the benchmark surface. Record it with every serious result.

## Seed RX 6900 XT State

Observed through LACT and amdgpu sysfs:

- LACT version: `0.9.0`
- LACT daemon: enabled and running
- LACT config: `/etc/lact/config.yaml`
- `performance_level`: `manual`
- `power_profile_mode_index`: `1`
- Active sysfs profile: `3D_FULL_SCREEN`
- Available relevant sysfs profile: `COMPUTE` at index `5`

The first seed results used `3D_FULL_SCREEN`. Matched q8 reruns were later collected under `COMPUTE` after manually switching sysfs:

```bash
sudo bash -lc 'GPU=/sys/class/drm/card1/device; echo manual > "$GPU/power_dpm_force_performance_level"; echo 5 > "$GPU/pp_power_profile_mode"'
```

The compute rows are now the preferred RX 6900 XT baseline for serious llama.cpp/HIP testing. Keep the 3D rows as comparison data because many desktop systems will default to a graphics-oriented profile under LACT.

## Why It Matters

The kernel amdgpu sysfs documentation says `pp_power_profile_mode` adjusts the heuristics for switching between power levels. `3D_FULL_SCREEN` and `COMPUTE` can therefore produce different clock behavior under llama.cpp/HIP workloads even when the model fit is unchanged.

For apples-to-apples results, run each promoted profile under a recorded power mode. Ideally collect matched `3D_FULL_SCREEN` and `COMPUTE` rows for the same model/context/KV settings.

## CLI Checks

```bash
lact cli info
lact cli stats
lact cli profile get
cat /sys/class/drm/card1/device/power_dpm_force_performance_level
cat /sys/class/drm/card1/device/pp_power_profile_mode
```

LACT exposes profile management through:

```bash
lact cli profile list
lact cli profile get
lact cli profile set "Profile Name"
```

On the seed desktop only the `Default` LACT profile currently exists, so direct sysfs is the clearer temporary benchmark control for compute-mode comparison:

```bash
sudo sh -c 'echo manual > /sys/class/drm/card1/device/power_dpm_force_performance_level'
sudo sh -c 'echo 5 > /sys/class/drm/card1/device/pp_power_profile_mode'
```

To restore the current observed mode:

```bash
sudo sh -c 'echo 1 > /sys/class/drm/card1/device/pp_power_profile_mode'
```

Do not change this silently during normal desktop use. For benchmark work, record before/after state and restore the prior profile.
