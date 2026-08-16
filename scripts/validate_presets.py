#!/usr/bin/env python3
"""Validate canonical preset manifests without promoting them to public evidence.

Every active manifest is compared exactly against the llama.cpp INI section it
references (ctx-size, batch-size, ubatch-size, KV cache types, parallel,
speculation, and thinking/reasoning), so the copyable recipe and the manifest
cannot drift apart. Active presets must keep q8_0 KV, and recommended or
alternative presets must point at a published evidence bundle.
"""
import argparse
import configparser
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {"schema_version", "id", "title", "status", "provenance", "purpose", "hardware", "runtime", "model", "serving", "profile", "context"}
STATUSES = {"candidate", "recommended", "alternative", "experimental", "archived"}
ACTIVE_STATUSES = {"candidate", "recommended", "alternative", "experimental"}
PROVENANCE = {"seed-tested", "community-verified", "community-submitted"}
LANES = {"1x-rdna16", "2x-rdna16", "multi-rdna16", "other-radeon-16gb", "other-amd", "unknown"}
BACKENDS = {"ROCm/HIP", "Vulkan", "CUDA", "other"}
POWER_PROFILES = {"COMPUTE", "3D_FULL_SCREEN", "default", "unknown"}
ARCHITECTURE_TARGET_RE = re.compile(r"^gfx[0-9]+$")
TRUTHY_REASONING = {"on", "1", "true", "yes"}
FALSY_REASONING = {"off", "0", "false", "no"}
SERVING_FIELDS = ("kv_cache_k", "kv_cache_v", "batch_size", "ubatch_size", "parallel", "speculation", "thinking")


def parse_ini_section(preset_file: str, section: str):
    """Return the requested llama.cpp INI section as a lower-case option map."""
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.optionxform = str.lower
    parser.read(preset_file, encoding="utf-8")
    if not parser.has_section(section):
        return None
    return {key.lower(): value.strip() for key, value in parser.items(section)}


def ini_value(ini, key, errors, label):
    value = ini.get(key)
    if value is None:
        errors.append(f"{label}: INI section does not declare {key}, so the manifest cannot be verified against it")
    return value


def ini_bool(value):
    normalized = value.lower()
    if normalized in TRUTHY_REASONING:
        return "on"
    if normalized in FALSY_REASONING:
        return "off"
    return None


def compare_ini_int(ini, key, manifest_value, errors, label):
    raw = ini_value(ini, key, errors, label)
    if raw is None:
        return
    try:
        parsed = int(raw)
    except ValueError:
        errors.append(f"{label}: INI {key}={raw!r} is not an integer")
        return
    if manifest_value != parsed:
        errors.append(f"{label}: {key} mismatch: manifest {manifest_value!r} vs INI {parsed!r}")


def compare_ini_str(ini, key, manifest_value, errors, label):
    raw = ini_value(ini, key, errors, label)
    if raw is None:
        return
    if (manifest_value or "").lower() != raw.lower():
        errors.append(f"{label}: {key} mismatch: manifest {manifest_value!r} vs INI {raw!r}")


def compare_speculation(ini, serving, errors, label):
    manifest_type = serving.get("speculation") or "none"
    spec_type = ini.get("spec-type")
    if manifest_type == "none":
        if spec_type not in (None, "", "none"):
            errors.append(f"{label}: speculation mismatch: manifest 'none' vs INI spec-type={spec_type!r}")
        return
    if manifest_type in ("draft-mtp", "draft"):
        if spec_type != manifest_type:
            errors.append(f"{label}: speculation mismatch: manifest {manifest_type!r} vs INI spec-type={spec_type!r}")
        if manifest_type == "draft-mtp":
            raw_n = ini.get("spec-draft-n-max")
            if raw_n is None:
                errors.append(f"{label}: INI declares spec-type draft-mtp without spec-draft-n-max, so speculation_n cannot be verified")
            else:
                try:
                    if serving.get("speculation_n") != int(raw_n):
                        errors.append(f"{label}: speculation_n mismatch: manifest {serving.get('speculation_n')!r} vs INI spec-draft-n-max={raw_n!r}")
                except ValueError:
                    errors.append(f"{label}: INI spec-draft-n-max={raw_n!r} is not an integer")
    elif manifest_type == "other":
        if spec_type in (None, "", "none"):
            errors.append(f"{label}: speculation 'other' requires an explicit spec-type in the INI section")
    else:
        errors.append(f"{label}: unknown speculation type {manifest_type!r}")


def compare_thinking(ini, thinking, errors, label):
    raw = ini_value(ini, "reasoning", errors, label)
    if raw is None:
        return
    expected = ini_bool(raw)
    if expected is None:
        errors.append(f"{label}: INI reasoning={raw!r} is not a recognized on/off value")
        return
    if thinking != expected:
        errors.append(f"{label}: thinking mismatch: manifest {thinking!r} vs INI reasoning={raw!r} (route {expected})")


def compare_with_ini(value, errors):
    label = str(Path("data/presets") / value.get("id", "?"))
    preset_file = (value.get("runtime") or {}).get("preset_file")
    section = (value.get("runtime") or {}).get("preset_section")
    if not preset_file or not Path(preset_file).is_file():
        errors.append(f"{label}: runtime.preset_file must reference a tracked file")
        return
    if not section:
        errors.append(f"{label}: runtime.preset_section is required for INI agreement checks")
        return
    try:
        ini = parse_ini_section(preset_file, section)
    except configparser.Error as exc:
        errors.append(f"{label}: could not parse {preset_file}: {exc}")
        return
    if ini is None:
        errors.append(f"{label}: runtime.preset_section {section!r} is not present in {preset_file}")
        return

    context = value.get("context") or {}
    compare_ini_int(ini, "ctx-size", context.get("target_tokens"), errors, label)

    serving = value.get("serving") or {}
    compare_ini_int(ini, "batch-size", serving.get("batch_size"), errors, label)
    compare_ini_int(ini, "ubatch-size", serving.get("ubatch_size"), errors, label)
    compare_ini_int(ini, "parallel", serving.get("parallel"), errors, label)
    compare_ini_str(ini, "cache-type-k", serving.get("kv_cache_k"), errors, label)
    compare_ini_str(ini, "cache-type-v", serving.get("kv_cache_v"), errors, label)
    compare_speculation(ini, serving, errors, label)
    compare_thinking(ini, serving.get("thinking"), errors, label)


def published_evidence_presets(evidence_dir: Path):
    published = set()
    if not evidence_dir.is_dir():
        return published
    for path in evidence_dir.glob("*.json"):
        try:
            bundle = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(bundle, dict) and bundle.get("status") == "published" and bundle.get("preset"):
            published.add(bundle["preset"])
    return published


def validate(path: Path, evidence_dir: Path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]
    errors = []
    if not isinstance(value, dict):
        return [f"{path}: manifest must be an object"]
    missing = sorted(REQUIRED - set(value))
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
    if value.get("schema_version") != "1.0":
        errors.append(f"{path}: schema_version must be 1.0")
    status = value.get("status")
    if status not in STATUSES:
        errors.append(f"{path}: invalid status")
        return errors
    if value.get("provenance") not in PROVENANCE:
        errors.append(f"{path}: invalid provenance")
    hardware = value.get("hardware") or {}
    if hardware.get("lane") not in LANES:
        errors.append(f"{path}: invalid hardware lane")
    if not isinstance(hardware.get("gpu_count"), int) or hardware.get("gpu_count") < 1:
        errors.append(f"{path}: hardware.gpu_count must be a positive integer")
    if not hardware.get("gpu_model"):
        errors.append(f"{path}: hardware.gpu_model must name the exact GPU, never a generic 16GB Radeon label")
    if not hardware.get("architecture_target") or not ARCHITECTURE_TARGET_RE.fullmatch(str(hardware.get("architecture_target", ""))):
        errors.append(f"{path}: hardware.architecture_target must be an explicit gfx target (e.g. gfx1030)")
    if hardware.get("power_profile") not in POWER_PROFILES:
        errors.append(f"{path}: hardware.power_profile must be one of {', '.join(sorted(POWER_PROFILES))}")
    runtime = value.get("runtime") or {}
    if runtime.get("backend") not in BACKENDS:
        errors.append(f"{path}: runtime.backend must be one of {', '.join(sorted(BACKENDS))}")
    if runtime.get("backend_target") and not ARCHITECTURE_TARGET_RE.fullmatch(str(runtime.get("backend_target", ""))):
        errors.append(f"{path}: runtime.backend_target must be an explicit gfx target (e.g. gfx1030)")
    profile = value.get("profile")
    if not profile or not Path(profile).is_file():
        errors.append(f"{path}: profile must reference a tracked file")
    context = value.get("context") or {}
    target, minimum = context.get("target_tokens"), context.get("minimum_useful_tokens")
    if not isinstance(target, int) or not isinstance(minimum, int) or minimum < 1 or target < minimum:
        errors.append(f"{path}: context target/minimum must be positive and target >= minimum")

    serving = value.get("serving") or {}
    for field in SERVING_FIELDS:
        if serving.get(field) is None:
            errors.append(f"{path}: serving.{field} is required for INI agreement and KV policy checks")
    kv_k, kv_v = serving.get("kv_cache_k"), serving.get("kv_cache_v")
    for name, kv in (("kv_cache_k", kv_k), ("kv_cache_v", kv_v)):
        if kv == "f16":
            errors.append(f"{path}: f16 KV is not a supported preset on 16GB Radeon")
        elif status in {"candidate", "recommended", "alternative"} and kv != "q8_0":
            errors.append(f"{path}: {name} must be q8_0 for {status} status; lower KV variants are experimental only")

    if status == "recommended" and value.get("provenance") == "community-submitted":
        errors.append(f"{path}: community-submitted presets cannot be recommended without verification")
    if status in {"candidate", "recommended", "alternative"} and value.get("provenance") == "seed-tested" and not value.get("known_evidence"):
        errors.append(f"{path}: active seed-tested presets require known evidence")
    if status in {"recommended", "alternative"}:
        published = published_evidence_presets(evidence_dir)
        if value.get("id") not in published:
            errors.append(f"{path}: {status} presets must reference a published evidence bundle in {evidence_dir} (none found for {value.get('id')!r})")
        if not value.get("known_evidence"):
            errors.append(f"{path}: {status} presets require known_evidence")

    if status in ACTIVE_STATUSES:
        compare_with_ini(value, errors)

    if profile and Path(profile).is_file():
        try:
            profile_value = json.loads(Path(profile).read_text(encoding="utf-8"))
        except Exception:
            profile_value = None
        ladder = (profile_value or {}).get("context_ladder") if isinstance(profile_value, dict) else None
        if isinstance(ladder, list) and target not in ladder:
            errors.append(f"{path}: context target {target} is not a rung of the profile's context_ladder; the preset cannot be exercised by the ladder")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate data/presets/*.json manifests.")
    parser.add_argument("paths", nargs="*", default=["data/presets"])
    parser.add_argument("--evidence-dir", default=str(ROOT / "data" / "evidence"), help="Directory holding evidence bundles (default data/evidence).")
    args = parser.parse_args()
    files = []
    for raw in args.paths:
        path = Path(raw)
        files.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    errors = [error for path in files for error in validate(path, Path(args.evidence_dir))]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"validated {len(files)} preset manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
