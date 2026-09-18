#!/usr/bin/env python3
"""Garden D4 legacy batch capture: seed/show/verify the ONE import-event capture.

Usage:
    python3 scripts/garden_legacy_batch.py seed   --dir DIR [--quotes PATH] [--json]
    python3 scripts/garden_legacy_batch.py show   --dir DIR [--json]
    python3 scripts/garden_legacy_batch.py verify --dir DIR [--quotes PATH] [--json]

Decision D4 (2026-09-12, `docs/DECISIONS.md`): the 324 legacy `quotes.csv` rows get **ONE
batch capture** for the 2026-09-11 rehabilitation import, explicitly marked `legacy-import`
and explicitly noting that encounter context is unknown. Membership links every legacy row
id to that single capture so downstream code has a uniform provenance shape — without
inventing 324 per-row encounters or creating store candidates.

What this module guarantees (and what `scripts/check_garden_legacy_batch.py` asserts):

  1. **One capture, not 324.** `cap-2026-09-11-legacy-batch` is the only capture this
     surface writes; its body is the fixed true statement about the frozen archive.
  2. **Membership covers exactly the current `quotes.csv` id set.** `seed` / `verify`
     read the CSV (read-only) and refuse a count other than 324.
  3. **Idempotent seed, no silent overwrite.** Re-seeding the same set is a no-op;
     a conflicting capture or membership is refused.
  4. **Archive digests are part of the capture body.** `verify` re-hashes the live archive
     files when present and refuses a drift from the constants baked into the capture text.
  5. **`quotes.csv` / `sources.csv` are never written.**
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from garden_store import (  # noqa: E402
    LEGACY_BATCH_ARCHIVE_QUOTES,
    LEGACY_BATCH_ARCHIVE_QUOTES_SHA256,
    LEGACY_BATCH_ARCHIVE_SOURCES,
    LEGACY_BATCH_ARCHIVE_SOURCES_SHA256,
    LEGACY_BATCH_CAPTURE_ID,
    LEGACY_BATCH_CAPTURED_TEXT,
    LEGACY_BATCH_CONTEXT_NOTES,
    LEGACY_BATCH_EXPECTED_ROW_COUNT,
    LEGACY_BATCH_RAW_ARTIFACT_REF,
    Store,
    StoreError,
    json_line,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUOTES = ROOT / "quotes.csv"


class LegacyBatchError(Exception):
    """A refusal this module is designed to make (bad input, not a bug)."""


def _read_legacy_ids(quotes_path: Path) -> list[str]:
    if not quotes_path.is_file():
        raise LegacyBatchError(f"quotes.csv not found at {quotes_path}")
    with quotes_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise LegacyBatchError(f"{quotes_path} has no data rows")
    if "id" not in rows[0]:
        raise LegacyBatchError(f"{quotes_path} has no 'id' column")
    ids = [row["id"] for row in rows]
    if any(not row_id for row_id in ids):
        raise LegacyBatchError(f"{quotes_path} has at least one empty id")
    if len(ids) != len(set(ids)):
        raise LegacyBatchError(f"{quotes_path} has duplicate id values")
    if len(ids) != LEGACY_BATCH_EXPECTED_ROW_COUNT:
        raise LegacyBatchError(
            f"{quotes_path} has {len(ids)} rows; D4 expects exactly "
            f"{LEGACY_BATCH_EXPECTED_ROW_COUNT}"
        )
    return ids


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cmd_seed(args: argparse.Namespace) -> int:
    quotes_path = Path(args.quotes) if args.quotes else DEFAULT_QUOTES
    ids = _read_legacy_ids(quotes_path)
    with Store(args.dir) as store:
        result = store.seed_legacy_batch_capture(ids)
        if args.json:
            print(json_line(result))
        else:
            print(
                f"legacy batch capture {result['capture_id']} "
                f"{result['status']} ({result['row_count']} membership rows)"
            )
        store.sync_mirror()  # U0.1: a successful seed must leave the committed mirror current
    print("RESULT: PASS")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        capture = store.legacy_batch_capture()
        members = store.legacy_batch_membership()
        if capture is None:
            raise LegacyBatchError(
                f"legacy batch capture {LEGACY_BATCH_CAPTURE_ID!r} is not seeded"
            )
        payload = {
            "capture_id": capture["capture_id"],
            "capture_method": capture["capture_method"],
            "captured_by": capture["captured_by"],
            "captured_at": capture["captured_at"],
            "context_notes": capture["context_notes"],
            "raw_artifact_ref": capture["raw_artifact_ref"],
            "membership_count": len(members),
        }
        if args.json:
            print(json_line(payload))
        else:
            print(
                f"capture {payload['capture_id']} "
                f"({payload['capture_method']}/{payload['captured_by']}) "
                f"at {payload['captured_at']}; membership={payload['membership_count']}"
            )
            print(f"context_notes: {payload['context_notes']}")
    print("RESULT: PASS")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    quotes_path = Path(args.quotes) if args.quotes else DEFAULT_QUOTES
    expected_ids = set(_read_legacy_ids(quotes_path))
    with Store(args.dir) as store:
        capture = store.legacy_batch_capture()
        if capture is None:
            raise LegacyBatchError(
                f"legacy batch capture {LEGACY_BATCH_CAPTURE_ID!r} is not seeded"
            )
        if capture["captured_text"] != LEGACY_BATCH_CAPTURED_TEXT:
            raise LegacyBatchError(
                "seeded capture text does not match the D4 constant (capture body drifted)"
            )
        if capture["context_notes"] != LEGACY_BATCH_CONTEXT_NOTES:
            raise LegacyBatchError(
                "seeded context_notes do not match the D4 constant"
            )
        if capture["raw_artifact_ref"] != LEGACY_BATCH_RAW_ARTIFACT_REF:
            raise LegacyBatchError(
                "seeded raw_artifact_ref does not match the D4 constant"
            )
        if capture["capture_method"] != "legacy-import" or capture["captured_by"] != "legacy-import":
            raise LegacyBatchError(
                "seeded capture is not marked legacy-import on method and captured_by"
            )
        members = store.legacy_batch_membership()
        member_ids = {row["legacy_row_id"] for row in members}
        if member_ids != expected_ids:
            missing = sorted(expected_ids - member_ids)
            extra = sorted(member_ids - expected_ids)
            raise LegacyBatchError(
                "membership set does not equal quotes.csv ids "
                f"(missing={missing[:5]}{'…' if len(missing) > 5 else ''}, "
                f"extra={extra[:5]}{'…' if len(extra) > 5 else ''})"
            )
        for row in members:
            if row["capture_id"] != LEGACY_BATCH_CAPTURE_ID:
                raise LegacyBatchError(
                    f"membership for {row['legacy_row_id']!r} points at "
                    f"{row['capture_id']!r}, not {LEGACY_BATCH_CAPTURE_ID!r}"
                )

    archive_quotes = ROOT / LEGACY_BATCH_ARCHIVE_QUOTES
    archive_sources = ROOT / LEGACY_BATCH_ARCHIVE_SOURCES
    if archive_quotes.is_file():
        digest = _sha256(archive_quotes)
        if digest != LEGACY_BATCH_ARCHIVE_QUOTES_SHA256:
            raise LegacyBatchError(
                f"live {LEGACY_BATCH_ARCHIVE_QUOTES} sha256={digest} does not match "
                f"the capture constant {LEGACY_BATCH_ARCHIVE_QUOTES_SHA256}"
            )
    if archive_sources.is_file():
        digest = _sha256(archive_sources)
        if digest != LEGACY_BATCH_ARCHIVE_SOURCES_SHA256:
            raise LegacyBatchError(
                f"live {LEGACY_BATCH_ARCHIVE_SOURCES} sha256={digest} does not match "
                f"the capture constant {LEGACY_BATCH_ARCHIVE_SOURCES_SHA256}"
            )

    payload = {
        "capture_id": LEGACY_BATCH_CAPTURE_ID,
        "membership_count": len(expected_ids),
        "quotes_path": str(quotes_path),
    }
    if args.json:
        print(json_line(payload))
    else:
        print(
            f"verified {payload['capture_id']} against {payload['membership_count']} "
            f"quotes.csv ids and archive digests"
        )
    print("RESULT: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed, show, or verify the D4 legacy batch capture."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="create the batch capture + membership from quotes.csv")
    seed.add_argument("--dir", required=True, help="store directory")
    seed.add_argument("--quotes", default=None, help="path to quotes.csv (default: repo root)")
    seed.add_argument("--json", action="store_true")
    seed.set_defaults(func=cmd_seed)

    show = sub.add_parser("show", help="print the seeded batch capture summary")
    show.add_argument("--dir", required=True, help="store directory")
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=cmd_show)

    verify = sub.add_parser(
        "verify",
        help="assert membership equals quotes.csv and capture body matches constants",
    )
    verify.add_argument("--dir", required=True, help="store directory")
    verify.add_argument("--quotes", default=None, help="path to quotes.csv (default: repo root)")
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (LegacyBatchError, StoreError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
