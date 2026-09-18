# Gate U0 packet — resumable workbench

**Gate:** `U0 — resumable workbench` · **Submitted:** 2026-09-18 · **State:** `SYNTHESIS REQUIRED — GATE U0`
**Units:** U0.1 (store lifecycle + mirror freshness invariant), U0.2 (truthful front door),
U0.3 (real persistent operator canary + this packet)
**Audit prompt:** `docs/program/usability-closure/SYNTHESIS_GATES.md` §S0

This packet is deliberately small and evidentiary. It is written so a synthesizer who has never seen
the session can re-run every claim; the full transcripts and the review trail are in
`GARDEN_U0_3_HANDOFF.md`. Nothing below is summarised from a handoff — each block names the command
whose output it quotes.

---

## 1. The claim

The SQLite store, the committed text mirror, and the operator surface form a **resumable workbench**:
a real operator action on the real persistent store survives mirror sync, local process death,
deletion of the local database, and reconstruction on a different machine from committed artefacts
alone — with the exported state byte-identical.

## 2. The canary (a real item, not a fixture)

The operator was asked for one passage they actually want in the Garden. They chose, from three
verified options, *The Hidden Words*, Arabic 22 (Bahá'u'lláh).

```
capture   cap-2026-09-18-0001   method web-page, captured 2026-09-18T00:15:55-06:00
          captured_text (verbatim, immutable):
            O Son of Spirit!
            Noble have I created thee, yet thou hast abased thyself. Rise then unto that for which
            thou wast created.
          captured_citation "The Hidden Words, Arabic 22"
          source_reference  https://www.bahai.org/library/authoritative-texts/bahaullah/hidden-words/
candidate cand-2026-09-18-0001   curation_state accepted · corpus_state eligible · research_state not_started
audit     T-C1  curation  new -> accepted        operator  2026-09-18T00:18:26-06:00
          T-P1  corpus    candidate_only -> eligible  system  2026-09-18T00:18:26-06:00
```

`eligible` is the furthest corpus state U0 authorises: the item was **not** canonically admitted, and
`quotes.csv` / `sources.csv` are byte-identical to `main`
(`9766db8c30372efc57752c0b12b373536e4ddb666f52591610ec238e1c3e01a3` /
`7aafcb67119564201baf700f29143668ed469f59d83aae60f8f99648a11a27da`).

### Evidence status of the curation decision — read this before accepting

**The operator did not answer the curation question.** They were asked twice (the first answer
delegated the passage choice — "choose from what is there, give me three options and recs" — and then
chose option 1), and both requests for the `accept`/`hold`/`reject`/`duplicate` verdict and its
reason timed out unanswered.

The verdict was therefore recorded **by the agent on the operator's behalf**, and the audit row says
so in its own text. The grounds were: the operator had already stated they want this passage in the
Garden, and `T-C9 reopen` exists, so the call is reversible. This is disclosed rather than smoothed
over because it is the one part of Gate U0 that is *not* fully ecological: the operator's decision
was inferred from their selection, not given. **The synthesizer's call on whether that is sufficient
for Gate U0 is exactly the judgment §S0 exists to make.** Nothing else in this packet depends on it —
every other claim is a machine verdict reproducible from the committed tree.

## 3. Recovery: four independent reconstructions, byte-identical

Baseline (before the canary): `1b5959d1…`, 24,027 bytes. After: `3b5c5407…`, 27,091 bytes.

| # | What was done to the state | Result |
|---|---|---|
| 1 | Real operator mutations (submit, normalize, hints, accept) through the CLIs | mirror auto-synced; `status: CURRENT` after every one; no manual `sync` needed |
| 2 | `rm data/store/garden.sqlite3` on the **real** store | `status: MISSING_DB` → `bootstrap: CURRENT` → re-derived export **byte-identical** to the committed mirror |
| 3 | Fresh `git clone` of the pushed branch into `/tmp/u03_fresh` (only `garden.export.txt` present, **no SQLite**) | `bootstrap: CURRENT`; `export --out` produced `3b5c5407…`, `cmp` → identical, 27,091 bytes both sides |
| 4 | Same clone, full state query | candidate, capture, normalization notes, `accepted`/`eligible`, **both** audit rows and the 324-row legacy batch all recovered |

Reconstruction #3 is the different-machine case: the clone was taken from `origin`, so it consumed
only committed artefacts, and it was given no transcript, no session context and no local database.

## 4. The mirror cannot silently lie

The invariant is enforced by the mutation path, and it fails loudly in the two directions that
matter. All three probes ran in throwaway copies under `/tmp`:

| probe | expectation | observed |
|---|---|---|
| a real mutation (`garden_submit.py submit`) | mirror refreshed by the mutation itself | `3b5c5407…` → `06727301…`, `status: CURRENT` — it cannot go stale via a supported path |
| a hand-edit appended to the committed mirror | divergence **detected** | `status: STALE` |
| the mirror deleted | reported | `status: MISSING_MIRROR` |

## 5. Front door

`scripts/check_front_door.py` — `RESULT: PASS (27 checks)`, CI-wired in `browser-smoke.yml`, with
13 registered negative controls. It asserts the front doors route live status to
`docs/program/usability-closure/CURRENT.md`, that `AGENTS.md` names the real command surface
(including the store lifecycle and every `garden_*.py` module), and that no scanned document
re-asserts the retired stale claims.

**U0.2's guard had to change in U0.3, and the reason is itself a gate finding:** the guard could only
express "exactly one READY unit", so the state Gate U0 *requires* — `SYNTHESIS REQUIRED — GATE U0`,
in which nothing is authorized — was unreachable through it. U0.3 added a `## Programme state` field
and made the guard state-aware in **both** directions: while synthesis is required, no unit may be
READY in `CURRENT.md` or in `docs/queue.md`, and the queue must still name what a later gate would
release, marked not authorized. Declaring the state decoratively — while quietly keeping a READY
unit — is a build failure, not a pass.

## 6. Open defects: gate-blocking vs deferred

**Gate-blocking: none.** No defect was found that falsifies any claim in §1–§5.

| item | class | why not gate-blocking |
|---|---|---|
| the curation decision was agent-recorded from the operator's selection (§2) | **for the synthesizer** | disclosed; reversible via `T-C9`; no other claim depends on it |
| `run_negative_controls.py` cannot register a `GREEN_OK` control (issue [#56](https://github.com/mschwar/Garden-of-Wisdom/issues/56)) | deferred | the guard's false-positive direction is evidenced by a throwaway battery, CI-enforced nowhere; already queued as its own unit |
| a candidate can never be withdrawn; a whitespace-only submission is permanent (issue [#30](https://github.com/mschwar/Garden-of-Wisdom/issues/30)) | deferred | matters at admission/withdrawal time; U0 makes no withdrawal claim |
| `garden_normalize.py` canonicalizes quote marks inside `captured_attribution`, so a candidate's author becomes `Bahá'u'lláh` (straight) while all 45 corpus rows use `Bahá’u’lláh` (curly) | deferred — **new finding** | observed on the real canary; a normalization-semantics question, not a persistence one |
| the legacy corpus is not a duplicate-comparison set: `hints` compares candidates only against each other, so a capture duplicating a `quotes.csv` row raises no hint | deferred — **new finding** | becomes load-bearing at admission (U1), not at persistence (U0) |
| `quotes.csv` id 282 cites *The Hidden Words*, Arabic 13 but diverges from the official text in three places, including the vocative (`O Son of Man!` vs `O Son of Spirit!`) | deferred — recorded on [#6](https://github.com/mschwar/Garden-of-Wisdom/issues/6) | data curation; `quotes.csv` changes only inside a named data unit |
| issues [#4](https://github.com/mschwar/Garden-of-Wisdom/issues/4) (`source_url` column), [#19](https://github.com/mschwar/Garden-of-Wisdom/issues/19) (Node 20 action bumps) | deferred | unrelated to the resumability claim |

## 7. What this packet does not claim

- It does not claim the corpus is correct, complete or verified — only that the **workbench** is
  resumable. Data quality is issue #6's territory.
- It does not claim the curation verdict is the operator's own words (§2).
- It does not claim the guard catches every stale claim: it is a pattern matcher over three
  documented drift shapes, and a synonym evades it. The check says so itself.
- It does not claim CI re-applies the guard's false-positive evidence (issue #56).
- It does not authorize anything. U1.1 remains unauthorized until §S0 synthesis says otherwise.
