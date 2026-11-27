# Website Spec (GitHub Pages)

A static, interactive version of the series, built from the same YAML as the PDFs. No framework, no external requests (no CDN, no analytics, no web fonts from Google). Works offline once loaded, on a phone and on a desktop.

## Build

`python scripts/build_site.py` writes `build/site/` (gitignored). It reuses `scripts/render.py` (`build_story`, `glossary`, `quran_text`, `apply_vowels`, `bidi`) and `scripts/surahs.py`, so the web text is the print text. GitHub Actions runs it and deploys to Pages; it needs only Python, PyYAML, Jinja2 and MarkupSafe (not WeasyPrint).

Templates live in `templates/site/` (Jinja2). Styles: `templates/site/site.css`, which starts with `@import url("tokens.css")` (copied from `templates/tokens.css`) and uses only the tokens for sizes, line heights, gaps and colours. Screen sizes may scale the tokens with one `--scale` multiplier per breakpoint; no raw values in rules. Script: one `templates/site/site.js`, plain ES modules, under about 300 lines.

Fonts: self hosted from the installed files (Scheherazade New regular and bold, Charis SIL regular, bold and italic) under `build/site/fonts/`, with the SIL Open Font License text alongside. Use woff2 when available, else ttf.

## Pages

1. **Home** (`index.html`): what the series is; **who it is for**, as a proficiency statement (see below); how the five booklets grade (vowel marks and glosses fade); a card per booklet with its level, stories, a "Read online" link and "Download PDF" links (URLs from `site.yaml`, release assets); how to print.
2. **Booklet** (`b1/index.html` ...): intro and how-to from `booklets/*.yaml`, story list, glossary link.
3. **Story** (`b1/01-bilal-fil-madrasa.html` ...): the reader (below), then grammar box, tip, dictionary, root families, reread box, unvowelled challenge.
4. **Glossary** per booklet, searchable by Arabic (with or without marks), root or English.
5. **About**: sources (Tanzil, the tafsirs and hadith collections named in the stories, Kalila wa Dimna), how the text was checked (Tanzil match, linter, independent proofreading, tafsir check), licences, attribution, how to report a mistake (GitHub issue link).

## The reader

* Each sentence: Arabic words right to left, gloss under each word, English line under the sentence, sentence number, Quran words in the Quran colour inside ﴾ ﴿ with the reference (surah name and ayah).
* **Controls** (sticky bar, remembered in localStorage per browser):
  * Vowel marks: Full · No case endings · Partial · None. Default: the booklet's print mode. Every word's four forms are precomputed at build time with the same rules as print (`q` words never fade, `k` words keep marks, pronoun vowels kept in no-case, pause form on the last word), stored as `data-` attributes; the control only swaps text.
  * Glosses: All · New words only · Off.
  * English: Show · Hide (tap a sentence number to reveal its line).
* **Tap or click a word**: a small popover with the fully vowelled word, its gloss, and, if the word has a dictionary entry in this booklet (match on bare letters), the card: meaning, part of speech, root, pattern, present and bab for verbs, plural, ayah hook with reference and meaning. Escape or tapping elsewhere closes it. Keyboard: words are focusable buttons.
* Illustrations as in print, with their alt text.
* The unvowelled reading text is a separate section with its own vowel control locked to None, and a "show marks" toggle.

## Rules

* Text for the public: never mention any particular school, family or person the series was first made for. Describe the reader by proficiency: reads Arabic script with full vowel marks; knows some of the Quran by heart; knows the basics of Madinah Book 1 (ism, fi'l, harf; al and tanwin; idafa; simple nominal and verbal sentences). Each booklet states what it adds and what it assumes.
* House style (`docs/house_style.md`) and design system (`docs/design_system.md`) apply. No dashes as punctuation in English prose written for the site.
* Accessibility: `lang="ar" dir="rtl"` on Arabic, visible focus, controls reachable by keyboard, contrast at least 4.5:1 for text, no information by colour alone (Quran text also has the brackets and reference).
* Responsive: one column on phones (393px wide), reading line words wrap, no horizontal scroll; the controls bar stays usable with a thumb.
* Attribution in the footer of every page: Quran text from Tanzil (tanzil.net), CC BY 3.0, unchanged; content CC BY-SA 4.0; code MIT.

## Checks

* `python scripts/build_site.py` finishes with no warnings; every story page exists; every internal link resolves (the builder checks).
* Playwright screenshots at 393x852 (iPhone, scale 3) and 1440x900 of home, one story per booklet, and a glossary: no horizontal overflow (`scrollWidth > innerWidth` is false), vowel control changes the text, a word tap opens the popover.
