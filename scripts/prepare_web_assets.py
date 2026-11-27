"""One-off preparation of the website's fonts and pictures, written to assets/web/.

Run it when the illustrations or the installed fonts change; commit the result so the
GitHub Actions build (which has no fonts and no Pillow) can copy it as is.

  python scripts/prepare_web_assets.py

Fonts:    Scheherazade New regular and bold (all glyphs), Charis SIL regular, bold and italic
          (Latin, Latin Extended and punctuation only), all as woff2, plus the licence text.
Pictures: every PNG in assets/illustrations as a 1200 px wide WebP, plus sizes.json.
Needs Pillow, fontTools and brotli (all in .venv).
"""
import json
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "web"
FONT_DIR = Path.home() / ".local" / "share" / "fonts"
SYSTEM_FONTS = Path("/usr/share/fonts/TTF")
LICENCE = Path("/usr/share/licenses/ttf-scheherazade-new/OFL.txt")

# Latin, Latin Extended, IPA and modifier letters (ʿ ʾ), combining marks, Latin Extended Additional (ḥ ṣ ḍ ṭ ẓ), general punctuation.
LATIN = "U+0000-024F,U+02B0-02FF,U+0300-036F,U+1E00-1EFF,U+2000-206F,U+20A0-20CF,U+2190-21FF"

FONTS = [
    # (source file, output name, unicode subset or None for everything)
    (SYSTEM_FONTS / "ScheherazadeNew-Regular.ttf", "ScheherazadeNew-Regular.woff2", None),
    (SYSTEM_FONTS / "ScheherazadeNew-Bold.ttf", "ScheherazadeNew-Bold.woff2", None),
    (FONT_DIR / "CharisSIL" / "Charis-Regular.ttf", "Charis-Regular.woff2", LATIN),
    (FONT_DIR / "CharisSIL" / "Charis-Bold.ttf", "Charis-Bold.woff2", LATIN),
    (FONT_DIR / "CharisSIL" / "Charis-Italic.ttf", "Charis-Italic.woff2", LATIN),
]


def make_font(src: Path, dest: Path, unicodes: str | None) -> None:
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.glyph_names = False
    font = subset.load_font(str(src), opts)
    sub = subset.Subsetter(opts)
    if unicodes:
        wanted = []
        for part in unicodes.split(","):
            a, _, b = part.partition("-")
            lo = int(a[2:], 16)
            hi = int(b[2:], 16) if b else lo
            wanted += range(lo, hi + 1)
        sub.populate(unicodes=wanted)
    else:
        sub.populate(glyphs=font.getGlyphOrder())
    sub.subset(font)
    subset.save_font(font, str(dest), opts)


def notice(src: Path) -> str:
    names = TTFont(str(src))["name"]
    return f"{names.getDebugName(1)} {names.getDebugName(2)}\n{names.getDebugName(0)}\n"


def embedded_licence(src: Path) -> str:
    """The licence text the font file itself carries (name ID 13)."""
    return TTFont(str(src))["name"].getDebugName(13)


def main() -> None:
    (OUT / "fonts").mkdir(parents=True, exist_ok=True)
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    notes = []
    for src, name, unicodes in FONTS:
        make_font(src, OUT / "fonts" / name, unicodes)
        notes.append(notice(src))
        print("font", name, (OUT / "fonts" / name).stat().st_size // 1024, "KB")
    (OUT / "fonts" / "OFL.txt").write_text(LICENCE.read_text(encoding="utf-8"), encoding="utf-8")
    (OUT / "fonts" / "OFL-Charis.txt").write_text(embedded_licence(FONTS[2][0]) + "\n", encoding="utf-8")
    (OUT / "fonts" / "NOTICE.txt").write_text(
        "Fonts on this site, all under the SIL Open Font License 1.1 (OFL.txt for Scheherazade New, OFL-Charis.txt for Charis).\n\n"
        + "\n".join(notes), encoding="utf-8")

    sizes = {}
    for png in sorted((ROOT / "assets" / "illustrations").glob("*.png")):
        im = Image.open(png).convert("RGB")
        if im.width > 1200:
            im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
        dest = OUT / "img" / (png.stem + ".webp")
        im.save(dest, "WEBP", quality=80, method=6)
        sizes[dest.name] = [im.width, im.height]
    (OUT / "img" / "sizes.json").write_text(json.dumps(sizes, indent=0), encoding="utf-8")
    total = sum(p.stat().st_size for p in (OUT / "img").glob("*.webp"))
    print(f"{len(sizes)} pictures, {total // 1024 // 1024} MB")


if __name__ == "__main__":
    main()
