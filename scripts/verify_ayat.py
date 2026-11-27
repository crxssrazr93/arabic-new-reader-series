"""Check every ayah hook and Quran quote in story files against the Tanzil text.

The letters we type must match a run of whole words in the cited ayah. On the page,
the renderer prints Tanzil's own vowelled words, never ours.

Usage: python scripts/verify_ayat.py stories/booklet-1/*.yaml
Exit code 1 if anything fails.
"""
import sys
from pathlib import Path

import yaml

from arabic import norm, tanzil_span

ROOT = Path(__file__).resolve().parent.parent
TANZIL = ROOT / "lexicon" / "sources" / "quran-simple.txt"


def load_quran() -> dict[str, str]:
    ayat = {}
    for line in TANZIL.read_text(encoding="utf-8").splitlines():
        parts = line.split("|")
        if len(parts) == 3 and parts[0].isdigit():
            ayat[f"{parts[0]}:{parts[1]}"] = parts[2]
    return ayat


def main(paths: list[str]) -> int:
    quran = load_quran()
    failures = checks = 0
    for path in paths:
        story = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        items = [(f"dictionary {e['ar']}", e["ayah"]) for e in story.get("dictionary", []) if "ayah" in e]
        for n, sent in enumerate(story.get("sentences", []), 1):
            if "quote" not in sent:
                continue
            items.append((f"sentence {n} quote", sent["quote"]))
            quoted = " ".join(w[0] for w in sent["words"] if len(w) > 2 and w[2] == "q")
            if norm(quoted) != norm(sent["quote"]["text"]):
                print(f"FAIL {path}: sentence {n}: quoted words differ from quote text")
                failures += 1
        for label, ayah in items:
            checks += 1
            if label.startswith("dictionary") and not ayah.get("en"):
                print(f"FAIL {path}: {label}: ayah {ayah['ref']} has no English meaning (add en:)")
                failures += 1
            source = quran.get(ayah["ref"])
            if source is None:
                print(f"FAIL {path}: {label}: no ayah {ayah['ref']}")
                failures += 1
            elif tanzil_span(source, ayah["text"]) is None:
                print(f"FAIL {path}: {label}: words not found in {ayah['ref']}")
                print(f"     ours:   {ayah['text']}\n     tanzil: {source}")
                failures += 1
    print(f"{checks} ayah references checked, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
