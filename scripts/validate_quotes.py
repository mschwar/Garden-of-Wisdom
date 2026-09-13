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
"""
import csv
import difflib
import sys
from collections import Counter

REQUIRED_FIELDS = ["id", "quote_text", "tradition", "source_ref", "author", "tags"]
VALID_ITEM_TYPES = {"full-passage", "excerpt", "paraphrase", "oral-attribution", "unknown"}
VALID_VERIFICATION_STATUSES = {"unverified", "verified", "disputed"}

# A pair is a near-duplicate candidate when they share an exact source_ref, or
# when their text similarity exceeds this. See the module docstring for how the
# similarity is scored.
NEAR_DUPLICATE_THRESHOLD = 0.6


def pair_similarity(a, b):
    """Order-independent similarity of two texts.

    `SequenceMatcher.ratio()` is asymmetric, so scoring a pair with a single
    directional call makes the reported number a function of which row was
    visited first. Averaging both directions makes it a property of the pair.
    """
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

    # near-duplicate candidates: same source_ref root (strip trailing verse
    # variance) or high text similarity within same tradition.
    #
    # Scope ruling (#31): the text sweep stays scoped WITHIN one tradition. A
    # corpus-wide sweep adds 151 pairs on this data, 146 of them the
    # generic-`source_ref` false-positive class this report already documents,
    # so widening it now would bury the signal -- see
    # docs/data/DATA_QUALITY_REPORT.md, "Re-derivation 2026-09-13".
    by_tradition = {}
    for r in rows:
        by_tradition.setdefault(r["tradition"], []).append(r)

    def detect_pairs(groups):
        """Flag candidate pairs from the given per-tradition row groups."""
        found = []
        for trows in groups:
            for i in range(len(trows)):
                for j in range(i + 1, len(trows)):
                    a, b = trows[i], trows[j]
                    if a["id"] == b["id"]:
                        continue
                    similarity = pair_similarity(a["quote_text"], b["quote_text"])
                    if a["source_ref"] == b["source_ref"]:
                        # A shared citation is reported even with no text
                        # evidence. When the pair ALSO clears the text threshold
                        # the number is appended: the two kinds of evidence are
                        # independent, and the operator needs both to judge the
                        # pair (#31, decision 1).
                        reason = "same source_ref"
                        if similarity > NEAR_DUPLICATE_THRESHOLD:
                            reason += f"; text similarity {similarity:.2f}"
                        found.append((a["id"], b["id"], reason))
                        continue
                    if similarity > NEAR_DUPLICATE_THRESHOLD:
                        found.append((a["id"], b["id"], f"text similarity {similarity:.2f}"))
        return found

    near_dupe_pairs = detect_pairs(by_tradition.values())
    print(f"near-duplicate candidates: {len(near_dupe_pairs)}")
    for a, b, reason in near_dupe_pairs:
        print(f"  {a} ~ {b} ({reason})")

    # Hard check -- the issue this rule exists for (#31): the reported number for
    # a pair must be reproducible in the other order, i.e. it is a property of
    # the pair and not of the order the rows were visited in. Run the SAME
    # detection over the same rows with every group reversed and require an
    # identical result. Scoring a pair with a single directional
    # `SequenceMatcher.ratio()` call breaks this two ways on this corpus: pair
    # 113 ~ 114 reports 0.69 one way and 0.67 the other, and pair 189 ~ 216
    # crosses the 0.60 threshold only in one of the two orders (0.6023 vs
    # 0.5909) -- so a directional implementation changes both numbers and
    # membership. This is a hard failure: an order-dependent number is a
    # correctness bug in the validator, not a curation item.
    def canonical(pairs):
        return sorted((min(int(a), int(b)), max(int(a), int(b)), reason) for a, b, reason in pairs)

    reversed_pairs = detect_pairs([list(reversed(g)) for g in by_tradition.values()])
    print(f"pair detection re-run with every tradition's rows reversed: {len(reversed_pairs)} candidates")
    if canonical(near_dupe_pairs) != canonical(reversed_pairs):
        only_forward = sorted(set(canonical(near_dupe_pairs)) - set(canonical(reversed_pairs)))
        only_reversed = sorted(set(canonical(reversed_pairs)) - set(canonical(near_dupe_pairs)))
        fail(
            "near-duplicate detection is row-order dependent: "
            f"pairs/numbers only in file order {only_forward}, only in reversed order {only_reversed}"
        )
        hard_failures += 1

    # Reporting contract, checked independently of detect_pairs(): every reason
    # printed above must name the evidence that actually holds for that pair, as
    # re-derived here from the rows themselves. Its own falsifier is the
    # dual-reason suffix -- a pair that shares a citation AND clears the text
    # threshold must carry the number, so silently dropping the suffix fails
    # here rather than passing quietly.
    by_id = {r["id"]: r for r in rows}
    misreported = []
    for a, b, reason in near_dupe_pairs:
        ra, rb = by_id.get(a), by_id.get(b)
        if ra is None or rb is None:
            misreported.append((a, b, reason, "pair references an id not in quotes.csv"))
            continue
        similarity = pair_similarity(ra["quote_text"], rb["quote_text"])
        clears_text = similarity > NEAR_DUPLICATE_THRESHOLD
        if ra["source_ref"] == rb["source_ref"]:
            expected = "same source_ref" + (f"; text similarity {similarity:.2f}" if clears_text else "")
        else:
            expected = f"text similarity {similarity:.2f}"
        if reason != expected:
            misreported.append((a, b, reason, expected))
    print(f"near-duplicate reasons re-derived from the rows and matched: {len(near_dupe_pairs) - len(misreported)}")
    if misreported:
        fail(f"near-duplicate reasons do not match the evidence (reported, expected): {misreported}")
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
