#!/usr/bin/env python3
import argparse
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def post_json(url, payload, timeout, api_key):
    data = json.dumps(payload).encode("utf-8")
    headers = {"content-type": "application/json"}
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def build_prompt(target_chars, needle, salt):
    prefix = (
        "You are testing long-context retrieval for a local model. "
        "Somewhere in this context there is a key. Remember it exactly.\n"
        f"Run salt: {salt}\n\n"
    )
    block = (
        "Benchmark filler: record hardware, ROCm version, llama.cpp commit, model file, quant, context, "
        "KV cache, batch size, ubatch size, MTP settings, and all caveats before comparing results.\n"
    )
    middle = f"\nIMPORTANT KEY: {needle}\n\n"
    suffix = "\nQuestion: What exact key appeared after IMPORTANT KEY? Reply with only the key."
    left = max(target_chars - len(prefix) - len(middle) - len(suffix), 0)
    half = left // 2
    before = (block * ((half // len(block)) + 1))[:half]
    after = (block * (((left - half) // len(block)) + 1))[: left - half]
    return prefix + before + middle + after + suffix


def main():
    parser = argparse.ArgumentParser(description="Run a synthetic long-context needle retrieval request.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088/v1")
    parser.add_argument("--api-key", default=os.environ.get("LLAMA_API_KEY", ""))
    parser.add_argument("--model", required=True)
    parser.add_argument("--target-chars", type=int, default=300000)
    parser.add_argument("--needle", default="CLUB-RDNA16-NEEDLE-194")
    parser.add_argument("--salt", default="")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--no-thinking", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    salt = args.salt or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    prompt = build_prompt(args.target_chars, args.needle, salt)
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "stream": False,
    }
    if args.no_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    started = time.monotonic()
    response = post_json(f"{args.base_url.rstrip('/')}/chat/completions", payload, args.timeout, args.api_key)
    elapsed = time.monotonic() - started
    message = response.get("choices", [{}])[0].get("message", {})
    content = message.get("content") or ""
    usage = response.get("usage") or {}
    timings = response.get("timings") or {}
    result = {
        "schema": "club-rdna16.long-context-needle.v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "target_chars": args.target_chars,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "wall_seconds": round(elapsed, 3),
        "prompt_tok_s": timings.get("prompt_per_second"),
        "decode_tok_s": timings.get("predicted_per_second"),
        "needle": args.needle,
        "salt": salt,
        "answer": content.strip(),
        "passed": args.needle in content,
    }
    print(json.dumps(result, indent=2))
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
