# -*- coding: utf-8 -*-
"""Kinetic typography — type-first motion engine.

The visual language of Steve Jobs quote videos, Nike brand films, Apple keynote slides,
Beeple cold opens, A24 title cards, lyric videos, "After Effects agency reel" cuts.
Text IS the visual. One word fills the frame. Dramatic scale changes. Rhythmic reveals
tied to the voice. Flat colour blocks that frame or swap behind the type. No photos
(the type is the point).

WHAT MAKES IT WORK
  * one idea per card, often just ONE word, massive on screen
  * caption style = `pop` so each spoken word hits with a big outlined highlight
  * title style: dramatic weights, extreme tracking, mixed cases, mixed fonts
  * every scene breathes: text SLIDES in from an edge, settles with overshoot
  * accent colour SWAPS between scenes (red / yellow / cyan / white rotation)
  * black / white / flat colour backgrounds -- never photo
  * markup is the whole point: `_word_` highlighter, `*accent*`, `[boxed]`, `~underlined~`
  * numbers hit hard: `counter` from 0 to a big number, 1-2 s rolling animation
  * silence between words is as important as the words -- 0.5-1 s empty beats

ESSENTIAL ELEMENTS
  title         massive display type, 1 word or short phrase per scene
  keyword       alternates neon / outline / marker / label -- never pill
  counter       the ONLY numeric visual; set `prefix`/`suffix` for units
  callout       tiny mono label at a focal corner, like a frame reference
  stamp         occasional for "VOL 2" tabs, use `label` box

LAYOUTS unique to this style
  mega_word      ONE word fills the frame -- the signature move
  word_stack     3 words stacked vertically (left-align, different sizes)
  split_type     left half colour block + right half type
  marquee        text that sweeps across the frame
  manifesto      full-frame paragraph in body font, one phrase bolded

AVOID
  * photos (except as fullscreen colour swatches), vignette, grain, letterbox
  * mono headlines (reserve mono for the kicker tag only)
  * sticker frames, polaroids, drop shadows, doodles, scribbles

IMAGE PROMPTS: this style rarely needs images. When a scene DOES need a single
abstract shape (gradient, texture, blur), the prompt is a minimal abstract gradient
with the scene's accent colour.
"""

NAME = "kinetic"
ALIASES = ["typography", "kinetic_typography", "lyric", "motion_type"]

_NEG = ("no illustration of a face, no photoreal scene, no cityscape, no character, "
        "no text, no letters, no watermark, no UI, no frames, no borders, no collage")

STYLE = {
    "look": {
        # by default dark; override per scene with `accent` field to swap palette
        "bg": (8, 8, 10),
        "ink": (248, 248, 250),
        "muted": (160, 160, 170),
        "accent": (242, 76, 61),         # cadmium red (swap per scene)
        "accent2": (255, 230, 120),      # pale yellow highlighter
        "accent3": (120, 220, 240),      # electric cyan
        "panel": (14, 14, 18, 245),
        "stamp_color": (242, 76, 61),
        "string_color": (248, 248, 250),
        "caption": "pop",                # BIG outlined one-word highlights
        "asset_frame": "clean",
        "photo_frame": "card",
        "letterbox": 0.0, "grade": "", "grain": 0, "vignette": False,
        "transition": "whip",            # fast, confident swap
        "camera": "still",               # motion comes from TEXT, not the camera
        "kicker_prefix": "",
        "title_font": "impact",          # Anton all-caps for display
        "boxes": ["neon", "outline", "marker", "label"],
    },
    "prompt": {
        "clarity": (
            "minimal abstract composition, ONE large flat colour field, soft gradient edge, "
            "heavy negative space, no subjects, no faces, no architecture -- a backdrop "
            "for massive typography"
        ),
        "medium": "minimal abstract graphic design background, flat colour field with subtle gradient and gentle film grain",
        "lighting": "flat even wash, no cast shadows",
        "palette": "monochromatic single-colour wash with one slightly darker vignette corner",
        "camera": {"shot": "flat graphic", "lens": "flat 2D", "angle": "straight-on", "movement": "none"},
        "mood": "bold, confident, kinetic, modern",
        "quality": "ultra-minimal, massive negative space, print-ready, zero clutter",
        "negative": _NEG,
        "asset_medium": "minimal flat colour swatch with soft gradient and faint grain",
    },
}

LAYOUTS_16_9 = {
    # THE signature: one word owns the frame
    "mega_word": {
        "tag": (0.06, 0.10, 0.88, 0.04),
        "title": (0.06, 0.18, 0.88, 0.48),       # massive title area
        "label": (0.06, 0.68, 0.88, 0.05),
    },
    # 3 words stacked vertically, left-aligned, each a different size
    "word_stack": {
        "tag": (0.06, 0.10, 0.88, 0.04),
        "a": (0.06, 0.20, 0.88, 0.17),
        "b": (0.06, 0.40, 0.88, 0.17),
        "c": (0.06, 0.60, 0.88, 0.17),
    },
    # Left colour block + right type panel
    "split_type": {
        "back": (0.00, 0.00, 0.46, 1.00),         # colour block behind the type (add a `block` item)
        "tag": (0.52, 0.12, 0.44, 0.04),
        "title": (0.52, 0.18, 0.44, 0.28),
        "label": (0.52, 0.48, 0.44, 0.06),
        "list": (0.52, 0.56, 0.44, 0.19),
    },
    # Full-frame paragraph with ONE phrase bolded
    "manifesto": {
        "tag": (0.06, 0.08, 0.88, 0.04),
        "title": (0.06, 0.18, 0.88, 0.50),
        "label": (0.06, 0.70, 0.88, 0.06),
    },
    # Marquee strip (horizontal band)
    "marquee": {
        "tag": (0.06, 0.14, 0.88, 0.04),
        "title": (0.06, 0.26, 0.88, 0.22),
        "label": (0.06, 0.54, 0.88, 0.06),
    },
}
LAYOUTS_9_16 = {
    "mega_word": {
        "tag": (0.07, 0.10, 0.86, 0.03),
        "title": (0.07, 0.22, 0.86, 0.40),
        "label": (0.07, 0.64, 0.86, 0.04),
    },
    "word_stack": {
        "tag": (0.07, 0.08, 0.86, 0.03),
        "a": (0.07, 0.17, 0.86, 0.14),
        "b": (0.07, 0.33, 0.86, 0.14),
        "c": (0.07, 0.49, 0.86, 0.14),
    },
    "manifesto": {
        "tag": (0.07, 0.14, 0.86, 0.03),
        "title": (0.07, 0.20, 0.86, 0.44),
        "label": (0.07, 0.66, 0.86, 0.04),
    },
    "marquee": {
        "tag": (0.07, 0.22, 0.86, 0.03),
        "title": (0.07, 0.32, 0.86, 0.24),
        "label": (0.07, 0.58, 0.86, 0.04),
    },
}

RECIPES = {
    # Single word fills the screen (change `accent` per scene to swap colour)
    "mega_word": {
        "layout": "mega_word", "bg": "dark", "transition": "whip",
        "items": [
            {"type": "kicker", "text": "VOL. 01"},
            {"type": "title", "text": "*रुकिए।*", "font": "impact", "fill": "gradient"},
            {"type": "lower_third", "text": "ONE WORD. ONE IDEA.", "slot": "label"},
        ],
    },
    # Three words stacked
    "word_stack": {
        "layout": "word_stack", "bg": "dark",
        "items": [
            {"type": "kicker", "text": "THE RULES"},
            {"type": "title", "text": "*सत्ता।*", "slot": "a", "font": "impact"},
            {"type": "title", "text": "_साज़िश।_", "slot": "b", "font": "impact"},
            {"type": "title", "text": "~खून।~", "slot": "c", "font": "impact"},
        ],
    },
    # Giant counter + unit label
    "counter_hero": {
        "layout": "mega_word", "bg": "dark",
        "items": [
            {"type": "kicker", "text": "NUMBERS DON'T LIE"},
            {"type": "counter", "from": 0, "to": 104, "suffix": "", "slot": "title",
             "at": "WORD", "dur": 1.6, "plain": True},
            {"type": "lower_third", "text": "YEARS OF RANA RULE", "slot": "label"},
        ],
    },
    # Full-frame paragraph with one bolded phrase
    "manifesto": {
        "layout": "manifesto", "bg": "dark",
        "items": [
            {"type": "kicker", "text": "MANIFESTO"},
            {"type": "title", "text": "सत्ता किसी *एक खानदान* की नहीं होती।", "font": "serif"},
            {"type": "lower_third", "text": "— HISTORY, 1951", "slot": "label"},
        ],
    },
    # Split block: solid colour left, type right
    "split": {
        "layout": "split_type", "bg": "dark",
        "items": [
            {"type": "kicker", "text": "CHAPTER TWO"},
            {"type": "title", "text": "*रक्त*रंजित रात"},
            {"type": "lower_third", "text": "14 SEPT 1846", "slot": "label"},
            {"type": "list", "items": [
                {"text": "मध्यरात्रि", "at": "WORD_1"},
                {"text": "आदेश", "at": "WORD_2"},
                {"text": "40 मृत", "at": "WORD_3"},
            ]},
        ],
    },
}

EXAMPLES = [
    "ONE word hero: RECIPES['mega_word']",
    "3-word rhythm: RECIPES['word_stack']",
    "big counter: RECIPES['counter_hero']",
    "quote manifesto: RECIPES['manifesto']",
    "colour block + type: RECIPES['split']",
]

# ---- asset plan: typography IS the video; images are rare abstract backdrops ---------------------------
BEAT_S = 1.2
MIX = {"scene": 0.08, "asset": 0.12, "reuse": 0.0, "text": 0.80}
MENU = {
    "scene": ["flat colour field with soft gradient", "abstract grain texture", "single geometric shape on a colour field"],
    "asset": ["single bold object on a colour field", "simple icon-like silhouette"],
}
ACCENTS = ["cadmium red field", "electric cyan field", "pale yellow field", "pure white field"]

DESIGN = __doc__
