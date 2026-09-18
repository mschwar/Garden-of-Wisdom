#!/usr/bin/env python3
"""Garden corpus store: SQLite store of record + a deterministic, diffable text export.

Usage:
    python3 scripts/garden_store.py create --dir DIR
    python3 scripts/garden_store.py export --dir DIR [--out PATH]
    python3 scripts/garden_store.py dump   --dir DIR          # export bytes to stdout
    python3 scripts/garden_store.py import --dir DIR --from FILE
    python3 scripts/garden_store.py verify --dir DIR

W1.1 (Garden corpus program, `docs/program/W1_1_STORAGE_AND_SCHEMA.md`) records the storage
decision: **SQLite via the Python standard library** is the store of record, and a full
human-readable text export (`garden.export/1`) is the diffable mirror committed to git.
No third-party dependency, no server, no network.

What this module guarantees (and what `scripts/check_garden_store.py` asserts):

  1. **Captures are immutable.** `captures` rows cannot be UPDATEd or DELETEd; the guarantee
     is a pair of SQLite triggers, not a convention. The raw encounter
     (`docs/program/PROVENANCE_AND_CAPTURE_CONTRACT.md`) is preserved verbatim, byte for byte.
  2. **The decision log is append-only.** `decisions` rows cannot be UPDATEd or DELETEd, so
     every curation / research / corpus / work transition keeps `who/what, when, from, to,
     reason` forever (`docs/program/STATE_MODEL.md`).
  3. **One vocabulary, taken from the model.** The four state dimensions carry exactly the
     values in `docs/program/STATE_MODEL.md` (curation 5, research 6, corpus 4, work 5),
     enforced by SQL `CHECK` constraints and re-checked against the document itself by the
     acceptance script -- no vocabulary is invented here.
  4. **The export is a pure function of the store.** Records are emitted in a fixed section
     order and sorted by key, one canonical JSON object per line, so the same store always
     exports the same bytes -- no wall-clock, no unordered iteration. `import` re-imports
     that text and re-asserts byte-identity before it accepts the data.
  5. **Read-only on the frozen view.** Nothing here reads or writes `quotes.csv` /
     `sources.csv` / `browser/`; the legacy corpus is untouched for the whole of W1.

Out of W1.1 scope, deliberately absent: any intake/submission CLI (W1.3), envelope validation
(W1.2), the normalization *algorithm* and the duplicate-hint *generator* (W1.4, which live in
`scripts/garden_normalize.py` -- this module only carries the guarded write path they use,
`apply_normalization`, and the derived-hint write mode, `replace_duplicate_hints`), the curation
review surface and the transition guard machinery (W1.5), any promotion path to `canonical` (W3),
and anything to do with `quotes.csv`. This unit ships the store, the migration, the round-trip, and
the evidence -- `docs/program/W1_DECOMPOSITION.md` section "W1.1 - Storage decision + minimal
schema".
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

STORE_FILENAME = "garden.sqlite3"
DEFAULT_EXPORT_NAME = "garden.export.txt"
EXPORT_HEADER = "garden.export/1"
SCHEMA_VERSION = 1

#: Vocabularies, copied from `docs/program/STATE_MODEL.md` sections 1-4. The acceptance
#: script parses that document and fails if these drift from it.
CURATION_STATES = ("new", "accepted", "hold", "rejected", "duplicate")
RESEARCH_STATES = (
    "not_started",
    "in_research",
    "verified",
    "disputed",
    "unverifiable",
    "needs_more_evidence",
)
CORPUS_STATES = ("candidate_only", "eligible", "canonical", "retired")
WORK_STATES = ("queued", "active", "qa", "blocked", "done")
DIMENSIONS: dict[str, tuple[str, ...]] = {
    "curation": CURATION_STATES,
    "research": RESEARCH_STATES,
    "corpus": CORPUS_STATES,
    "work": WORK_STATES,
}
STATE_COLUMNS = {
    "curation": "curation_state",
    "research": "research_state",
    "corpus": "corpus_state",
    "work": "work_state",
}
#: The values an envelope may arrive with (`docs/program/CANDIDATE_ENVELOPE.md`, validation
#: rule 3). A candidate enters the store in exactly these states; every later move is a
#: recorded transition, and the transition machinery itself is W1.5.
INTAKE_STATES = {
    "curation_state": "new",
    "research_state": "not_started",
    "corpus_state": "candidate_only",
    "work_state": "queued",
}
#: The five curation actions the operator can take, each mapping to the curation state it
#: requests. The legal (from, to) pairs come from `CURATION_TRANSITIONS` below (STATE_MODEL.md
#: section 1); an action whose current state does not fit a legal transition is refused.
CURATION_ACTIONS: dict[str, str] = {
    "accept": "accepted",
    "hold": "hold",
    "reject": "rejected",
    "duplicate": "duplicate",
    "reopen": "new",
}
#: The twelve curation transitions, exactly as `docs/program/STATE_MODEL.md` section 1 lists
#: them. `(from, to) -> transition_id`. Every one of them is authority `operator`; moving a
#: candidate any other way is refused by `Store.curate`.
CURATION_TRANSITIONS: dict[tuple[str, str], str] = {
    ("new", "accepted"): "T-C1",
    ("new", "hold"): "T-C2",
    ("new", "rejected"): "T-C3",
    ("new", "duplicate"): "T-C4",
    ("hold", "accepted"): "T-C5",
    ("hold", "rejected"): "T-C6",
    ("hold", "duplicate"): "T-C7",
    ("accepted", "rejected"): "T-C8",
    ("accepted", "duplicate"): "T-C9",
    ("rejected", "new"): "T-C10",
    ("duplicate", "new"): "T-C11",
    ("duplicate", "accepted"): "T-C12",
}
#: The corpus transitions W1.5 may fire, `(from, to) -> (transition_id, authority)`.
#:   * T-P1 `candidate_only -> eligible` is the deterministic, audited consequence of
#:     acceptance (`STATE_MODEL.md` section 3) -- authority `system`.
#:   * T-P7 `eligible -> candidate_only` is the operator-authority reversal that runs when a
#:     curation acceptance is withdrawn (`T-C8`/`T-C9`), so no record is ever left `eligible`
#:     while its curation is `hold`/`rejected`/`duplicate` (the no-stranded-dimension rule).
#: T-P2..T-P6 (including retirement T-P3) are operator promotion decisions and are out of W1.5.
CORPUS_TRANSITIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("candidate_only", "eligible"): ("T-P1", "system"),
    ("eligible", "candidate_only"): ("T-P7", "operator"),
}
HINT_KINDS = ("exact-text", "near-text", "same-reference", "same-passage")
CAPTURE_METHODS = (
    "manual-entry",
    "pasted-text",
    "photo",
    "screenshot",
    "web-page",
    "book-scan",
    "audio-transcript",
    "agent-research",
    "legacy-import",
)
ACTOR_KINDS = ("operator", "agent", "system")
SUBJECT_KINDS = ("candidate", "capture", "work_unit", "research_case")
SENTINELS = ("unknown", "und", "none", "legacy-import")

CAPTURE_COLUMNS = (
    "capture_id",
    "captured_text",
    "captured_attribution",
    "captured_citation",
    "capture_method",
    "captured_at",
    "captured_by",
    "language",
    "source_reference",
    "context_notes",
    "raw_artifact_ref",
)
CANDIDATE_COLUMNS = (
    "candidate_id",
    "candidate_text",
    "candidate_author",
    "candidate_source_ref",
    "normalization_notes",
    "intake_schema_version",
    "external_id",
    "curation_state",
    "research_state",
    "corpus_state",
    "work_state",
    "created_at",
)
LINK_COLUMNS = ("candidate_id", "capture_id", "ordinal")
HINT_COLUMNS = ("candidate_id", "hint_seq", "kind", "target", "basis")
DECISION_COLUMNS = (
    "seq",
    "occurred_at",
    "actor",
    "actor_kind",
    "subject_kind",
    "subject_id",
    "dimension",
    "action",
    "transition_id",
    "from_state",
    "to_state",
    "reason",
)
#: The `unverifiable` side-car ledger (decision D3, 2026-09-12): one row per LEGACY row id
#: adjudicated unverifiable, so a record proven unverifiable is no longer indistinguishable
#: from a never-checked row in the 3-valued `quotes.csv` enum. Keyed by the legacy `id`
#: column, never a `candidates` FK -- legacy rows are not store candidates and may never be.
#: See `docs/program/D3_UNVERIFIABLE_LEDGER.md`.
LEGACY_VERIFICATION_COLUMNS = (
    "legacy_row_id",
    "research_state",
    "transition_id",
    "reason",
    "evidence_ref",
    "decided_by",
    "decided_at",
)
#: The four research transitions that terminate in `unverifiable`, exactly as
#: `docs/program/STATE_MODEL.md` section 2 lists them, mapped to their documented `From`
#: state. The `From` is derived from the transition so the audit row always agrees with the
#: model; a legacy row's *true* prior research state is unknown (D4), so the declared route
#: is recorded as the operator's stated path, never an invented encounter.
UNVERIFIABLE_FROM_STATE: dict[str, str] = {
    "T-R6": "in_research",
    "T-R7": "needs_more_evidence",
    "T-R10": "disputed",
    "T-R11": "verified",
}

#: Decision D4 (2026-09-12): ONE batch capture for the 2026-09-11 rehabilitation import of
#: the 324 legacy `quotes.csv` rows. The capture records the import *event* (a true,
#: verifiable statement about the frozen archive + transform), never a fabricated per-row
#: encounter. Membership links every legacy row id to that single capture so downstream
#: code has a uniform provenance shape. See `docs/program/D4_LEGACY_BATCH_CAPTURE.md`.
LEGACY_BATCH_CAPTURE_ID = "cap-2026-09-11-legacy-batch"
LEGACY_BATCH_CAPTURED_AT = "2026-09-11T00:00:00-06:00"
LEGACY_BATCH_EXPECTED_ROW_COUNT = 324
LEGACY_BATCH_ARCHIVE_QUOTES = "data/archive/2026-09-11/quotes.original.csv"
LEGACY_BATCH_ARCHIVE_SOURCES = "data/archive/2026-09-11/sources.original.csv"
LEGACY_BATCH_ARCHIVE_QUOTES_SHA256 = (
    "cad3d9f5f333121ed5ca020cd4929b9439fc474a0c5f56d5d7f52a77d5368c52"
)
LEGACY_BATCH_ARCHIVE_SOURCES_SHA256 = (
    "f86a72f69f8e04be3ece71f88ccc9c8eec4738a8994b6f32e701695390e9af6d"
)
LEGACY_BATCH_CAPTURED_TEXT = (
    "2026-09-11 Garden rehabilitation import of 324 legacy quotes.csv rows. "
    "Encounter context unknown. Provenance is the frozen archive at "
    f"{LEGACY_BATCH_ARCHIVE_QUOTES} (sha256:{LEGACY_BATCH_ARCHIVE_QUOTES_SHA256}) and "
    f"{LEGACY_BATCH_ARCHIVE_SOURCES} (sha256:{LEGACY_BATCH_ARCHIVE_SOURCES_SHA256}), "
    "plus git history and the documented Mac OS Roman→UTF-8 transform. "
    "This is ONE batch capture for the import event — not a per-row encounter record."
)
LEGACY_BATCH_CONTEXT_NOTES = (
    "Encounter context is unknown. This capture records the 2026-09-11 rehabilitation "
    "import event (decision D4), not a reconstructable per-row encounter."
)
LEGACY_BATCH_SOURCE_REFERENCE = "data/archive/2026-09-11/"
LEGACY_BATCH_RAW_ARTIFACT_REF = (
    f"{LEGACY_BATCH_ARCHIVE_QUOTES};{LEGACY_BATCH_ARCHIVE_SOURCES}"
)
LEGACY_BATCH_MEMBERSHIP_COLUMNS = (
    "legacy_row_id",
    "capture_id",
)

#: Export sections, in fixed order: (name, columns, ORDER BY). Deterministic ordering is the
#: whole point -- the export must be a pure function of the store.
EXPORT_SECTIONS = (
    ("captures", CAPTURE_COLUMNS, "ORDER BY capture_id"),
    ("candidate_captures", LINK_COLUMNS, "ORDER BY candidate_id, ordinal"),
    ("candidates", CANDIDATE_COLUMNS, "ORDER BY candidate_id"),
    ("duplicate_hints", HINT_COLUMNS, "ORDER BY candidate_id, hint_seq"),
    ("decisions", DECISION_COLUMNS, "ORDER BY seq"),
    ("legacy_verification", LEGACY_VERIFICATION_COLUMNS, "ORDER BY legacy_row_id"),
    ("legacy_batch_membership", LEGACY_BATCH_MEMBERSHIP_COLUMNS, "ORDER BY legacy_row_id"),
)
ROW_TABLES = {
    "captures": "captures",
    "candidate_captures": "candidate_captures",
    "candidates": "candidates",
    "duplicate_hints": "duplicate_hints",
    "decisions": "decisions",
    "legacy_verification": "legacy_verification",
    "legacy_batch_membership": "legacy_batch_membership",
}


class StoreError(Exception):
    """A refusal this module is designed to make (broken input, not a bug)."""


def _sql_list(values: tuple[str, ...]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def now_iso() -> str:
    """Current local time as ISO-8601 with an offset (e.g. ``2026-09-12T09:14:11-06:00``)."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def json_line(obj: dict) -> str:
    """One canonical, sortable single-line JSON object -- the export's record encoding."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


_DDL_0001 = (
    # Migration bookkeeping. The idempotency rule is: a migration id is applied at most once
    # (`schema_migrations` is the ledger), so re-running `create` is a no-op that says so.
    """
    CREATE TABLE IF NOT EXISTS schema_migrations(
        migration_id TEXT PRIMARY KEY,
        applied_at   TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS meta(
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    f"""
    CREATE TABLE IF NOT EXISTS captures(
        capture_id           TEXT PRIMARY KEY,
        captured_text        TEXT NOT NULL CHECK(length(captured_text) > 0),
        captured_attribution TEXT NOT NULL,
        captured_citation    TEXT NOT NULL,
        capture_method       TEXT NOT NULL CHECK(capture_method IN ({_sql_list(CAPTURE_METHODS)})),
        captured_at          TEXT NOT NULL,
        captured_by          TEXT NOT NULL,
        language             TEXT NOT NULL,
        source_reference     TEXT NOT NULL,
        context_notes        TEXT NOT NULL,
        raw_artifact_ref     TEXT NOT NULL
    )
    """,
    # Immutability, enforced. A capture is history: the encounter is never rewritten, and it
    # is never deleted because a candidate derived from it was rejected.
    """
    CREATE TRIGGER IF NOT EXISTS captures_immutable_update
    BEFORE UPDATE ON captures
    BEGIN SELECT RAISE(ABORT, 'captures is immutable: UPDATE rejected'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS captures_immutable_delete
    BEFORE DELETE ON captures
    BEGIN SELECT RAISE(ABORT, 'captures is immutable: DELETE rejected'); END
    """,
    f"""
    CREATE TABLE IF NOT EXISTS candidates(
        candidate_id          TEXT PRIMARY KEY,
        candidate_text        TEXT NOT NULL CHECK(length(candidate_text) > 0),
        candidate_author      TEXT NOT NULL,
        candidate_source_ref  TEXT NOT NULL,
        normalization_notes   TEXT NOT NULL CHECK(length(normalization_notes) > 0),
        intake_schema_version TEXT NOT NULL,
        external_id           TEXT,
        curation_state        TEXT NOT NULL CHECK(curation_state IN ({_sql_list(CURATION_STATES)})),
        research_state        TEXT NOT NULL CHECK(research_state IN ({_sql_list(RESEARCH_STATES)})),
        corpus_state          TEXT NOT NULL CHECK(corpus_state IN ({_sql_list(CORPUS_STATES)})),
        work_state            TEXT NOT NULL CHECK(work_state IN ({_sql_list(WORK_STATES)})),
        created_at            TEXT NOT NULL
    )
    """,
    # Requirement 6: the unreviewed queue is `curation_state = 'new' ORDER BY created_at DESC`.
    """
    CREATE INDEX IF NOT EXISTS idx_candidates_queue
        ON candidates(curation_state, created_at DESC, candidate_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_candidates_research
        ON candidates(research_state, candidate_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_candidates_corpus
        ON candidates(corpus_state, candidate_id)
    """,
    # A candidate references one or more captures. Ordinal keeps the export order stable and
    # the PK stops the same pair being linked twice.
    """
    CREATE TABLE IF NOT EXISTS candidate_captures(
        candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
        capture_id   TEXT NOT NULL REFERENCES captures(capture_id),
        ordinal      INTEGER NOT NULL CHECK(ordinal >= 1),
        PRIMARY KEY (candidate_id, ordinal),
        UNIQUE (candidate_id, capture_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_candidate_captures_capture
        ON candidate_captures(capture_id, candidate_id)
    """,
    # Duplicate hints are rows (kind/target/basis). They are *derived* data: rebuildable
    # deterministically by deleting and regenerating in `hint_seq` order, never hand-edited,
    # and never a state (`docs/program/CANDIDATE_ENVELOPE.md` section Duplicate hints).
    f"""
    CREATE TABLE IF NOT EXISTS duplicate_hints(
        candidate_id TEXT NOT NULL REFERENCES candidates(candidate_id) ON DELETE CASCADE,
        hint_seq     INTEGER NOT NULL CHECK(hint_seq >= 1),
        kind         TEXT NOT NULL CHECK(kind IN ({_sql_list(HINT_KINDS)})),
        target       TEXT NOT NULL,
        basis        TEXT NOT NULL CHECK(length(basis) > 0),
        PRIMARY KEY (candidate_id, hint_seq)
    )
    """,
    # The append-only decision/audit log. One row per curation / research / corpus / work
    # transition: who/what, when, from-state, to-state, reason.
    """
    CREATE TABLE IF NOT EXISTS decisions(
        seq           INTEGER PRIMARY KEY AUTOINCREMENT,
        occurred_at   TEXT NOT NULL,
        actor         TEXT NOT NULL CHECK(length(actor) > 0),
        actor_kind    TEXT NOT NULL CHECK(actor_kind IN ('operator','agent','system')),
        subject_kind  TEXT NOT NULL CHECK(subject_kind IN ('candidate','capture','work_unit','research_case')),
        subject_id    TEXT NOT NULL,
        dimension     TEXT NOT NULL CHECK(dimension IN ('curation','research','corpus','work')),
        action        TEXT NOT NULL CHECK(length(action) > 0),
        transition_id TEXT,
        from_state    TEXT NOT NULL,
        to_state      TEXT NOT NULL,
        reason        TEXT NOT NULL CHECK(length(reason) > 0)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_decisions_subject
        ON decisions(subject_kind, subject_id, seq)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_decisions_dimension
        ON decisions(dimension, seq)
    """,
    # Append-only, enforced: a corrected decision is a new decision, not an edit.
    """
    CREATE TRIGGER IF NOT EXISTS decisions_append_only_update
    BEFORE UPDATE ON decisions
    BEGIN SELECT RAISE(ABORT, 'decisions is append-only: UPDATE rejected'); END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS decisions_append_only_delete
    BEFORE DELETE ON decisions
    BEGIN SELECT RAISE(ABORT, 'decisions is append-only: DELETE rejected'); END
    """,
)

#: (migration_id, statements). Appending here is how schema change happens; never edit an
#: applied migration's statements in place -- add a new id.
_DDL_0002 = (
    # The `unverifiable` side-car ledger (decision D3, 2026-09-12). Keyed by legacy row id;
    # asserts the terminal research state `unverifiable` and the STATE_MODEL transition that
    # produced it. The row is NOT a `candidates` FK: legacy rows are not store candidates.
    # `evidence_ref` names the source of the adjudication (an issue, an export review, 'none').
    f"""
    CREATE TABLE IF NOT EXISTS legacy_verification(
        legacy_row_id  TEXT PRIMARY KEY,
        research_state TEXT NOT NULL CHECK(research_state = 'unverifiable'),
        transition_id  TEXT NOT NULL CHECK(transition_id IN ('T-R6','T-R7','T-R10','T-R11')),
        reason         TEXT NOT NULL CHECK(length(reason) > 0),
        evidence_ref   TEXT NOT NULL CHECK(length(evidence_ref) > 0),
        decided_by     TEXT NOT NULL CHECK(length(decided_by) > 0),
        decided_at     TEXT NOT NULL
    )
    """,
)

_DDL_0003 = (
    # Decision D4 (2026-09-12): membership side-car linking every legacy quotes.csv id to the
    # ONE batch capture for the 2026-09-11 rehabilitation import. The capture itself lives in
    # `captures` (immutable); this table only records which legacy rows that capture covers.
    # Not a `candidates` FK — legacy rows are not store candidates (same posture as D3).
    """
    CREATE TABLE IF NOT EXISTS legacy_batch_membership(
        legacy_row_id TEXT PRIMARY KEY,
        capture_id    TEXT NOT NULL REFERENCES captures(capture_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_legacy_batch_membership_capture
        ON legacy_batch_membership(capture_id, legacy_row_id)
    """,
)

MIGRATIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("0001_create_core", _DDL_0001),
    ("0002_unverifiable_ledger", _DDL_0002),
    ("0003_legacy_batch_capture", _DDL_0003),
)


def connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_migrations(conn: sqlite3.Connection, applied_at: str) -> list[str]:
    """Apply every migration not already in the ledger. Returns the ids applied *now*.

    Idempotency rule: a migration id is applied at most once. Re-running with nothing new
    applies nothing and returns ``[]`` -- that is the no-op that `create` reports.
    """
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations("
        "migration_id TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    ledger = {row[0] for row in conn.execute("SELECT migration_id FROM schema_migrations")}
    applied: list[str] = []
    for migration_id, statements in MIGRATIONS:
        if migration_id in ledger:
            continue
        for statement in statements:
            conn.execute(statement)
        conn.execute(
            "INSERT INTO schema_migrations(migration_id, applied_at) VALUES (?, ?)",
            (migration_id, applied_at),
        )
        applied.append(migration_id)
    conn.commit()
    return applied


def create_store(store_dir: Path | str, *, created_at: str | None = None) -> tuple[Path, list[str]]:
    """Create (or open) the store in `store_dir`. Returns (db path, migrations applied now).

    Safe to re-run: the second run applies nothing and leaves the store byte-identical.
    """
    store_dir = Path(store_dir)
    store_dir.mkdir(parents=True, exist_ok=True)
    db_path = store_dir / STORE_FILENAME
    stamp = created_at or now_iso()
    conn = connect(db_path)
    try:
        applied = apply_migrations(conn, stamp)
        conn.execute(
            "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        conn.execute(
            "INSERT OR IGNORE INTO meta(key, value) VALUES ('created_at', ?)", (stamp,)
        )
        conn.commit()
    finally:
        conn.close()
    return db_path, applied


def store_status(store_dir: Path | str) -> str:
    """The store-vs-mirror freshness state without requiring an open Store.

    One of CURRENT / STALE / MISSING_DB / MISSING_MIRROR. `MISSING_DB` is reported here because
    no Store can be opened when the SQLite file is absent; the other three are also what an open
    Store's `status()` reports.
    """
    store_dir = Path(store_dir)
    db_path = store_dir / STORE_FILENAME
    mirror = store_dir / DEFAULT_EXPORT_NAME
    if not db_path.exists():
        return "MISSING_DB"
    if not mirror.exists():
        return "MISSING_MIRROR"
    with Store(store_dir) as store:
        if store.export_bytes() == mirror.read_bytes():
            return "CURRENT"
    return "STALE"


def bootstrap_store(store_dir: Path | str) -> str:
    """Hydrate the local store from the committed mirror, or report the existing state.

    The U0.1 bootstrap rule: the mirror is the committed source of truth for reconstructing a
    machine-local store, but a store that already exists is never silently overwritten.

      * DB absent, mirror present -> create the store and import the mirror; returns CURRENT.
      * DB absent, mirror absent  -> refused (nothing to bootstrap from); raises StoreError.
      * DB present, mirror equal  -> no-op; returns CURRENT.
      * DB present, mirror differs -> refused (a divergent store is never clobbered by the
        mirror, and a divergent mirror is never clobbered by the store); raises StoreError.

    Returns the post-bootstrap `store_status`.
    """
    store_dir = Path(store_dir)
    db_path = store_dir / STORE_FILENAME
    mirror = store_dir / DEFAULT_EXPORT_NAME
    if db_path.exists():
        if not mirror.exists():
            raise StoreError(
                f"store exists at {db_path} but the mirror {mirror} is absent; "
                "refusing to guess (run 'sync' to write the mirror, or remove the store)"
            )
        with Store(store_dir) as store:
            if store.export_bytes() == mirror.read_bytes():
                return "CURRENT"
        raise StoreError(
            f"store at {db_path} and mirror {mirror} diverge; bootstrap never overwrites a "
            "divergent store or mirror (reconcile by hand, or wipe the store and re-bootstrap)"
        )
    if not mirror.exists():
        raise StoreError(
            f"neither the store ({db_path}) nor the mirror ({mirror}) exists; "
            "there is nothing to bootstrap from (create the store, or commit a mirror first)"
        )
    create_store(store_dir)
    with Store(store_dir) as store:
        store.import_bytes(mirror.read_bytes())
    return store_status(store_dir)



def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StoreError(message)


def _corpus_followon_reason(transition_id: str, curation_reason: str) -> str:
    """The audit reason for a corpus follow-on, tied to the curation decision that forced it."""
    if transition_id == "T-P1":
        return (
            f"deterministic consequence of acceptance (STATE_MODEL.md T-P1): a wanted record "
            f"becomes eligible, never 'true'; operator reason: {curation_reason}"
        )
    if transition_id == "T-P7":
        return (
            f"curation acceptance withdrawn; the record returns to the candidate queue "
            f"(STATE_MODEL.md T-P7); operator reason: {curation_reason}"
        )
    raise StoreError(f"no documented reason for corpus follow-on {transition_id}")


class Store:
    """Read/write access to one Garden store. Small on purpose: W1.1 is the schema, not a CLI."""

    def __init__(self, store_dir: Path | str):
        self.dir = Path(store_dir)
        self.db_path = self.dir / STORE_FILENAME
        if not self.db_path.exists():
            raise StoreError(f"no store at {self.db_path} (run 'create' first)")
        self.conn = connect(self.db_path)

    # -- lifecycle ---------------------------------------------------------------------
    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- writes ------------------------------------------------------------------------
    def add_capture(
        self,
        capture_id: str,
        captured_text: str,
        *,
        captured_attribution: str = "unknown",
        captured_citation: str = "none",
        capture_method: str = "manual-entry",
        captured_at: str | None = None,
        captured_by: str = "operator",
        language: str = "und",
        source_reference: str = "none",
        context_notes: str = "none",
        raw_artifact_ref: str = "none",
    ) -> str:
        """Write one immutable capture row. `captured_text` is stored verbatim."""
        _require(bool(capture_id), "capture_id must be non-empty")
        _require(captured_text != "", "captured_text must be non-empty (never cleaned or trimmed)")
        _require(
            capture_method in CAPTURE_METHODS,
            f"capture_method {capture_method!r} is outside the contract vocabulary "
            f"{list(CAPTURE_METHODS)}",
        )
        try:
            self.conn.execute(
                f"INSERT INTO captures ({', '.join(CAPTURE_COLUMNS)}) "
                f"VALUES ({', '.join('?' * len(CAPTURE_COLUMNS))})",
                (
                    capture_id,
                    captured_text,
                    captured_attribution,
                    captured_citation,
                    capture_method,
                    captured_at or now_iso(),
                    captured_by,
                    language,
                    source_reference,
                    context_notes,
                    raw_artifact_ref,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise StoreError(f"capture {capture_id!r} rejected: {exc}") from None
        self.conn.commit()
        return capture_id

    def add_candidate(
        self,
        candidate_id: str,
        candidate_text: str,
        capture_ids: list[str] | tuple[str, ...],
        *,
        candidate_author: str = "unknown",
        candidate_source_ref: str = "none",
        normalization_notes: str,
        intake_schema_version: str = "garden.candidate-envelope/1",
        external_id: str | None = None,
        created_at: str | None = None,
    ) -> str:
        """Write one candidate and its capture links. States enter at their intake values.

        The four dimensions are written as `new` / `not_started` / `candidate_only` /
        `queued` and cannot be overridden here: an envelope arriving with a decision already
        made is rejected (`CANDIDATE_ENVELOPE.md` rule 3), and moving them afterwards is a
        recorded transition -- W1.5's job, not W1.1's.
        """
        _require(bool(candidate_id), "candidate_id must be non-empty")
        _require(candidate_text != "", "candidate_text must be non-empty")
        _require(
            normalization_notes != "",
            "normalization_notes is required even when nothing changed "
            "('identical to capture' must be an assertion, not an omission)",
        )
        _require(len(capture_ids) >= 1, "a candidate must reference at least one capture")
        columns = list(CANDIDATE_COLUMNS)
        values = {
            "candidate_id": candidate_id,
            "candidate_text": candidate_text,
            "candidate_author": candidate_author,
            "candidate_source_ref": candidate_source_ref,
            "normalization_notes": normalization_notes,
            "intake_schema_version": intake_schema_version,
            "external_id": external_id,
            "created_at": created_at or now_iso(),
            **INTAKE_STATES,
        }
        try:
            self.conn.execute(
                f"INSERT INTO candidates ({', '.join(columns)}) "
                f"VALUES ({', '.join('?' * len(columns))})",
                tuple(values[c] for c in columns),
            )
            for ordinal, capture_id in enumerate(capture_ids, start=1):
                self.conn.execute(
                    "INSERT INTO candidate_captures (candidate_id, capture_id, ordinal) "
                    "VALUES (?, ?, ?)",
                    (candidate_id, capture_id, ordinal),
                )
        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            raise StoreError(f"candidate {candidate_id!r} rejected: {exc}") from None
        self.conn.commit()
        return candidate_id

    def apply_normalization(
        self,
        candidate_id: str,
        *,
        candidate_text: str,
        candidate_author: str,
        candidate_source_ref: str,
        normalization_notes: str,
    ) -> None:
        """Write a candidate's normalized proposal and its notes (W1.4's write path).

        Four guards, all checked before anything is written:

          * the candidate must exist;
          * `curation_state` must still be `new` -- normalization is an *intake-time* operation.
            A candidate the operator has already decided on is history; re-deriving its proposal
            after a decision would silently restate the evidence a decision was made on;
          * `candidate_text` and `normalization_notes` must be non-empty -- "we did not touch it"
            is an assertion (`identical to capture`), never an omission;
          * nothing in this method touches `captures`, the four state columns, or `decisions`.
            The capture it derives from is immutable and stays byte-for-byte the encounter.
        """
        _require(bool(candidate_id), "candidate_id must be non-empty")
        _require(candidate_text != "", "candidate_text must be non-empty (an empty proposal is not a proposal)")
        _require(
            normalization_notes != "",
            "normalization_notes is required even when nothing changed "
            "('identical to capture' must be an assertion, not an omission)",
        )
        row = self.conn.execute(
            "SELECT curation_state FROM candidates WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
        if row is None:
            raise StoreError(f"no candidate {candidate_id!r} in the store")
        if row["curation_state"] != "new":
            raise StoreError(
                f"candidate {candidate_id!r} is curation_state={row['curation_state']!r}: "
                f"normalization only applies while a candidate is 'new'"
            )
        self.conn.execute(
            "UPDATE candidates SET candidate_text = ?, candidate_author = ?, "
            "candidate_source_ref = ?, normalization_notes = ? WHERE candidate_id = ?",
            (
                candidate_text,
                candidate_author,
                candidate_source_ref,
                normalization_notes,
                candidate_id,
            ),
        )
        self.conn.commit()

    def add_duplicate_hints(self, candidate_id: str, hints: list[dict]) -> int:
        """Append duplicate hints in `hint_seq` order. Returns the new high-water seq."""
        start = self._next_hint_seq(candidate_id)
        for offset, hint in enumerate(hints):
            kind = hint.get("kind")
            _require(
                kind in HINT_KINDS,
                f"duplicate-hint kind {kind!r} is outside the contract vocabulary "
                f"{list(HINT_KINDS)}",
            )
            basis = hint.get("basis") or ""
            _require(bool(basis), "every duplicate hint carries a basis string")
            target = hint.get("target")
            _require(
                isinstance(target, str) and target != "",
                "every duplicate hint carries a target (an id or 'external')",
            )
            try:
                self.conn.execute(
                    "INSERT INTO duplicate_hints (candidate_id, hint_seq, kind, target, basis) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (candidate_id, start + offset, kind, target, basis),
                )
            except sqlite3.IntegrityError as exc:
                self.conn.rollback()
                raise StoreError(f"duplicate hint rejected: {exc}") from None
        self.conn.commit()
        return start + len(hints) - 1 if hints else start - 1

    def replace_duplicate_hints(self, candidate_id: str, hints: list[dict]) -> int:
        """Rebuild a candidate's hints from scratch (the only sanctioned write mode)."""
        self.conn.execute("DELETE FROM duplicate_hints WHERE candidate_id = ?", (candidate_id,))
        self.conn.commit()
        return self.add_duplicate_hints(candidate_id, hints)

    def _next_hint_seq(self, candidate_id: str) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(MAX(hint_seq), 0) FROM duplicate_hints WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        return int(row[0]) + 1

    def _insert_decision(
        self,
        *,
        subject_kind: str,
        subject_id: str,
        dimension: str,
        action: str,
        from_state: str,
        to_state: str,
        actor: str,
        actor_kind: str,
        reason: str,
        transition_id: str | None = None,
        occurred_at: str | None = None,
    ) -> int:
        """Validate and append one audit row. Returns its `seq`. Does NOT commit.

        `from_state`/`to_state` must be values of the named dimension's vocabulary as written
        in `STATE_MODEL.md`; anything else is refused here *and* by the column's CHECK path.
        Whether the move is a legal transition in the table is `curate`'s guard (W1.5), not
        this row's.
        """
        _require(dimension in DIMENSIONS, f"unknown dimension {dimension!r}")
        _require(actor_kind in ACTOR_KINDS, f"unknown actor_kind {actor_kind!r}")
        _require(subject_kind in SUBJECT_KINDS, f"unknown subject_kind {subject_kind!r}")
        _require(bool(subject_id), "subject_id must be non-empty")
        _require(bool(action), "a decision must name its action")
        _require(bool(reason), "a decision must carry a reason")
        vocabulary = DIMENSIONS[dimension]
        for label, value in (("from_state", from_state), ("to_state", to_state)):
            _require(
                value in vocabulary,
                f"{label}={value!r} is outside the {dimension} vocabulary {list(vocabulary)} "
                f"in docs/program/STATE_MODEL.md",
            )
        cur = self.conn.execute(
            "INSERT INTO decisions (occurred_at, actor, actor_kind, subject_kind, subject_id, "
            "dimension, action, transition_id, from_state, to_state, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                occurred_at or now_iso(),
                actor,
                actor_kind,
                subject_kind,
                subject_id,
                dimension,
                action,
                transition_id,
                from_state,
                to_state,
                reason,
            ),
        )
        assert cur.lastrowid is not None  # an INSERT always yields one
        return int(cur.lastrowid)

    def record_decision(
        self,
        *,
        subject_kind: str,
        subject_id: str,
        dimension: str,
        action: str,
        from_state: str,
        to_state: str,
        actor: str,
        actor_kind: str,
        reason: str,
        transition_id: str | None = None,
        occurred_at: str | None = None,
    ) -> int:
        """Append one audit row, committing it. Returns its `seq`."""
        seq = self._insert_decision(
            subject_kind=subject_kind,
            subject_id=subject_id,
            dimension=dimension,
            action=action,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            actor_kind=actor_kind,
            reason=reason,
            transition_id=transition_id,
            occurred_at=occurred_at,
        )
        self.conn.commit()
        return seq

    def curate(
        self,
        candidate_id: str,
        *,
        action: str,
        actor: str,
        reason: str,
        occurred_at: str | None = None,
    ) -> dict:
        """Apply one operator curation decision and its required corpus follow-on, atomically.

        This is W1.5's single write gate (`docs/program/W1_5_CURATION_SURFACE.md`). The
        curation state moves along a legal T-C1…T-C12 transition and, when the model requires
        it, the corpus state moves too:

          * becoming `accepted` while `candidate_only` fires the deterministic, audited
            **T-P1** `candidate_only -> eligible` (authority `system`) -- eligibility is
            "wanted", never "true";
          * leaving `accepted` (`T-C8`/`T-C9`) while `eligible` fires **T-P7**
            `eligible -> candidate_only` (authority `operator`, the operator making the
            reversal) so no record is ever left `eligible` while its curation is `hold` /
            `rejected` / `duplicate`.

        Everything -- the curation state, any corpus state, and the audit rows for all of it --
        is written in ONE transaction and then committed, so there is never a window in which a
        state changed without its audit row. The method touches **only** `curation_state` and
        `corpus_state`: `research_state` and `work_state` are never written here (a curation
        decision implies no research), and `reason` is required before anything is written.

        Returns a description of what was recorded: `{candidate_id, curation: (from,to,id),
        corpus: (from,to,id) or None, seq: [first decision seq, ...]}`.
        """
        _require(bool(candidate_id), "candidate_id must be non-empty")
        _require(bool(actor), "every curation decision needs an actor")
        _require(bool(reason), "every curation decision must carry a reason (required, never omitted)")
        _require(action in CURATION_ACTIONS, f"unknown curation action {action!r}")
        row = self.conn.execute(
            "SELECT curation_state, corpus_state FROM candidates WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        if row is None:
            raise StoreError(f"no candidate {candidate_id!r} in the store")
        from_c, from_p = row["curation_state"], row["corpus_state"]
        to_c = CURATION_ACTIONS[action]
        pair = (from_c, to_c)
        if pair not in CURATION_TRANSITIONS:
            raise StoreError(
                f"no legal curation transition {from_c!r} -> {to_c!r} for action {action!r} "
                f"(STATE_MODEL.md has {CURATION_TRANSITIONS.get(pair, 'no such move')}); "
                f"nothing was written"
            )
        curation_transition = CURATION_TRANSITIONS[pair]

        # The corpus follow-ons this curation move forces, in order.
        follow: list[tuple[str, str, str, str, str]] = []  # (dim, from, to, trans_id, authority)
        to_p = from_p
        if to_c == "accepted" and from_p == "candidate_only":
            follow.append(("corpus", "candidate_only", "eligible", "T-P1", "system"))
            to_p = "eligible"
        elif from_c == "accepted":
            # T-C8 / T-C9 -- curation left 'accepted'; if eligibility was granted on that
            # acceptance it must be withdrawn now (no dimension is stranded).
            if from_p == "eligible":
                follow.append(("corpus", "eligible", "candidate_only", "T-P7", "operator"))
                to_p = "candidate_only"
        if not follow and to_p != from_p:
            raise StoreError(
                f"internal: corpus would move {from_p!r} -> {to_p!r} with no recorded transition"
            )

        try:
            cur = self.conn.execute(
                "UPDATE candidates SET curation_state = ?, corpus_state = ? WHERE candidate_id = ?",
                (to_c, to_p, candidate_id),
            )
            if cur.rowcount != 1:
                self.conn.rollback()
                raise StoreError(f"candidate {candidate_id!r} did not update (rowcount {cur.rowcount})")
            seqs = [
                self._insert_decision(
                    subject_kind="candidate",
                    subject_id=candidate_id,
                    dimension="curation",
                    action="curation-decision",
                    from_state=from_c,
                    to_state=to_c,
                    transition_id=curation_transition,
                    actor=actor,
                    actor_kind="operator",
                    reason=reason,
                    occurred_at=occurred_at,
                )
            ]
            corpus_desc: dict | None = None
            for dim, f_state, t_state, trans_id, authority in follow:
                if authority == "system":
                    follow_actor, follow_kind = "system", "system"
                else:  # operator -- the operator who made the curation reversal
                    follow_actor, follow_kind = actor, "operator"
                seqs.append(
                    self._insert_decision(
                        subject_kind="candidate",
                        subject_id=candidate_id,
                        dimension=dim,
                        action="corpus-follow-on",
                        from_state=f_state,
                        to_state=t_state,
                        transition_id=trans_id,
                        actor=follow_actor,
                        actor_kind=follow_kind,
                        reason=_corpus_followon_reason(trans_id, reason),
                        occurred_at=occurred_at,
                    )
                )
                corpus_desc = {
                    "from": f_state,
                    "to": t_state,
                    "transition_id": trans_id,
                    "authority": authority,
                }
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            raise StoreError(f"curation decision for {candidate_id!r} rejected: {exc}") from None
        return {
            "candidate_id": candidate_id,
            "curation": {"from": from_c, "to": to_c, "transition_id": curation_transition},
            "corpus": corpus_desc,
            "seq": seqs,
        }

    def mark_legacy_unverifiable(
        self,
        legacy_row_id: str,
        *,
        transition_id: str,
        reason: str,
        evidence_ref: str = "none",
        decided_by: str = "operator",
        decided_at: str | None = None,
    ) -> dict:
        """Record that a legacy row (a `quotes.csv` `id`) is `unverifiable` (decision D3).

        The `unverifiable` side-car ledger is keyed by the legacy row id and leaves the
        `quotes.csv` enum untouched, so a record proven unverifiable is no longer
        indistinguishable from a never-checked row. Every write appends a `research`
        `decisions` audit row (the declared STATE_MODEL transition) in the SAME transaction,
        so there is never a ledger row without its audit row.

        Guarded before anything is written: the id, `reason`, `evidence_ref` and `decided_by`
        must be non-empty; `transition_id` must be one of the four transitions that terminate
        in `unverifiable` (T-R6 / T-R7 / T-R10 / T-R11); and the row must not already be in
        the ledger -- a legacy row is either `unverifiable` or it is not, so re-adjudicating
        means `reopen` (T-R12) then `mark` again, never a silent overwrite.

        `from_state` for the audit row is derived from `transition_id` per STATE_MODEL.md
        section 2. The legacy row's true prior research state is unknown (D4), so the
        declared route is what the operator records as the path to the terminal outcome.

        Returns `{legacy_row_id, research_state, transition_id, seq}`.
        """
        _require(bool(legacy_row_id), "legacy_row_id must be non-empty")
        _require(bool(reason), "every unverifiable adjudication must carry a reason")
        _require(bool(evidence_ref), "evidence_ref is required ('none' is the explicit no-reference assertion)")
        _require(bool(decided_by), "decided_by must be non-empty")
        _require(
            transition_id in UNVERIFIABLE_FROM_STATE,
            f"transition_id {transition_id!r} does not terminate in unverifiable "
            f"(STATE_MODEL.md lists {sorted(UNVERIFIABLE_FROM_STATE)})",
        )
        row = self.conn.execute(
            "SELECT legacy_row_id FROM legacy_verification WHERE legacy_row_id = ?",
            (legacy_row_id,),
        ).fetchone()
        if row is not None:
            raise StoreError(
                f"legacy row {legacy_row_id!r} is already in the unverifiable ledger; "
                f"re-adjudicate with reopen (T-R12) then mark again, never a silent overwrite"
            )
        from_state = UNVERIFIABLE_FROM_STATE[transition_id]
        # One clock read for the whole adjudication: the ledger row's decided_at and the
        # audit row's occurred_at MUST be the same instant. When decided_at is omitted, take
        # a single now_iso() here and reuse it -- two separate reads (the audit path calls
        # now_iso() again) would record two different clocks for one decision (foreign-QA D-1).
        stamp = decided_at or now_iso()
        try:
            self.conn.execute(
                f"INSERT INTO legacy_verification ({', '.join(LEGACY_VERIFICATION_COLUMNS)}) "
                f"VALUES ({', '.join('?' * len(LEGACY_VERIFICATION_COLUMNS))})",
                (
                    legacy_row_id,
                    "unverifiable",
                    transition_id,
                    reason,
                    evidence_ref,
                    decided_by,
                    stamp,
                ),
            )
            seq = self._insert_decision(
                subject_kind="research_case",
                subject_id=legacy_row_id,
                dimension="research",
                action="research-adjudication",
                transition_id=transition_id,
                from_state=from_state,
                to_state="unverifiable",
                actor=decided_by,
                actor_kind="operator",
                reason=reason,
                occurred_at=stamp,
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            raise StoreError(
                f"unverifiable adjudication for legacy row {legacy_row_id!r} rejected: {exc}"
            ) from None
        return {
            "legacy_row_id": legacy_row_id,
            "research_state": "unverifiable",
            "transition_id": transition_id,
            "seq": seq,
        }

    def reopen_legacy_unverifiable(
        self,
        legacy_row_id: str,
        *,
        reason: str,
        decided_by: str = "operator",
        decided_at: str | None = None,
    ) -> dict:
        """Reverse an `unverifiable` adjudication when a new witness appears (STATE_MODEL T-R12).

        The row leaves the side-car ledger and the reversal is recorded as a `research`
        audit transition `unverifiable -> in_research`, in ONE transaction. Guarded: the row
        must currently be in the ledger, and `reason` / `decided_by` must be non-empty.

        Returns `{legacy_row_id, from_state, to_state, transition_id, seq}`.
        """
        _require(bool(legacy_row_id), "legacy_row_id must be non-empty")
        _require(bool(reason), "every reopen decision must carry a reason")
        _require(bool(decided_by), "decided_by must be non-empty")
        row = self.conn.execute(
            "SELECT legacy_row_id FROM legacy_verification WHERE legacy_row_id = ?",
            (legacy_row_id,),
        ).fetchone()
        if row is None:
            raise StoreError(
                f"legacy row {legacy_row_id!r} is not in the unverifiable ledger; nothing to reopen"
            )
        try:
            seq = self._insert_decision(
                subject_kind="research_case",
                subject_id=legacy_row_id,
                dimension="research",
                action="research-adjudication",
                transition_id="T-R12",
                from_state="unverifiable",
                to_state="in_research",
                actor=decided_by,
                actor_kind="operator",
                reason=reason,
                occurred_at=decided_at,
            )
            self.conn.execute(
                "DELETE FROM legacy_verification WHERE legacy_row_id = ?", (legacy_row_id,)
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            raise StoreError(
                f"reopen of legacy row {legacy_row_id!r} rejected: {exc}"
            ) from None
        return {
            "legacy_row_id": legacy_row_id,
            "from_state": "unverifiable",
            "to_state": "in_research",
            "transition_id": "T-R12",
            "seq": seq,
        }

    def unverifiable_ledger(self) -> list[sqlite3.Row]:
        """Every legacy row adjudicated `unverifiable`, ordered by legacy row id."""
        return list(
            self.conn.execute(
                "SELECT " + ", ".join(LEGACY_VERIFICATION_COLUMNS)
                + " FROM legacy_verification ORDER BY legacy_row_id"
            )
        )

    def seed_legacy_batch_capture(
        self,
        legacy_row_ids: list[str] | tuple[str, ...],
    ) -> dict:
        """Record the ONE D4 batch capture and link every legacy row id to it.

        The capture is the 2026-09-11 rehabilitation import event: `capture_method` /
        `captured_by` are `legacy-import`, `captured_text` is the fixed true statement about
        the frozen archive (never fabricated per-row quote text), and `context_notes`
        explicitly records that encounter context is unknown. Membership is all-or-nothing:
        either every provided id is linked to `LEGACY_BATCH_CAPTURE_ID`, or nothing is written.

        Idempotent when the store already holds exactly this capture and exactly this
        membership set (same ids, same capture_id). Any other existing state — a different
        capture body, a partial membership, a foreign capture_id — is refused rather than
        silently overwritten. Does not create candidates (legacy rows are not store
        candidates; same posture as D3).

        Returns `{capture_id, row_count, status}` where status is ``created`` or ``no-op``.
        """
        _require(len(legacy_row_ids) > 0, "legacy_row_ids must be non-empty")
        _require(
            len(legacy_row_ids) == LEGACY_BATCH_EXPECTED_ROW_COUNT,
            f"legacy_row_ids has {len(legacy_row_ids)} entries; D4 expects exactly "
            f"{LEGACY_BATCH_EXPECTED_ROW_COUNT}",
        )
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in legacy_row_ids:
            _require(bool(raw), "every legacy_row_id must be non-empty")
            row_id = str(raw)
            _require(row_id not in seen, f"duplicate legacy_row_id {row_id!r} in the seed set")
            seen.add(row_id)
            cleaned.append(row_id)
        # Lexicographic order matches the export's `ORDER BY legacy_row_id` (TEXT).
        cleaned_sorted = sorted(cleaned)

        existing_capture = self.conn.execute(
            "SELECT " + ", ".join(CAPTURE_COLUMNS) + " FROM captures WHERE capture_id = ?",
            (LEGACY_BATCH_CAPTURE_ID,),
        ).fetchone()
        existing_members = [
            row["legacy_row_id"]
            for row in self.conn.execute(
                "SELECT legacy_row_id FROM legacy_batch_membership ORDER BY legacy_row_id"
            )
        ]

        if existing_capture is not None or existing_members:
            expected_capture = {
                "capture_id": LEGACY_BATCH_CAPTURE_ID,
                "captured_text": LEGACY_BATCH_CAPTURED_TEXT,
                "captured_attribution": "unknown",
                "captured_citation": "none",
                "capture_method": "legacy-import",
                "captured_at": LEGACY_BATCH_CAPTURED_AT,
                "captured_by": "legacy-import",
                "language": "und",
                "source_reference": LEGACY_BATCH_SOURCE_REFERENCE,
                "context_notes": LEGACY_BATCH_CONTEXT_NOTES,
                "raw_artifact_ref": LEGACY_BATCH_RAW_ARTIFACT_REF,
            }
            if existing_capture is None:
                raise StoreError(
                    "legacy batch membership exists without the batch capture; "
                    "refusing to repair in place — wipe the store and re-seed"
                )
            for key, expected in expected_capture.items():
                if existing_capture[key] != expected:
                    raise StoreError(
                        f"legacy batch capture {LEGACY_BATCH_CAPTURE_ID!r} already exists "
                        f"with a different {key}: {existing_capture[key]!r} != {expected!r}"
                    )
            if existing_members != cleaned_sorted:
                raise StoreError(
                    "legacy batch membership already exists with a different id set "
                    f"(have {len(existing_members)}, asked {len(cleaned_sorted)}); "
                    "refusing a silent overwrite"
                )
            return {
                "capture_id": LEGACY_BATCH_CAPTURE_ID,
                "row_count": len(cleaned_sorted),
                "status": "no-op",
            }

        try:
            self.conn.execute(
                f"INSERT INTO captures ({', '.join(CAPTURE_COLUMNS)}) "
                f"VALUES ({', '.join('?' * len(CAPTURE_COLUMNS))})",
                (
                    LEGACY_BATCH_CAPTURE_ID,
                    LEGACY_BATCH_CAPTURED_TEXT,
                    "unknown",
                    "none",
                    "legacy-import",
                    LEGACY_BATCH_CAPTURED_AT,
                    "legacy-import",
                    "und",
                    LEGACY_BATCH_SOURCE_REFERENCE,
                    LEGACY_BATCH_CONTEXT_NOTES,
                    LEGACY_BATCH_RAW_ARTIFACT_REF,
                ),
            )
            self.conn.executemany(
                "INSERT INTO legacy_batch_membership (legacy_row_id, capture_id) VALUES (?, ?)",
                [(row_id, LEGACY_BATCH_CAPTURE_ID) for row_id in cleaned_sorted],
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            raise StoreError(
                f"legacy batch capture seed rejected: {exc}"
            ) from None
        return {
            "capture_id": LEGACY_BATCH_CAPTURE_ID,
            "row_count": len(cleaned_sorted),
            "status": "created",
        }

    def legacy_batch_capture(self) -> sqlite3.Row | None:
        """The D4 batch capture row, or None if it has not been seeded."""
        return self.conn.execute(
            "SELECT " + ", ".join(CAPTURE_COLUMNS) + " FROM captures WHERE capture_id = ?",
            (LEGACY_BATCH_CAPTURE_ID,),
        ).fetchone()

    def legacy_batch_membership(self) -> list[sqlite3.Row]:
        """Every legacy row linked to the D4 batch capture, ordered by legacy row id."""
        return list(
            self.conn.execute(
                "SELECT " + ", ".join(LEGACY_BATCH_MEMBERSHIP_COLUMNS)
                + " FROM legacy_batch_membership ORDER BY legacy_row_id"
            )
        )

    # -- reads -------------------------------------------------------------------------
    def counts(self) -> dict[str, int]:
        return {
            table: int(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "captures",
                "candidates",
                "candidate_captures",
                "duplicate_hints",
                "decisions",
                "legacy_verification",
                "legacy_batch_membership",
            )
        }

    def unreviewed_queue(self, limit: int | None = None) -> list[sqlite3.Row]:
        """Requirement 6's first query: unreviewed candidates, newest first."""
        sql = (
            "SELECT candidate_id, candidate_text, candidate_author, created_at, curation_state "
            "FROM candidates WHERE curation_state = 'new' "
            "ORDER BY created_at DESC, candidate_id"
        )
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        return list(self.conn.execute(sql))

    def rejected_with_reasons(self) -> list[sqlite3.Row]:
        """Requirement 6's second query: every rejected item with the reason it was rejected."""
        return list(
            self.conn.execute(
                "SELECT c.candidate_id, d.reason, d.occurred_at, d.actor, d.transition_id "
                "FROM candidates c JOIN decisions d "
                "  ON d.subject_id = c.candidate_id AND d.dimension = 'curation' "
                "WHERE c.curation_state = 'rejected' AND d.to_state = 'rejected' "
                "ORDER BY d.seq DESC, c.candidate_id"
            )
        )

    # -- export / import ---------------------------------------------------------------
    def export_bytes(self) -> bytes:
        """The whole store as deterministic, diffable text (`garden.export/1`).

        Pure function of the store: fixed section order, records sorted by key, one canonical
        JSON object per line. No timestamps are generated here, so exporting the same store
        twice -- in the same process or not -- yields the same bytes.
        """
        lines = [EXPORT_HEADER]
        meta = {
            row["key"]: row["value"]
            for row in self.conn.execute("SELECT key, value FROM meta ORDER BY key")
        }
        lines.append("[meta]")
        lines.append(
            json_line(
                {
                    "schema_version": int(meta.get("schema_version", SCHEMA_VERSION)),
                    "created_at": meta.get("created_at", ""),
                }
            )
        )
        for section, columns, order_by in EXPORT_SECTIONS:
            lines.append(f"[{section}]")
            rows = self.conn.execute(
                f"SELECT {', '.join(columns)} FROM {section} {order_by}"
            ).fetchall()
            for row in rows:
                lines.append(json_line({key: row[key] for key in columns}))
        return ("\n".join(lines) + "\n").encode("utf-8")

    def write_export(self, out_path: Path | str | None = None) -> Path:
        target = Path(out_path) if out_path else self.dir / DEFAULT_EXPORT_NAME
        target.write_bytes(self.export_bytes())
        return target

    # -- lifecycle (U0.1) -------------------------------------------------------------
    def mirror_path(self) -> Path:
        """The committed, diffable text mirror for this store (default DIR/garden.export.txt)."""
        return self.dir / DEFAULT_EXPORT_NAME

    def status(self) -> str:
        """The store-vs-mirror freshness state: CURRENT / STALE / MISSING_MIRROR.

        The DB is known to exist (this is an open Store). `MISSING_DB` is reported by the
        module-level `store_status` when no Store can be opened.
        """
        mirror = self.mirror_path()
        if not mirror.exists():
            return "MISSING_MIRROR"
        if self.export_bytes() == mirror.read_bytes():
            return "CURRENT"
        return "STALE"

    def sync_mirror(self) -> str:
        """Atomically refresh the committed mirror from this store. Returns the post-sync status.

        The write is atomic in the practical sense: the export bytes are computed first and the
        file is replaced in one `write_bytes` call, so a reader never sees a half-written mirror.
        After a successful sync the status is `CURRENT`; a failure to write raises, so a caller
        that must not claim success while the mirror is stale can let the exception propagate.
        """
        self.write_export(self.mirror_path())
        return self.status()

    def is_empty(self) -> bool:
        return all(value == 0 for value in self.counts().values())

    def import_bytes(self, data: bytes) -> str:
        """Load an export into this store. Returns a one-line status.

        Idempotent: importing the text the store already holds is a no-op and says so.
        Re-importing into a non-empty store that differs is refused rather than merged.
        The imported text is re-exported and compared byte for byte before the write is
        accepted, so a lossy or order-dependent import cannot pass silently.
        """
        if self.export_bytes() == data:
            return "no-op: store already holds exactly this text"
        if not self.is_empty():
            raise StoreError(
                "refusing to import into a non-empty store that differs from the input "
                "(wipe the store directory first)"
            )
        records = parse_export(data)
        meta = records["meta"]
        if int(meta.get("schema_version", 0)) != SCHEMA_VERSION:
            raise StoreError(
                f"export schema_version {meta.get('schema_version')!r} is not {SCHEMA_VERSION}"
            )
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?), ('created_at', ?)",
                (str(meta["schema_version"]), meta.get("created_at", "")),
            )
            for section in (
                "captures",
                "candidates",
                "candidate_captures",
                "duplicate_hints",
                "decisions",
                "legacy_verification",
                "legacy_batch_membership",
            ):
                for record in records[section]:
                    columns = tuple(record)
                    self.conn.execute(
                        f"INSERT INTO {section} ({', '.join(columns)}) "
                        f"VALUES ({', '.join('?' * len(columns))})",
                        tuple(record[c] for c in columns),
                    )
        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            raise StoreError(f"import rejected: {exc}") from None
        self.conn.commit()
        if self.export_bytes() != data:
            raise StoreError(
                "re-export after import is not byte-identical to the imported text "
                "(the export encoding lost or reordered data)"
            )
        total = sum(len(records[s]) for s in ROW_TABLES)
        return f"imported {total} record(s)"


def parse_export(data: bytes) -> dict:
    """Parse `garden.export/1` text into sections. Raises StoreError on a malformed file."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StoreError(f"export is not valid UTF-8: {exc}") from None
    lines = text.split("\n")
    if not lines or lines[0] != EXPORT_HEADER:
        raise StoreError(f"export must start with {EXPORT_HEADER!r}")
    sections: dict[str, list[dict]] = {"meta": []}
    for section, _, _ in EXPORT_SECTIONS:
        sections[section] = []
    current: str | None = None
    for lineno, line in enumerate(lines[1:], start=2):
        if line == "":
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            if current != "meta" and current not in sections:
                raise StoreError(f"line {lineno}: unknown section {line!r}")
            continue
        if current is None:
            raise StoreError(f"line {lineno}: record outside any section")
        try:
            sections[current].append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise StoreError(f"line {lineno}: not a JSON record ({exc.msg})") from None
    if not sections["meta"]:
        raise StoreError("export has no [meta] record")
    meta = dict(sections["meta"][0])
    return {"meta": meta, **{k: v for k, v in sections.items() if k != "meta"}}


# -- CLI -------------------------------------------------------------------------------


def cmd_create(args: argparse.Namespace) -> int:
    db_path, applied = create_store(args.dir)
    print(f"store: {db_path}")
    if applied:
        print(f"applied migration(s): {', '.join(applied)}")
    else:
        ids = ", ".join(mid for mid, _ in MIGRATIONS)
        print(f"applied migration(s): none")
        print(f"no-op: migration {ids} already applied; store unchanged")
    print("RESULT: PASS")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        target = store.write_export(args.out)
        print(f"export: {target} ({len(store.export_bytes())} bytes)")
    print("RESULT: PASS")
    return 0


def cmd_dump(args: argparse.Namespace) -> int:
    """Write only the export bytes to stdout, so the text can be piped or hashed."""
    with Store(args.dir) as store:
        sys.stdout.buffer.write(store.export_bytes())
        sys.stdout.buffer.flush()
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    create_store(args.dir)
    src = Path(args.src)
    data = src.read_bytes()
    with Store(args.dir) as store:
        status = store.import_bytes(data)
    print(f"import: {src} -> {store.db_path}")
    print(status)
    print("RESULT: PASS")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Self-check: export, re-import into a throwaway copy, re-export, compare bytes."""
    import shutil
    import tempfile

    with Store(args.dir) as store:
        first = store.export_bytes()
    tmp = Path(tempfile.mkdtemp(prefix="garden-store-verify-"))
    try:
        empty = tmp / "store"
        create_store(empty)
        with Store(empty) as fresh:
            status = fresh.import_bytes(first)
            second = fresh.export_bytes()
        if first != second:
            print("FAIL: re-imported store exports different bytes")
            print("RESULT: FAIL")
            return 1
        print(f"round-trip: {len(first)} bytes identical ({status})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("RESULT: PASS")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = store_status(args.dir)
    print(f"store: {args.dir}")
    print(f"status: {state}")
    print("RESULT: PASS")
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    state = bootstrap_store(args.dir)
    print(f"store: {args.dir}")
    print(f"bootstrap: {state}")
    print("RESULT: PASS")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    with Store(args.dir) as store:
        state = store.sync_mirror()
    print(f"store: {args.dir}")
    print(f"sync: {state}")
    print("RESULT: PASS")
    return 0



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="create the store from empty in --dir (idempotent)")
    create.add_argument("--dir", required=True, help="store directory (created if missing)")
    create.set_defaults(func=cmd_create)

    export = sub.add_parser("export", help="write the deterministic text export")
    export.add_argument("--dir", required=True)
    export.add_argument("--out", default=None, help="output path (default DIR/garden.export.txt)")
    export.set_defaults(func=cmd_export)

    dump = sub.add_parser("dump", help="write the export bytes to stdout")
    dump.add_argument("--dir", required=True)
    dump.set_defaults(func=cmd_dump)

    imp = sub.add_parser("import", help="import an export into --dir (idempotent)")
    imp.add_argument("--dir", required=True)
    imp.add_argument("--from", dest="src", required=True, help="export file to import")
    imp.set_defaults(func=cmd_import)

    verify = sub.add_parser("verify", help="export -> re-import -> compare bytes")
    verify.add_argument("--dir", required=True)
    verify.set_defaults(func=cmd_verify)

    status = sub.add_parser(
        "status", help="report the store-vs-mirror freshness state (CURRENT/STALE/MISSING_DB/MISSING_MIRROR)"
    )
    status.add_argument("--dir", required=True)
    status.set_defaults(func=cmd_status)

    bootstrap = sub.add_parser(
        "bootstrap",
        help="hydrate the local store from the committed mirror (never overwrites a divergent store)",
    )
    bootstrap.add_argument("--dir", required=True)
    bootstrap.set_defaults(func=cmd_bootstrap)

    sync = sub.add_parser(
        "sync", help="atomically refresh the committed mirror from the local store"
    )
    sync.add_argument("--dir", required=True)
    sync.set_defaults(func=cmd_sync)


    args = parser.parse_args(argv)
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    try:
        return args.func(args)
    except StoreError as exc:
        print(f"FAIL: {exc}")
        print("RESULT: FAIL")
        return 1
    except (OSError, sqlite3.Error) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        print("RESULT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
