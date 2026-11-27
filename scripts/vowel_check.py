"""Cross check our vowel marks against CAMeL Tools, and our roots against its analyser.

CAMeL sees only the bare letters of each sentence and vowels them on its own. Every
word where it disagrees with the story file goes on a review list for a human.
Quran quotes are skipped: they are printed from Tanzil.

Usage: python scripts/vowel_check.py stories/booklet-1/01-*.yaml
Writes review/<story id>.md and prints a summary.
"""
import re
import sys
from pathlib import Path

import yaml
from camel_tools.disambig.mle import MLEDisambiguator

from arabic import strip

ROOT = Path(__file__).resolve().parent.parent
MARKS = "ً-ْٰ"
CLUSTER = re.compile(f"[^{MARKS}][{MARKS}]*")


SUKUN, SHADDA, FATHATAN = "ْ", "ّ", "ً"


def clusters(word: str) -> list[tuple[str, set[str]]]:
    """(letter, marks) per letter. Alif wasla as alif, sukun dropped, fathatan moved off a final alif."""
    word = word.replace("ٱ", "ا").replace("ـ", "").replace(SUKUN, "")
    out = [(c[0], set(c[1:])) for c in CLUSTER.findall(word)]
    if len(out) >= 2 and out[-1][0] in "اى" and FATHATAN in out[-1][1]:
        out[-1][1].discard(FATHATAN)
        out[-2][1].add(FATHATAN)
    return out


def conflict(ours: str, theirs: str) -> str | None:
    """Where the two vowellings truly disagree, or None.

    CAMeL often leaves marks out (vowel before a long letter, shadda on sun letters).
    A letter CAMeL left bare counts as no opinion. Returns "case ending" when only the
    last letter disagrees, "INTERNAL" otherwise.
    """
    a, b = clusters(ours), clusters(theirs)
    if [x for x, _ in a] != [x for x, _ in b]:
        return "INTERNAL"
    bad = [i for i, ((_, ma), (_, mb)) in enumerate(zip(a, b)) if mb and not mb <= ma]
    if not bad:
        return None
    return "case ending" if bad == [len(a) - 1] else "INTERNAL"


def root_matches(ours: str, camel: str) -> bool:
    """CAMeL writes weak and hamza radicals as #, and doubled roots with two letters."""
    if len(camel) == len(ours) - 1 and ours[-1] == ours[-2]:
        ours = ours[:-1]
    return len(ours) == len(camel) and all(c == o or (c == "#" and o in "ءأوي") for o, c in zip(ours, camel))


def main(paths: list[str]) -> int:
    mle = MLEDisambiguator.pretrained()
    total_flags = 0
    for path in paths:
        story = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        rows = []
        words_checked = 0
        for n, sent in enumerate(story["sentences"], 1):
            words = [w for w in sent["words"] if not (len(w) > 2 and w[2] == "q")]
            bare = [strip(w[0]) for w in words]
            for w, d in zip(words, mle.disambiguate(bare)):
                words_checked += 1
                theirs = d.analyses[0].analysis.get("diac", "") if d.analyses else ""
                kind = conflict(w[0], theirs) if theirs else "no analysis"
                if kind:
                    rows.append((n, w[0], theirs or "(none)", kind))

        root_rows = []
        for e in story.get("dictionary", []):
            if "root" not in e:
                continue
            got = mle.disambiguate([strip(e["ar"])])[0]
            camel_root = got.analyses[0].analysis.get("root", "").replace(".", "") if got.analyses else ""
            ours = e["root"]
            if camel_root and not root_matches(ours, camel_root):
                root_rows.append((e["ar"], ours, camel_root))

        out = ROOT / "review" / f"{story['id']}.md"
        out.parent.mkdir(exist_ok=True)
        lines = [f"# Review list: {story['title_en']} ({story['id']})", "",
                 f"{words_checked} words checked against CAMeL Tools. "
                 f"{len(rows)} disagree. Tick each one after checking.", "",
                 "Column **ours** is what will print. Column **CAMeL** is the machine's guess. "
                 "A disagreement does not mean ours is wrong: CAMeL often misses context.", "",
                 "| ✓ | Sentence | Ours | CAMeL | Where |", "|---|---|---|---|---|"]
        lines += [f"| ☐ | {n} | {o} | {t} | {k} |" for n, o, t, k in rows]
        if root_rows:
            lines += ["", "## Roots that differ", "", "| ✓ | Word | Ours | CAMeL |", "|---|---|---|---|"]
            lines += [f"| ☐ | {w} | {o} | {c} |" for w, o, c in root_rows]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        internal = sum(1 for r in rows if r[3] == "INTERNAL")
        print(f"{story['id']}: {words_checked} words, {len(rows)} flagged "
              f"({internal} internal, {len(rows) - internal} case ending), "
              f"{len(root_rows)} root differences -> {out.relative_to(ROOT)}")
        total_flags += len(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
