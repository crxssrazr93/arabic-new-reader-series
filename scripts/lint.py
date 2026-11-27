"""Lint the story files and scan the rendered PDFs.

Story rules work on the fully vowelled source text (Quran words, flag q, are skipped:
verify_ayat.py checks those against Tanzil). PDF rules look at what was printed.

Severity: error (almost certainly wrong), warn (probably wrong, look), info (worth a glance).

Usage:
  python scripts/lint.py                 all stories and all build/*.pdf
  python scripts/lint.py stories/booklet-2/02-yusuf-wal-jubb.yaml
  python scripts/lint.py --no-pdf
Writes review/lint.md and prints a summary. Exit code 1 when there are errors.
"""
import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arabic import strip  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

FATHA, DAMMA, KASRA, SUKUN, SHADDA = "َ", "ُ", "ِ", "ْ", "ّ"
FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
DAGGER = "ٰ"
VOWELS = {FATHA, DAMMA, KASRA, SUKUN, FATHATAN, DAMMATAN, KASRATAN}
TANWIN = {FATHATAN, DAMMATAN, KASRATAN}
MARKS = VOWELS | {SHADDA, DAGGER, "ٓ", "ٔ", "ٕ"}

SUN = set("تثدذرزسشصضطظلن")

findings: list[dict] = []


def add(sev, where, rule, msg):
    findings.append({"sev": sev, "where": where, "rule": rule, "msg": msg})


def clusters(word: str) -> list[tuple[str, set]]:
    out = []
    for ch in word:
        if ch in MARKS and out:
            out[-1][1].add(ch)
        elif ch in MARKS:  # a mark before any letter: keep it on an empty cluster
            out.append(("", {ch}))
        else:
            out.append((ch, set()))
    return out


def lint_word(w: str, where: str):
    cs = clusters(w)
    if not cs:
        return
    letters = [c for c, _ in cs]
    for i, (c, m) in enumerate(cs):
        v = m & VOWELS
        if len(v) > 1:
            add("error", where, "T1 two vowels", f"{w}: letter {c} carries {len(v)} vowel marks")
        if m & TANWIN:
            last = i == len(cs) - 1
            before_alif = i == len(cs) - 2 and letters[-1] in "اى" and FATHATAN in m
            if not (last or before_alif):
                add("error", where, "T2 tanwin mid-word", f"{w}: tanwin on {c}, not on the last letter")
    lc, lm = cs[-1]
    if FATHATAN in lm and lc not in "ةءئؤأ" and not (lc == "ء" or (len(cs) > 1 and letters[-2] == "ا" and lc == "ء")):
        add("error", where, "T3 tanwin fath without alif", f"{w}: fathatan on {lc} needs a following alif ({w}ا)")
    if article_end(cs) is not None and any(m & TANWIN for _, m in cs):
        add("error", where, "T4 tanwin with al", f"{w}: a word with ال cannot take tanwin")
    if "ةًا" in w or "ةا" in strip(w):
        add("error", where, "T5 ta marbuta alif", f"{w}: no alif is written after ta marbuta")
    if SUKUN in cs[0][1] and strip(w) not in ("بن",):  # بْنُ between two names drops its alif
        add("error", where, "T6 initial sukun", f"{w}: a word cannot start with sukun")
    for i in range(1, len(cs)):
        c, m = cs[i]
        pc, pm = cs[i - 1]
        nxt = cs[i + 1] if i + 1 < len(cs) else None
        if m:
            continue  # a marked letter is a consonant, not a long vowel
        if c == "ا":
            if nxt and (nxt[0] == "ل" or SUKUN in nxt[1] or SHADDA in nxt[1]):
                continue  # hamzat al-wasl after a prefix (بِالْ, وَاسْتَ)
            if i == len(cs) - 1 and pc == "و":
                continue  # alif after plural waw (ذَهَبُوا)
            if pc == "م" and "مائة" in strip(w):
                continue  # مِائَة: the classical spelling keeps a silent alif
            if pm & {KASRA, DAMMA}:
                add("warn", where, "T7 long vowel", f"{w}: alif after {'kasra' if KASRA in pm else 'damma'} on {pc}")
        elif c == "ي" and i < len(cs) - 1 or c == "ي" and pm:
            if FATHA in pm:
                add("warn", where, "T7 diphthong", f"{w}: ي after fatha has no sukun (ay) and no vowel")
            elif DAMMA in pm:
                add("warn", where, "T7 long vowel", f"{w}: bare ي after damma on {pc}")
        elif c == "و":
            if i == len(cs) - 2 and letters[-1] == "ا":
                pass
            if FATHA in pm:
                add("warn", where, "T7 diphthong", f"{w}: و after fatha has no sukun (aw) and no vowel")
            elif KASRA in pm:
                add("warn", where, "T7 long vowel", f"{w}: bare و after kasra on {pc}")
    # The article: the lam is silent (sukun before a moon letter) or the next letter doubles (sun letter).
    k = article_end(cs)
    if k is not None and k < len(cs):
        lam_marks, first = cs[k - 1][1], cs[k]
        if first[0] in SUN and first[0] != "ت" and SUKUN in lam_marks:  # الْتَفَتَ is Form VIII, not the article
            add("warn", where, "T8 sun letter", f"{w}: lam has sukun before the sun letter {first[0]}; expected {first[0]} with shadda")
        if first[0] not in SUN and not lam_marks and first[1]:
            add("info", where, "T8 moon letter", f"{w}: moon letter after ال: lam usually shows sukun (الْ)")


def article_end(cs: list) -> int | None:
    """Index of the first noun letter after a definite article (with any one-letter prefix), else None."""
    letters = "".join(c for c, _ in cs)
    for pre in ("", "و", "ف", "ب", "ك", "وب", "فب", "وك"):
        if letters.startswith(pre + "ال") and len(letters) > len(pre) + 2:
            i = len(pre) + 1  # cluster index of the lam
        elif letters.startswith(pre + "لل") and len(letters) > len(pre) + 2 and pre in ("", "و", "ف"):
            i = len(pre) + 1  # لِلْ: the alif drops after li-
        else:
            continue
        if any(m & VOWELS for _, m in cs[len(pre):i]) and not letters.startswith(pre + "لل"):
            continue  # the alif carries a vowel: not the article
        lam, nxt = cs[i][1], cs[i + 1][1]
        if SUKUN in lam or (not lam & VOWELS and SHADDA not in lam and SHADDA in nxt):
            return i + 1
    return None


def gloss_checks(ar: str, gl: str, where: str):
    if gl.count("(") != gl.count(")"):
        add("error", where, "G1 brackets", f"{ar}: gloss '{gl}' has unbalanced brackets (cut by an unquoted comma?)")
    b = strip(ar)
    if gl and ar.endswith("َيْنِ") and not re.search(r"\btwo\b|\bboth\b|\bpair\b", gl, re.I) and len(b) > 3:
        add("info", where, "G2 dual", f"{ar}: dual ending but gloss '{gl}' does not say two")


def lint_story(path: Path):
    s = yaml.safe_load(path.read_text(encoding="utf-8"))
    sid = s.get("id", path.stem)
    n_sent = len(s.get("sentences", []))
    for n, sent in enumerate(s.get("sentences", []), 1):
        where = f"{sid} s{n}"
        en = sent.get("en", "")
        if en.count("(") != en.count(")"):
            add("error", where, "E1 brackets", f"English line has unbalanced brackets: {en}")
        if en and en.rstrip()[-1] not in ".!?:;,'\")":
            add("warn", where, "E2 punctuation", f"English line has no closing punctuation: {en}")
        english_checks(en, where)
        toks = []
        for w in sent.get("words", []):
            if isinstance(w, str):
                continue
            ar = str(w[0])
            gl = w[1] if len(w) > 1 and isinstance(w[1], str) else ""
            flags = str(w[2]) if len(w) > 2 else ""
            toks.append((ar, gl, flags))
            if "q" in flags:
                continue
            lint_word(ar, where)
            gloss_checks(ar, gl, where)
            english_checks(gl, where, gloss=True)
        sentence_checks(toks, where)
    for ill in s.get("illustrations", []):
        if not 1 <= ill.get("before", 0) <= n_sent:
            add("error", f"{sid} ill", "I1 picture index", f"{ill.get('file')}: before {ill.get('before')} is outside 1..{n_sent}")
        if not (ROOT / "assets" / "illustrations" / ill["file"]).exists():
            add("error", f"{sid} ill", "I2 picture file", f"{ill['file']} is missing")
    for e in s.get("dictionary", []):
        where = f"{sid} dict {e.get('ar')}"
        for key in ("en", "note"):
            v = str(e.get(key, ""))
            if v.count("(") != v.count(")"):
                add("error", where, "G1 brackets", f"{key} has unbalanced brackets: {v}")
            english_checks(v, where)
        if re.search(r"\bform\s+(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", str(e.get("pattern", "")) + str(e.get("note", "")), re.I):
            add("warn", where, "L33 bab names", "uses a Form number; name the bab (docs/house_style.md)")
        pos = e.get("pos") or [""]
        if str(pos[0]).startswith("فعل"):
            if not e.get("present") or not e.get("bab"):
                add("warn", where, "D1 verb card", "verb entry needs present: and bab: (docs/house_style.md)")
            else:
                bab_check(str(e["ar"]), str(e["present"]), str(e["bab"]), where)
        lint_word(str(e.get("ar", "")), where)
    for key in ("grammar", "tip"):
        box = s.get(key) or {}
        english_checks(str(box.get("body", "")), f"{sid} {key}")




JARR = {"فِي", "مِنْ", "مِنَ", "مِنِ", "إِلَى", "عَلَى", "عَنْ", "عَنِ"}  # حَتَّى left out: it is also "even" and governs verbs
INNA = {"إِنَّ", "أَنَّ", "لَكِنَّ", "كَأَنَّ", "لَيْتَ", "لَعَلَّ"}
JAZM = {"لَمْ", "لَمَّا"}
NASB = {"لَنْ", "كَيْ", "لِكَيْ"}
DIPTOTE_NAMES = {"إبراهيم", "إسماعيل", "إسحاق", "يعقوب", "يوسف", "فرعون", "هارون", "سليمان", "عثمان",
                 "عمر", "أحمد", "مريم", "فاطمة", "عائشة", "زينب", "مكة", "مصر", "رمضان", "يونس", "موسى",
                 "عيسى", "زكريا", "يحيى", "إدريس", "داود", "أيوب", "آدم"}
NAMES_EN = {r"\bMoses\b": "Musa", r"\bAbraham\b": "Ibrahim", r"\bJoseph\b": "Yusuf", r"\bNoah\b": "Nuh",
            r"\bJesus\b": "Isa", r"\bJonah\b": "Yunus", r"\bSolomon\b": "Sulayman", r"\bJacob\b": "Ya'qub",
            r"\bMohammed\b": "Muhammad", r"\bPharaoh\b": "Fir'awn (if the house style wants it)"}
BANNED_EN = re.compile(r"\b(myth|legend|fairy tale|Mohammedan)\b", re.I)


MABNI_DAMMA = {"قبل", "بعد", "حيث", "منذ"}  # قَبْلُ، بَعْدُ cut off from idafa, حَيْثُ: built on damma
PRONOUNS = ("هما", "هم", "هن", "ها", "ه", "كما", "كم", "كن", "ك", "نا", "ي")


def final_marks(w: str) -> set:
    """Marks of the case ending: on the last letter, or before an attached pronoun.
    Returns {'?'} when the ending cannot be told apart from an attached pronoun."""
    cs = clusters(w)
    if not cs:
        return set()
    base = strip(w)
    if base in MABNI_DAMMA or base.lstrip("وفمن") in MABNI_DAMMA:
        return {"MABNI"}
    for suf in PRONOUNS:
        if base.lstrip("وفب") in ("الله", "لله"):
            break  # the ه of اللَّه is a root letter
        if suf in ("ه", "ك") and SUKUN in cs[-1][1]:
            continue  # أَتْرُكْ: a root letter with sukun, not a pronoun
        if base.endswith(suf) and len(base) - len(suf) >= 2:
            k = len(cs) - len(suf) - 1  # the letter before the pronoun carries the case vowel
            if base.endswith("ه") and SUKUN in cs[k][1]:
                return {SUKUN}  # يَقْتُلْهُ: the jussive sits before the pronoun
            return cs[k][1] if k >= 0 else set()
    c, m = cs[-1]
    if c in "اى" and len(cs) > 1:
        return cs[-2][1] | {"ALIF"}
    return m


def sentence_checks(toks: list[tuple[str, str, str]], where: str):
    """Government rules over neighbouring words. toks: (arabic, gloss, flags)."""
    for i, (ar, _, fl) in enumerate(toks[:-1]):
        nxt, _, nfl = toks[i + 1]
        if "q" in fl or "q" in nfl:
            continue
        fm = final_marks(nxt)
        bare = strip(nxt)
        name = bare.lstrip("وفب")
        if ar in JARR:
            if fm & {DAMMA, DAMMATAN} and not bare.startswith(("هو", "هم", "هي", "أنت", "نحن")):
                add("warn", where, "L17 jarr", f"{ar} {nxt}: the noun after a harf jarr should be majrur, not marfu'")
        if ar in INNA and fm & {DAMMA, DAMMATAN} and strip(nxt) not in ("له", "لها", "لهم", "لك", "لي", "لنا", "فيه", "فيها", "عليه", "منه"):
            add("warn", where, "L19 inna", f"{ar} {nxt}: the noun after {ar} is mansub, not marfu'")
        if ar in JAZM and fm & {DAMMA} and not nxt.endswith(("ونَ", "ينَ", "انِ")):
            add("warn", where, "L21 jazm", f"{ar} {nxt}: the verb after {ar} is majzum; damma is right only if a weak final letter dropped (لَمْ يَدْعُ)")
        if ar in JAZM and nxt.endswith(("ونَ", "ينَ", "انِ")) and nxt.startswith(("يَ", "تَ", "يُ", "تُ")):
            add("error", where, "L21 jazm", f"{ar} {nxt}: the five verbs drop their nun after {ar}")
        if ar in NASB and fm & {DAMMA}:
            add("error", where, "L22 nasb", f"{ar} {nxt}: the verb after {ar} is mansub (fatha), not damma")
    for ar, _, fl in toks:
        if "q" in fl:
            continue
        b = strip(ar).lstrip("وفبل")
        if b in DIPTOTE_NAMES and final_marks(ar) & (TANWIN | {KASRA}):
            add("warn", where, "L13 diptote", f"{ar}: a diptote name takes no tanwin and no kasra (fatha in jarr)")


MUJARRAD = {("َ", "ُ"): "نصر", ("َ", "ِ"): "ضرب", ("َ", "َ"): "فتح", ("ِ", "َ"): "سمع", ("ِ", "ِ"): "حسب", ("ُ", "ُ"): "كرم"}
MAZID = {"أفعل": "الإفعال", "فعّل": "التفعيل", "فاعل": "المفاعلة", "تفعّل": "التفعل", "تفاعل": "التفاعل",
         "انفعل": "الانفعال", "افتعل": "الافتعال", "استفعل": "الاستفعال"}


def bab_check(past: str, present: str, bab: str, where: str):
    """For a sound three letter verb, the bab must match the two middle vowels."""
    bb = strip(bab).replace("باب", "").strip()
    pc, rc = clusters(past), clusters(present)
    if len(strip(past)) == 3 and len(strip(present)) == 4 and len(pc) == 3 and len(rc) == 4:
        if past[0] in "أآ" or strip(past)[1] in "اوي" or strip(present)[2] in "اوي" or SHADDA in pc[1][1] | pc[2][1]:
            return  # hollow, defective or doubled: the vowels do not show the bab
        key = (next(iter(pc[1][1] & {FATHA, KASRA, DAMMA}), ""), next(iter(rc[2][1] & {FATHA, KASRA, DAMMA}), ""))
        want = MUJARRAD.get(key)
        if want and want not in strip(bb).replace("ال", ""):
            add("warn", where, "D2 bab", f"{past} {present}: middle vowels give باب {want}, entry says {bab}")


PROPHET = re.compile(r"\b(the Prophet|Messenger of Allah|Muhammad)\b(?!'s)(?!\s*ﷺ)")


def english_checks(text: str, where: str, gloss: bool = False):
    if not gloss and PROPHET.search(text):
        add("warn", where, "H1 salawat", f"'{PROPHET.search(text).group(0)}' without ﷺ: {text[:80]}")
    for pat, good in NAMES_EN.items():
        if re.search(pat, text):
            add("warn", where, "L38 names", f"uses {re.search(pat, text).group(0)}; house style is {good}")
    if BANNED_EN.search(text):
        add("warn", where, "L40 wording", f"'{BANNED_EN.search(text).group(0)}' is not used for religious narratives")



def scan_pdf(pdf: Path):
    name = pdf.name
    fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout
    for line in fonts.splitlines()[2:]:
        f = line.split()[0].split("+")[-1]
        if not re.match("(Charis|Scheherazade|Amiri)", f):
            add("error", name, "P1 fallback font", f"{f} is used: some characters are missing from the booklet fonts")
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    if pages % 2:
        add("error", name, "P2 odd pages", f"{pages} pages: double sided printing needs an even count")
    if pages > 48:
        add("warn", name, "P3 thick", f"{pages} pages ({pages // 4} sheets) is a lot for one staple")
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    for i, pg in enumerate(text.split("\f")[:pages], 1):
        body = re.sub(r"\s+", " ", pg).strip()
        if i > 1 and len(body) < 120 and "Notes" not in body:
            add("warn", name, "P4 near blank", f"page {i} holds only: {body[:80]!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args()
    stories = [Path(p) for p in a.paths] or sorted((ROOT / "stories").glob("**/*.yaml"))

    for p in stories:
        lint_story(p)
    if not a.no_pdf and not a.paths:
        for pdf in sorted((ROOT / "build").glob("*.pdf")):
            if re.match(r"(booklet-\d-part-\d|bonus|booklet-\d)\.pdf$", pdf.name):
                scan_pdf(pdf)
    order = {"error": 0, "warn": 1, "info": 2}
    findings.sort(key=lambda f: (order[f["sev"]], f["rule"], f["where"]))
    out = ROOT / "review" / "lint.md"
    out.parent.mkdir(exist_ok=True)
    lines = ["# Lint report", "", "| Severity | Rule | Where | Finding |", "|---|---|---|---|"]
    lines += [f"| {f['sev']} | {f['rule']} | {f['where']} | {f['msg'].replace('|', '/')} |" for f in findings]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    counts = defaultdict(int)
    for f in findings:
        counts[(f["sev"], f["rule"])] += 1
    for (sev, rule), n in sorted(counts.items(), key=lambda x: (order[x[0][0]], x[0][1])):
        print(f"{sev:5} {n:4}  {rule}")
    print(f"wrote {out.relative_to(ROOT)}")
    return 1 if any(f["sev"] == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
