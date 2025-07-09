# A Garden of Wisdom

This is a personal collection of impactful quotes from various world religions and philosophies, curated for memorization and reflection.

The idea is inspired by the Baha'i quote: “A kindly tongue is the lodestone of the heart of men.”

The goal is not to be exhaustive, but to be a clean, simple, and impactful source of personal inspiration. The data is stored in a single `quotes.csv` file, designed for both human readability and machine processing.

## Data Structure and Conventions

To maintain the integrity and simplicity of this collection, all entries in `quotes.csv` must adhere to the following structure and conventions.

### File Format: CSV

The data is stored in a Comma-Separated Values (CSV) file named `quotes.csv`.
- The first row is the header row.
- All text fields should be enclosed in double quotes (`"`) to handle commas and other special characters within the text.
- The file encoding must be UTF-8 to support a wide range of characters.

### Field Definitions

The CSV has the following 6 fields:

| Field Name     | Data Type | Description                                                                                             | Required |
| :------------- | :-------- | :------------------------------------------------------------------------------------------------------ | :------- |
| `id`           | Integer   | A unique, sequential number for each quote. Start at `1` and increment by one for each new entry.       | Yes      |
| `quote_text`   | String    | The full text of the quote. For line breaks within a quote, use the `\n` character.                       | Yes      |
| `tradition`    | String    | The religious or philosophical tradition from a controlled list. See **Tradition Conventions** below.   | Yes      |
| `source_ref`   | String    | The specific book, chapter, verse, or surah where the quote is found. See **Reference Conventions**.    | Yes      |
| `author`       | String    | The attributed author, speaker, or primary figure of the quote.                                         | Yes      |
| `tags`         | String    | A comma-separated list of lowercase keywords or themes. See **Tagging Conventions**.                    | Yes      |

---

### Convention Details

#### 1. Tradition Conventions
The `tradition` field must use one of the following exact values:

- `Baha'i`
- `Buddhism`
- `Christianity`
- `Hinduism`
- `Islam`
- `Judaism`
- `Zoroastrianism`

#### 2. Reference (`source_ref`) Conventions
Follow a consistent format for clarity.

- **Bible (Judaism/Christianity):** `Book Chapter:Verse-range` (e.g., `Proverbs 15:1`, `Matthew 5:3-10`)
- **Qur'an (Islam):** `Qur'an Surah#:Ayah#` (e.g., `Qur'an 2:286`)
- **Baha'i Writings:** `Book Title` (e.g., `Gleanings from the Writings of Baháʼu'lláh`, `The Hidden Words`)
- **Hindu Writings:** `Book Chapter.Verse` (e.g., `Gita 2.47`, `Upanishads 1.1.1`)
- **Buddhist Writings:** `Text Name, Chapter.Verse` (e.g., `Dhammapada, 1.5`)
- **Other Texts:** Use a clear, consistent `Book, Section` format.

#### 3. Tagging (`tags`) Conventions
Tags are the primary tool for organizing quotes by theme.

- **Format:** A single string of comma-separated values.
- **No spaces:** Do not include spaces between tags (e.g., `kindness,speech,wisdom`).
- **Lowercase:** All tags must be in lowercase.
- **Singular:** Use the singular form of a word where possible (e.g., `virtue` instead of `virtues`).

---

## Example Entry

Here is what a few rows in `quotes.csv` look like:

```csv
id,quote_text,tradition,source_ref,author,tags
1,"A kindly tongue is the lodestone of the heart of men. It is the bread of the spirit, it clotheth the words with meaning, it is the fountain of the light of wisdom and understanding.",Baha'i,"Gleanings from the Writings of Baháʼu'lláh",Baháʼu'lláh,"kindness,speech,influence,heart"
2,"A gentle answer turns away wrath,\nbut a harsh word stirs up anger.",Judaism,"Proverbs 15:1",Solomon,"kindness,anger,speech,wisdom"
3,"He who has a hundred desires, has a hundred woes. He who has no desires, has no woes.",Buddhism,"The Dhammapada, 13.177",The Buddha,"desire,suffering,detachment,peace"