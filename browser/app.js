// Garden of Wisdom quote browser. No framework, no backend: fetches
// ../quotes.csv and ../sources.csv over the local static server and does
// everything client-side.

function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else { inQuotes = false; }
      } else {
        field += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ",") {
      row.push(field);
      field = "";
    } else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += c;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  const header = rows.shift();
  return rows
    .filter((r) => r.length === header.length && r.some((v) => v !== ""))
    .map((r) => Object.fromEntries(header.map((h, idx) => [h, r[idx]])));
}

const state = {
  quotes: [],
  sources: {},
  search: "",
  filters: { tradition: "", author: "", source: "", tag: "", item_type: "", verification_status: "" },
  issuesOnly: false,
  sortField: "id",
  sortDir: "asc",
};

function detectIssues(q) {
  const issues = [];
  if (q.has_unresolved_glyph === "true") issues.push("unresolved glyph");
  if (!q.source_id) issues.push("unresolved source link");
  if (q.item_type === "unknown") issues.push("item type unknown");
  if (q.verification_status !== "verified") issues.push("unverified");
  return issues;
}

function populateSelect(id, values) {
  const el = document.getElementById(id);
  const current = el.value;
  el.innerHTML = '<option value="">All</option>';
  [...values].sort((a, b) => a.localeCompare(b)).forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    el.appendChild(opt);
  });
  el.value = current;
}

function populateFilterOptions() {
  populateSelect("filter-tradition", new Set(state.quotes.map((q) => q.tradition)));
  populateSelect("filter-author", new Set(state.quotes.map((q) => q.author)));
  populateSelect("filter-source", new Set(state.quotes.map((q) => q.source_ref)));
  populateSelect("filter-item-type", new Set(state.quotes.map((q) => q.item_type)));
  populateSelect("filter-verification", new Set(state.quotes.map((q) => q.verification_status)));
  const allTags = new Set();
  state.quotes.forEach((q) => (q.tags || "").split(",").forEach((t) => t.trim() && allTags.add(t.trim())));
  populateSelect("filter-tag", allTags);
}

function matchesSearch(q, term) {
  if (!term) return true;
  const haystack = `${q.quote_text} ${q.author} ${q.source_ref} ${q.tags}`.toLowerCase();
  return haystack.includes(term.toLowerCase());
}

function applyFilters() {
  let rows = state.quotes.filter((q) => matchesSearch(q, state.search));
  const f = state.filters;
  if (f.tradition) rows = rows.filter((q) => q.tradition === f.tradition);
  if (f.author) rows = rows.filter((q) => q.author === f.author);
  if (f.source) rows = rows.filter((q) => q.source_ref === f.source);
  if (f.item_type) rows = rows.filter((q) => q.item_type === f.item_type);
  if (f.verification_status) rows = rows.filter((q) => q.verification_status === f.verification_status);
  if (f.tag) rows = rows.filter((q) => (q.tags || "").split(",").map((t) => t.trim()).includes(f.tag));
  if (state.issuesOnly) rows = rows.filter((q) => detectIssues(q).length > 0);

  const dir = state.sortDir === "asc" ? 1 : -1;
  rows.sort((a, b) => {
    let av, bv;
    if (state.sortField === "length") {
      av = a.quote_text.length;
      bv = b.quote_text.length;
    } else if (state.sortField === "id") {
      av = parseInt(a.id, 10);
      bv = parseInt(b.id, 10);
    } else {
      av = (a[state.sortField] || "").toLowerCase();
      bv = (b[state.sortField] || "").toLowerCase();
    }
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });
  return rows;
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (el.hidden = true), 1500);
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => toast("Copied")).catch(() => toast("Copy failed"));
}

function render() {
  const rows = applyFilters();
  document.getElementById("total-count").textContent = state.quotes.length;
  document.getElementById("filtered-count").textContent = rows.length;

  const container = document.getElementById("results");
  const template = document.getElementById("card-template");
  container.innerHTML = "";
  const frag = document.createDocumentFragment();

  rows.forEach((q) => {
    const node = template.content.cloneNode(true);
    const card = node.querySelector(".card");
    card.dataset.id = q.id;

    const issues = detectIssues(q);
    const badgeWrap = node.querySelector(".card-badges");
    const idBadge = document.createElement("span");
    idBadge.className = "badge";
    idBadge.textContent = `#${q.id}`;
    badgeWrap.appendChild(idBadge);
    issues.forEach((issue) => {
      const b = document.createElement("span");
      b.className = "badge issue";
      b.textContent = issue;
      badgeWrap.appendChild(b);
    });

    node.querySelector(".quote-text").textContent = q.quote_text;
    node.querySelector(".author").textContent = q.author;
    node.querySelector(".source-ref").textContent = q.source_ref;
    node.querySelector(".tradition-pill").textContent = q.tradition;
    node.querySelector(".tags").textContent = q.tags;

    const dl = node.querySelector(".provenance dl");
    const source = state.sources[q.source_id];
    const entries = [
      ["item_type", q.item_type],
      ["verification_status", q.verification_status],
      ["source_id", q.source_id || "(unresolved)"],
      ["source manifest", source ? source.source_title : "(none linked)"],
      ["manifest notes", source ? source.notes : ""],
    ];
    entries.forEach(([k, v]) => {
      const dt = document.createElement("dt");
      dt.textContent = k;
      const dd = document.createElement("dd");
      dd.textContent = v || "—";
      dl.appendChild(dt);
      dl.appendChild(dd);
    });

    node.querySelector(".copy-quote").addEventListener("click", () => copyText(q.quote_text));
    node.querySelector(".copy-attributed").addEventListener("click", () =>
      copyText(`"${q.quote_text}" — ${q.author}, ${q.source_ref}`)
    );
    node.querySelector(".copy-json").addEventListener("click", () => copyText(JSON.stringify(q, null, 2)));

    frag.appendChild(node);
  });
  container.appendChild(frag);
}

function wireControls() {
  document.getElementById("search").addEventListener("input", (e) => {
    state.search = e.target.value;
    render();
  });
  document.getElementById("filter-tradition").addEventListener("change", (e) => {
    state.filters.tradition = e.target.value;
    render();
  });
  document.getElementById("filter-author").addEventListener("change", (e) => {
    state.filters.author = e.target.value;
    render();
  });
  document.getElementById("filter-source").addEventListener("change", (e) => {
    state.filters.source = e.target.value;
    render();
  });
  document.getElementById("filter-tag").addEventListener("change", (e) => {
    state.filters.tag = e.target.value;
    render();
  });
  document.getElementById("filter-item-type").addEventListener("change", (e) => {
    state.filters.item_type = e.target.value;
    render();
  });
  document.getElementById("filter-verification").addEventListener("change", (e) => {
    state.filters.verification_status = e.target.value;
    render();
  });
  document.getElementById("filter-issues-only").addEventListener("change", (e) => {
    state.issuesOnly = e.target.checked;
    render();
  });
  document.getElementById("sort-field").addEventListener("change", (e) => {
    state.sortField = e.target.value;
    render();
  });
  document.getElementById("sort-dir").addEventListener("click", (e) => {
    state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    e.target.textContent = state.sortDir === "asc" ? "↑ Ascending" : "↓ Descending";
    render();
  });
}

async function main() {
  const [quotesText, sourcesText] = await Promise.all([
    fetch("../quotes.csv").then((r) => r.text()),
    fetch("../sources.csv").then((r) => r.text()),
  ]);
  state.quotes = parseCSV(quotesText);
  const sourceRows = parseCSV(sourcesText);
  state.sources = Object.fromEntries(sourceRows.map((s) => [s.source_id, s]));

  populateFilterOptions();
  wireControls();
  render();
}

main().catch((err) => {
  document.getElementById("results").textContent = `Failed to load data: ${err}`;
  console.error(err);
});
