"""Generate every missing illustration named in story and booklet files.

Each illustration's prompt is its `prompt` field if present, else its `alt` text.
Images use the pinned `arabic-readers` style (snippet + reference image) on the
Codex backend, 3 at a time. Existing files are never overwritten.

Usage: python scripts/illustrate.py stories/booklet-1/*.yaml booklets/booklet-1.yaml [--dry-run]
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "illustrations"
IMAGE_USE = Path.home() / ".local" / "bin" / "image-use"  # real binary; the PATH wrapper forces the web backend
POLICY = (" Draw only the buildings and objects named here: no mosque, minaret or palm tree unless asked."
          " Remember: no text, no animals or birds, no faces; people only as tiny featureless silhouettes."
          " Never depict a prophet or companion in any form.")


def jobs(paths: list[str]) -> list[tuple[Path, str, str]]:
    out = []
    for p in paths:
        data = yaml.safe_load(Path(p).read_text(encoding="utf-8"))
        for ill in data.get("illustrations", []):
            out.append((OUT / ill["file"], ill.get("prompt", ill["alt"]), "1536x1024"))
        if data.get("cover_image"):
            out.append((OUT / data["cover_image"], data.get("cover_prompt", data["title"]), "1536x1024"))
    return [j for j in out if not j[0].exists()]


def run(job: tuple[Path, str, str]) -> str:
    path, prompt, size = job
    cmd = [str(IMAGE_USE), prompt + POLICY, "--backend", "codex", "--style", "arabic-readers",
           "--size", size, "-o", str(path), "--quiet", "--no-progress", "--timeout", "420"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return f"{'ok  ' if r.returncode == 0 and path.exists() else 'FAIL'} {path.name}" + \
           ("" if r.returncode == 0 else f"  {r.stderr.strip()[-200:]}")


def main(args: list[str]) -> int:
    dry = "--dry-run" in args
    todo = jobs([a for a in args if a != "--dry-run"])
    print(f"{len(todo)} illustrations missing")
    if dry:
        for p, prompt, _ in todo:
            print(f"  {p.name}: {prompt}")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as ex:
        for line in ex.map(run, todo):
            print(line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
