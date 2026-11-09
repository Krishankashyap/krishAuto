# -*- coding: utf-8 -*-
"""motion_mix.py: High-Engagement Asset + Typography Compositor & Visual Annotation Engine.

Inspired by top-tier motion graphics (Vox, Butter, Orchiv):
1. Gradient Typography: Fiery orange-red, royal purple, electric cyan gradients with dual-tier shadows.
2. Mix-Match Color Text: Dynamic multi-color word coloring ({red}word{/red}, {blue}word{/blue}, pills).
3. Pinned Process Cards: Angled paper cards with fiery gradient headlines and pushpins.
4. Procedural Technical Backgrounds: Dot grids, blueprint graph grids, tactile paper textures.
5. Asset + Typography Duets: Asymmetric layouts with assets perched atop or interlocking with typography.
6. Hand-Drawn Doodle Annotations: Crayon loops, marker highlights, sticky notes, process ladders.
"""

import math, os, sys, re
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Color standards
PAPER = (248, 246, 239)
PAPER_DARK = (24, 27, 36)
INK = (20, 17, 15)
INK_MUTED = (85, 80, 75)
YELLOW_HIGHLIGHT = (252, 238, 56)
RED_MARKER = (232, 44, 44)
BLUE_BRAND = (35, 75, 215)
CYAN_ELECTRIC = (0, 215, 255)
PURPLE_ROYAL = (145, 55, 235)
GREEN_ACCENT = (46, 185, 95)
ORANGE_FIRE = (255, 118, 0)
WHITE = (255, 255, 255)

GRADIENT_PRESETS = {
    "fire": ((255, 118, 0), (228, 30, 30)),       # Fiery warm orange into bold red (Ref 2)
    "purple": ((175, 75, 255), (85, 20, 185)),     # Royal vibrant purple into deep violet (Ref 3)
    "violet": ((195, 90, 255), (105, 30, 215)),
    "cyan": ((0, 215, 255), (30, 85, 240)),        # Electric cyan to punchy blue (Ref 4)
    "electric_blue": ((0, 215, 255), (30, 85, 240)),
    "sunset": ((255, 95, 105), (255, 185, 45)),
    "emerald": ((20, 210, 140), (5, 130, 85)),
    "gold": ((255, 215, 0), (218, 140, 15)),
    "crimson": ((255, 45, 85), (165, 10, 40)),
}

def natural_shadow_under(sprite, off=(0, 8), blur=16, strength=0.14, tint=(26, 20, 16)):
    """v3 natural contour shadow: returns a NEW sprite (sprite + soft contour drop shadow 0px 8px 16px rgba(0,0,0,0.14))
    on a canvas padded by 3.2x blur, so the shadow follows the asset contour and fades smoothly to 0.
    The original sprite sits at (m, m) of the result; m is returned so callers can keep their positions."""
    sprite = sprite if sprite.mode == "RGBA" else sprite.convert("RGBA")
    m = int(blur * 3.2) + max(abs(off[0]), abs(off[1])) + 2
    W, H = sprite.width + 2 * m, sprite.height + 2 * m
    a = sprite.split()[3]
    out = Image.new("RGBA", (W, H), tint + (0,))
    amb = Image.new("L", (W, H), 0); amb.paste(a, (m + off[0], m + off[1]))
    con = Image.new("L", (W, H), 0); con.paste(a, (m + off[0] // 4, m + off[1] // 4))
    amb = np.asarray(amb.filter(ImageFilter.GaussianBlur(blur)), np.float32) * strength
    con = np.asarray(con.filter(ImageFilter.GaussianBlur(max(1, blur // 4))), np.float32) * strength * 0.8
    al = 255 - (255 - amb) * (255 - con) / 255
    out.putalpha(Image.fromarray(np.clip(al, 0, 255).astype(np.uint8)))
    out.alpha_composite(sprite, (m, m))
    return out, m



DEV_RE = re.compile(r"[\u0900-\u097F\uA8E0-\uA8FF\u1CD0-\u1CFF]")

def resolve_font(style="bold", size=48, text=""):
    """Resolves true type font from fonts directory or system with heavy bold weight prioritization and full Devanagari support."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base_dir, "fonts")
    is_dev = bool(text and DEV_RE.search(text)) or style in ("hindi", "devanagari")
    
    candidates = []
    if is_dev:
        candidates += [
            os.path.join(fonts_dir, "hindi", "NotoSansDevanagari-VF.ttf"),
            os.path.join(fonts_dir, "hindi", "Baloo2-Bold.ttf"),
            os.path.join(fonts_dir, "hindi", "Baloo2-ExtraBold.ttf"),
            os.path.join(fonts_dir, "hindi", "Khand-Bold.ttf"),
            os.path.join(fonts_dir, "Kalam-Bold.ttf"),
            "/system/fonts/NotoSansDevanagari-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
        ]
    elif style in ("serif", "editorial", "luxury"):
        candidates += [
            os.path.join(fonts_dir, "english", "PlayfairDisplay-Bold.ttf"),
            os.path.join(fonts_dir, "english", "Lora-Bold.ttf"),
            os.path.join(fonts_dir, "english", "Merriweather-Bold.ttf"),
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
        ]
    elif style == "handwritten":
        candidates += [
            os.path.join(fonts_dir, "Kalam-Bold.ttf"),
            os.path.join(fonts_dir, "PatrickHand-Regular.ttf")
        ]
    elif style == "mono":
        candidates += [
            os.path.join(fonts_dir, "english", "SpaceMono-Bold.ttf"),
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
        ]
    elif style in ("display", "anton", "headline", "impact"):
        candidates += [
            os.path.join(fonts_dir, "english", "Anton-Regular.ttf"),
            "/home/cat/.local/share/fonts/xdeep/Anton-Regular.ttf",
            os.path.join(fonts_dir, "hindi", "Khand-Bold.ttf"),
            os.path.join(fonts_dir, "english", "Aquawax-Black.ttf")
        ]
    else:  # bold display sans default
        candidates += [
            os.path.join(fonts_dir, "english", "Anton-Regular.ttf"),
            "/home/cat/.local/share/fonts/xdeep/Anton-Regular.ttf",
            os.path.join(fonts_dir, "english", "LiberationSans-Bold.ttf"),
            os.path.join(fonts_dir, "hindi", "Khand-Bold.ttf"),
            os.path.join(fonts_dir, "hindi", "Baloo2-ExtraBold.ttf"),
            os.path.join(fonts_dir, "english", "Aquawax-Black.ttf"),
            os.path.join(fonts_dir, "english", "Metropolis-Bold.otf"),
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        ]
        
    # Portable Android & Termux fallback paths
    termux_prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    candidates += [
        "/system/fonts/Roboto-Bold.ttf",
        "/system/fonts/Roboto-Medium.ttf",
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/NotoSansDevanagari-Bold.ttf",
        "/system/fonts/NotoSans-Bold.ttf",
        os.path.join(termux_prefix, "share/fonts/TTF/DejaVuSans-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
    ]
        
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, layout_engine=ImageFont.Layout.RAQM)
            except Exception:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
    return ImageFont.load_default()

def parse_color_spec(spec):
    """Parses color preset name, hex string (#RRGGBB), or RGB tuple."""
    if isinstance(spec, (tuple, list)):
        return tuple(spec[:3])
    if isinstance(spec, str):
        spec = spec.strip().lower()
        if spec == "red": return RED_MARKER
        if spec == "blue": return BLUE_BRAND
        if spec == "cyan": return CYAN_ELECTRIC
        if spec == "purple": return PURPLE_ROYAL
        if spec == "yellow": return YELLOW_HIGHLIGHT
        if spec == "green": return GREEN_ACCENT
        if spec == "orange": return ORANGE_FIRE
        if spec == "ink" or spec == "black": return INK
        if spec == "white": return WHITE
        if spec.startswith("#"):
            h = spec.lstrip("#")
            if len(h) == 6:
                return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    return INK

def draw_gradient_text(
    text: str,
    gradient="fire",
    font_size: int = 72,
    font_style: str = "bold",
    shadow: bool = True,
    tracking: int = -2,
    angle: float = 0.0,
    bevel_highlight: bool = True,
    padding: int = 50
) -> Image.Image:
    """Renders high-impact linear gradient typography with dual-tier shadows and zero text overflow."""
    # Format and clean text: replace underscores with spaces
    clean_text = text.replace("_", " ").strip()
    
    # Auto-wrap long single-line titles into balanced 2-line headlines
    if "//" not in clean_text and "\n" not in clean_text:
        words = clean_text.split()
        if len(words) >= 4 or (len(words) >= 3 and len(clean_text) > 18):
            mid = (len(words) + 1) // 2
            clean_text = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
    
    # Resolve gradient stops
    if isinstance(gradient, str) and gradient.lower() in GRADIENT_PRESETS:
        c_top, c_bot = GRADIENT_PRESETS[gradient.lower()]
    elif isinstance(gradient, (tuple, list)) and len(gradient) >= 2:
        c_top, c_bot = parse_color_spec(gradient[0]), parse_color_spec(gradient[1])
    else:
        c_top, c_bot = GRADIENT_PRESETS["fire"]
        
    dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    d_dummy = ImageDraw.Draw(dummy)
    
    lines = clean_text.replace("//", "\n").split("\n")
    
    is_dev = bool(DEV_RE.search(clean_text))
    # Dynamic auto-shrink to guarantee fitting within 1180px safe width
    max_allowed_w = 1180
    while font_size > 28:
        font = resolve_font(font_style, font_size, text=clean_text)
        line_boxes = []
        max_w = 0
        total_h = 0
        line_h_base = 0
        
        for line in lines:
            if is_dev:
                bbox = d_dummy.textbbox((0, 0), line, font=font)
                w_cur = bbox[2] - bbox[0]
                h_cur = bbox[3] - bbox[1]
            else:
                w_cur = 0
                h_cur = 0
                for ch in line:
                    bbox = d_dummy.textbbox((0, 0), ch, font=font)
                    cw = bbox[2] - bbox[0]
                    ch_h = bbox[3] - bbox[1]
                    w_cur += cw + tracking
                    h_cur = max(h_cur, ch_h)
            line_boxes.append((line, w_cur, h_cur))
            max_w = max(max_w, w_cur)
            line_h_base = max(line_h_base, h_cur)
            total_h += int(h_cur * 1.25)
            
        if max_w <= max_allowed_w:
            break
        font_size -= 4
        
    # Oversize buffer for text rendering
    tex_w = max(10, max_w + 40)
    tex_h = max(10, total_h + 30)
    
    # 1. Generate text alpha mask
    mask_im = Image.new("L", (tex_w, tex_h), 0)
    d_mask = ImageDraw.Draw(mask_im)
    
    cur_y = 15
    for line, lw, lh in line_boxes:
        # Center-align multi-line gradient text
        cur_x = 20 + max(0, int((max_w - lw) / 2))
        if is_dev:
            d_mask.text((cur_x, cur_y), line, fill=255, font=font)
        else:
            for ch in line:
                bbox = d_dummy.textbbox((0, 0), ch, font=font)
                cw = bbox[2] - bbox[0]
                d_mask.text((cur_x, cur_y), ch, fill=255, font=font)
                cur_x += cw + tracking
        cur_y += int(lh * 1.25)
        
    # 2. Build smooth linear gradient texture
    grad_arr = np.zeros((tex_h, tex_w, 4), dtype=np.uint8)
    for y in range(tex_h):
        p = y / float(max(1, tex_h - 1))
        # Ease gradient slightly towards bottom for punchy visual weight
        p_curved = p ** 1.15
        r = int(c_top[0] * (1.0 - p_curved) + c_bot[0] * p_curved)
        g = int(c_top[1] * (1.0 - p_curved) + c_bot[1] * p_curved)
        b = int(c_top[2] * (1.0 - p_curved) + c_bot[2] * p_curved)
        grad_arr[y, :, 0] = r
        grad_arr[y, :, 1] = g
        grad_arr[y, :, 2] = b
        grad_arr[y, :, 3] = 255
        
    grad_im = Image.fromarray(grad_arr, mode="RGBA")
    grad_im.putalpha(mask_im)
    
    # 3. Specular top bevel highlight for tactile physical pop
    if bevel_highlight:
        top_rim = mask_im.copy()
        # Shift mask down 2px and subtract to find top rim edges
        shifted = Image.new("L", (tex_w, tex_h), 0)
        shifted.paste(mask_im, (0, 2))
        rim_diff = np.clip(np.array(mask_im, dtype=np.int16) - np.array(shifted, dtype=np.int16), 0, 255).astype(np.uint8)
        rim_im = Image.new("RGBA", (tex_w, tex_h), (255, 255, 255, 0))
        rim_im.putalpha(Image.fromarray((rim_diff * 0.45).astype(np.uint8)))
        grad_im = Image.alpha_composite(grad_im, rim_im)
        
    # 4. Composite natural two-tier shadow (v3: padded, never clipped)
    if shadow:
        final_im, _ = natural_shadow_under(grad_im, off=(8, 14), blur=16, strength=0.34)
    else:
        final_im = grad_im
        
    if abs(angle) > 0.01:
        final_im = final_im.rotate(angle, resample=Image.BICUBIC, expand=True)
        
    return final_im

def draw_mix_match_text(
    text_spec,
    base_font_size: int = 64,
    base_style: str = "bold",
    tracking: int = -2,
    line_spacing: float = 1.25,
    padding: int = 40,
    shadow: bool = True
) -> Image.Image:
    """Renders multi-color mixed typography supporting inline tags or structured tuples.
    
    Example text_spec:
      "You've got the {red}ideas{/red} and {red}content{/red}"
      "{mono}01 //{/mono} {fire}STRATEGY{/fire} Without Content"
      "{pill:yellow}FREE{/pill} {blue}ANIMATION TOOL{/blue}"
    """
    dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    d_dummy = ImageDraw.Draw(dummy)
    
    # 1. Parse into structured lines and tokens
    lines_raw = text_spec.replace("//", chr(10)).split(chr(10)) if isinstance(text_spec, str) else [text_spec]
    
    parsed_lines = []
    max_w = 0
    total_h = 0
    
    for l_raw in lines_raw:
        tokens = []
        if isinstance(l_raw, str):
            # Parse tags like {red}word{/red}, {blue}word{/blue}, {fire}word{/fire}, {pill:yellow}word{/pill}
            pattern = re.compile(r"\{([a-zA-Z0-9_:]+)\}(.*?)\{/\}|([^{]+)")
            matches = pattern.findall(l_raw)
            for tag, tagged_txt, plain_txt in matches:
                if tagged_txt:
                    tokens.append({"tag": tag, "text": tagged_txt})
                elif plain_txt:
                    tokens.append({"tag": "normal", "text": plain_txt})
        elif isinstance(l_raw, list):
            for item in l_raw:
                if isinstance(item, tuple):
                    tokens.append({"tag": item[1], "text": item[0]})
                elif isinstance(item, dict):
                    tokens.append(item)
                    
        # Token metrics
        line_tokens = []
        cur_x = 0
        line_h = 0
        for tok in tokens:
            tag = tok.get("tag", "normal")
            txt = tok.get("text", "")
            
            # Resolve font and style
            f_style = base_style
            if "serif" in tag: f_style = "serif"
            elif "mono" in tag: f_style = "mono"
            elif "hand" in tag: f_style = "handwritten"
            
            f_size = base_font_size
            if "pill" in tag: f_size = int(base_font_size * 0.85)
            
            font = resolve_font(f_style, f_size, text=txt)
            bbox = d_dummy.textbbox((0, 0), txt, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            line_h = max(line_h, th)
            
            line_tokens.append({
                "text": txt,
                "tag": tag,
                "font": font,
                "style": f_style,
                "w": tw,
                "h": th,
                "x": cur_x
            })
            cur_x += tw + tracking
            
        max_w = max(max_w, cur_x)
        total_h += int(line_h * line_spacing)
        parsed_lines.append({"tokens": line_tokens, "w": cur_x, "h": line_h})
        
    # Oversize buffer
    tex_w = max_w + padding * 2
    tex_h = total_h + padding * 2
    canvas = Image.new("RGBA", (tex_w, tex_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    
    cur_y = padding
    for pl in parsed_lines:
        lh = pl["h"]
        baseline_y = cur_y + int(lh * 0.80)
        for tok in pl["tokens"]:
            tx = padding + tok["x"]
            ty = baseline_y - int(tok["h"] * 0.80)
            tag = tok["tag"]
            txt = tok["text"]
            font = tok["font"]
            
            # Pill Tag
            if "pill" in tag:
                pill_col_name = tag.split(":")[-1] if ":" in tag else "yellow"
                pill_col = parse_color_spec(pill_col_name)
                pw, ph = tok["w"] + 24, tok["h"] + 14
                px, py = tx - 12, ty - 5
                d.rounded_rectangle([px, py, px + pw, py + ph], radius=8, fill=pill_col + (255,))
                pill_txt_col = INK if pill_col_name in ("yellow", "white") else WHITE
                d.text((tx, ty), txt, fill=pill_txt_col + (255,), font=font)
                continue
                
            # Gradient Tags (fire, purple, cyan, etc.)
            if tag in GRADIENT_PRESETS:
                grad_tile = draw_gradient_text(txt, gradient=tag, font_size=font.size, font_style=tok["style"], shadow=False, bevel_highlight=True, padding=0)
                canvas.paste(grad_tile, (tx, ty), grad_tile)
                continue
                
            # Color Tag
            color = parse_color_spec(tag)
            d.text((tx, ty), txt, fill=color + (255,), font=font)
            
        cur_y += int(lh * line_spacing)
        
    if shadow:
        res, _ = natural_shadow_under(canvas, off=(6, 12), blur=14, strength=0.34)
        return res
    return canvas

def draw_pinned_gradient_card(
    gradient_text: str = "FREE",
    gradient_preset: str = "fire",
    subtitle: str = "",
    card_angle: float = -2.5,
    font_size: int = 76,
    width: int = 720,
    height: int = 440
) -> Image.Image:
    """Renders an angled pinned card with fiery gradient headline, contextual badge, and pushpin."""
    pad = 80
    cw = width + pad * 2
    ch = height + pad * 2
    
    # 1. Base Paper Card
    card = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    cd = ImageDraw.Draw(card)
    
    # Subtle inner border line
    cd.rounded_rectangle([10, 10, width - 10, height - 10], radius=16, outline=(230, 225, 215, 255), width=2)
    
    # Clean text: replace underscores with spaces
    clean_text = gradient_text.replace("_", " ").strip()
    
    # Intelligent line splitting for multi-word titles
    if "//" not in clean_text and "\n" not in clean_text:
        words = clean_text.split()
        if len(words) >= 4:
            mid = (len(words) + 1) // 2
            clean_text = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
        elif len(words) == 3 and len(clean_text) > 13:
            clean_text = words[0] + " " + words[1] + "\n" + words[2]
        elif len(words) == 2 and len(clean_text) > 13:
            clean_text = words[0] + "\n" + words[1]
            
    # Auto-fit gradient headline font size to guarantee zero clipping
    avail_w = width - 80
    avail_h = int(height * 0.48)
    cur_fsize = font_size
    grad_tile = None
    
    while cur_fsize >= 24:
        grad_tile = draw_gradient_text(clean_text, gradient=gradient_preset, font_size=cur_fsize, font_style="bold", shadow=False, bevel_highlight=True, padding=0)
        gw, gh = grad_tile.size
        if gw <= avail_w and gh <= avail_h:
            break
        cur_fsize -= 3
        
    gw, gh = grad_tile.size
    
    # Smart contextual subtitle (replaces generic ANIMATION TOOL)
    if not subtitle or subtitle in ("ANIMATION TOOL", "-", "None"):
        upper_txt = clean_text.upper()
        if "3" in upper_txt and "SECOND" in upper_txt:
            subtitle = "STEP 01 // THE 3-SECOND PAUSE"
        elif "TACTICAL" in upper_txt or "LABEL" in upper_txt:
            subtitle = "STEP 02 // TACTICAL LABELING"
        elif "CALIBRATED" in upper_txt or "QUESTION" in upper_txt:
            subtitle = "STEP 03 // CALIBRATED INQUIRY"
        elif "EMOTION" in upper_txt or "NAME" in upper_txt:
            subtitle = "CORE TECHNIQUE // AFFECT LABELING"
        elif "FIRST" in upper_txt or "SHOULD" in upper_txt:
            subtitle = "DE-ESCALATION SCRIPT // SOLVE TOGETHER"
        else:
            subtitle = os.environ.get("CARD_SUBTITLE", "KEY CONCEPT")
            
    # Render Subtitle Pill Badge
    sub_font = resolve_font("bold", 24, text=subtitle)
    s_bbox = cd.textbbox((0, 0), subtitle, font=sub_font)
    sw = s_bbox[2] - s_bbox[0]
    sh = s_bbox[3] - s_bbox[1]
    
    if sw > width - 80:
        sub_font = resolve_font("bold", 20, text=subtitle)
        s_bbox = cd.textbbox((0, 0), subtitle, font=sub_font)
        sw = s_bbox[2] - s_bbox[0]
        sh = s_bbox[3] - s_bbox[1]
        
    # Vertical composition centering
    spacing = 18
    tot_content_h = gh + spacing + sh + 16
    start_y = max(44, int((height - tot_content_h) / 2) + 12)
    
    # Paste gradient headline centered
    gx = int((width - gw) / 2)
    card.paste(grad_tile, (gx, start_y), grad_tile)
    
    # Draw pill badge container for subtitle
    pill_w = sw + 32
    pill_h = sh + 14
    pill_x = int((width - pill_w) / 2)
    pill_y = start_y + gh + spacing
    cd.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=10, fill=(244, 241, 234, 255))
    cd.text((pill_x + 16, pill_y + 4), subtitle, fill=INK + (255,), font=sub_font)
    
    # 2. Pushpin at top center
    pin_r = 16
    pin_x = int(width / 2)
    pin_y = 24
    # Pin shadow
    cd.ellipse([pin_x - pin_r + 4, pin_y - pin_r + 6, pin_x + pin_r + 4, pin_y + pin_r + 6], fill=(0, 0, 0, 70))
    # Pin outer red head
    cd.ellipse([pin_x - pin_r, pin_y - pin_r, pin_x + pin_r, pin_y + pin_r], fill=RED_MARKER + (255,))
    # Pin highlight
    cd.ellipse([pin_x - 7, pin_y - 7, pin_x + 1, pin_y + 1], fill=(255, 140, 140, 255))
    
    # 3. Rotate Card with Lanczos
    rot_card = card.rotate(card_angle, resample=Image.BICUBIC, expand=True)
    rw, rh = rot_card.size
    
    # 4. Natural two-tier shadow (v3: canvas padded for the full blur tail -> no hard cut edge)
    final, _ = natural_shadow_under(rot_card, off=(12, 24), blur=26, strength=0.30)
    return final

def generate_procedural_background(
    style: str = "dot_grid",
    theme: str = "paper",
    width: int = 1920,
    height: int = 1080
) -> Image.Image:
    """Generates agency-grade technical backgrounds (dot grid, graph paper, blueprint)."""
    if theme in ("noir", "night", "dark"):
        bg_col = (15, 18, 28)
        grid_col = (40, 46, 62)
        dot_col = (55, 62, 82)
    elif theme == "blueprint":
        bg_col = (11, 20, 38)
        grid_col = (25, 45, 80)
        dot_col = (45, 85, 145)
    else:  # paper
        bg_col = PAPER
        grid_col = (226, 222, 210)
        dot_col = (202, 196, 180)
        
    im = Image.new("RGBA", (width, height), bg_col + (255,))
    d = ImageDraw.Draw(im)
    
    # 1. Subtle Paper Fiber Texture
    rng = np.random.default_rng(42)
    fib = rng.normal(0, 2.2, (height // 4, width // 4)).repeat(4, 0).repeat(4, 1)
    base_arr = np.array(im, dtype=np.float32)
    base_arr[..., :3] = np.clip(base_arr[..., :3] + fib[..., None], 0, 255)
    im = Image.fromarray(base_arr.astype(np.uint8), mode="RGBA")
    d = ImageDraw.Draw(im)
    
    # 2. Pattern Overlay
    if style in ("dot_grid", "dots"):
        step = 40
        dot_r = 1.5
        for x in range(step // 2, width, step):
            for y in range(step // 2, height, step):
                d.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill=dot_col + (255,))
                
    elif style in ("graph", "grid", "blueprint"):
        step = 40
        for x in range(0, width, step):
            lw = 2 if x % (step * 5) == 0 else 1
            col = grid_col if lw == 1 else (grid_col[0] - 20, grid_col[1] - 20, grid_col[2] - 20)
            d.line([x, 0, x, height], fill=col + (255,), width=lw)
        for y in range(0, height, step):
            lw = 2 if y % (step * 5) == 0 else 1
            col = grid_col if lw == 1 else (grid_col[0] - 20, grid_col[1] - 20, grid_col[2] - 20)
            d.line([0, y, width, y], fill=col + (255,), width=lw)
            
        # Add technical registration crosses in 4 corners
        margin = 60
        cross_r = 10
        for cx, cy in [(margin, margin), (width - margin, margin), (margin, height - margin), (width - margin, height - margin)]:
            d.line([cx - cross_r, cy, cx + cross_r, cy], fill=grid_col + (255,), width=2)
            d.line([cx, cy - cross_r, cx, cy + cross_r], fill=grid_col + (255,), width=2)
            
    return im

def draw_highlighter_text(
    lines: list,
    highlight_indices: list,
    font_size: int = 56,
    highlight_color=YELLOW_HIGHLIGHT,
    text_color=INK,
    padding: int = 40
) -> Image.Image:
    """Draws multi-line text where designated words have vibrant marker highlighter boxes behind them."""
    font = resolve_font("bold", font_size, text=" ".join(lines))
    dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    d_dummy = ImageDraw.Draw(dummy)
    
    line_metrics = []
    max_w = 0
    total_h = padding * 2
    
    for l_idx, line in enumerate(lines):
        words = line.split()
        words_data = []
        cur_x = 0
        line_h = 0
        for w_idx, w in enumerate(words):
            bbox = d_dummy.textbbox((0, 0), w, font=font)
            ww = bbox[2] - bbox[0]
            wh = bbox[3] - bbox[1]
            line_h = max(line_h, wh)
            is_hl = (l_idx, w_idx) in highlight_indices or (l_idx, -1) in highlight_indices
            words_data.append({"word": w, "x": cur_x, "w": ww, "h": wh, "highlight": is_hl})
            cur_x += ww + int(font_size * 0.28)
        max_w = max(max_w, cur_x)
        line_metrics.append({"words": words_data, "w": cur_x, "h": line_h})
        total_h += int(line_h * 1.35)

    img_w = max_w + padding * 2
    im = Image.new("RGBA", (img_w, total_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    y = padding
    for lm in line_metrics:
        lh = lm["h"]
        for wd in lm["words"]:
            wx = padding + wd["x"]
            ww = wd["w"]
            if wd["highlight"]:
                pad_x = 8
                pad_y = 6
                hl_box = [wx - pad_x, y - pad_y, wx + ww + pad_x, y + lh + pad_y]
                d.rounded_rectangle(hl_box, radius=8, fill=highlight_color + (250,))
            d.text((wx, y), wd["word"], fill=text_color + (255,), font=font)
        y += int(lh * 1.35)
        
    return im

def draw_doodle_annotated_text(
    text: str,
    circle_word: str = "",
    underline_word: str = "",
    font_size: int = 64,
    marker_color=RED_MARKER
) -> Image.Image:
    """Draws typography with hand-drawn marker loop around a word and underline."""
    font = resolve_font("bold", font_size, text=text)
    dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    d_dummy = ImageDraw.Draw(dummy)
    
    words = text.split()
    words_data = []
    cur_x = 50
    line_h = 0
    for w in words:
        clean_w = w.strip(".,!?")
        bbox = d_dummy.textbbox((0, 0), w, font=font)
        ww = bbox[2] - bbox[0]
        wh = bbox[3] - bbox[1]
        line_h = max(line_h, wh)
        words_data.append({"word": w, "clean": clean_w, "x": cur_x, "w": ww, "h": wh})
        cur_x += ww + int(font_size * 0.25)
        
    img_w = cur_x + 60
    img_h = line_h + 100
    im = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    text_y = 40
    for wd in words_data:
        d.text((wd["x"], text_y), wd["word"], fill=INK + (255,), font=font)
        
        if circle_word and circle_word.lower() in wd["clean"].lower():
            cx = wd["x"] + wd["w"] / 2
            cy = text_y + wd["h"] / 2
            rx = wd["w"] / 2 + 18
            ry = wd["h"] / 2 + 14
            d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=marker_color + (240,), width=4)
            d.ellipse([cx - rx - 2, cy - ry + 1, cx + rx + 3, cy + ry - 1], outline=marker_color + (180,), width=2)
            
        if underline_word and underline_word.lower() in wd["clean"].lower():
            ux0 = wd["x"] - 6
            ux1 = wd["x"] + wd["w"] + 8
            uy = text_y + wd["h"] + 10
            d.line([ux0, uy, ux1, uy - 2], fill=marker_color + (250,), width=5)
            d.line([ux0 + 4, uy + 2, ux1 - 4, uy + 1], fill=marker_color + (180,), width=3)
            
    return im

def draw_sticky_note(
    title: str = "Notes",
    bullets: list = None,
    width: int = 420,
    height: int = 440,
    accent_color=GREEN_ACCENT
) -> Image.Image:
    """Draws a tactile yellow paper sticky note with drop shadow and handwritten notes."""
    if bullets is None:
        bullets = ["And ultimately", "I decided on"]
        
    pad = 40
    cw = width + pad * 2
    ch = height + pad * 2
    
    note_im = Image.new("RGBA", (width, height), (255, 248, 175, 255))
    nd = ImageDraw.Draw(note_im)
    nd.rectangle([0, 0, width, 24], fill=(245, 235, 145, 255))
    
    f_title = resolve_font("handwritten", 36, text=title)
    nd.text((30, 45), title, fill=INK + (255,), font=f_title)
    nd.line([30, 90, width - 30, 90], fill=INK_MUTED + (120,), width=2)
    
    f_body = resolve_font("handwritten", 28, text=" ".join(bullets))
    by = 115
    for b in bullets:
        nd.text((30, by), b, fill=INK + (255,), font=f_body)
        by += 44
        
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    note_sh, m = natural_shadow_under(note_im, off=(4, 12), blur=14, strength=0.30)
    extra = max(0, pad - m)                            # keep at least the old `pad` margin around the note
    canvas = Image.new("RGBA", (note_sh.width + 2 * extra, note_sh.height + 2 * extra), (0, 0, 0, 0))
    canvas.alpha_composite(note_sh, (extra, extra))
    return canvas

def draw_step_ladder(
    steps: list,
    card_width: int = 440,
    card_height: int = 68,
    vertical_gap: int = 24,
    horizontal_offset: int = 60,
    pill_color=(255, 255, 255),
    wire_color=ORANGE_FIRE
) -> Image.Image:
    """Draws stepped process cards connected by curved connector wires (Ref 1)."""
    n = len(steps)
    total_w = card_width + (n - 1) * horizontal_offset + 120
    total_h = n * card_height + (n - 1) * vertical_gap + 100
    
    im = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    
    all_step_texts = " ".join(s.get("text", "") if isinstance(s, dict) else str(s) for s in steps)
    f_step = resolve_font("bold", 24, text=all_step_texts)
    card_centers = []
    
    for i, s_data in enumerate(steps):
        cx0 = 50 + i * horizontal_offset
        cy0 = 50 + i * (card_height + vertical_gap)
        cx1 = cx0 + card_width
        cy1 = cy0 + card_height
        
        # Soft shadow
        d.rounded_rectangle([cx0 + 2, cy0 + 6, cx1 + 2, cy1 + 6], radius=card_height // 2, fill=(0, 0, 0, 45))
        d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=card_height // 2, fill=pill_color + (255,), outline=(230, 226, 215, 255), width=2)
        
        # Badge circle
        badge_r = 18
        bx = cx0 + 28
        by = cy0 + card_height // 2
        d.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=wire_color + (255,))
        d.text((bx - 6, by - 12), str(i + 1), fill=(255, 255, 255, 255), font=f_step)
        
        # Text
        txt = s_data.get("text", f"Step {i+1}")
        d.text((bx + 32, cy0 + 19), txt, fill=INK + (255,), font=f_step)
        
        card_centers.append((cx1, cy0 + card_height // 2, cx0, cy0 + card_height // 2))
        
    # Draw curved wire connecting step i to step i+1
    for i in range(n - 1):
        x_start, y_start = card_centers[i][0] - 20, card_centers[i][1]
        x_end, y_end = card_centers[i + 1][2] + 20, card_centers[i + 1][3]
        pts = []
        for step in range(30):
            p = step / 29.0
            x = (1 - p) ** 2 * x_start + 2 * (1 - p) * p * (x_start + 40) + p ** 2 * x_end
            y = (1 - p) ** 2 * y_start + 2 * (1 - p) * p * (y_start + 20) + p ** 2 * y_end
            pts.append((x, y))
        d.line(pts, fill=wire_color + (220,), width=3)
        
    return im

def draw_radiate_burst(size: int = 120, color=INK, num_ticks: int = 8) -> Image.Image:
    """Draws kinetic radiating action burst ticks."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = size / 2, size / 2
    r_in = size * 0.22
    r_out = size * 0.44
    for i in range(num_ticks):
        angle = i * (2 * math.pi / num_ticks)
        x0 = cx + r_in * math.cos(angle)
        y0 = cy + r_in * math.sin(angle)
        x1 = cx + r_out * math.cos(angle)
        y1 = cy + r_out * math.sin(angle)
        d.line([x0, y0, x1, y1], fill=color + (240,), width=3)
    return im

def composite_asset_typography_duet(
    asset_img: Image.Image,
    badge_text: str = "01 // DIRECTION",
    headline_spec: str = "You've got the {red}ideas{/red} and {red}content{/red}",
    subtext: str = "Elevate every scene with agency-grade typography and seamless motion.",
    bg_style: str = "dot_grid",
    bg_theme: str = "paper",
    layout: str = "asset_left", # "asset_left", "asset_right", "perched"
    gradient_headline: str = "",
    burst: bool = False,
    width: int = 1920,
    height: int = 1080
) -> Image.Image:
    """Assembles an agency-grade Asset + Typography Duet composite frame directly matching reference styles."""
    # 1. Base procedural background
    frame = generate_procedural_background(style=bg_style, theme=bg_theme, width=width, height=height)
    
    # 2. Responsive Geometry Detection (16:9 Desktop vs 9:16 Vertical Mobile)
    is_vertical = (height > width)
    aw, ah = asset_img.size
    
    if is_vertical:
        # MOBILE VERTICAL SAFE ZONES (9:16 - e.g. 1080x1920)
        # Guarantees margin clearance: Top 180px, Bottom 320px, Right 140px, Left 60px
        safe_left = 60
        safe_right = 140
        safe_top = 180
        safe_bottom = 320
        safe_w = width - safe_left - safe_right
        
        target_ah = int(height * 0.32)
        scale = target_ah / float(max(1, ah))
        target_aw = int(aw * scale)
        asset_scaled = asset_img.resize((target_aw, target_ah), Image.LANCZOS)
        
        if layout == "perched":
            asset_scaled = asset_img.resize((int(target_aw * 0.75), int(target_ah * 0.75)), Image.LANCZOS)
            target_aw, target_ah = asset_scaled.size
            asset_x = safe_left + int(safe_w * 0.52)
            asset_y = safe_top + int(height * 0.14)
            text_x = safe_left
            text_w_limit = safe_w
            cur_y = asset_y + int(target_ah * 0.70)
        else:
            asset_x = safe_left + max(0, int((safe_w - target_aw) / 2))
            asset_y = safe_top + 30
            text_x = safe_left
            text_w_limit = safe_w
            cur_y = asset_y + target_ah + 35
            
        hl_font_size = 54
        sub_font_size = 28
    else:
        # DESKTOP WIDESCREEN (16:9 - e.g. 1920x1080)
        target_ah = int(height * 0.60)
        scale = target_ah / float(max(1, ah))
        target_aw = int(aw * scale)
        asset_scaled = asset_img.resize((target_aw, target_ah), Image.LANCZOS)
        
        if layout == "asset_left":
            asset_x = int(width * 0.14)
            asset_y = int((height - target_ah) / 2)
            text_x = int(width * 0.48)
            text_w_limit = int(width * 0.46)
            cur_y = int(height * 0.28)
        elif layout == "perched":
            text_x = int(width * 0.18)
            text_w_limit = int(width * 0.65)
            asset_scaled = asset_img.resize((int(target_aw * 0.70), int(target_ah * 0.70)), Image.LANCZOS)
            target_aw, target_ah = asset_scaled.size
            asset_x = int(width * 0.56)
            asset_y = int(height * 0.22)
            cur_y = int(height * 0.38)
        else:  # asset_right
            asset_x = int(width * 0.86 - target_aw)
            asset_y = int((height - target_ah) / 2)
            text_x = int(width * 0.10)
            text_w_limit = int(width * 0.46)
            cur_y = int(height * 0.28)
            
        hl_font_size = 72 if gradient_headline else 68
        sub_font_size = 30
        
    # 3. Natural Contour Shadow under asset (0px 8px 16px rgba(0, 0, 0, 0.14))
    alpha_mask = asset_scaled.split()[-1] if asset_scaled.mode == "RGBA" else Image.new("L", asset_scaled.size, 255)
    _m = 16 * 3 + 20
    shadow = Image.new("RGBA", (target_aw + 2 * _m, target_ah + 2 * _m), (26, 20, 16, 0))
    _sa = Image.new("L", shadow.size, 0)
    _sa.paste(alpha_mask.point(lambda p: int(p * 0.14)), (_m, _m + 8))
    shadow.putalpha(_sa.filter(ImageFilter.GaussianBlur(16)))
    frame.paste(shadow, (asset_x - _m, asset_y - _m), shadow)
    
    # 4. Typographic Stack
    d = ImageDraw.Draw(frame)
    
    # Badge Pill (e.g. "01 // DIRECTION" or "NEW FEATURE")
    if badge_text:
        font_badge = resolve_font("mono", 20 if is_vertical else 22, text=badge_text)
        bbox = d.textbbox((0, 0), badge_text, font=font_badge)
        bw = bbox[2] - bbox[0] + 28
        bh = bbox[3] - bbox[1] + 16
        pill_fill = BLUE_BRAND if bg_theme == "paper" else (30, 58, 138)
        d.rounded_rectangle([text_x, cur_y, text_x + bw, cur_y + bh], radius=6, fill=pill_fill + (255,))
        d.text((text_x + 14, cur_y + 8), badge_text, fill=(255, 255, 255, 255), font=font_badge)
        cur_y += bh + (18 if is_vertical else 24)
        
    # Headline (Gradient or Mix-Match)
    if gradient_headline:
        hl_im = draw_gradient_text(headline_spec, gradient=gradient_headline, font_size=hl_font_size, font_style="serif" if "serif" in gradient_headline else "bold", shadow=True)
    else:
        hl_im = draw_mix_match_text(headline_spec, base_font_size=hl_font_size, base_style="bold", shadow=True)
        
    frame.paste(hl_im, (text_x - 20, cur_y - 20), hl_im)
    cur_y += hl_im.height + 8
    
    # Subtext (clean, readable editorial)
    if subtext:
        font_sub = resolve_font("bold", sub_font_size, text=subtext)
        sub_col = (80, 75, 70, 240) if bg_theme == "paper" else (190, 195, 210, 240)
        words = subtext.split()
        sub_lines = []
        cur_line = []
        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = d.textbbox((0, 0), test_line, font=font_sub)
            if bbox[2] - bbox[0] > text_w_limit:
                sub_lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            sub_lines.append(" ".join(cur_line))
            
        for sl in sub_lines:
            d.text((text_x, cur_y), sl, fill=sub_col, font=font_sub)
            cur_y += int(sub_font_size * 1.35)
            
    # 5. Paste Asset (on top of background or overlapping headline in perched mode)
    frame.paste(asset_scaled, (asset_x, asset_y), asset_scaled)
    
    # Radiate burst ticks near the top of the asset (only if requested, max 2 in video)
    if burst:
        burst_img = draw_radiate_burst(size=120 if is_vertical else 130, color=INK if bg_theme == "paper" else CYAN_ELECTRIC)
        frame.paste(burst_img, (asset_x + target_aw - 35, asset_y + 30), burst_img)
    
    return frame

