#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_result_file(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def main():
    parser = argparse.ArgumentParser(description="Build static site data from data/results/*.json.")
    parser.add_argument("--results-dir", default="data/results")
    parser.add_argument("--output", default="site/data/results.json")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results = []
    for path in sorted(results_dir.glob("*.json")):
        for item in load_result_file(path):
            item = dict(item)
            item["_source_file"] = str(path)
            results.append(item)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(results)} result(s) to {output}")


if __name__ == "__main__":
    raise SystemExit(main())
