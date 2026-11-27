"""Render a booklet (or one story) from YAML to PDF.

Usage:
  python scripts/render.py booklets/booklet-1.yaml          -> build/booklet-1.pdf
  python scripts/render.py --story stories/booklet-1/01-x.yaml  -> build/<id>.pdf (proof of one story)

Booklet settings (booklets/booklet-N.yaml):
  vowels:      full | pausal | no_case | partial | none
  gloss:       all | marked          (marked: only words that carry a gloss in the story file)
  translation: inline | after | back
  unvowelled:  try | full | none     (the "read it without vowels" practice)
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from arabic import keep_shadda, mark_root, norm, strip, strip_final, tanzil_span
from surahs import ref_name

ROOT = Path(__file__).resolve().parent.parent
TANZIL = ROOT / "lexicon" / "sources" / "quran-simple.txt"
ILLUSTRATIONS = ROOT / "assets" / "illustrations"

DEFAULTS = {"vowels": "full", "gloss": "all", "translation": "inline", "unvowelled": "try"}
ARABIC_ORDER = "ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىي"


def load_quran() -> dict[str, str]:
    ayat = {}
    for line in TANZIL.read_text(encoding="utf-8").splitlines():
        p = line.split("|")
        if len(p) == 3 and p[0].isdigit():
            ayat[f"{p[0]}:{p[1]}"] = p[2]
    return ayat


QURAN = load_quran()


def quran_text(ayah: dict) -> str:
    """Tanzil's own vowelled words for an ayah hook. Never our typing."""
    span = tanzil_span(QURAN[ayah["ref"]], ayah["text"])
    if span is None:
        sys.exit(f"Ayah text not found in {ayah['ref']}: {ayah['text']} (run verify_ayat.py)")
    return span


def quran_words(ref: str, text: str) -> list[str]:
    """Tanzil words for a quote, pause signs glued to the word before them."""
    out: list[str] = []
    for w in quran_text({"ref": ref, "text": text}).split():
        if norm(w):
            out.append(w)
        elif out:
            out[-1] += " " + w
    return out


def word_items(sentence: dict) -> list[dict]:
    items = []
    for w in sentence["words"]:
        if isinstance(w, str):
            w = [w]
        flags = w[2] if len(w) > 2 else ""
        if len(w) > 1 and not isinstance(w[1], str):
            # YAML reads unquoted on/off/yes/no as booleans and numbers as ints.
            sys.exit(f"Gloss for {w[0]} is {w[1]!r}, not text: quote it in the YAML ({sentence['en']})")
        items.append({"ar": w[0], "gloss": w[1] if len(w) > 1 else "", "flags": flags})
    if "quote" in sentence:
        qw = quran_words(sentence["quote"]["ref"], sentence["quote"]["text"])
        qi = [i for i in items if "q" in i["flags"]]
        if len(qw) != len(qi):
            sys.exit(f"Quote word count mismatch in sentence: {sentence['en']}")
        for item, tw in zip(qi, qw):
            item["ar"] = tw
    return items


def apply_vowels(items: list[dict], mode: str) -> None:
    # The stop falls on the last word only when no Quran quote follows it in the same sentence.
    last = len(items) - 1 if items and "q" not in items[-1]["flags"] else None
    for i, it in enumerate(items):
        if "q" in it["flags"] or "k" in it["flags"]:
            continue  # Quran text and words marked "keep" stay fully vowelled
        a = it["ar"]
        if mode == "pausal" and i == last:
            a = strip_final(a)
        elif mode == "no_case":
            # The vowel of a subject or object pronoun (كَتَبْتُ, أَعْطَيْتُكَ) is not a case ending: keep it.
            if not (re.search(r"[تك][\u064e\u064f\u0650]$", a) and re.search(r"\b(I|you|You|your|Your)\b", it.get("gloss") or "")):
                a = strip_final(a)
        elif mode == "partial":
            a = keep_shadda(a)
        elif mode == "none":
            a = strip(a)
        it["ar"] = a


def root_html(word: str, root: str | None) -> str:
    if not root:
        return html.escape(word)
    # Zero width joiners keep letters joined across colour changes.
    out = []
    for chunk, hit in mark_root(word, root):
        c = html.escape(chunk)
        out.append(f'<span class="rt">‍{c}‍</span>' if hit else f"‍{c}‍")
    return "".join(out)


def validate(s: dict, path: Path) -> None:
    """Stop on YAML that parsed into the wrong shape (unquoted 'x: y', commas, on/off)."""
    errs = []

    def pair(item, where):
        if not (isinstance(item, list) and len(item) == 2 and all(isinstance(x, str) for x in item)):
            errs.append(f"{where}: expected [arabic, english], got {item!r} (quote text with : or , in it)")

    for n, sent in enumerate(s.get("sentences", []), 1):
        if not isinstance(sent.get("en"), str):
            errs.append(f"sentence {n}: en is {sent.get('en')!r}")
        for w in sent.get("words", []):
            if isinstance(w, list) and not all(isinstance(x, str) for x in w):
                errs.append(f"sentence {n}: word {w!r} has a non-text part")
    for ex in (s.get("grammar") or {}).get("examples", []):
        pair(ex, "grammar example")
    for fam in s.get("root_families", []):
        for w in fam.get("words", []):
            pair(w, f"root family {fam.get('root')}")
    for e in s.get("dictionary", []):
        for k in ("ar", "en", "note", "pattern", "plural", "root", "present", "bab"):
            if k in e and not isinstance(e[k], str):
                errs.append(f"dictionary {e.get('ar')}: {k} is {e[k]!r}")
    for k in ("reread",):
        if k in s and not isinstance(s[k], str):
            errs.append(f"{k} is {s[k]!r}")
    for k in ("title", "body"):
        if s.get("tip") and not isinstance(s["tip"].get(k), str):
            errs.append(f"tip {k} is {s['tip'].get(k)!r}")
    if errs:
        sys.exit(f"{path}:\n  " + "\n  ".join(errs))


def plain_sentence(toks: list[dict]) -> str:
    """The unvowelled reading text. Quran words keep their marks inside ﴿ ﴾ so the
    student can tell the ayah from the retelling."""
    out, inq = [], False
    for it in toks:
        q = "q" in it["flags"]
        if q and not inq:
            out.append("﴾")  # same pair, in the same order, as the story lines
        if not q and inq:
            out[-1] += "﴿"
        out.append(it["ar"] if q else strip(it["ar"]))
        inq = q
    if inq:
        out[-1] += "﴿"
    return " ".join(out).replace("﴾ ", "﴾")


def build_story(path: Path, cfg: dict) -> dict:
    s = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate(s, path)
    s["cfg"] = {**DEFAULTS, **cfg, **s.get("override", {})}
    ills = {i["before"]: i for i in s.get("illustrations", [])}
    sents = []
    for n, raw in enumerate(s["sentences"], 1):
        items = word_items(raw)
        raw_items = [dict(it) for it in items]  # fully vowelled, before the booklet setting (the website derives every form from it)
        apply_vowels(items, s["cfg"]["vowels"])
        if s["cfg"]["gloss"] == "marked":
            for it in items:
                if "n" not in it["flags"]:
                    it["gloss"] = ""
        ill = ills.get(n)
        if ill and not (ILLUSTRATIONS / ill["file"]).exists():
            ill = {**ill, "missing": True}
        sents.append({"n": n, "toks": items, "raw": raw_items, "en": raw["en"], "quote": raw.get("quote"), "ill": ill,
                      "plain": " ".join(it["ar"] for it in items)})
    s["sents"] = sents
    # One short header line; the full source notes stay in the YAML for the teacher.
    parts = []
    if s.get("source"):
        parts.append(re.split(r"[.;(,]", s["source"])[0].strip())
    if s.get("madinah"):
        parts.append("Madinah " + re.split(r"[:(]", s["madinah"])[0].strip())
    s["meta_line"] = " · ".join(p for p in parts if p)
    s["plain_text"] = " ".join(plain_sentence(sent["toks"]) for sent in sents)
    for e in s.get("dictionary", []):
        e["word_html"] = html.escape(e["ar"])  # colouring letters inside a word breaks joining in WeasyPrint
        e["bare"] = strip(e["ar"])
        # Visual order (first root letter on the right), locked with bidi-override in CSS.
        e["root_spaced"] = " ".join(reversed(e["root"])) if e.get("root") else ""
        if "ayah" in e:
            e["ayah_text"] = quran_text(e["ayah"])
    return s


def glossary(stories: list[dict]) -> list[dict]:
    seen = {}
    for st in stories:
        for e in st.get("dictionary", []):
            key = strip(e["ar"])
            if key not in seen:
                seen[key] = {"ar": e["ar"], "en": e["en"], "root": " ".join(reversed(e.get("root", ""))),
                             "story": st["number"]}
    def sort_key(e):
        base = norm(e["root"].replace(" ", ""))[::-1] or norm(e["ar"])  # root is stored in visual order
        return [ARABIC_ORDER.find(ch) for ch in base.replace(" ", "")]
    return sorted(seen.values(), key=sort_key)


# ﷺ is its own run: inside a longer run it would be reordered with the Arabic word after it.
ARABIC_RUN = re.compile("ﷺ|"
                        "[؀-ۿݐ-ݿﭐ-ﷹﷻ-﷿ﹰ-﻿]"
                        "[؀-ۿݐ-ݿﭐ-ﷹﷻ-﷿ﹰ-﻿\\s]*")


def bidi(text: str) -> Markup:
    """Escape English prose and isolate each Arabic run so it sits in the right place."""
    out, last = [], 0
    for m in ARABIC_RUN.finditer(text or ""):
        run = m.group(0).rstrip()
        out.append(html.escape(text[last:m.start()]))
        out.append(f'<bdi class="ar-in" dir="rtl">{html.escape(run)}</bdi>')
        last = m.start() + len(run)
    out.append(html.escape((text or "")[last:]))
    return Markup("".join(out))


def render(context: dict, out: Path) -> None:
    from weasyprint import HTML  # imported here so the website build does not need WeasyPrint
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    env.filters["bidi"] = bidi
    env.filters["ref"] = ref_name
    template = env.get_template("booklet.html.j2")
    page = template.render(**context, notes_page=False)
    doc = HTML(string=page, base_url=str(ROOT)).render()
    if context["booklet"] and len(doc.pages) % 2:
        # Double sided printing needs an even page count: add a lined notes page.
        page = template.render(**context, notes_page=True)
        doc = HTML(string=page, base_url=str(ROOT)).render()
    out.parent.mkdir(exist_ok=True)
    out.with_suffix(".html").write_text(page, encoding="utf-8")
    # Page of every sentence, dictionary entry and box, for the review checklist.
    anchors = {name: i for i, p in enumerate(doc.pages, 1) for name in p.anchors}
    out.with_suffix(".anchors.json").write_text(json.dumps(anchors, ensure_ascii=False), encoding="utf-8")
    doc.write_pdf(out)
    print(f"wrote {out.relative_to(ROOT)} ({len(doc.pages)} pages)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--story", action="store_true", help="render a single story as a proof")
    args = ap.parse_args()
    path = Path(args.path)
    if args.story:
        st = build_story(path, {})
        ctx = {"booklet": None, "stories": [st], "glossary": []}
        render(ctx, ROOT / "build" / f"{st['id']}.pdf")
        return
    b = yaml.safe_load(path.read_text(encoding="utf-8"))
    cfg = {k: b[k] for k in DEFAULTS if k in b}
    stories = [build_story(ROOT / p, cfg) for p in b["stories"]]
    # `parts: [3]` splits after story 3 into Part 1 and Part 2 (thin enough to staple).
    cuts = [0, *b.get("parts", []), len(stories)]
    groups = [stories[a:z] for a, z in zip(cuts, cuts[1:])]
    for i, group in enumerate(groups, 1):
        part = {**b, "part": i if len(groups) > 1 else None}
        name = f"{path.stem}-part-{i}" if len(groups) > 1 else path.stem
        render({"booklet": part, "stories": group, "glossary": glossary(group)}, ROOT / "build" / f"{name}.pdf")


if __name__ == "__main__":
    main()
