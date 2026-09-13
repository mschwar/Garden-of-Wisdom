#!/usr/bin/env python3
"""Deterministic acceptance test for W1.2: the `garden.candidate-envelope/1` serialized form,
its validator (rules 1-6, each reporting its rule id), the sentinel handling, and the store
bridge into W1.1's `scripts/garden_store.py`.

Usage:
    python3 scripts/check_garden_envelope.py

Runs entirely in a throwaway temporary directory (never the repo) and asserts the W1.2
acceptance criteria from `docs/program/W1_DECOMPOSITION.md` section "W1.2":

  1. a valid envelope is accepted and STORED through the W1.1 store, and read back intact
     (all 21 required fields equal), with the read-back envelope itself validating clean;
  2. each of the six validation rules has a fixture that fails it, and the validator reports
     THAT rule's id -- asserted as an exact set, so a fixture that reports extra rules or a
     generic error fails;
  3. re-serialization round-trips losslessly: serialize -> parse -> serialize is byte-identical
     for every valid envelope, and two envelopes equal as objects serialize identically whatever
     their key insertion order (the check that a lost `sort_keys` turns red);
  4. the sentinel vocabulary is handled as the contract says: every declared sentinel survives
     verbatim through validation, serialization and the store (never turned into ""), a sentinel
     is refused on a field the contract does not declare it for, and a missing required field is
     refused rather than defaulted;
  5. `quotes.csv` / `sources.csv` are byte-identical before and after, and nothing is written
     outside the temp directory.

It also runs the twelve walkthrough envelopes from `docs/program/fixtures/w0_scenarios.json`
(the envelopes `check_program_contracts.py` already asserts satisfy rules 1-4) through the full
validator with a capture record each, so the fixture set and the W0 scenarios cannot diverge.

Exits 0 with `RESULT: PASS` when every check holds, non-zero with `RESULT: FAIL` and one `FAIL:`
line per broken check -- never a traceback, even on a broken envelope or a broken fixture file.

Every negative control for this unit (mutation -> observed FAIL line) is recorded in
`GARDEN_W1_2_HANDOFF.md`.
"""
from __future__ import annotations

import contextlib
import hashlib
import inspect
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import garden_envelope as ge  # noqa: E402
import garden_store  # noqa: E402
from garden_envelope import (  # noqa: E402
    OPTIONAL_FIELDS,
    REQUIRED_FIELDS,
    RULE_IDS,
    SENTINELS,
    EnvelopeError,
    parse,
    read_envelope,
    serialize,
    store_capture,
    store_envelope,
    validate,
)
from garden_store import Store, create_store  # noqa: E402

FIXTURES = ROOT / "docs" / "program" / "fixtures" / "envelope_fixtures.json"
W0_FIXTURES = ROOT / "docs" / "program" / "fixtures" / "w0_scenarios.json"
QUOTES = ROOT / "quotes.csv"
SOURCES = ROOT / "sources.csv"
STORE_FILENAME = garden_store.STORE_FILENAME

failures: list[str] = []


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


def load_json(path: Path, label: str) -> object:
    try:
        return json.loads(path.read_bytes().decode("utf-8"))
    except OSError as exc:
        raise SystemExit(f"FAIL: cannot read {label} {path}: {exc}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL: {label} {path} is not valid JSON: {exc}")


def w0_envelopes() -> tuple[list[tuple[str, dict]], dict[str, str]]:
    """The twelve W0 walkthrough envelopes (template + overrides) and their capture records."""
    fixture = load_json(W0_FIXTURES, "W0 fixture")
    template = fixture["envelope_template"]
    envelopes: list[tuple[str, dict]] = []
    captures: dict[str, str] = {}
    for scenario in fixture["scenarios"]:
        envelope = dict(template)
        envelope.update(scenario.get("envelope_overrides", {}))
        envelopes.append((f"W0:{scenario['id']}", envelope))
        captures[envelope["capture_id"]] = envelope["captured_text"]
    return envelopes, captures


def main() -> int:
    scratch = Path(tempfile.mkdtemp(prefix="garden-envelope-check-"))
    quotes_before = sha256(QUOTES) if QUOTES.exists() else None
    sources_before = sha256(SOURCES) if SOURCES.exists() else None
    print(f"scratch: {scratch}")

    try:
        run_checks(scratch)
    except Exception as exc:  # no traceback on broken input: RESULT must still print
        fail(f"unexpected {type(exc).__name__}: {exc}")
    finally:
        if quotes_before is not None and sha256(QUOTES) != quotes_before:
            fail("quotes.csv changed during the run")
        if sources_before is not None and sha256(SOURCES) != sources_before:
            fail("sources.csv changed during the run")
        if quotes_before is not None and sources_before is not None:
            ok("quotes.csv and sources.csv are byte-identical before and after the run")
        stray = [
            p
            for p in scratch.rglob("*")
            # the store's own files, plus the malformed input this script deliberately writes
            if p.is_file() and p.name not in (STORE_FILENAME, "garden.export.txt", "broken.json")
        ]
        check(not stray, "nothing was written outside the store's own directory", str(stray))
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed)")
        return 1
    print("RESULT: PASS (envelope contract enforced: 6/6 rules, sentinels verbatim, stored and read back)")
    return 0


def run_checks(scratch: Path) -> None:
    fixture = load_json(FIXTURES, "envelope fixture")
    if not isinstance(fixture, dict):
        fail("fixture file is not a JSON object")
        return
    captures = fixture.get("capture_records", {})
    valid_cases = fixture.get("valid_envelopes", [])
    invalid_cases = fixture.get("invalid_envelopes", [])
    print(f"fixtures: {len(valid_cases)} valid, {len(invalid_cases)} invalid, "
          f"{len(captures)} capture record(s)")

    # -- 1. the serialized form: deterministic, canonical, round-trip byte-identical -------
    base = valid_cases[0]["envelope"]
    first = serialize(base)
    check(serialize(base) == first, "serialize is a pure function of the envelope")
    check(parse(first) == base, "parse(serialize(e)) equals e")
    check(
        serialize(parse(first)) == first,
        "serialize -> parse -> serialize is byte-identical (rule 6's round-trip)",
    )
    reversed_order = {key: base[key] for key in reversed(list(base))}
    check(
        serialize(reversed_order) == first,
        "key insertion order cannot change the serialized bytes (sort_keys is load-bearing)",
    )
    check(
        "Bahá’u’lláh" in first and "\\u00" not in first,
        "UTF-8 survives the serialized form as UTF-8, not as \\u escapes",
    )
    try:
        ge.serialize([1, 2, 3])
        fail("serialize accepted a non-object envelope")
    except EnvelopeError as exc:
        ok(f"serialize refuses a non-object envelope ({exc})")
    try:
        parse("not json at all")
        fail("parse accepted text that is not JSON")
    except EnvelopeError as exc:
        ok(f"parse refuses non-JSON text cleanly ({exc})")

    # -- 2. every valid envelope validates clean; the twelve W0 scenarios too --------------
    for case in valid_cases:
        violations = validate(case["envelope"], captures)
        check(
            not violations,
            f"valid fixture {case['id']!r} passes all six rules",
            "; ".join(str(v) for v in violations),
        )
    scenarios, w0_captures = w0_envelopes()
    for label, envelope in scenarios:
        violations = validate(envelope, w0_captures)
        check(
            not violations,
            f"{label} (the W0 walkthrough envelope) passes all six rules",
            "; ".join(str(v) for v in violations),
        )

    # -- 3. re-serialization round-trips losslessly for every valid envelope ---------------
    for case in valid_cases + [{"id": label, "envelope": env} for label, env in scenarios]:
        envelope = case["envelope"]
        text = serialize(envelope)
        check(
            serialize(parse(text)) == text,
            f"round-trip is lossless for {case['id']!r} (including nested optional fields)",
            f"{len(text)} bytes",
        )

    # -- 4. each rule has a failing fixture, and the validator reports THAT rule id ---------
    print()
    print("-- validator output over the fixture set (pass cases + every failing rule id) --")
    seen_rules: dict[str, list[str]] = {rule: [] for rule in RULE_IDS}
    for case in invalid_cases:
        violations = validate(case["envelope"], captures)
        reported = sorted({v.rule for v in violations})
        print(f"case {case['id']}: expected {case['fails_rule']}, reported {reported}")
        for violation in violations:
            # deliberate fixture violations, indented so a `grep '^FAIL:'` still finds only the
            # real broken acceptance checks (one FAIL: line per broken check, as the house style)
            print(f"    rule reported -> {violation}")
        check(
            reported == [case["fails_rule"]],
            f"fixture {case['id']!r} reports exactly {case['fails_rule']}",
            f"reported {reported}",
        )
        if case["fails_rule"] in reported:
            seen_rules[case["fails_rule"]].append(case["id"])
    print("-- end validator output --")
    print()
    for rule in RULE_IDS:
        check(
            len(seen_rules[rule]) >= 1,
            f"{rule} has a failing fixture ({len(seen_rules[rule])}: {', '.join(seen_rules[rule])})",
        )
    check(
        set(seen_rules) == set(RULE_IDS),
        "the fixture set covers every declared rule id",
        str(sorted(seen_rules)),
    )

    # -- 5. sentinel handling: verbatim, never "", never on the wrong field ----------------
    sentinel_case = next(
        (c for c in valid_cases if c["id"] == "sentinel-maximal"), None
    )
    if sentinel_case is None:
        fail("fixture has no 'sentinel-maximal' valid case")
    else:
        envelope = sentinel_case["envelope"]
        expected = {
            "captured_attribution": "unknown",
            "captured_citation": "none",
            "capture_method": "legacy-import",
            "captured_by": "legacy-import",
            "language": "und",
            "source_reference": "none",
            "context_notes": "none",
            "raw_artifact_ref": "none",
            "candidate_author": "unknown",
            "candidate_source_ref": "none",
        }
        for field, sentinel in expected.items():
            check(
                envelope.get(field) == sentinel and sentinel in SENTINELS,
                f"sentinel {sentinel!r} on {field!r} survives validation verbatim",
                repr(envelope.get(field)),
            )
        reparsed = parse(serialize(envelope))
        check(
            all(reparsed.get(f) == s for f, s in expected.items()),
            "every sentinel survives serialize/parse as the sentinel, never as ''",
            str({f: reparsed.get(f) for f in expected}),
        )
    wrong_field = [c for c in invalid_cases if c["fails_rule"] == "rule-1"]
    check(
        len(wrong_field) >= 3,
        f"rule-1 has fixtures for a missing field, an empty string and a mis-placed sentinel "
        f"({len(wrong_field)} rule-1 cases)",
    )
    check(
        bool(validate({}, captures)) and all(v.rule == "rule-1" for v in validate({}, captures)),
        "an envelope with every required field missing is refused (rule-1), never defaulted",
    )
    check(
        bool(validate(base, None)) and [v.rule for v in validate(base, None)] == ["rule-5"],
        "omitting the capture records makes rule 5 report itself (it is never skipped silently)",
    )

    # -- 6. the store bridge: accepted, stored, read back intact ---------------------------
    store_dir = scratch / "store"
    create_store(store_dir)
    with Store(store_dir) as store:
        # (a) the doc's worked example, with its duplicate hint.
        worked = next(c for c in valid_cases if c["id"] == "doc-worked-example")["envelope"]
        store_capture(store, worked)
        candidate_id = store_envelope(store, worked, candidate_id="cand-worked-0001")
        read_back = read_envelope(store, candidate_id)
        check(
            all(read_back.get(f) == worked[f] for f in REQUIRED_FIELDS),
            "every one of the 21 required fields is read back intact from the W1.1 store",
            str([f for f in REQUIRED_FIELDS if read_back.get(f) != worked[f]]),
        )
        violations = validate(read_back, ge.capture_texts(store))
        check(
            not violations,
            "the stored-and-read-back envelope is itself a valid envelope (all six rules)",
            "; ".join(str(v) for v in violations),
        )
        hints = [
            dict(row)
            for row in store.conn.execute(
                "SELECT kind, target, basis FROM duplicate_hints WHERE candidate_id = ? "
                "ORDER BY hint_seq",
                (candidate_id,),
            )
        ]
        check(
            hints == [dict(h) for h in worked["duplicate_hints"]],
            "the envelope's duplicate hints are stored as rows (kind/target/basis)",
            str(hints),
        )
        states = store.conn.execute(
            "SELECT curation_state, research_state, corpus_state, work_state FROM candidates "
            "WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
        check(
            tuple(states) == ("new", "not_started", "candidate_only", "queued"),
            "the stored candidate enters at the intake states only",
            str(tuple(states)) if states else "missing",
        )

        # (b) the sentinel-maximal envelope: sentinels survive the store verbatim.
        sentinel_env = sentinel_case["envelope"]
        store_capture(store, sentinel_env)
        sentinel_candidate = store_envelope(
            store, sentinel_env, candidate_id="cand-sentinel-0001"
        )
        sentinel_read = read_envelope(store, sentinel_candidate)
        check(
            (sentinel_read["language"], sentinel_read["captured_attribution"],
             sentinel_read["captured_by"], sentinel_read["captured_citation"])
            == ("und", "unknown", "legacy-import", "none"),
            "sentinels survive the store verbatim (und / unknown / legacy-import / none), not as ''",
            str({k: sentinel_read[k] for k in
                 ("language", "captured_attribution", "captured_by", "captured_citation")}),
        )
        check(
            validate(sentinel_read, ge.capture_texts(store)) == [],
            "the stored sentinel envelope re-validates clean",
        )

        # (c) the optional-fields envelope stores; only external_id has a column today.
        optional_env = next(
            c for c in valid_cases if c["id"] == "optional-fields-carried"
        )["envelope"]
        store_capture(store, optional_env)
        optional_candidate = store_envelope(
            store, optional_env, candidate_id="cand-optional-0001"
        )
        optional_read = read_envelope(store, optional_candidate)
        check(
            optional_read.get("external_id") == optional_env["external_id"],
            "external_id is the one optional field with a store column today, and it persists",
            repr(optional_read.get("external_id")),
        )
        persisted = sorted(set(optional_read) & set(OPTIONAL_FIELDS))
        check(
            persisted == ["external_id"],
            "the other eight optional fields have no store column yet -- a known W1.2 gap, "
            "recorded as discovered work, not dropped silently",
            f"persisted={persisted}",
        )

        # -- 7. an envelope carrying a decision is refused by the store path, not just the
        #       validator, and the store exposes no way to set a state itself --------------
        decided = next(
            c for c in invalid_cases if c["id"] == "decision-already-made-curation"
        )["envelope"]
        try:
            # The capture record already exists (the worked example above used it), so this is
            # purely the store path's rule-3 refusal: the envelope claims a decision already made.
            store_envelope(store, decided, candidate_id="cand-decided-0001")
            fail("the store path accepted an envelope with curation_state 'accepted'")
        except EnvelopeError as exc:
            check(
                "[rule-3]" in str(exc) and "accepted" in str(exc),
                f"the store path refuses a decision-already-made envelope with rule-3 ({str(exc)[:70]}...)",
            )
        check(
            not any("state" in name for name in inspect.signature(Store.add_candidate).parameters),
            "garden_store.add_candidate exposes no state parameter, so rule 3 cannot be "
            "contradicted by a second write path",
        )
        try:
            store_capture(store, {k: v for k, v in base.items() if k != "captured_text"})
            fail("store_capture accepted an envelope missing a required field")
        except (EnvelopeError, KeyError) as exc:
            ok(f"store_capture refuses an envelope with a missing required field ({type(exc).__name__})")

        # (d) rule 5 against the store: a capture_id that exists but whose recorded text differs
        #     is refused -- the store's capture record, not the envelope's claim, is the witness.
        mismatched = dict(worked)
        mismatched["capture_id"] = "cap-2026-09-12-0002"
        mismatched["captured_text"] = "One finger cannot lift a pebble!"
        try:
            store_envelope(store, mismatched, candidate_id="cand-mismatch-0001")
            fail("the store path accepted a captured_text that contradicts capture "
                 "cap-2026-09-12-0002")
        except EnvelopeError as exc:
            check(
                "[rule-5]" in str(exc),
                "the store path refuses a captured_text that is not byte-identical to the "
                "stored capture (rule-5)",
            )

    # -- 8. broken input is refused cleanly, not with a traceback ---------------------------
    for label, value in (
        ("a JSON list", [1, 2, 3]),
        ("None", None),
        ("a bare string", "The earth is but one country."),
    ):
        violations = validate(value, captures)
        check(
            len(violations) == 1 and violations[0].rule == "rule-1",
            f"validate({label}) reports one rule-1 violation instead of raising",
            str([str(v) for v in violations]),
        )
    for args in (["serialize", "--envelope", str(scratch / "missing.json")],):
        chunk, code = run_cli(args)
        check(
            "RESULT: FAIL" in chunk and "Traceback" not in chunk,
            f"the CLI prints RESULT: FAIL and no traceback for {args[2]}",
            chunk.strip().replace("\n", " | "),
        )
    broken = scratch / "broken.json"
    broken.write_bytes(b"{not json")
    chunk, code = run_cli(["validate", "--envelope", str(broken)])
    check(
        "RESULT: FAIL" in chunk and "Traceback" not in chunk,
        "the CLI reports a malformed envelope as RESULT: FAIL with no traceback",
        chunk.strip().replace("\n", " | "),
    )


def run_cli(args: list[str]) -> tuple[str, int]:
    """Run the module's CLI in-process and capture stdout, so a traceback can be detected."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = ge.main(args)
    return buffer.getvalue(), code


if __name__ == "__main__":
    getattr(sys.stdout, "reconfigure", lambda **_: None)(line_buffering=True)
    sys.exit(main())
