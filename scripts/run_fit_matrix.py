#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MODELS = {
    "qwen36-27b-iq3xxs": "models/unsloth/Qwen3.6-27B-MTP-GGUF/Qwen3.6-27B-UD-IQ3_XXS.gguf",
    "qwen36-35b-a3b-iq3xxs": "models/unsloth/Qwen3.6-35B-A3B-MTP-GGUF/Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf",
}

CONTEXTS = [32768, 65536, 102400, 131072, 204800, 262144]
KV_TYPES = ["q8_0", "q5_1", "q4_0"]


def run_fit(binary, model_path, context, kv_type, timeout):
    cmd = [
        binary,
        "-m",
        str(model_path),
        "-c",
        str(context),
        "-b",
        "1024",
        "-ub",
        "512",
        "-fa",
        "on",
        "-ctk",
        kv_type,
        "-ctv",
        kv_type,
    ]
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    fitted = ""
    lines = proc.stdout.splitlines()
    for index, line in enumerate(lines):
        if "printing fitted CLI arguments" in line and index + 1 < len(lines):
            fitted = lines[index + 1].strip()
            break
    if not fitted:
        for line in reversed(lines):
            if line.strip():
                fitted = line.strip()
                break
    return {
        "context_tokens": context,
        "kv_cache": kv_type,
        "returncode": proc.returncode,
        "fit": fitted,
        "ok": proc.returncode == 0,
        "command": " ".join(shlex.quote(part) for part in cmd),
    }


def write_markdown(path, data):
    lines = [
        "# Fit Matrix",
        "",
        f"Generated: {data['timestamp_utc']}",
        "",
        "| model | context | KV | ok | fit |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for result in data["results"]:
        lines.append(
            f"| {result['model']} | {result['context_tokens']} | {result['kv_cache']} | "
            f"{'yes' if result['ok'] else 'no'} | `{result['fit']}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run llama-fit-params across model/context/KV combinations.")
    parser.add_argument("--llama-fit-params", default="llama-fit-params")
    parser.add_argument("--models-root", default=".")
    parser.add_argument("--model", action="append", choices=sorted(DEFAULT_MODELS), default=None)
    parser.add_argument("--context", action="append", type=int, default=None)
    parser.add_argument("--kv", action="append", choices=KV_TYPES, default=None)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output-json", default="artifacts/fit-matrix.json")
    parser.add_argument("--output-md", default="artifacts/fit-matrix.md")
    args = parser.parse_args()

    selected_models = args.model or list(DEFAULT_MODELS)
    contexts = args.context or CONTEXTS
    kv_types = args.kv or KV_TYPES
    root = Path(args.models_root)

    data = {
        "schema": "club-rdna16.fit-matrix.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "results": [],
    }

    for name in selected_models:
        path = root / DEFAULT_MODELS[name]
        if not path.exists():
            data["results"].append({
                "model": name,
                "error": f"missing model file: {path}",
                "ok": False,
            })
            continue
        for context in contexts:
            for kv_type in kv_types:
                result = run_fit(args.llama_fit_params, path, context, kv_type, args.timeout)
                result["model"] = name
                data["results"].append(result)
                print(f"{name} ctx={context} kv={kv_type}: {result['fit']}")

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write_markdown(Path(args.output_md), data)
    print(f"wrote {output_json}")
    print(f"wrote {args.output_md}")


if __name__ == "__main__":
    raise SystemExit(main())
