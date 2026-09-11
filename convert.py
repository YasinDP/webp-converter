#!/usr/bin/env python3
"""Convert images in input/ to WebP in output/. Offline, Pillow only.

  python3 convert.py                 # quality 80
  python3 convert.py -q 90           # quality
  python3 convert.py --lossless
  python3 convert.py -i src -o dst
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".ico"}
ROOT = Path(__file__).parent


def convert(src: Path, dst: Path, quality: int, lossless: bool) -> None:
    with Image.open(src) as im:
        animated = getattr(im, "n_frames", 1) > 1
        if not animated and im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "transparency" in im.info or "A" in im.getbands() else "RGB")
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "WEBP", quality=quality, lossless=lossless,
                method=6, save_all=animated, minimize_size=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-i", "--input", type=Path, default=ROOT / "input")
    p.add_argument("-o", "--output", type=Path, default=ROOT / "output")
    p.add_argument("-q", "--quality", type=int, default=80)
    p.add_argument("--lossless", action="store_true")
    a = p.parse_args(argv)

    if not a.input.is_dir():
        print(f"no input dir: {a.input}", file=sys.stderr)
        return 1

    files = [f for f in sorted(a.input.rglob("*"))
             if f.is_file() and f.suffix.lower() in EXTS and not f.name.startswith(".")]
    if not files:
        print(f"nothing to convert in {a.input}")
        return 0

    failed = 0
    for src in files:
        dst = a.output / src.relative_to(a.input).with_suffix(".webp")
        try:
            convert(src, dst, a.quality, a.lossless)
        except Exception as e:
            print(f"FAIL {src.name}: {e}", file=sys.stderr)
            failed += 1
            continue
        before, after = src.stat().st_size, dst.stat().st_size
        print(f"{src.relative_to(a.input)} -> {dst.relative_to(a.output)}  "
              f"{before/1024:.1f}K -> {after/1024:.1f}K ({100 - after*100//before:.0f}% smaller)")
    print(f"\n{len(files) - failed}/{len(files)} converted into {a.output}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
