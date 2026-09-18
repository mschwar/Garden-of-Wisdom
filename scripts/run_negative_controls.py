#!/usr/bin/env python3
"""Machine-check the checkers' negative controls.

Usage:
    python3 scripts/run_negative_controls.py              # self-tests + anchor check + every control
    python3 scripts/run_negative_controls.py --check       # anchors only (no checker is run)
    python3 scripts/run_negative_controls.py --list
    python3 scripts/run_negative_controls.py --checker scripts/check_pages_contract.py

Why this exists
---------------
Every checker in this repo is supposed to come with a table of *negative controls*: one
mutation per guard, which must turn the run red with that guard's own ``FAIL:`` line. Until
this script, those tables lived only in prose in ``GARDEN_*_HANDOFF.md`` and were produced by
a throwaway harness in ``/tmp`` that was deleted when the unit ended (issue #43). Two things
followed:

  * the evidence was not independently verifiable -- foreign QA on the Pages guard unit
    reported that it could not verify the author's control table without reading the author's
    private harness, which was out of bounds for that pass;
  * a *vacuous* check was undetectable -- ``check_pages_contract.py``'s ``EXPECTED_CHECKS``
    count guard fails when a check is **deleted**, but foreign QA mutation ``p36`` showed that
    gutting a check body to ``return None`` while keeping its registration leaves the run
    green. Counting registrations is not proving falsifiability.

So the harness is now a first-class script: the mutation table is committed, anyone can run
it, CI runs it on every PR and push to ``main``, and a mutation that no longer turns its
checker red is reported as a **coverage gap** instead of being quietly dropped.

What it does
------------
  1. copies this repo's working tree to a throwaway directory (never mutating the working
     tree -- asserted, and the copy excludes ``.git`` / ``.venv`` / ``__pycache__``);
  2. for each control: asserts the control's anchor occurs **exactly once** in its target
     file, applies one substitution, runs the checker from inside the copy, then restores the
     file's pristine bytes;
  3. asserts the **first** ``FAIL:`` line the checker prints is the one the control aimed at;
  4. reports a control that stayed green as a COVERAGE GAP and a GREEN-expectation control
     that went red as a FALSE POSITIVE, and fails the run for either.

What it can NOT do (measured limits, stated rather than papered over)
--------------------------------------------------------------------
  * it proves a *mutation* is detected, never that a check is *complete*: a guard with an
    unmodelled bypass still passes. The control table is the model of "what could go wrong",
    so its coverage is exactly as good as the mutations a human wrote;
  * ``EXPECTED_CONTROLS`` catches a deleted control registration the same way
    ``check_pages_contract.py``'s count guard catches a deleted check -- it is a floor, not a
    proof (that distinction is the whole point of issue #43);
  * a control is a single exact-string substitution: controls that need a file deleted,
    renamed, or a multi-file edit are out of the table's vocabulary. Adding one means adding a
    mutation kind to ``_apply_mutation``, and the self-tests below are where that kind must
    first be proven detectable;
  * the browsers' own negative controls for ``scripts/smoke_quote_browser.py`` run a real
    Chromium; if the browser is not installed the checker is reported as SKIPPED, and in CI
    (``CI`` set, or ``--require-all``) a skip is an error rather than a quiet reduction in
    coverage.

The harness has its own controls
--------------------------------
``run_self_tests`` builds a synthetic mini-repo whose fake checker can be broken in exactly
the five ways this harness must recognize -- a fired control, a green mutation (coverage gap),
a wrong first ``FAIL:`` line (masked), an anchor that no longer exists (rot), and a false
positive -- and asserts the harness assigns each the right verdict. Four more self-tests cover
the table's own hygiene: an empty table, a checker with no controls, a deleted registration, and
the rule that a narrowed ``--checker`` selection is never validated against the whole-table
count guard. A harness that can no longer detect a green mutation is the same defect one level
up, so those self-tests run on every invocation and are counted in the result line.

Exits 0 with ``RESULT: PASS`` / non-zero with ``RESULT: FAIL`` and one ``FAIL:`` line per
broken control, in the same shape as every other checker here. Stdlib only; the only write is
the throwaway copy.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories never copied into the throwaway tree: version control, the test-only
# virtualenv, and bytecode caches (which would otherwise be stale copies of the real ones).
COPY_IGNORE = shutil.ignore_patterns(".git", ".venv", "node_modules", "__pycache__", "*.pyc")

# A checker that hangs must not hang this harness. The slowest checker here
# (check_garden_e2e.py, validate_quotes.py) runs in ~22s; 300s is a huge margin.
CHECK_TIMEOUT_SECONDS = 300

# The count guard. Deleting a control registration (or an entire checker's block) fails the
# run, exactly as deleting a check fails check_pages_contract.py. It is a floor, not a proof:
# a control whose mutation is edited to a no-op is caught by the COVERAGE GAP verdict above,
# which is the real guard.
EXPECTED_CONTROLS = 52
EXPECTED_SELF_TESTS = 9


@dataclass(frozen=True)
class Mutation:
    """One negative control: a single exact-string substitution and the FAIL line it must aim at.

    ``expect_fail`` is the exact first ``FAIL:`` line the mutated checker must print. ``None``
    means the opposite expectation: the edit is contract-preserving and the checker must stay
    GREEN (a control set needs a must-stay-green half, or it only proves a check *can* fail and
    never that it accepts a legitimate edit).
    """

    control_id: str
    description: str
    path: str
    anchor: str
    replacement: str
    expect_fail: str | None


@dataclass(frozen=True)
class Checker:
    """One checker and the controls that must be able to turn it red."""

    script: str
    controls: tuple[Mutation, ...]
    # "venv" -> the repo's .venv interpreter when present (playwright lives there), else
    # the interpreter running this script.
    interpreter: str | None = None
    # Named environment capabilities the controls need; an unmet requirement SKIPs the
    # checker's controls and says why, rather than reporting an unearned PASS.
    requires: tuple[str, ...] = ()


# --------------------------------------------------------------------------- the table
#
# Every entry was authored by running the mutation in a throwaway copy first and pasting the
# observed first FAIL: line, then re-verified through this harness. The anchor must occur
# exactly once in the target file; if the file is edited so that it no longer does, the run
# says so ("anchor ... occurs 0 times") instead of silently skipping the control.
CHECKERS: tuple[Checker, ...] = (
    Checker(
        "scripts/validate_quotes.py",
        (
            Mutation(
                "c1", "a duplicated primary key (row 344 rekeyed onto an existing id)",
                "quotes.csv", "344,", "1,",
                "FAIL: duplicate ids: ['1']",
            ),
            Mutation(
                "c2", "a dangling source link: sources.csv renames the id row 344 cites",
                "sources.csv", "32,Modern Mayan Oral Tradition", "999,Modern Mayan Oral Tradition",
                "FAIL: quotes reference source_id not present in sources.csv: ['344']",
            ),
            Mutation(
                "c3", "a controlled-vocabulary regression: row 1's item_type leaves the enum",
                "quotes.csv",
                '"kindness, speech, influence, heart",unknown,unverified,12,true',
                '"kindness, speech, influence, heart",unknwon,unverified,12,true',
                "FAIL: rows with invalid item_type: ['1']",
            ),
            Mutation(
                "c4", "the near-duplicate score reverts to one directional difflib ratio (issue #31)",
                "scripts/validate_quotes.py",
                "    forward = difflib.SequenceMatcher(None, a, b).ratio()\n"
                "    backward = difflib.SequenceMatcher(None, b, a).ratio()\n"
                "    return (forward + backward) / 2.0",
                "    forward = difflib.SequenceMatcher(None, a, b).ratio()\n"
                "    return forward",
                "FAIL: near-duplicate detection is row-order dependent: pairs/numbers only in "
                "file order [(66, 67, 'same specific citation'), (87, 187, 'text similarity "
                "0.64'), (113, 114, 'text similarity 0.69')], only in reversed order [(66, 67, "
                "'same specific citation; text similarity 0.61'), (113, 114, 'text similarity "
                "0.67'), (189, 216, 'text similarity 0.60')]",
            ),
            Mutation(
                "c5", "the imported locator rule drifts: citation_specificity() always 'generic'",
                "scripts/garden_normalize.py",
                '    return "specific" if LOCATOR_PATTERN.search(value) else "generic"',
                '    return "generic"',
                "FAIL: citation rule drift: citation_specificity('Gita 2.47') is 'generic', but "
                "this report's ruling assumes 'specific'",
            ),
            Mutation(
                "c6", "the sweep is narrowed back to per-tradition groups (issue #34's reversion)",
                "scripts/validate_quotes.py",
                "    groups = [rows]",
                '    groups = [[r for r in rows if r["tradition"] == t] for t in '
                'sorted({r["tradition"] for r in rows})]',
                "FAIL: the near-duplicate sweep is not corpus-wide: pairs/numbers only in the "
                "corpus-wide scan [(39, 53, 'text similarity 0.82'), (50, 318, 'text similarity "
                "0.71'), (78, 173, 'text similarity 0.62'), (87, 187, 'text similarity 0.61'), "
                "(175, 332, 'text similarity 0.61')], only in the reported sweep []",
            ),
        ),
    ),
    Checker(
        "scripts/check_program_contracts.py",
        (
            Mutation(
                "pc1", "S2's wording claim demoted to unverifiable: the record aggregate disagrees",
                "docs/program/fixtures/w0_scenarios.json",
                '{"claim": "wording", "status": "verified", "evidence": [{"witness": "Official '
                "Bahá’í Writings, Gleanings from the Writings of Bahá’u’lláh (bahai.org "
                'authoritative text)"',
                '{"claim": "wording", "status": "unverifiable", "evidence": [{"witness": '
                '"Official Bahá’í Writings, Gleanings from the Writings of Bahá’u’lláh '
                '(bahai.org authoritative text)"',
                "FAIL: S2: record research_state 'verified' disagrees with the aggregate of its "
                "claims ('unverifiable')",
            ),
            Mutation(
                "pc2", "S3's walkthrough names a transition the STATE_MODEL table does not define",
                "docs/program/fixtures/w0_scenarios.json",
                '"transitions": ["T-C1", "T-P1", "T-R1", "T-R5", "T-P2", "T-W1", "T-W2", "T-W6"],',
                '"transitions": ["T-C1", "T-P1", "T-R1", "T-R99", "T-P2", "T-W1", "T-W2", "T-W6"],',
                "FAIL: S3: transition T-R99 (step 4) is not in the STATE_MODEL table",
            ),
            Mutation(
                "pc3", "the fixture template loses a required envelope field (capture_id)",
                "docs/program/fixtures/w0_scenarios.json",
                '"garden.candidate-envelope/1",\n'
                '    "capture_id": "cap-2026-09-12-0001",\n'
                '    "captured_text": "PLACEHOLDER",\n',
                '"garden.candidate-envelope/1",\n'
                '    "captured_text": "PLACEHOLDER",\n',
                "FAIL: CANDIDATE_ENVELOPE.md required fields and the fixture template disagree: "
                "doc-only=['capture_id'] template-only=[]",
            ),
        ),
    ),
    Checker(
        "scripts/validate_homepage_preview_export.py",
        (
            Mutation(
                "h1", "an exported item's text drifts from the frozen quotes.csv wording",
                "exports/bahai-homepage-preview/v1/collection.json",
                "The earth is but one country, and mankind its citizens.",
                "The earth is but one country, and humankind its citizens.",
                "FAIL: items[0]: text does not match quotes.csv id 3",
            ),
            Mutation(
                "h2", "exact scripture is re-typed as a paraphrase (item_type excerpt -> paraphrase)",
                "exports/bahai-homepage-preview/v1/collection.json",
                '"text": "The earth is but one country, and mankind its citizens.",\n'
                '      "author": "Bahá’u’lláh",\n'
                '      "source_ref": "Gleanings from the Writings of Bahá’u’lláh, CXVII",\n'
                '      "source_url": "https://www.bahai.org/library/authoritative-texts/bahaullah/'
                'gleanings-writings-bahaullah/6",\n'
                '      "item_type": "excerpt",',
                '"text": "The earth is but one country, and mankind its citizens.",\n'
                '      "author": "Bahá’u’lláh",\n'
                '      "source_ref": "Gleanings from the Writings of Bahá’u’lláh, CXVII",\n'
                '      "source_url": "https://www.bahai.org/library/authoritative-texts/bahaullah/'
                'gleanings-writings-bahaullah/6",\n'
                '      "item_type": "paraphrase",',
                "FAIL: items[0]: paraphrase may not be emitted as exact scripture",
            ),
        ),
    ),
    Checker(
        "scripts/check_pages_contract.py",
        (
            Mutation(
                "p1", "the upload action major regresses to v3, the one that published ./.gitignore",
                ".github/workflows/pages.yml",
                "uses: actions/upload-pages-artifact@v5",
                "uses: actions/upload-pages-artifact@v3",
                "FAIL: the upload action major excludes top-level hidden files -- "
                "actions/upload-pages-artifact@3 is below the minimum verified major 4 -- its tar "
                "invocation does NOT exclude top-level dotfiles, which published ./.gitignore "
                "(issue #23)",
            ),
            Mutation(
                "p2", "the artifact is rooted at browser/, so ../quotes.csv 404s and the page is empty",
                ".github/workflows/pages.yml",
                "path: '.'",
                "path: 'browser/'",
                "FAIL: the uploaded path is the repo root ('.') -- the upload path is "
                "\"'browser/'\", not '.': browser/index.html fetches ../quotes.csv, so a "
                "differently-rooted artifact renders 0 quotes",
            ),
            Mutation(
                "p3", "include-hidden-files is switched on, republishing top-level dotfiles",
                ".github/workflows/pages.yml",
                "          path: '.'",
                "          path: '.'\n          include-hidden-files: true",
                "FAIL: the upload step does not include hidden files -- include-hidden-files is "
                "'true': top-level dotfiles would be published (issue #23)",
            ),
            Mutation(
                "p4", "app.js fetch repointed to the wrong root, old path kept in a // comment",
                "browser/app.js",
                '    fetch("../quotes.csv").then((r) => r.text()),',
                '    fetch("./quotes.csv").then((r) => r.text()), // fetch("../quotes.csv")',
                "FAIL: browser/app.js still fetches ../quotes.csv and ../sources.csv -- "
                "browser/app.js no longer fetches '../quotes.csv'; if the fetch changed, the "
                "artifact layout requirement changed with it",
            ),
        ),
    ),
    Checker(
        "scripts/smoke_quote_browser.py",
        (
            Mutation(
                "sm1", "matchesSearch() stops narrowing: every search returns all 324 rows",
                "browser/app.js",
                "  return haystack.includes(term.toLowerCase());",
                "  return true;",
                "FAIL: search 'Dhammapada': page never showed 29 quotes within 15000ms "
                "(filtered-count='324')",
            ),
            Mutation(
                "sm2", "the card/table empty state loses its message",
                "browser/app.js",
                'const EMPTY_STATE_MESSAGE = "No matching quotes. Adjust the filters or search.";',
                'const EMPTY_STATE_MESSAGE = "Nothing to see here.";',
                "FAIL: empty result (#filter-tradition = 'Akan (Ghana)' + search 'Dhammapada'): "
                "empty-state text was 'Nothing to see here.', expected it to contain 'No matching "
                "quotes.'",
            ),
        ),
        interpreter="venv",
        requires=("playwright",),
    ),
    Checker(
        "scripts/check_garden_store.py",
        (
            Mutation(
                "g1", "capture immutability: the UPDATE trigger no longer aborts",
                "scripts/garden_store.py",
                "RAISE(ABORT, 'captures is immutable: UPDATE rejected')",
                "1",
                "FAIL: captures accepted UPDATE: captures are not immutable",
            ),
            Mutation(
                "g2", "the research_state CHECK constraint is dropped (W1.1 review's finding)",
                "scripts/garden_store.py",
                "CHECK(research_state IN ({_sql_list(RESEARCH_STATES)}))",
                "CHECK(1)",
                "FAIL: the SQL layer accepted research_state = 'maybe' (outside STATE_MODEL.md)",
            ),
            Mutation(
                "g3", "a migration id is renamed: the ledger no longer matches the schema",
                "scripts/garden_store.py",
                '"0001_create_core"',
                '"0001_create_core_v2"',
                "FAIL: create-from-empty applied migration ['0001_create_core_v2', "
                "'0002_unverifiable_ledger', '0003_legacy_batch_capture'] into an empty "
                "directory",
            ),
            Mutation(
                "g4", "the captures UPDATE trigger still aborts but its RAISE message no longer "
                "names the invariant (issue #45 gap 5)",
                "scripts/garden_store.py",
                "RAISE(ABORT, 'captures is immutable: UPDATE rejected')",
                "RAISE(ABORT, 'captures is immutable (trigger)')",
                "FAIL: the UPDATE trigger's own RAISE message names the invariant it enforces "
                "-- 'captures is immutable (trigger)' does not contain 'captures is immutable: "
                "UPDATE rejected'",
            ),
        ),
    ),
    Checker(
        "scripts/check_garden_envelope.py",
        (
            Mutation(
                "e1", "the serializer loses canonical determinism (sort_keys is load-bearing)",
                "scripts/garden_envelope.py",
                "sort_keys=True,",
                "sort_keys=False,",
                "FAIL: key insertion order cannot change the serialized bytes (sort_keys is "
                "load-bearing)",
            ),
            Mutation(
                "e2", "rule 1 stops checking the intake schema version",
                "scripts/garden_envelope.py",
                "version != SCHEMA_KEY",
                "False",
                "FAIL: fixture 'wrong-intake-schema-version' reports exactly rule-1 -- reported []",
            ),
            Mutation(
                "e3", "rule 2 stops refusing an empty captured_text",
                "scripts/garden_envelope.py",
                'if isinstance(text, str) and text == "":',
                'if isinstance(text, str) and False:',
                "FAIL: fixture 'empty-captured-text' reports exactly rule-2 -- reported []",
            ),
        ),
    ),
    Checker(
        "scripts/check_garden_submit.py",
        (
            Mutation(
                "t1", "the capture is trimmed instead of stored byte-for-byte",
                "scripts/garden_submit.py",
                'return raw.decode("utf-8")',
                'return raw.decode("utf-8").strip()',
                "FAIL: captured_text is byte-identical to the submitted file (verified against "
                "the file bytes) -- 75 vs 78 bytes",
            ),
            Mutation(
                "t2", "the no-normalization-without-a-note refusal is dropped",
                "scripts/garden_submit.py",
                "if differing:",
                "if False and differing:",
                "FAIL: --candidate-text differing with no note is refused (exit 0, RESULT: FAIL)",
            ),
        ),
    ),
    Checker(
        "scripts/check_garden_normalize.py",
        (
            Mutation(
                "n1", "the similarity collapses to one directional ratio (asymmetric basis)",
                "scripts/garden_normalize.py",
                "    return (forward + backward) / 2",
                "    return forward",
                "FAIL: the similarity of a pair is symmetric (the same number reaches both "
                "candidates' hints)",
            ),
            Mutation(
                "n2", "a shared generic label counts as a specific citation again (ruling 2)",
                "scripts/garden_normalize.py",
                "    same_specific_citation = shared and specific",
                "    same_specific_citation = shared",
                "FAIL: the legacy heuristic flags rows 319 ~ 331 on the shared label 'Oral "
                "Tradition', and W1.4 emits no same-reference/same-passage hint for them -- "
                "['same-reference']",
            ),
            Mutation(
                "n3", "the hint rebuild accumulates instead of replacing (the DELETE is lost)",
                "scripts/garden_store.py",
                '        self.conn.execute("DELETE FROM duplicate_hints WHERE candidate_id = ?", '
                "(candidate_id,))\n"
                "        self.conn.commit()\n"
                "        return self.add_duplicate_hints(candidate_id, hints)",
                "        self.conn.commit()\n"
                "        return self.add_duplicate_hints(candidate_id, hints)",
                "FAIL: rebuilding every hint exports byte-identical text (derived, deterministic, "
                "not appended)",
            ),
            Mutation(
                "n4", "the comparison view stops case-folding (issue #45 gap 1)",
                "scripts/garden_normalize.py",
                '        "text": normalize_text(row["candidate_text"]).casefold(),',
                '        "text": normalize_text(row["candidate_text"]),',
                "FAIL: two candidates whose text differs only in letter case still get an "
                "exact-text hint -- the comparison view is case-folded, as "
                "W1_4_NORMALIZATION_HINTS.md documents -- []",
            ),
        ),
    ),
    Checker(
        "scripts/check_garden_review.py",
        (
            Mutation(
                "r1", "acceptance no longer fires the required T-P1 corpus follow-on",
                "scripts/garden_store.py",
                'to_c == "accepted" and from_p == "candidate_only"',
                'to_c == "accepted" and from_p == "eligible"',
                "FAIL: accept: cand-t01 recorded exactly ['T-C1', 'T-P1'] -- ['T-C1']",
            ),
            Mutation(
                "r2", "curate's OWN required-reason guard is disabled (the backstop remains)",
                "scripts/garden_store.py",
                '_require(bool(reason), "every curation decision must carry a reason (required, '
                'never omitted)")',
                '_require(True, "every curation decision must carry a reason (required, never '
                'omitted)")',
                "FAIL: the refusal for an empty reason came from curate's OWN guard ('every "
                "curation decision must carry a reason') not a shared/backstop guard -- a "
                "decision must carry a reason",
            ),
            Mutation(
                "r3", "a curation action writes research state (invariant 5)",
                "scripts/garden_store.py",
                '"UPDATE candidates SET curation_state = ?, corpus_state = ? WHERE candidate_id '
                '= ?",',
                '"UPDATE candidates SET curation_state = ?, corpus_state = ?, research_state = '
                "'in_research' WHERE candidate_id = ?\",",
                "FAIL: accept: cand-t01 research_state stayed not_started -- in_research",
            ),
            Mutation(
                "r4", "the corpus follow-on is filed under the curation action vocabulary "
                "(issue #45 gap 2)",
                "scripts/garden_store.py",
                '                        action="corpus-follow-on",',
                '                        action="curation-decision",',
                "FAIL: every curation-dimension row is recorded as 'curation-decision' and every "
                "corpus-dimension follow-on row as 'corpus-follow-on'",
            ),
        ),
    ),
    Checker(
        "scripts/check_garden_e2e.py",
        (
            Mutation(
                "x1", "the withdrawal path bypasses its state write, stranding a dimension",
                "scripts/garden_store.py",
                'to_p = "candidate_only"',
                'to_p = "eligible"',
                "FAIL: the reversal strands no dimension: curation=rejected, "
                "corpus=candidate_only -- curation=rejected corpus=eligible",
            ),
            Mutation(
                "x2", "the decision log stops being append-only (trigger narrowed to seq)",
                "scripts/garden_store.py",
                "BEFORE UPDATE ON decisions",
                "BEFORE UPDATE OF seq ON decisions",
                "FAIL: decisions accepted UPDATE: the log is not append-only",
            ),
            Mutation(
                "x3", "the T-P7 audit row records the wrong to_state while the live column stays "
                "right (issue #45 gap 3)",
                "scripts/garden_store.py",
                '                follow.append(("corpus", "eligible", "candidate_only", "T-P7", '
                '"operator"))',
                '                follow.append(("corpus", "eligible", "eligible", "T-P7", '
                '"operator"))',
                "FAIL: the T-P7 audit row itself records to_state=candidate_only (not just the "
                "live corpus_state) -- to_state='eligible'",
            ),
        ),
    ),
    Checker(
        "scripts/check_garden_legacy_batch.py",
        (
            Mutation(
                "b1", "the conflicting-membership guard is disabled: a partial re-seed is accepted",
                "scripts/garden_store.py",
                "            if existing_members != cleaned_sorted:\n"
                "                raise StoreError(\n"
                '                    "legacy batch membership already exists with a different id set "\n'
                '                    f"(have {len(existing_members)}, asked {len(cleaned_sorted)}); "\n'
                '                    "refusing a silent overwrite"\n'
                "                )\n",
                "            if False:\n"
                "                raise StoreError('unreachable')\n",
                "FAIL: a conflicting membership set was accepted",
            ),
            Mutation(
                "b2", "seed also writes a candidate, breaking D4's no-candidates ruling",
                "scripts/garden_store.py",
                "            self.conn.executemany(\n"
                '                "INSERT INTO legacy_batch_membership (legacy_row_id, capture_id) VALUES (?, ?)",\n'
                "                [(row_id, LEGACY_BATCH_CAPTURE_ID) for row_id in cleaned_sorted],\n"
                "            )\n"
                "            self.conn.commit()\n",
                "            self.conn.executemany(\n"
                '                "INSERT INTO legacy_batch_membership (legacy_row_id, capture_id) VALUES (?, ?)",\n'
                "                [(row_id, LEGACY_BATCH_CAPTURE_ID) for row_id in cleaned_sorted],\n"
                "            )\n"
                "            self.conn.execute(\n"
                '                "INSERT INTO candidates (candidate_id, candidate_text, candidate_author, "\n'
                '                "candidate_source_ref, normalization_notes, intake_schema_version, "\n'
                '                "external_id, curation_state, research_state, corpus_state, work_state, "\n'
                '                "created_at) VALUES (\'cand-d4-leak\', \'leak\', \'unknown\', \'none\', "\n'
                '                "\'identical to capture\', \'garden.candidate-envelope/1\', NULL, "\n'
                '                "\'new\', \'not_started\', \'candidate_only\', \'queued\', "\n'
                "                \"'2026-09-11T00:00:00-06:00')\")\n"
                "            self.conn.commit()\n",
                "FAIL: seed creates no candidates and no candidate_captures links -- "
                "{'captures': 1, 'candidates': 1, 'candidate_captures': 0, 'duplicate_hints': 0, "
                "'decisions': 0, 'legacy_verification': 0, 'legacy_batch_membership': 324}",
            ),
            Mutation(
                "b3", "the export-section-order assertion drops the membership section",
                "scripts/check_garden_legacy_batch.py",
                '            "[legacy_verification]",\n'
                '            "[legacy_batch_membership]",\n',
                '            "[legacy_verification]",\n',
                "FAIL: the export sections appear in the documented fixed order -- "
                "['[meta]', '[captures]', '[candidate_captures]', '[candidates]', "
                "'[duplicate_hints]', '[decisions]', '[legacy_verification]', "
                "'[legacy_batch_membership]']",
            ),
        ),
    ),
    Checker(
        "scripts/check_garden_ledger.py",
        (
            Mutation(
                "l1", "the re-adjudication guard is disabled: a marked row can be re-marked",
                "scripts/garden_store.py",
                "        if row is not None:\n",
                "        if False:\n",
                "FAIL: a duplicate mark is refused by the explicit re-adjudication guard -- "
                "unverifiable adjudication for legacy row '30' rejected: UNIQUE constraint "
                "failed: legacy_verification.legacy_row_id",
            ),
            Mutation(
                "l2", "the ledger row is written without its research audit row (D3 §2)",
                "scripts/garden_store.py",
                "            seq = self._insert_decision(\n"
                '                subject_kind="research_case",\n'
                "                subject_id=legacy_row_id,\n"
                '                dimension="research",\n'
                '                action="research-adjudication",\n'
                "                transition_id=transition_id,\n"
                "                from_state=from_state,\n"
                '                to_state="unverifiable",\n'
                "                actor=decided_by,\n"
                '                actor_kind="operator",\n'
                "                reason=reason,\n"
                "                occurred_at=stamp,\n"
                "            )\n",
                "            seq = None\n",
                "FAIL: mark appends one research audit row (T-R6 from_state derived from the "
                "model) -- []",
            ),
            Mutation(
                "l3", "reopen no longer requires the row to be in the ledger",
                "scripts/garden_store.py",
                "        if row is None:\n"
                "            raise StoreError(\n"
                '                f"legacy row {legacy_row_id!r} is not in the unverifiable '
                'ledger; nothing to reopen"\n'
                "            )\n",
                "        # guard removed\n",
                "FAIL: reopen on a missing row was accepted",
            ),
            Mutation(
                "l4", "quotes.csv's enum is widened by hand: a row leaves the 3-valued "
                "verification_status (issue #45 gap 4, D3's ruling)",
                "quotes.csv",
                '"kindness, speech, influence, heart",unknown,unverified,12,true',
                '"kindness, speech, influence, heart",unknown,unverifiable,12,true',
                "FAIL: issue #45 gap 4: quotes.csv's verification_status stays exactly "
                "['disputed', 'unverified', 'verified'] -- D3 chose the side-car ledger 'instead "
                "of widening the 3-valued quotes.csv enum', and this suite (not just "
                "validate_quotes.py) falsifies that ruling directly -- ['1']",
            ),
        ),
    ),
    Checker(
        "scripts/check_garden_lifecycle.py",
        (
            Mutation(
                "u1", "the mutation invariant is dropped from submit: mirror stays stale",
                "scripts/garden_submit.py",
                "        counts = store.counts()\n"
                "        store.sync_mirror()  # U0.1: a successful mutation must leave the committed mirror current\n",
                "        counts = store.counts()\n",
                "FAIL: 4a. after a successful submit the mirror is current (mutation invariant) -- STALE",
            ),
            Mutation(
                "u2", "the divergence check in bootstrap is disabled",
                "scripts/garden_store.py",
                "        with Store(store_dir) as store:\n"
                "            if store.export_bytes() == mirror.read_bytes():\n"
                "                return \"CURRENT\"\n"
                "        raise StoreError(\n",
                "        with Store(store_dir) as store:\n"
                "            if True:\n"
                "                return \"CURRENT\"\n"
                "        raise StoreError(\n",
                "FAIL: 6a. bootstrap did not refuse a divergent store + mirror",
            ),
            Mutation(
                "u3", "store_status fails to detect a stale mirror",
                "scripts/garden_store.py",
                "    with Store(store_dir) as store:\n"
                "        if store.export_bytes() == mirror.read_bytes():\n"
                "            return \"CURRENT\"\n"
                "    return \"STALE\"\n",
                "    return \"CURRENT\"\n",
                "FAIL: 5a. a store mutated behind the mirror reports STALE",
            ),
        ),
    ),
    Checker(
        "scripts/check_front_door.py",
        (
            Mutation(
                "fd1", "the program README re-asserts that the W1 runtime does not exist (U0.2)",
                "docs/program/README.md",
                "and the W1 runtime all landed:",
                "and no W1 runtime code exists:",
                "FAIL: 22. no front door document makes the stale claim "
                "[w1-runtime-or-store-absent] (docs/program/README.md -> claims the W1 "
                "runtime/store does not exist)",
            ),
            Mutation(
                "fd2", "AGENTS.md stops naming a corpus-program module (U0.2)",
                "AGENTS.md",
                "scripts/garden_review.py {queue",
                "scripts/garden_reveiw.py {queue",
                "FAIL: 19. AGENTS.md names every corpus-program module in scripts/ "
                "(unnamed: garden_review.py)",
            ),
            Mutation(
                "fd3", "docs/queue.md marks a second unit READY (U0.2)",
                "docs/queue.md",
                "— UNAUTHORIZED until Gate U0 accepted",
                "— READY",
                "FAIL: 10. docs/queue.md marks exactly one unit READY in the usability-closure "
                "section (found 2)",
            ),
            Mutation(
                "fd4", "README.md stops routing live status to CURRENT.md (U0.2)",
                "README.md",
                "it lives in\n`docs/program/usability-closure/CURRENT.md` (current gate, the "
                "single READY unit, the last\ncompleted unit, the frontier).",
                "status is tracked in the programme's own current-state pointer.",
                "FAIL: 13. README.md routes live programme status to "
                "docs/program/usability-closure/CURRENT.md",
            ),
            Mutation(
                "fd5", "CURRENT.md loses its last-completed heading (U0.2 structure guard)",
                "docs/program/usability-closure/CURRENT.md",
                "## Last completed unit",
                "## Previously completed unit",
                "FAIL: 2. CURRENT.md keeps its required structure (missing '## Last completed "
                "unit')",
            ),
        ),
    ),
)


# --------------------------------------------------------------------------- verdicts

FIRED = "FIRED"
COVERAGE_GAP = "COVERAGE_GAP"
MASKED = "MASKED"
ROTTEN_ANCHOR = "ROTTEN_ANCHOR"
FALSE_POSITIVE = "FALSE_POSITIVE"
TIMEOUT = "TIMEOUT"
CRASH = "CRASH"
INCONSISTENT = "INCONSISTENT"
GREEN_OK = "GREEN_OK"
SKIPPED = "SKIPPED"

BAD_VERDICTS = (COVERAGE_GAP, MASKED, ROTTEN_ANCHOR, FALSE_POSITIVE, TIMEOUT, CRASH, INCONSISTENT)


def table_problems(checkers: tuple[Checker, ...], expected_controls: int) -> list[str]:
    """Structural problems with the control table itself, independent of any checker run.

    Kept pure so the self-tests can drive it: an empty table that still prints ``RESULT: PASS``
    is exactly the vacuous-check defect this harness exists to end, so the harness refuses to
    pass on a table that checks nothing.
    """
    problems: list[str] = []
    if not checkers:
        problems.append(
            "no checkers are registered: a run that checks nothing must not print PASS")
    for checker in checkers:
        if not checker.controls:
            problems.append(f"{checker.script} has no controls registered")
    total = sum(len(checker.controls) for checker in checkers)
    if total != expected_controls:
        problems.append(
            f"EXPECTED_CONTROLS is {expected_controls} but {total} are registered; re-derive "
            "this harness rather than deleting a control")
    if expected_controls <= 0:
        problems.append("EXPECTED_CONTROLS must be positive, else the count guard is a no-op")
    return problems


def first_fail_line(stdout: str) -> str | None:
    """The first line of checker output whose first token is ``FAIL:``; else None.

    Checkers here print one ``FAIL: <label> -- <detail>`` line per broken check, so this is
    "which guard refused" -- which is the whole evidence a control produces. An indented or
    re-prefixed line still counts (leading whitespace is stripped); a traceback does not.
    """
    for line in stdout.splitlines():
        if line.lstrip().startswith("FAIL:"):
            return line.strip()
    return None


def normalize_paths(text: str, work: Path) -> str:
    """Mask machine-specific absolute paths so a control's expected FAIL line is portable.

    A checker's ``FAIL:`` detail can name the file it read. Inside this harness that file lives
    in a throwaway copy under the system temp dir, whose path differs on every run and between
    macOS and CI's Linux -- so the raw line could never be matched by a committed table. The
    copy root becomes ``<copy>`` and the temp root becomes ``<tmp>`` on both sides of the
    comparison. Order matters: the copy sits under the temp root.
    """
    text = text.replace(str(work), "<copy>")
    text = text.replace(tempfile.gettempdir(), "<tmp>")
    return text


def judge(expect_fail: str | None, exit_code: int, stdout: str) -> tuple[str, str | None, str]:
    """Verdict for one finished checker run. Pure: the self-tests below drive it end to end."""
    first = first_fail_line(stdout)
    if expect_fail is None:
        if exit_code == 0 and first is None:
            return GREEN_OK, None, "stayed green as required"
        return (
            FALSE_POSITIVE,
            first,
            f"a contract-preserving edit must stay GREEN, but the run exited {exit_code} "
            f"with first FAIL: {first!r}",
        )
    if first is None:
        if exit_code == 0:
            return (
                COVERAGE_GAP,
                None,
                "expected a FAIL line but the run stayed GREEN -- this check has no "
                "falsifier (or the mutation no longer models a real break)",
            )
        return (
            CRASH,
            None,
            f"the checker exited {exit_code} without printing any FAIL: line -- a crash is "
            "not the aimed guard refusing",
        )
    if first != expect_fail:
        return (
            MASKED,
            first,
            f"a different check refused first; expected {expect_fail!r}",
        )
    if exit_code == 0:
        return (
            INCONSISTENT,
            first,
            "the aimed FAIL line was printed but the checker exited 0",
        )
    return FIRED, first, "fired as aimed"


# --------------------------------------------------------------------------- machinery

def read_text(path: Path) -> str:
    """Read a file with no newline translation, so a mutation is byte-for-byte reversible."""
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def apply_mutation(text: str, anchor: str, replacement: str) -> tuple[str | None, str | None]:
    """Return (mutated_text, None) or (None, why_not). A non-unique anchor is a hard failure."""
    occurrences = text.count(anchor)
    if occurrences != 1:
        return None, (
            f"anchor occurs {occurrences} time(s) in the target, expected exactly 1 -- the "
            "file changed under the control table; re-derive this control"
        )
    if anchor == replacement:
        return None, "the replacement is identical to the anchor: the mutation is a no-op"
    return text.replace(anchor, replacement), None


def copy_tree(destination: Path) -> None:
    shutil.copytree(REPO_ROOT, destination, ignore=COPY_IGNORE, symlinks=True)


def venv_interpreter() -> str:
    """The repo's .venv interpreter when it exists, else the interpreter running this script."""
    candidate = REPO_ROOT / ".venv" / "bin" / "python"
    return str(candidate) if candidate.exists() else sys.executable


_REQUIREMENT_PROBES = {
    # A real Chromium probe, not just `import playwright`: the package can be installed while
    # the browser binary is not (which is exactly what a first run on a fresh machine hits),
    # and a failed launch inside the smoke test surfaces as an unrelated "unexpected error".
    "playwright": (
        "from playwright.sync_api import sync_playwright\n"
        "with sync_playwright() as p:\n"
        "    p.chromium.launch().close()\n"
    ),
}


def unmet_requirements(interpreter: str, requires: tuple[str, ...]) -> list[str]:
    missing = []
    for requirement in requires:
        probe = _REQUIREMENT_PROBES.get(requirement)
        if probe is None:
            missing.append(f"{requirement} (no probe is defined for this requirement)")
            continue
        try:
            result = subprocess.run(
                [interpreter, "-c", probe],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            missing.append(f"{requirement} ({type(exc).__name__})")
            continue
        if result.returncode != 0:
            missing.append(requirement)
    return missing


@dataclass
class ControlResult:
    checker: str
    control_id: str
    description: str
    verdict: str
    detail: str
    first_fail: str | None
    exit_code: int | None
    seconds: float


def run_checker(checker: Checker, work: Path, timeout: float) -> tuple[int, str, float]:
    interpreter = venv_interpreter() if checker.interpreter == "venv" else sys.executable
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    started = time.monotonic()
    try:
        result = subprocess.run(
            [interpreter, str(work / checker.script)],
            cwd=str(work),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return (-1, f"TIMEOUT after {timeout:g}s", time.monotonic() - started)
    return (result.returncode, (result.stdout or "") + (result.stderr or ""),
            time.monotonic() - started)


def run_specs(
    checker: Checker,
    work: Path,
    *,
    timeout: float = CHECK_TIMEOUT_SECONDS,
    execute: bool = True,
) -> list[ControlResult]:
    """Run every control of one checker inside an already-copied throwaway tree.

    ``execute=False`` is the rot check: anchors are verified against the *pristine* file in the
    copy, but no checker is run (so the cheap mode costs nothing and still fails loudly when
    the file a mutation anchors on has changed).
    """
    script_path = work / checker.script
    results: list[ControlResult] = []

    pristine: dict[str, str] = {}
    for control in checker.controls:
        if control.path in pristine:
            continue
        target = work / control.path
        pristine[control.path] = read_text(target) if target.is_file() else ""

    for control in checker.controls:
        text = pristine[control.path]
        if not (work / control.path).is_file():
            results.append(ControlResult(
                checker.script, control.control_id, control.description, ROTTEN_ANCHOR,
                f"the target file {control.path} no longer exists", None, None, 0.0))
            continue
        mutated, why_not = apply_mutation(text, control.anchor, control.replacement)
        if mutated is None:
            # A rotten anchor gets its own verdict and its target file is never written: a
            # table that no longer matches the files it mutates must fail loudly, not skip.
            results.append(ControlResult(
                checker.script, control.control_id, control.description, ROTTEN_ANCHOR,
                f"{why_not} ({control.path})", None, None, 0.0))
            continue
        if not execute:
            results.append(ControlResult(
                checker.script, control.control_id, control.description, FIRED,
                f"anchor occurs exactly once in {control.path} (not executed: --check)",
                None, None, 0.0))
            continue

        target = work / control.path
        write_text(target, mutated)
        try:
            exit_code, output, seconds = run_checker(checker, work, timeout)
        finally:
            write_text(target, text)

        if exit_code == -1:
            results.append(ControlResult(
                checker.script, control.control_id, control.description, TIMEOUT, output,
                None, None, seconds))
            continue
        verdict, first, detail = judge(
            None if control.expect_fail is None else normalize_paths(control.expect_fail, work),
            exit_code,
            normalize_paths(output, work),
        )
        results.append(ControlResult(
            checker.script, control.control_id, control.description, verdict, detail,
            first, exit_code, seconds))
    return results


# --------------------------------------------------------------------------- self-tests

_FAKE_CHECKER = '''\
import pathlib
import sys

text = (pathlib.Path(__file__).resolve().parent / "target.txt").read_text()
failed = 0
for number in (1, 2, 3):
    token = "ok-%d" % number
    if token in text:
        print("PASS: check %d" % number)
    else:
        print("FAIL: check %d -- token %s missing" % (number, token))
        failed += 1
print("\\nRESULT: FAIL" if failed else "\\nRESULT: PASS")
sys.exit(1 if failed else 0)
'''

_FAKE_TARGET = "ok-1 ok-2 ok-3\n"

_FAKE_CHECKER_SCRIPT = "fake_checker.py"


def _fake_repo(parent: Path) -> Path:
    root = parent / "fake_repo"
    root.mkdir()
    write_text(root / _FAKE_CHECKER_SCRIPT, _FAKE_CHECKER)
    write_text(root / "target.txt", _FAKE_TARGET)
    return root


def run_self_tests() -> list[tuple[str, str, str]]:
    """Prove the harness assigns each verdict it claims. Returns [(id, description, detail)].

    Five controls on a synthetic checker, each built to produce exactly one verdict. These are
    the harness's own negative controls: if ``judge`` or the copy/mutate/run path stops being
    able to tell a green mutation from a fired one, one of these stops matching and the run
    goes red here before it can ever mis-report a real checker.
    """
    cases = (
        ("s1", "a mutation that breaks a check is reported FIRED",
         Mutation("s1", "break check 2", "target.txt", "ok-2", "nope",
                  "FAIL: check 2 -- token ok-2 missing"), FIRED),
        ("s2", "a mutation that changes nothing observable is a COVERAGE GAP",
         Mutation("s2", "touch the file but keep every token", "target.txt",
                  "ok-1 ok-2 ok-3", "ok-1 ok-2 ok-3 # touched",
                  "FAIL: check 1 -- token ok-1 missing"), COVERAGE_GAP),
        ("s3", "a different check refusing first is reported MASKED",
         Mutation("s3", "break check 1 while expecting check 3", "target.txt", "ok-1", "nope",
                  "FAIL: check 3 -- token ok-3 missing"), MASKED),
        ("s4", "an anchor that no longer exists is reported ROTTEN_ANCHOR",
         Mutation("s4", "anchor on a token the file does not contain", "target.txt",
                  "ok-9", "nope", "FAIL: check 9 -- token ok-9 missing"), ROTTEN_ANCHOR),
        ("s5", "a contract-preserving edit that goes red is a FALSE POSITIVE",
         Mutation("s5", "break a check while declaring the edit safe", "target.txt", "ok-3",
                  "nope", None), FALSE_POSITIVE),
    )

    results: list[tuple[str, str, str]] = []
    with tempfile.TemporaryDirectory(prefix="negative-controls-selftest-") as scratch:
        scratch_path = Path(scratch)
        fake_root = _fake_repo(scratch_path)
        checker = Checker(_FAKE_CHECKER_SCRIPT,
                          tuple(case[2] for case in cases))
        work = scratch_path / "copy"
        shutil.copytree(fake_root, work)
        outcomes = run_specs(checker, work)
        by_id = {outcome.control_id: outcome for outcome in outcomes}
        for case_id, description, _, expected in cases:
            outcome = by_id.get(case_id)
            if outcome is None:
                results.append((case_id, description, f"the harness produced no verdict for {case_id}"))
                continue
            detail = ("as expected: " + outcome.verdict if outcome.verdict == expected
                      else f"expected {expected}, got {outcome.verdict} ({outcome.detail})")
            results.append((case_id, description, detail))

    # The table's own hygiene guards get the same treatment: if one of these stops firing, a
    # table that checks nothing (or has lost a control) would print PASS again.
    one = Mutation("t1", "a control", "target.txt", "a", "b", "FAIL: x")
    table_cases = (
        ("s6", "an empty table is refused, not passed vacuously",
         (), 0, "no checkers are registered"),
        ("s7", "a checker with no controls is refused",
         (Checker("fake_checker.py", ()),), 0, "has no controls registered"),
        ("s8", "a deleted control registration is caught by the count guard",
         (Checker("fake_checker.py", (one,)),), 7, "EXPECTED_CONTROLS is 7 but 1 are registered"),
        # The count guard belongs to the WHOLE table: a `--checker` selection validated against
        # it would fail on every narrowed run, which is why `report()` is always handed
        # `table=CHECKERS`. This self-test pins the invariant (the harness's own control `h5`
        # found the call-site bug it describes).
        ("s9", "a narrowed selection is never validated against the whole-table count guard",
         (Checker("fake_checker.py", (one,)),), 36, "EXPECTED_CONTROLS is 36 but 1 are registered"),
    )
    for case_id, description, table, expected_controls, wanted in table_cases:
        problems = table_problems(table, expected_controls)
        if any(wanted in problem for problem in problems):
            results.append((case_id, description, f"as expected: {wanted}"))
        else:
            results.append((case_id, description,
                            f"expected a problem containing {wanted!r}, got {problems}"))
    return results


# --------------------------------------------------------------------------- cli

def report(checkers: tuple[Checker, ...], execute: bool, require_all: bool,
           table: tuple[Checker, ...] | None = None) -> int:
    """Run the selected checkers. ``table`` is the WHOLE table and defaults to ``checkers``.

    The count and vacuity guards are properties of the committed table, so they are always
    checked against it and never against a `--checker` selection -- otherwise narrowing a local
    run would trip the count guard and the harness would be unusable for the one thing
    `--checker` exists for. (That defect was found by the harness's own control `h5`.)
    """
    if table is None:
        table = checkers
    failures: list[str] = []

    print("harness self-tests")
    self_results = run_self_tests()
    self_failed = 0
    for case_id, description, detail in self_results:
        if detail.startswith("as expected:"):
            print(f"PASS: self-test {case_id} -- {description}")
        else:
            print(f"FAIL: self-test {case_id} -- {description}: {detail}")
            self_failed += 1
    if len(self_results) != EXPECTED_SELF_TESTS:
        print(f"FAIL: self-test count -- EXPECTED_SELF_TESTS is {EXPECTED_SELF_TESTS} but "
              f"{len(self_results)} ran; re-derive this harness rather than deleting a self-test")
        self_failed += 1

    selected_controls = sum(len(checker.controls) for checker in checkers)
    fired = bad = skipped_checkers = 0
    skipped_reasons: list[str] = []

    if len(checkers) != len(table):
        print(f"\nscope: {len(checkers)} of {len(table)} checkers selected "
              f"({selected_controls} of {sum(len(c.controls) for c in table)} controls); the "
              "table guards below still cover the whole table")

    for problem in table_problems(table, EXPECTED_CONTROLS):
        print(f"FAIL: control table -- {problem}")
        failures.append(f"control table: {problem}")

    with tempfile.TemporaryDirectory(prefix="negative-controls-") as scratch:
        work = Path(scratch) / "copy"
        copy_tree(work)
        print(f"\nthrowaway copy: {work}")

        for checker in checkers:
            interpreter = venv_interpreter() if checker.interpreter == "venv" else sys.executable
            missing = unmet_requirements(interpreter, checker.requires) if execute else []
            print(f"\nchecker {checker.script}  ({len(checker.controls)} control(s), "
                  f"{interpreter})")
            if missing and execute:
                skipped_checkers += 1
                reason = (f"SKIP {checker.script}: requirement not met -- "
                          f"{', '.join(missing)}; these controls were NOT run on this machine")
                print(reason)
                skipped_reasons.append(reason)
                if require_all:
                    failures.append(
                        f"required capability missing for {checker.script}: {', '.join(missing)}")
                continue

            if execute:
                # The baseline is the control's control: "the mutation makes it red" only means
                # something if the unmutated tree is green. A red baseline is reported as
                # itself, never as a fired control.
                exit_code, output, _ = run_checker(checker, work, CHECK_TIMEOUT_SECONDS)
                baseline_fail = first_fail_line(output)
                result_line = next((line.strip() for line in output.splitlines()
                                    if line.strip().startswith("RESULT:")), "(no RESULT line)")
                if exit_code != 0 or baseline_fail is not None:
                    print(f"FAIL: baseline -- {checker.script} is already red on the unmutated "
                          f"copy: exit={exit_code} {result_line}")
                    if baseline_fail:
                        print(f"       first FAIL: {baseline_fail}")
                    failures.append(f"{checker.script} baseline")
                    bad += len(checker.controls)
                    continue
                print(f"baseline: exit=0 {result_line}")

            for outcome in run_specs(checker, work, execute=execute):
                if outcome.verdict == FIRED:
                    fired += 1
                    print(f"ok   {outcome.control_id} {outcome.description}")
                    if outcome.first_fail:
                        print(f"       first FAIL: {outcome.first_fail}")
                else:
                    bad += 1
                    print(f"FAIL: {checker.script} {outcome.control_id} ({outcome.verdict}) -- "
                          f"{outcome.detail}")
                    if outcome.first_fail:
                        print(f"       observed first FAIL: {outcome.first_fail}")
                    failures.append(f"{checker.script} {outcome.control_id} {outcome.verdict}")

    print("\nsummary")
    print(f"  checkers: {len(checkers)} of {len(table)} selected, {skipped_checkers} skipped")
    print(f"  controls: {fired} fired, {bad} not fired of {selected_controls} selected "
          f"({sum(len(c.controls) for c in table)} registered in the table)")
    print(f"  harness self-tests: {len(self_results) - self_failed} of {len(self_results)} passed")
    for reason in skipped_reasons:
        print(f"  {reason}")

    mode = "anchor check" if not execute else "negative controls"
    if failures or self_failed:
        print(f"\nRESULT: FAIL ({len(failures)} of {selected_controls} selected controls failed, "
              f"{self_failed} self-test(s) failed) [{mode}]")
        return 1
    if not execute:
        print(f"\nRESULT: PASS ({selected_controls} anchors checked) [{mode}]")
    else:
        print(f"\nRESULT: PASS ({fired} controls fired, {len(self_results)} harness self-tests) "
              f"[{mode}]")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--list", action="store_true",
                        help="print the control table and exit")
    parser.add_argument("--check", action="store_true",
                        help="verify every anchor still occurs exactly once; run no checker")
    parser.add_argument("--checker", action="append", default=[], metavar="SCRIPT",
                        help="only this checker (repeatable, e.g. scripts/check_pages_contract.py)")
    parser.add_argument("--require-all", action="store_true",
                        help="a checker skipped for a missing capability fails the run "
                             "(implied when the CI environment variable is set)")
    args = parser.parse_args(argv)

    checkers = tuple(
        checker for checker in CHECKERS
        if not args.checker or checker.script in set(args.checker)
    )
    unknown = set(args.checker) - {checker.script for checker in CHECKERS}
    if unknown:
        print(f"FAIL: unknown checker(s): {', '.join(sorted(unknown))}")
        return 1

    if args.list:
        for checker in checkers:
            print(f"{checker.script}  (interpreter={checker.interpreter or 'this script'}, "
                  f"requires={checker.requires or 'none'})")
            for control in checker.controls:
                expectation = control.expect_fail or "GREEN"
                print(f"  {control.control_id}  {control.description}")
                print(f"      {control.path}: {control.anchor!r} -> {control.replacement!r}")
                print(f"      must print: {expectation}")
        print(f"\n{sum(len(c.controls) for c in checkers)} controls in "
              f"{len(checkers)} checker(s)")
        return 0

    require_all = args.require_all or bool(os.environ.get("CI"))
    return report(checkers, execute=not args.check, require_all=require_all, table=CHECKERS)


if __name__ == "__main__":
    sys.exit(main())
