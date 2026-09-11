# Product Doctrine

## What Garden of Wisdom is

A personal, curated collection of impactful quotes from world religions and philosophies,
kept for memorization and reflection. It is a corpus + a curation/review workbench, not a
publishing product.

## What it is not

- Not a scholarly critical edition. Provenance is tracked so uncertainty is visible, not so
  every quote is footnoted to publication standard.
- Not `bahai-homepage`. The two repos stay separate. Garden may later export a small,
  explicitly verified subset for that project, but Garden's own schema, scope, and pace of
  curation are not dictated by that downstream consumer.
- Not an exhaustive anthology. Breadth across traditions is a value, but completeness within
  any one tradition is not a goal.

## Non-negotiables

1. **Uncertainty must stay visible.** A quote that hasn't been checked against a primary
   source is `unverified`, and the browser must show that, not hide it behind a clean layout.
2. **Never silently rewrite quote wording.** Fixing an encoding bug (bytes decoded with the
   wrong charset) is allowed and mechanical. Guessing what a garbled or placeholder character
   "probably" was is not — that changes meaning without evidence.
3. **Preserve legacy identifiers and history.** IDs assigned in 2025 stay stable even where
   non-contiguous. Git history from the 2025 CSV-only era is not rewritten or squashed away.
4. **Respect tradition boundaries.** Attribution conventions (e.g. how the Qur'an is
   attributed) are conscious data-modeling choices, documented in `docs/data/DATA_CONTRACT.md`,
   not defaults left unexamined.

## Roadmap posture

Phase 0 (this retrofit) rehabilitates data and ships a browser. It does **not** authorize
verifying quotes at scale or building any homepage export — those are separate, later,
explicitly-scoped work units.
