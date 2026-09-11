#!/usr/bin/env python3
"""Convert images and SVGs to WebP. Fully offline.

  python3 convert.py                  input/ -> output/, quality 80
  python3 convert.py logo.svg -s 2    single file, SVG at 2x
  python3 convert.py img/ -o webp/    any folder (subfolders mirrored)
  python3 convert.py --delete         remove sources that converted OK
"""
import argparse
import ctypes.util
import glob
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

# cairocffi looks up "cairo" by bare name, which misses Homebrew/MacPorts prefixes.
_find = ctypes.util.find_library
ctypes.util.find_library = lambda n: _find(n) or next(
    iter(sum([glob.glob(f"{p}/lib{n}*.dylib") for p in
              ("/opt/homebrew/lib", "/usr/local/lib", "/opt/local/lib")], [])), None)
try:
    import cairosvg
except (ImportError, OSError):
    cairosvg = None

RASTER = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".ico"}
EXTS = RASTER | {".svg"}
ROOT = Path(__file__).parent


def convert(src: Path, dst: Path, quality: int, lossless: bool, scale: float) -> None:
    if src.suffix.lower() == ".svg":
        if cairosvg is None:
            raise RuntimeError("SVG needs cairosvg + cairo: pip3 install CairoSVG && brew install cairo")
        img = Image.open(BytesIO(cairosvg.svg2png(url=str(src), scale=scale)))
    else:
        img = Image.open(src)
    with img as im:
        animated = getattr(im, "n_frames", 1) > 1
        if not animated and im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "transparency" in im.info or "A" in im.getbands() else "RGB")
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "WEBP", quality=quality, lossless=lossless,
                method=6, save_all=animated, minimize_size=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", type=Path, nargs="?", default=ROOT / "input", help="file or folder (default: ./input)")
    p.add_argument("-o", "--output", type=Path, default=None, help="output folder (default: ./output)")
    p.add_argument("-q", "--quality", type=int, default=80, help="1-100 (default: 80)")
    p.add_argument("-s", "--scale", type=float, default=1.0, help="SVG render scale (default: 1.0)")
    p.add_argument("--lossless", action="store_true")
    p.add_argument("--delete", action="store_true", help="delete each source that converted successfully")
    p.add_argument("--force", action="store_true", help="reconvert even if the .webp is already up to date")
    a = p.parse_args(argv)

    if not 1 <= a.quality <= 100:
        p.error("quality must be 1-100")
    if not a.input.exists():
        print(f"no such input: {a.input}", file=sys.stderr)
        return 1
    base = a.input if a.input.is_dir() else a.input.parent
    out = a.output or (ROOT / "output" if a.input == ROOT / "input" else base)

    files = [a.input] if a.input.is_file() else [
        f for f in sorted(a.input.rglob("*"))
        if f.is_file() and f.suffix.lower() in EXTS and not f.name.startswith(".")]
    if not files:
        print(f"nothing to convert in {a.input}")
        return 0

    done = failed = 0
    for src in files:
        dst = out / src.relative_to(base).with_suffix(".webp")
        if not a.force and dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
            print(f"skip (up to date)  {src.relative_to(base)}")
            done += 1
            continue
        try:
            convert(src, dst, a.quality, a.lossless, a.scale)
        except Exception as e:
            print(f"FAIL {src.name}: {e}", file=sys.stderr)
            failed += 1
            continue
        before, after = src.stat().st_size, dst.stat().st_size
        note = ""
        if a.delete:
            src.unlink()
            note = "  (source removed)"
        pct = (before - after) * 100 // before
        size = f"{before/1024:.1f}K -> {after/1024:.1f}K ({abs(pct)}% {'smaller' if pct >= 0 else 'larger'})"
        print(f"{src.relative_to(base)} -> {dst.relative_to(out)}  {size}{note}")
        done += 1
    print(f"\n{done}/{len(files)} converted into {out}" + (f", {failed} failed" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
