#!/usr/bin/env python3
"""Choose the highest useful context from raw high-context profile receipts.

A failed high tier never erases lower passing tiers. This writes a local candidate
summary by default; --publish is intentionally required to write public evidence.

Every receipt is checked for AMD operating-point identity against the preset
manifest it claims to validate: backend, power profile, exact GPU, gfx target,
and model. Receipts that do not match the preset are refused, so a review can
never accidentally promote evidence recorded under a different serving point.
"""
import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRESET_MAP = {
    "backend": ("runtime", "backend"),
    "power_profile": ("hardware", "power_profile"),
    "gpu_model": ("hardware", "gpu_model"),
    "gfx_target": ("hardware", "architecture_target"),
}


def load_preset(preset):
    path = ROOT / "data" / "presets" / f"{preset}.json"
    if not path.is_file():
        raise SystemExit(f"preset manifest not found: {path} (expected data/presets/{preset}.json)")
    return json.loads(path.read_text(encoding="utf-8"))


def read_receipt(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("not an object")
    if value.get("kind") != "raw-high-context-profile":
        raise ValueError("not a raw high-context profile receipt")
    return value


def preset_identity(preset_value):
    return {key: (preset_value.get(section) or {}).get(field) for key, (section, field) in PRESET_MAP.items()}


def check_receipt_identity(receipt, preset_value):
    expected = preset_identity(preset_value)
    runtime = receipt.get("runtime") or {}
    errors = []
    for key, field in (("backend", "backend"), ("power_profile", "power_profile"), ("gpu_model", "gpu_model"), ("gfx_target", "gfx_target")):
        actual = runtime.get(field)
        if not actual:
            errors.append(f"missing runtime.{field}")
        elif expected.get(key) is not None and actual != expected[key]:
            errors.append(f"runtime.{field} {actual!r} does not match preset {expected[key]!r}")
    if receipt.get("model") and (expected_model := (preset_value.get("model") or {}).get("id")):
        if receipt["model"] != expected_model:
            errors.append(f"model {receipt['model']!r} does not match preset model.id {expected_model!r}")
    return errors


def median(values):
    values = [float(value) for value in values if isinstance(value, (int, float)) and value > 0]
    return round(statistics.median(values), 3) if values else None


def main():
    parser = argparse.ArgumentParser(description="Review raw context receipts and select the highest useful tier.")
    parser.add_argument("--preset", required=True)
    parser.add_argument("--input", action="append", required=True, help="Receipt JSON file or directory. Repeat as needed.")
    parser.add_argument("--output", default="", help="Local candidate output, default .local/bench/<preset>/review.json")
    parser.add_argument("--publish", action="store_true", help="Write reviewed evidence into data/evidence/candidates instead of .local.")
    args = parser.parse_args()

    preset_value = load_preset(args.preset)
    files = []
    for raw in args.input:
        path = Path(raw)
        files.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    receipts, errors = [], []
    for path in files:
        try:
            receipt = read_receipt(path)
            if receipt.get("preset") != args.preset:
                raise ValueError(f"belongs to preset {receipt.get('preset')!r}")
            identity_errors = check_receipt_identity(receipt, preset_value)
            if identity_errors:
                raise ValueError("runtime identity mismatch against preset: " + "; ".join(identity_errors))
            receipts.append((path, receipt))
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if not receipts:
        raise SystemExit("no receipts found")

    by_context = {}
    for path, receipt in receipts:
        by_context.setdefault(receipt["context_tokens"], []).append((path, receipt))
    tiers = []
    for context, group in sorted(by_context.items()):
        useful = [item for _, item in group if (item.get("summary") or {}).get("useful")]
        tiers.append({
            "context_tokens": context,
            "receipts": [str(path) for path, _ in group],
            "attempts": len(group),
            "useful_attempts": len(useful),
            "validated": bool(useful),
            "median_decode_tok_s": median((item.get("summary") or {}).get("median_sustained_decode_tok_s") for item in useful),
            "median_prompt_tok_s": median((item.get("summary") or {}).get("median_prompt_tok_s") for item in useful),
            "failures": [
                {"retrieval": (item.get("summary") or {}).get("retrieval_passed"), "sustained": (item.get("summary") or {}).get("sustained_passed"), "prompt_coverage": (item.get("summary") or {}).get("prompt_coverage_passed")}
                for _, item in group if not (item.get("summary") or {}).get("useful")
            ],
        })
    validated = [tier for tier in tiers if tier["validated"]]
    highest = max(validated, key=lambda tier: tier["context_tokens"]) if validated else None
    summary = {
        "schema_version": "1.0",
        "kind": "context-fit-review",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "preset": args.preset,
        "runtime_identity": preset_identity(preset_value),
        "publication_status": "candidate" if not args.publish else "reviewed-evidence-candidate",
        "highest_useful_context_tokens": highest["context_tokens"] if highest else None,
        "highest_useful_summary": highest,
        "tiers": tiers,
        "decision": "No context tier passed all required checks." if not highest else f"Highest useful validated tier is {highest['context_tokens']} tokens. Higher failed tiers remain recorded as diagnostics, not as a claim that lower tiers do not fit.",
    }
    output = Path(args.output) if args.output else (
        Path("data/evidence/candidates") / f"{args.preset}-context-fit.json" if args.publish else Path(".local/bench") / args.preset / "context-fit-review.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {'reviewed candidate' if args.publish else 'local review'} to {output}")
    print(summary["decision"])
    return 0 if highest else 2


if __name__ == "__main__":
    raise SystemExit(main())
