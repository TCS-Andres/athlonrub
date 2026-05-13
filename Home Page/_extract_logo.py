"""
Crop the primary Athlon Rub logo from page 1 of the brand PDF, then convert
its solid-black background to true alpha using the same pipeline as the
brand elements. Outputs two variants:

  Brand Elements/00_logo_full.png       — full lockup (shield + ATHLON RUB)
  Brand Elements/00_logo_shield.png     — shield-only crest (no wordmark)

Both are tight-cropped to the alpha bounding box so CSS sizing controls
visible artwork, not transparent margin.
"""
import os
import fitz
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF  = os.path.join(ROOT, "New Logo Athlon Rub Cinturon.pdf")
OUT  = os.path.join(ROOT, "Brand Elements")

# Same three-zone alpha curve as the element generation pipeline.
# This one uses a LOWER `LOW` because the gold strokes are highly saturated
# but darker than pure white, so we want to keep more of the tonal range.
LOW, HIGH = 18, 55
ALPHA_CROP_THRESHOLD = 30
PAD_RATIO = 0.03


def alpha_extract_and_crop(rgb_img: Image.Image) -> Image.Image:
    arr = np.array(rgb_img.convert("RGB")).astype(np.float32)
    brightness = np.max(arr, axis=2)

    alpha = np.where(
        brightness <= LOW, 0.0,
        np.where(
            brightness >= HIGH,
            brightness,
            brightness * (brightness - LOW) / (HIGH - LOW),
        ),
    )
    alpha = np.clip(alpha, 0, 255)

    safe = np.where(alpha > 0, alpha, 1.0)
    straight = np.minimum(arr * 255.0 / safe[..., None], 255.0)

    rgba = np.dstack([straight, alpha]).astype(np.uint8)

    mask = alpha > ALPHA_CROP_THRESHOLD
    if mask.any():
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        y0, y1 = np.where(rows)[0][[0, -1]]
        x0, x1 = np.where(cols)[0][[0, -1]]
        h, w = rgba.shape[:2]
        pad = int(min(h, w) * PAD_RATIO)
        y0, y1 = max(0, y0 - pad), min(h, y1 + 1 + pad)
        x0, x1 = max(0, x0 - pad), min(w, x1 + 1 + pad)
        rgba = rgba[y0:y1, x0:x1]

    return Image.fromarray(rgba, "RGBA")


def main():
    doc = fitz.open(PDF)
    page = doc[0]
    mat = fitz.Matrix(4.0, 4.0)  # 4x DPI render
    pix = page.get_pixmap(matrix=mat, alpha=False)
    full = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    W, H = full.size
    print(f"page render: {W} x {H}")

    # Hero section of the layout = top ~23.5% of the page
    top = full.crop((0, 0, W, int(H * 0.235)))

    # Full lockup (shield + wordmark)
    full_logo = alpha_extract_and_crop(top)
    full_out  = os.path.join(OUT, "00_logo_full.png")
    full_logo.save(full_out, "PNG", optimize=True)
    print(f"saved {full_out}  ({full_logo.size[0]}x{full_logo.size[1]})")

    # Shield-only crest: roughly the upper 65% of the cropped hero
    # The wordmark sits below the crest with a visible gap, so cutting at 0.62
    # cleanly separates them.
    tw, th = top.size
    shield_crop = top.crop((0, 0, tw, int(th * 0.62)))
    shield = alpha_extract_and_crop(shield_crop)
    shield_out = os.path.join(OUT, "00_logo_shield.png")
    shield.save(shield_out, "PNG", optimize=True)
    print(f"saved {shield_out}  ({shield.size[0]}x{shield.size[1]})")


if __name__ == "__main__":
    main()
