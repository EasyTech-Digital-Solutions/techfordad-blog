#!/usr/bin/env python3
"""Make small WebP thumbnails for the review/guide cards from the full-size hero photos.

    python3 scripts/make_card_images.py

The cards show a 400x180 slot (about 364 px wide on desktop), but used to load the full ~900 px hero
photo (30-260 KB each), which made the reviews index 1.9 MB. For every images/heroes/hero-*.jpg this
writes images/cards/hero-*.webp: centre-cropped to the card's 20:9 shape, 640x288 (retina-sharp),
WebP quality 74. Re-run after adding a hero image. Needs Pillow.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images" / "heroes"
OUT = ROOT / "images" / "cards"
W, H = 640, 288
QUALITY = 74


def thumb(src):
    im = Image.open(src).convert("RGB")
    target = W / H
    w, h = im.size
    if w / h > target:  # too wide: crop the sides
        nw = round(h * target)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:  # too tall: crop top and bottom
        nh = round(w / target)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((W, H), Image.LANCZOS)


def main():
    OUT.mkdir(exist_ok=True)
    before = after = 0
    for src in sorted(SRC.glob("hero-*.jpg")):
        dest = OUT / (src.stem + ".webp")
        thumb(src).save(dest, "WEBP", quality=QUALITY, method=6)
        before += src.stat().st_size
        after += dest.stat().st_size
    print(f"{len(list(OUT.glob('*.webp')))} thumbnails: {before // 1024} KB of heroes -> {after // 1024} KB of cards")


if __name__ == "__main__":
    main()
