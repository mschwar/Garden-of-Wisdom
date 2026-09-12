#!/usr/bin/env python3
"""Deterministic consistency checker for the W0 corpus-program doctrine set.

Usage:
    python3 scripts/check_program_contracts.py

This is a DOCUMENTATION test, not runtime. It reads only:

  docs/program/STATE_MODEL.md            (transition table + vocabularies)
  docs/program/CANDIDATE_ENVELOPE.md     (required envelope fields + method enum)
  docs/program/fixtures/w0_scenarios.json (the ten canonical adversarial walkthroughs)

and asserts that the doctrine set is internally consistent:

  1. every transition id used by a scenario exists in the STATE_MODEL table
  2. each scenario's transition chain is connected and ends in its declared end state
  3. operator-authority transitions are declared as such, and no operator gate is
     performed implicitly
  4. transition guards hold (T-P1/T-P2 need curation accepted; T-R4 needs a real
     research case to have run)
  5. each scenario's record-level research state equals the aggregate of its per-claim
     statuses, using the rule written in VERIFICATION_CONTRACT.md
  6. a claim may only be `verified` if it carries evidence with a witness AND a locator
  7. uncertainty stays visible wherever the record is not fully verified, or makes no
     wording claim at all (paraphrase)
  8. canonical is never reached without curation acceptance
  9. every scenario envelope satisfies the candidate-envelope contract
 10. all ten canonical test cases and the five Gate A requirement kinds are covered

Exits 0 with `RESULT: PASS` when every check holds.

It reads quotes.csv / sources.csv READ-ONLY, purely to re-derive the row counts the doctrine
asserts about the current corpus. It writes nothing and does not import or exercise any W1
runtime behaviour -- W1 is not started.
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "docs" / "program"
STATE_MODEL = PROGRAM / "STATE_MODEL.md"
ENVELOPE = PROGRAM / "CANDIDATE_ENVELOPE.md"
FIXTURES = PROGRAM / "fixtures" / "w0_scenarios.json"
VERIFICATION_CONTRACT = PROGRAM / "VERIFICATION_CONTRACT.md"

DIMENSIONS = {"curation", "research", "corpus", "work"}
STATE_KEY = {
    "curation": "curation_state",
    "research": "research_state",
    "corpus": "corpus_state",
    "work": "work_state",
}
SECTION_TO_DIMENSION = {
    "## 1. Curation state": "curation",
    "## 2. Research state": "research",
    "## 3. Corpus state": "corpus",
    "## 4. Work state": "work",
}
AUTHORITIES = {"system", "agent", "operator"}
HINT_KINDS = {"exact-text", "near-text", "same-reference", "same-passage"}
#: Gate A's requirement kinds, HARDCODED from
#: bootstrap/seed/2026-09-12-garden-corpus-program/ACCEPTANCE_GATES.md. Deliberately not read
#: from the fixture: coverage must be asserted against the gate, not against whatever the
#: fixture happens to declare.
GATE_A_KINDS = {"uncited", "verified", "disputed", "unverifiable", "translation-variant"}
#: Corpus states that constitute promotion. Every transition INTO one of these must have a
#: named way back out, or a reversed curation decision strands the record forever.
PROMOTED_CORPUS_STATES = {"eligible", "canonical"}
INTAKE_STATES = {
    "curation_state": "new",
    "research_state": "not_started",
    "corpus_state": "candidate_only",
    "work_state": "queued",
}
CANONICAL_CASES = [
    "exact-quote",
    "paraphrase",
    "wrong-author",
    "wrong-work",
    "quote-of-a-quote",
    "translation-variant",
    "fabricated-attribution",
    "oral-attribution",
    "ambiguous-source",
    "unverifiable",
]

FAILURES = []


def fail(msg):
    FAILURES.append(msg)
    print(f"FAIL: {msg}")


def tokens(text):
    return re.findall(r"`([^`]+)`", text)


def parse_state_model(path):
    """Returns (transitions, vocabularies)."""
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
        return {}, {}
    lines = path.read_text(encoding="utf-8").splitlines()
    transitions = {}
    vocabularies = {"curation": set(), "research": set(), "corpus": set(), "work": set()}
    dimension = None
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        for header, dim in SECTION_TO_DIMENSION.items():
            if stripped.startswith(header):
                dimension = dim
        if stripped.startswith("Vocabulary:"):
            collected = list(tokens(stripped))
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("`"):
                collected += tokens(lines[j])
                j += 1
            if dimension is not None:
                vocabularies[dimension] |= set(collected)
            i = j
            continue
        if stripped.startswith("| T-"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) != 6:
                fail(f"transition row has {len(cells)} columns, expected 6: {stripped[:60]}")
            else:
                tid, dim, src, dst, authority, _cond = cells
                if dim not in DIMENSIONS:
                    fail(f"{tid}: unknown dimension {dim!r}")
                if authority not in AUTHORITIES:
                    fail(f"{tid}: unknown authority {authority!r}")
                if tid in transitions:
                    fail(f"duplicate transition id {tid}")
                transitions[tid] = {
                    "dimension": dim,
                    "from": src.strip("`"),
                    "to": dst.strip("`"),
                    "authority": authority,
                }
        i += 1
    if not transitions:
        fail(f"no transition rows parsed from {path.relative_to(ROOT)}")
    return transitions, vocabularies


def parse_required_envelope_fields(path):
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
        return [], set()
    text = path.read_text(encoding="utf-8")
    start = text.find("## Required fields")
    stop = text.find("## Duplicate hints")
    if start < 0 or stop < 0 or stop <= start:
        fail("could not locate the '## Required fields' section in CANDIDATE_ENVELOPE.md")
        return [], set()
    section = text[start:stop]
    required = []
    for line in section.splitlines():
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(parts) >= 3 and parts[0].startswith("`"):
            required.append(parts[0].strip("`"))
    methods = set()
    for line in section.splitlines():
        if line.strip().startswith("| `capture_method`"):
            parts = [c.strip() for c in line.strip().strip("|").split("|")]
            # the enum lives in the last cell of the row, not the second
            for cell in parts[1:]:
                methods |= set(tokens(cell))
    if not methods:
        fail("could not parse the capture_method enum from CANDIDATE_ENVELOPE.md")
    return required, methods


def parse_aggregate_rule(path):
    """Parse the normative aggregate rule out of VERIFICATION_CONTRACT.md's code block.

    Returns an ordered list of (condition, outcome) pairs, e.g.
    ('any claim is unverifiable', 'unverifiable').
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    marker = "if any claim is unverifiable"
    start = text.find(marker)
    if start < 0:
        fail("VERIFICATION_CONTRACT.md no longer contains the aggregate-rule block")
        return []
    end = text.find("```", start)
    block = text[start : end if end > 0 else len(text)]
    rule = []
    for line in block.splitlines():
        line = line.strip()
        if "->" not in line:
            continue
        cond, _, outcome = line.partition("->")
        cond = cond.strip()
        for prefix in ("if ", "elif ", "else "):
            if cond.startswith(prefix):
                cond = cond[len(prefix):].strip()
        cond = cond.strip("()").strip()
        outcome = outcome.strip().rstrip(":")
        # the first rule reads "-> record research_state = unverifiable"; keep the value
        outcome = outcome.split("=")[-1].strip().split()[0] if outcome.split() else outcome
        rule.append((cond, outcome))
    return rule


#: The rule the checker implements. MUST equal the block parsed out of
#: VERIFICATION_CONTRACT.md -- a doc edit that changes the rule fails the run.
AGGREGATE_RULE = [
    ("any claim is unverifiable", "unverifiable"),
    ("any claim is disputed", "disputed"),
    ("any claim is needs_more_evidence", "needs_more_evidence"),
    ("any claim is in_research", "in_research"),
    ("any claim is not_started", "not_started"),
    ("all claims verified", "verified"),
]


def aggregate_research_state(claims):
    """Rule from VERIFICATION_CONTRACT.md, asserted against AGGREGATE_RULE."""
    statuses = [c["status"] for c in claims]
    if not statuses:
        return "not_started"
    for cond, outcome in AGGREGATE_RULE:
        if cond == "any claim is unverifiable" and "unverifiable" in statuses:
            return outcome
        if cond == "any claim is disputed" and "disputed" in statuses:
            return outcome
        if cond == "any claim is needs_more_evidence" and "needs_more_evidence" in statuses:
            return outcome
        if cond == "any claim is in_research" and "in_research" in statuses:
            return outcome
        if cond == "any claim is not_started" and "not_started" in statuses:
            return outcome
        if cond == "all claims verified":
            return outcome
    return "not_started"


def check_envelope(scenario, envelope, required, methods):
    sid = scenario.get("id", "<unnamed scenario>")
    for field in required:
        if field not in envelope:
            fail(f"{sid}: envelope missing required field {field!r}")
        elif not isinstance(envelope[field], list) and str(envelope[field]).strip() == "":
            fail(f"{sid}: envelope field {field!r} is empty (use a sentinel: unknown/und/none)")
    if methods and envelope.get("capture_method") not in methods:
        fail(f"{sid}: capture_method {envelope.get('capture_method')!r} not in {sorted(methods)}")
    start = scenario.get("start", {})
    for key, expected in INTAKE_STATES.items():
        if envelope.get(key) != expected:
            fail(f"{sid}: envelope {key} must be {expected!r} at intake, got {envelope.get(key)!r}")
        if start.get(key) != expected:
            fail(f"{sid}: scenario.start {key} must be {expected!r} at intake, got {start.get(key)!r}")
    if not str(envelope.get("normalization_notes", "")).strip():
        fail(f"{sid}: normalization_notes must assert what normalization did (or 'identical to capture')")
    for hint in envelope.get("duplicate_hints", []):
        if hint.get("kind") not in HINT_KINDS:
            fail(f"{sid}: duplicate hint kind {hint.get('kind')!r} not in {sorted(HINT_KINDS)}")
        if not str(hint.get("target", "")).strip() or not str(hint.get("basis", "")).strip():
            fail(f"{sid}: duplicate hint needs non-empty target and basis")


def check_walkthrough(scenario, transitions, vocabularies):
    sid = scenario.get("id", "<unnamed scenario>")
    for key in ("start", "end", "transitions", "operator_transitions"):
        if key not in scenario:
            fail(f"{sid}: scenario is missing the required key {key!r}")
            return
    start = dict(scenario["start"])
    end = dict(scenario["end"])
    for key, expected in INTAKE_STATES.items():
        if start.get(key) != expected:
            fail(f"{sid}: scenario.start {key} must be {expected!r} at intake, got {start.get(key)!r}")
            return
    state = start
    used_operator = set()
    research_ran = False

    for step, tid in enumerate(scenario["transitions"]):
        tr = transitions.get(tid)
        if tr is None:
            fail(f"{sid}: transition {tid} (step {step + 1}) is not in the STATE_MODEL table")
            continue
        dim = tr["dimension"]
        key = STATE_KEY[dim]
        if state[key] != tr["from"]:
            fail(f"{sid}: {tid} expects {dim}=={tr['from']!r} but the chain is at {state[key]!r}")
        if dim in vocabularies and (tr["from"] not in vocabularies[dim] or tr["to"] not in vocabularies[dim]):
            fail(f"{sid}: {tid} uses states outside the declared {dim} vocabulary")
        # guards
        if tid in ("T-P1", "T-P2") and state["curation_state"] != "accepted":
            fail(f"{sid}: {tid} requires curation 'accepted', chain has {state['curation_state']!r}")
        if tid == "T-R4" and not research_ran:
            fail(f"{sid}: T-R4 (-> verified) without any research case having run (invariant 2)")
        if tr["authority"] == "operator":
            used_operator.add(tid)
        if tid in ("T-R1", "T-R3", "T-R12"):
            research_ran = True
        state[key] = tr["to"]

    if state != end:
        fail(f"{sid}: chain ends in {state} but scenario.end declares {end}")

    # End-state consistency: the corpus dimension must agree with the curation decision.
    if end["corpus_state"] in ("eligible", "canonical") and end["curation_state"] != "accepted":
        fail(
            f"{sid}: corpus_state {end['corpus_state']!r} requires curation 'accepted', "
            f"but the record ends {end['curation_state']!r}"
        )
    if end["curation_state"] in ("rejected", "duplicate", "hold") and end["corpus_state"] in (
        "eligible",
        "canonical",
    ):
        fail(
            f"{sid}: a {end['curation_state']!r} curation decision must not leave the record "
            f"{end['corpus_state']!r} (no reversal transition was taken)"
        )

    declared_operator = set(scenario["operator_transitions"])
    if used_operator != declared_operator:
        fail(
            f"{sid}: operator_transitions {sorted(declared_operator)} do not match the "
            f"operator-authority transitions actually used {sorted(used_operator)}"
        )

    claims = scenario.get("claims", [])
    for claim in claims:
        if claim["status"] not in vocabularies["research"]:
            fail(f"{sid}: claim {claim['claim']!r} status {claim['status']!r} outside the research vocabulary")
        if claim["status"] == "verified":
            for ev in claim.get("evidence", []):
                if not str(ev.get("witness", "")).strip() or not str(ev.get("locator", "")).strip():
                    fail(f"{sid}: claim {claim['claim']!r} is verified but its evidence lacks witness/locator")
            if not claim.get("evidence"):
                fail(f"{sid}: claim {claim['claim']!r} is verified with no evidence item")

    derived = aggregate_research_state(claims)
    if derived != scenario["end"]["research_state"]:
        fail(
            f"{sid}: record research_state {scenario['end']['research_state']!r} disagrees with the "
            f"aggregate of its claims ({derived!r})"
        )

    if scenario["end"]["corpus_state"] == "canonical" and scenario["end"]["curation_state"] != "accepted":
        fail(f"{sid}: canonical without curation acceptance (invariant 1/5)")

    makes_wording_claim = any(c["claim"] == "wording" for c in claims)
    if scenario["end"]["research_state"] != "verified" or not makes_wording_claim:
        if not scenario.get("uncertainty_visible"):
            fail(
                f"{sid}: uncertainty must stay visible (research_state="
                f"{scenario['end']['research_state']!r}, wording claim present={makes_wording_claim})"
            )


def check_documented_facts(facts):
    """Re-derive the doctrine's claims about the current corpus from the data itself."""
    if not facts:
        fail("fixture has no documented_csv_facts block")
        return
    try:
        with open(ROOT / "quotes.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        with open(ROOT / "sources.csv", encoding="utf-8", newline="") as fh:
            src_rows = list(csv.DictReader(fh))
    except OSError as exc:
        fail(f"could not read the canonical CSVs: {exc}")
        return

    def compare(label, actual, expected):
        if actual != expected:
            fail(f"documented fact {label} says {expected!r} but the data says {actual!r}")

    compare("quote_rows", len(rows), facts.get("quote_rows"))
    compare(
        "verification_status_counts",
        {k: v for k, v in sorted(Counter(r["verification_status"] for r in rows).items())},
        {k: v for k, v in sorted((facts.get("verification_status_counts") or {}).items())},
    )
    compare(
        "verified_ids",
        sorted(r["id"] for r in rows if r["verification_status"] == "verified"),
        sorted(facts.get("verified_ids") or []),
    )
    compare(
        "tradition_values",
        len({r["tradition"] for r in rows}),
        facts.get("tradition_values"),
    )
    compare(
        "unresolved_glyph_ids",
        sorted(r["id"] for r in rows if r.get("has_unresolved_glyph") == "true"),
        sorted(facts.get("unresolved_glyph_ids") or []),
    )
    compare(
        "unresolved_source_link_count",
        sum(1 for r in rows if not (r.get("source_id") or "").strip()),
        facts.get("unresolved_source_link_count"),
    )
    compare(
        "item_type_counts",
        {k: v for k, v in sorted(Counter(r.get("item_type", "") for r in rows).items())},
        {k: v for k, v in sorted((facts.get("item_type_counts") or {}).items())},
    )
    compare("source_rows", len(src_rows), facts.get("source_rows"))
    print(f"documented corpus facts re-derived from the data: {len(rows)} rows checked")


def check_projection_totality(vocabularies, path):
    """Every research state must appear in the documented projection rule."""
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    marker = "## Projection into the current"
    start = text.find(marker)
    if start < 0:
        fail(f"{path.name} no longer has a projection section")
        return
    section = text[start:]
    rule_rows = "\n".join(
        line for line in section.splitlines() if line.strip().startswith("| research state")
    )
    if not rule_rows:
        fail(f"{path.name} projection section has no 'research state' mapping row")
        return
    for state in sorted(vocabularies.get("research", set())):
        if state not in rule_rows:
            fail(f"research state {state!r} is not covered by the documented projection rule")


def main():
    transitions, vocabularies = parse_state_model(STATE_MODEL)
    required, methods = parse_required_envelope_fields(ENVELOPE)

    if not FIXTURES.exists():
        fail(f"missing {FIXTURES.relative_to(ROOT)}")
        print("\nRESULT: FAIL")
        return sys.exit(1)

    try:
        fixture = json.loads(FIXTURES.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        fail(f"{FIXTURES.relative_to(ROOT)} is not valid JSON: {exc}")
        print("\nRESULT: FAIL")
        return sys.exit(1)
    if not isinstance(fixture, dict):
        fail(f"{FIXTURES.relative_to(ROOT)} must contain a JSON object")
        print("\nRESULT: FAIL")
        return sys.exit(1)

    template = fixture.get("envelope_template", {})
    scenarios = fixture.get("scenarios", [])

    # The doc's required-field table and the fixture's template must agree exactly,
    # in both directions: a field dropped from (or added to) either side fails.
    doc_required = set(required)
    template_fields = set(template)
    if doc_required != template_fields:
        fail(
            "CANDIDATE_ENVELOPE.md required fields and the fixture template disagree: "
            f"doc-only={sorted(doc_required - template_fields)} "
            f"template-only={sorted(template_fields - doc_required)}"
        )

    # The aggregate rule implemented here must equal the one written in the doc.
    doc_rule = parse_aggregate_rule(VERIFICATION_CONTRACT)
    if doc_rule and doc_rule != AGGREGATE_RULE:
        fail(
            "VERIFICATION_CONTRACT.md aggregate rule and the checker's rule disagree: "
            f"doc={doc_rule} checker={AGGREGATE_RULE}"
        )

    # Every transition's authority must be asserted, not just the operator ones.
    expected_authorities = fixture.get("expected_authorities", {})
    for tid, tr in transitions.items():
        if tid not in expected_authorities:
            fail(f"{tid} has no declared authority in the fixture (expected_authorities)")
        elif expected_authorities[tid] != tr["authority"]:
            fail(
                f"{tid} authority in STATE_MODEL.md is {tr['authority']!r} but the fixture "
                f"declares {expected_authorities[tid]!r}"
            )
    for tid in expected_authorities:
        if tid not in transitions:
            fail(f"fixture declares authority for unknown transition {tid}")

    print(f"parsed {len(transitions)} transitions, {len(required)} required envelope fields, {len(scenarios)} scenarios")
    print(f"vocabularies: " + "; ".join(f"{d}={len(v)}" for d, v in sorted(vocabularies.items())))
    print(f"authorities asserted: {len(expected_authorities)}/{len(transitions)} transitions")

    # The template itself must be a conforming envelope (otherwise an invalid value in it
    # would be invisible whenever every scenario overrides that field).
    template_probe = dict(template)
    template_probe["id"] = "<envelope_template>"
    template_probe["start"] = {k: template.get(k) for k in INTAKE_STATES}
    check_envelope(template_probe, template, required, methods)

    seen_cases = []
    seen_gates = set()
    for scenario in scenarios:
        envelope = dict(template)
        envelope.update(scenario.get("envelope_overrides", {}))
        check_envelope(scenario, envelope, required, methods)
        check_walkthrough(scenario, transitions, vocabularies)
        seen_cases.append(scenario.get("canonical_case"))
        if scenario.get("gate_requirement") and scenario["gate_requirement"] != "none":
            seen_gates.add(scenario["gate_requirement"])

    missing_cases = [c for c in CANONICAL_CASES if c not in seen_cases]
    if missing_cases:
        fail(f"canonical test cases not covered by any scenario: {missing_cases}")
    counted = [c for c in seen_cases if c]
    dupes = [c for c in counted if counted.count(c) > 1]
    if dupes:
        fail(f"canonical test cases covered more than once: {sorted(set(dupes))}")

    for gate in GATE_A_KINDS:
        if gate not in seen_gates:
            fail(f"Gate A requirement {gate!r} is not exercised by any scenario")
    declared = set(fixture.get("gate_requirement_coverage", []) or [])
    if declared and declared != GATE_A_KINDS:
        fail(
            "fixture gate_requirement_coverage disagrees with the Gate A kinds the checker "
            f"asserts: fixture={sorted(declared)} checker={sorted(GATE_A_KINDS)}"
        )

    # Every promotion transition must have a way back out.
    for tid, tr in transitions.items():
        if tr["dimension"] != "corpus" or tr["to"] not in PROMOTED_CORPUS_STATES:
            continue
        escapes = [
            other
            for other, otr in transitions.items()
            if otr["dimension"] == "corpus"
            and otr["from"] == tr["to"]
            and otr["to"] not in PROMOTED_CORPUS_STATES
        ]
        if not escapes:
            fail(
                f"{tid} promotes corpus into {tr['to']!r} with no transition back out "
                f"(a reversed curation decision would strand the record)"
            )

    check_documented_facts(fixture.get("documented_csv_facts", {}))
    check_projection_totality(vocabularies, STATE_MODEL)

    for doc_key in ("envelope_doc", "state_model_doc", "verification_contract_doc"):
        doc = ROOT / fixture[doc_key]
        if not doc.exists():
            fail(f"fixture references missing doc {fixture[doc_key]}")

    print()
    if FAILURES:
        print(f"RESULT: FAIL ({len(FAILURES)} problem(s))")
        return sys.exit(1)
    print("RESULT: PASS (transition chains simulate, claim aggregates agree, envelopes conform)")
    return sys.exit(0)


if __name__ == "__main__":
    main()
