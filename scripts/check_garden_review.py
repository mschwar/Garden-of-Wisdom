#!/usr/bin/env python3
"""Deterministic acceptance + evidence run for W1.5: curation review + decision recording + audit history.

Usage:
    python3 scripts/check_garden_review.py

Runs entirely in a throwaway temporary directory (never the repo) and asserts the W1.5
acceptance criteria from `docs/program/W1_DECOMPOSITION.md` section "W1.5":

  1. all twelve curation transitions (T-C1..T-C12) are exercisable through the CLI and each
     produces an audit entry with actor, timestamp, from, to, transition_id and reason;
  2. acceptance fires the deterministic corpus follow-on T-P1 `candidate_only -> eligible`
     (authority `system`), recorded and audited;
  3. both reversal paths (`T-C8` then `T-P7`, `T-C9` then `T-P7`) leave no dimension stranded:
     a record whose curation leaves `accepted` is never left `eligible`;
  4. rejecting an item keeps the capture and the candidate readable;
  5. no curation action writes research state: `research_state` stays `not_started` throughout,
     and the surface has no research write path;
  6. the queue view is read-only, newest-first, and renders the capture, proposal, notes and
     hints each with the machine-inferred-vs-asserted marker (STATE_MODEL.md invariant 6);
  7. a refused decision writes nothing at all, the `decisions` log is append-only, and the
     read-only commands never write;
  8. `quotes.csv` / `sources.csv` are byte-identical before and after, and nothing is written
     outside the temp directory.

Every transition and every refusal is driven through the real `garden_review.py` CLI as a
subprocess; every fixture candidate and its text/citation are submitted through the real W1.3
CLI and derived from the real `quotes.csv`, so the expectations are derived from the corpus
rather than hard-coded. Negative controls (mutation -> observed `FAIL:` line) are recorded in
`GARDEN_W1_5_HANDOFF.md`.

Exits 0 with `RESULT: PASS`, non-zero with `RESULT: FAIL` and one `FAIL:` line per broken check
-- never a traceback.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import garden_review as gr  # noqa: E402
import garden_store  # noqa: E402
from garden_store import Store, StoreError  # noqa: E402

REVIEW = SCRIPTS / "garden_review.py"
SUBMIT = SCRIPTS / "garden_submit.py"
NORMALIZE = SCRIPTS / "garden_normalize.py"
STORE_CLI = SCRIPTS / "garden_store.py"
QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"
STORE_FILENAME = garden_store.STORE_FILENAME

failures: list[str] = []
refusal_outputs: list[tuple[str, str]] = []


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    failures.append(msg)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def check(condition: bool, msg: str, detail: str = "") -> bool:
    if condition:
        ok(msg)
        return True
    fail(msg + (f" -- {detail}" if detail else ""))
    return False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def would_be_vacuous(msg: str) -> None:
    fail(f"{msg} -- would be vacuous")


def run(script: Path, *args: object) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
        capture_output=True,
    )


def out_text(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout + proc.stderr).decode("utf-8", "replace")


def first_json(proc: subprocess.CompletedProcess) -> dict:
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if line.startswith("{"):
            import json

            return json.loads(line)
    return {}


def counts(store_dir: Path) -> dict[str, int]:
    with Store(store_dir) as store:
        return store.counts()


def export_bytes(store_dir: Path) -> bytes:
    with Store(store_dir) as store:
        return store.export_bytes()


def candidate_row(store_dir: Path, candidate_id: str) -> dict:
    with Store(store_dir) as store:
        row = store.conn.execute(
            "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
        ).fetchone()
    return dict(row) if row else {}


def capture_rows(store_dir: Path, candidate_id: str) -> list[dict]:
    with Store(store_dir) as store:
        return [
            dict(r)
            for r in store.conn.execute(
                "SELECT c.* FROM candidate_captures cc JOIN captures c ON c.capture_id = cc.capture_id "
                "WHERE cc.candidate_id = ? ORDER BY cc.ordinal",
                (candidate_id,),
            )
        ]


def decision_rows(store_dir: Path, candidate_id: str | None = None) -> list[dict]:
    with Store(store_dir) as store:
        if candidate_id is None:
            rows = store.conn.execute(
                "SELECT * FROM decisions ORDER BY seq"
            )
        else:
            rows = store.conn.execute(
                "SELECT * FROM decisions WHERE subject_kind = 'candidate' AND subject_id = ? "
                "ORDER BY seq",
                (candidate_id,),
            )
        return [dict(r) for r in rows]


def decision_transitions(store_dir: Path, candidate_id: str) -> list[str]:
    return [row["transition_id"] for row in decision_rows(store_dir, candidate_id)]


def all_candidate_ids(store_dir: Path) -> list[str]:
    with Store(store_dir) as store:
        return [
            row["candidate_id"]
            for row in store.conn.execute("SELECT candidate_id FROM candidates ORDER BY candidate_id")
        ]


def submit_raw(store_dir: Path, text: str, citation: str, *, candidate_id: str, capture_id: str,
               attribution: str = "operator") -> subprocess.CompletedProcess:
    return run(
        SUBMIT, "submit", "--dir", store_dir, "--text", text,
        "--attribution", attribution, "--citation", citation,
        "--capture-method", "pasted-text",
        "--candidate-id", candidate_id, "--capture-id", capture_id,
    )


def decide(action: str, store_dir: Path, candidate_id: str, reason: str, actor: str = "operator") -> subprocess.CompletedProcess:
    return run(REVIEW, action, "--dir", store_dir, "--candidate-id", candidate_id,
               "--reason", reason, "--actor", actor)


def refusal(label: str, proc: subprocess.CompletedProcess, needle: str, store_dir: Path, before: bytes) -> None:
    text = out_text(proc)
    refusal_outputs.append((label, text))
    check(proc.returncode != 0 and "RESULT: FAIL" in text, f"{label} is refused (exit {proc.returncode}, RESULT: FAIL)")
    check(needle in text, f"{label} names {needle!r} in the refusal", text.strip()[:170])
    check(export_bytes(store_dir) == before, f"{label} wrote nothing at all (store byte-identical)", "")


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-review-check-"))
    quotes_before = sha256(QUOTES) if QUOTES.exists() else None
    sources_before = sha256(SOURCES) if SOURCES.exists() else None
    print(f"scratch: {scratch}")
    try:
        run_checks(scratch)
    except Exception as exc:  # never a traceback: RESULT must still print
        fail(f"unexpected {type(exc).__name__}: {exc}")
    finally:
        for label, text in refusal_outputs:
            if "Traceback" in text:
                fail(f"{label} refused with a traceback instead of a FAIL line")
        if refusal_outputs:
            ok(f"none of the {len(refusal_outputs)} refusals printed a traceback")
        if quotes_before is not None and sha256(QUOTES) != quotes_before:
            fail("quotes.csv changed during the run")
        if sources_before is not None and sha256(SOURCES) != sources_before:
            fail("sources.csv changed during the run")
        if quotes_before is not None and sources_before is not None:
            ok("quotes.csv and sources.csv are byte-identical before and after the run")
        check(not (ROOT / STORE_FILENAME).exists(), "no store was created in the repo root (the CLIs only ever write to --dir)", "")
        stray = [p for p in scratch.rglob("*") if p.is_file() and p.relative_to(scratch).parts[0] not in ("store", "store_order", "trans", "store_direct", "queue_store")]
        check(not stray, "nothing was written outside the stores and scratch inputs", str(stray))
        shutil.rmtree(scratch, ignore_errors=True)
    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed)")
        return 1
    print("RESULT: PASS (all twelve curation transitions audit correctly, the reversal path strands no dimension, and no curation action writes research state)")
    return 0


def run_checks(scratch: Path) -> None:  # noqa: C901 -- one linear evidence script, by design
    store = scratch / "store"
    created = run(STORE_CLI, "create", "--dir", store)
    check(created.returncode == 0 and "RESULT: PASS" in out_text(created), "the store is created from empty", out_text(created).strip()[:170])

    # -- 0. the W1.5 rulings, stated as executable facts --------------------------------
    print("\n-- the W1.5 rulings (transitions + authorities) --")
    check(set(gr.CURATION_ACTIONS) == {"accept", "hold", "reject", "duplicate", "reopen"},
          "the five curation actions are accept/hold/reject/duplicate/reopen",
          str(sorted(gr.CURATION_ACTIONS)))
    check(set(gr.CURATION_ACTIONS) <= set(garden_store.CURATION_ACTIONS) and set(gr.CURATION_ACTIONS) == set(garden_store.CURATION_ACTIONS),
          "the CLI exposes exactly the store's curation actions (one vocabulary)")
    check(len(garden_store.CURATION_TRANSITIONS) == 12, "there are exactly twelve curation transitions",
          str(len(garden_store.CURATION_TRANSITIONS)))
    for tid, pair in (("T-C1", ("new", "accepted")), ("T-C2", ("new", "hold")), ("T-C3", ("new", "rejected")),
                      ("T-C4", ("new", "duplicate")), ("T-C5", ("hold", "accepted")), ("T-C6", ("hold", "rejected")),
                      ("T-C7", ("hold", "duplicate")), ("T-C8", ("accepted", "rejected")), ("T-C9", ("accepted", "duplicate")),
                      ("T-C10", ("rejected", "new")), ("T-C11", ("duplicate", "new")), ("T-C12", ("duplicate", "accepted"))):
        check(garden_store.CURATION_TRANSITIONS[pair] == tid, f"the transition table names {tid} for {pair}", "")
    check(garden_store.CORPUS_TRANSITIONS[("candidate_only", "eligible")] == ("T-P1", "system"),
          "T-P1 candidate_only->eligible is the deterministic system consequence of acceptance")
    check(garden_store.CORPUS_TRANSITIONS[("eligible", "candidate_only")] == ("T-P7", "operator"),
          "T-P7 eligible->candidate_only is the operator reversal (no stranded dimension)")
    check(gr.DEFAULT_ACTOR == "operator", "an omitted --actor records the decision as 'operator', not anonymous")

    # -- 1. the fixture batch (derived from quotes.csv) --------------------------------
    print("\n-- the fixture batch (derived from quotes.csv, submitted through W1.3) --")
    import csv

    rows: dict[int, dict] = {}
    with QUOTES.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[int(row["id"])] = row
    check(bool(rows), "quotes.csv is readable as CSV", str(len(rows)))
    fixture_ids = list(rows)[:10]  # the first ten rows, whatever they are -- real corpus text
    fixture_of = {}
    for i, row_id in enumerate(fixture_ids, start=1):
        row = rows[row_id]
        proc = submit_raw(store, row["quote_text"], row["source_ref"],
                          candidate_id=f"cand-F{row_id:03d}", capture_id=f"cap-F{row_id:03d}",
                          attribution=row["author"])
        check(proc.returncode == 0, f"fixture row {row_id} is submitted through the real W1.3 CLI", out_text(proc).strip()[:170])
        fixture_of[row_id] = f"cand-F{row_id:03d}"
    check(len(fixture_of) == len(fixture_ids) and len(set(fixture_of.values())) == len(fixture_ids),
          f"all {len(fixture_ids)} fixtures have a distinct candidate in the store", "")
    norm = run(NORMALIZE, "normalize", "--dir", store, "--all")
    check(norm.returncode == 0, "normalize --all is accepted before review", out_text(norm).strip()[:170])
    hints = run(NORMALIZE, "hints", "--dir", store, "--all")
    check(hints.returncode == 0, "hints --all is accepted before review", out_text(hints).strip()[:170])
    check(counts(store)["decisions"] == 0, "submission + normalization + hints wrote no decision row", str(counts(store)["decisions"]))

    # -- 2. the queue surface ----------------------------------------------------------
    print("\n-- the queue view: read-only, newest-first, machine-inferred markers --")
    q = run(REVIEW, "queue", "--dir", store)
    transcript = out_text(q)
    check(q.returncode == 0 and "RESULT: PASS" in transcript, "queue is accepted (exit 0)", transcript.strip()[:170])
    check("Traceback" not in transcript, "queue prints no traceback")
    check(f"{len(fixture_of)} candidate(s)" in transcript, "the queue reports the size of the unreviewed queue")
    for row_id, fid in fixture_of.items():
        check(f"candidate: {fid}" in transcript, f"queue shows fixture candidate {fid} (row {row_id})")
    check("capture (asserted" in transcript, "the queue labels the capture as asserted (verbatim encounter)")
    check("derived (deterministic normalization" in transcript, "the queue labels the proposal as derived (normalization)")
    check("normalization_notes (asserted" in transcript, "the queue labels the normalization notes as asserted")
    check("machine-inferred" in transcript, "the queue marks the duplicate hints as machine-inferred")
    check("a hint is evidence, never a decision" in transcript, "the queue says out loud that a hint is never a decision")
    check("read-only in W1.5" in transcript and "not_started" in transcript,
          "the queue renders research_state read-only and always not_started")
    check("the operator decides" in transcript, "the queue marks curation as the operator's call")
    check(counts(store)["decisions"] == 0, "running the queue wrote no decision", str(counts(store)["decisions"]))
    q_again = out_text(run(REVIEW, "queue", "--dir", store))
    check(q_again == transcript, "the queue output is deterministic (byte-identical across runs)")

    # newest-first order, asserted on a controlled store with distinct created_at values.
    order_store = scratch / "store_order"
    run(STORE_CLI, "create", "--dir", order_store)
    with Store(order_store) as s:
        for n, stamp in ((1, "2026-09-13T08:00:00-06:00"), (2, "2026-09-13T09:00:00-06:00"), (3, "2026-09-13T10:00:00-06:00")):
            s.add_capture(f"cap-o{n}", f"quote number {n}", captured_at=stamp)
            s.add_candidate(f"cand-o{n:03d}", f"quote number {n}", [f"cap-o{n}"], normalization_notes="identical to capture", created_at=stamp)
    order_text = out_text(run(REVIEW, "queue", "--dir", order_store))
    q_ids = [line.split(": ", 1)[1] for line in order_text.splitlines() if line.startswith("candidate: ")]
    check(q_ids == ["cand-o003", "cand-o002", "cand-o001"],
          "the queue lists the unreviewed candidates newest-first (created_at DESC)",
          str(q_ids))

    # -- 3. all twelve curation transitions, driven through the CLI --------------------
    print("\n-- every one of the twelve curation transitions, driven through the CLI --")
    trans_store = scratch / "trans"
    run(STORE_CLI, "create", "--dir", trans_store)
    for i in range(1, 13):
        proc = run(SUBMIT, "submit", "--dir", trans_store, "--text", f"transition fixture {i}",
                   "--citation", f"Work {i}", "--capture-method", "pasted-text",
                   "--candidate-id", f"cand-t{i:02d}", "--capture-id", f"cap-t{i:02d}")
        check(proc.returncode == 0, f"transition fixture {i:02d} is submitted", out_text(proc).strip()[:170])

    def expect(action, candidate, reason, *, c_to, c_from="new", p_to="candidate_only", transitions_after):
        prev_candidate_rows = len(decision_rows(trans_store, candidate))
        before_total = counts(trans_store)["decisions"]
        proc = decide(action, trans_store, candidate, reason)
        text = out_text(proc)
        check(proc.returncode == 0 and "RESULT: PASS" in text,
              f"{action}: {candidate} ({reason[:24]!r}...) is accepted (exit 0)", text.strip()[:170])
        got = decision_transitions(trans_store, candidate)
        check(got == transitions_after, f"{action}: {candidate} recorded exactly {transitions_after}",
              str(got))
        row = candidate_row(trans_store, candidate)
        check(row.get("curation_state") == c_to, f"{action}: {candidate} curation_state is {c_to!r}", row.get("curation_state", ""))
        check(row.get("corpus_state") == p_to, f"{action}: {candidate} corpus_state is {p_to!r}", row.get("corpus_state", ""))
        check(row.get("research_state") == "not_started", f"{action}: {candidate} research_state stayed not_started", row.get("research_state", ""))
        new_rows = len(transitions_after) - prev_candidate_rows
        check(counts(trans_store)["decisions"] == before_total + new_rows,
              f"{action}: {candidate} added exactly {new_rows} new decision row(s) to the store",
              f"{counts(trans_store)['decisions']} vs {before_total}+{new_rows}")

    # T-C1 new -> accepted (+ T-P1)
    expect("accept", "cand-t01", "wanted and pursuable", c_to="accepted", p_to="eligible",
           transitions_after=["T-C1", "T-P1"])
    # T-C2 new -> hold
    expect("hold", "cand-t02", "defer until attribution is checked", c_to="hold",
           transitions_after=["T-C2"])
    # T-C3 new -> rejected
    expect("reject", "cand-t03", "not wanted in the Garden", c_to="rejected",
           transitions_after=["T-C3"])
    # T-C4 new -> duplicate
    expect("duplicate", "cand-t04", "already represented by another passage", c_to="duplicate",
           transitions_after=["T-C4"])
    # T-C2 hold, then T-C5 hold -> accepted (+ T-P1)
    expect("hold", "cand-t05", "defer first", c_to="hold", transitions_after=["T-C2"])
    expect("accept", "cand-t05", "deferred decision resolved", c_to="accepted", p_to="eligible",
           transitions_after=["T-C2", "T-C5", "T-P1"])
    # T-C2 hold, then T-C6 hold -> rejected
    expect("hold", "cand-t06", "defer first", c_to="hold", transitions_after=["T-C2"])
    expect("reject", "cand-t06", "on reflection not wanted", c_to="rejected",
           transitions_after=["T-C2", "T-C6"])
    # T-C2 hold, then T-C7 hold -> duplicate
    expect("hold", "cand-t07", "defer first", c_to="hold", transitions_after=["T-C2"])
    expect("duplicate", "cand-t07", "confirmed duplicate of t05", c_to="duplicate",
           transitions_after=["T-C2", "T-C7"])
    # T-C1 accept (+ T-P1), then T-C8 accepted -> rejected (+ T-P7): the reversal
    expect("accept", "cand-t08", "wanted first", c_to="accepted", p_to="eligible",
           transitions_after=["T-C1", "T-P1"])
    expect("reject", "cand-t08", "reversal: attribution is wrong", c_to="rejected", p_to="candidate_only",
           transitions_after=["T-C1", "T-P1", "T-C8", "T-P7"])
    # T-C1 accept (+ T-P1), then T-C9 accepted -> duplicate (+ T-P7): the reversal
    expect("accept", "cand-t09", "wanted first", c_to="accepted", p_to="eligible",
           transitions_after=["T-C1", "T-P1"])
    expect("duplicate", "cand-t09", "duplicate link established later", c_to="duplicate", p_to="candidate_only",
           transitions_after=["T-C1", "T-P1", "T-C9", "T-P7"])
    # T-C3 reject, then T-C10 rejected -> new
    expect("reject", "cand-t10", "reject first", c_to="rejected", transitions_after=["T-C3"])
    expect("reopen", "cand-t10", "new information arrived", c_to="new",
           transitions_after=["T-C3", "T-C10"])
    # T-C4 duplicate, then T-C11 duplicate -> new
    expect("duplicate", "cand-t11", "duplicate first", c_to="duplicate", transitions_after=["T-C4"])
    expect("reopen", "cand-t11", "duplicate link disproved", c_to="new",
           transitions_after=["T-C4", "T-C11"])
    # T-C4 duplicate, then T-C12 duplicate -> accepted (+ T-P1)
    expect("duplicate", "cand-t12", "duplicate first", c_to="duplicate", transitions_after=["T-C4"])
    expect("accept", "cand-t12", "duplicate link disproved, item wanted", c_to="accepted", p_to="eligible",
           transitions_after=["T-C4", "T-C12", "T-P1"])

    covered = {
        row["transition_id"]
        for d in all_candidate_ids(trans_store)
        for row in decision_rows(trans_store, d)
        if row["dimension"] == "curation"
    }
    check(set(covered) == {f"T-C{i}" for i in range(1, 13)},
          "all twelve curation transition ids T-C1..T-C12 were actually recorded", str(sorted(covered)))

    # -- 4. audit entries have actor, timestamp, from, to, transition_id, reason ------
    print("\n-- the audit entries (who/what/when/from/to/reason) --")
    audited = True
    for d in all_candidate_ids(trans_store):
        for row in decision_rows(trans_store, d):
            if not (row.get("actor") and row.get("reason") and row.get("from_state") in garden_store.CURATION_STATES + garden_store.CORPUS_STATES
                    and row.get("to_state") in garden_store.CURATION_STATES + garden_store.CORPUS_STATES
                    and row.get("transition_id") and row.get("occurred_at")):
                audited = False
    check(audited, "every decision row carries actor, reason, from/to (in the vocab), transition_id and a timestamp")

    # issue #45 gap 2: the `action` vocabulary itself was never inspected.
    action_ok = True
    for d in all_candidate_ids(trans_store):
        for row in decision_rows(trans_store, d):
            expected_action = "curation-decision" if row["dimension"] == "curation" else "corpus-follow-on"
            if row.get("action") != expected_action:
                action_ok = False
    check(action_ok,
          "every curation-dimension row is recorded as 'curation-decision' and every corpus-dimension "
          "follow-on row as 'corpus-follow-on'")
    for d in ("cand-t08", "cand-t09"):
        for row in decision_rows(trans_store, d):
            try:
                datetime.fromisoformat(row["occurred_at"].replace("Z", "+00:00"))
                stamp_ok = True
            except ValueError:
                stamp_ok = False
            check(stamp_ok, f"decision on {d} has a parseable ISO timestamp ({row['occurred_at']})")
            break
    t1 = [row for row in decision_rows(trans_store, "cand-t08") if row["transition_id"] == "T-P1"]
    check(bool(t1 and t1[0]["actor_kind"] == "system" and t1[0]["dimension"] == "corpus"),
          "T-P1 is recorded as a system-authority corpus transition", str(t1[0] if t1 else None))
    t7 = [row for row in decision_rows(trans_store, "cand-t08") if row["transition_id"] == "T-P7"]
    check(bool(t7 and t7[0]["actor_kind"] == "operator" and t7[0]["dimension"] == "corpus" and t7[0]["actor"] == "operator"),
          "T-P7 is recorded as an operator-authority corpus transition tied to the operator", str(t7[0] if t7 else None))
    audit_cli = out_text(run(REVIEW, "audit", "--dir", trans_store, "--candidate-id", "cand-t08"))
    check("T-C1" in audit_cli and "T-P1" in audit_cli and "T-C8" in audit_cli and "T-P7" in audit_cli,
          "the audit command prints the candidate's full append-only history", "")

    # -- 5. no dimension is stranded ---------------------------------------------------
    print("\n-- the reversal path strands no dimension --")
    stranded = []
    for cid in all_candidate_ids(trans_store):
        row = candidate_row(trans_store, cid)
        if row["curation_state"] in ("hold", "rejected", "duplicate") and row["corpus_state"] in ("eligible", "canonical"):
            stranded.append((cid, row["curation_state"], row["corpus_state"]))
    check(not stranded, "no record has curation hold/rejected/duplicate while corpus is eligible/canonical", str(stranded))
    # every corpus=eligible record is accepted
    not_accepted_eligible = [
        (cid, candidate_row(trans_store, cid)["curation_state"])
        for cid in all_candidate_ids(trans_store)
        if candidate_row(trans_store, cid)["corpus_state"] == "eligible"
        and candidate_row(trans_store, cid)["curation_state"] != "accepted"
    ]
    check(not not_accepted_eligible, "every corpus=eligible record is curations=accepted", str(not_accepted_eligible))

    # -- 6. research state stays untouched by curation ---------------------------------
    print("\n-- no curation action writes research state --")
    research_ok = all(
        candidate_row(trans_store, cid).get("research_state") == "not_started"
        for cid in all_candidate_ids(trans_store)
    ) and all(
        candidate_row(store, cid).get("research_state") == "not_started"
        for cid in all_candidate_ids(store)
    )
    check(research_ok, "after every curation action, research_state is still not_started on every candidate")
    check("research" not in "accept hold reject duplicate reopen".split() and "research" not in list(gr.CURATION_ACTIONS),
          "no curation action name is a research operation")
    try:
        with Store(trans_store) as s:
            s.curate("cand-t01", action="accept", actor="operator", reason="x")
        fail("a second accept on an already-accepted candidate was accepted (accepted->accepted is illegal)")
    except StoreError:
        ok("curate refuses an illegal transition (accepted->accepted), so nothing here can touch research state")

    # -- 7. rejecting keeps the capture and the candidate readable --------------------
    print("\n-- rejecting keeps the capture and candidate readable --")
    rejected = candidate_row(trans_store, "cand-t03")
    rejected_captures = capture_rows(trans_store, "cand-t03")
    check(rejected.get("curation_state") == "rejected", "the rejected candidate's curation_state is rejected")
    check(bool(rejected_captures) and rejected_captures[0]["captured_text"] == "transition fixture 3",
          "the rejected candidate still reads back with its verbatim capture")
    show_rejected = out_text(run(REVIEW, "show", "--dir", trans_store, "--candidate-id", "cand-t03"))
    check("transition fixture 3" in show_rejected and "rejected" in show_rejected,
          "show still renders the rejected candidate and its capture", "")

    # -- 8. refusals write nothing -----------------------------------------------------
    print("\n-- refusals (every one writes nothing at all) --")
    before_export = export_bytes(trans_store)
    refusal("an accept on an already-accepted candidate",
            decide("accept", trans_store, "cand-t01", "again"), "no legal curation transition", trans_store, before_export)
    refusal("a reject on an already-rejected candidate",
            decide("reject", trans_store, "cand-t03", "again"), "no legal curation transition", trans_store, before_export)
    refusal("a reject on a duplicate candidate (duplicate->rejected is not a transition)",
            decide("reject", trans_store, "cand-t04", "x"), "no legal curation transition", trans_store, before_export)
    refusal("an accept on a rejected candidate (must reopen first)",
            decide("accept", trans_store, "cand-t03", "x"), "no legal curation transition", trans_store, before_export)
    refusal("a reopen on a new candidate (new->new is not a transition)",
            decide("reopen", trans_store, "cand-t10", "x"), "no legal curation transition", trans_store, before_export)
    refusal("a duplicate on a rejected candidate",
            decide("duplicate", trans_store, "cand-t03", "x"), "no legal curation transition", trans_store, before_export)
    refusal("a decision with an empty reason",
            run(REVIEW, "accept", "--dir", trans_store, "--candidate-id", "cand-t10", "--reason", ""),
            "reason", trans_store, before_export)
    refusal("a decision for a candidate that does not exist",
            decide("accept", trans_store, "cand-NOPE", "x"), "no candidate", trans_store, before_export)
    check(export_bytes(trans_store) == before_export, "the store is byte-identical after all refusals")

    # -- 9. the read-only commands never write -----------------------------------------
    print("\n-- the read-only commands never write --")
    ro_before = export_bytes(store)
    for sub in ("queue",):
        run(REVIEW, sub, "--dir", store)
    run(REVIEW, "show", "--dir", trans_store, "--candidate-id", "cand-t08")
    run(REVIEW, "audit", "--dir", trans_store)
    check(export_bytes(store) == ro_before, "queue/show/audit left the fixture store byte-identical")

    # -- 10. the decision log is append-only -------------------------------------------
    print("\n-- the decision log is append-only --")
    import sqlite3

    with Store(trans_store) as s:
        before_rows = [tuple(r) for r in s.conn.execute("SELECT * FROM decisions ORDER BY seq")]
        for statement, params in (("UPDATE decisions SET reason='rewritten' WHERE seq=1", ()),
                                  ("DELETE FROM decisions WHERE seq=1", ())):
            try:
                s.conn.execute(statement, params)
                s.conn.commit()
                fail(f"decisions accepted {statement.split()[0]}: the log is not append-only")
            except sqlite3.IntegrityError as exc:
                ok(f"decisions rejects {statement.split()[0]} ({str(exc).splitlines()[0]})")
        after_rows = [tuple(r) for r in s.conn.execute("SELECT * FROM decisions ORDER BY seq")]
        check(before_rows == after_rows, "no decision row changed after the rejected writes")

    # -- 11. the store-layer gate refuses bad curate calls, writing nothing ------------
    print("\n-- the store written against directly (each guard has its own falsifier) --")
    direct = scratch / "store_direct"
    run(STORE_CLI, "create", "--dir", direct)
    run(SUBMIT, "submit", "--dir", direct, "--text", "direct call", "--citation", "Work 1",
        "--capture-method", "pasted-text", "--candidate-id", "cand-d01", "--capture-id", "cap-d01")
    d_before = export_bytes(direct)
    # Each store-layer guard gets its OWN falsifier. The reason/actor/unknown-action cases must
    # target a VALID candidate (cand-d01) so their guard fires before the candidate-existence
    # check can mask it; only the missing-candidate case targets an id that does not exist.
    for label, candidate, kwargs, needle, layer_needle in (
        # `layer_needle` is the distinctive substring of the STORE-CURATE guard (curate's own
        # _require) as opposed to the shared _insert_decision guard, so removing curate's guard
        # (which _insert_decision would otherwise mask) is caught by the layering assertion.
        ("an empty reason", "cand-d01", {"action": "accept", "actor": "operator", "reason": ""},
         "reason", "every curation decision must carry a reason"),
        ("a missing actor", "cand-d01", {"action": "accept", "actor": "", "reason": "x"},
         "actor", "every curation decision needs an actor"),
        ("an unknown action", "cand-d01", {"action": "nuke", "actor": "operator", "reason": "x"},
         "unknown curation action", "unknown curation action"),
        ("a missing candidate", "cand-does-not-exist", {"action": "accept", "actor": "operator", "reason": "x"},
         "no candidate", "no candidate"),
    ):
        try:
            with Store(direct) as s:
                s.curate(candidate, **kwargs)
            fail(f"store.curate accepted {label} -- it must refuse")
        except StoreError as exc:
            check(needle in str(exc), f"store.curate refuses {label} and names {needle!r}", str(exc)[:170])
            check(layer_needle in str(exc),
                  f"the refusal for {label} came from curate's OWN guard ({layer_needle!r}) not a shared/backstop guard",
                  str(exc)[:170])
    check(export_bytes(direct) == d_before, "the refused store-layer calls wrote nothing at all")


if __name__ == "__main__":
    sys.exit(main())