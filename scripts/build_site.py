"""Build the static website from the same YAML as the PDFs.

Usage:
  python scripts/build_site.py            writes build/site/ (open it through a web server, e.g.
                                          python3 -m http.server -d build/site)

Needs Python, PyYAML, Jinja2 and MarkupSafe (not WeasyPrint). The reading text, vowel rules, Quran
spans and bidi handling all come from scripts/render.py, so the web text is the print text.
Fonts and pictures are copied from assets/web/ (made once by scripts/prepare_web_assets.py).
See docs/site_spec.md.
"""
import copy
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

import render as R
from arabic import norm, strip
from surahs import ref_name

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "site"
TPL = ROOT / "templates" / "site"
WEB = ROOT / "assets" / "web"

# The four forms the reader switches between, in the order of the data-v attribute (a fifth,
# the fully vowelled word, is kept for the popover). A booklet that reads in pause shows the
# pause form on the last word under "Full".
KEYS = ["full", "nocase", "partial", "none"]
DEFAULT_KEY = {"full": "full", "pausal": "full", "no_case": "nocase", "partial": "partial", "none": "none"}
STRAND = {"quran": "Quran", "seerah": "Seerah", "hadith": "Hadith", "tale": "Tale", "modern": "Modern"}

PREFIXES = ["وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ك", "ل", "س"]
SUFFIXES = ["ها", "هم", "هن", "كم", "نا", "ني", "ون", "ين", "ان", "ات", "وا", "ه", "ك", "ي", "ة", "ا"]

warnings: list[str] = []


def warn(msg: str) -> None:
    warnings.append(msg)


# ---------- dictionary matching ----------

def stems(word: str):
    """Candidate dictionary forms of a word, plainest first: the word itself, then without a
    joined particle, then also without a pronoun or plural ending (never shorter than 3 letters)."""
    w = norm(word)
    bases = [w] + [w[len(p):] for p in PREFIXES if w.startswith(p) and len(w) - len(p) >= 3]
    yield from bases
    for b in bases:
        for s in SUFFIXES:
            if b.endswith(s) and len(b) - len(s) >= 3:
                yield b[: -len(s)]


class BookletDictionary:
    """Every dictionary entry of a booklet, found by bare letters."""

    def __init__(self, stories: list[dict]):
        self.entries: list[dict] = []
        self.index: dict[str, int] = {}
        for st in stories:
            for i, e in enumerate(st.get("dictionary", []), 1):
                key = norm(e["ar"])
                if key in self.index:
                    continue
                self.index[key] = len(self.entries)
                self.entries.append({"e": e, "story": st, "n": i})

    def find(self, word: str) -> int | None:
        for cand in stems(word):
            if cand in self.index:
                return self.index[cand]
        return None

    def card(self, idx: int, word: str) -> dict:
        item = self.entries[idx]
        e, st = item["e"], item["story"]
        c = {"en": e["en"], "pos": e["pos"], "href": f"{st['slug']}.html#d-{st['id']}-{item['n']}"}
        for k in ("root", "pattern", "present", "bab", "plural"):
            if e.get(k):
                c[k] = e[k]
        if norm(word) != norm(e["ar"]):
            c["headword"] = e["ar"]
        if e.get("ayah") and e.get("ayah_text"):
            c["ayah"] = {"ref": ref_name(e["ayah"]["ref"]), "text": e["ayah_text"], "en": e["ayah"].get("en", "")}
        return c


# ---------- one story ----------

def vowel_forms(raw: list[dict], booklet_vowels: str) -> list[list[str]]:
    """The four forms of every word, computed with the print rules (render.apply_vowels)."""
    modes = ["pausal" if booklet_vowels == "pausal" else "full", "no_case", "partial", "none"]
    forms = []
    for mode in modes:
        items = copy.deepcopy(raw)
        R.apply_vowels(items, mode)
        forms.append([it["ar"] for it in items])
    return forms


def prepare_story(st: dict, path: Path, ctx: dict) -> None:
    st["slug"] = path.stem
    st["file"] = f"{st['slug']}.html"
    dflt = KEYS.index(DEFAULT_KEY[st["cfg"]["vowels"]])
    st["default"] = {"vowels": DEFAULT_KEY[st["cfg"]["vowels"]], "gloss": "all" if st["cfg"]["gloss"] == "all" else "new",
                     "english": "show" if st["cfg"]["translation"] == "inline" else "hide"}
    n_words = 0
    for s in st["sents"]:
        forms = vowel_forms(s["raw"], st["cfg"]["vowels"])
        words, plain = [], []
        for i, it in enumerate(s["raw"]):
            q = "q" in it["flags"]
            prev_q = i > 0 and "q" in s["raw"][i - 1]["flags"]
            next_q = i + 1 < len(s["raw"]) and "q" in s["raw"][i + 1]["flags"]
            opens, closes = q and not prev_q, q and not next_q
            v = [forms[k][i] for k in range(4)] + [it["ar"]]
            words.append({"text": v[dflt], "v": v, "q": q, "new": "n" in it["flags"], "gloss": it["gloss"],
                          "opens": opens, "closes": closes, "card": None, "_ar": it["ar"]})
            plain.append({"bare": strip(it["ar"]), "marked": it["ar"], "q": q, "opens": opens, "closes": closes})
        s["words"], s["plain"] = words, plain
        n_words += len(words)
        ill = s.get("ill")
        if ill:
            web = WEB / "img" / (Path(ill["file"]).stem + ".webp")
            if ill.get("missing") or not web.exists():
                warn(f"{st['id']}: illustration {ill['file']} is missing (sentence {s['n']}); run scripts/prepare_web_assets.py")
                s["ill"] = None
            else:
                w, h = ctx["sizes"][web.name]
                s["ill"] = {"file": web.name, "alt": ill["alt"], "w": w, "h": h}
                ctx["images"].add(web.name)
    st["n_words"] = n_words
    for i, e in enumerate(st.get("dictionary", []), 1):
        e["id"] = f"d-{st['id']}-{i}"


def attach_cards(st: dict, bdict: BookletDictionary) -> dict:
    """Link every word to its dictionary entry; returns the cards the page needs."""
    cards = {}
    for s in st["sents"]:
        for w in s["words"]:
            idx = bdict.find(w["_ar"])
            if idx is not None:
                cid = f"c{idx}"
                w["card"] = cid
                if cid not in cards:
                    cards[cid] = bdict.card(idx, w["_ar"])
    return cards


# ---------- pages ----------

def make_env() -> Environment:
    env = Environment(loader=FileSystemLoader(TPL), autoescape=True)
    env.filters["bidi"] = R.bidi
    env.filters["ref"] = ref_name
    env.filters["spaced"] = lambda s: " ".join(s)
    env.filters["jsondata"] = lambda d: Markup(json.dumps(d, ensure_ascii=False).replace("<", "\\u003c"))
    return env


def part_labels(stories: list[dict], cuts: list[int]) -> list[str]:
    bounds = [0, *cuts, len(stories)]
    out = []
    for i, (a, z) in enumerate(zip(bounds, bounds[1:]), 1):
        first, last = stories[a]["number"], stories[z - 1]["number"]
        out.append(f"Part {i}: story {first}" if first == last else f"Part {i}: stories {first} to {last}")
    return out


def grade_sample(stories: list[dict]) -> dict:
    """One sentence shown at each of the five levels: the first with five or six words,
    no Quran quote, and a different spelling at every level."""
    levels = [("full", "full"), ("pausal", "full"), ("no_case", "nocase"), ("partial", "partial"), ("none", "none")]
    for st in stories:
        for s in st["sents"]:
            raw = s["raw"]
            if s.get("quote") or not 5 <= len(raw) <= 6 or any(not it["gloss"] for it in raw):
                continue
            rows = []
            for mode, _ in levels:
                items = copy.deepcopy(raw)
                R.apply_vowels(items, mode)
                rows.append([it["ar"] for it in items])
            if len({" ".join(r) for r in rows}) == 5:
                new = max(range(len(raw)), key=lambda i: len(strip(raw[i]["ar"])))
                return {"rows": rows, "glosses": [it["gloss"] for it in raw], "new": new}
    warn("no sample sentence found for the grading strip")
    return {"rows": [], "glosses": [], "new": 0}


def write(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def build() -> int:
    cfg_site = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    env = make_env()
    sizes = json.loads((WEB / "img" / "sizes.json").read_text(encoding="utf-8")) if (WEB / "img" / "sizes.json").exists() else {}
    if not sizes:
        sys.exit("assets/web/img is empty: run python scripts/prepare_web_assets.py first")
    ctx = {"sizes": sizes, "images": set()}

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    booklets, bonus_booklet = [], []
    all_stories = {}
    matched = total = 0
    for n in [1, 2, 3, 4, 5, "bonus"]:
        bonus = n == "bonus"
        path = ROOT / "booklets" / (f"{n}.yaml" if bonus else f"booklet-{n}.yaml")
        b = yaml.safe_load(path.read_text(encoding="utf-8"))
        cfg = {k: b[k] for k in R.DEFAULTS if k in b}
        stories = []
        for p in b["stories"]:
            st = R.build_story(ROOT / p, cfg)
            prepare_story(st, ROOT / p, ctx)
            # Bonus pages are surahs: label them by surah number, from "Quran 105".
            st["surah"] = st["source"].replace("Quran ", "") if bonus else None
            st["where"] = f"Surah {st['surah']}" if bonus else f"Story {st['number']}"
            st["all_q"] = all(w["q"] for s in st["sents"] for w in s["words"])
            stories.append(st)
        bdict = BookletDictionary(stories)
        level = cfg_site["levels"][n]
        dl = cfg_site["downloads"].get(n, [])
        labels = ["Whole booklet"] if bonus else part_labels(stories, b.get("parts", []))
        if len(dl) != len(labels):
            warn(f"site.yaml lists {len(dl)} downloads for booklet {n}, but booklets/booklet-{n}.yaml has {len(labels)} parts")
        cover = None
        if b.get("cover_image"):
            web = WEB / "img" / (Path(b["cover_image"]).stem + ".webp")
            if web.exists():
                cover = {"src": web.name, "w": sizes[web.name][0], "h": sizes[web.name][1]}
                ctx["images"].add(web.name)
            else:
                warn(f"booklet {n}: cover {b['cover_image']} is missing")
        booklet = {"n": n, "bonus": bonus, "key": "bonus" if bonus else f"b{n}", "label": "Bonus booklet" if bonus else f"Booklet {n}",
                   "dir": "bonus" if bonus else f"b{n}", "title": b["title"], "title_ar": b["title_ar"], "subtitle": b["subtitle"],
                   "intro": b["intro"], "howto": b["howto"], "stories": stories, "level": level, "cover": cover,
                   "downloads": [{"label": l, "url": u} for l, u in zip(labels, dl)], "glossary": R.glossary(stories),
                   "dict": bdict}
        (bonus_booklet if bonus else booklets).append(booklet)
        for st in stories:
            all_stories[st["id"]] = st

    sample = grade_sample(booklets[1]["stories"])
    site = cfg_site["site"]
    common = {"site": site, "booklets": booklets, "card_list": [booklets[0], *bonus_booklet, *booklets[1:]]}

    # home, about
    write(OUT / "index.html", env.get_template("index.html.j2").render(
        **common, root="", title=site["title"], sample=sample,
        description="Graded Arabic stories that take you from fully vowelled text to the bare page, with every word explained."))
    write(OUT / "about.html", env.get_template("about.html.j2").render(
        **common, root="", title="About", description="Sources, how the text was checked, licences and how to report a mistake."))

    n_pages = 2
    for b in [*booklets, *bonus_booklet]:
        d = OUT / b["dir"]
        root = "../"
        write(d / "index.html", env.get_template("booklet.html.j2").render(
            **common, root=root, b=b, title=f"{b['label']}: {b['title']}",
            description=b["level"]["adds"]))
        glossary = []
        slug_by_number = {st["number"]: st["slug"] for st in b["stories"]}
        where = {st["number"]: st["where"].lower() for st in b["stories"]}
        for g in b["glossary"]:
            letters = "".join(reversed(g["root"].split()))
            glossary.append({**g, "plain_root": letters, "slug": slug_by_number[g["story"]], "where": where[g["story"]],
                             "q": " ".join([norm(g["ar"]), norm(letters), g["en"].lower()])})
        write(d / "glossary.html", env.get_template("glossary.html.j2").render(
            **common, root=root, b=b, glossary=glossary, title=f"Glossary, {b['label'].lower()}",
            description=f"Every dictionary word of the {b['label'].lower()}, ordered by root and searchable."))
        n_pages += 2
        sts = b["stories"]
        for i, st in enumerate(sts):
            cards = attach_cards(st, b["dict"])
            nw = sum(1 for s in st["sents"] for w in s["words"])
            total += nw
            matched += sum(1 for s in st["sents"] for w in s["words"] if w["card"])
            write(d / st["file"], env.get_template("story.html.j2").render(
                **common, root=root, b=b, st=st, cards=cards, prev=sts[i - 1] if i else None,
                next=sts[i + 1] if i + 1 < len(sts) else None,
                title=f"{st['title_en']}, {b['label'].lower()}", description=f"{st['where']} of the {b['label'].lower()}: {st['title_en']}."))
            n_pages += 1

    # static files
    for name in ("site.css", "site.js"):
        shutil.copy2(TPL / name, OUT / name)
    shutil.copy2(ROOT / "templates" / "tokens.css", OUT / "tokens.css")
    shutil.copytree(WEB / "fonts", OUT / "fonts")
    (OUT / "img").mkdir()
    for name in sorted(ctx["images"]):
        shutil.copy2(WEB / "img" / name, OUT / "img" / name)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    problems = check_links()
    for p in problems:
        warn(p)
    print(f"wrote {OUT.relative_to(ROOT)}: {n_pages} pages, {len(ctx['images'])} pictures, "
          f"{matched} of {total} words linked to a dictionary entry")
    for w in warnings:
        print("WARNING:", w)
    return 1 if warnings else 0


# ---------- link check ----------

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs = set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])


def check_links() -> list[str]:
    pages = {}
    for f in OUT.rglob("*.html"):
        p = Links()
        p.feed(f.read_text(encoding="utf-8"))
        pages[f] = p
    problems = []
    for f, p in pages.items():
        for ref in p.refs:
            if re.match(r"^(https?:|mailto:|data:)", ref):
                continue
            path, _, frag = ref.partition("#")
            target = f if not path else (f.parent / path).resolve()
            if not target.exists():
                problems.append(f"{f.relative_to(OUT)}: broken link {ref}")
            elif frag and target.suffix == ".html" and frag not in pages.get(target, p).ids:
                problems.append(f"{f.relative_to(OUT)}: no anchor #{frag} in {target.name}")
    css = (OUT / "site.css").read_text(encoding="utf-8")
    for u in re.findall(r'url\("([^"]+)"\)', css):
        if not (OUT / u).exists():
            problems.append(f"site.css: missing {u}")
    return problems


if __name__ == "__main__":
    sys.exit(build())
