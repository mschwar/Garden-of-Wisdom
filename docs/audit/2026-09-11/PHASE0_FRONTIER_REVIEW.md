# Phase 0 Frontier Review — 2026-09-11

Independent re-check of the Phase 0 rehabilitation (G0–G3), landed as PR #1
(`a2e0a70`, merged to `main`). Reviewed against `main` at `10d43e0` (PR #2 donor-set
approval already merged). Not a re-run of the original agent's assertions: encoding
bytes, rehab/validate scripts, CSVs vs `data/archive/2026-09-11/*.original.csv`, and
a live browser pass at `http://localhost:8000/browser/index.html`.

## Verdict

**PASS / accept, with documented debt.** No data-integrity reason to revert or
block. Encoding diagnosis is correct. Quote wording was not silently altered. The
rehabilitated model is solid enough to later build a small verified donor-set
export, once specific rows are actually verified. `item_type` is a queue signal,
not a classification to ship.

## What was proven

| Claim | Independent check |
|---|---|
| Original CSVs were Mac OS Roman, not UTF-8 | Archive `quotes.csv` fails `utf-8` at offset 275, byte `0x87`. Context is `Bah\x87_u'll\x87h`. `mac_roman` → `á`; latin-1 → C1 control; cp1252 → `‡`. Byte `0xd5` is `’` under Mac OS Roman, `Õ` under latin-1/cp1252. |
| Archive is the true original | SHA-256 of `data/archive/2026-09-11/*.original.csv` matches git blobs at `ef38aca` / `a2e0a70^` exactly (quotes `cad3d9f5…`, sources `f86a72f6…`). |
| Wording not rewritten | 324/324 core fields (`id`, `quote_text`, `tradition`, `source_ref`, `author`, `tags`) equal mac_roman-decoded originals. IDs unchanged, including gaps 250→261 and 290→301. |
| `_` placeholders left alone | Ids 1, 16, 314, 320 still contain literal ASCII `0x5F`. `has_unresolved_glyph` matches those four and only those four. |
| `sources.csv` notes repair | Ragged unescaped commas rejoined; notes length matches a manual rejoin for all 18 rows. Rehab output equals the current file. |
| Counts | `python3 scripts/validate_quotes.py` exits 0: 324 rows, 27 traditions, 14 blank `source_id`, 4 glyph rows, 45 near-dupe candidates, `item_type` `{excerpt: 268, oral-attribution: 34, unknown: 22}`, all `unverified`. Matches `docs/data/DATA_QUALITY_REPORT.md` exactly. |
| `source_id` linker | Zero keyword collisions across different source ids on this corpus. Tradition/source mismatches: none. The 14 blanks are real manifest gaps, not timid matching. |
| Browser | Live load 324/324, 0 console errors. Search "Dhammapada" → 29. Tradition Baha'i → 45. `item_type` unknown → 22. Issues-only → 324 (expected: every row is unverified). Tag kindness → 15. Sort-by-length descending works. Copy quote / attribution / JSON payloads are correct. Headless clipboard write is denied; the toast handles failure. Uncertainty is visible on the card (badges + provenance). |

## Heuristic misses (not merge blockers; do not export as-is)

`item_type` / `source_id` as coded in `scripts/rehabilitate_2026_09_11.py`:

1. **Roman-numeral Gleanings citations classified `unknown`.** The rule is “digit or `:` → excerpt.” `Gleanings, CXVII` has neither, so ~10 pinpoint Baha'i citations land in `unknown`, including **donor ids 3 and 15**. Working as coded; too narrow for this corpus.
2. **Paraphrase-shaped rows not typed `paraphrase`.** Id 267 (`Various Sutras (paraphrased)`); id 31 (author `‘Abdu’l-Bahá (paraphrased)`). The script never assigns `paraphrase` or `full-passage` (already a documented Phase 0 deviation). 267 is the row that is obviously wrong, not merely conservative.
3. **Written texts tagged `oral-attribution` because tradition is in `ORAL_TRADITIONS`:** Popol Vuh (341), Huehuetlahtolli (342), Florentine Codex (343). Black Elk Speaks (314) is a published book of oral material — borderline, not a silent lie.
4. **Glyph split of the same author.** Filter `Bahá_u'lláh` → 1 row (id 1); `Bahá’u’lláh` → 28 rows. Consequence of leaving `_` in place; not called out in the quality report.

`source_id` itself is conservative and correct on this data. `"John"` only hits Gospel/1 John; `"Tablet"` only hits Baha'i tablets.

## Claims check

Garden does **not** list “5 unresolved decisions.” That set lives on the
`bahai-homepage` H2B-A collection contract (migrate Hidden Words in place vs new
path; default Hidden Words to `verified`; default them to `full-passage`;
`verification_status` vs `verification_state`; where the iOS regen script lives).

Garden’s analogous lists, checked against the data:

- `docs/queue.md` five open curation items: **accurate** (14 source gaps, 45
  near-dupes, 4 glyphs, 22 unknown, 27-value tradition list). The unresolved-id
  table in the quality report is complete.
- Near-dupe caveat: ~25/45 pairs are the generic `"Oral Tradition"` false-positive
  (~55%, “roughly half”). Accurate.
- `docs/data/DATA_CONTRACT.md` four known issues: **true, incomplete.** Missing:
  Roman-numeral → `unknown`; written-as-oral rows; paraphrase-shaped rows 31 and
  267; author split from the `_` glyph.

Donor-set decision (PR #2, not G0–G3) claimed ids 3/12/15/26/30 appear in **no**
near-dupe pair. Id **3 ~ 283** is in the validator output (similarity 0.74):
“The earth is but one country…” (Bahá’u’lláh, Gleanings CXVII) vs “The earth is
one home…” (‘Abdu’l-Bahá, Selections 255). Different author, different work,
similar teaching — not a reason to drop 3, but the claim is false. Corrected by
a superseding entry in `docs/DECISIONS.md`.

## Schema vs a future `bahai-homepage` (H2B) export

Precise enough for an agent to write a mapper. **Not** a drop-in JSON schema.
Phase 0 handoff §12 (new generated file, never a live read of `quotes.csv`) is
the right seam.

| Garden | H2B item | Notes |
|---|---|---|
| `id` | `upstream_id` | Stable. Keep. |
| `quote_text` | `text` | Only after word-for-word verification. |
| `author`, `source_ref` | same names | Fine. |
| `item_type` | `item_type` | Same enum, different authority. Reclassify at verify time. Do not export current values. |
| `verification_status` | `verification_state` | Same enum, one-word name mismatch (H2B unresolved decision 4). Map in the exporter; do not silently rename Garden. |
| (none) | `source_url` | Does not exist per quote. Record during G4 from bahai.org. |
| `tags` CSV string | `tags` array | Split/trim in the exporter. |
| `has_unresolved_glyph` | — | Garden-only. Current donor set has none. |
| `source_id` | provenance, not an H2B field | String, not int (`7.1` is Hadith). |

Also missing on Garden rows, and correctly so: collection wrapper, `rights_note`,
`schema_version`. Those belong on the export, not on the workbench CSV.

Validator gaps (debt, not blockers): `warn()` is defined and never called; new
columns are not in `REQUIRED_FIELDS` (empty `item_type`/`verification_status`
still fail the enum check; a missing `has_unresolved_glyph` column would not).

## Block vs accept-as-debt

**Would have blocked PR #1 on:** nothing found. Encoding, wording preservation,
ID stability, archive integrity, and “everything is unverified” are all actually
true.

**Accept as documented debt:** 14 source gaps, 4 `_` glyphs, 45 near-dupes,
all-unverified, no duplicate-review UI, no browser CI, issues-only matching
324/324 today, `full-passage`/`paraphrase` unused.

**Do in G4 / next curation pass, not by rewriting Phase 0 data now:**

- Reclassify `item_type` at verification time (especially donor ids 3 and 15).
- Map `verification_status` → `verification_state` in the exporter.
- Record `source_url` during verification.
- Optionally document the Roman-numeral heuristic miss and written-as-oral rows
  in `docs/data/DATA_CONTRACT.md`.

## Export readiness

**Yes.** This rehabilitated model is solid enough to eventually build a small
verified donor-set export from, once specific quotes are approved for
verification.

The gates that matter are in place: stable legacy ids, UTF-8 bytes you can
prove, wording that was not silently edited, `verification_status` defaulting to
`unverified`, `source_id` left blank rather than guessed, and an export shape
that is a new file rather than a live CSV coupling. What is *not* solid enough
to ship as-is is `item_type`. G4 should reclassify each donor against the
primary text, write `source_url`, and refuse to emit any row still `unverified`.

G4 remains gated on owner acceptance of the `bahai-homepage` H2B collection
contract (still proposed as of this review).
