# -*- coding: utf-8 -*-
"""Retro 8-Bit Arcade Style — pixel art sprites, arcade badges, retro stage bosses, and CRT scanlines.

Based on the prompt engineering methodologies from skills/retro-8bit-arcade-style/SKILL.md.
"""

NAME = "arcade"
ALIASES = ["8bit", "retro", "pixel", "retro_arcade", "retro_8bit", "arcade_8bit"]

_NEG = ("no photorealism, no 3D render, no smooth brushstrokes, no modern photograph, "
        "no blurry textures, no text, no captions, no watermark, no logo, no UI")

STYLE = {
    "look": {
        "bg": (16, 14, 28), "ink": (245, 245, 250), "muted": (140, 140, 170),
        "accent": (255, 215, 0),           # arcade gold
        "accent2": (0, 225, 255),          # retro cyan
        "accent3": (255, 50, 95),          # arcade crimson / neon red
        "panel": (24, 20, 42, 235),
        "stamp_color": (255, 50, 95), "string_color": (255, 215, 0),
        "caption": "box", "asset_frame": "clean", "photo_frame": "card",
        "letterbox": 0.0, "grade": "eq=contrast=1.12:saturation=1.15",
        "grain": 0, "vignette": True, "transition": "whip", "camera": "drift",
        "kicker_prefix": "STAGE", "title_font": "mono",
        "boxes": ["rpg", "neon", "label", "pill", "outline"],
    },
    "prompt": {
        "clarity": (
            "16-bit retro arcade game pixel art, vibrant pixelated sprites, dramatic isometric or side-scrolling perspective, "
            "dithering pixel shadows, rich arcade game color palette, uncluttered composition with dark negative space for title"
        ),
        "medium": "16-bit retro arcade video game pixel art, nostalgic CRT scanlines aesthetic, master pixel artist",
        "lighting": "vibrant neon backlight, dramatic pixelated rim lighting, high contrast pixel shadows",
        "palette": "rich 16-bit arcade palette: golden yellow, deep navy blue, arcade crimson, glowing cyan, emerald green",
        "camera": {"shot": "wide establishing shot", "lens": "isometric 16-bit game view", "angle": "slightly elevated 30-degree",
                   "movement": "smooth horizontal 2D parallax side-scroll"},
        "mood": "epic, adventurous, nostalgic arcade challenge",
        "quality": "crisp pixel grid, gorgeous pixel dithering, authentic 90s arcade aesthetic",
        "negative": _NEG,
        "asset_medium": "isolated 16-bit pixel art sprite prop on solid magenta background, crisp pixel edges",
    },
}

LAYOUTS_16_9 = {
    "boss_stage": {
        "tag": (0.06, 0.07, 0.44, 0.05), "title": (0.06, 0.14, 0.44, 0.28),
        "center": (0.52, 0.10, 0.44, 0.65),
    },
    "rpg_dialogue": {
        "tag": (0.06, 0.07, 0.20, 0.04),
        "center": (0.28, 0.10, 0.44, 0.44),
        "label": (0.10, 0.56, 0.80, 0.19),
    },
    "loot_card": {
        "tag": (0.06, 0.07, 0.88, 0.05), "title": (0.06, 0.13, 0.88, 0.14),
        "a": (0.10, 0.30, 0.35, 0.44), "b": (0.55, 0.30, 0.35, 0.44),
    },
}

LAYOUTS_9_16 = {
    "boss_stage": {
        "tag": (0.08, 0.08, 0.84, 0.04), "title": (0.08, 0.13, 0.84, 0.12),
        "center": (0.10, 0.26, 0.80, 0.42),
    },
    "rpg_dialogue": {
        "tag": (0.08, 0.08, 0.84, 0.04),
        "center": (0.15, 0.14, 0.70, 0.34),
        "label": (0.08, 0.50, 0.84, 0.18),
    },
    "loot_card": {
        "tag": (0.08, 0.08, 0.84, 0.04), "title": (0.08, 0.13, 0.84, 0.12),
        "a": (0.12, 0.26, 0.76, 0.20), "b": (0.12, 0.48, 0.76, 0.20),
    },
}

DEFAULT_MENU = {
    "scene": ["wide 16-bit arcade stage background", "isometric game room", "cyberpunk pixel city level",
              "retro boss battle arena", "dungeon chamber pixel art", "2D side-scrolling platformer backdrop"],
    "asset": ["pixel art character sprite", "arcade weapon / tool", "pixel gold coin / treasure chest",
              "retro vehicle sprite", "pixel potion / powerup badge", "arcade flag / emblem"],
}

PLAN = {
    "beat_s": 2.2,
    "mix": {"scene": 0.55, "asset": 0.35, "reuse": 0.05, "text": 0.05},
    "menu": DEFAULT_MENU,
    "accents": ["golden yellow", "neon cyan", "arcade crimson"],
}

BEAT_S = 1.2
MIX = {"scene": 0.55, "asset": 0.35, "reuse": 0.05, "text": 0.05}
