"""
Generate 10 unique brand elements for Athlon Rub.

Brand identity (from "New Logo Athlon Rub Cinturon.pdf"):
  - All-Sports Rub. Premium athletic topical analgesic.
  - Shield + 5-point star + "A"-shaped athlete monogram.
  - Palette: forest green #0F2F2F, gold #D9AF37, cream #EAE9CB.
  - Brand attributes: Proteccion, Excelencia, Rendimiento, Superacion.
  - Style: bold athletic emblem / varsity / military insignia
    (NOT hand-drawn marker — that's a different brand's playbook).

Technique follows ELEMENT_GENERATION_GUIDE.md verbatim:
  1) Generate each element composited on solid pure black (no checker bug).
  2) Recover true alpha by reading max(R,G,B) and un-premultiplying.
  3) Auto-crop to bbox so CSS sizing controls visible artwork, not margin.
"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from PIL import Image

API_KEY = os.environ.get("KIE_API_KEY")
if not API_KEY:
    sys.exit("Set KIE_API_KEY in your environment. Get one at https://kie.ai/api-key")

CREATE_URL = "https://api.kie.ai/api/v1/jobs/createTask"
QUERY_URL  = "https://api.kie.ai/api/v1/jobs/recordInfo"

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR     = os.path.join(WORKING_DIR, "_raw_black_bg")
QA_DIR      = os.path.join(WORKING_DIR, "_qa_on_brand_green")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(QA_DIR, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Brand-style block adapted for Athlon Rub's premium athletic-emblem identity.
# Same solid-black-background safeguards as the guide — that's the technique
# rule and it's universal. The style language is bespoke to this brand.
BRAND_STYLE = (
    "Premium athletic emblem style in the visual language of the Athlon Rub "
    "shield logo: bold, confident, sharp vector linework with crisp edges, "
    "subtle highlights and bevels that read like a polished gold-foil sports "
    "insignia stamped onto a varsity letterman jacket. Strong geometric "
    "shapes, dynamic balance, premium sports-brand finish — not flat icon, "
    "not cartoon, not hand-drawn doodle. Single-element composition. "
    "BACKGROUND: a UNIFORM SOLID PURE BLACK (#000000) studio backdrop "
    "filling the entire canvas behind the artwork — flat, opaque, "
    "photographic black. DO NOT draw a checkered transparency-indicator "
    "pattern. DO NOT draw light gray and dark gray alternating squares. "
    "DO NOT draw any pattern, gradient, or texture in the background. The "
    "background must be a single uniform solid black color, like a product "
    "shot taken against a black studio sweep. The artwork is the only thing "
    "on the canvas besides flat black. Isolated, centered, with generous "
    "empty black margin around the artwork. No text, no captions, no "
    "labels, no border around the element."
)

GOLD = "metallic GOLD with a warm antique tone (approximately #D9AF37), with "\
       "subtle lighter highlights along the upper edges and slightly darker "\
       "shading on the lower edges to give a polished low-relief 3D finish"

CREAM = "soft warm CREAM (approximately #EAE9CB), clean and elegant, no shading"


ELEMENTS = [
    {
        "name": "01_triple_chevron_forward",
        "aspect_ratio": "16:9",
        "prompt": (
            f"A horizontal arrangement of THREE chevron arrowheads in {GOLD}, "
            "pointing to the right, stacked side-by-side with even spacing — "
            "the iconic '>>>' forward-motion mark from the Athlon Rub bottle "
            "label. Each chevron is a clean V-shape with crisp angles and a "
            "uniform stroke thickness, suggesting speed, momentum, and "
            f"forward progress through recovery. {BRAND_STYLE}"
        ),
    },
    {
        "name": "02_athletic_five_point_star",
        "aspect_ratio": "1:1",
        "prompt": (
            f"A single bold 5-pointed athletic star in {GOLD}, centered, "
            "drawn as a solid filled shape with clean symmetrical points. "
            "This is the excellence-mark star from inside the Athlon Rub "
            "shield, isolated as a standalone emblem. Sharp tips, slight "
            "highlight on the upper facets to suggest dimensional gold-foil "
            f"relief. {BRAND_STYLE}"
        ),
    },
    {
        "name": "03_shield_outline_frame",
        "aspect_ratio": "4:5",
        "prompt": (
            f"An empty heraldic SHIELD silhouette outlined in {GOLD}, in the "
            "exact shape of the Athlon Rub shield: rounded shoulders at the "
            "top, gently curved sides tapering down to a pointed base. Bold "
            "uniform stroke width forming a clean closed outline. The inside "
            "of the shield is empty (no fill, no star, no monogram) so it "
            "can frame other content. The shield is upright, centered. "
            f"{BRAND_STYLE}"
        ),
    },
    {
        "name": "04_A_athlete_monogram",
        "aspect_ratio": "1:1",
        "prompt": (
            f"The signature ATHLON 'A' monogram in {GOLD} — a stylized "
            "capital letter A whose two diagonal legs evoke a striding "
            "athlete in mid-motion: the left leg planted, the right leg "
            "kicked forward and slightly raised, with a sharp angular "
            "crossbar. The shape simultaneously reads as the letter A and "
            "as a dynamic athlete figure. Strong, masculine, "
            f"performance-driven, exactly as on the brand shield. {BRAND_STYLE}"
        ),
    },
    {
        "name": "05_runner_silhouette_icon",
        "aspect_ratio": "1:1",
        "prompt": (
            f"A solid filled silhouette of a runner mid-stride in {GOLD}: "
            "leaning slightly forward, one leg extended back, the other "
            "lifted ahead in full sprint, arms swinging in opposition. "
            "Clean modern athletic icon — the same little runner figure "
            "that appears in the benefit-badge row of the Athlon Rub bottle "
            "label, but rendered larger and more refined. Side-profile view, "
            f"facing right. {BRAND_STYLE}"
        ),
    },
    {
        "name": "06_laurel_wreath_open",
        "aspect_ratio": "1:1",
        "prompt": (
            f"A classic athletic LAUREL WREATH in {GOLD}, formed by two "
            "curved branches of stylized laurel leaves arching upward and "
            "inward from the bottom — left branch and right branch — almost "
            "meeting at the top but leaving a clear open space in the "
            "middle for content to be placed inside. Symmetrical, elegant, "
            "premium sports-award finish with subtle leaf veining. The "
            f"bottom of the wreath is gently bound with a small band. {BRAND_STYLE}"
        ),
    },
    {
        "name": "07_crossed_lightning_bolts",
        "aspect_ratio": "1:1",
        "prompt": (
            f"Two angular LIGHTNING BOLTS in {GOLD}, crossed in an X "
            "configuration at their middles — like crossed swords on a "
            "military crest, but bolts instead of blades. Each bolt has the "
            "classic jagged 'Z' silhouette with sharp angular tips. "
            "Symbolizes explosive power and fast recovery. Bold and "
            f"confident, with subtle highlights along the leading edges. {BRAND_STYLE}"
        ),
    },
    {
        "name": "08_star_divider_bar",
        "aspect_ratio": "21:9",
        "prompt": (
            f"A horizontal section divider in {GOLD}: a long thin horizontal "
            "line stretching from left to right across the canvas, "
            "interrupted exactly in the center by a small 5-pointed athletic "
            "star (the same star used in the Athlon Rub shield). The line "
            "tapers slightly toward both ends. Military-insignia-style "
            f"divider — clean, premium, symmetrical. {BRAND_STYLE}"
        ),
    },
    {
        "name": "09_dynamic_speed_streaks",
        "aspect_ratio": "16:9",
        "prompt": (
            f"A cluster of three to five horizontal SPEED STREAKS in {CREAM}, "
            "stacked closely with slight vertical staggering — long thin "
            "tapered strokes that begin sharp on the right and dissolve "
            "softly toward the left, suggesting an object racing forward at "
            "high speed (motion-blur lines). Clean, modern, geometric — like "
            "the dynamic action streaks used behind premium sports-brand "
            f"hero graphics. {BRAND_STYLE}"
        ),
    },
    {
        "name": "10_ribbon_banner",
        "aspect_ratio": "16:9",
        "prompt": (
            f"A premium RIBBON BANNER in {GOLD}, horizontal, gently arched "
            "across the middle of the canvas — the kind of unfurled "
            "scroll-ribbon used on athletic crests and championship medals. "
            "The main central panel is a flat blank face (empty so a "
            "designer can drop a word like 'EXCELENCIA' or 'RENDIMIENTO' "
            "onto it later). The left and right ends of the ribbon fold back "
            "behind themselves and terminate in classic notched swallow-tail "
            "cuts. Subtle highlight along the upper edge and darker "
            f"underside to give the ribbon a low-relief 3D look. {BRAND_STYLE}"
        ),
    },
]


# ----------------------------------------------------------------------
# API helpers
# ----------------------------------------------------------------------
def http_post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def http_get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/png,image/*,*/*"})
    with urllib.request.urlopen(req, timeout=180) as r:
        with open(path, "wb") as f:
            f.write(r.read())


def submit(el):
    body = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": el["prompt"],
            "image_input": [],
            "aspect_ratio": el["aspect_ratio"],
            "resolution": "2K",
            "output_format": "png",
        },
    }
    r = http_post(CREATE_URL, body)
    if r.get("code") != 200:
        raise RuntimeError(f"submit failed for {el['name']}: {r}")
    tid = r["data"]["taskId"]
    print(f"  submitted {el['name']}  taskId={tid}", flush=True)
    return el["name"], tid


def poll_and_download(name, tid, max_wait=600):
    deadline = time.time() + max_wait
    while time.time() < deadline:
        info = http_get(f"{QUERY_URL}?taskId={tid}")
        state = info.get("data", {}).get("state")
        if state == "success":
            result = json.loads(info["data"]["resultJson"])
            raw_path = os.path.join(RAW_DIR, f"{name}.png")
            download(result["resultUrls"][0], raw_path)
            print(f"  downloaded raw {name}.png", flush=True)
            return raw_path
        if state == "fail":
            raise RuntimeError(f"task {tid} ({name}) failed: {info.get('data', {}).get('failMsg')}")
        time.sleep(8)
    raise TimeoutError(f"task {tid} ({name}) timed out")


# ----------------------------------------------------------------------
# Alpha extraction — three-zone curve + un-premultiply + auto-crop
# (per the ELEMENT_GENERATION_GUIDE.md pipeline)
# ----------------------------------------------------------------------
LOW, HIGH = 35, 70
ALPHA_CROP_THRESHOLD = 25
PAD_RATIO = 0.04


def black_to_alpha(in_path: str, out_path: str) -> None:
    img = Image.open(in_path).convert("RGB")
    arr = np.array(img).astype(np.float32)

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

    Image.fromarray(rgba).save(out_path, "PNG", optimize=True)


# ----------------------------------------------------------------------
# QA composite onto Athlon Rub forest green
# ----------------------------------------------------------------------
BRAND_BG = (15, 47, 47)  # #0F2F2F approx — Athlon Rub dark forest green


def qa_on_brand(rgba_path: str, qa_path: str) -> None:
    fg = Image.open(rgba_path).convert("RGBA")
    bg = Image.new("RGB", fg.size, BRAND_BG)
    bg.paste(fg, (0, 0), fg)
    bg.save(qa_path, "PNG", optimize=True)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    print(f"submitting {len(ELEMENTS)} Athlon Rub elements in parallel...", flush=True)
    submissions = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for fut in as_completed([ex.submit(submit, el) for el in ELEMENTS]):
            submissions.append(fut.result())

    print("\npolling for completion...", flush=True)
    failures = []
    raw_paths = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(poll_and_download, name, tid): name for name, tid in submissions}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                raw_paths[name] = fut.result()
            except Exception as e:
                print(f"  FAILED {name}: {e}", flush=True)
                failures.append(name)

    if failures:
        print(f"\n{len(failures)} generation failure(s): {failures}", flush=True)

    print("\nconverting black backgrounds to true alpha + QA-compositing on forest green...", flush=True)
    for name, raw_path in raw_paths.items():
        out_path = os.path.join(WORKING_DIR, f"{name}.png")
        qa_path  = os.path.join(QA_DIR, f"{name}_on_green.png")
        black_to_alpha(raw_path, out_path)
        qa_on_brand(out_path, qa_path)
        size_kb = os.path.getsize(out_path) // 1024
        print(f"  cleaned {name}.png  ({size_kb} KB)", flush=True)

    print(f"\nDone. {len(raw_paths)} of {len(ELEMENTS)} elements ready.")
    print(f"  transparent PNGs: {WORKING_DIR}")
    print(f"  QA composites:    {QA_DIR}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
