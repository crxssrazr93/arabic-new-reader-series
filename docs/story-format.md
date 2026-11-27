# Story File Format and Writing Rules

One YAML file per story in `stories/booklet-N/NN-slug.yaml`. The reference example is `stories/booklet-1/01-bilal-fil-madrasa.yaml`: copy its shape exactly.

## Fields

| Field | Meaning |
|---|---|
| `id` | `bN-NN`, e.g. `b2-03` |
| `booklet`, `number` | integers |
| `strand` | `modern`, `quran`, `seerah`, `hadith` or `tale` |
| `title_ar`, `title_en` | fully vowelled Arabic title, English title |
| `madinah` | the Madinah lessons whose grammar the story stays within |
| `source` | for quran, seerah, hadith and tale stories: the exact references the retelling follows (e.g. "Quran 11:36 to 48"; "Sahih al-Bukhari 2272") |
| `illustrations` | list of `{before: sentence number, file: bN-NN-slug.png, alt: description}`; 2 or 3 per story |
| `sentences` | list of `{words: [...], en: "..."}` plus optional `quote` |
| `dictionary` | entries, same keys as the example |
| `root_families` | 1 or 2 boxes |
| `grammar` | one grammar point from the story, with 2 or 3 examples |
| `tip` | one "reading without vowels" tip suited to the booklet |
| `try_it` | booklets 1 and 2 only: 4 to 6 unvowelled words and one unvowelled sentence from the story |
| `reread` | one line |

## Words

Each word is `[arabic, gloss]` or `[arabic, gloss, flags]`.

* **Arabic is always written fully vowelled**, including case endings, in every booklet. The renderer removes marks according to the booklet setting. Never type a booklet's reduced form yourself.
* Attached particles stay on their word as in normal spelling (وَذَهَبَ, بِالْقَلَمِ, كِتَابَهُ).
* Words starting with hamzat al-wasl at the very start of a sentence take a kasra or damma on the alif (اِسْمُ, اُدْخُلْ); inside a sentence write plain ا.
* Moon letter ال takes sukun on the lam (الْقَمَرُ); sun letter ال has no mark on the lam and shadda on the next letter (الشَّمْسُ).
* Gloss: short English, implied words in parentheses as in the reference screenshot: `"(is) a student"`, `"(of) Bilal"`.
* Flags: `q` = word of a Quran quote; `n` = new word (gets a gloss in booklets 3 and 4, where only new words are glossed); `k` = keep vowels even in partial or unvowelled booklets (use for genuinely ambiguous words).
* In booklets 3 to 5, glosses are still written for every `n` word; other words may have an empty gloss `""`.
* **Quote any gloss YAML could misread**: `on`, `off`, `yes`, `no`, `true`, `false`, numbers. Unquoted they become booleans or integers.
* **Always double quote the English half of `[arabic, english]` pairs** (glosses with a colon or comma, grammar examples, root family words). Unquoted, `Say: ...` becomes a map and `x, y` splits into two items. The renderer validates shapes and stops with the location.

## Length per booklet

| Booklet | Sentences | Words per sentence | Story length |
|---|---|---|---|
| 1 | about 25 | 4 to 9 | 100 to 150 words |
| 2 | 30 to 40 | 5 to 11 | 250 to 400 |
| 3 | 40 to 55 | 6 to 13 | 450 to 650 |
| 4 | 50 to 70 | 7 to 15 | 650 to 900 |
| 5 | 60 to 80 | free | 900 to 1,200 |

One or two Quran quotes per Quran story is right; use a quote wherever the prophet's own words matter, rather than inventing speech.

## Quran quotes

* A sentence quoting the Quran adds `quote: {ref: "S:A", text: ...}` and flags each quoted word `q`.
* The Quran text you type is only used to find the span; the page prints Tanzil's own text. Words must match Tanzil letter for letter (simple script, e.g. هَـٰذَا, الرَّحْمَـٰنِ). Check with `scripts/verify_ayat.py`.
* Never paraphrase inside a quote. Retell around the ayat in your own Arabic.

## Dictionary entries

`{ar, en, pos: [Arabic term, English], root, pattern, plural, ayah: {ref, text}, register, note}`

* `ar`: dictionary form, vowelled with tanwin for nouns (طَالِبٌ) and the past 3rd person for verbs (ذَهَبَ).
* `root`: letters only, no spaces, hamza as أ, weak letters as و or ي (أخو, صلو, قرأ).
* `pos` Arabic terms as taught in madrasa: اسم، فعل ماض، فعل مضارع، فعل أمر، حرف، صفة، اسم فاعل، اسم مفعول، اسم مكان، مصدر، جمع تكسير.
* `ayah`: a short, well known ayah containing a word from the same root, ideally the same word. Prefer Juz 'Amma, al-Fatiha, al-Baqara opening, al-Kahf, Yasin, al-Mulk, famous ayat. Must pass `verify_ayat.py`.
* `register`: `modern` (MSA only), `both` (classical meaning differs from modern; explain in `note`). Leave out for ordinary classical words.
* 15 to 25 entries per story in booklets 1 and 2; 12 to 20 new words in later booklets. Do not repeat a word already in an earlier story's dictionary (check the earlier files); instead recycle it in the text.

## Writing rules

1. **Grammar ceiling.** Stay within the Madinah lessons named for the booklet. Booklet 1: nominal sentences, هٰذَا/هٰذِهِ/ذٰلِكَ/تِلْكَ, ال, prepositions, idafa, adjectives, attached pronouns, simple past verbs (3rd person mostly), يَا. No present tense in booklet 1 except fixed expressions.
2. **Vocabulary.** Prefer high frequency Quranic words. About 1 new word in 50 is the target from booklet 2 on; booklet 1 introduces the core. **Recycle earlier dictionary words heavily**: each later story should reuse at least 25 earlier dictionary words.
3. **Accuracy of religious content.** Retell only what the Quran or a sahih hadith says, in order, without invented dialogue for prophets beyond what the source states. No weak narrations. Cite the source in `source`.
4. **Voice.** Short, clear sentences; one idea per sentence; 4 to 9 words per sentence in booklet 1. Natural classical style for classical strands, plain MSA for modern ones. A 15 year old reader: warm, never childish.
5. **Illustrations** follow `docs/illustration-policy.md`: no animals, no faces, never prophets or sahaba. Describe scenes of places and objects.
6. **English** is a natural translation, not word for word.

## Checks (all must pass before a story is done)

```
.venv/bin/python scripts/verify_ayat.py stories/booklet-N/*.yaml        # 0 failures
.venv/bin/python scripts/vowel_check.py stories/booklet-N/NN-*.yaml     # read review/bN-NN.md
.venv/bin/python scripts/render.py --story stories/booklet-N/NN-*.yaml  # renders without error
```

For every word in `review/bN-NN.md`: if ours is wrong, fix the story and rerun. If CAMeL is wrong, leave it; the teacher sees the list.
