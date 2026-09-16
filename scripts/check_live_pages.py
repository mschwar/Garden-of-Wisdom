#!/usr/bin/env python3
"""Automated live acceptance checker for GitHub Pages deployments.

Usage:
    python3 scripts/check_live_pages.py [--base-url URL] [--repo-dir DIR] [--timeout SECS]
    python3 scripts/check_live_pages.py --self-test

Why this exists
---------------
docs/RUNBOOK.md ("GitHub Pages") lists the live acceptance probes every deploy must pass:
  * four URLs must be 200: /, /browser/index.html, /quotes.csv, /sources.csv
  * paths that must be 404: /.gitignore (issue #23 class -- published top-level dotfile),
    /.git/config (unexcluded .git directory), and /.github/workflows/pages.yml
  * both live CSVs must be sha256-identical to the repo

Until this script, every work unit ran these by hand with curl + shasum and transcribed the
results into the unit handoff. That had two failure modes (issue #41):
  1. it was easy to run a subset -- a missing probe was precisely why issue #23 was misread
     (the checklist only tested /.git/config, so a published /.gitignore looked fine);
  2. transcription into a handoff is a manual copy step, not evidence: nothing re-checked
     the pasted numbers.

This script executes all probes in one command, downloads and compares both CSVs against the
local repository bytes, and exits 0 with RESULT: PASS or non-zero with RESULT: FAIL.

It complements scripts/check_pages_contract.py (the offline config guard): the config guard
asserts what the workflow specifies; this script asserts what the deployment actually published.
It also includes an offline deterministic self-test suite (`--self-test`) using an in-process
mock server to verify negative controls (mis-rooted artifact, published dotfile, stale CSV,
connection errors).
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import socket
import socketserver
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_BASE_URL = "https://mschwar.github.io/Garden-of-Wisdom"
DEFAULT_TIMEOUT = 15.0
DEFAULT_USER_AGENT = "Garden-Acceptance-Checker/1.0"

# Required 200 URLs (relative to base URL)
REQUIRED_200_PATHS = [
    "/",
    "/browser/index.html",
    "/quotes.csv",
    "/sources.csv",
]

# Forbidden 404 paths (relative to base URL)
FORBIDDEN_404_PATHS = [
    "/.gitignore",
    "/.git/config",
    "/.github/workflows/pages.yml",
]

EXPECTED_CHECKS = 9
EXPECTED_SELF_TESTS = 10


def sha256_bytes(data: bytes) -> str:
    """Compute sha256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def fetch_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    user_agent: str = DEFAULT_USER_AGENT,
) -> tuple[int | None, bytes, str | None]:
    """Fetch URL and return (status_code, body_bytes, error_message)."""
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), None
    except urllib.error.HTTPError as exc:
        body = b""
        try:
            body = exc.read()
        except Exception:
            pass
        return exc.code, body, None
    except Exception as exc:
        return None, b"", str(exc)


def run_checks(
    base_url: str,
    repo_dir: Path,
    timeout: float = DEFAULT_TIMEOUT,
    user_agent: str = DEFAULT_USER_AGENT,
) -> tuple[int, int, list[tuple[str, str | None]]]:
    """Run all live acceptance checks against base_url and repo_dir.

    Returns:
        (passed_count, failed_count, results)
        where results is a list of (label, detail_or_none).
    """
    clean_base = base_url.rstrip("/")
    results: list[tuple[str, str | None]] = []
    passed = 0
    failed = 0

    downloaded_bodies: dict[str, bytes] = {}

    # 1. Required 200 probes
    for path in REQUIRED_200_PATHS:
        url = f"{clean_base}{path}"
        label = f"GET {path} returns 200"
        status, body, err = fetch_url(url, timeout=timeout, user_agent=user_agent)
        if err is not None:
            results.append((label, f"network error fetching {url}: {err}"))
            failed += 1
        elif status == 200:
            downloaded_bodies[path] = body
            results.append((f"{label} ({len(body)} bytes)", None))
            passed += 1
        else:
            results.append((label, f"got HTTP {status} (expected 200) from {url}"))
            failed += 1

    # 2. Forbidden 404 probes
    for path in FORBIDDEN_404_PATHS:
        url = f"{clean_base}{path}"
        guard_desc = "published dotfile guard" if path == "/.gitignore" else f"{path.split('/')[1]} exclusion guard"
        label = f"GET {path} returns 404 ({guard_desc})"
        status, _, err = fetch_url(url, timeout=timeout, user_agent=user_agent)
        if err is not None:
            results.append((label, f"network error fetching {url}: {err}"))
            failed += 1
        elif status == 404:
            results.append((label, None))
            passed += 1
        elif status == 200:
            results.append((label, f"got HTTP 200 (expected 404; {path} was published!)"))
            failed += 1
        else:
            results.append((label, f"got HTTP {status} (expected 404) from {url}"))
            failed += 1

    # 3. CSV byte-identical sha256 comparisons
    for csv_name in ("quotes.csv", "sources.csv"):
        path = f"/{csv_name}"
        label = f"live {csv_name} is byte-identical to repo {csv_name}"
        local_path = repo_dir / csv_name
        if not local_path.is_file():
            results.append((label, f"local file missing from repo: {local_path}"))
            failed += 1
            continue

        try:
            local_bytes = local_path.read_bytes()
        except OSError as exc:
            results.append((label, f"could not read local {local_path}: {exc}"))
            failed += 1
            continue

        local_sha = sha256_bytes(local_bytes)

        if path not in downloaded_bodies:
            # Need to download if 200 probe failed or wasn't run
            url = f"{clean_base}{path}"
            status, live_bytes, err = fetch_url(url, timeout=timeout, user_agent=user_agent)
            if err is not None:
                results.append((label, f"network error downloading {url}: {err}"))
                failed += 1
                continue
            if status != 200:
                results.append((label, f"got HTTP {status} downloading {url} (expected 200)"))
                failed += 1
                continue
        else:
            live_bytes = downloaded_bodies[path]

        live_sha = sha256_bytes(live_bytes)
        if live_bytes == local_bytes:
            results.append((f"{label} (sha256: {live_sha})", None))
            passed += 1
        else:
            results.append(
                (
                    label,
                    f"hash mismatch: live sha256={live_sha} ({len(live_bytes)} bytes) vs "
                    f"repo sha256={local_sha} ({len(local_bytes)} bytes)",
                )
            )
            failed += 1

    return passed, failed, results


# --- Mock Server and Self-Test Harness for Negative Controls ---


class MockPagesHandler(http.server.BaseHTTPRequestHandler):
    """Configurable mock HTTP handler simulating various Pages responses."""

    def __init__(self, routes: dict[str, tuple[int, bytes]], *args: Any, **kwargs: Any) -> None:
        self.routes = routes
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        if path in self.routes:
            status, body = self.routes[path]
        else:
            status, body = 404, b"Not Found"

        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any, **kwargs: Any) -> None:
        # Suppress logging in test runs
        pass


class MockServer:
    """In-process mock HTTP server on an ephemeral loopback port."""

    def __init__(self, routes: dict[str, tuple[int, bytes]]) -> None:
        handler = functools.partial(MockPagesHandler, routes)
        self._httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
        self._httpd.daemon_threads = True
        self.port = self._httpd.server_address[1]

    def __enter__(self) -> "MockServer":
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


def run_self_tests(repo_dir: Path = REPO_ROOT) -> int:
    """Run built-in offline negative controls and self-tests against an ephemeral mock server."""
    print("=== check_live_pages self-tests (negative controls) ===")
    quotes_bytes = (repo_dir / "quotes.csv").read_bytes()
    sources_bytes = (repo_dir / "sources.csv").read_bytes()

    baseline_routes: dict[str, tuple[int, bytes]] = {
        "/": (200, b"<html>shim</html>"),
        "/browser/index.html": (200, b"<html>app</html>"),
        "/quotes.csv": (200, quotes_bytes),
        "/sources.csv": (200, sources_bytes),
        "/.gitignore": (404, b"Not Found"),
        "/.git/config": (404, b"Not Found"),
        "/.github/workflows/pages.yml": (404, b"Not Found"),
    }

    test_failures = 0
    tests_run = 0

    def assert_self_test(
        test_id: str,
        desc: str,
        routes: dict[str, tuple[int, bytes]] | None,
        expected_pass: bool,
        aimed_fail_label: str | None = None,
        override_repo: Path = repo_dir,
        unreachable: bool = False,
    ) -> None:
        nonlocal test_failures, tests_run
        tests_run += 1

        if unreachable:
            # Dynamically find an unused ephemeral loopback port that refuses connections
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 0))
                closed_port = s.getsockname()[1]
            url = f"http://127.0.0.1:{closed_port}"
            passed, failed, results = run_checks(url, override_repo, timeout=0.5)
        else:
            assert routes is not None
            with MockServer(routes) as srv:
                url = f"http://127.0.0.1:{srv.port}"
                passed, failed, results = run_checks(url, override_repo, timeout=2.0)

        total_checks = passed + failed
        if total_checks != EXPECTED_CHECKS:
            print(f"FAIL: {test_id} ({desc}) -- expected {EXPECTED_CHECKS} checks to run, got {total_checks}")
            test_failures += 1
            return

        if expected_pass:
            if failed == 0:
                print(f"PASS: {test_id} -- {desc}")
            else:
                first_fail = next(f"{lbl}: {err}" for lbl, err in results if err is not None)
                print(f"FAIL: {test_id} ({desc}) -- expected all checks to pass, but {failed} failed (first: {first_fail})")
                test_failures += 1
        else:
            if failed > 0:
                # Check aimed fail label if provided
                failing_labels = [lbl for lbl, err in results if err is not None]
                if aimed_fail_label and not any(aimed_fail_label in lbl for lbl in failing_labels):
                    print(
                        f"FAIL: {test_id} ({desc}) -- expected aimed failure '{aimed_fail_label}', "
                        f"but failing checks were {failing_labels}"
                    )
                    test_failures += 1
                else:
                    first_err = next(err for lbl, err in results if err is not None)
                    print(f"PASS: {test_id} -- {desc} (fired as aimed: {first_err})")
            else:
                print(f"FAIL: {test_id} ({desc}) -- expected failure, but all checks passed (COVERAGE GAP)")
                test_failures += 1

    # 1. Baseline: all valid
    assert_self_test(
        "s1_baseline",
        "mock server provides all valid probes -> PASS",
        baseline_routes,
        expected_pass=True,
    )

    # 2. Control: required page 404 (mis-rooted artifact)
    r_misroot = dict(baseline_routes)
    r_misroot["/browser/index.html"] = (404, b"Not Found")
    assert_self_test(
        "s2_misroot_app",
        "mis-rooted artifact (/browser/index.html returns 404) -> FAIL",
        r_misroot,
        expected_pass=False,
        aimed_fail_label="GET /browser/index.html returns 200",
    )

    # 3. Control: required CSV 404
    r_csv404 = dict(baseline_routes)
    r_csv404["/quotes.csv"] = (404, b"Not Found")
    assert_self_test(
        "s3_missing_csv",
        "missing CSV (/quotes.csv returns 404) -> FAIL",
        r_csv404,
        expected_pass=False,
        aimed_fail_label="GET /quotes.csv returns 200",
    )

    # 4. Control: published dotfile returns 200 (issue #23 class)
    r_dotfile = dict(baseline_routes)
    r_dotfile["/.gitignore"] = (200, b"node_modules\n.venv\n")
    assert_self_test(
        "s4_dotfile_leak",
        "published dotfile (/.gitignore returns 200) -> FAIL",
        r_dotfile,
        expected_pass=False,
        aimed_fail_label="GET /.gitignore returns 404",
    )

    # 5. Control: published .git/config returns 200
    r_gitconfig = dict(baseline_routes)
    r_gitconfig["/.git/config"] = (200, b"[core]\nrepositoryformatversion = 0\n")
    assert_self_test(
        "s5_git_leak",
        "published git config (/.git/config returns 200) -> FAIL",
        r_gitconfig,
        expected_pass=False,
        aimed_fail_label="GET /.git/config returns 404",
    )

    # 6. Control: published workflow returns 200
    r_workflow = dict(baseline_routes)
    r_workflow["/.github/workflows/pages.yml"] = (200, b"name: Pages\n")
    assert_self_test(
        "s6_workflow_leak",
        "published workflow (/.github/workflows/pages.yml returns 200) -> FAIL",
        r_workflow,
        expected_pass=False,
        aimed_fail_label="GET /.github/workflows/pages.yml returns 404",
    )

    # 7. Control: stale quotes.csv (hash mismatch)
    r_stale_quotes = dict(baseline_routes)
    r_stale_quotes["/quotes.csv"] = (200, b"id,quote_text\n1,mutated\n")
    assert_self_test(
        "s7_stale_quotes",
        "stale quotes.csv (sha256 mismatch) -> FAIL",
        r_stale_quotes,
        expected_pass=False,
        aimed_fail_label="live quotes.csv is byte-identical to repo quotes.csv",
    )

    # 8. Control: stale sources.csv (hash mismatch)
    r_stale_sources = dict(baseline_routes)
    r_stale_sources["/sources.csv"] = (200, b"id,title\n1,mutated\n")
    assert_self_test(
        "s8_stale_sources",
        "stale sources.csv (sha256 mismatch) -> FAIL",
        r_stale_sources,
        expected_pass=False,
        aimed_fail_label="live sources.csv is byte-identical to repo sources.csv",
    )

    # 9. Control: unreachable server
    assert_self_test(
        "s9_unreachable",
        "unreachable server (connection refused) -> FAIL",
        None,
        expected_pass=False,
        aimed_fail_label="GET / returns 200",
        unreachable=True,
    )

    # 10. Control: local repo CSV missing
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "quotes.csv").write_bytes(quotes_bytes)
        # sources.csv missing!
        assert_self_test(
            "s10_local_missing",
            "local repository CSV missing -> FAIL",
            baseline_routes,
            expected_pass=False,
            aimed_fail_label="live sources.csv is byte-identical to repo sources.csv",
            override_repo=tmp_path,
        )

    # Count guard on self-tests
    if tests_run != EXPECTED_SELF_TESTS:
        print(f"FAIL: self-test count -- EXPECTED_SELF_TESTS is {EXPECTED_SELF_TESTS} but {tests_run} ran")
        test_failures += 1

    if test_failures:
        print(f"\nRESULT: FAIL ({test_failures} self-test(s) failed)")
        return 1

    print(f"\nRESULT: PASS ({tests_run} self-tests / negative controls)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Automated live acceptance checker for GitHub Pages deployments."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"base URL of the deployed Pages site (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=REPO_ROOT,
        help="path to local repository root containing quotes.csv and sources.csv",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run offline self-tests and negative controls against an ephemeral mock server",
    )

    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_tests(args.repo_dir)

    print(f"Target URL: {args.base_url}")
    print(f"Local repo: {args.repo_dir}\n")

    passed, failed, results = run_checks(
        base_url=args.base_url,
        repo_dir=args.repo_dir,
        timeout=args.timeout,
    )

    for label, err in results:
        if err is None:
            print(f"PASS: {label}")
        else:
            print(f"FAIL: {label} -- {err}")

    total = passed + failed
    if total != EXPECTED_CHECKS:
        print(f"\nFAIL: check count -- EXPECTED_CHECKS is {EXPECTED_CHECKS} but {total} checks ran")
        failed += 1
        total += 1

    if failed:
        print(f"\nRESULT: FAIL ({failed} of {total} checks failed)")
        return 1

    print(f"\nRESULT: PASS ({total} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
