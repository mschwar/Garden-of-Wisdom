# Gate A Frontier Review — 2026-09-12

Independent re-check of the W0 corpus-program doctrine submission (Gate A), landed as PR #12
(`593ab6e`, merged to `main`). Reviewed against `main` at `593ab6e`. Not a re-run of the
original agent's assertions alone: re-executed the doctrine checker and both existing
validators, recomputed file hashes against the values recorded in the report, and cross-checked
every count claim in `docs/program/W0_GATE_REPORT.md` and `docs/queue.md` against the actual
fixture, doc, and decision-log contents.

## Verdict

**PASS / ACCEPT.** All eight Gate A criteria
(`bootstrap/seed/2026-09-12-garden-corpus-program/ACCEPTANCE_GATES.md`) are satisfied by the
doctrine as it stands on `main`. Three evidence-hygiene defects were found in the Gate A
package itself — all stale numbers left over from the `T-P7`/`T-P8` stranded-state fix
(`docs/DECISIONS.md`, 9th W0 entry), not doctrine defects — and are fixed as part of this
review (see below). No doctrine content, transition table, envelope contract, or scenario
logic was changed. `quotes.csv`/`sources.csv` remain byte-identical to `main`; no W1
implementation exists anywhere in the tree.

**W1.1 is not authorized by this verdict.** Per `docs/program/CORPUS_PROGRAM_DOCTRINE.md` and
the W0 report's own stop point, Gate A acceptance and W1.1 authorization are two separate
operator decisions. This review renders only the former.

## What was proven

| Claim | Independent check |
|---|---|
| Doctrine checker passes | `python3 scripts/check_program_contracts.py` → `RESULT: PASS`; "parsed 40 transitions, 21 required envelope fields, 12 scenarios"; "authorities asserted: 40/40 transitions" |
| Existing validators unaffected | `python3 scripts/validate_quotes.py` and `python3 scripts/validate_homepage_preview_export.py` both exit 0; output matches the baseline recorded in the report |
| `quotes.csv`/`sources.csv` untouched | `sha256` of both files matches the baseline in `W0_GATE_REPORT.md` §Evidence exactly: `quotes.csv 5675d7e6…`, `sources.csv 10b4c156…` |
| `STATE_MODEL.md` has exactly 40 transitions, including `T-P7`/`T-P8` | `grep -c '^| T-' docs/program/STATE_MODEL.md` → 40; `T-P7 eligible→candidate_only` and `T-P8 canonical→eligible` both present, operator-authority |
| Fixture has exactly 12 scenarios (`S1`–`S12`) | parsed `docs/program/fixtures/w0_scenarios.json`: scenario ids are exactly `S1..S12`, no more, no fewer |
| Negative-controls table has 20 rows, not 15 | counted the "Negative controls" table in `W0_GATE_REPORT.md`: 20 data rows |
| `docs/DECISIONS.md` has 9 W0-dated entries, not 8 | 9 `## 2026-09-12 — W0…` headings; the 9th is the `T-P7`/`T-P8` stranded-state fix, absent from the report's own "Decisions made" list |
| Gate A criteria walk (all 8) | re-read `STATE_MODEL.md`, `CANDIDATE_ENVELOPE.md`, `PROVENANCE_AND_CAPTURE_CONTRACT.md`, `VERIFICATION_CONTRACT.md`, `CLASSIFICATION_AND_FACETS.md`, `W1_DECOMPOSITION.md` against each criterion in `ACCEPTANCE_GATES.md`; all satisfied, none resting on unbacked assertion |

## Defects found and fixed

The report's own standard is evidence "backed by commands and outputs... not by assertion."
Three places broke that standard — all because the `T-P7`/`T-P8` stranded-state fix landed
*after* these numbers were first captured, and the surrounding prose was never refreshed:

1. **Stale appended acceptance-run block in `W0_GATE_REPORT.md`.** The "Post-change acceptance
   run" block reported "parsed 38 transitions ... 10 scenarios" — the pre-fix counts.
   Re-running the identical command today gives 40/12, matching the rest of the document.
   Fixed by appending a dated correction block with the actual current output, rather than
   silently editing the historical one — consistent with how this repo already handles a
   falsified prior claim (e.g. the donor-set near-dupe correction in `docs/DECISIONS.md`).
2. **Undercounted decision-log entries.** The "What landed" table claimed "8 entries appended"
   to `docs/DECISIONS.md`, and the "Decisions made" list enumerated only items 1–8. There are 9:
   the `T-P7`/`T-P8` stranded-state fix is decision 9 and was missing from both. Fixed by
   correcting the count and appending item 9.
3. **`docs/queue.md` closed-item summary drifted the same way.** "11 walkthroughs" and "15
   negative controls recorded" — corrected to 12 and 20.

None of these reach doctrine substance, the transition table, the envelope contract, or the
checker's actual behavior. The checker re-derives its own counts from the fixture and doc
tables and would have caught a *doctrine* drift; it does not parse the report's prose, so a
stale copy-pasted number in the narrative was not something it could catch on its own.

## Block vs accept-as-debt

**Would have blocked:** nothing found reaches doctrine substance. Curation/research-state
separation, the candidate envelope, the provenance contract, the verification contract,
faceted classification, and the W1 decomposition are all present, cross-checked, and
internally consistent once the three drift points above are fixed.

**Accepted as existing, already-documented debt (unchanged by this review):** D1–D8 in
`W0_GATE_REPORT.md` §"Unresolved questions / debt", and the five carried-forward risks already
explicitly deferred to W1 in that same report.

## Next authorized action

Gate A: **accepted**, 2026-09-12. W1 remains unauthorized. The next decision available to the
operator is a separate, explicit authorization of **W1.1 only**
(`docs/program/W1_DECOMPOSITION.md`) — this review does not grant it.

## Update — 2026-09-12

Point-in-time review; its findings and its Gate A verdict stand unchanged. **W1 was subsequently
authorized in full on 2026-09-12** (decision D1 in `docs/DECISIONS.md`; see also
`docs/queue.md`), which supersedes the "W1 remains unauthorized" posture stated above. The
per-unit gates are not merged by that authorization: each W1 unit still lands its own branch, PR
and independent QA, and the wave stops at the Gate B packet.
