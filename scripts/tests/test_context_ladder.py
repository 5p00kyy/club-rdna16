#!/usr/bin/env python3
"""Safety contract for the context ladder launcher."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_context_ladder.py"


def main():
    result = subprocess.run([
        sys.executable, str(SCRIPT), "--base-url", "http://127.0.0.1:19999/v1",
        "--model", "test-model", "--preset", "test", "--server-command-template", "llama-server --ctx-size 4096",
        "--backend", "ROCm/HIP", "--power-profile", "COMPUTE", "--gpu-model", "AMD Radeon RX 6900 XT", "--gfx-target", "gfx1030",
    ], text=True, capture_output=True)
    assert result.returncode != 0
    assert "{context_tokens}" in result.stderr
    result = subprocess.run([
        sys.executable, str(SCRIPT), "--base-url", "http://127.0.0.1:19999/v1",
        "--model", "test-model", "--preset", "test", "--start-at", "12345",
        "--server-command-template", "llama-server --ctx-size {context_tokens}",
        "--backend", "ROCm/HIP", "--power-profile", "COMPUTE", "--gpu-model", "AMD Radeon RX 6900 XT", "--gfx-target", "gfx1030",
    ], text=True, capture_output=True)
    assert result.returncode != 0
    assert "--start-at" in result.stderr

    result = subprocess.run([
        sys.executable, str(SCRIPT), "--base-url", "http://127.0.0.1:19999/v1",
        "--model", "test-model", "--preset", "test", "--server-command-template", "llama-server --ctx-size {context_tokens}",
        "--backend", "OpenCL", "--power-profile", "COMPUTE", "--gpu-model", "AMD Radeon RX 6900 XT", "--gfx-target", "gfx1030",
    ], text=True, capture_output=True)
    assert result.returncode != 0
    assert "--backend" in result.stderr

    result = subprocess.run([
        sys.executable, str(SCRIPT), "--base-url", "http://127.0.0.1:19999/v1",
        "--model", "test-model", "--preset", "test", "--server-command-template", "llama-server --ctx-size {context_tokens}",
        "--backend", "ROCm/HIP", "--power-profile", "COMPUTE", "--gpu-model", "AMD Radeon RX 6900 XT", "--gfx-target", "nvidia",
    ], text=True, capture_output=True)
    assert result.returncode != 0
    assert "--gfx-target" in result.stderr
    print("context ladder safety contract test passed")


if __name__ == "__main__":
    main()
