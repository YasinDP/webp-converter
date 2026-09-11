#!/usr/bin/env python3
"""Self-check: python3 test_convert.py"""
import tempfile
from pathlib import Path

from PIL import Image

from convert import main

with tempfile.TemporaryDirectory() as d:
    src, out = Path(d) / "in" / "sub", Path(d) / "out"
    src.mkdir(parents=True)
    Image.new("RGB", (32, 32), "red").save(src / "a.jpg")
    Image.new("RGBA", (32, 32), (0, 255, 0, 128)).save(src / "b.png")
    Image.new("RGB", (16, 16), "red").save(
        src / "c.gif", save_all=True, duration=120, loop=0,
        append_images=[Image.new("RGB", (16, 16), "blue")])
    (src / "skip.txt").write_text("x")
    (src / ".DS_Store").write_text("x")

    assert main(["-i", str(src.parent), "-o", str(out)]) == 0
    made = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.webp"))
    assert made == ["sub/a.webp", "sub/b.webp", "sub/c.webp"], made
    assert not list(out.rglob("*.txt"))
    with Image.open(out / "sub" / "b.webp") as im:
        assert im.mode == "RGBA" and im.size == (32, 32)
    with Image.open(out / "sub" / "c.webp") as im:
        im.load()
        assert im.n_frames == 2, im.n_frames  # animation survives
        assert im.info["duration"] == 120, im.info  # and its timing

print("ok")
