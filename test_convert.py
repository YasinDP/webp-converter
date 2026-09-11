#!/usr/bin/env python3
"""Self-check: python3 test_convert.py"""
import tempfile
from pathlib import Path

from PIL import Image

import convert
from convert import main

with tempfile.TemporaryDirectory() as d:
    src, out = Path(d) / "in" / "sub", Path(d) / "out"
    src.mkdir(parents=True)
    Image.new("RGB", (32, 32), "red").save(src / "a.jpg")
    Image.new("RGBA", (32, 32), (0, 255, 0, 128)).save(src / "b.png")
    Image.new("RGB", (16, 16), "red").save(
        src / "c.gif", save_all=True, duration=120, loop=0,
        append_images=[Image.new("RGB", (16, 16), "blue")])
    (src / "d.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<circle cx="5" cy="5" r="5" fill="green"/></svg>')
    (src / "skip.txt").write_text("x")
    (src / ".DS_Store").write_text("x")

    assert main([str(src.parent), "-o", str(out), "-s", "2"]) == 0
    made = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.webp"))
    assert made == ["sub/a.webp", "sub/b.webp", "sub/c.webp", "sub/d.webp"], made
    assert not list(out.rglob("*.txt"))

    with Image.open(out / "sub" / "b.webp") as im:
        assert im.mode == "RGBA" and im.size == (32, 32)
    with Image.open(out / "sub" / "c.webp") as im:  # animation + timing survive
        im.load()
        assert im.n_frames == 2 and im.info["duration"] == 120, im.info
    if convert.cairosvg:
        with Image.open(out / "sub" / "d.webp") as im:
            assert im.size == (20, 20), im.size  # --scale 2 applied
    else:
        print("note: cairosvg unavailable, SVG check skipped")

    # second run is a no-op, sources untouched
    stamp = (out / "sub" / "a.webp").stat().st_mtime
    assert main([str(src.parent), "-o", str(out)]) == 0
    assert (out / "sub" / "a.webp").stat().st_mtime == stamp
    assert (src / "a.jpg").exists()

    # --delete removes only converted sources
    assert main([str(src.parent), "-o", str(out), "--delete", "--force"]) == 0
    assert not (src / "a.jpg").exists() and (src / "skip.txt").exists()

print("ok")
