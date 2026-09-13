# W1.6 — End-to-end test pack + Gate B evidence packet

**Lane:** Platform/governance.
**Contract:** `docs/program/W1_DECOMPOSITION.md` section "W1.6". **Unit order:** after W1.5.
**Gate:** `bootstrap/seed/2026-09-12-garden-corpus-program/ACCEPTANCE_GATES.md` §Gate B.

W1.6 is the last unit of the wave. It does not add a new surface: it proves the loop W1.1–W1.5
built works as one reproducible whole, and packages that proof as the **Gate B evidence packet**.
The wave stops here — **W2 is not started.**

## What W1.6 ships

| Artifact | What it is |
|---|---|
| `scripts/check_garden_e2e.py` | The deterministic end-to-end acceptance run (**96 checks**). Runs from a clean clone with **one command** (`python3 scripts/check_garden_e2e.py`), drives every step through the real W1.3/W1.4/W1.5 CLIs as subprocesses inside a throwaway temp dir, and exits 0 only if the whole loop preserves originals, provenance, decision history and duplicate hints and no curation action implies verification. |
| this design doc | Why the pack looks the way it does and what each assertion proves. |
| `docs/program/W1_6_GATE_B_PACKET.md` | The Gate B evidence packet, mirroring the shape of `W0_GATE_REPORT.md` (Gate A's packet). |

The Gate B packet is written *after* the e2e run, on the merged `main`, with real transcript and
hashes pasted in — exactly the way W0's packet appended its post-change acceptance block.

## The messy batch

Gate B's phrase is *"a representative batch of messy manual submissions"*. The batch is both
real-corpus and controlled-messy:

- **Row 320** (a literal `_` placeholder glyph, *Mitákuye Oyás_i_*) and **row 21** (a curly
  apostrophe) are read **verbatim from `quotes.csv` at runtime** — the corpus's own most awkward
  bytes — so the test proves the loop survives the corpus's actual hard shapes, not a toy.
- Controlled messy shapes: a **wrong author**, **leading/trailing whitespace**, a **missing
  citation** (omitted flag → `none` sentinel), a **near-duplicate text pair** (must produce a
  hint), and two unrelated rows sharing the generic **`Oral Tradition`** label (must produce **no**
  reference hint — the W1.4 false-positive fix).

Every expected value is derived from `quotes.csv` or from the submitted batch itself — nothing is
hard-coded, and a fixture that stops narrowing fails loudly rather than passing vacuously (the
glyph/curly/whitespace fixtures each assert the property is actually present before relying on it).

## The assertion pipeline (what each block proves)

1. **Submission** (W1.3): every messy submission is accepted, produces exactly one capture + one
   candidate, and writes no decision row.
2. **Originals preserved verbatim**: every capture is byte-identical to the submitted text
   (nothing trimmed, glyph-"fixed", or quote-normalized); the `_` survives, the curly apostrophe
   survives, a wrong author and leading whitespace and a missing citation all survive on the
   capture; capture provenance (method, timestamp) is recorded. A whole-export snapshot is taken
   before normalization.
3. **Normalize + hints** (W1.4): `normalize --all` then `hints --all` are accepted; the whole
   `[captures]` export section is **byte-identical after both** (the capture is never touched);
   the glyph is reported and preserved in the proposal; whitespace is collapsed with a named note;
   the near-duplicate pair produces a hint; the generic `Oral Tradition` pair produces **no**
   reference hint; every hint carries a basis; hint generation writes **no** decision row and
   leaves every candidate `curation_state = 'new'` (a hint is never a state).
4. **Review** (W1.5): accept / hold / reject / duplicate / reopen all driven through the CLI; the
   reversal (`accept` → `reject`) records exactly `['T-C1', 'T-P1', 'T-C8', 'T-P7']` and strands no
   dimension; a rejected candidate keeps its capture and candidate readable; no record is left
   `eligible` while its curation is hold/rejected/duplicate.
5. **Decision history survives**: every decision row carries actor/from/to/transition_id/reason/
   timestamp; the review produces exactly the expected audit rows; the `decisions` log is
   re-proven append-only (UPDATE/DELETE refused).
6. **No curation action implies verification**: after every decision every candidate's
   `research_state` is still `not_started`; no decision row writes or implies a research state;
   corpus stays in the W1 vocabulary (`candidate_only`/`eligible` — nothing claiming truth).
7. **Reproducibility**: the store export (`garden.export/1`) round-trips (write → import → re-export
   byte-identical) and the store's own `verify` passes — the artifact the packet names.
8. **Clean-tree discipline**: `quotes.csv`/`sources.csv` are byte-identical before/after the whole
   loop, `validate_quotes.py` still exits 0, and nothing is written outside the temp dir (in
   particular no store appears in the repo root).

## Negative controls (same-session review pass)

The scope is one big evidence script, so this session both authored and reviewed it. The review
pass is an independent mutation harness (`/tmp/w16_controls.py`, throwaway) written after the code,
aimed at the **stored write paths** the e2e asserts. Every control copies the repo, applies one
source mutation, runs the e2e in the copy, and is recorded in the handoff.

| # | Mutation | Observed first `FAIL:` | Proves |
|---|---|---|---|
| c1 | `store_capture` trims the capture (`.strip()`) | `cand-W02 is accepted` (rule-5 read-back refuses) | a capture surface that trims breaks byte-identity |
| c2 | `curate` also writes `research_state='in_research'` | `after every decision, every candidate's research_state is still 'not_started'` | the no-verification guard |
| c3 | remove the T-P7 reversal (`elif False`) | `the reversal recorded exactly ['T-C1','T-P1','T-C8','T-P7']` | the no-stranded-dimension guard |
| c4 | a shared generic citation is treated as evidence | `produce NO reference hint` | the generic-`source_ref` fix |
| c5 | `import_bytes` silently drops the `decisions` section | `unexpected StoreError: re-export after import is not byte-identical…` | the store's *own* round-trip guard fires (see finding) |
| c6 | normalize stops reporting the `_` placeholder | `the glyph is reported in the normalization note and preserved in the proposal` | the preserve-and-report glyph guard |

**Finding (c5):** mutating `import_bytes` to drop `decisions` makes the run red, but on the store's
*own* `StoreError` ("re-export after import is not byte-identical…") rather than on the e2e's
round-trip `FAIL:` line. The e2e's round-trip check is therefore **backstopped** by `import_bytes`'
internal re-export comparison: if that guard were removed the e2e's `re-export after import is
byte-identical` line would be the one to catch the loss. This is the same "one guard per layer,
give each its own falsifier" lesson W1.4/W1.5 recorded — the e2e does not need to duplicate a
guard the store already proves, and it is recorded here rather than papered over.

## Deliberately NOT done

- **No W2 research functionality**, no canonical promotion, no new migration (W1.1's exact-ledger
  assertion `["0001_create_core"]` is untouched). This unit adds one script and two docs.
- **No populated store mirror is committed.** Gate B's reproducibility is proved by the e2e's
  temp-dir round-trip from a clean clone; a committed `data/store/garden.export.txt` is left to
  the first real operator population (W1.3 decision), not synthesized by this unit.
- **CI still does not run the W1 acceptance suites** (now **six**, with `check_garden_e2e.py`, plus
  a seventh surface). This is the long-open W1.2 queue item; it is a change to the guarded
  `browser-smoke.yml` workflow and is re-filed, not fixed inside a unit.
