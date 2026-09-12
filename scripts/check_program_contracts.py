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

It deliberately does NOT read quotes.csv / sources.csv, and does not import or
exercise any W1 runtime behaviour -- W1 is not started.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "docs" / "program"
STATE_MODEL = PROGRAM / "STATE_MODEL.md"
ENVELOPE = PROGRAM / "CANDIDATE_ENVELOPE.md"
FIXTURES = PROGRAM / "fixtures" / "w0_scenarios.json"

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
            methods = set(tokens(parts[1]))
    return required, methods


def aggregate_research_state(claims):
    """Rule from VERIFICATION_CONTRACT.md."""
    statuses = [c["status"] for c in claims]
    if not statuses:
        return "not_started"
    if "unverifiable" in statuses:
        return "unverifiable"
    if "disputed" in statuses:
        return "disputed"
    if "needs_more_evidence" in statuses:
        return "needs_more_evidence"
    if "in_research" in statuses:
        return "in_research"
    if "not_started" in statuses:
        return "not_started"
    return "verified"


def check_envelope(scenario, envelope, required, methods):
    sid = scenario["id"]
    for field in required:
        if field not in envelope:
            fail(f"{sid}: envelope missing required field {field!r}")
        elif not isinstance(envelope[field], list) and str(envelope[field]).strip() == "":
            fail(f"{sid}: envelope field {field!r} is empty (use a sentinel: unknown/und/none)")
    if methods and envelope.get("capture_method") not in methods:
        fail(f"{sid}: capture_method {envelope.get('capture_method')!r} not in {sorted(methods)}")
    for key, expected in INTAKE_STATES.items():
        if envelope.get(key) != expected:
            fail(f"{sid}: envelope {key} must be {expected!r} at intake, got {envelope.get(key)!r}")
        if scenario["start"].get(key) != expected:
            fail(f"{sid}: scenario.start {key} must be {expected!r} at intake, got {scenario['start'].get(key)!r}")
    if not str(envelope.get("normalization_notes", "")).strip():
        fail(f"{sid}: normalization_notes must assert what normalization did (or 'identical to capture')")
    for hint in envelope.get("duplicate_hints", []):
        if hint.get("kind") not in HINT_KINDS:
            fail(f"{sid}: duplicate hint kind {hint.get('kind')!r} not in {sorted(HINT_KINDS)}")
        if not str(hint.get("target", "")).strip() or not str(hint.get("basis", "")).strip():
            fail(f"{sid}: duplicate hint needs non-empty target and basis")


def check_walkthrough(scenario, transitions, vocabularies):
    sid = scenario["id"]
    state = dict(scenario["start"])
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

    if state != scenario["end"]:
        fail(f"{sid}: chain ends in {state} but scenario.end declares {scenario['end']}")

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


def main():
    transitions, vocabularies = parse_state_model(STATE_MODEL)
    required, methods = parse_required_envelope_fields(ENVELOPE)

    if not FIXTURES.exists():
        fail(f"missing {FIXTURES.relative_to(ROOT)}")
        print("\nRESULT: FAIL")
        return sys.exit(1)

    fixture = json.loads(FIXTURES.read_text(encoding="utf-8"))
    template = fixture.get("envelope_template", {})
    scenarios = fixture.get("scenarios", [])

    print(f"parsed {len(transitions)} transitions, {len(required)} required envelope fields, {len(scenarios)} scenarios")
    print(f"vocabularies: " + "; ".join(f"{d}={len(v)}" for d, v in sorted(vocabularies.items())))

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
    dupes = [c for c in seen_cases if seen_cases.count(c) > 1]
    if dupes:
        fail(f"canonical test cases covered more than once: {sorted(set(dupes))}")

    for gate in fixture.get("gate_requirement_coverage", []):
        if gate not in seen_gates:
            fail(f"Gate A requirement {gate!r} is not exercised by any scenario")

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
