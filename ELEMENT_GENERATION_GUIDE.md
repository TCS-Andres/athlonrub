# Brand Element Generation Guide

A reusable playbook for generating hand-drawn brand graphic elements with
**true alpha transparency** using Nano Banana Pro (kie.ai). Solves the
fake-checker-pattern bug that happens when you ask the model directly
for "transparent background."

This file is project-agnostic. Drop it into any client folder.

---

## TL;DR — two non-negotiable rules

1. **Never ask the model for a "transparent background."** It paints the
   visual checker pattern that image editors *use to represent* transparency
   — into the actual pixels. The resulting PNG is opaque with a fake-looking
   gray-block texture behind the artwork.
2. **Always do two stages: generate on solid black, then extract alpha in
   Python.** This produces clean anti-aliased edges with no black halos.

---

## How to brief me

When you ask me to generate elements, tell me:

- **What the element is** (a hand-drawn arrow, a checkmark, a head
  silhouette, a divider line, etc.)
- **The brand reference** (book cover, logo, photo, design system —
  whatever defines the style)
- **Color** (single-color ink? specific hex? white-on-dark vs.
  yellow-on-dark?)
- **Use case** (hero accent, list bullet, section divider, numbered
  badge, etc.)
- **Aspect ratio** if it matters

I'll handle:
- Writing the prompt with the right safeguards
- Running it through the kie.ai API (parallel batch if you want many)
- Post-processing to true alpha
- Verifying the result by compositing onto the brand-color background

---

## The prompt formula

Every element prompt = **element-specific description** + **shared
brand-style block**. The shared block is the load-bearing part — every
phrase is doing work, don't paraphrase it.

### Element-specific description (varies per element)

Be concrete about:
- Shape and composition
- Stroke type — *loose marker, fine pen, thick brush, etc.*
- Color in plain English **and** hex — e.g. `GOLDEN YELLOW INK (approximately #FFC72C)`
- Position/orientation within the canvas

### Shared brand-style block (use this wording)

```
[ELEMENT-SPECIFIC DESCRIPTION HERE]. Hand-drawn brand graphic in the loose
marker-doodle style of [BRAND REFERENCE]. Single-color line art drawn with
energetic strokes that have a subtle hand-drawn wobble (not perfectly
straight, not vector-clean). Consistent stroke weight.

BACKGROUND: a UNIFORM SOLID PURE BLACK (#000000) studio backdrop filling
the entire canvas behind the artwork — flat, opaque, photographic black.
DO NOT draw a checkered transparency-indicator pattern. DO NOT draw light
gray and dark gray alternating squares. DO NOT draw any pattern, gradient,
or texture in the background. The background must be a single uniform
solid black color, like a product shot taken against a black studio sweep.
The line art is the only thing on the canvas besides flat black.

Isolated, centered, with generous empty black margin around the artwork.
No text, no captions, no labels, no border.
```

### Words to avoid

These trigger the wrong behavior every time:

- ❌ `transparent background` → model paints the checker pattern
- ❌ `alpha channel` → same
- ❌ `PNG with transparency` → same
- ❌ `no background` → often ignored or interpreted oddly
- ❌ `isolated on white` → produces a white bg you can't cleanly remove

### Words that work

- ✅ `uniform solid pure BLACK (#000000) studio backdrop`
- ✅ `flat, opaque, photographic black`
- ✅ `like a product shot taken against a black studio sweep`
- ✅ The explicit `DO NOT draw a checkered transparency-indicator pattern`
  enumeration — naming the failure mode is what prevents it

---

## The post-processing pipeline

After the raw black-background PNG is downloaded, this Python step
converts black → true alpha using premultiplied-alpha math. Drop this
function into any generation script.

```python
import numpy as np
from PIL import Image

LOW, HIGH = 35, 70             # brightness thresholds for the alpha ramp
ALPHA_CROP_THRESHOLD = 25      # pixels with alpha below this don't count for bbox
PAD_RATIO = 0.04               # 4% breathing room after auto-crop

def black_to_alpha(in_path, out_path):
    img = Image.open(in_path).convert("RGB")
    arr = np.array(img).astype(np.float32)

    # alpha = brightest channel per pixel (artwork is bright on black bg)
    brightness = np.max(arr, axis=2)

    # Three-zone alpha curve:
    #   brightness <= LOW   → fully transparent (kills JPEG noise)
    #   brightness >= HIGH  → alpha = brightness (preserve antialiased edges)
    #   between LOW & HIGH  → smooth linear ramp from 0 → brightness
    alpha = np.where(
        brightness <= LOW, 0.0,
        np.where(
            brightness >= HIGH,
            brightness,
            brightness * (brightness - LOW) / (HIGH - LOW),
        ),
    )
    alpha = np.clip(alpha, 0, 255)

    # Un-premultiply RGB so the artwork color is recovered cleanly
    # (no black halo at antialiased edges). Inverse of compositing on black.
    safe = np.where(alpha > 0, alpha, 1.0)
    straight = np.minimum(arr * 255.0 / safe[..., None], 255.0)

    rgba = np.dstack([straight, alpha]).astype(np.uint8)

    # Auto-crop to the alpha bounding box so transparent margins don't
    # eat CSS sizing on the page.
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

    Image.fromarray(rgba).save(out_path, "PNG", optimize=True)
```

### Why each piece works

1. **`alpha = max(R, G, B)`** — when an image is composited on solid black,
   every visible pixel value equals `(original_color × alpha)`. The brightest
   channel of a pixel reveals how opaque it was. So we can recover alpha
   from luminance, regardless of artwork color (white, yellow, magenta —
   all work).

2. **Un-premultiplying** — dividing each RGB channel by the recovered alpha
   restores the original artwork color. Skip this step and anti-aliased
   edges retain their "mixed with black" tone, producing visible dark
   halos around every stroke.

3. **Three-zone alpha curve** — a simple `alpha = brightness` keeps too
   much JPEG/PNG compression noise (background pixels in the 8–25 range
   become faint visible specks when composited on a light background).
   A hard threshold loses the soft edges of pen strokes. The linear ramp
   between LOW and HIGH gives you noise-free background *and* clean
   anti-aliasing.

4. **Auto-crop** — the model leaves generous empty margins around the
   artwork. Without cropping, the PNG's bounding box is mostly empty
   space, and CSS `max-width` controls that empty box instead of the
   visible artwork. Cropping tight ensures `max-width` ≈ "how big the
   actual graphic appears."

---

## API workflow (kie.ai Nano Banana Pro)

### Submit task

```
POST https://api.kie.ai/api/v1/jobs/createTask
Authorization: Bearer <YOUR_KEY>
Content-Type: application/json

{
  "model": "nano-banana-pro",
  "input": {
    "prompt": "<full prompt>",
    "image_input": [],
    "aspect_ratio": "1:1",     // or 16:9, 4:5, 3:4, 21:9, etc.
    "resolution": "2K",
    "output_format": "png"
  }
}
```

Returns `{ "data": { "taskId": "..." } }`.

### Poll for completion

```
GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId=<id>
```

State is `waiting` → `success` | `fail`. On success, parse
`resultJson.resultUrls[0]` for the download URL.

### Download with a real User-Agent

The CDN serving result images blocks the default `urllib`/`requests` UA
with a **403 Forbidden**. Always send a browser UA:

```python
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 Chrome/124.0",
    "Accept": "image/png,image/*,*/*",
})
```

### Parallelize when generating in batches

Submit all elements simultaneously with `ThreadPoolExecutor(max_workers=10)`.
Polling can also run in parallel. A 10-element batch usually completes
in **2–4 minutes total**, not 20–40.

---

## Always verify on the actual brand background

After saving the cleaned PNG, **don't trust how it looks on the default
white viewer background.** Composite onto the actual brand color you'll
use on the page — that's where halos, residual noise, and stray pixels
become visible.

```python
from PIL import Image

BRAND_BG = (181, 32, 142)  # e.g. magenta — use your actual hex

fg = Image.open("element.png").convert("RGBA")
bg = Image.new("RGB", fg.size, BRAND_BG)
bg.paste(fg, (0, 0), fg)
bg.save("_qa.png")
```

A clean result shows:
- Crisp anti-aliased edges, no dark halo
- No background noise or pixel artifacts in the supposedly-empty areas
- The artwork's original color preserved (not muted, not shifted toward
  the brand background)

If you see halos → the un-premultiplying step is broken or skipped. If you
see speckle noise → raise the `LOW` threshold. If edges look chunky →
lower the `HIGH` threshold for a softer ramp.

---

## Content-filter pitfalls

A few prompts will trip Nano Banana's content filter (task returns
`state: fail` with `failCode: 422` and `failMsg: "The input or output
was flagged as sensitive."`). What I've seen so far:

- The phrase **"empty/transparent interior"** inside a frame description
  tripped the filter on a circle-badge prompt. Reworded to **"The center
  of the frame is empty"** and it passed.
- Clinical/anatomical language ("brain", "head") in close proximity can
  flag — wrap in clear artistic framing: *"a hand-drawn silhouette of a
  human head in profile, outlined in white ink with a single continuous
  line."*

If a task fails: soften the language, keep the visual direction, re-submit.
Usually one revision gets through.

---

## Quick pre-flight checklist

- [ ] Element description is concrete (shape, color, orientation,
      stroke style)
- [ ] The brand-style block (verbatim) is appended
- [ ] None of the forbidden words appear: `transparent background`,
      `alpha channel`, `PNG with transparency`, `no background`, `isolated
      on white`
- [ ] Aspect ratio chosen to fit the artwork's natural shape (avoid
      wasted margin)
- [ ] Resolution: **2K** is plenty for landing-page use; **4K** only
      for hero/print
- [ ] Post-processing pipeline runs and saves the cleaned PNG
- [ ] QA composite on the actual brand background looks clean

Then ship it.

---

## Reference implementations in this repo

If you want to see a full working version of the pipeline:

- `fix_transparent_elements.py` — generates 10 elements in parallel,
  full alpha extraction, dual-folder save.
- `reprocess_alpha.py` — alpha-extraction only (re-runs on existing raw
  black-background PNGs without re-generating).
- `_verify_on_magenta.py` — the QA composite step.

Copy any of those scripts and adapt to a new project — the prompts are
the only thing that needs to change.
