#!/usr/bin/env python3
"""Validate exports/bahai-homepage-preview/v1 against the H2B collection contract.

Usage:
    python3 scripts/validate_homepage_preview_export.py

Checks the producer-agnostic H2B-A schema (bahai-homepage
docs/architecture/COLLECTION_CONTRACT.md, accepted as D27) plus Garden-specific
constraints for this preview: approved donor ids only, no paraphrases, verified
text frozen against quotes.csv, rejected donors absent.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "bahai-homepage-preview" / "v1"
COLLECTION_PATH = EXPORT_DIR / "collection.json"
MAPPING_PATH = EXPORT_DIR / "mapping.json"
QUOTES_PATH = ROOT / "quotes.csv"

COLLECTION_ID_RE = re.compile(r"^[a-z0-9-]+$")
ITEM_TYPES = {"full-passage", "excerpt", "paraphrase", "oral-attribution", "unknown"}
VERIFICATION_STATES = {"unverified", "verified", "disputed"}
REQUIRED_COLLECTION = [
    "collection_id",
    "label",
    "version",
    "schema_version",
    "description",
    "producer",
    "provenance_note",
    "rights_note",
    "default_eligibility",
    "items",
]
REQUIRED_ITEM = [
    "item_id",
    "text",
    "source_ref",
    "source_url",
    "item_type",
    "verification_state",
]


def fail(msg: str, hard: list[int]) -> None:
    print(f"FAIL: {msg}")
    hard[0] += 1


def warn(msg: str) -> None:
    print(f"WARN: {msg}")


def count_words(text: str) -> int:
    return len([w for w in (text or "").strip().split() if w])


def well_formed_url(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> None:
    hard = [0]
    if not COLLECTION_PATH.is_file():
        fail(f"missing {COLLECTION_PATH.relative_to(ROOT)}", hard)
        raise SystemExit(1)
    if not MAPPING_PATH.is_file():
        fail(f"missing {MAPPING_PATH.relative_to(ROOT)}", hard)
        raise SystemExit(1)

    try:
        collection = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"collection.json is not valid JSON: {e}", hard)
        raise SystemExit(1)

    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    approved = {str(i) for i in mapping["approved_garden_ids"]}
    accepted_ids = {d["garden_id"] for d in mapping["donors"] if d["verdict"] == "accept"}
    rejected_ids = {d["garden_id"] for d in mapping["donors"] if d["verdict"] == "reject"}

    with QUOTES_PATH.open(encoding="utf-8", newline="") as f:
        quotes = {row["id"]: row for row in csv.DictReader(f)}

    if not isinstance(collection, dict):
        fail("collection root must be an object, not an array", hard)
        raise SystemExit(1)

    for field in REQUIRED_COLLECTION:
        if field not in collection:
            fail(f"missing collection field: {field}", hard)

    cid = collection.get("collection_id")
    if not isinstance(cid, str) or not COLLECTION_ID_RE.fullmatch(cid or ""):
        fail(f"collection_id must match [a-z0-9-]+: {cid!r}", hard)

    for field in ("label", "description", "producer", "provenance_note", "rights_note"):
        if field in collection and not isinstance(collection[field], str):
            fail(f"{field} must be a string", hard)

    if collection.get("version") != 1:
        fail(f"version must be integer 1 for this preview, got {collection.get('version')!r}", hard)
    if collection.get("schema_version") != 1:
        fail(
            f"unrecognized schema_version {collection.get('schema_version')!r} (known: 1)",
            hard,
        )

    elig = collection.get("default_eligibility")
    if not isinstance(elig, dict) or set(elig.keys()) != {"max_words"}:
        fail("default_eligibility must be {\"max_words\": <int>} for schema_version 1", hard)
    elif not isinstance(elig.get("max_words"), int) or elig["max_words"] < 1:
        fail(f"max_words must be a positive int, got {elig.get('max_words')!r}", hard)

    items = collection.get("items")
    if not isinstance(items, list):
        fail("items must be an array", hard)
        items = []
    if not items:
        fail("items must not be empty for this preview export", hard)

    item_ids = []
    texts = []
    upstream_ids = []
    max_words = elig.get("max_words") if isinstance(elig, dict) else 75

    for i, item in enumerate(items):
        loc = f"items[{i}]"
        if not isinstance(item, dict):
            fail(f"{loc} is not an object", hard)
            continue
        for field in REQUIRED_ITEM:
            if field not in item:
                fail(f"{loc} missing field: {field}", hard)
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            fail(f"{loc}.item_id must be a non-empty string", hard)
        else:
            item_ids.append(item_id)
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            fail(f"{loc}.text must be a non-empty string", hard)
        else:
            texts.append(text)
            if isinstance(max_words, int) and count_words(text) > max_words:
                fail(f"{loc} exceeds max_words={max_words} ({count_words(text)} words)", hard)
        if "author" in item and item["author"] is not None and not isinstance(item["author"], str):
            fail(f"{loc}.author must be a string if present", hard)
        if not isinstance(item.get("source_ref"), str) or not item.get("source_ref"):
            fail(f"{loc}.source_ref must be a non-empty string", hard)
        if not well_formed_url(item.get("source_url")):
            fail(f"{loc}.source_url must be null or a well-formed http(s) URL", hard)
        if item.get("item_type") not in ITEM_TYPES:
            fail(f"{loc}.item_type invalid: {item.get('item_type')!r}", hard)
        if item.get("item_type") == "paraphrase":
            fail(f"{loc}: paraphrase may not be emitted as exact scripture", hard)
        if item.get("verification_state") not in VERIFICATION_STATES:
            fail(f"{loc}.verification_state invalid: {item.get('verification_state')!r}", hard)
        if item.get("verification_state") != "verified":
            fail(f"{loc}: this preview may only emit verified items", hard)
        tags = item.get("tags", [])
        if tags is None:
            tags = []
        if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
            fail(f"{loc}.tags must be an array of strings", hard)
        upstream = item.get("upstream_id")
        if not isinstance(upstream, str) or not upstream:
            fail(f"{loc}.upstream_id must be a Garden id string", hard)
        else:
            upstream_ids.append(upstream)
            if upstream not in approved:
                fail(f"{loc}.upstream_id {upstream} is not in the approved donor set {sorted(approved)}", hard)
            if upstream in rejected_ids:
                fail(f"{loc}: rejected donor {upstream} must not appear in items", hard)
            if upstream not in quotes:
                fail(f"{loc}: upstream_id {upstream} not in quotes.csv", hard)
            elif quotes[upstream]["quote_text"] != text:
                fail(f"{loc}: text does not match quotes.csv id {upstream}", hard)
            elif quotes[upstream]["verification_status"] != "verified":
                fail(f"{loc}: quotes.csv id {upstream} is not verified", hard)

    dup_ids = sorted({x for x in item_ids if item_ids.count(x) > 1})
    if dup_ids:
        fail(f"duplicate item_id values: {dup_ids}", hard)

    text_counts: dict[str, int] = {}
    for t in texts:
        text_counts[t] = text_counts.get(t, 0) + 1
    dup_texts = [t for t, c in text_counts.items() if c > 1]
    if dup_texts:
        warn(f"exact-duplicate text within collection: {len(dup_texts)} group(s)")

    missing_accepted = sorted(accepted_ids - set(upstream_ids))
    if missing_accepted:
        fail(f"accepted donors missing from items: {missing_accepted}", hard)

    leaked_rejected = sorted(set(upstream_ids) & rejected_ids)
    if leaked_rejected:
        fail(f"rejected donors present in items: {leaked_rejected}", hard)

    extra_mapped = sorted(set(upstream_ids) - accepted_ids)
    if extra_mapped:
        fail(f"items whose upstream_id is not an accepted donor: {extra_mapped}", hard)

    digest = hashlib.sha256(COLLECTION_PATH.read_bytes()).hexdigest()
    print(f"collection: {COLLECTION_PATH.relative_to(ROOT)}")
    print(f"schema_version: {collection.get('schema_version')}")
    print(f"collection_id: {collection.get('collection_id')}")
    print(f"items: {len(items)}")
    print(f"upstream_ids: {upstream_ids}")
    print(f"rejected (not exported): {sorted(rejected_ids)}")
    print(f"sha256: {digest}")
    print()
    if hard[0]:
        print(f"RESULT: FAIL ({hard[0]} hard failure(s))")
        raise SystemExit(1)
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
