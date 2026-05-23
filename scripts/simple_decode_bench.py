#!/usr/bin/env python3
import argparse
import json
import time
import urllib.request


PROMPT = """Write a concise technical checklist for validating a local LLM server.
Include health checks, model listing, a short generation test, GPU memory checks,
and one benchmark caveat. Keep it practical."""


def post_json(url, payload, timeout):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Simple OpenAI-compatible decode benchmark.")
    parser.add_argument("--base-url", required=True, help="Example: http://127.0.0.1:8000/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--no-thinking", action="store_true", help="Send Qwen/vLLM enable_thinking=false.")
    args = parser.parse_args()

    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0,
        "max_tokens": args.max_tokens,
    }
    if args.no_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}

    started = time.monotonic()
    result = post_json(f"{args.base_url.rstrip('/')}/chat/completions", payload, args.timeout)
    elapsed = time.monotonic() - started

    usage = result.get("usage") or {}
    completion_tokens = usage.get("completion_tokens")
    if completion_tokens is None:
        content = result["choices"][0]["message"].get("content") or ""
        completion_tokens = len(content.split())

    print(json.dumps({
        "elapsed_seconds": round(elapsed, 3),
        "completion_tokens": completion_tokens,
        "completion_tokens_per_second": round(completion_tokens / elapsed, 3) if elapsed else None,
        "usage": usage,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

