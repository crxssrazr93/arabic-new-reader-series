# Proofreading Pass

One proofreader per booklet, after the stories are written and before the teacher sees anything. The goal is that the teacher's checklist holds only real questions.

## What to check, per story

1. **Vowels and i'rab, independently.** For every sentence, first work out the correct full vowelling and case endings yourself from the bare letters and the meaning (the English line). Only then compare with the story file. Check: case endings (raf', nasb, jarr, jazm), mabni endings, tanwin, hamzat al-wasl, shadda, sun and moon letter marks, long vowels, verb forms (active or passive, person, mood).
2. **The machine flags.** Read `review/<id>.md`. For each row decide: ours correct (CAMeL wrong), ours wrong, or unsure.
3. **Glosses.** Each gloss matches its word in this sentence (number, tense, person, implied words in parentheses).
4. **English lines.** Each translation says what the Arabic says.
5. **Dictionary entries.** Root, pattern, plural, part of speech (madrasa terms), meaning, and the English meaning of the ayah hook.
6. **Religious content.** Retellings say nothing the Quran or the sahih source does not support. Flag anything doubtful; do not rewrite the story.
7. **Grammar box and tip.** Accurate, and the examples really show the point.

## What to do

* **Clear errors**: fix them in the story YAML directly (keep the file's style; quote English halves of pairs), and record each in `fixed`.
* **Real doubts** (two readings possible, a scholarly difference, something only a teacher can settle): do not change; record in `check` with a short question.
* After fixing, rerun from the project root:
  `.venv/bin/python scripts/verify_ayat.py <files>` (0 failures),
  `.venv/bin/python scripts/vowel_check.py <file>` (refreshes the review list),
  `.venv/bin/python scripts/render.py --story <file>` (must pass validation).

## Output: `proof/<id>.yaml`

```yaml
fixed:
  - {sentence: 4, before: "قَرِيبٍ", after: "قَرِيبٌ", reason: "khabar, marfu'"}
check:
  - {sentence: 12, word: "الْفَصْلِ", question: "Is فصل the usual word for classroom where the reader studies, or صف?"}
camel_unsure:
  - {sentence: 9, word: "غُرْفَتِهَا", camel: "غُرْفَتها", note: "..."}
camel_cleared: 41
```

Use the dictionary entry's `ar` as the `sentence` value for dictionary items (e.g. `sentence: "dict صَبَاحٌ"`). Double quote every string.
