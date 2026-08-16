#!/usr/bin/env python3
"""Validate reviewed public evidence bundles for canonical presets.

Enforces the full evidence schema (context, checks, metrics), published-bundle
constraints, AMD operating-point identity (preset -> bundle -> receipt), and
scans every JSON under data/evidence/ - including orphaned receipts - for the
forbidden raw/private fields (request_nonce, response, reasoning_response).
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {"schema_version", "id", "preset", "status", "provenance", "hardware", "runtime", "context", "evidence", "caveats"}
STATUSES = {"candidate", "published", "archived"}
PROVENANCE = {"seed-tested", "community-verified"}
BACKENDS = {"ROCm/HIP", "Vulkan", "CUDA", "other"}
POWER_PROFILES = {"COMPUTE", "3D_FULL_SCREEN", "default", "unknown"}
FORBIDDEN_RECEIPT_FIELDS = {"request_nonce", "response", "reasoning_response"}
PRIVATE_RE = re.compile(
    r"Bearer [A-Za-z0-9._-]{10,}|hf_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{10,}|"
    r"(192\.168|10\.[0-9]|172\.(1[6-9]|2[0-9]|3[0-1]))\.|"
    r"/(home|Users|root)/[^\s'\"]+"
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def find_forbidden_receipt_fields(value, prefix=""):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if key in FORBIDDEN_RECEIPT_FIELDS:
                found.append(path)
            found.extend(find_forbidden_receipt_fields(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_forbidden_receipt_fields(child, f"{prefix}[{index}]"))
    return found


def find_private_text(value, prefix=""):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            found.extend(find_private_text(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_private_text(child, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        match = PRIVATE_RE.search(value)
        if match:
            found.append(prefix)
    return found


def forbidden_scan(value):
    return find_forbidden_receipt_fields(value), find_private_text(value)


def median(values):
    values = [float(value) for value in values if isinstance(value, (int, float)) and value > 0]
    return round(statistics.median(values), 3) if values else None


def same_number(actual, expected, tolerance=0.001):
    return (isinstance(actual, (int, float)) and isinstance(expected, (int, float))
            and abs(float(actual) - float(expected)) <= tolerance)


def load_presets():
    presets = {}
    for path in sorted((ROOT / "data" / "presets").glob("*.json")):
        try:
            presets[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return presets


def validate_bundle(path, value, presets):
    errors = []
    missing = sorted(REQUIRED - set(value))
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
        return errors, []
    if value.get("schema_version") != "1.0":
        errors.append(f"{path}: schema_version must be 1.0")
    status = value.get("status")
    if status not in STATUSES:
        errors.append(f"{path}: invalid status")
    if value.get("provenance") not in PROVENANCE:
        errors.append(f"{path}: invalid provenance")
    preset = presets.get(value.get("preset"))
    if preset is None:
        errors.append(f"{path}: unknown preset {value.get('preset')!r}")

    hardware = value.get("hardware") or {}
    runtime = value.get("runtime") or {}
    if hardware.get("gpu_model") and not hardware.get("gpu_model").strip():
        errors.append(f"{path}: hardware.gpu_model must name the exact GPU")
    if hardware.get("power_profile") not in POWER_PROFILES:
        errors.append(f"{path}: hardware.power_profile must be one of {', '.join(sorted(POWER_PROFILES))}")
    if runtime.get("backend") not in BACKENDS:
        errors.append(f"{path}: runtime.backend must be one of {', '.join(sorted(BACKENDS))}")

    if preset is not None:
        preset_hardware = preset.get("hardware") or {}
        preset_runtime = preset.get("runtime") or {}
        for key, expected in (("gpu_count", preset_hardware.get("gpu_count")), ("gpu_model", preset_hardware.get("gpu_model")), ("architecture_target", preset_hardware.get("architecture_target")), ("power_profile", preset_hardware.get("power_profile"))):
            if hardware.get(key) != expected:
                errors.append(f"{path}: hardware.{key} does not match preset {value.get('preset')!r} (bundle {hardware.get(key)!r} vs preset {expected!r})")
        if runtime.get("backend") != preset_runtime.get("backend"):
            errors.append(f"{path}: runtime.backend does not match preset {value.get('preset')!r} (bundle {runtime.get('backend')!r} vs preset {preset_runtime.get('backend')!r})")

    context = value.get("context") or {}
    highest = context.get("highest_useful_tokens")
    if not isinstance(highest, int) or highest < 1:
        errors.append(f"{path}: context.highest_useful_tokens must be positive")
    if not isinstance(context.get("validated_for"), str) or not context["validated_for"].strip():
        errors.append(f"{path}: context.validated_for is required")
    actual = context.get("actual_prompt_tokens")
    if not isinstance(actual, (int, dict)):
        errors.append(f"{path}: context.actual_prompt_tokens must be an integer or workload map")
    elif isinstance(actual, dict):
        for key in ("retrieval", "sustained_generation"):
            if not isinstance(actual.get(key), int) or actual[key] < 1:
                errors.append(f"{path}: context.actual_prompt_tokens.{key} must be positive")
    for key in ("server_effective_tokens", "server_configured_tokens"):
        if key in context and context[key] is not None and not isinstance(context[key], int):
            errors.append(f"{path}: context.{key} must be an integer or null")

    checks = (value.get("evidence") or {}).get("checks") or {}
    if not isinstance(checks.get("retrieval_repeats"), int) or checks["retrieval_repeats"] < 1:
        errors.append(f"{path}: evidence.checks.retrieval_repeats must be positive")
    sustained = checks.get("sustained_generation_repeats")
    if not isinstance(sustained, int) or sustained < 0:
        errors.append(f"{path}: evidence.checks.sustained_generation_repeats must be zero or positive")
    if not checks.get("prompt_cache_disabled"):
        errors.append(f"{path}: evidence.checks.prompt_cache_disabled must be true")
    if not checks.get("unique_leading_request_nonce"):
        errors.append(f"{path}: evidence.checks.unique_leading_request_nonce must be true")
    if not isinstance(checks.get("thinking_disabled_explicitly"), bool):
        errors.append(f"{path}: evidence.checks.thinking_disabled_explicitly must be a boolean")
    for key in ("retrieval_output_tokens", "sustained_output_tokens", "minimum_generated_tokens"):
        if not isinstance(checks.get(key), int) or checks[key] < 1:
            errors.append(f"{path}: evidence.checks.{key} must be positive")

    metrics = (value.get("evidence") or {}).get("metrics") or {}
    for name in ("median_prefill_tok_s", "median_decode_tok_s"):
        if not isinstance(metrics.get(name), (int, float)) or metrics[name] <= 0:
            errors.append(f"{path}: evidence.metrics.{name} must be positive")
    for name in ("retrieval_decode_tok_s",):
        if name in metrics and (not isinstance(metrics[name], (int, float)) or metrics[name] <= 0):
            errors.append(f"{path}: evidence.metrics.{name} must be positive")
    acceptance = metrics.get("median_draft_acceptance_rate")
    if acceptance is not None and (not isinstance(acceptance, (int, float)) or not 0 <= acceptance <= 1):
        errors.append(f"{path}: evidence.metrics.median_draft_acceptance_rate must be in [0, 1]")

    caveats = value.get("caveats") or []
    if not isinstance(caveats, list) or not all(isinstance(item, str) for item in caveats):
        errors.append(f"{path}: caveats must be a list of strings")

    receipts = value.get("source_receipts") or []
    if not isinstance(receipts, list):
        errors.append(f"{path}: source_receipts must be a list")
        receipts = []
    if status == "published":
        if not receipts:
            errors.append(f"{path}: published evidence requires source_receipts")
        if sustained < 1:
            errors.append(f"{path}: published evidence requires sustained-generation checks")
        if checks.get("visible_final_content_required") is not True:
            errors.append(f"{path}: published evidence requires visible_final_content_required true")
        if context.get("server_effective_tokens") is None:
            errors.append(f"{path}: published evidence requires context.server_effective_tokens")
        if metrics.get("retrieval_decode_tok_s") is None:
            errors.append(f"{path}: published evidence requires evidence.metrics.retrieval_decode_tok_s")
    return errors, receipts


def validate_receipt(path, value, presets):
    errors = []
    if not isinstance(value, dict):
        return [f"{path}: receipt must be an object"]
    if value.get("kind") != "raw-high-context-profile":
        errors.append(f"{path}: receipt kind must be raw-high-context-profile")
    if value.get("schema_version") != "1.0":
        errors.append(f"{path}: receipt schema_version must be 1.0")
    preset = value.get("preset")
    preset_value = presets.get(preset)
    if preset_value is None:
        errors.append(f"{path}: receipt references unknown preset {preset!r}")
    expected_model = ((preset_value or {}).get("model") or {}).get("id")
    if not value.get("model"):
        errors.append(f"{path}: receipt model is required")
    elif expected_model and value["model"] != expected_model:
        errors.append(f"{path}: receipt model {value['model']!r} does not match preset model {expected_model!r}")
    if not isinstance(value.get("context_tokens"), int) or value["context_tokens"] < 1:
        errors.append(f"{path}: receipt context_tokens must be positive")
    for key in ("active_server_context_tokens", "active_server_parallel", "effective_request_context_tokens"):
        if not isinstance(value.get(key), int) or value[key] < 1:
            errors.append(f"{path}: receipt {key} must be positive")
    if not isinstance(value.get("requested_context_matches_server"), bool):
        errors.append(f"{path}: receipt requested_context_matches_server must be a boolean")
    runtime = value.get("runtime") or {}
    for key in ("backend", "power_profile", "gpu_model", "gfx_target"):
        if not runtime.get(key):
            errors.append(f"{path}: receipt runtime.{key} is required for AMD operating-point identity")
    policy = value.get("policy") or {}
    if policy.get("prompt_cache_disabled") is not True:
        errors.append(f"{path}: receipt policy.prompt_cache_disabled must be true")
    if policy.get("unique_leading_request_nonce") is not True:
        errors.append(f"{path}: receipt policy.unique_leading_request_nonce must be true")
    if not isinstance(policy.get("disable_thinking"), bool):
        errors.append(f"{path}: receipt policy.disable_thinking must be a boolean")
    for key in ("retrieval_output_tokens", "sustained_output_tokens", "minimum_generated_tokens"):
        if not isinstance(policy.get(key), int) or policy[key] < 1:
            errors.append(f"{path}: receipt policy.{key} must be positive")
    summary = value.get("summary") or {}
    if not isinstance(summary.get("useful"), bool):
        errors.append(f"{path}: receipt summary.useful must be a boolean")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append(f"{path}: receipt cases must be a non-empty list")
    return errors


def validate_review(path, value, presets):
    errors = []
    if value.get("kind") != "context-fit-review":
        errors.append(f"{path}: review kind must be context-fit-review")
    if value.get("preset") not in presets:
        errors.append(f"{path}: review references unknown preset {value.get('preset')!r}")
    return errors


def collect_json_files(raw_paths):
    files = []
    for raw in raw_paths:
        path = Path(raw)
        files.extend(sorted(path.rglob("*.json")) if path.is_dir() else [path])
    return files


def main():
    parser = argparse.ArgumentParser(description="Validate data/evidence/*.json bundles and scan every JSON under data/evidence for private/raw fields.")
    parser.add_argument("paths", nargs="*", default=["data/evidence"])
    args = parser.parse_args()
    presets = load_presets()
    files = collect_json_files(args.paths)
    evidence_root = Path("data/evidence")
    if evidence_root.is_dir() and any(Path(raw) == evidence_root or evidence_root in Path(raw).parents for raw in args.paths):
        pass
    else:
        files = list(files) + collect_json_files([str(evidence_root)])
    seen = set()
    errors = []
    referenced_receipts = []
    for path in sorted(files, key=str):
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        try:
            value = load(path)
        except Exception as exc:
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        forbidden, private = forbidden_scan(value)
        if forbidden:
            errors.append(f"{path}: contains forbidden raw/private fields: {', '.join(forbidden)}")
        if private:
            errors.append(f"{path}: contains private/raw text: {', '.join(private)}")
        if isinstance(value, dict) and "evidence" in value and "preset" in value:
            bundle_errors, receipts = validate_bundle(path, value, presets)
            errors.extend(bundle_errors)
            for receipt in receipts:
                referenced_receipts.append((path, value, receipt))
        elif isinstance(value, dict) and value.get("kind") == "raw-high-context-profile":
            errors.extend(validate_receipt(path, value, presets))
        elif isinstance(value, dict) and value.get("kind") == "context-fit-review":
            errors.extend(validate_review(path, value, presets))

    published_support = {}
    for bundle_path, bundle, raw in referenced_receipts:
        receipt_path = Path(raw)
        if not receipt_path.is_file():
            errors.append(f"{bundle_path}: source receipt is missing: {raw!r}")
            continue
        try:
            receipt = load(receipt_path)
        except Exception as exc:
            errors.append(f"{bundle_path}: source receipt is invalid JSON: {raw!r}: {exc}")
            continue
        forbidden, private = forbidden_scan(receipt)
        if forbidden:
            errors.append(f"{bundle_path}: source receipt contains forbidden raw/private fields: {raw!r}: {', '.join(forbidden)}")
        if private:
            errors.append(f"{bundle_path}: source receipt contains private/raw text: {raw!r}: {', '.join(private)}")
        if receipt.get("kind") != "raw-high-context-profile":
            errors.append(f"{bundle_path}: source receipt is not a raw-high-context-profile: {raw!r}")
            continue
        if receipt.get("preset") != bundle.get("preset"):
            errors.append(
                f"{bundle_path}: source receipt preset mismatch: {raw!r}: "
                f"expected {bundle.get('preset')!r}, found {receipt.get('preset')!r}"
            )
        preset = presets.get(bundle.get("preset")) or {}
        expected_model = (preset.get("model") or {}).get("id")
        if expected_model and receipt.get("model") != expected_model:
            errors.append(
                f"{bundle_path}: source receipt model mismatch: {raw!r}: "
                f"expected {expected_model!r}, found {receipt.get('model')!r}"
            )
        expected_parallel = (preset.get("serving") or {}).get("parallel")
        if expected_parallel is not None and receipt.get("active_server_parallel") != expected_parallel:
            errors.append(
                f"{bundle_path}: source receipt parallel mismatch: {raw!r}: "
                f"expected {expected_parallel!r}, found {receipt.get('active_server_parallel')!r}"
            )
        bundle_runtime = bundle.get("runtime") or {}
        bundle_hardware = bundle.get("hardware") or {}
        receipt_runtime = receipt.get("runtime") or {}
        identity = (
            ("backend", bundle_runtime.get("backend"), receipt_runtime.get("backend")),
            ("power_profile", bundle_hardware.get("power_profile"), receipt_runtime.get("power_profile")),
            ("gpu_model", bundle_hardware.get("gpu_model"), receipt_runtime.get("gpu_model")),
            ("gfx_target", bundle_hardware.get("architecture_target"), receipt_runtime.get("gfx_target")),
        )
        for key, expected, actual in identity:
            if actual is None:
                errors.append(f"{bundle_path}: source receipt missing runtime.{key}: {raw!r}")
            elif expected is not None and actual != expected:
                errors.append(f"{bundle_path}: source receipt runtime identity mismatch: {raw!r}: {key} bundle {expected!r} vs receipt {actual!r}")

        if bundle.get("status") != "published":
            continue
        context = bundle.get("context") or {}
        checks = (bundle.get("evidence") or {}).get("checks") or {}
        metrics = (bundle.get("evidence") or {}).get("metrics") or {}
        highest = context.get("highest_useful_tokens")
        reaches_tier = isinstance(receipt.get("context_tokens"), int) and isinstance(highest, int) and receipt["context_tokens"] == highest
        if not reaches_tier or (receipt.get("summary") or {}).get("useful") is not True:
            continue

        support_errors = []
        metadata_pairs = (
            ("active_server_context_tokens", context.get("server_configured_tokens")),
            ("effective_request_context_tokens", context.get("server_effective_tokens")),
        )
        for key, expected in metadata_pairs:
            if receipt.get(key) != expected:
                support_errors.append(f"{key} bundle {expected!r} vs receipt {receipt.get(key)!r}")
        if receipt.get("requested_context_matches_server") is not True:
            support_errors.append("requested_context_matches_server is not true")

        policy = receipt.get("policy") or {}
        policy_pairs = (
            ("prompt_cache_disabled", checks.get("prompt_cache_disabled")),
            ("unique_leading_request_nonce", checks.get("unique_leading_request_nonce")),
            ("disable_thinking", checks.get("thinking_disabled_explicitly")),
            ("retrieval_output_tokens", checks.get("retrieval_output_tokens")),
            ("sustained_output_tokens", checks.get("sustained_output_tokens")),
            ("minimum_generated_tokens", checks.get("minimum_generated_tokens")),
        )
        for key, expected in policy_pairs:
            if policy.get(key) != expected:
                support_errors.append(f"policy.{key} bundle {expected!r} vs receipt {policy.get(key)!r}")

        cases = receipt.get("cases") or []
        retrieval = [case for case in cases if case.get("kind") == "retrieval"]
        sustained_cases = [case for case in cases if case.get("kind") == "sustained"]
        if len(retrieval) != checks.get("retrieval_repeats") or not all(case.get("passed") is True for case in retrieval):
            support_errors.append("retrieval repeat count/pass state does not match bundle")
        if len(sustained_cases) != checks.get("sustained_generation_repeats") or not all(case.get("passed") is True for case in sustained_cases):
            support_errors.append("sustained repeat count/pass state does not match bundle")

        actual_prompts = context.get("actual_prompt_tokens") or {}
        measured_prompts = {
            "retrieval": min((case.get("actual_prompt_tokens") for case in retrieval if isinstance(case.get("actual_prompt_tokens"), int)), default=None),
            "sustained_generation": min((case.get("actual_prompt_tokens") for case in sustained_cases if isinstance(case.get("actual_prompt_tokens"), int)), default=None),
        }
        for key, measured in measured_prompts.items():
            if actual_prompts.get(key) != measured:
                support_errors.append(f"context.actual_prompt_tokens.{key} bundle {actual_prompts.get(key)!r} vs receipt {measured!r}")

        measured_metrics = {
            "median_prefill_tok_s": median(case.get("prompt_tok_s") for case in cases),
            "median_decode_tok_s": median(case.get("decode_tok_s") for case in sustained_cases),
            "retrieval_decode_tok_s": median(case.get("decode_tok_s") for case in retrieval),
            "median_draft_acceptance_rate": median(case.get("draft_acceptance_rate") for case in sustained_cases),
        }
        for key, measured in measured_metrics.items():
            if not same_number(metrics.get(key), measured):
                support_errors.append(f"evidence.metrics.{key} bundle {metrics.get(key)!r} vs receipt {measured!r}")

        if (preset.get("serving") or {}).get("speculation") == "draft-mtp" and not same_number(
            metrics.get("median_draft_acceptance_rate"), measured_metrics.get("median_draft_acceptance_rate")
        ):
            support_errors.append("draft-MTP preset lacks matching acceptance evidence")
        if support_errors:
            errors.append(f"{bundle_path}: source receipt does not support published claims: {raw!r}: {'; '.join(support_errors)}")
        else:
            published_support[bundle_path] = published_support.get(bundle_path, 0) + 1

    published_bundles = {path for path, bundle, _ in referenced_receipts if bundle.get("status") == "published"}
    for bundle_path in sorted(published_bundles - set(published_support)):
        errors.append(f"{bundle_path}: no source receipt reaches context.highest_useful_tokens for a published bundle")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"validated {len(seen)} evidence JSON file(s) and scanned for private/raw fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
