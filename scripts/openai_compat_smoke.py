#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.request


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Smoke test an OpenAI-compatible chat endpoint.")
    parser.add_argument("--base-url", required=True, help="Example: http://127.0.0.1:8000/v1")
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-tokens", type=int, default=64)
    args = parser.parse_args()

    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": "Reply with exactly: rdna16 ok"}],
        "temperature": 0,
        "max_tokens": args.max_tokens,
    }

    try:
        result = post_json(f"{args.base_url.rstrip('/')}/chat/completions", payload)
    except urllib.error.HTTPError as exc:
        sys.stderr.write(exc.read().decode("utf-8", errors="replace") + "\n")
        return 1

    message = result["choices"][0]["message"]
    content = (message.get("content") or "").strip()
    reasoning = message.get("reasoning") or message.get("reasoning_content")
    print(json.dumps({"content": content, "has_reasoning": bool(reasoning)}, indent=2))
    return 0 if "rdna16 ok" in content.lower() else 2


if __name__ == "__main__":
    raise SystemExit(main())

