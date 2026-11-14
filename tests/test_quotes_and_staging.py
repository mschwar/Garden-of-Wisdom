"""Fast regression tests for validate_quotes.py, Pages _site staging, and browser bugfixes."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_QUOTES = REPO_ROOT / "scripts" / "validate_quotes.py"
VALIDATE_PREVIEW = REPO_ROOT / "scripts" / "validate_homepage_preview_export.py"
PAGES_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "pages.yml"


def test_validate_quotes_succeeds_from_tmp_cwd() -> None:
    res = subprocess.run(
        [sys.executable, str(VALIDATE_QUOTES)],
        cwd="/tmp",
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "parsed 324 quote rows" in res.stdout
    assert "sources.csv: 32 rows" in res.stdout
    assert "RESULT: PASS" in res.stdout


def test_validate_quotes_handles_non_digit_and_mixed_ids(tmp_path: Path) -> None:
    quotes_csv = tmp_path / "quotes.csv"
    sources_csv = tmp_path / "sources.csv"

    with sources_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["source_id", "source_title", "notes"])
        writer.writerow(["src-1", "Bhagavad Gita", "test"])

    rows = [
        {
            "id": "cand-alpha",
            "quote_text": "You have a right to perform your prescribed duty, never to the fruits.",
            "tradition": "Hinduism",
            "source_ref": "Gita 2.47",
            "author": "Vyasa",
            "tags": "duty,action",
            "source_id": "src-1",
            "item_type": "excerpt",
            "verification_status": "verified",
            "has_unresolved_glyph": "false",
        },
        {
            "id": "cand-beta",
            "quote_text": "You have a right to perform your prescribed duty, but not to the fruits.",
            "tradition": "Hinduism",
            "source_ref": "Gita 2.47",
            "author": "Vyasa",
            "tags": "duty,action",
            "source_id": "src-1",
            "item_type": "excerpt",
            "verification_status": "verified",
            "has_unresolved_glyph": "false",
        },
        {
            "id": "10",
            "quote_text": "Kindness is the light of wisdom in speech.",
            "tradition": "Folklore",
            "source_ref": "Oral Tradition",
            "author": "Traditional",
            "tags": "kindness",
            "source_id": "",
            "item_type": "oral-attribution",
            "verification_status": "unverified",
            "has_unresolved_glyph": "false",
        },
        {
            "id": "cand-gamma",
            "quote_text": "Patience is the companion of wisdom across generations.",
            "tradition": "Folklore",
            "source_ref": "Oral Tradition",
            "author": "Traditional",
            "tags": "patience",
            "source_id": "",
            "item_type": "oral-attribution",
            "verification_status": "unverified",
            "has_unresolved_glyph": "false",
        },
    ]
    with quotes_csv.open("w", encoding="utf-8", newline="") as fh:
        dict_writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        dict_writer.writeheader()
        dict_writer.writerows(rows)

    res = subprocess.run(
        [
            sys.executable,
            str(VALIDATE_QUOTES),
            "--quotes",
            str(quotes_csv),
            "--sources",
            str(sources_csv),
        ],
        cwd="/tmp",
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "cand-alpha ~ cand-beta (same specific citation" in res.stdout
    assert "RESULT: PASS" in res.stdout


def test_corpus_counts_and_preview_export_intact() -> None:
    with (REPO_ROOT / "quotes.csv").open(encoding="utf-8", newline="") as qf:
        quote_rows = list(csv.DictReader(qf))
    with (REPO_ROOT / "sources.csv").open(encoding="utf-8", newline="") as sf:
        source_rows = list(csv.DictReader(sf))
    assert len(quote_rows) == 324
    assert len(source_rows) == 32

    res = subprocess.run(
        [sys.executable, str(VALIDATE_PREVIEW)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "RESULT: PASS" in res.stdout


def test_pages_workflow_stages_only_public_site_files(tmp_path: Path) -> None:
    wf_text = PAGES_WORKFLOW.read_text(encoding="utf-8")
    val_quotes_idx = wf_text.index("python3 scripts/validate_quotes.py")
    val_export_idx = wf_text.index("python3 scripts/validate_homepage_preview_export.py")
    upload_idx = wf_text.index("actions/upload-pages-artifact@v5")
    assert val_quotes_idx < upload_idx
    assert val_export_idx < upload_idx
    assert "path: '_site'" in wf_text
    assert "path: '.'" not in wf_text

    site_dir = tmp_path / "_site"
    site_dir.mkdir(parents=True, exist_ok=True)
    for rel in ("index.html", "quotes.csv", "sources.csv"):
        shutil.copy2(REPO_ROOT / rel, site_dir / rel)
    shutil.copytree(REPO_ROOT / "browser", site_dir / "browser")

    staged_files = {
        p.relative_to(site_dir).as_posix()
        for p in site_dir.rglob("*")
        if p.is_file()
    }
    assert staged_files == {
        "index.html",
        "quotes.csv",
        "sources.csv",
        "browser/index.html",
        "browser/app.js",
        "browser/style.css",
    }


def test_browser_html_and_js_bugfixes() -> None:
    html_text = (REPO_ROOT / "browser" / "index.html").read_text(encoding="utf-8")
    assert '<div id="table-wrap" hidden>' in html_text

    node = shutil.which("node")
    assert node is not None, "node is required to exercise browser/app.js"
    app_js = str(REPO_ROOT / "browser" / "app.js")
    harness = f"""
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync({json.dumps(app_js)}, 'utf8');

function makeEnv(fetchImpl) {{
  const elements = {{}};
  function makeEl(id = '') {{
    return {{
      id,
      value: '',
      checked: false,
      hidden: id === 'table-wrap' || id === 'quote-table',
      textContent: '',
      innerHTML: '',
      className: '',
      style: {{}},
      dataset: id === 'sort-dir' ? {{ dir: 'asc' }} : {{}},
      listeners: {{}},
      children: [],
      classList: {{ remove() {{}}, add() {{}} }},
      setAttribute(k, v) {{ this[k] = v; }},
      removeAttribute(k) {{ delete this[k]; }},
      appendChild(c) {{ this.children.push(c); }},
      addEventListener(ev, fn) {{ this.listeners[ev] = fn; }},
      querySelector(sel) {{ return makeEl(sel); }},
      content: {{ cloneNode() {{ return makeEl('card-clone'); }} }},
    }};
  }}
  const ids = [
    'total-count', 'filtered-count', 'search', 'filter-tradition', 'filter-author',
    'filter-source', 'filter-tag', 'filter-item-type', 'filter-verification',
    'filter-issues-only', 'view-mode', 'sort-field', 'sort-dir', 'results',
    'table-wrap', 'quote-table', 'card-template', 'toast'
  ];
  for (const id of ids) elements[id] = makeEl(id);
  const tbody = makeEl('tbody');
  const thId = makeEl('th-id');
  thId.dataset = {{ sort: 'id' }};
  const ctx = {{
    fetch: fetchImpl,
    console: {{ error() {{}} }},
    navigator: {{ clipboard: {{ writeText: async () => {{}} }} }},
    setTimeout,
    clearTimeout,
    document: {{
      getElementById(id) {{ return elements[id] || (elements[id] = makeEl(id)); }},
      createElement(tag) {{ return makeEl(tag); }},
      createDocumentFragment() {{ return makeEl('frag'); }},
      querySelector(sel) {{ return sel === '#quote-table tbody' ? tbody : makeEl(sel); }},
      querySelectorAll(sel) {{ return sel.includes('th') ? [thId] : []; }},
    }},
  }};
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  return {{ ctx, elements }};
}}

(async () => {{
  // 1) HTTP 404 on quotes.csv rejects and keeps #table-wrap hidden (never #NaN cards)
  const badQuotes = makeEnv(async (url) => ({{
    ok: url.includes('sources.csv'),
    status: url.includes('quotes.csv') ? 404 : 200,
    text: async () => '<html>404 Not Found</html>',
  }}));
  await new Promise((r) => setTimeout(r, 20));
  if (!badQuotes.elements['results'].textContent.includes('HTTP 404')) {{
    throw new Error('Expected HTTP 404 failure message on quotes.csv: ' + badQuotes.elements['results'].textContent);
  }}
  if (badQuotes.elements['table-wrap'].hidden !== true) {{
    throw new Error('#table-wrap must remain hidden on failed load');
  }}

  // 2) HTTP 500 on sources.csv also rejects cleanly
  const badSources = makeEnv(async (url) => ({{
    ok: url.includes('quotes.csv'),
    status: url.includes('sources.csv') ? 500 : 200,
    text: async () => 'id,quote_text,tradition,source_ref,author,tags,source_id,item_type,verification_status,has_unresolved_glyph\\n',
  }}));
  await new Promise((r) => setTimeout(r, 20));
  if (!badSources.elements['results'].textContent.includes('HTTP 500')) {{
    throw new Error('Expected HTTP 500 failure message on sources.csv');
  }}

  // 3) parseCSV empty input + sort-dir data-dir attribute sync
  const okEnv = makeEnv(async (url) => ({{
    ok: true,
    status: 200,
    text: async () => url.includes('quotes.csv')
      ? 'id,quote_text,tradition,source_ref,author,tags,source_id,item_type,verification_status,has_unresolved_glyph\\n1,Hello,Test,Ref 1,Author,tag,s1,excerpt,verified,false\\n'
      : 'source_id,source_title,notes\\ns1,Book,ok\\n',
  }}));
  await new Promise((r) => setTimeout(r, 20));
  if (okEnv.ctx.parseCSV('').length !== 0 || okEnv.ctx.parseCSV('   \\n').length !== 0) {{
    throw new Error('parseCSV empty input did not return []');
  }}
  const sortBtn = okEnv.elements['sort-dir'];
  sortBtn.listeners.click({{ currentTarget: sortBtn, target: sortBtn }});
  if (sortBtn.dataset.dir !== 'desc') {{
    throw new Error('Expected sort-dir dataset.dir === desc after click, got ' + sortBtn.dataset.dir);
  }}
  okEnv.ctx.sortByField('id');
  if (sortBtn.dataset.dir !== 'asc') {{
    throw new Error('Expected sort-dir dataset.dir === asc after sortByField toggle, got ' + sortBtn.dataset.dir);
  }}
  console.log('BROWSER_CHECKS_PASS');
}})().catch((e) => {{ console.error(e); process.exit(1); }});
"""
    res = subprocess.run([node, "-e", harness], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "BROWSER_CHECKS_PASS" in res.stdout
