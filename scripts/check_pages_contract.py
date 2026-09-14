#!/usr/bin/env python3
"""Deterministic guard for the GitHub Pages deploy contract.

Usage:
    python3 scripts/check_pages_contract.py

Why this exists
---------------
The live quote browser fetches ``../quotes.csv`` and ``../sources.csv`` at load time, so the
Pages artifact must be the **repo root**. If the artifact is rooted anywhere else the page
still loads and silently renders **0 quotes**; if the upload action's hidden-file exclusion
regresses, tracked dotfiles are **published**. Both failure modes are invisible to every
other test in this repo:

  * ``scripts/smoke_quote_browser.py`` drives the page over a *local* server rooted at the
    repo root -- it cannot see the Pages artifact at all;
  * ``validate_quotes.py`` / the corpus-program suites never read the workflow files;
  * the deploy job itself **succeeds** in both cases (a mis-rooted or dotfile-leaking
    artifact deploys cleanly).

Until this script, the contract lived only in prose (``docs/RUNBOOK.md`` -> "GitHub Pages",
``docs/architecture/QUOTE_BROWSER.md`` -> "Deployment", and a comment block in
``.github/workflows/pages.yml``), with no falsifier. That is exactly how issue #23 was
missed: the acceptance checklist probed ``/.git/config`` (404) but never ``/.gitignore``,
so a published dotfile went unnoticed.

What it checks (the repository-side half of the contract)
--------------------------------------------------------
  1.  the workflow file parses into the expected shape, else FAIL and ask for a re-derive
  2.  triggers: push to main + workflow_dispatch
  3.  concurrency group `pages` with `cancel-in-progress: false`
  4.  permissions include `pages: write` and `id-token: write`
  5.  the deploy job is guarded to `refs/heads/main`
  6.  an upload step uses `actions/upload-pages-artifact@vN`
  7.  `N` is a major in `VERIFIED_UPLOAD_MAJORS` (below)
  8.  that step's `path` is `'.'` (the repo root)
  9.  that step does not set `include-hidden-files: true`
  10. that step does not override the artifact `name` (deploy-pages requires `github-pages`)
  11. the deploy step keeps `id: deployment` and the environment URL reads its page_url
  12. `browser/app.js` still fetches `../quotes.csv` and `../sources.csv`
  13. both CSVs exist at the repo root (the files that fetch resolves to)
  14. the root `index.html` shim still forwards to `browser/index.html`
  +   the number of checks that actually ran equals `EXPECTED_CHECKS` (a deleted check fails)

``VERIFIED_UPLOAD_MAJORS`` records the action majors whose artifact is *known* to exclude
top-level hidden files, established by reading the action's own ``action.yml``:

    v3  tar ... --exclude=.git --exclude=.github .                  # dotfiles NOT excluded
    v4  ... --exclude=".[^/]*"                                      # dotfiles excluded
    v5  ... --exclude=.[^/]*                                        # dotfiles excluded

v3 is the version this repo ran when issue #23 was filed, and it published ``./.gitignore``
(404 today, because the major bump in PR #22 moved the repo to v5). The minimum is therefore
4, and a major above the verified set fails with a re-derive instruction rather than passing
silently -- an unverified major may have changed the tar invocation.

This is a *config* guard, not an artifact guard: it proves the workflow still asks for a
rooted artifact produced by an action version that excludes hidden files. Proving what a
given *deployment* actually published needs the live checklist in docs/RUNBOOK.md.

Exits 0 with ``RESULT: PASS`` / non-zero with ``RESULT: FAIL`` and one ``FAIL:`` line per
broken check. Stdlib only; reads files, writes nothing, needs no network.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
APP_JS = ROOT / "browser" / "app.js"
ROOT_INDEX = ROOT / "index.html"

# Action majors whose `tar` invocation is verified to exclude top-level hidden files.
# v3 (the version that published ./.gitignore -- issue #23) is deliberately absent.
VERIFIED_UPLOAD_MAJORS = {4, 5}
MIN_UPLOAD_MAJOR = 4
UPLOAD_ACTION = "actions/upload-pages-artifact"
DEPLOY_ACTION = "actions/deploy-pages"
# The artifact name deploy-pages requires. Overriding it is not a style question: the
# deploy step then fails to find an artifact.
REQUIRED_ARTIFACT_NAME = "github-pages"

EXPECTED_CHECKS = 14

CHECKS = []


def check(label):
    """Register one check. The function returns None when it holds, else a failure detail."""

    def register(fn):
        CHECKS.append((label, fn))
        return fn

    return register


class ContractShapeError(Exception):
    """The workflow file is not shaped the way this guard knows how to read."""


def _read(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractShapeError(f"could not read {path.relative_to(ROOT)}: {exc}") from exc


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _blocks(text):
    """Return (header_lines, steps) for the workflow's first ``steps:`` list.

    A step is ``{"dash_indent": int, "lines": [str, ...]}``. Raises ContractShapeError when
    no ``steps:`` list is found -- a silent pass on an unreadable file is the defect class
    this guard exists to stop, so the caller turns that into a FAIL.
    """
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    for index, line in enumerate(lines):
        if not re.match(r"^\s*steps:\s*$", line):
            continue
        base = _indent(line)
        body = []
        for later in lines[index + 1:]:
            if later.strip() and _indent(later) <= base:
                break
            body.append(later)
        step_indents = sorted({_indent(ln) for ln in body if re.match(r"^\s*- ", ln)})
        if not step_indents:
            raise ContractShapeError("found a `steps:` list with no step entries")
        dash_indent = step_indents[0]
        starts = [i for i, ln in enumerate(body) if re.match(r"^\s*- ", ln)
                  and _indent(ln) == dash_indent]
        steps = []
        for position, start in enumerate(starts):
            end = starts[position + 1] if position + 1 < len(starts) else len(body)
            steps.append({"dash_indent": dash_indent, "lines": body[start:end]})
        return lines, steps
    raise ContractShapeError("no `steps:` list found in the workflow")


def _parse_step(step):
    """Return ({own scalar keys}, {with: sub-keys}) for one step block.

    A step's own keys sit at the dash indent (inline, after ``- ``) or at dash+2; the
    ``with:`` mapping's keys sit two levels deeper again. Keeping the two apart matters:
    ``name`` and ``id`` are step keys, while ``with.name`` would be the artifact name.
    """
    dash = step["dash_indent"]
    own, with_map = {}, {}
    with_indent = None
    for line in step["lines"]:
        if not line.strip():
            continue
        indent = _indent(line)
        if indent == dash and line.lstrip().startswith("- "):
            match = re.match(r"^\s*- (\S+):\s*(.*)$", line)
            if match:
                own[match.group(1)] = match.group(2).strip()
            continue
        if with_indent is not None and indent >= with_indent + 2:
            match = re.match(r"^\s*(\S+):\s*(.*)$", line)
            if match:
                with_map[match.group(1)] = match.group(2).strip()
            continue
        if with_indent is not None and indent <= with_indent:
            with_indent = None
        if indent == dash + 2:
            match = re.match(r"^\s*(\S+):\s*(.*)$", line)
            if match:
                if match.group(1) == "with" and not match.group(2).strip():
                    with_indent = dash + 2
                else:
                    own[match.group(1)] = match.group(2).strip()
    return own, with_map


def _step_scalar(step, key):
    """Read a scalar key of the step itself (not of its nested ``with:`` mapping)."""
    value = _parse_step(step)[0].get(key)
    return None if value is None else value.strip("'\"")


def _step_with(step):
    """Return the step's ``with:`` mapping as {key: raw value string}."""
    return _parse_step(step)[1]


def _step_uses(step):
    value = _parse_step(step)[0].get("uses")
    return None if value is None else value.split()[0]


def _find_step(steps, action):
    return [s for s in steps if (_step_uses(s) or "").startswith(action + "@")]


def _action_major(reference):
    match = re.match(r"^[^@]+@v(\d+)$", reference or "")
    return int(match.group(1)) if match else None


def _nested(lines, parent, key):
    """A value nested one level under a `parent:` mapping (e.g. concurrency -> group).

    The parent may sit at any indent (top-level `permissions:`, or a job-level
    `environment:`), so the mapping's keys are read at exactly parent+2.
    """
    parent_indent = None
    for line in lines:
        if not line.strip():
            continue
        indent = _indent(line)
        if parent_indent is not None and indent > parent_indent:
            if indent == parent_indent + 2:
                match = re.match(r"^\s*(\S+):\s*(.*)$", line)
                if match and match.group(1) == key:
                    return match.group(2).strip()
            continue
        parent_indent = None
        match = re.match(r"^(\s*)([A-Za-z0-9_.-]+):\s*$", line)
        if match and match.group(2) == parent:
            parent_indent = len(match.group(1))
    return None


_WORKFLOW_PARSED = None
_WORKFLOW_ERROR = None


def _lazy_workflow():
    """Parse the workflow once; shape errors are reported by check 1."""
    global _WORKFLOW_PARSED, _WORKFLOW_ERROR
    if _WORKFLOW_PARSED is None and _WORKFLOW_ERROR is None:
        text = _read(WORKFLOW)
        try:
            lines, steps = _blocks(text)
            _WORKFLOW_PARSED = {"text": text, "lines": lines, "steps": steps}
        except ContractShapeError as exc:
            _WORKFLOW_ERROR = str(exc)
            raise
    if _WORKFLOW_ERROR is not None:
        raise ContractShapeError(_WORKFLOW_ERROR)
    return _WORKFLOW_PARSED


def _workflow_or_none():
    try:
        return _lazy_workflow()
    except ContractShapeError:
        return None


# ---------------------------------------------------------------- workflow shape

@check("the workflow parses into the shape this guard reads")
def check_shape():
    if _workflow_or_none() is None:
        return (
            f"{WORKFLOW.relative_to(ROOT)} could not be parsed ({_WORKFLOW_ERROR}); "
            "re-derive this guard rather than deleting it"
        )
    return None


@check("triggers: push to main and workflow_dispatch")
def check_triggers():
    parsed = _workflow_or_none()
    if parsed is None:
        return "workflow unreadable (see the shape check above)"
    lines = parsed["lines"]
    on_lines = []
    seen_on = False
    for line in lines:
        if _indent(line) == 0:
            seen_on = bool(re.match(r"^on:\s*$", line))
            continue
        if seen_on:
            on_lines.append(line)
    if not on_lines:
        return "the workflow no longer declares an `on:` block"
    body = "\n".join(on_lines)
    if "workflow_dispatch" not in body:
        return "`workflow_dispatch` is no longer a trigger"
    if not re.search(r"^ {2}push:\s*$", body, re.M):
        return "`push` is no longer a trigger"
    if not re.search(r"branches:\s*\[main\]", body):
        return "push is no longer filtered to `main`"
    return None


@check("concurrency: group `pages`, cancel-in-progress false")
def check_concurrency():
    parsed = _workflow_or_none()
    if parsed is None:
        return "workflow unreadable (see the shape check above)"
    lines = parsed["lines"]
    group = _nested(lines, "concurrency", "group")
    cancel = _nested(lines, "concurrency", "cancel-in-progress")
    if group != "pages":
        return f"concurrency group is {group!r}, not 'pages'"
    if cancel != "false":
        return (
            f"cancel-in-progress is {cancel!r}, not 'false' -- a deploy must never be "
            "cancelled mid-flight"
        )
    return None


@check("permissions include `pages: write` and `id-token: write`")
def check_permissions():
    parsed = _workflow_or_none()
    if parsed is None:
        return "workflow unreadable (see the shape check above)"
    lines = parsed["lines"]
    wanted = {"pages": "write", "id-token": "write"}
    for key, value in wanted.items():
        if _nested(lines, "permissions", key) != value:
            return f"permissions no longer grant `{key}: {value}`"
    return None


@check("the deploy job is guarded to refs/heads/main")
def check_main_guard():
    parsed = _workflow_or_none()
    if parsed is None:
        return "workflow unreadable (see the shape check above)"
    lines = parsed["lines"]
    guards = [ln.strip() for ln in lines
              if re.match(r"^\s{4}if:\s*github\.ref\s*==\s*'refs/heads/main'\s*$", ln)]
    if not guards:
        return (
            "the deploy job has no `if: github.ref == 'refs/heads/main'` guard -- a "
            "workflow_dispatch from a branch could overwrite the live site"
        )
    return None


# ---------------------------------------------------------------- upload step

@check("an upload step uses actions/upload-pages-artifact")
def check_upload_step_present():
    parsed = _workflow_or_none()
    if parsed is None:
        return "workflow unreadable (see the shape check above)"
    if not _find_step(parsed["steps"], UPLOAD_ACTION):
        return f"no step uses {UPLOAD_ACTION}@vN; re-derive this guard"
    return None


@check("the upload action major excludes top-level hidden files")
def check_upload_major():
    uploads = _upload_steps()
    if not uploads:
        return "upload step missing (see the step-presence check above)"
    reference = _step_uses(uploads[0])
    major = _action_major(reference)
    if major is None:
        return f"could not read a major version from {reference!r}; re-derive this guard"
    if major < MIN_UPLOAD_MAJOR:
        return (
            f"{UPLOAD_ACTION}@{major} is below the minimum verified major {MIN_UPLOAD_MAJOR} "
            "-- its tar invocation does NOT exclude top-level dotfiles, which published "
            "./.gitignore (issue #23)"
        )
    if major not in VERIFIED_UPLOAD_MAJORS:
        return (
            f"{UPLOAD_ACTION}@{major} is not in VERIFIED_UPLOAD_MAJORS "
            f"{sorted(VERIFIED_UPLOAD_MAJORS)}: confirm the action still excludes top-level "
            "hidden files (read its action.yml) and extend the set with the evidence"
        )
    return None


@check("the uploaded path is the repo root ('.')")
def check_upload_path():
    uploads = _upload_steps()
    if not uploads:
        return "upload step missing (see the step-presence check above)"
    path = _step_with(uploads[0]).get("path")
    if path is None:
        return "the upload step sets no `path:` -- the action default is `_site/`, not the repo root"
    if path.strip("'\"") != ".":
        return (
            f"the upload path is {path!r}, not '.': browser/index.html fetches "
            "../quotes.csv, so a differently-rooted artifact renders 0 quotes"
        )
    return None


@check("the upload step does not include hidden files")
def check_upload_hidden_files():
    uploads = _upload_steps()
    if not uploads:
        return "upload step missing (see the step-presence check above)"
    value = _step_with(uploads[0]).get("include-hidden-files")
    if value is not None and value.strip("'\"").lower() == "true":
        return (
            "include-hidden-files is 'true': top-level dotfiles would be published "
            "(issue #23)"
        )
    return None


@check("the upload step keeps the artifact name `github-pages`")
def check_artifact_name():
    uploads = _upload_steps()
    if not uploads:
        return "upload step missing (see the step-presence check above)"
    name = _step_with(uploads[0]).get("name")
    if name is not None and name.strip("'\"") != REQUIRED_ARTIFACT_NAME:
        return (
            f"the artifact name is {name!r}, not {REQUIRED_ARTIFACT_NAME!r}: "
            "actions/deploy-pages requires the default name"
        )
    return None


@check("the deploy step keeps id `deployment` and the environment reads its page_url")
def check_deploy_step():
    parsed = _workflow_or_none()
    if parsed is None:
        return "workflow unreadable (see the shape check above)"
    deploys = _find_step(parsed["steps"], DEPLOY_ACTION)
    if not deploys:
        return f"no step uses {DEPLOY_ACTION}@vN; re-derive this guard"
    if _step_scalar(deploys[0], "id") != "deployment":
        return "the deploy step's `id` is no longer `deployment`"
    url = _nested(parsed["lines"], "environment", "url")
    if url is None or url.strip("'\"") != "${{ steps.deployment.outputs.page_url }}":
        return (
            "the github-pages environment no longer publishes exactly "
            "`${{ steps.deployment.outputs.page_url }}`"
        )
    return None


def _upload_steps():
    parsed = _workflow_or_none()
    return [] if parsed is None else _find_step(parsed["steps"], UPLOAD_ACTION)


# ---------------------------------------------------------------- the layout it serves

@check("browser/app.js still fetches ../quotes.csv and ../sources.csv")
def check_app_fetches():
    try:
        app = _read(APP_JS)
    except ContractShapeError as exc:
        return str(exc)
    for target in ("../quotes.csv", "../sources.csv"):
        if f'fetch("{target}")' not in app:
            return (
                f"{APP_JS.relative_to(ROOT)} no longer fetches {target!r}; if the fetch "
                "changed, the artifact layout requirement changed with it"
            )
    if "app.js" not in _read(ROOT / "browser" / "index.html"):
        return "browser/index.html no longer loads app.js"
    return None


@check("the fetched CSVs exist at the repo root")
def check_csvs_at_root():
    missing = [name for name in ("quotes.csv", "sources.csv") if not (ROOT / name).is_file()]
    if missing:
        return (
            f"{missing} missing from the repo root; the live page's ../<name> fetches "
            "would 404 and the page would render 0 quotes"
        )
    return None


@check("the root index.html shim still forwards to browser/index.html")
def check_root_shim():
    try:
        shim = _read(ROOT_INDEX)
    except ContractShapeError as exc:
        return str(exc)
    if "browser/index.html" not in shim:
        return "the root index.html no longer forwards to browser/index.html"
    return None


def main():
    failed = 0
    for label, fn in CHECKS:
        try:
            detail = fn()
        except Exception as exc:  # a guard that crashes must fail, never silently pass
            detail = f"check raised {type(exc).__name__}: {exc}"
        if detail is None:
            print(f"PASS: {label}")
        else:
            print(f"FAIL: {label} -- {detail}")
            failed += 1

    # A check that no longer runs is not a check. Deleting one (or an early return that
    # skips the rest) must fail loudly.
    if len(CHECKS) != EXPECTED_CHECKS:
        print(
            f"FAIL: check count -- EXPECTED_CHECKS is {EXPECTED_CHECKS} but {len(CHECKS)} "
            "checks are registered; re-derive this guard rather than deleting a check"
        )
        failed += 1

    total = len(CHECKS) + 1
    if failed:
        print(f"\nRESULT: FAIL ({failed} of {total} checks failed)")
        return 1
    print(f"\nRESULT: PASS ({total} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
