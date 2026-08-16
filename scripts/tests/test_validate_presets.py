#!/usr/bin/env python3
"""Regression contract for the preset manifest validator.

Checks that validate_presets still catches: INI/manifest drift, non-q8_0 KV on
active presets, thinking/reasoning mismatches, recommended presets without
published evidence, and context targets that are not ladder rungs.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_presets  # noqa: E402

INI_SECTION = "test-preset"


def write_ini(directory, overrides=None):
    values = {
        "ctx-size": "16384",
        "batch-size": "256",
        "ubatch-size": "128",
        "parallel": "1",
        "cache-type-k": "q8_0",
        "cache-type-v": "q8_0",
        "spec-type": "draft-mtp",
        "spec-draft-n-max": "3",
        "reasoning": "on",
    }
    values.update(overrides or {})
    lines = ["[test-preset]"] + [f"{key} = {value}" for key, value in values.items()]
    path = directory / "test.ini"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_profile(directory):
    path = directory / "profile.json"
    path.write_text(json.dumps({"name": "test", "context_ladder": [16384, 32768]}), encoding="utf-8")
    return path


def manifest(tmpdir, ini_path, profile_path, overrides=None):
    value = {
        "schema_version": "1.0",
        "id": "test-preset",
        "title": "test preset",
        "status": "candidate",
        "provenance": "seed-tested",
        "purpose": "regression test",
        "hardware": {
            "lane": "1x-rdna16",
            "gpu_count": 1,
            "gpu_model": "AMD Radeon RX 6900 XT",
            "architecture_target": "gfx1030",
            "power_profile": "COMPUTE",
        },
        "runtime": {
            "backend": "ROCm/HIP",
            "backend_target": "gfx1030",
            "preset_file": str(ini_path),
            "preset_section": INI_SECTION,
        },
        "model": {"id": "Test-1B", "family": "Test", "quant": "Q4_K_M"},
        "serving": {
            "kv_cache_k": "q8_0",
            "kv_cache_v": "q8_0",
            "batch_size": 256,
            "ubatch_size": 128,
            "parallel": 1,
            "speculation": "draft-mtp",
            "speculation_n": 3,
            "thinking": "on",
        },
        "profile": str(profile_path),
        "context": {"target_tokens": 16384, "minimum_useful_tokens": 1000},
        "known_evidence": {"kind": "seed-tested", "summary": {}},
    }
    value.update(overrides or {})
    path = tmpdir / "test-preset.json"
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    return path


def errors_for(tmpdir, overrides=None, ini_overrides=None):
    ini = write_ini(tmpdir, ini_overrides)
    profile = write_profile(tmpdir)
    path = manifest(tmpdir, ini, profile, overrides)
    evidence_dir = tmpdir / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    return validate_presets.validate(path, evidence_dir)


def expect(tmpdir, needle, overrides=None, ini_overrides=None, negate=False):
    errors = errors_for(tmpdir, overrides, ini_overrides)
    hits = [error for error in errors if needle in error]
    if negate:
        assert not hits, f"expected no error containing {needle!r}, got {hits}"
    else:
        assert hits, f"expected error containing {needle!r}, got {errors}"


def main():
    with tempfile.TemporaryDirectory() as directory:
        tmpdir = Path(directory)

        expect(tmpdir, "batch-size mismatch", overrides={"serving": {"batch_size": 999}})

        expect(tmpdir, "f16 KV is not a supported preset on 16GB Radeon", overrides={"serving": {"kv_cache_k": "f16"}})

        expect(tmpdir, "kv_cache_k must be q8_0", overrides={"serving": {"kv_cache_k": "q4_0"}})

        expect(tmpdir, "thinking mismatch", ini_overrides={"reasoning": "off"})

        expect(tmpdir, "must reference a published evidence bundle", overrides={"status": "recommended"})

        expect(tmpdir, "must reference a published evidence bundle", overrides={"status": "alternative"})

        expect(tmpdir, "context target 20000 is not a rung", overrides={"context": {"target_tokens": 20000, "minimum_useful_tokens": 1000}})

    with tempfile.TemporaryDirectory() as directory:
        tmpdir = Path(directory)
        ini = write_ini(tmpdir)
        profile = write_profile(tmpdir)
        evidence_dir = tmpdir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        (evidence_dir / "published.json").write_text(json.dumps({"schema_version": "1.0", "preset": "test-preset", "status": "published"}), encoding="utf-8")
        path = manifest(tmpdir, ini, profile, {"status": "recommended"})
        errors = validate_presets.validate(path, evidence_dir)
        assert not [e for e in errors if "must reference a published evidence bundle" in e], errors

    print("preset validator regression test passed")


if __name__ == "__main__":
    main()
