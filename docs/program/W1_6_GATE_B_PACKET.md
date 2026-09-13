# W1 Gate B Report — intake/curation end-to-end (Gate B)

Date: 2026-09-13. Branch: `w1/gate-b-packet`. **W1 COMPLETE — W2 NOT STARTED.**

This is the evidence package for Gate B (`ACCEPTANCE_GATES.md` section "Gate B"), the wave gate of
the Garden corpus program. It mirrors the shape of `W0_GATE_REPORT.md` (Gate A's packet): claims
below are backed by the commands and outputs in §Evidence, not by assertion. The gate reads:

> **Gate B — W1 intake/curation.** Pass only if a representative batch of messy manual submissions
> can be ingested and reviewed while preserving originals, provenance, decision history, and
> duplicate hints. No curation action may imply verification.

## What landed (the W1.6 unit)

| Artifact | What it is |
|---|---|
| `scripts/check_garden_e2e.py` | The deterministic end-to-end acceptance run — **96 checks**, one command from a clean clone, exit 0/1, stdlib-only, runs in a throwaway temp dir. Drives the whole loop through the real W1.3/W1.4/W1.5 CLIs as subprocesses. |
| `docs/program/W1_6_E2E_TEST_PACK.md` | Design doc for the test pack (the assertion pipeline, the messy batch, negative controls). |
| this file | The Gate B evidence packet. |
| `docs/DECISIONS.md` / `docs/queue.md` / `docs/RUNBOOK.md` | Close-out updates. |
| `GARDEN_W1_6_HANDOFF.md` | The unit handoff (negative controls, findings, next action). |

The loop under test is the whole wave: `manual submission (W1.3) → durable capture (W1.1 store)
→ normalized proposal + duplicate hints (W1.4) → operator accept/hold/reject/duplicate/reopen with
audit history (W1.5)`. W1.6 adds no new surface; it proves the assembled loop works as one
reproducible whole and packages the proof.

## Gate B criteria, item by item

| Gate B requirement | Where satisfied (W1.6 e2e) |
|---|---|
| A representative batch of messy manual submissions | §1 of the e2e: a literal `_` glyph row (320) and a curly-quote row (21) taken **verbatim from `quotes.csv`**, plus a wrong-author row, a leading/trailing-whitespace row, a missing-citation row, a near-duplicate text pair, and two unrelated rows sharing the generic `Oral Tradition` label — 9 submissions through the real W1.3 CLI. |
| …can be ingested | §1–§2: every submission accepted, one capture + one candidate each, no decision row written. |
| …and reviewed | §4: accept/hold/reject/duplicate/reopen plus the full `accept → reject` reversal driven through the real W1.5 CLI; the reversal records exactly `['T-C1','T-P1','T-C8','T-P7']` and strands no dimension. |
| …while preserving **originals** | §2–§3: every capture byte-identical to the submitted text before, during and after normalize+hints; the whole `[captures]` export section byte-identical after `normalize --all` and after `hints --all`; the `_` glyph and curly apostrophe survive verbatim (never guessed / never "fixed"). |
| …**provenance** | §2: capture method, `captured_at` (with offset), wrong author, leading whitespace and a missing citation are all preserved on the capture (the encounter, not a correction); a missing citation becomes the `none` sentinel, never an empty string. |
| …**decision history** | §4–§5: every decision audited with actor/from/to/transition_id/reason/timestamp; the review produces exactly 10 audit rows; the `decisions` log is re-proven append-only (UPDATE/DELETE refused). |
| …and **duplicate hints** | §3: the near-duplicate pair produces a hint with a basis; the generic `Oral Tradition` pair produces **no** reference hint (the W1.4 false-positive fix); hints write no decision row and never move `curation_state` (a hint is never a state). |
| **No curation action may imply verification** | §6: after every decision every candidate's `research_state` is still `not_started`; no decision row writes or implies a research state; corpus stays in the W1 vocabulary (`candidate_only`/`eligible`) — nothing claims truth. |

## Required artifacts (W1.6 acceptance criteria from `W1_DECOMPOSITION.md`)

- **The end-to-end test runs from a clean clone with one command and exits 0.** `python3
  scripts/check_garden_e2e.py` is self-contained: it reads `quotes.csv` for fixtures, creates its
  own store in a temp dir, and asserts the loop end to end. It never depends on a pre-seeded
  `data/store`, on Playwright, or on the browser — stdlib only.
- **`python3 scripts/validate_quotes.py` still exits 0 and `quotes.csv`/`sources.csv` are
  byte-identical to pre-W1.** The e2e hashes both CSVs before and after and runs
  `validate_quotes.py` as a subprocess; §8 asserts all three.
- **The evidence packet names every test and artifact.** This report (§What landed) names them, and
  §Evidence shows each running.

## Evidence

The e2e acceptance run, from this branch, under the CI interpreter and the local one, plus the
legacy validators (which the e2e itself re-runs). `quotes.csv`/`sources.csv` hashes are the pre-W1
baseline from `W0_GATE_REPORT.md` (§Evidence) and are unchanged.

```text
$ python3 scripts/check_garden_e2e.py        # also run under /opt/homebrew/bin/python3.12 (CI)
scratch: /var/folders/kc/…/garden-e2e-check-b4cvfbf8
… 96 PASS lines …
RESULT: PASS (a messy batch is ingested, normalized, hinted and reviewed while originals,
provenance, decision history and duplicate hints all survive, and no curation action implies
verification)
exit=0
```

Full 96-line transcript: `GARDEN_W1_6_HANDOFF.md` §Acceptance evidence (pasted verbatim). The five
prior W1 acceptance suites all re-ran green on this branch under both interpreters
(`check_garden_store.py` 59, `check_garden_envelope.py` 102, `check_garden_submit.py` 134,
`check_garden_normalize.py` 232, `check_garden_review.py` 246), and `check_program_contracts.py`
(exits 0) — so the new pack did not regress any prior W1 surface.

```text
$ python3 scripts/validate_quotes.py
counts by verification_status: {'unverified': 320, 'verified': 4}
sources.csv: 18 rows …
RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)
exit=0

$ python3 scripts/check_program_contracts.py
parsed 40 transitions, 21 required envelope fields, 12 scenarios
…
RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)
exit=0

$ python3 scripts/validate_homepage_preview_export.py
RESULT: PASS
exit=0

$ shasum -a 256 quotes.csv sources.csv
5675d7e67da256e6211574bbf416a8e2f8c3f37a834816090c9a32847acac793  quotes.csv
10b4c1567dbfc80b3b681599e85b7e2e6a241eff3cf2b610baf392508dea0c13  sources.csv
# byte-identical to the pre-W1 baseline (W0_GATE_REPORT.md §Evidence)
```

## Negative controls (proving the gate can fail)

Same-session review pass, six mutations, each to a stored write path, each turning the e2e red on
the check it probes — full table in `GARDEN_W1_6_HANDOFF.md`. In brief: a capture surface that trims
(c1), a curate that writes research state (c2), a removed T-P7 reversal (c3), a shared-generic-
citation hint (c4), a lossy import (c5, caught by the store's own guard — a recorded finding), and
a normalizer that stops reporting the `_` glyph (c6). A control that did not go red on its own
check is a finding, not a nuisance — see c5 in the handoff.

## Carried-forward risks — status at Gate B

`W0_GATE_REPORT.md` §"Carried-forward risks" named invariants W1 must falsify. At Gate B:

| Risk (from W0) | Falsified by | Status |
|---|---|---|
| The reversal rule (`T-C8 → T-P7`) is legal on paper but untested against a real store | W1.5 exercised accept → eligible → reject → `candidate_only` and asserted no dimension stranded; **W1.6 re-exercises it through the assembled loop** and records exactly `['T-C1','T-P1','T-C8','T-P7']` (e2e §4). | **Falsified (and re-asserted end-to-end)** |
| The envelope is proven against fixtures, not against this repo's own awkward rows (`_` placeholders, unresolved source links, oral-tradition chains) | W1.6 §1–§2 intakes row 320 (literal `_` glyph) and row 21 (curly apostrophe) **verbatim from `quotes.csv`** and asserts byte-identical captures and the marker preserved. | **Falsified** |
| The 3-valued projection is asserted in prose; its totals could drift | `check_program_contracts.py` recomputes row counts from `quotes.csv` and stays green; `validate_quotes.py` exits 0. | **Green** |
| Eligibility vs the read-only CSV for legacy rows | W1 cross-unit rule held: `quotes.csv`/`sources.csv` byte-identical (`5675d7e6…`/`10b4c156…`); T-P1 applies to new store candidates only, no CSV write ever occurred. | **Held** |
| Per-claim statuses on a record whose wording is verified but whose translation identity is not | S12 walkthrough (W0) + W1.2 validator fixtures remain green. | **Green** |

## Stop point

**Gate B packet submitted. W1 is COMPLETE. W2 is not started.** Per `W1_DECOMPOSITION.md` and the
wave authorization (decision D1), W1 ends at the Gate B packet; nothing past it was touched — no
research surface, no promotion path, no migration. The next authorized action is an
operator/frontier decision on **Gate B**, followed (if accepted) by authorization of **W2**.

---

### Post-merge verification (appended after merge)

_(filled in the follow-up docs commit, like W0's "Post-change acceptance run"): merge sha, PR
number, CI run ids, and the live `curl` acceptance._
