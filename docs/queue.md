# Work Queue

Status as of the 2026-09-11 Phase 0 retrofit. This is a living document — update it as items
are picked up or closed, don't just append.

## Open — data curation

- [ ] Resolve the 14 unresolved `source_id` links (`docs/data/DATA_QUALITY_REPORT.md`). Mostly
      needs new `sources.csv` rows for small oral traditions (Shawnee, Cherokee, Nez Perce,
      Lakota, Tewa, Zuni, Ethiopian, Nguni) plus Nahua works and the Mahabharata.
- [ ] Human review of the 45 near-duplicate candidate pairs to decide: distinct variant
      translations (keep both) vs. accidental duplication (merge/remove). Note the
      generic-`"Oral Tradition"`-label false-positive caveat before trusting the list at face
      value.
- [ ] Resolve the 4 rows with literal `_` placeholder glyphs (IDs 1, 16, 314, 320) — needs a
      human who knows the correct diacritic/modifier character, not a guess.
- [ ] Review and reclassify the 22 `item_type = unknown` rows.
- [ ] Decide whether the 27-value tradition list should be formally documented as the new
      controlled list (this retrofit's README treats it as such) or trimmed/normalized further.

## Open — infra

- [ ] Consider adding a duplicate/near-duplicate review view to the browser if the curation
      pass above finds the CLI report insufficient (see `docs/architecture/QUOTE_BROWSER.md`).
- [ ] No automated browser test exists yet; only a manual Claude-in-Chrome smoke test was run
      this phase.

## Explicitly NOT started (out of Phase 0 scope, do not start without human sign-off)

- Authoritative verification or export of any quotes. **Donor-set selection is done** — ids
  [3, 12, 15, 26, 30] approved 2026-09-11 (`docs/DECISIONS.md`) and filled into
  `bootstrap/seed/2026-09-11-garden-2026-retrofit/prompts/02_GARDEN_VERIFY_AND_EXPORT_HOMEPAGE_PREVIEW.txt`'s
  `APPROVED_GARDEN_IDS`. Running that prompt (verification against the authoritative Bahá'í
  Reference Library, then export) is the next step, still gated on the `bahai-homepage` H2B
  collection contract being reviewed/accepted.
- Any `bahai-homepage` export or implementation work.
- Bulk quote verification.

## Closed — 2026-09-11 Phase 0

- [x] G0 archaeology — `docs/audit/2026-09-11/FINDINGS.md`
- [x] G1 agent-first retrofit docs (this file and its siblings)
- [x] G2 data rehabilitation — UTF-8 canonical CSVs, `item_type`/`verification_status`/
      `source_id`/`has_unresolved_glyph` columns, archived originals, `.DS_Store` untracked
- [x] G3 static quote browser
