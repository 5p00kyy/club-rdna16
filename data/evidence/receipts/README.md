# Sanitized public receipts

This directory holds the **sanitized public copies** of raw high-context profile
receipts that published evidence bundles reference.

- Raw receipts from `scripts/run_high_context_profile.py` default to the ignored
  `.local/bench/<preset>/` tree. They contain `request_nonce`, `response`, and
  `reasoning_response` fields and must never be committed here as-is.
- To promote evidence, a maintainer writes a sanitized copy that removes
  `request_nonce`, `response`, and `reasoning_response`, then points the evidence
  bundle at the sanitized copy via `source_receipts`.
- `scripts/validate_evidence.py` rejects any bundle whose source receipt still
  contains those private fields, leaks private IPs/paths, or references a preset that
  does not match the bundle.

No public receipts exist yet. Everything recorded so far is seed benchmark data under
`data/results/`, which is separate from preset-fit evidence.
