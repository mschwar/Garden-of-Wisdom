# Donor review table — garden-homepage-preview v1

Approved set (owner, 2026-09-11): Garden ids **3, 12, 15, 26, 30**.

| id | Garden text | Garden author → export | Garden `source_ref` → export | Official URL | `item_type` | Verdict | Notes |
|---|---|---|---|---|---|---|---|
| 3 | The earth is but one country, and mankind its citizens. | Bahá’u’lláh (unchanged) | `Gleanings, CXVII` → Gleanings CXVII (full title in export) | [Gleanings HTML part 6](https://www.bahai.org/library/authoritative-texts/bahaullah/gleanings-writings-bahaullah/6) | excerpt | **accept** | Exact closing sentence of CXVII. CSV `item_type` was heuristic `unknown`. |
| 12 | Truthfulness is the foundation of all human virtues. | Bahá’u’lláh → **‘Abdu’l-Bahá** | ADJ p. 22 → Tablet of ‘Abdu’l-Bahá; cited in ADJ | [Additional Tablets extract](https://www.bahai.org/library/authoritative-texts/abdul-baha/additional-tablets-extracts-talks/826608209/826608209.xhtml) | excerpt | **accept** | Wording exact. Author and locator were wrong; corrected in CSV. |
| 15 | Regard man as a mine rich in gems of inestimable value. | Bahá’u’lláh (unchanged) | `Gleanings, CXXII` → Gleanings CXXII (full title in export) | [Gleanings HTML part 6](https://www.bahai.org/library/authoritative-texts/bahaullah/gleanings-writings-bahaullah/6) | excerpt | **accept** | Exact sentence in CXXII after “The Great Being saith:”. CSV `item_type` was heuristic `unknown`. |
| 26 | Service to humanity is service to God. | ‘Abdu’l-Bahá (unchanged) | Paris Talks, Oct 22 1911 → **PUP, 12 April 1912** | [Promulgation of Universal Peace](https://www.bahai.org/library/authoritative-texts/abdul-baha/promulgation-universal-peace/promulgation-universal-peace.xhtml) | excerpt | **accept** | Wording exact. Work/date were wrong; corrected in CSV. |
| 30 | Prayer is the key of the doors of mercy. | ‘Abdu’l-Bahá | Paris Talks, Dec 2 1911 | — | (not exported) | **reject** | Sentence not found. No 2 Dec 1911 Paris Talks meeting. |

All four accepted items are ≤75 words (11, 8, 11, 7). None are Hidden Words.
None were near-duplicate pairs except id 3 ~ 283 (thematic echo, different
author/work; already recorded in `docs/DECISIONS.md`).
