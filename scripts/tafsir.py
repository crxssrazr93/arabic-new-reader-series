"""Fetch and cache tafsir text for an ayah from the quran.com API (v4), as plain text.

Usage:
  python scripts/tafsir.py 12:20                 all default tafsirs for one ayah
  python scripts/tafsir.py 12:20 18:21 --only baghawi ibn-kathir-en
  python scripts/tafsir.py --list

Cache: lexicon/sources/tafsir/<name>/<surah>_<ayah>.txt (not committed: the English
translations are copyrighted; the cache is for checking only, never for copying text in).
A long passage often covers several ayat; the API returns it for each ayah in the passage.
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "lexicon" / "sources" / "tafsir"
SOURCES = {
    "ibn-kathir": 14, "ibn-kathir-en": 169, "tabari": 15, "qurtubi": 90,
    "baghawi": 94, "saadi": 91, "muyassar": 16, "maarif-en": 168,
}


def text_of(name: str, ref: str) -> str:
    s, a = ref.split(":")
    path = CACHE / name / f"{int(s)}_{int(a)}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    url = f"https://api.quran.com/api/v4/tafsirs/{SOURCES[name]}/by_ayah/{int(s)}:{int(a)}"
    req = urllib.request.Request(url, headers={"User-Agent": "arabic-readers-check/1.0"})
    for attempt in range(3):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=30))
            break
        except Exception as e:  # network hiccup: wait and retry
            if attempt == 2:
                return f"[fetch failed: {e}]"
            time.sleep(2 * (attempt + 1))
    raw = data.get("tafsir", {}).get("text", "") or ""
    raw = re.sub(r"<(br|/p|/h\d)\s*/?>", "\n", raw)
    txt = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
    covers = ", ".join(data.get("tafsir", {}).get("verses", {}).keys())
    out = f"[{name} on {ref}; passage covers {covers}]\n{txt}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out, encoding="utf-8")
    time.sleep(0.3)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("refs", nargs="*")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print("\n".join(f"{k} (quran.com id {v})" for k, v in SOURCES.items()))
        return 0
    for ref in a.refs:
        for name in a.only or SOURCES:
            t = text_of(name, ref)
            print(f"{CACHE.relative_to(ROOT)}/{name}/{ref.replace(':', '_')}.txt  ({len(t)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
