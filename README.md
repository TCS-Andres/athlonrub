# Athlon Rub

Brand asset repo for [Athlon Rub](https://athlonrub.com) — a next-generation
Thai-oil topical liniment for athletes. FDA-registered cosmetic, manufactured
in an FDA, ISO and GMP certified lab in the USA.

## What's in here

```
Athlon Rub/
├─ Home Page/
│  ├─ index.html              # The home page, single-file (HTML + embedded CSS)
│  └─ _extract_logo.py        # Pulls the primary logo out of the brand PDF
│                               and alpha-extracts it for web use
│
├─ Brand Elements/
│  ├─ 00_logo_full.png        # Primary brand lockup (shield + ATHLON RUB)
│  ├─ 00_logo_shield.png      # Shield crest only (no wordmark)
│  ├─ 01–10_*.png             # 10 transparent-PNG brand accents
│  ├─ generate_elements.py    # Initial 10-element generation pipeline
│  └─ regenerate_three.py     # Retry script for elements that fail QA
│
├─ ELEMENT_GENERATION_GUIDE.md  # Reusable methodology (alpha extraction,
│                                 prompt formula, content-filter pitfalls)
│
├─ New Logo Athlon Rub Cinturon.pdf  # Brand logo system / guidelines
│
└─ .gitignore                # Excludes the Master Brain docs (sensitive)
```

## The home page

Single-file static landing page at `Home Page/index.html`. Open directly in
a browser — no build step. Loads Google Fonts (Oswald + Inter) and references
the PNGs in `Brand Elements/`. Section flow mirrors `tidl.com`:

```
nav → hero → credibility strip → clean-credentials chips → where to find us
→ persona grid → how-to-use → product grid → bundles → find-your-fit CTA
→ why it hits different → heritage band → reviews → stat band
→ featured product → FAQ → instagram feed → newsletter → footer
```

All copy stays inside Athlon Rub's FDA-cosmetic claim guardrails — no
*pain / heal / anti-inflammatory / treat / cure* language. Benefits framed
as what individual ingredients are known to do.

## The 10 brand elements

Generated through [kie.ai](https://kie.ai)'s Nano Banana Pro API. Each was
produced on a solid black background, then converted to true alpha via the
premultiplied-alpha pipeline documented in `ELEMENT_GENERATION_GUIDE.md`.
Two logo variants (`00_logo_full.png`, `00_logo_shield.png`) are extracted
from page 1 of the brand PDF using the same alpha pipeline.

| # | Element | Use case |
|---|---|---|
| 01 | Triple chevron forward | CTAs, forward motion, FAQ open/close |
| 02 | Athletic 5-point star | Star ratings, credential badges, step numbers |
| 03 | Shield outline frame | Product card frames |
| 04 | "A" athlete monogram | Brand mark in persona / feature cards |
| 05 | Runner silhouette | Persona iconography, Instagram tiles |
| 06 | Laurel wreath | Heritage band, "find your fit" CTA |
| 07 | Crossed lightning bolts | Power/feature iconography |
| 08 | Star divider bar | Section dividers |
| 09 | Dynamic speed streaks | Hero accent, newsletter band |
| 10 | Ribbon banner | "Best value" / "Most popular" labels |

## Regenerating elements

Set your kie.ai API key:

```bash
export KIE_API_KEY=your_key_from_kie_ai
```

Then either:

```bash
# Generate all 10 elements (writes to Brand Elements/)
python3 "Brand Elements/generate_elements.py"

# Retry only specific elements that failed QA
python3 "Brand Elements/regenerate_three.py"

# Re-extract the logo from the brand PDF
python3 "Home Page/_extract_logo.py"
```

Each script runs the full pipeline: API submission → polling → download →
black-to-alpha conversion → auto-crop → QA composite onto brand forest green.

## Brand palette

| Token | Hex | Use |
|---|---|---|
| `--green`   | `#0F2F2F` | Primary surface — nav, hero, heritage band |
| `--green-2` | `#163C3C` | Card surfaces inside green sections |
| `--green-3` | `#0a2222` | Deeper accents, newsletter band |
| `--gold`    | `#D9AF37` | Primary accent — buttons, dividers, stars |
| `--gold-2`  | `#B8932A` | Gold on hover / muted gold text |
| `--cream`   | `#EAE9CB` | Light backgrounds (credibility strip, FAQ) |
| `--cream-2` | `#F6F4E3` | Page-level light surfaces |
| `--ink`     | `#0B1A1A` | Body text |

## Compliance notes

Athlon Rub is registered with the FDA as a cosmetic product, **not** as an
over-the-counter drug. The website may not claim pain relief, anti-inflammatory
effect, healing, treatment, prevention, or cure of any condition. Approved
claim families: warming sensation, fast-absorbing, supports the body's natural
recovery process, prepares the body for activity, time-tested heritage. When
adding new copy, default to ingredient-led framing (*"Wintergreen, an ingredient
in Athlon Rub, is widely recognized for its warming properties"*) rather than
product-claim framing.

---

© Athlon Rub. External use only.
