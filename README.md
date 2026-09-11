# WebP Converter

Offline image → WebP converter. Nothing leaves your machine; no network calls, no online service.

**In:** PNG, JPG, GIF (animation preserved), BMP, TIFF, ICO, WebP, SVG → **out:** WebP.

## Setup

```bash
pip3 install -r requirements.txt   # Pillow; CairoSVG only if you need SVG
brew install cairo                 # macOS, SVG only
```

## Use

```bash
python3 convert.py                 # input/ -> output/, quality 80
python3 convert.py -q 95           # higher quality
python3 convert.py --lossless      # lossless (good for flat graphics/icons)
python3 convert.py logo.svg -s 2   # single file, SVG rendered at 2x
python3 convert.py img/ -o webp/   # any folders; subfolders are mirrored
python3 convert.py --delete        # delete sources that converted OK
python3 convert.py --force         # reconvert even if the .webp is up to date
```

Subfolders under the input are mirrored into the output. Dotfiles and unsupported
files are ignored. Re-running skips anything whose `.webp` is already newer than
its source, so it is cheap to run repeatedly.

| Option | Description |
|---|---|
| `input` | File or folder (default: `./input`) |
| `-o, --output` | Output folder (default: `./output`, or alongside the input when you pass a path) |
| `-q, --quality` | 1-100 (default: 80) |
| `-s, --scale` | SVG render scale (default: 1.0) |
| `--lossless` | Lossless WebP |
| `--delete` | Delete each source file that converted successfully |
| `--force` | Ignore the up-to-date check |

**`--delete` is opt-in.** Earlier versions deleted sources by default; that is now
behind the flag so a bad run cannot eat your originals.

## Check

```bash
python3 test_convert.py    # asserts structure, alpha, GIF animation, skip, --delete
```

## Notes

- Quality: 75-85 for photos, 85-95 (or `--lossless`) for icons and flat graphics.
- Transparency is preserved; animated GIFs keep their frames and timing.
- SVG is optional — without CairoSVG everything else still converts.
