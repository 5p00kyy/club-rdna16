#!/usr/bin/env python3
"""Regression contract for the evidence validator and privacy scanner.

Checks that validate_evidence still: refuses receipt identity omissions, refuses
published bundles without source receipts, and fails the whole tree when any
JSON under data/evidence - even an orphaned receipt - carries forbidden raw or
private fields.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_evidence  # noqa: E402


def main():
    presets = validate_evidence.load_presets()
    assert presets, "data/presets must be loadable for evidence validation"

    forbidden, private = validate_evidence.forbidden_scan({
        "cases": [{"request_nonce": "abc"}],
        "response": "answer",
        "reasoning_response": "trace",
        "runtime": {"backend": "ROCm/HIP", "power_profile": "COMPUTE", "gpu_model": "GPU", "gfx_target": "gfx1030"},
    })
    assert "cases[0].request_nonce" in forbidden, forbidden
    assert "response" in forbidden, forbidden
    assert "reasoning_response" in forbidden, forbidden
    assert not private, private

    private_sample = "ssh ubuntu@" + "192." + "168.1.5 " + "/" + "home/me/llama"
    _, private = validate_evidence.forbidden_scan({"notes": private_sample})
    assert private, "private IP / path should be flagged"

    real_preset = next(iter(presets))
    receipt = {
        "schema_version": "1.0",
        "kind": "raw-high-context-profile",
        "preset": real_preset,
        "context_tokens": 16384,
        "model": "Test",
        "runtime": {"power_profile": "COMPUTE", "gpu_model": "GPU", "gfx_target": "gfx1030"},
        "summary": {"useful": True},
    }
    errors = validate_evidence.validate_receipt(Path("receipt.json"), receipt, presets)
    assert any("runtime.backend is required" in error for error in errors), errors

    bundle = {
        "schema_version": "1.0",
        "id": "test-bundle",
        "preset": real_preset,
        "status": "published",
        "provenance": "seed-tested",
        "hardware": {"gpu_model": "GPU", "power_profile": "COMPUTE"},
        "runtime": {"backend": "ROCm/HIP"},
        "context": {"highest_useful_tokens": 16384, "validated_for": "test", "actual_prompt_tokens": 100},
        "evidence": {"checks": {"retrieval_repeats": 1, "sustained_generation_repeats": 0, "prompt_cache_disabled": True, "unique_leading_request_nonce": True, "thinking_disabled_explicitly": False, "retrieval_output_tokens": 512, "sustained_output_tokens": 512, "minimum_generated_tokens": 100}, "metrics": {"median_prefill_tok_s": 100.0, "median_decode_tok_s": 20.0}},
        "caveats": [],
        "source_receipts": [],
    }
    errors, receipts = validate_evidence.validate_bundle(Path("bundle.json"), bundle, presets)
    assert any("published evidence requires source_receipts" in error for error in errors), errors
    assert any("published evidence requires sustained-generation checks" in error for error in errors), errors
    assert receipts == [], "no source_receipts were declared"

    with tempfile.TemporaryDirectory() as directory:
        orphan_dir = Path(directory)
        orphan = orphan_dir / "orphan-receipt.json"
        orphan.write_text(json.dumps({
            "schema_version": "1.0",
            "kind": "raw-high-context-profile",
            "preset": real_preset,
            "context_tokens": 16384,
            "model": "Test",
            "runtime": {"backend": "ROCm/HIP", "power_profile": "COMPUTE", "gpu_model": "GPU", "gfx_target": "gfx1030"},
            "summary": {"useful": True},
            "request_nonce": "secret",
            "response": "answer",
            "reasoning_response": "trace",
        }), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_evidence.py"), str(orphan)],
            text=True, capture_output=True,
        )
        assert result.returncode != 0, "orphan receipt with raw fields must fail validation"
        assert "contains forbidden raw/private fields" in result.stderr, result.stderr

    with tempfile.TemporaryDirectory() as directory:
        identity_dir = Path(directory)
        preset_value = presets[real_preset]
        preset_hardware = preset_value["hardware"]
        preset_runtime = preset_value["runtime"]
        source_receipt = identity_dir / "source-receipt.json"
        source_receipt.write_text(json.dumps({
            "schema_version": "1.0",
            "kind": "raw-high-context-profile",
            "preset": real_preset,
            "context_tokens": 16384,
            "model": "Test",
            "runtime": {
                "backend": preset_runtime["backend"],
                "power_profile": preset_hardware["power_profile"],
                "gpu_model": preset_hardware["gpu_model"],
                "gfx_target": "gfx1201",
            },
            "summary": {"useful": True},
        }), encoding="utf-8")
        identity_bundle = identity_dir / "bundle.json"
        identity_bundle.write_text(json.dumps({
            "schema_version": "1.0",
            "id": "test-bundle",
            "preset": real_preset,
            "status": "candidate",
            "provenance": "seed-tested",
            "hardware": {
                "gpu_count": preset_hardware["gpu_count"],
                "gpu_model": preset_hardware["gpu_model"],
                "architecture_target": preset_hardware["architecture_target"],
                "power_profile": preset_hardware["power_profile"],
            },
            "runtime": {"backend": preset_runtime["backend"]},
            "context": {"highest_useful_tokens": 16384, "validated_for": "test", "actual_prompt_tokens": 100},
            "evidence": {
                "checks": {
                    "retrieval_repeats": 1,
                    "sustained_generation_repeats": 1,
                    "prompt_cache_disabled": True,
                    "unique_leading_request_nonce": True,
                    "thinking_disabled_explicitly": False,
                    "retrieval_output_tokens": 512,
                    "sustained_output_tokens": 512,
                    "minimum_generated_tokens": 100,
                },
                "metrics": {"median_prefill_tok_s": 100.0, "median_decode_tok_s": 20.0},
            },
            "caveats": [],
            "source_receipts": [str(source_receipt)],
        }), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_evidence.py"), str(identity_dir)],
            text=True, capture_output=True,
        )
        assert result.returncode != 0, "source receipt gfx target mismatching the bundle must fail validation"
        assert "runtime identity mismatch" in result.stderr, result.stderr
        assert "gfx_target" in result.stderr, result.stderr

    published_paths = sorted((ROOT / "data" / "evidence").glob("*.json"))
    published_bundle = next(
        json.loads(path.read_text()) for path in published_paths
        if json.loads(path.read_text()).get("status") == "published"
    )
    source_path = ROOT / published_bundle["source_receipts"][0]
    source_value = json.loads(source_path.read_text())

    with tempfile.TemporaryDirectory() as directory:
        tamper_dir = Path(directory)
        tampered_receipt = dict(source_value)
        tampered_receipt["model"] = "wrong-model"
        receipt_path = tamper_dir / "receipt.json"
        receipt_path.write_text(json.dumps(tampered_receipt), encoding="utf-8")
        tampered_bundle = dict(published_bundle)
        tampered_bundle["source_receipts"] = [str(receipt_path)]
        (tamper_dir / "bundle.json").write_text(json.dumps(tampered_bundle), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_evidence.py"), str(tamper_dir)],
            text=True, capture_output=True,
        )
        assert result.returncode != 0, "published source receipt with wrong model must fail validation"
        assert "source receipt model mismatch" in result.stderr, result.stderr

    with tempfile.TemporaryDirectory() as directory:
        tamper_dir = Path(directory)
        receipt_path = tamper_dir / "receipt.json"
        receipt_path.write_text(json.dumps(source_value), encoding="utf-8")
        tampered_bundle = json.loads(json.dumps(published_bundle))
        tampered_bundle["source_receipts"] = [str(receipt_path)]
        tampered_bundle["evidence"]["metrics"]["median_decode_tok_s"] += 1
        (tamper_dir / "bundle.json").write_text(json.dumps(tampered_bundle), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_evidence.py"), str(tamper_dir)],
            text=True, capture_output=True,
        )
        assert result.returncode != 0, "published bundle with overstated metrics must fail validation"
        assert "median_decode_tok_s" in result.stderr, result.stderr

    print("evidence validator regression test passed")


if __name__ == "__main__":
    main()
