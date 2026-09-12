#!/usr/bin/env python3
"""Emit the versioned bahai-homepage preview collection from quotes.csv + mapping.

Usage:
    python3 scripts/export_homepage_preview.py

Reads:
    quotes.csv
    exports/bahai-homepage-preview/v1/mapping.json

Writes:
    exports/bahai-homepage-preview/v1/collection.json

Does not invent wording. Accepted donors must match quotes.csv quote_text
byte-for-byte against the verified_text snapshot in mapping.json.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "bahai-homepage-preview" / "v1"
MAPPING_PATH = EXPORT_DIR / "mapping.json"
QUOTES_PATH = ROOT / "quotes.csv"
COLLECTION_PATH = EXPORT_DIR / "collection.json"

COLLECTION_META = {
    "collection_id": "garden-homepage-preview",
    "label": "Garden of Wisdom (preview)",
    "version": 1,
    "schema_version": 1,
    "description": (
        "Tiny verified Bahá’í preview export from Garden of Wisdom, produced to "
        "exercise the bahai-homepage H2B collection contract. Not Hidden Words, "
        "and not the full Garden Bahá’í subset."
    ),
    "producer": "garden-of-wisdom",
    "provenance_note": (
        "Verified 2026-09-11 against the Bahá’í Reference Library at bahai.org. "
        "Garden legacy ids are retained as upstream_id. See PROVENANCE.md in this "
        "directory."
    ),
    "rights_note": (
        "Texts are copyright © Bahá’í International Community. Personal "
        "non-commercial use with attribution is permitted; commercial use "
        "requires prior permission. See https://www.bahai.org/legal."
    ),
    "default_eligibility": {"max_words": 75},
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_quotes() -> dict[str, dict[str, str]]:
    with QUOTES_PATH.open(encoding="utf-8", newline="") as f:
        return {row["id"]: row for row in csv.DictReader(f)}


def main() -> None:
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    quotes = load_quotes()
    approved = [str(i) for i in mapping["approved_garden_ids"]]
    mapped_ids = [d["garden_id"] for d in mapping["donors"]]
    if mapped_ids != approved:
        fail(f"mapping donor ids {mapped_ids} != approved set {approved}")

    items = []
    for donor in mapping["donors"]:
        gid = donor["garden_id"]
        if gid not in quotes:
            fail(f"garden id {gid} not in quotes.csv")
        row = quotes[gid]
        if donor["verdict"] == "reject":
            continue
        if donor["verdict"] != "accept":
            fail(f"id {gid}: unknown verdict {donor['verdict']!r}")
        verified = donor["verified_text"]
        if row["quote_text"] != verified:
            fail(
                f"id {gid}: quotes.csv quote_text does not match verified_text "
                f"snapshot.\n  csv: {row['quote_text']!r}\n  map: {verified!r}"
            )
        if row["verification_status"] != "verified":
            fail(f"id {gid}: quotes.csv verification_status is {row['verification_status']!r}, expected verified")
        if row["item_type"] != donor["item_type"]:
            fail(f"id {gid}: quotes.csv item_type {row['item_type']!r} != mapping {donor['item_type']!r}")
        if row["author"] != donor["export_author"]:
            fail(f"id {gid}: quotes.csv author {row['author']!r} != export_author {donor['export_author']!r}")
        items.append(
            {
                "item_id": f"garden-{gid}",
                "text": verified,
                "author": donor["export_author"],
                "source_ref": donor["export_source_ref"],
                "source_url": donor["source_url"],
                "item_type": donor["item_type"],
                "verification_state": "verified",
                "tags": list(donor["tags"]),
                "upstream_id": gid,
            }
        )

    if not items:
        fail("no accepted donors; refusing to emit an empty collection")

    collection = dict(COLLECTION_META)
    collection["items"] = items
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    COLLECTION_PATH.write_text(
        json.dumps(collection, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {COLLECTION_PATH.relative_to(ROOT)} ({len(items)} items)")


if __name__ == "__main__":
    main()
