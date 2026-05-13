"""
Background-remove the 4 raw product photos using rembg, then tight-crop
to the bottle bounding box and save as transparent PNGs to Brand Elements/.

Outputs:
  Brand Elements/bottle_travel.png       3.4 fl oz / 100 mL — "Clear" travel size
  Brand Elements/bottle_pro.png          8.5 fl oz / 250 mL — clean studio shot for product grid
  Brand Elements/bottle_pro_hero.png     8.5 fl oz / 250 mL — angled shot with clear pump cover, for hero
  Brand Elements/bottle_large.png        17 fl oz / 500 mL — "coach" cap (no spray)
"""
import os
import numpy as np
from PIL import Image
from rembg import remove, new_session
from scipy.ndimage import binary_fill_holes, binary_erosion, binary_dilation, label as cc_label

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "Product Photos", "_raw")
OUT  = os.path.join(ROOT, "Brand Elements")

JOBS = [
    ("1600x1600.jpg",                          "bottle_travel.png"),
    ("Mock Template-bottle pro_spray_gap.jpg", "bottle_pro.png"),
    ("Pro Bottle 8.5 fl Oz 250 ML.jpeg",       "bottle_pro_hero.png"),
    ("Mock Template-bottle coach.jpg",         "bottle_large.png"),
]

# The "isnet-general-use" model gives the cleanest cutouts for product photos
# with subtle shadows and transparent caps.
SESSION = new_session("isnet-general-use")

ALPHA_CROP_THRESHOLD = 15  # pixels with alpha below this don't count for bbox
PAD_RATIO = 0.02           # 2% breathing room around the bottle


def cut_and_crop(in_path: str, out_path: str) -> None:
    src_rgb = np.array(Image.open(in_path).convert("RGB"))
    cut = remove(Image.fromarray(src_rgb), session=SESSION)
    if cut.mode != "RGBA":
        cut = cut.convert("RGBA")
    arr = np.array(cut)

    # rembg's salient-object model often punches a label-shaped hole through
    # product bottles that have white-paper labels. binary_fill_holes can't
    # rescue these because rembg also leaves tiny gaps at the bottle base
    # that "leak" the hole out to the canvas edge.
    #
    # The robust fix bypasses rembg entirely for the label: identify the
    # studio background by edge flood-fill on the source RGB, and treat
    # everything NOT reachable from the canvas edge as part of the bottle.
    #
    # Studio background is detected as: brightness >= 235 (very near-white)
    # The bottle's silhouette is darker than that, so the flood stops at
    # the bottle edge. The white label, surrounded by darker label graphics
    # and bottle edges, is NOT reachable from outside and stays opaque.
    bright_mask = src_rgb.min(axis=2) >= 235

    # Seed = all pixels on the 4 canvas edges that are bright
    h, w = bright_mask.shape
    seed = np.zeros_like(bright_mask)
    seed[0,    :] = bright_mask[0,    :]
    seed[-1,   :] = bright_mask[-1,   :]
    seed[:,    0] = bright_mask[:,    0]
    seed[:,   -1] = bright_mask[:,   -1]

    # Flood fill: keep dilating seed restricted to bright_mask until convergence.
    # binary_dilation(seed) & bright_mask — equivalent to morphological
    # reconstruction by dilation. Iterate until no change.
    reachable = seed.copy()
    while True:
        new = binary_dilation(reachable) & bright_mask
        if np.array_equal(new, reachable):
            break
        reachable = new

    # `reachable` is now the studio background. Everything else is the bottle.
    bottle_mask = ~reachable

    # Build the final alpha: full opacity inside the bottle silhouette,
    # use rembg's softer alpha at the silhouette EDGE for nice antialiasing.
    interior = binary_erosion(bottle_mask, iterations=2)  # strictly interior
    final_alpha = arr[..., 3].copy()
    final_alpha[interior] = 255
    # On the silhouette edge, take the max of (rembg alpha) and (255 if
    # bottle_mask says it's bottle) — but lean toward antialiased values
    # to avoid jaggy edges.
    edge_band = bottle_mask & ~interior
    final_alpha[edge_band] = np.maximum(final_alpha[edge_band], 200)
    # Anything not in bottle_mask but rembg gave low alpha → keep transparent
    final_alpha[~bottle_mask] = np.minimum(final_alpha[~bottle_mask], 30)
    # Force fully transparent outside the studio sweep
    final_alpha[reachable] = 0

    arr[..., 3] = final_alpha
    # Restore RGB inside the bottle from the source so we don't carry
    # rembg's potentially-altered colors
    arr[bottle_mask, :3] = src_rgb[bottle_mask]

    alpha = arr[..., 3]
    mask  = alpha > ALPHA_CROP_THRESHOLD
    if mask.any():
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        y0, y1 = np.where(rows)[0][[0, -1]]
        x0, x1 = np.where(cols)[0][[0, -1]]
        h, w = arr.shape[:2]
        pad = int(min(h, w) * PAD_RATIO)
        y0, y1 = max(0, y0 - pad), min(h, y1 + 1 + pad)
        x0, x1 = max(0, x0 - pad), min(w, x1 + 1 + pad)
        arr = arr[y0:y1, x0:x1]

    out = Image.fromarray(arr, "RGBA")
    out.save(out_path, "PNG", optimize=True)
    bottle_pct = 100 * bottle_mask.sum() / bottle_mask.size
    print(f"  {os.path.basename(in_path):<45s} -> {os.path.basename(out_path)}  ({out.size[0]}x{out.size[1]})  bottle: {bottle_pct:.1f}%")


def main():
    print(f"processing {len(JOBS)} product photos with rembg (isnet-general-use)...")
    for src_name, out_name in JOBS:
        cut_and_crop(os.path.join(RAW, src_name), os.path.join(OUT, out_name))
    print("done.")


if __name__ == "__main__":
    main()
