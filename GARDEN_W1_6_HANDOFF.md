# GARDEN_W1_6_HANDOFF.md

**Unit:** W1.6 — End-to-end test pack + Gate B evidence packet.
**Branch:** `w1/gate-b-packet` · **PR:** [#33](https://github.com/mschwar/Garden-of-Wisdom/pull/33) ·
**Merge:** `0d8f5e5`.
**Date:** 2026-09-13.

## Summary

W1.6 is the last unit of the wave. It does not add a new surface: it proves the loop W1.1–W1.5
built works as one reproducible whole, and packages that proof as the **Gate B evidence packet**.
The deliverable is a deterministic, clean-clone, one-command acceptance run —
`scripts/check_garden_e2e.py`, **96 checks** — that drives the whole loop through the real W1.3 /
W1.4 / W1.5 CLIs as subprocesses inside a throwaway temp dir and asserts the Gate B pass condition
verbatim: *"a representative batch of messy manual submissions can be ingested and reviewed while
preserving originals, provenance, decision history, and duplicate hints. No curation action may
imply verification."*

**W1 is COMPLETE. The Gate B packet is submitted. W2 is not started.**

## What landed

- `scripts/check_garden_e2e.py` — the end-to-end acceptance run (**96 checks**, both interpreters,
  stdlib-only, exit 0/1, throwaway temp dir).
- `docs/program/W1_6_E2E_TEST_PACK.md` — the design doc (messy batch, assertion pipeline, negative
  controls).
- `docs/program/W1_6_GATE_B_PACKET.md` — the Gate B evidence packet, mirroring `W0_GATE_REPORT.md`'s
  shape (criteria item-by-item, required artifacts, evidence, negative controls, carried-forward
  risks status, stop point).
- `docs/DECISIONS.md` / `docs/queue.md` / `docs/RUNBOOK.md` — close-out updates.
- This handoff.

**No migration** (W1.1's exact-ledger assertion `["0001_create_core"]` is untouched). **No populated
store mirror is committed** — reproducibility is proved by the e2e's temp-dir round-trip from a clean
clone (W1.3 decision). `quotes.csv`/`sources.csv` untouched (`5675d7e6…` / `10b4c156…`).

## The messy batch (real corpus + controlled mess)

Gate B says "representative batch of messy manual submissions". The batch is both real-corpus and
controlled-messy:

- **Row 320** (a literal `_` placeholder glyph, *Mitákuye Oyás_i_*) and **row 21** (a curly
  apostrophe) are read **verbatim from `quotes.csv` at runtime** — the corpus's own most awkward
  bytes — so the loop is proved against the corpus's actual hard shapes.
- Controlled messy shapes: a **wrong author**, **leading/trailing whitespace**, a **missing
  citation** (omitted flag → `none` sentinel), a **near-duplicate text pair** (must produce a hint),
  and two unrelated rows sharing the generic **`Oral Tradition`** label (must produce **no**
  reference hint — the W1.4 false-positive fix).

Every expected value is derived from `quotes.csv` or the submitted batch itself — nothing hard-coded;
a fixture that stops narrowing fails loudly rather than passing vacuously.

## The assertion pipeline

1. **Submission** (W1.3): every messy submission accepted; one capture + one candidate each; no
   decision row.
2. **Originals preserved verbatim**: every capture byte-identical to the submitted text; the `_`
   glyph, curly apostrophe, wrong author, leading whitespace and a missing citation's `none` sentinel
   all survive on the capture; provenance (method, timestamp) recorded; a whole-export snapshot taken.
3. **Normalize + hints** (W1.4): both accepted; the whole `[captures]` export section byte-identical
   after **both** (the capture is never touched); the glyph reported and preserved in the proposal;
   whitespace collapsed with a named note; the near-duplicate pair produces a hint; the generic
   `Oral Tradition` pair produces **no** reference hint; every hint has a basis; hint generation
   writes no decision row and leaves every candidate `curation_state='new'` (a hint is never a state).
4. **Review** (W1.5): accept/hold/reject/duplicate/reopen driven through the CLI; the full `accept →
   reject` reversal records exactly `['T-C1','T-P1','T-C8','T-P7']` and strands no dimension; a
   rejected candidate keeps its capture and candidate readable.
5. **Decision history survives**: every decision row carries actor/from/to/transition_id/reason/
   timestamp; exactly 10 audit rows; the `decisions` log re-proven append-only (UPDATE/DELETE
   refused).
6. **No curation action implies verification**: after every decision every candidate's
   `research_state` is still `not_started`; no decision row writes or implies a research state;
   corpus stays in the W1 vocabulary (`candidate_only`/`eligible`).
7. **Reproducibility**: the store export (`garden.export/1`) round-trips (write → import → re-export
   byte-identical) and the store's own `verify` passes.
8. **Clean-tree discipline**: `quotes.csv`/`sources.csv` byte-identical before/after, `validate_quotes.py`
   exits 0, nothing written outside the temp dir (in particular no store in the repo root).

## Acceptance evidence

Both interpreters, and `quotes.csv`/`sources.csv` byte-identical (`5675d7e6…` / `10b4c156…`):

```text
$ python3 scripts/check_garden_e2e.py
scratch: /var/folders/kc/…/garden-e2e-check-b4cvfbf8
PASS: quotes.csv is readable as CSV
PASS: the store is created from empty

-- 1. the messy manual submission batch --
PASS: the glyph fixture really contains a literal `_` placeholder
PASS: the curly fixture really contains a curly quote
PASS: messy submission cand-G01 is accepted by the real W1.3 CLI
PASS: messy submission cand-G02 is accepted by the real W1.3 CLI
PASS: messy submission cand-W01 is accepted by the real W1.3 CLI
PASS: messy submission cand-W02 is accepted by the real W1.3 CLI
PASS: messy submission cand-N01 is accepted by the real W1.3 CLI
PASS: messy submission cand-N02 is accepted by the real W1.3 CLI
PASS: messy submission cand-N03 is accepted by the real W1.3 CLI
PASS: messy submission cand-D01 is accepted by the real W1.3 CLI
PASS: messy submission cand-D02 is accepted by the real W1.3 CLI
PASS: the batch produced 9 captures and 9 candidates
PASS: submission alone wrote no decision row

-- 2. originals are preserved verbatim (nothing trimmed, glyph-fixed, or quote-normalized) --
PASS: cand-G01: capture cap-G01 is byte-identical to the submitted text
PASS: cand-G02: capture cap-G02 is byte-identical to the submitted text
PASS: cand-W01: capture cap-W01 is byte-identical to the submitted text
PASS: cand-W02: capture cap-W02 is byte-identical to the submitted text
PASS: cand-N01: capture cap-N01 is byte-identical to the submitted text
PASS: cand-N02: capture cap-N02 is byte-identical to the submitted text
PASS: cand-N03: capture cap-N03 is byte-identical to the submitted text
PASS: cand-D01: capture cap-D01 is byte-identical to the submitted text
PASS: cand-D02: capture cap-D02 is byte-identical to the submitted text
PASS: the `_` placeholder glyph survives the capture byte-for-byte (never guessed)
PASS: the curly apostrophe survives the capture byte-for-byte
PASS: a wrong author is preserved on the capture (the encounter, not a correction)
PASS: leading whitespace is preserved verbatim on the capture
PASS: a missing citation becomes the 'none' sentinel on the capture (absence, not empty)
PASS: capture provenance (method, timestamp with offset) is preserved on the capture
PASS: the store export is deterministic before any normalization (byte-identical snapshot)

-- 3. normalize --all then hints --all (W1.4) --
PASS: normalize --all is accepted
PASS: the whole [captures] export section is byte-identical after normalize --all
PASS: the glyph is reported in the normalization note and preserved in the proposal
PASS: the curly quote is canonicalized in the proposal and its change is noted
PASS: whitespace is collapsed/trimmed in the proposal with a named note
PASS: normalize wrote no decision row
PASS: hints --all is accepted
PASS: the near-duplicate pair cand-N02/N03 produces a duplicate hint
PASS: two unrelated rows sharing the generic 'Oral Tradition' label produce NO reference hint
PASS: every duplicate hint carries a basis string
PASS: hint generation wrote no decision row
PASS: after hints, every candidate is still curation_state='new' (a hint is never a state)
PASS: the [captures] export section is still byte-identical after hints --all

-- 4. review (W1.5): every decision audited, reversal strands no dimension --
PASS: accept cand-G01 (exit 0)
PASS: accept sets curation=accepted and fires T-P1 to corpus=eligible
PASS: accept cand-G01 recorded exactly ['T-C1', 'T-P1']
PASS: hold cand-N01 (exit 0)
PASS: hold sets curation=hold (no corpus change)
PASS: hold cand-N01 recorded T-C2
PASS: reject cand-W01 (exit 0)
PASS: reject sets curation=rejected
PASS: the rejected candidate still reads back with its verbatim capture
PASS: show still renders the rejected candidate and its capture
PASS: duplicate cand-D01 (exit 0)
PASS: duplicate sets curation=duplicate
PASS: duplicate cand-D01 recorded T-C4
PASS: accept cand-N02 (exit 0)
PASS: accept cand-N02 fired T-P1 to eligible
PASS: reject cand-N02 (reversal, exit 0)
PASS: the reversal recorded exactly ['T-C1', 'T-P1', 'T-C8', 'T-P7']
PASS: the reversal strands no dimension: curation=rejected, corpus=candidate_only
PASS: reopen cand-W01 (exit 0)
PASS: reopen returns a rejected candidate to new (T-C10)
PASS: reopen cand-W01 recorded ['T-C3', 'T-C10']
PASS: no record has curation hold/rejected/duplicate while corpus is eligible/canonical

-- 5. decision history survives, every decision audited, append-only --
PASS: cand-G01: every decision row carries actor/from/to/transition_id/reason/timestamp
PASS: cand-G01: every decision row carries actor/from/to/transition_id/reason/timestamp
PASS: cand-N02: every decision row carries actor/from/to/transition_id/reason/timestamp
PASS: cand-N02: every decision row carries actor/from/to/transition_id/reason/timestamp
PASS: cand-N02: every decision row carries actor/from/to/transition_id/reason/timestamp
PASS: cand-N02: every decision row carries actor/from/to/transition_id/reason/timestamp
PASS: the review produced exactly 10 audited decision rows (got 10)
PASS: decisions rejects UPDATE (decisions is append-only: UPDATE rejected)
PASS: decisions rejects DELETE (decisions is append-only: DELETE rejected)
PASS: no decision row changed after the rejected writes

-- 6. no curation action implies verification (research stays not_started) --
PASS: after every decision, every candidate's research_state is still 'not_started'
PASS: no decision row writes or implies a research state
PASS: cand-D01: corpus_state stays in the W1 vocabulary (candidate_only/eligible)
PASS: cand-D02: corpus_state stays in the W1 vocabulary (candidate_only/eligible)
PASS: cand-G01: corpus_state stays in the W1 vocabulary (candidate_only/eligible)
PASS: cand-G02: corpus_state stays in the W1 vocabulary (candidate_only/eligible)
PASS: cand-N01: corpus_state stays in the W1 vocabulary (candidate_only/eligible)
PASS: cand-N02: corpus_state stays in the W1 vocabulary (candidate_only/eligible)
PASS: cand-N03: corpus_state stays in the W1 vocabulary (candidate_only/eligible)
PASS: cand-W01: corpus_state stays in the W1 vocabulary (candidate_only/eligible)
PASS: cand-W02: corpus_state stays in the W1 vocabulary (candidate_only/eligible)

-- 7. the store export round-trips (garden.export/1) --
PASS: write_export wrote the same bytes the in-memory export returned
PASS: the export imports into a fresh store
PASS: re-export after import is byte-identical to the original (round-trip lossless)
PASS: the store's own verify (export -> re-import -> compare) passes

-- 8. the whole loop is one self-contained command from a clean tree --
PASS: the run did not create a store in the repo (a clean clone reproduces it via --dir)
PASS: quotes.csv and sources.csv are byte-identical before and after the whole loop
PASS: validate_quotes.py still exits 0 after the whole loop
PASS: no store was created in the repo root (the loop only ever wrote to the temp --dir)
PASS: nothing was written outside the stores and scratch inputs

RESULT: PASS (a messy batch is ingested, normalized, hinted and reviewed while originals,
provenance, decision history and duplicate hints all survive, and no curation action implies
verification)
exit=0
```

```text
$ /opt/homebrew/bin/python3.12 scripts/check_garden_e2e.py   # CI's interpreter
… identical 96 PASS lines …
RESULT: PASS (…)
exit=0
```

Determinism: two consecutive runs under the same interpreter differ only in the throwaway scratch
dir name; every `PASS:` line is byte-identical.

Prior suites, re-run on this branch under both interpreters (nothing regressed):
`check_garden_store.py` 59 · `check_garden_envelope.py` 102 · `check_garden_submit.py` 134 ·
`check_garden_normalize.py` 232 · `check_garden_review.py` 246 — all `RESULT: PASS`; plus
`check_program_contracts.py` (exit 0) and `validate_homepage_preview_export.py` (exit 0).

## Negative controls (same-session review pass)

The scope is one big evidence script, so this session both authored and reviewed it (the operator may
still want a foreign pass — see the skill's note). The review pass is an **independent mutation
harness** (`/tmp/w16_controls.py`, throwaway) written after the code, aimed at the **stored write
paths** the e2e asserts. Every control copies the repo, applies exactly one source mutation, runs the
e2e in the copy with the real `python3`, and each **goes red on the intended guard**:

| # | Mutation | Observed `FAIL:` line (first) | Proves |
|---|---|---|---|
| c1 | `store_capture` trims the capture (`.strip()`) | `cand-W02 is accepted` (W1.3's rule-5 read-back refuses) | a capture surface that trims breaks byte-identity |
| c2 | `curate` also writes `research_state='in_research'` | `after every decision, every candidate's research_state is still 'not_started'` | the no-verification guard |
| c3 | remove the T-P7 reversal (`elif False`) | `the reversal recorded exactly ['T-C1','T-P1','T-C8','T-P7']` | the no-stranded-dimension guard |
| c4 | a shared generic citation treated as evidence | `produce NO reference hint` | the generic-`source_ref` fix |
| c5 | `import_bytes` silently drops the `decisions` section | `unexpected StoreError: re-export after import is not byte-identical…` | the store's *own* round-trip guard (see finding) |
| c6 | normalize stops reporting the `_` placeholder | `the glyph is reported in the normalization note and preserved in the proposal` | the preserve-and-report glyph guard |

**Finding (c5):** mutating `import_bytes` to drop `decisions` makes the run red, but on the store's
*own* `StoreError` — "re-export after import is not byte-identical…" — rather than on the e2e's
round-trip `FAIL:` line. The e2e's round-trip check is therefore **backstopped** by `import_bytes`'
internal re-export comparison. This is the same "one guard per layer, give each its own falsifier"
lesson W1.4/W1.5 recorded (the surface's check is masked by the store's), and it is recorded here
rather than papered over: the e2e does not need to duplicate a guard the store already proves. If a
future change removes `import_bytes`' internal guard, the e2e's round-trip line would be the one to
catch it. This is a test-design observation, not a product defect — no issue filed.

## Out-of-scope findings (recorded, not fixed in passing)

- **CI still does not run any of the six W1 acceptance suites** (now `check_garden_store.py` 59,
  `check_garden_envelope.py` 102, `check_garden_submit.py` 134, `check_garden_normalize.py` 232,
  `check_garden_review.py` 246, `check_garden_e2e.py` 96) nor the seventh surface `garden_review.py`.
  This is the long-open W1.2 queue item, re-filed to SIX; it is a change to the guarded
  `browser-smoke.yml` workflow and was not fixed as a side effect of the gate unit. This is the final
  recorded count for W1. (Not a new issue — same tracking item.)

## Deliberately NOT done

- **No W2 research functionality**, no canonical promotion, no migration — the wave stops at the Gate
  B packet. `quotes.csv`/`sources.csv` read-only rule held (byte-identical `5675d7e6…`/`10b4c156…`).
- **No populated store mirror committed** — Gate B reproducibility is proved by the e2e's clean-clone
  temp-dir run; a committed `data/store/garden.export.txt` belongs to the first real operator
  population (W1.3 decision).

## Resume / next action

W1 is complete and the Gate B packet (`docs/program/W1_6_GATE_B_PACKET.md`) is submitted. The next
authorized action is an **operator/frontier decision on Gate B**; if accepted, authorization of
**W2** is a separate operator decision. **W2 is not started** — nothing past the packet was touched.

### Exact next Prompt

**Review the Gate B packet (`docs/program/W1_6_GATE_B_PACKET.md`) as a fresh, independent evaluator** —
verify the acceptance transcript reproduces from a clean clone with `python3 scripts/check_garden_e2e.py`
(96 checks, exit 0), confirm `quotes.csv`/`sources.csv` are byte-identical
(`5675d7e6…`/`10b4c156…`) and `validate_quotes.py` exits 0, and run an independent mutation pass of
your own against the e2e's stored write paths (not this handoff's c1–c6 table). If Gate B passes,
record acceptance and STOP — do not start W2 without a separate operator authorization.
