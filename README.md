# Arabic New Reader Series

Graded, illustrated reading booklets for learners of Classical Arabic, with some Modern Standard Arabic. Read them online, or print them at home on A4.

**Read online:** https://crxssrazr93.github.io/arabic-new-reader-series/
**Printable PDFs:** [latest release](https://github.com/crxssrazr93/arabic-new-reader-series/releases/latest)

> **Draft.** A teacher of Arabic and Islamic studies is reviewing the series now. Mistakes are possible; please [report any you find](https://github.com/crxssrazr93/arabic-new-reader-series/issues/new).

## Who it is for

You will get the most from the series if you:

* read Arabic script with full vowel marks,
* know some of the Quran by heart, and
* know the basics of Madinah Book 1 (ism, fi'l and harf; al and tanwin; idafa; simple nominal and verbal sentences).

The English is the language of explanation throughout.

## How it works

Every sentence shows the Arabic, the meaning of each word under it, and the whole sentence in English. Across five booklets the help fades, until you read unvowelled classical and modern text.

| Booklet | Vowel marks | What it adds |
|---|---|---|
| 1 | Full | Short stories for meaning; every word glossed; a dictionary per story, with roots and an ayah for each word |
| Bonus | Full, as in the Mushaf | Al-Fatiha and surahs 105 to 114, word by word |
| 2 | Full, last word in pause | Past and present verbs, agreement, plurals |
| 3 | No case endings | Longer stories, only new words glossed, each story repeated with no marks |
| 4 | Only new and difficult words | Working words out from root, pattern and position |
| 5 | None | Unvowelled stories, ending with the original Arabic of a fable from Kalila wa Dimna |

The stories retell the prophets and the Seerah from the Quran and sahih hadith, tell fables and Juha tales, and follow a modern cast in everyday Arabic. The pictures never show faces, animals, prophets or companions.

Online, you can switch the vowel marks between full, no case endings, partial and none, hide the glosses or the English, and tap any word for its meaning and dictionary card.

## Printing

Print each PDF in colour, double sided (flip on the long edge), on A4, and staple at the spine. Each file is one booklet of 48 pages or fewer.

## How the text was made and checked

The stories, glosses and dictionaries were written with the help of AI models (Claude), and checked with these steps:

1. Every quoted ayah is matched letter for letter against the Tanzil text (`scripts/verify_ayat.py`).
2. Every word is compared with an independent morphological analyser, CAMeL Tools (`scripts/vowel_check.py`).
3. A linter checks the vowelling rules a machine can check reliably: tanwin, the article, sun and moon letters, case after prepositions and particles (`scripts/lint.py`).
4. A separate proofreading pass works out the i'rab of each sentence from the bare letters before comparing it with the text.
5. Retelling details, attributions and hadith are checked against the tafsirs (Ibn Kathir, al-Tabari, al-Qurtubi, al-Baghawi) and the hadith collections.
6. A teacher reviews the result (in progress).

These checks reduce mistakes; they do not remove them. Ask a teacher about anything that matters.

## Building it yourself

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/build_site.py                 # website in build/site
.venv/bin/python scripts/render.py booklets/booklet-1.yaml   # PDFs in build/
.venv/bin/python scripts/lint.py --no-pdf              # checks
```

The website needs only PyYAML and Jinja2. The PDFs need WeasyPrint and the fonts Scheherazade New and Charis SIL installed on your system. Each push to `main` rebuilds the website through GitHub Actions.

* `stories/`: one YAML file per story (format in `docs/story-format.md`)
* `booklets/`: which stories go in each booklet, and its settings
* `docs/`: house style, design system, illustration policy, proofreading method

## Contributing

Corrections are very welcome, especially from teachers. Open an issue naming the booklet, story and sentence number, what is printed, and what you think it should be.

## License

Stories, glosses, dictionaries, translations and pictures: CC BY-SA 4.0 (see `LICENSE-CONTENT.md`). Code: MIT (see `LICENSE`). Quran text from Tanzil (tanzil.net), CC BY 3.0, unchanged. Fonts: SIL Open Font License 1.1.
