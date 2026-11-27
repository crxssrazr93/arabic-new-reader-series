"""Small Arabic text helpers shared by the scripts."""
import re

# Harakat, tanwin, shadda, sukun, dagger alif, small high marks used by Tanzil, tatweel.
DIACRITICS = re.compile("[ؐ-ًؚ-ٰٟۖ-ۭـ]")
ALIF_FORMS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي"})


def strip(text: str) -> str:
    """Remove all vowel marks and tatweel."""
    return DIACRITICS.sub("", text)


def norm(text: str) -> str:
    """Bare letters with alif and ya forms unified, single spaces. For matching only."""
    text = strip(text).translate(ALIF_FORMS)
    text = re.sub(r"[^ء-ي ]", " ", text)
    return " ".join(text.split())


def tanzil_span(source: str, text: str) -> str | None:
    """Return the exact vowelled words of `source` (a Tanzil ayah) that spell `text`.

    Matching is on bare letters, so our typed vowel marks never reach the page.
    Pause signs inside the span (e.g. ۛ) are kept as Tanzil has them.
    """
    want = norm(text).split()
    words = source.split()
    keyed = [(i, norm(w)) for i, w in enumerate(words) if norm(w)]
    for s in range(len(keyed) - len(want) + 1):
        if [k for _, k in keyed[s:s + len(want)]] == want:
            first, last = keyed[s][0], keyed[s + len(want) - 1][0]
            return " ".join(words[first:last + 1])
    return None


SHADDA = "ّ"
FATHATAN = "ً"
MARK_RE = "[ؐ-ًؚ-ٰٟـ]"


def _clusters(word: str) -> list[str]:
    return re.findall(f"[^ؐ-ًؚ-ٰٟـ]{MARK_RE}*", word)


def strip_final(word: str) -> str:
    """Pausal form: drop the marks on the last letter (keep shadda and dagger alif).

    A final bare alif or alif maqsura after fathatan (كَثِيرًا) loses the fathatan too.
    """
    cs = _clusters(word)
    if not cs:
        return word

    def bare(c: str) -> str:
        return c[0] + "".join(m for m in c[1:] if m in (SHADDA, "ٰ"))

    if len(cs) >= 2 and cs[-1] in ("ا", "ى") and FATHATAN in cs[-2]:
        # Read -ā at a stop (kawkabā): the fathatan becomes a plain fatha before the alif.
        cs[-2] = cs[-2].replace(FATHATAN, "َ")
    elif "ْ" in cs[-1]:
        pass  # already silent (أَبِيهِمْ): keep the sukun
    else:
        cs[-1] = bare(cs[-1])
    return "".join(cs)


def keep_shadda(word: str) -> str:
    """All marks removed except shadda."""
    return "".join(c[0] + (SHADDA if SHADDA in c else "") for c in _clusters(word))


# Letters that may stand in for a root letter in a written word.
ROOT_EQUIV = {
    "ء": "ءأإآؤئا",
    "أ": "ءأإآؤئا",
    "و": "وايىآ",
    "ي": "يايىو",
}


def mark_root(word: str, root: str) -> list[tuple[str, bool]]:
    """Split a vowelled word into (chunk, is_root_letter) pieces.

    Each chunk is one base letter plus the marks that follow it. Root letters are
    matched greedily in order. A doubled root letter (e.g. أمم) can match one
    letter carrying shadda.
    """
    chunks = re.findall(r"[^ؐ-ًؚ-ٰٟـ][ؐ-ًؚ-ٰٟـ]*", word)
    letters = list(root)
    out, i = [], 0
    for ch in chunks:
        base = ch[0]
        hit = False
        if i < len(letters):
            want = letters[i]
            if base == want or base in ROOT_EQUIV.get(want, ""):
                hit = True
                i += 1
                # Shadda on this letter covers a doubled root letter.
                if "ّ" in ch and i < len(letters) and letters[i] == want:
                    i += 1
        out.append((ch, hit))
    return out
