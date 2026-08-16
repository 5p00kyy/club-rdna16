# Preset And Evidence Workflow

club-rdna16 publishes **tested presets**, not every successful benchmark request.

A preset is a configuration someone can copy and use. Evidence is the compact,
reviewed proof that it fits its stated hardware lane, backend, and use case. Raw
benchmark receipts remain useful, but they are local until a maintainer
deliberately promotes an evidence bundle.

## Data Boundaries

| Location | Purpose | Published to Pages? |
| --- | --- | --- |
| `examples/` | Copyable llama.cpp and engine presets | Linked from docs/cards |
| `data/presets/` | Canonical preset manifests | Yes |
| `.local/bench/` | Raw runs, retries, failures, and local reviews | No |
| `data/evidence/` | Reviewed evidence candidates and promoted bundles | Yes, after promotion |
| `data/results/` | Existing benchmark corpus and historical provenance | Explorer only |

Do not write a new routine run into `data/results/` just because it completed.

## AMD Evidence Rules

- The preset manifest must name the **exact GPU model** (`AMD Radeon RX 6900 XT`),
  an **explicit gfx target** (`gfx1030`), the **backend** (`ROCm/HIP` or `Vulkan`),
  and the **power profile** used for the evidence (`COMPUTE`, `3D_FULL_SCREEN`,
  `default`, or `unknown`).
- Evidence recorded on one card is **never generalized** to all 16GB Radeon cards.
  An RX 6900 XT (gfx1030) result is not an RX 9070 XT (gfx1201) result; each needs
  its own measurements.
- `q8_0` KV is the recommendation floor for presets on 16GB Radeon cards. `q5_1` or
  `q4_0` KV variants are exploratory only and must be marked `experimental`.
- Backend lanes are separate: a ROCm/HIP run under `COMPUTE` and a Vulkan run under
  `3D_FULL_SCREEN` are different presets, even when the INI section is identical.

## High-Context Fit

The `high-context` profile validates one unchanged serving preset at a time. It
walks a declared context ladder rather than treating one failed high tier as a
model-wide fit verdict.

At each tier the server must already be launched with that exact context. The
profile then performs uncached retrieval and sustained-generation checks. Every
request includes a unique leading nonce as well as `cache_prompt: false`, so a
server's longest-common-prefix reuse cannot make repeated synthetic prompts look
like fresh prefills. It records actual prompt tokens, prompt/prefill speed,
decode speed, output length, and failures.

A tier is useful only when it:

- reaches the required fraction of its configured context with an uncached prompt;
- passes repeated retrieval checks;
- passes repeated sustained-generation checks with enough client-visible final content;
- sustains the profile's minimum decode speed.

Failures are diagnostic. A failure at 131K does not invalidate a 96K result. The
review script selects the highest passing tier and keeps higher failures visible.

The runner never changes quant, KV type, CPU offload, speculation, backend, power
profile, or other quality-affecting settings to make a tier fit. Those are new
preset candidates. If a preset deliberately runs non-thinking, pass
`--disable-thinking` and record that request-level template setting in the preset
manifest. The runner validates the client-visible final answer separately from
`reasoning_content`: a model that spends its whole output budget reasoning and
produces no final answer has not passed retrieval or useful sustained generation.
Never silently hide reasoning merely to make retrieval look clean.

The retrieval and sustained output allowances are deliberately larger than the
minimum useful final answer. This gives thinking-heavy models enough room to
finish hidden reasoning and still return client-visible content without forcing
concise models to consume the entire allowance. Record both allowances in public
evidence: changing an answer budget is a protocol change, not a retry detail.

## Run A Profile

First validate the preset manifest:

~~~bash
python3 scripts/validate_presets.py data/presets/rx6900xt-qwen36-35b-a3b-iq3xxs-131k-q8-nomtp.json
~~~

Launch the server using the selected preset and context tier. Then run a single
tier. The profile first sends small uncached calibration requests against the
actual tokenizer, estimates the filler needed, and corrects it before the real
checks. It aims slightly above each minimum prompt fraction so nonce and tokenizer
variation cannot turn an otherwise valid repeated check into a one-token miss.
It will not claim a configured context from character-count guesswork.

~~~bash
python3 scripts/run_high_context_profile.py \
  --base-url http://127.0.0.1:8080/v1 \
  --model Qwen3.6-35B-A3B-rdna16-131k-q8kv-nomtp \
  --preset rx6900xt-qwen36-35b-a3b-iq3xxs-131k-q8-nomtp \
  --context-tokens 131072 \
  --backend ROCm/HIP \
  --power-profile COMPUTE \
  --gpu-model "AMD Radeon RX 6900 XT" \
  --gfx-target gfx1030
~~~

`--backend`, `--power-profile`, `--gpu-model`, and `--gfx-target` are recorded in
the raw receipt so the evidence bundle can reproduce the AMD-specific operating
point.

Raw receipts go to `.local/bench/` and are ignored by Git. Repeat at lower or
higher declared tiers as appropriate. A failed tier returns exit code `2`, but
still writes its receipt.

For a fresh dedicated test server, the ladder script can launch one isolated
server process per tier and stop only the process it owns. The launch template
must visibly contain `{context_tokens}`, which prevents a hidden setting change
from being mistaken for a result. It refuses to use an endpoint already serving
the target model, so it cannot replace a shared router/service.

~~~bash
python3 scripts/run_context_ladder.py \
  --base-url http://127.0.0.1:18081/v1 \
  --model Qwen3.6-35B-A3B-rdna16-131k-q8kv-nomtp \
  --preset rx6900xt-qwen36-35b-a3b-iq3xxs-131k-q8-nomtp \
  --server-command-template 'llama-server --model /models/qwen36-35b-a3b-iq3xxs.gguf --ctx-size {context_tokens} --cache-type-k q8_0 --cache-type-v q8_0 --n-gpu-layers 99 --port 18081'
~~~

By default, the ladder stops after the first unusable tier and the review still
selects the highest lower passing tier. Use `--keep-going` only for diagnostic
work; it does not turn a failed tier into a viable result. Use `--start-at` with
a declared rung when an existing reliable result already establishes the lower
bound, so a refresh can concentrate on the next meaningful range.

Review all receipts for that preset:

~~~bash
python3 scripts/review_context_fit.py \
  --preset rx6900xt-qwen36-35b-a3b-iq3xxs-131k-q8-nomtp \
  --input .local/bench/rx6900xt-qwen36-35b-a3b-iq3xxs-131k-q8-nomtp
~~~

This writes a local candidate review. It does not publish anything.

## Promotion

Promotion is a maintainer decision after inspecting the exact preset, raw
receipts, quality/caveat evidence, and whether the recipe genuinely improves the
community guide. A promoted bundle should describe the highest useful context,
median metrics, proof checks, caveats, and source receipts.

To publish:

1. Copy the raw receipt for the chosen tier into
   `data/evidence/receipts/<preset>-<date>.json`, **removing** `request_nonce`,
   `response`, and `reasoning_response` from every case, plus any private text.
2. Write the evidence bundle into `data/evidence/<preset>-<tier>.json` with
   `status: "published"`, `provenance`, context, checks, metrics, and
   `source_receipts` pointing at the sanitized receipt.
3. Run `python3 scripts/validate_evidence.py data/evidence` - it rejects receipts
   that still contain private/raw fields or mismatch the preset.
4. Optionally promote the preset status to `recommended` or `alternative` in
   `data/presets/`; `recommended` is never assigned by the benchmark runner.

`data/evidence/` contains only reviewed candidate or published bundles, while raw
receipts remain local. `scripts/build_preset_data.py` builds compact preset cards
from those manifests without reading routine benchmark rows. The site shows only
`published` evidence in the "tested presets" grid.

Community submissions may be raw receipts, reproduction evidence, or new preset
candidates. Multi-GPU community lanes are welcome, including 3x/4x+ and mixed
systems, but must record PCIe topology and tensor/TP configuration and are not
presented as seed-system reproductions.
