# Design System

Every size, line height, gap and colour in `templates/style.css` comes from the tokens in its `:root` block. A rule never uses a raw number for these; if a new value seems needed, add a token here first.

## Why line height needs care here

Fully vowelled Arabic carries marks above and below the letters (shadda plus fatha on top, kasratan underneath). Scheherazade New draws them far outside the letter body. If a line is set too tight, the marks touch the line above or the gloss below. Latin text has no such marks. So the system has separate line heights for Latin, for Arabic, and for Latin lines that contain Arabic words.

## Tokens

### Type: Latin (Charis SIL)

| Token | Size | Used for |
|---|---|---|
| `--fs-micro` | 7pt | story number in the glossary, tags |
| `--fs-caption` | 7.8pt | word glosses under Arabic, ayah reference labels |
| `--fs-small` | 8.5pt | dictionary facts and notes, ayah meanings, glossary, kicker lines |
| `--fs-body` | 10.5pt | English lines, front matter, boxes |
| `--fs-h3` | 11pt | box headings |
| `--fs-h2` | 15pt | dictionary heading, section titles |
| `--fs-h1` | 19pt | story title |
| `--fs-display` | 30pt | cover title |

### Type: Arabic (Scheherazade New, Amiri as fallback)

| Token | Size | Used for |
|---|---|---|
| `--ar-s` | 13pt | glossary words, contents titles, ayah hooks on cards, unvowelled form on cards |
| `--ar-m` | 17pt | grammar box examples, root family rows |
| `--ar-l` | 23pt | the reading line (every story sentence), unvowelled reading text |
| `--ar-xl` | 26pt | "try it" practice words, dictionary headwords |
| `--ar-title` | 30pt | story title in Arabic |
| `--ar-display` | 36pt | cover title |
| `--ar-inline` | 1.25em | an Arabic word inside an English sentence |

### Line height

| Token | Value | Used for |
|---|---|---|
| `--lh-tight` | 1.2 | headings, glosses (Latin only, one or two lines) |
| `--lh-latin` | 1.5 | English text with no Arabic in it |
| `--lh-mixed` | 1.85 | English text that may contain Arabic words: notes, boxes, facts, intro, translations |
| `--lh-ar-word` | 1.6 | a single Arabic word or short phrase standing alone (card headword, glossary word, contents title) |
| `--lh-ar` | 1.9 | Arabic that may wrap onto more lines: reading lines, ayah hooks, box examples |
| `--lh-ar-para` | 2.1 | running Arabic paragraphs (the unvowelled reading text) |

Rule: any element whose content can mix Arabic into English uses `--lh-mixed`, and the inline Arabic itself keeps `line-height: normal` within that line, so the marks get the room the paragraph gives them.

### Space

`--sp-1` 1mm · `--sp-2` 2mm · `--sp-3` 3mm · `--sp-4` 4mm · `--sp-5` 5mm · `--sp-6` 6mm.
`--gloss-gap` 2.4mm (from the bottom of an Arabic word to its gloss; enough to clear kasratan under ح and خ).
`--word-gap` 5.5mm (between words on a reading line) · `--line-gap` 3mm (between wrapped reading lines).

### Shape and colour

`--radius-s` 1.5mm · `--radius-m` 2.5mm · `--radius-l` 3mm.
Colours: `--ink`, `--muted`, `--gloss`, `--rule`, `--accent`, `--accent-soft`, `--root` (root letters), `--quran` and `--quran-soft` (all Quran text), `--gold` (grammar box), `--paper-soft`.

## Components

* **Reading line** (`.sent`): Arabic `--ar-l` / `--lh-ar`, gloss `--fs-caption` / `--lh-tight` at `--gloss-gap`, English line `--fs-body` / `--lh-mixed`.
* **Boxes** (grammar, tip, reread, translation): body `--fs-body` / `--lh-mixed`; examples Arabic `--ar-m` / `--lh-ar`.
* **Dictionary card**: headword `--ar-xl` / `--lh-ar-word`; meaning `--fs-body`; facts and notes `--fs-small` / `--lh-mixed`; ayah `--ar-s` / `--lh-ar`, its meaning `--fs-small` / `--lh-mixed`.
* **Glossary**: `--fs-small` / `--lh-mixed`, Arabic `--ar-s` / `--lh-ar-word`.
* **Contents**: English `--fs-body`, Arabic `--ar-s` / `--lh-ar-word`, one line each (no wrapping).

## Checks

After any change to the CSS: render all booklets, run `scripts/lint.py` (page counts, near blank pages, fonts), and look at one page of each component at 220 dpi for marks touching neighbouring lines. Part files must stay at 48 pages (12 sheets) or fewer.
