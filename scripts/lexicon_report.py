"""Count how often each dictionary word comes back across the series.

Every token in every story is lemmatised with CAMeL Tools. Each dictionary entry is
matched to a lemma, and its encounters are counted from the story where it first
appears to the end of the given list. Target: 10 or more by the end of the series.

Usage: python scripts/lexicon_report.py booklets/booklet-1.yaml [booklets/booklet-2.yaml ...]
Writes lexicon/report.md and prints a short summary.
"""
import sys
from collections import Counter
from pathlib import Path

import yaml
from camel_tools.disambig.mle import MLEDisambiguator

from arabic import norm, strip

ROOT = Path(__file__).resolve().parent.parent


def tokens(story: dict) -> list[str]:
    out = []
    for s in story["sentences"]:
        for w in s["words"]:
            ar = w if isinstance(w, str) else w[0]
            out.append(strip(ar))
    return out


def main(booklets: list[str]) -> int:
    mle = MLEDisambiguator.pretrained()
    stories = []
    for b in booklets:
        data = yaml.safe_load(Path(b).read_text(encoding="utf-8"))
        for p in data["stories"]:
            stories.append(yaml.safe_load((ROOT / p).read_text(encoding="utf-8")))

    per_story: list[Counter] = []
    for st in stories:
        lex = Counter()
        sents = [[strip(w if isinstance(w, str) else w[0]) for w in s["words"]] for s in st["sentences"]]
        for toks in sents:
            for d in mle.disambiguate(toks):
                if d.analyses:
                    lex[norm(d.analyses[0].analysis.get("lex", ""))] += 1
        per_story.append(lex)

    rows, low = [], 0
    for i, st in enumerate(stories):
        for e in st.get("dictionary", []):
            d = mle.disambiguate([strip(e["ar"])])[0]
            lemma = norm(d.analyses[0].analysis.get("lex", "")) if d.analyses else norm(e["ar"])
            count = sum(c[lemma] for c in per_story[i:])
            later = sum(c[lemma] for c in per_story[i + 1:])
            rows.append((st["id"], e["ar"], e["en"], count, later))
            low += count < 10

    lines = ["# Word recycling report", "",
             f"{len(stories)} stories, {len(rows)} dictionary words. "
             f"{low} words are met fewer than 10 times so far (target 10 by the end of the series).", "",
             "| Introduced | Word | Meaning | Times met (from intro) | In later stories |", "|---|---|---|---|---|"]
    lines += [f"| {a} | {w} | {m} | {c} | {l} |" for a, w, m, c, l in sorted(rows, key=lambda r: r[3])]
    out = ROOT / "lexicon" / "report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} dictionary words, {low} met fewer than 10 times -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
