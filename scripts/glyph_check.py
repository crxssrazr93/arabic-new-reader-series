"""Find characters in the rendered PDFs that the booklet fonts cannot draw.

WeasyPrint silently falls back to a system font (seen: Times New Roman) for such
characters. This lists each one, the file and the page, so the source can be fixed.

Usage: python scripts/glyph_check.py build/*.pdf
"""
import subprocess
import sys
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont

FONT_NAMES = ("Charis", "Scheherazade")


def font_files() -> list[Path]:
    out = subprocess.run(["fc-list", "--format", "%{file}\n"], capture_output=True, text=True).stdout
    return [Path(p) for p in out.splitlines() if any(n.lower() in p.lower() for n in FONT_NAMES)]


def covered() -> set[int]:
    cps: set[int] = set()
    for f in font_files():
        try:
            cps |= set(TTFont(f, fontNumber=0, lazy=True).getBestCmap())
        except Exception:
            pass
    return cps


def main(paths: list[str]) -> int:
    ok = covered() | {0x0A, 0x0C, 0x20}
    found = 0
    for p in paths:
        pages = subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True).stdout.split("\f")
        for n, text in enumerate(pages, 1):
            for line in text.splitlines():
                for ch in sorted(set(line)):
                    if ord(ch) not in ok:
                        found += 1
                        name = unicodedata.name(ch, "?")
                        print(f"{Path(p).name} p{n}: U+{ord(ch):04X} {name} | {line.strip()[:90]}")
    print(f"{found} uncovered character uses")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
