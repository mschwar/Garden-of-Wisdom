#!/usr/bin/env python3
"""Deterministic validator for quotes.csv / sources.csv.

Usage:
    python3 scripts/validate_quotes.py

Exits non-zero if any hard-failure check fails (parse errors, malformed
UTF-8, duplicate IDs, missing required fields, invalid controlled values,
or a near-duplicate score that depends on row order).

Everything else (near-duplicates, unresolved source links, unknown item
type) is reported but does not fail the run -- those are curation queue
items, not data-integrity bugs.

Near-duplicate scoring rule: a pair's similarity is the MEAN OF BOTH
DIRECTIONAL `difflib.SequenceMatcher.ratio()` values, because that ratio is
not symmetric (rows 113/114 score 0.6888... one way and 0.6666... the other).
The number a pair is reported with is therefore a property of the pair, not
of the order the two rows happen to be visited in -- and the run asserts that
for every pair it reports.

Near-duplicate scope and citation rule (both decided 2026-09-13, issue #34):

- the sweep is CORPUS-WIDE, not scoped within one `tradition`. A duplicate can
  be filed under a different `tradition` label, so a sweep scoped to one label
  cannot see the class of defect it exists to catch. A hard check re-derives the
  pair set from the rows with no grouping at all and fails if the reported sweep
  is narrower than that.
- a shared `source_ref` is evidence only when the citation PINPOINTS a place (a
  locator: an Arabic digit, a Roman numeral, or the section mark). That is W1.4
  ruling 2, whose implementation is imported from `garden_normalize`
  (`citation_specificity`) rather than re-implemented here, so the store and
  this legacy-corpus validator cannot drift into two definitions of one rule.

The measurement behind both rulings, and what each does to the counts, is in
`docs/data/DATA_QUALITY_REPORT.md` under "Re-derivation 2026-09-13 (issue #34)".
"""
import csv
import difflib
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# Ruling 2's locator test, imported so there is ONE implementation of it. The
# import is deliberately not optional: a silently missing rule would weaken the
# sweep, and a change to the store's rule must show up here as a named drift
# failure rather than as a quietly moved pair count.
from garden_normalize import citation_specificity  # noqa: E402

REQUIRED_FIELDS = ["id", "quote_text", "tradition", "source_ref", "author", "tags"]
VALID_ITEM_TYPES = {"full-passage", "excerpt", "paraphrase", "oral-attribution", "unknown"}
VALID_VERIFICATION_STATUSES = {"unverified", "verified", "disputed"}

# A pair is a near-duplicate candidate when they share an exact source_ref, or
# when their text similarity exceeds this. See the module docstring for how the
# similarity is scored.
NEAR_DUPLICATE_THRESHOLD = 0.6

#: Character multiset per text, memoized across the passes below. Pure cache.
_CHAR_COUNTS = {}


def _char_counts(text):
    """Character multiset of a text, cached: the pre-filter below needs it per pair."""
    counts = _CHAR_COUNTS.get(text)
    if counts is None:
        counts = _CHAR_COUNTS[text] = Counter(text)
    return counts


def pair_similarity(a, b):
    """Order-independent similarity of two texts.

    `SequenceMatcher.ratio()` is asymmetric, so scoring a pair with a single
    directional call makes the reported number a function of which row was
    visited first. Averaging both directions makes it a property of the pair.

    Exact pre-filter. `ratio() == 2*M / (len(a) + len(b))` where `M`, the number
    of matching characters, cannot exceed the size of the two texts' multiset
    intersection -- so as soon as that bound cannot clear the threshold the pair
    needs no scoring at all. The sweep is corpus-wide, i.e. every unordered pair
    (52,326 of them on this corpus), and this halves the pairs handed to
    `SequenceMatcher`. It cannot change any output: a pair it declines to score
    is one that provably could not have been flagged, and a score is only ever
    printed for a pair that was.
    """
    la, lb = len(a), len(b)
    ca, cb = _char_counts(a), _char_counts(b)
    smaller, larger = (ca, cb) if len(ca) <= len(cb) else (cb, ca)
    overlap = 0
    for char, count in smaller.items():
        other = larger.get(char)
        if other:
            overlap += count if count < other else other
    if 2 * overlap <= NEAR_DUPLICATE_THRESHOLD * (la + lb):
        return 0.0
    forward = difflib.SequenceMatcher(None, a, b).ratio()
    backward = difflib.SequenceMatcher(None, b, a).ratio()
    return (forward + backward) / 2.0



def fail(msg):
    print(f"FAIL: {msg}")


def warn(msg):
    print(f"WARN: {msg}")


def main():
    hard_failures = 0

    try:
        raw = open("quotes.csv", "rb").read()
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        fail(f"quotes.csv is not valid UTF-8: {e}")
        hard_failures += 1
        return sys.exit(1)

    with open("quotes.csv", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    for req in REQUIRED_FIELDS:
        if req not in fieldnames:
            fail(f"missing required column: {req}")
            hard_failures += 1

    print(f"parsed {len(rows)} quote rows, {len(fieldnames)} columns: {fieldnames}")

    ids = [r["id"] for r in rows]
    id_counts = Counter(ids)
    dupes = [i for i, c in id_counts.items() if c > 1]
    if dupes:
        fail(f"duplicate ids: {dupes}")
        hard_failures += 1
    else:
        print("duplicate ids: none")

    nums = sorted(int(i) for i in ids if i.isdigit())
    gaps = [(a, b) for a, b in zip(nums, nums[1:]) if b - a > 1]
    print(f"id range: {nums[0]}-{nums[-1]} ({len(nums)} ids). non-contiguous gaps (expected, legacy IDs preserved): {gaps}")

    missing_field_rows = []
    for r in rows:
        for req in REQUIRED_FIELDS:
            if not r.get(req, "").strip():
                missing_field_rows.append((r["id"], req))
    if missing_field_rows:
        fail(f"rows with missing required fields: {missing_field_rows}")
        hard_failures += 1
    else:
        print("missing required fields: none")

    valid_traditions = set(r["tradition"] for r in rows)
    print(f"traditions in use ({len(valid_traditions)}): {sorted(valid_traditions)}")

    bad_item_types = [r["id"] for r in rows if r.get("item_type", "") not in VALID_ITEM_TYPES]
    if bad_item_types:
        fail(f"rows with invalid item_type: {bad_item_types}")
        hard_failures += 1

    bad_verif = [r["id"] for r in rows if r.get("verification_status", "") not in VALID_VERIFICATION_STATUSES]
    if bad_verif:
        fail(f"rows with invalid verification_status: {bad_verif}")
        hard_failures += 1

    exact_text = Counter(r["quote_text"].strip() for r in rows)
    exact_dupes = {t: c for t, c in exact_text.items() if c > 1}
    print(f"exact duplicate quote_text groups: {len(exact_dupes)}")
    for t, c in exact_dupes.items():
        print(f"  x{c}: {t[:80]!r}")

    # Near-duplicate candidates, corpus-wide (#34). Two rulings decided with the
    # measurement recorded in docs/data/DATA_QUALITY_REPORT.md ("Re-derivation
    # 2026-09-13 (issue #34)"):
    #
    # SCOPE -- the sweep runs over every row, not within one `tradition`. #31
    # kept it scoped and recorded why: widening the sweep *as the rules then
    # were* added 151 pairs, 146 of them the generic-`source_ref` false-positive
    # class. The citation rule below removes exactly that noise, so the reason
    # for scoping is gone; measured, corpus-wide under both rules adds 5 pairs,
    # all text-similarity driven and none of them label noise.
    #
    # CITATION RULE -- a shared `source_ref` is evidence only when it is
    # SPECIFIC (carries a locator). This is W1.4 ruling 2; see the import above.
    groups = [rows]

    def detected_reason(a, b):
        """Why this pair is flagged, or None when it is not flagged at all."""
        similarity = pair_similarity(a["quote_text"], b["quote_text"])
        if (a["source_ref"] == b["source_ref"]
                and citation_specificity(a["source_ref"]) == "specific"):
            # A specific shared citation is reported even with no text
            # evidence. When the pair ALSO clears the text threshold the number
            # is appended: the two kinds of evidence are independent, and the
            # operator needs both to judge the pair (#31, decision 1).
            suffix = f"; text similarity {similarity:.2f}" if similarity > NEAR_DUPLICATE_THRESHOLD else ""
            return f"same specific citation{suffix}"
        if similarity > NEAR_DUPLICATE_THRESHOLD:
            return f"text similarity {similarity:.2f}"
        return None

    def detect_pairs(row_groups):
        """Flag candidate pairs from the given row groups."""
        found = []
        for trows in row_groups:
            for i in range(len(trows)):
                for j in range(i + 1, len(trows)):
                    a, b = trows[i], trows[j]
                    if a["id"] == b["id"]:
                        continue
                    reason = detected_reason(a, b)
                    if reason is not None:
                        found.append((a["id"], b["id"], reason))
        return found

    def canonical(pairs):
        return sorted((min(int(a), int(b)), max(int(a), int(b)), reason) for a, b, reason in pairs)

    near_dupe_pairs = detect_pairs(groups)
    print(f"near-duplicate candidates: {len(near_dupe_pairs)} (corpus-wide)")
    for a, b, reason in near_dupe_pairs:
        print(f"  {a} ~ {b} ({reason})")

    # Hard check 1 -- SCOPE (#34). The detection above is handed `groups`; this
    # walks every unordered pair of rows itself, with no grouping at all, so a
    # sweep narrowed back to per-`tradition` groups cannot pass. A narrower
    # report is internally consistent, so nothing else can catch that reversion:
    # this is the guard #31 recorded as missing (its control c4, "the scope has
    # no automated falsifier"). It shares the reason rule with `detect_pairs`,
    # which hard check 3 covers independently -- what it proves on its own is
    # that the scope really is the whole corpus.
    blind_scan = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            reason = detected_reason(rows[i], rows[j])
            if reason is not None:
                blind_scan.append((rows[i]["id"], rows[j]["id"], reason))
    if canonical(near_dupe_pairs) != canonical(blind_scan):
        missing = sorted(set(canonical(blind_scan)) - set(canonical(near_dupe_pairs)))
        extra = sorted(set(canonical(near_dupe_pairs)) - set(canonical(blind_scan)))
        fail(
            "the near-duplicate sweep is not corpus-wide: pairs/numbers only in the "
            f"corpus-wide scan {missing}, only in the reported sweep {extra}"
        )
        hard_failures += 1

    # Hard check 2 -- the issue this rule exists for (#31): the reported number for
    # a pair must be reproducible in the other order, i.e. it is a property of
    # the pair and not of the order the rows were visited in. Run the SAME
    # detection over the same rows with the order reversed and require an
    # identical result. Scoring a pair with a single directional
    # `SequenceMatcher.ratio()` call breaks this two ways on this corpus: pair
    # 113 ~ 114 reports 0.69 one way and 0.67 the other, and pair 189 ~ 216
    # crosses the 0.60 threshold only in one of the two orders (0.6023 vs
    # 0.5909) -- so a directional implementation changes both numbers and
    # membership. This is a hard failure: an order-dependent number is a
    # correctness bug in the validator, not a curation item.
    reversed_pairs = detect_pairs([list(reversed(g)) for g in groups])
    print(f"pair detection re-run with the corpus rows reversed: {len(reversed_pairs)} candidates")
    if canonical(near_dupe_pairs) != canonical(reversed_pairs):
        only_forward = sorted(set(canonical(near_dupe_pairs)) - set(canonical(reversed_pairs)))
        only_reversed = sorted(set(canonical(reversed_pairs)) - set(canonical(near_dupe_pairs)))
        fail(
            "near-duplicate detection is row-order dependent: "
            f"pairs/numbers only in file order {only_forward}, only in reversed order {only_reversed}"
        )
        hard_failures += 1

    # Hard check 3 -- reporting contract, checked independently of
    # `detected_reason`: every reason printed above must name the evidence that
    # actually holds for that pair, re-derived here from the rows with the rule
    # written out inline. Its own falsifiers are a dropped locator condition (a
    # generic shared `source_ref` reported as citation evidence -- the rule
    # #34 adopted) and the dropped dual-reason suffix (#31's control c3).
    by_id = {r["id"]: r for r in rows}
    misreported = []
    for a, b, reason in near_dupe_pairs:
        ra, rb = by_id.get(a), by_id.get(b)
        if ra is None or rb is None:
            misreported.append((a, b, reason, "pair references an id not in quotes.csv"))
            continue
        similarity = pair_similarity(ra["quote_text"], rb["quote_text"])
        clears_text = similarity > NEAR_DUPLICATE_THRESHOLD
        shared_specific = (ra["source_ref"] == rb["source_ref"]
                           and citation_specificity(ra["source_ref"]) == "specific")
        if shared_specific:
            expected = "same specific citation" + (f"; text similarity {similarity:.2f}" if clears_text else "")
        elif clears_text:
            expected = f"text similarity {similarity:.2f}"
        else:
            expected = None  # nothing in the evidence flags this pair
        if reason != expected:
            misreported.append((a, b, reason, expected))
    print(f"near-duplicate reasons re-derived from the rows and matched: {len(near_dupe_pairs) - len(misreported)}")
    if misreported:
        fail(f"near-duplicate reasons do not match the evidence (reported, expected): {misreported}")
        hard_failures += 1

    # Hard check 4 -- the imported locator rule still means what the ruling
    # assumes, and it is doing work on this corpus. Because
    # `citation_specificity` comes from `garden_normalize`, a change to the
    # store's rule would otherwise move this report silently (both guard 1 and
    # guard 3 call the same function, so they cannot see it). Pin the two
    # canonical outcomes -- a bare label is generic, a pinpoint is specific --
    # and require the corpus to offer at least one pair the rule suppresses, so
    # the suppression cannot be vacuous.
    for value, expected_class in (("Oral Tradition", "generic"), ("Gita 2.47", "specific")):
        actual_class = citation_specificity(value)
        if actual_class != expected_class:
            fail(
                f"citation rule drift: citation_specificity({value!r}) is {actual_class!r}, "
                f"but this report's ruling assumes {expected_class!r}"
            )
            hard_failures += 1
    shared_ref_pairs = [
        (rows[i], rows[j])
        for i in range(len(rows))
        for j in range(i + 1, len(rows))
        if rows[i]["source_ref"] == rows[j]["source_ref"]
    ]
    suppressed = [p for p in shared_ref_pairs if citation_specificity(p[0]["source_ref"]) != "specific"]
    print(
        f"pairs sharing an exact source_ref (corpus-wide): {len(shared_ref_pairs)} "
        f"-- {len(shared_ref_pairs) - len(suppressed)} specific (citation evidence), "
        f"{len(suppressed)} generic (suppressed by the locator rule)"
    )
    if not suppressed:
        fail(
            "vacuity guard: no pair on this corpus shares a generic source_ref, so the locator "
            "rule's suppression cannot be shown to do work -- re-derive this guard against the "
            "current corpus rather than letting it pass on nothing"
        )
        hard_failures += 1

    unresolved = [r["id"] for r in rows if not r.get("source_id", "").strip()]
    print(f"unresolved source links: {len(unresolved)} -> ids {unresolved}")

    unresolved_glyphs = [r["id"] for r in rows if r.get("has_unresolved_glyph") == "true"]
    print(f"rows with unresolved glyph markers (literal '_' standing in for an untyped character): {len(unresolved_glyphs)} -> ids {unresolved_glyphs}")

    type_counts = Counter(r.get("item_type", "") for r in rows)
    print(f"counts by item_type: {dict(type_counts)}")
    verif_counts = Counter(r.get("verification_status", "") for r in rows)
    print(f"counts by verification_status: {dict(verif_counts)}")

    # sources.csv checks
    try:
        with open("sources.csv", encoding="utf-8", newline="") as f:
            src_reader = csv.DictReader(f)
            src_rows = list(src_reader)
    except UnicodeDecodeError as e:
        fail(f"sources.csv is not valid UTF-8: {e}")
        hard_failures += 1
        src_rows = []

    src_ids = set(s["source_id"] for s in src_rows)
    print(f"sources.csv: {len(src_rows)} rows, ids: {sorted(src_ids)}")
    dangling = [r["id"] for r in rows if r.get("source_id") and r["source_id"] not in src_ids]
    if dangling:
        fail(f"quotes reference source_id not present in sources.csv: {dangling}")
        hard_failures += 1

    print()
    if hard_failures:
        print(f"RESULT: FAIL ({hard_failures} hard failure categories)")
        sys.exit(1)
    else:
        print("RESULT: PASS (no hard-integrity failures; see WARN-level items above for curation queue)")
        sys.exit(0)


if __name__ == "__main__":
    main()
