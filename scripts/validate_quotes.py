#!/usr/bin/env python3
"""Deterministic validator for quotes.csv / sources.csv.

Usage:
    python3 scripts/validate_quotes.py

Exits non-zero if any hard-failure check fails (parse errors, malformed
UTF-8, duplicate IDs, missing required fields, invalid controlled values).
Everything else (near-duplicates, unresolved source links, unknown item
type) is reported but does not fail the run -- those are curation queue
items, not data-integrity bugs.
"""
import csv
import difflib
import sys
from collections import Counter

REQUIRED_FIELDS = ["id", "quote_text", "tradition", "source_ref", "author", "tags"]
VALID_ITEM_TYPES = {"full-passage", "excerpt", "paraphrase", "oral-attribution", "unknown"}
VALID_VERIFICATION_STATUSES = {"unverified", "verified", "disputed"}


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
    near_dupe_pairs = []
    by_tradition = {}
    for r in rows:
        by_tradition.setdefault(r["tradition"], []).append(r)
    for trad, trows in by_tradition.items():
        for i in range(len(trows)):
            for j in range(i + 1, len(trows)):
                a, b = trows[i], trows[j]
                if a["source_ref"] == b["source_ref"] and a["id"] != b["id"]:
                    near_dupe_pairs.append((a["id"], b["id"], "same source_ref"))
                    continue
                ratio = difflib.SequenceMatcher(None, a["quote_text"], b["quote_text"]).ratio()
                if ratio > 0.6:
                    near_dupe_pairs.append((a["id"], b["id"], f"text similarity {ratio:.2f}"))
    print(f"near-duplicate candidates: {len(near_dupe_pairs)}")
    for a, b, reason in near_dupe_pairs:
        print(f"  {a} ~ {b} ({reason})")

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
