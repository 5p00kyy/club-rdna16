#!/usr/bin/env bash
set -euo pipefail

python3 -m py_compile scripts/*.py
shopt -s nullglob
bash_files=(scripts/*.sh examples/*.sh)
if [[ "${#bash_files[@]}" -gt 0 ]]; then
  bash -n "${bash_files[@]}"
fi
python3 scripts/validate_results.py data/results
python3 scripts/build_site_data.py

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  search=(git grep -nE)
else
  search=(rg -n)
fi

if "${search[@]}" 'Bearer [A-Za-z0-9._-]{20,}|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|(192\.168|10\.[0-9]|172\.(1[6-9]|2[0-9]|3[0-1]))\.|/(home|Users|root)/[^[:space:]'"'"'"\\]+'; then
  echo "Review the matches above. Placeholders may be fine; real secrets/internal hosts are not." >&2
  exit 1
fi

echo "repo checks passed"
