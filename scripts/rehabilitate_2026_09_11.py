#!/usr/bin/env python3
"""One-time migration: Mac OS Roman -> UTF-8, plus schema additions.

Run once, from repo root, against the archived originals:

    python3 scripts/rehabilitate_2026_09_11.py

Reads data/archive/2026-09-11/{quotes,sources}.original.csv (untouched raw
bytes) and writes canonical UTF-8 quotes.csv / sources.csv at the repo root.

This script is kept for provenance (it documents exactly how the 2026-09-11
retrofit derived the canonical files from the legacy bytes) and is safe to
re-run: it always reads from the frozen archive, never from its own output.
"""
import csv
import io

ORAL_TRADITIONS = {
    "Diné (Navajo)", "Hopi (Pueblo)", "Haudenosaunee (Iroquois)",
    "Yoruba (Nigeria)", "Nahua (Aztec)", "Multitribal Proverb",
    "Oglala Lakota", "Shawnee", "Cherokee", "Nez Perce", "Lakota",
    "Tewa (Pueblo)", "Zuni (Pueblo)", "Nguni (Bantu)", "Akan (Ghana)",
    "Ethiopian", "Igbo (Nigeria)", "K'iche' (Maya)", "Modern Mayan",
}

# source_ref substring -> source_id in sources.csv. Matched in order;
# first hit wins. This links each quote row to a specific manifest entry
# based on what the source_ref text actually names, rather than guessing
# from tradition alone (a tradition like Judaism spans three different
# sources.csv rows: Talmud, Bible, Pirkei Avot).
SOURCE_REF_KEYWORDS = [
    ("Avesta", "1"), ("Yasna", "1"), ("Gatha", "1"), ("Vendidad", "1"),
    ("Fravarane", "1"), ("Ashem Vohu", "1"), ("Zoroastrian Creed", "1"),
    ("Talmud", "2"),
    ("Gita", "3"),
    ("Black Elk", "4"),
    ("Beauty Way", "5"), ("Blessingway", "5"), ("Night Way", "5"),
    ("Dhammapada", "6"),
    ("Hadith", "7.1"), ("Bukhari", "7.1"), ("Sahih Muslim", "7.1"),
    ("Great Law of Peace", "8"),
    ("Genesis", "9"), ("Exodus", "9"), ("Leviticus", "9"), ("Numbers", "9"),
    ("Deuteronomy", "9"), ("Psalm", "9"), ("Proverbs", "9"), ("Ecclesiastes", "9"),
    ("Isaiah", "9"), ("Matthew", "9"), ("Mark", "9"), ("Luke", "9"), ("John", "9"),
    ("Corinthians", "9"), ("James", "9"), ("Romans", "9"), ("Galatians", "9"),
    ("Thessalonians", "9"), ("Ephesians", "9"), ("Colossians", "9"),
    ("Micah", "9"), ("Samuel", "9"), ("Philippians", "9"), ("Revelation", "9"),
    ("Timothy", "9"),
    ("Qur'an", "11"), ("Quran", "11"), ("Surah", "11"),
    ("Gleanings", "12"), ("Hidden Words", "12"), ("Kitáb", "12"), ("Kitab", "12"),
    ("Aqdas", "12"), ("Paris Talks", "12"), ("Lawḥ", "12"), ("Law_", "12"),
    ("Tablet", "12"), ("Epistle to the Son of the Wolf", "12"),
    ("Selections from the Writings of", "12"), ("Advent of Divine Justice", "12"),
    ("Promulgation of Universal Peace", "12"), ("The Chosen Highway", "12"),
    ("The World Order of Bahá", "12"),
    ("Guru Granth", "13"), ("Japji", "13"), ("GGS", "13"), ("Ang ", "13"),
    ("Swaya", "13"),
    ("Pirkei Avot", "14"), ("Ethics of the Fathers", "14"),
    ("Popol Vuh", "15"),
    ("Sutta", "16"), ("Pali Canon", "16"), ("Nikaya", "16"), ("Udana", "16"),
    ("Upanishad", "17"), ("Veda", "17"), ("Rig Veda", "17"), ("Rigveda", "17"),
    ("Nasadiya", "17"), ("Gayatri", "17"),
]

ORAL_SOURCE_BY_TRADITION = {
    "Oglala Lakota": "4",
    "Diné (Navajo)": "5",
    "Haudenosaunee (Iroquois)": "8",
    "Hopi (Pueblo)": "10",
    "Yoruba (Nigeria)": "18",
    "Akan (Ghana)": "18",
    "Igbo (Nigeria)": "18",
}


def resolve_source_id(source_ref, tradition):
    for keyword, sid in SOURCE_REF_KEYWORDS:
        if keyword in source_ref:
            return sid
    if tradition in ORAL_SOURCE_BY_TRADITION:
        return ORAL_SOURCE_BY_TRADITION[tradition]
    return ""


def decode_original(path):
    raw = open(path, "rb").read()
    try:
        raw.decode("utf-8")
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("mac_roman")


def classify_item_type(row_by_name):
    tradition = row_by_name["tradition"]
    source_ref = row_by_name["source_ref"]
    if tradition in ORAL_TRADITIONS:
        return "oral-attribution"
    has_pinpoint = any(ch.isdigit() for ch in source_ref) or ":" in source_ref
    if has_pinpoint:
        return "excerpt"
    return "unknown"


def load_sources():
    """sources.csv's `notes` column contains unescaped commas in the
    original (it was never properly CSV-quoted), so csv.reader fragments
    long notes into extra trailing fields. Those fragments belong back in
    `notes`, not deleted -- rejoin any fields past the header count into
    the final (notes) column instead of truncating them away.
    """
    text = decode_original("data/archive/2026-09-11/sources.original.csv")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    header = [h for h in rows[0] if h != ""]
    out = []
    for r in rows[1:]:
        if len(r) > len(header):
            head, tail = r[: len(header) - 1], r[len(header) - 1 :]
            while len(tail) > 1 and tail[-1] == "":
                tail.pop()
            r = head + [",".join(tail)]
        while len(r) < len(header):
            r.append("")
        out.append(dict(zip(header, r)))
    return header, out


def write_sources(header, sources):
    with open("sources.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for s in sources:
            w.writerow([s.get(h, "") for h in header])


def write_quotes(rows, new_header):
    with open("quotes.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(new_header)
        for r in rows:
            w.writerow([r.get(h, "") for h in new_header])


def main():
    src_header, sources = load_sources()
    write_sources(src_header, sources)

    text = decode_original("data/archive/2026-09-11/quotes.original.csv")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    header = rows[0]
    new_header = header + ["item_type", "verification_status", "source_id", "has_unresolved_glyph"]

    out_rows = []
    for r in rows[1:]:
        d = dict(zip(header, r))
        d["item_type"] = classify_item_type(d)
        d["verification_status"] = "unverified"
        d["source_id"] = resolve_source_id(d["source_ref"], d["tradition"])
        d["has_unresolved_glyph"] = "true" if "_" in d["quote_text"] + d["author"] + d["source_ref"] else "false"
        out_rows.append(d)

    write_quotes(out_rows, new_header)
    print(f"wrote {len(out_rows)} quote rows, {len(sources)} source rows")


if __name__ == "__main__":
    main()
