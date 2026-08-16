#!/usr/bin/env python3
"""Regression contract for context-fit review identity enforcement.

Checks that review_context_fit loads the preset manifest and refuses raw
receipts whose runtime identity is missing or does not match the preset
(backend, power profile, exact GPU, gfx target, model), while recording the
verified identity in a successful review.
"""
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import review_context_fit  # noqa: E402


def sample_preset():
    return {
        "schema_version": "1.0",
        "id": "test-preset",
        "hardware": {
            "gpu_count": 1,
            "gpu_model": "AMD Radeon RX 6900 XT",
            "architecture_target": "gfx1030",
            "power_profile": "COMPUTE",
        },
        "runtime": {"backend": "ROCm/HIP"},
        "model": {"id": "Test-1B"},
    }


def receipt(preset, runtime_overrides=None):
    runtime = {
        "backend": "ROCm/HIP",
        "power_profile": "COMPUTE",
        "gpu_model": "AMD Radeon RX 6900 XT",
        "gfx_target": "gfx1030",
    }
    runtime.update(runtime_overrides or {})
    return {
        "schema_version": "1.0",
        "kind": "raw-high-context-profile",
        "preset": preset,
        "context_tokens": 16384,
        "model": "Test-1B",
        "runtime": runtime,
        "summary": {"useful": True},
    }


def run_cli(arguments, output):
    original_load = review_context_fit.load_preset
    original_argv = sys.argv
    review_context_fit.load_preset = lambda _preset: sample_preset()
    try:
        sys.argv = ["review_context_fit"] + arguments + ["--output", str(output)]
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            rc = review_context_fit.main()
        return rc, stderr.getvalue()
    finally:
        sys.argv = original_argv
        review_context_fit.load_preset = original_load


def main():
    preset_value = sample_preset()

    missing = review_context_fit.check_receipt_identity(receipt("test-preset", {"backend": None}), preset_value)
    assert any("missing runtime.backend" in error for error in missing), missing

    missing = review_context_fit.check_receipt_identity(receipt("test-preset", {"gpu_model": ""}), preset_value)
    assert any("missing runtime.gpu_model" in error for error in missing), missing

    mismatched = review_context_fit.check_receipt_identity(receipt("test-preset", {"gfx_target": "gfx1201"}), preset_value)
    assert any("does not match preset" in error and "gfx_target" in error for error in mismatched), mismatched

    mismatched = review_context_fit.check_receipt_identity(receipt("test-preset", {"power_profile": "3D_FULL_SCREEN"}), preset_value)
    assert any("does not match preset" in error and "power_profile" in error for error in mismatched), mismatched

    mismatched = review_context_fit.check_receipt_identity(receipt("test-preset", {"backend": "Vulkan"}), preset_value)
    assert any("does not match preset" in error and "backend" in error for error in mismatched), mismatched

    assert not review_context_fit.check_receipt_identity(receipt("test-preset"), preset_value)

    with tempfile.TemporaryDirectory() as directory:
        tmpdir = Path(directory)

        bad = tmpdir / "bad.json"
        bad.write_text(json.dumps(receipt("test-preset", {"gfx_target": "gfx1201"})), encoding="utf-8")
        rc, stderr = run_cli(["--preset", "test-preset", "--input", str(bad)], tmpdir / "review.json")
        assert rc == 1, rc
        assert "runtime identity mismatch" in stderr, stderr

        other = tmpdir / "other.json"
        other.write_text(json.dumps(receipt("other-preset")), encoding="utf-8")
        rc, stderr = run_cli(["--preset", "test-preset", "--input", str(other)], tmpdir / "review.json")
        assert rc == 1, rc
        assert "belongs to preset" in stderr, stderr

        good = tmpdir / "good.json"
        good.write_text(json.dumps(receipt("test-preset")), encoding="utf-8")
        output = tmpdir / "review-good.json"
        rc, stderr = run_cli(["--preset", "test-preset", "--input", str(good)], output)
        assert rc == 0, (rc, stderr)
        review = json.loads(output.read_text(encoding="utf-8"))
        assert review["runtime_identity"] == review_context_fit.preset_identity(sample_preset())
        assert review["highest_useful_context_tokens"] == 16384

    print("context-fit review identity regression test passed")


if __name__ == "__main__":
    main()
