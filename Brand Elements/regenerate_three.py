"""
Retry the 3 elements that failed QA on the first pass:
  03 shield_outline_frame  — interior came back as opaque white
  05 runner_silhouette_icon — model drew a green badge + white ring (not on black)
  09 dynamic_speed_streaks  — partial opaque cream fills behind the streaks

Imports the helpers from generate_elements.py so we don't duplicate code.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_elements import (  # noqa: E402
    BRAND_STYLE, GOLD, CREAM,
    submit, poll_and_download,
    black_to_alpha, qa_on_brand,
    WORKING_DIR, RAW_DIR, QA_DIR,
)


RETRIES = [
    {
        # Was: "inside of the shield is empty so it can frame other content"
        # Model painted that as solid white. Reframe as "open / cut-out
        # silhouette" so the interior reads as void, not as a filled face.
        "name": "03_shield_outline_frame",
        "aspect_ratio": "4:5",
        "prompt": (
            f"A heraldic SHIELD outline-only frame in {GOLD} — JUST the "
            "outer rim of an Athlon Rub-shaped shield (rounded shoulders at "
            "the top, gently curved sides tapering to a pointed base), with "
            "a clean bold uniform stroke thickness forming the perimeter "
            "ONLY. The shield is hollow: the area inside the outline shows "
            "the same flat black studio backdrop as the area outside the "
            "outline — like a metal frame photographed against a black "
            "sweep, with nothing behind it. NO interior fill, NO white "
            "panel, NO inner color, NO inner emblem. The gold rim is the "
            f"only artwork on the canvas. {BRAND_STYLE}"
        ),
    },
    {
        # Was: came back as a circular badge graphic (green disc + white
        # outer ring). The "icon" language pulled the model toward a
        # complete UI badge. Strip out badge framing entirely and say
        # solid filled silhouette only.
        "name": "05_runner_silhouette_icon",
        "aspect_ratio": "1:1",
        "prompt": (
            f"A solid filled SILHOUETTE of a sprinting runner in {GOLD}, "
            "side-profile, facing right, captured mid-stride: torso leaning "
            "forward, one leg extended back, the other lifted and bent "
            "ahead, arms swinging in opposition. Single contiguous solid "
            "gold shape, no outline, no inner detail, no badge or circle "
            "behind it, no disc, no ring, no border. Just the runner "
            "shape alone, centered on the flat black backdrop. Inspired by "
            f"the small athlete pictograms on the Athlon Rub bottle label. {BRAND_STYLE}"
        ),
    },
    {
        # Was: streaks ended up sitting on opaque cream rectangles.
        # Be very explicit: each streak is an isolated stroke, with black
        # showing between and around them.
        "name": "09_dynamic_speed_streaks",
        "aspect_ratio": "16:9",
        "prompt": (
            f"Four to five SEPARATE thin tapered horizontal speed-streak "
            f"strokes in {CREAM}, arranged with slight vertical stagger. "
            "Each individual stroke begins as a sharp point on the LEFT, "
            "thickens slightly toward the middle, and tapers back to a thin "
            "point on the RIGHT — like fast motion-blur trails. The strokes "
            "are clearly DISTINCT and SEPARATE: visible black backdrop "
            "shows between every pair of streaks, above the top streak, "
            "below the bottom streak, and around the entire cluster. NO "
            "filled rectangle behind them, NO cream-colored panel, NO solid "
            f"banner shape — just isolated cream strokes on flat black. {BRAND_STYLE}"
        ),
    },
]


def main():
    print(f"retrying {len(RETRIES)} elements...", flush=True)
    submissions = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        for fut in as_completed([ex.submit(submit, el) for el in RETRIES]):
            submissions.append(fut.result())

    print("\npolling...", flush=True)
    raw_paths = {}
    failures = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(poll_and_download, name, tid): name for name, tid in submissions}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                raw_paths[name] = fut.result()
            except Exception as e:
                print(f"  FAILED {name}: {e}", flush=True)
                failures.append(name)

    print("\nalpha-extracting + QA compositing...", flush=True)
    for name, raw_path in raw_paths.items():
        out_path = os.path.join(WORKING_DIR, f"{name}.png")
        qa_path  = os.path.join(QA_DIR, f"{name}_on_green.png")
        black_to_alpha(raw_path, out_path)
        qa_on_brand(out_path, qa_path)
        size_kb = os.path.getsize(out_path) // 1024
        print(f"  cleaned {name}.png ({size_kb} KB)", flush=True)

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
