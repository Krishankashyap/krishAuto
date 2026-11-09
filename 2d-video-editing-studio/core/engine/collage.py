# -*- coding: utf-8 -*-
"""collage.py: the paper-collage toolkit behind the Vox (documentary) and sticker styles.

What the reference videos do that a plain "image in a frame" can't:
  * HALFTONE cut-outs: black-and-white dot-screen prints with ONE spot colour (the Vox signature)
  * torn / hand-cut paper edges with a white fibre rim, soft contact shadows, ground shadows
  * giant numerals or words BEHIND the cut-outs (depth), solid colour blocks, circles, glitch pixels
  * hand-drawn dashed arrows, thread loops and scribbles instead of vector lines
  * real surfaces: cream fibre paper, crumpled white paper, graph paper, kraft, green cutting mat,
    chalkboard -- with a vignette, never a flat fill
  * small UI badges, ransom-note letters, wooden picture frames, textured bar charts
Everything here returns RGBA sprites (or draws onto the RGB canvas) and is deterministic: the same
inputs give the same pixels, so parallel render workers agree frame for frame.
"""
import math, zlib

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

try:
    from . import kit
except (ImportError, ValueError):
    import kit


def rng_for(*key):
    return np.random.default_rng(zlib.crc32("|".join(str(k) for k in key).encode("utf-8")))


def noise(w, h, scale, rng, amp):
    """Smooth noise field (h x w), feature size ~scale px, standard deviation ~amp."""
    sw, sh = max(2, int(w / scale) + 2), max(2, int(h / scale) + 2)
    small = rng.normal(0, 1, (sh, sw)).astype(np.float32)
    big = np.asarray(Image.fromarray(small, mode="F").resize((w, h), Image.BICUBIC), dtype=np.float32)
    return big * amp


# ====================================================================== halftone
def halftone(im, cell=8, angle=45, mode="bw", ink=(22, 22, 24), spot=(245, 190, 50),
             paper=(250, 247, 238), contrast=1.3, auto=True):
    """Dot-screen print of an RGBA image (alpha is kept).
       mode  bw     black dots on paper-white            (classic newspaper cut-out)
             spot   dots in the spot colour on paper     (one-colour print)
             duo    black dots over a pale spot tint     (retro two-colour print)
             retro  the photo's own colours, dot-screened and punched up (sticker look)"""
    im = im.convert("RGBA")
    arr = np.asarray(im).astype(np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3]
    gray = (rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114) / 255.0
    solid = alpha > 128
    if auto and solid.sum() > 100:
        # auto-levels: stretch the subject to the full tonal range and centre its mean, so a dark night
        # photograph and a bright studio shot both print as readable dot screens
        lo, hi = np.percentile(gray[solid], (2, 98))
        if hi - lo > 0.05:
            gray = np.clip((gray - lo) / (hi - lo), 0, 1)
        m = float(np.clip(gray[solid].mean(), 0.06, 0.94))
        gray = gray ** float(np.clip(math.log(0.5) / math.log(m), 0.42, 1.9))
    gray = np.clip((gray - 0.5) * contrast + 0.5, 0, 1)
    g_img = Image.fromarray((gray * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(cell * 0.35))
    gray = np.asarray(g_img).astype(np.float32) / 255.0          # dot size follows tone, not texture
    H, W = gray.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    th = math.radians(angle)
    c, s = math.cos(th), math.sin(th)
    u, v = xx * c + yy * s, -xx * s + yy * c
    du = u - (np.floor(u / cell) + 0.5) * cell
    dv = v - (np.floor(v / cell) + 0.5) * cell
    d = np.hypot(du, dv)
    r = cell * 0.74 * np.sqrt(np.clip(1 - gray, 0, 1))
    dot = np.clip((r - d) * 1.5 + 0.5, 0, 1)[..., None]
    P, K, SP = (np.array(x, np.float32) for x in (paper, ink, spot))
    if mode == "spot":
        out = P * (1 - dot) + SP * dot
    elif mode == "duo":
        light = P * 0.72 + SP * 0.28
        out = light * (1 - dot) + K * dot
    elif mode == "retro":
        boosted = np.asarray(ImageEnhance.Contrast(ImageEnhance.Color(
            Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))).enhance(1.45)).enhance(1.18)).astype(np.float32)
        out = boosted * (1 - 0.58 * dot) + K * (0.12 * dot)
    else:
        out = P * (1 - dot) + K * dot
    res = np.dstack([np.clip(out, 0, 255), alpha]).astype(np.uint8)
    return Image.fromarray(res, "RGBA")


def print_texture(im, seed=1, speck=0.035, mottle=0.10):
    """Letterpress / screen-print feel for flat text sprites: ink pinholes + uneven coverage."""
    rng = rng_for("print", seed, im.size)
    a = np.asarray(im.getchannel("A")).astype(np.float32)
    m = 1.0 - mottle * (0.5 + 0.5 * noise(im.width, im.height, 9, rng, 1.0))
    holes = rng.random(a.shape) < speck
    a = a * m * np.where(holes, 0.45, 1.0)
    out = im.copy()
    out.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
    return out


# ====================================================================== torn paper & frames
def torn_mask(w, h, rough, seed=1):
    """L mask (w x h) of a rectangle whose four edges are hand-torn (random walk inward)."""
    rng = rng_for("torn", seed, w, h)
    S2 = 2
    pts = []

    def walk(n, inset_max):
        off, out = rough * 0.5, []
        for _ in range(n):
            off = float(np.clip(off + rng.normal(0, rough * 0.30), 0, inset_max))
            out.append(off)
        return out

    step = 7
    nx, ny = max(4, w // step), max(4, h // step)
    top, bot = walk(nx, rough * 1.7), walk(nx, rough * 1.7)
    lef, rig = walk(ny, rough * 1.7), walk(ny, rough * 1.7)
    for i in range(nx):
        pts.append((w * i / (nx - 1), top[i]))
    for i in range(ny):
        pts.append((w - rig[i], h * i / (ny - 1)))
    for i in range(nx):
        pts.append((w * (nx - 1 - i) / (nx - 1), h - bot[nx - 1 - i]))
    for i in range(ny):
        pts.append((lef[ny - 1 - i], h * (ny - 1 - i) / (ny - 1)))
    m = Image.new("L", (w * S2, h * S2), 0)
    ImageDraw.Draw(m).polygon([(x * S2, y * S2) for x, y in pts], fill=255)
    return m.resize((w, h), Image.LANCZOS)


def frame_torn(im, S, rough=None, seed=1, tilt=0.0, rim=(251, 248, 240), shadow_a=0.14):
    """Torn-paper print: image with irregular edges on a slightly larger white fibre sheet, soft natural shadow."""
    im = im.convert("RGBA")
    w, h = im.size
    r = rough or max(3.0, 0.011 * max(w, h))
    m = int(r * 1.9) + 3
    cw, ch = w + 2 * m, h + 2 * m
    paper = Image.new("RGBA", (cw, ch), rim + (255,))
    paper.putalpha(torn_mask(cw, ch, r * 1.2, seed))
    inner = Image.new("L", (cw, ch), 0)
    inner.paste(torn_mask(w, h, r * 0.9, seed + 7), (m, m))
    layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    layer.paste(im, (m, m))
    a = np.minimum(np.asarray(layer.getchannel("A")), np.asarray(inner))
    layer.putalpha(Image.fromarray(a))
    paper.alpha_composite(layer)
    if tilt:
        paper = paper.rotate(tilt, expand=True, resample=Image.BICUBIC)
    return kit.shadow(paper, blur=int(14 * S), dy=int(6 * S), alpha=shadow_a)


def frame_flat(im, S, color=(255, 255, 255), outline=True):
    """Flat illustration with crisp clean contour outline and subtle, professional natural shadow."""
    im = im.convert("RGBA")
    if outline and (np.asarray(im.getchannel("A")) < 255).any():
        px = max(2, int(round(0.020 * max(im.size))))
        pad = px + 2
        base = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
        base.paste(im, (pad, pad))
        edge = kit.dilate_alpha(base.getchannel("A"), px)
        out = Image.new("RGBA", base.size, color + (0,))
        out.putalpha(edge)
        out.alpha_composite(base)
        return kit.shadow(out, blur=int(12 * S), dy=int(5 * S), alpha=0.12)
    return kit.shadow(im, blur=int(12 * S), dy=int(5 * S), alpha=0.10)


def add_ground(im, k=0.06):
    """Floor oval shadows completely removed in v3.
    Contour drop shadows are applied directly to the asset silhouette instead."""
    return im


def frame_cutout(im, S, border=0.015, ground=False, color=(255, 255, 255), tilt=0.0, shadow_a=0.12):
    """Scissor-cut sticker: crisp white contour border + subtle, professional natural shadow."""
    px = max(3, int(border * max(im.size)))
    pad = px + 4
    base = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    base.paste(im, (pad, pad))
    edge = kit.dilate_alpha(base.getchannel("A"), px)
    out = Image.new("RGBA", base.size, color + (0,))
    out.putalpha(edge)
    out.alpha_composite(base)
    if tilt:
        out = out.rotate(tilt, expand=True, resample=Image.BICUBIC)
    return kit.shadow(out, blur=int(14 * S), dy=int(6 * S), alpha=shadow_a)


def frame_gilt(img, S):
    """Wooden picture frame with a gold lip (the Einstein portrait)."""
    img = img.convert("RGBA")
    b = max(10, int(max(img.size) * 0.058))
    W, H = img.width + 2 * b, img.height + 2 * b
    fr = Image.new("RGBA", (W, H), (96, 62, 30, 255))
    g = ImageDraw.Draw(fr)
    for i, c in enumerate(((132, 90, 46), (110, 72, 36), (84, 54, 26))):
        g.rectangle([i * b // 6, i * b // 6, W - 1 - i * b // 6, H - 1 - i * b // 6], outline=c, width=max(2, b // 7))
    g.rectangle([b - 5, b - 5, W - b + 4, H - b + 4], outline=(198, 158, 78), width=max(2, b // 9))
    fr.paste(img, (b, b))
    inner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(inner).rectangle([b, b, W - b, H - b], outline=(0, 0, 0, 90), width=4)
    fr.alpha_composite(inner.filter(ImageFilter.GaussianBlur(3)))
    return kit.shadow(fr, blur=int(16 * S), dy=int(12 * S), alpha=0.55)


# ====================================================================== surfaces
def _vignette(img, W, H, strength, tint=(1.0, 0.95, 0.88)):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    v = (np.clip((r - 0.30) / 0.95, 0, 1) ** 1.8) * strength
    img *= (1 - v)[..., None]
    img *= 1 - (v * 1.1)[..., None] * (1 - np.array(tint, np.float32))
    return img


def _grid(img, W, H, step, alpha=0.16, major=5, line=(110, 100, 86), lw=1):
    for k, x in enumerate(range(0, W, step)):
        a = alpha * (1.9 if major and k % major == 0 else 1.0)
        img[:, x:x + lw] = img[:, x:x + lw] * (1 - a) + np.array(line, np.float32) * a
    for k, y in enumerate(range(0, H, step)):
        a = alpha * (1.9 if major and k % major == 0 else 1.0)
        img[y:y + lw, :] = img[y:y + lw, :] * (1 - a) + np.array(line, np.float32) * a
    return img


def background(kind, W, H, look):
    rng = rng_for("bg", kind, W, H)
    base = np.array(look["bg"], np.float32)
    S = min(W, H) / 1080
    if kind == "paper":                               # cream fibre paper
        img = np.ones((H, W, 3), np.float32) * base
        img += (noise(W, H, 2.2, rng, 2.4) + noise(W, H, 70, rng, 3.2))[..., None]
        if look.get("dots"):
            step = int(min(W, H) / 18)
            rr = max(2, step // 16)
            yy, xx = np.mgrid[0:H, 0:W]
            m = (((xx + step // 2) % step) < rr) & (((yy + step // 2) % step) < rr)
            img = img - m[..., None] * 24
        img = _vignette(img, W, H, look.get("vig", 0.12), tuple(look.get("vig_tint", (1.0, 0.95, 0.88))))
    elif kind == "grid":                              # graph paper
        img = np.ones((H, W, 3), np.float32) * base
        img += (noise(W, H, 2.2, rng, 2.4) + noise(W, H, 70, rng, 3.0))[..., None]
        img = _grid(img, W, H, max(24, int(48 * S)), alpha=0.13, major=0, line=(120, 112, 98), lw=max(1, int(S)))
        img = _vignette(img, W, H, look.get("vig", 0.12))
    elif kind in ("white", "crumple"):                # crumpled white paper (soft creases)
        base = np.array(look.get("crumple_base", (247, 246, 242)), np.float32)
        n = noise(W, H, 110, rng, 1.0) + 0.6 * noise(W, H, 42, rng, 1.0) + 0.3 * noise(W, H, 16, rng, 1.0)
        gy, gx = np.gradient(n)
        light = np.clip((gx + gy) * 90, -3.5, 3.5)         # barely-there folds: paper, not plaster
        img = base + light[..., None] + (noise(W, H, 2.0, rng, 1.5))[..., None]
        img = _vignette(img, W, H, look.get("vig", 0.05), (1.0, 0.99, 0.97))
    elif kind == "kraft":                             # warm tan paper with a soft light pool
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        t = (yy / H)[..., None]
        img = (np.array((226, 200, 164), np.float32) * (1 - t) + np.array((198, 168, 130), np.float32) * t)
        r = np.hypot((xx - 0.72 * W) / (0.55 * W), (yy - 0.20 * H) / (0.60 * H))
        img += (np.exp(-r * r * 1.4) * 26)[..., None]
        streak = np.asarray(Image.fromarray(rng.normal(0, 1, (H // 3 + 1, max(2, W // 70))).astype(np.float32), mode="F")
                            .resize((W, H), Image.BICUBIC), dtype=np.float32)
        img += (streak * 3.2 + noise(W, H, 2.2, rng, 2.0))[..., None]
        img = _vignette(img, W, H, 0.16, (1.0, 0.93, 0.84))
    elif kind == "mat":                               # green self-healing cutting mat
        img = np.ones((H, W, 3), np.float32) * np.array((52, 116, 68), np.float32)
        img += (noise(W, H, 2.0, rng, 2.4) + noise(W, H, 90, rng, 3.0))[..., None]
        img = _grid(img, W, H, max(20, int(W / 40)), alpha=0.20, major=5, line=(236, 244, 230), lw=max(1, int(S)))
        img = _vignette(img, W, H, 0.30, (0.95, 1.0, 0.95))
    elif kind == "chalk":                             # chalkboard with faint hand-written physics
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        t = (yy / H)[..., None]
        img = (np.array((40, 56, 50), np.float32) * (1 - t) + np.array((26, 38, 35), np.float32) * t)
        r = np.hypot((xx - 0.45 * W) / (0.7 * W), (yy - 0.4 * H) / (0.7 * H))
        img += (np.exp(-r * r * 1.6) * 22)[..., None]
        img += (noise(W, H, 2.0, rng, 3.0) + noise(W, H, 40, rng, 2.2))[..., None]
        base_im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
        ov = Image.new("RGBA", base_im.size, (0, 0, 0, 0))
        g = ImageDraw.Draw(ov)
        formulas = ["E = mc^2", "F = ma", "a^2 + b^2 = c^2", "v = d / t", "PV = nRT", "sin^2 + cos^2 = 1",
                    "dx/dt", "p = mv", "e^(i*pi) + 1 = 0", "x = (-b +- sqrt(b^2-4ac)) / 2a", "G m1 m2 / r^2"]
        for i in range(26):
            f = kit.font("hand", rng.uniform(34, 70) * S, "x")
            g.text((rng.uniform(0.02, 0.88) * W, rng.uniform(0.03, 0.9) * H), formulas[i % len(formulas)], font=f,
                   fill=(235, 238, 230, int(rng.uniform(16, 38))))
        for i in range(7):                             # chalk doodles: waves, circles
            cx, cy = rng.uniform(0.05, 0.9) * W, rng.uniform(0.05, 0.9) * H
            if i % 2:
                g.ellipse([cx, cy, cx + rng.uniform(80, 200) * S, cy + rng.uniform(80, 200) * S],
                          outline=(235, 238, 230, 26), width=max(2, int(3 * S)))
            else:
                pts = [(cx + k * 9 * S, cy + math.sin(k * 0.45) * 34 * S) for k in range(34)]
                g.line(pts, fill=(235, 238, 230, 26), width=max(2, int(3 * S)))
        base_im.alpha_composite(ov.filter(ImageFilter.GaussianBlur(0.8)))
        img = np.asarray(base_im.convert("RGB")).astype(np.float32)
        img = _vignette(img, W, H, 0.34, (0.92, 1.0, 0.96))
    else:
        raise ValueError(kind)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


KINDS = ("paper", "grid", "white", "crumple", "kraft", "mat", "chalk")


# ====================================================================== hand-drawn lines
def hand_path(p0, p1, bend=0.22, seed=1, n=56, wobble=0.006):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    cx, cy = (x0 + x1) / 2 + nx * bend * L, (y0 + y1) / 2 + ny * bend * L
    rng = rng_for("hand", seed)
    wob = np.convolve(rng.normal(0, 1, n + 8), np.ones(5) / 5, "same")[4:n + 5]
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1
        k = wob[i] * L * wobble * math.sin(math.pi * t)
        pts.append((x + nx * k, y + ny * k))
    return pts


def loops_path(p0, p1, loops=3, seed=1, n=220, size=1.0):
    """Looping thread (prolate cycloid) from p0 to p1, like the pen loops in the hands collage."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    ang = math.atan2(y1 - y0, x1 - x0)
    th = np.linspace(0, 2 * math.pi * loops, n)
    R = L / (2 * math.pi * loops)
    d = R * (1.7 + 0.5 * size)
    xs, ys = R * th - d * np.sin(th), d - d * np.cos(th)
    xs = xs * (L / max(xs[-1], 1e-6))
    c, s = math.cos(ang), math.sin(ang)
    return [(x0 + x * c - y * s, y0 + x * s + y * c) for x, y in zip(xs, ys)]


def resample(pts, step=3.0):
    """Polyline -> points spaced `step` px apart along its length."""
    out, carry = [pts[0]], 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        d = step - carry
        while d <= L:
            out.append((a[0] + (b[0] - a[0]) * d / L, a[1] + (b[1] - a[1]) * d / L))
            d += step
        carry = L - (d - step)
    return out


def draw_dashed(cv, pts, p, color, width, dash, gap):
    """Draw the first fraction p of a polyline as hand-drawn dashes (dash/gap in px)."""
    step = 3.0
    rp = resample(pts, step)
    n = int(len(rp) * kit.clamp(p))
    g = ImageDraw.Draw(cv)
    period = dash + gap
    for i in range(1, n):
        if (i * step) % period < dash:
            g.line([rp[i - 1], rp[i]], fill=tuple(color), width=width)


def draw_arrowhead(cv, pts, color, width, size):
    (x1, y1), (x0, y0) = pts[-1], pts[max(0, len(pts) - 6)]
    ang = math.atan2(y1 - y0, x1 - x0)
    g = ImageDraw.Draw(cv)
    for da in (math.radians(150), math.radians(-150)):
        g.line([(x1, y1), (x1 + size * math.cos(ang + da), y1 + size * math.sin(ang + da))], fill=tuple(color), width=width)


# ====================================================================== badges, blocks, letters
def badge(icon, d, bg, fg=(255, 255, 255), shape="circle"):
    """Small UI badge (the blue circles on the dark collage, the YouTube/mail chips)."""
    K = 4
    D = int(d * K)
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    if shape == "square":
        g.rounded_rectangle([0, 0, D - 1, D - 1], int(D * 0.24), fill=tuple(bg) + (255,))
    else:
        g.ellipse([0, 0, D - 1, D - 1], fill=tuple(bg) + (255,))
    f = tuple(fg) + (255,)
    c, u = D / 2, D / 100.0
    w = max(2, int(6 * u))
    if icon == "play":
        g.polygon([(c - 14 * u, c - 20 * u), (c - 14 * u, c + 20 * u), (c + 22 * u, c)], fill=f)
    elif icon == "star":
        pts = []
        for i in range(10):
            rr = (26 if i % 2 == 0 else 11) * u
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
        g.polygon(pts, fill=f)
    elif icon == "hash":
        for dx in (-9, 9):
            g.line([(c + dx * u + 4 * u, c - 24 * u), (c + dx * u - 4 * u, c + 24 * u)], fill=f, width=w)
        for dy in (-9, 9):
            g.line([(c - 24 * u, c + dy * u), (c + 24 * u, c + dy * u)], fill=f, width=w)
    elif icon == "check":
        g.line([(c - 22 * u, c + 2 * u), (c - 6 * u, c + 18 * u), (c + 24 * u, c - 18 * u)], fill=f, width=int(8 * u), joint="curve")
    elif icon == "bell":
        g.pieslice([c - 20 * u, c - 26 * u, c + 20 * u, c + 14 * u], 180, 360, fill=f)
        g.polygon([(c - 20 * u, c - 6 * u), (c + 20 * u, c - 6 * u), (c + 26 * u, c + 16 * u), (c - 26 * u, c + 16 * u)], fill=f)
        g.ellipse([c - 6 * u, c + 16 * u, c + 6 * u, c + 28 * u], fill=f)
    elif icon == "mail":
        g.rounded_rectangle([c - 26 * u, c - 17 * u, c + 26 * u, c + 17 * u], int(4 * u), outline=f, width=w)
        g.line([(c - 24 * u, c - 14 * u), (c, c + 4 * u), (c + 24 * u, c - 14 * u)], fill=f, width=w)
    elif icon == "search":
        g.ellipse([c - 22 * u, c - 22 * u, c + 8 * u, c + 8 * u], outline=f, width=int(7 * u))
        g.line([(c + 6 * u, c + 6 * u), (c + 24 * u, c + 24 * u)], fill=f, width=int(8 * u))
    elif icon == "bolt":
        g.polygon([(c + 6 * u, c - 28 * u), (c - 16 * u, c + 4 * u), (c - 1 * u, c + 4 * u), (c - 7 * u, c + 28 * u),
                   (c + 17 * u, c - 6 * u), (c + 2 * u, c - 6 * u)], fill=f)
    elif icon == "arrow":
        g.line([(c - 24 * u, c), (c + 20 * u, c)], fill=f, width=int(8 * u))
        g.polygon([(c + 28 * u, c), (c + 8 * u, c - 17 * u), (c + 8 * u, c + 17 * u)], fill=f)
    elif icon == "plus":
        g.line([(c - 22 * u, c), (c + 22 * u, c)], fill=f, width=int(9 * u))
        g.line([(c, c - 22 * u), (c, c + 22 * u)], fill=f, width=int(9 * u))
    elif icon == "heart":
        g.ellipse([c - 26 * u, c - 24 * u, c + 2 * u, c + 4 * u], fill=f)
        g.ellipse([c - 2 * u, c - 24 * u, c + 26 * u, c + 4 * u], fill=f)
        g.polygon([(c - 25 * u, c - 4 * u), (c + 25 * u, c - 4 * u), (c, c + 28 * u)], fill=f)
    else:
        g.ellipse([c - 14 * u, c - 14 * u, c + 14 * u, c + 14 * u], fill=f)
    return im.resize((int(d), int(d)), Image.LANCZOS)


def block(shape, w, h, color, seed=1, glitch=False, S=1.0):
    """Flat colour block / circle / stripe with a faint paper-print grain; optional glitch pixels."""
    w, h = max(2, int(w)), max(2, int(h))
    rng = rng_for("block", seed, w, h)
    n = (noise(w, h, 3, rng, 3.0) + noise(w, h, 40, rng, 3.0))[..., None]
    arr = np.clip(np.array(color[:3], np.float32) + n, 0, 255).astype(np.uint8)
    im = Image.fromarray(np.dstack([arr, np.full((h, w), 255, np.uint8)]), "RGBA")
    m = Image.new("L", (w, h), 255)
    if shape == "circle":
        m = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(m).ellipse([0, 0, w * 2 - 1, h * 2 - 1], fill=255)
        m = m.resize((w, h), Image.LANCZOS)
    elif shape == "stripe":
        m = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(m).polygon([(int(w * 0.04) * 2, 0), (w * 2, 0), (int(w * 0.96) * 2, h * 2), (0, h * 2)], fill=255)
        m = m.resize((w, h), Image.LANCZOS)
    if glitch:
        px = max(6, int(10 * S))
        g = ImageDraw.Draw(im)
        for gy in range(0, h, px):
            for gx in range(int(w * 0.72), w, px):
                if rng.random() < 0.05 + 0.42 * (gx / w - 0.72):
                    k = int(rng.integers(0, 3))
                    col = [tuple(int(c * 0.88) for c in color[:3]), (250, 248, 240), tuple(min(255, int(c * 1.12)) for c in color[:3])][k]
                    g.rectangle([gx, gy, gx + px, gy + px], fill=col + (255,))
    im.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel("A")), np.asarray(m))))
    return im


def ransom(text, size, look, S, seed=1):
    """Ransom-note letter tiles in mixed fonts, colours and tiny rotations."""
    rng = rng_for("ransom", text, seed)
    dev = bool(kit.DEV.search(text))
    units = text.split(" ") if dev else list(text)           # Devanagari: whole words (never split conjuncts)
    roles = ["serif", "impact", "headline", "display", "vintage"]
    pals = [((20, 20, 22), (250, 248, 240)), ((250, 214, 38), (20, 20, 22)), ((250, 248, 240), (20, 20, 22)),
            (tuple(look["accent"]), (255, 255, 255)), (tuple(look["accent3"]), (255, 255, 255))]
    tiles = []
    for u in units:
        if not u.strip():
            tiles.append(None)
            continue
        sz = size * rng.uniform(0.82, 1.18)
        f = kit.font(roles[int(rng.integers(len(roles)))], sz, u)
        bb = f.getbbox(u)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pad = int(sz * 0.2)
        bg, fg = pals[int(rng.integers(len(pals)))]
        t = Image.new("RGBA", (tw + 2 * pad, th + 2 * pad), bg + (255,))
        ImageDraw.Draw(t).text((pad - bb[0], pad - bb[1]), u, font=f, fill=fg + (255,))
        t = t.rotate(float(rng.uniform(-7, 7)), expand=True, resample=Image.BICUBIC)
        tiles.append(t)
    gap = int(size * 0.35)
    W = sum((t.width if t else gap) for t in tiles) - int(size * 0.05) * len(tiles)
    H = int(max(t.height for t in tiles if t) * 1.3)
    out = Image.new("RGBA", (max(W, 4), H), (0, 0, 0, 0))
    x = 0
    for t in tiles:
        if t is None:
            x += gap
            continue
        out.alpha_composite(t, (max(0, x), int((H - t.height) / 2 + rng.uniform(-0.1, 0.1) * size)))
        x += t.width - int(size * 0.05)
    return kit.shadow(out, blur=int(6 * S), dy=int(5 * S), alpha=0.4)
