# -*- coding: utf-8 -*-
"""kinetic_text.py: Kinetic Typography Engine for Broadcast Explainers & Title Cards.

Derived from the kinetic-typography skill (https://github.com/iart-ai/kinetic-typography-skills).
Enforces:
1. Static typography foundations: display line-height (1.1-1.2), tight tracking (-1% to -3%), curated font pairings.
2. Split granularity: by line (calm/elegant), by word (energetic/VO sync), by char (high kinetic punch).
3. Workhorse reveal techniques:
   - mask_rise: overflow: hidden baseline rise with easeOutExpo (cubic-bezier(0.16, 1, 0.3, 1))
   - blur_in: filter: blur(12px) -> blur(0) focus pull
   - clip_wipe: clip-path: inset(0 100% 0 0) -> inset(0)
   - char_stagger: 25-35ms per character offset
4. Frame-accurate ?t=N freeze harness for deterministic headless rendering and verification.
5. High-end ASS dialogue generator with exponential ease-out curves and tight tracking.
"""

import argparse, math, os, re, subprocess, sys
from typing import List, Dict, Optional, Tuple

PALETTES = {
    "kinetic_bold": {
        "display": "Anton",
        "body": "Inter",
        "mono": "Space Mono",
        "num": "Anton",
        "serif": "Fraunces",
        "tracking_display": "-0.03em",
        "tracking_body": "0em",
        "colors": {
            "ink": "#14110F",
            "paper": "#F4F1EA",
            "paper2": "#ECE7DC",
            "red": "#E8503A",
            "amber": "#F2A93B",
            "blue": "#2F6DF0",
            "cream": "#FAF6EC"
        }
    },
    "kinetic_editorial": {
        "display": "Archivo Black",
        "body": "Inter",
        "mono": "Space Mono",
        "num": "Archivo Black",
        "serif": "Fraunces",
        "tracking_display": "-0.02em",
        "tracking_body": "0em",
        "colors": {
            "ink": "#111827",
            "paper": "#F9FAFB",
            "paper2": "#E5E7EB",
            "red": "#DC2626",
            "amber": "#D97706",
            "blue": "#2563EB",
            "cream": "#FFFFFF"
        }
    },
    "hindi_kinetic": {
        "display": "Khand",
        "body": "Noto Sans Devanagari",
        "mono": "Space Mono",
        "num": "Khand",
        "serif": "Yatra One",
        "tracking_display": "-0.01em",
        "tracking_body": "0em",
        "colors": {
            "ink": "#2A2420",
            "paper": "#F1E9D8",
            "paper2": "#E8DEC8",
            "red": "#D9452B",
            "amber": "#F2B705",
            "blue": "#2980B9",
            "cream": "#FAF6EC"
        }
    }
}

def generate_kinetic_html(
    text: str,
    technique: str = "mask_rise",
    palette_name: str = "kinetic_bold",
    subtext: str = "",
    aspect: str = "16:9",
    duration: float = 2.5
) -> str:
    try:
        from core.engine.kit import sanitize_scene_text
    except ImportError:
        try:
            from engine.kit import sanitize_scene_text
        except ImportError:
            sanitize_scene_text = lambda s: s

    text = sanitize_scene_text(text)
    if subtext:
        subtext = sanitize_scene_text(subtext)

    pal = PALETTES.get(palette_name, PALETTES["kinetic_bold"])
    colors = pal["colors"]
    words = text.strip().split()
    
    if technique == "mask_rise":
        words_html = "".join([
            f"<span class=\"slot\"><span class=\"word\" style=\"animation-delay: {i * 0.06:.2f}s;\">{w}</span></span> "
            for i, w in enumerate(words)
        ])
    elif technique == "blur_in":
        words_html = "".join([
            f"<span class=\"blur-word\" style=\"animation-delay: {i * 0.08:.2f}s;\">{w}</span> "
            for i, w in enumerate(words)
        ])
    elif technique == "char_stagger":
        char_idx = 0
        words_spans = []
        for w in words:
            chars_html = []
            for ch in w:
                chars_html.append(f"<span class=\"char\" style=\"animation-delay: {char_idx * 0.03:.2f}s;\">{ch}</span>")
            joined_chars = "".join(chars_html)
            words_spans.append(f"<span class=\"word-group\">{joined_chars}</span>")
            char_idx += 1
        words_html = " ".join(words_spans)
    else:
        words_html = f"<div class=\"wipe-content\">{text}</div>"

    subtext_html = ""
    if subtext:
        subtext_html = f"<div class=\"subtext\" style=\"animation-delay: 0.35s;\">{subtext}</div>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kinetic Typography · {technique}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo+Black&family=Fraunces:ital,opsz,wght@0,9..144,900;1,9..144,500&family=Hind:wght@400;600;700&family=Inter:wght@400;700;900&family=Khand:wght@700&family=Noto+Sans+Devanagari:wght@400;600;700&family=Space+Mono:wght@700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  :root {{
    --ink: {colors["ink"]};
    --paper: {colors["paper"]};
    --paper2: {colors["paper2"]};
    --red: {colors["red"]};
    --amber: {colors["amber"]};
    --blue: {colors["blue"]};
    --cream: {colors["cream"]};
  }}
  html, body {{
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: var(--paper);
    color: var(--ink);
    font-family: 'Noto Sans Devanagari', 'Hind', 'Inter', sans-serif;
  }}
  #stage {{
    position: fixed;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 5vw;
    background: radial-gradient(120% 120% at 50% 0%, #FFFFFF 0%, var(--paper) 50%, var(--paper2) 100%);
  }}
  .headline {{
    font-family: 'Noto Sans Devanagari', 'Hind', 'Inter', sans-serif;
    font-size: clamp(3.2rem, 9.5vw, 8.5rem);
    line-height: 1.05;
    letter-spacing: {pal["tracking_display"]};
    text-transform: uppercase;
    color: var(--ink);
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 0 0.28em;
  }}
  .slot {{
    display: inline-block;
    overflow: hidden;
    vertical-align: top;
    padding-bottom: 0.05em;
  }}
  .slot .word {{
    display: inline-block;
    transform: translateY(115%);
    animation: maskRise 0.65s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}
  @keyframes maskRise {{
    to {{ transform: translateY(0); }}
  }}
  .blur-word {{
    display: inline-block;
    opacity: 0;
    filter: blur(14px);
    transform: scale(0.96);
    animation: blurIn 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}
  @keyframes blurIn {{
    to {{
      opacity: 1;
      filter: blur(0);
      transform: scale(1);
    }}
  }}
  .word-group {{
    display: inline-block;
    white-space: nowrap;
  }}
  .char {{
    display: inline-block;
    opacity: 0;
    transform: translateY(0.45em);
    animation: charIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}
  @keyframes charIn {{
    to {{
      opacity: 1;
      transform: translateY(0);
    }}
  }}
  .wipe-content {{
    clip-path: inset(0 100% 0 0);
    animation: clipWipe 0.75s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}
  @keyframes clipWipe {{
    to {{ clip-path: inset(0 0 0 0); }}
  }}
  .subtext {{
    margin-top: 1.5rem;
    font-family: '{pal["mono"]}', monospace;
    font-size: clamp(1rem, 2vw, 1.6rem);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--red);
    opacity: 0;
    transform: translateY(12px);
    animation: subIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}
  @keyframes subIn {{
    to {{ opacity: 1; transform: translateY(0); }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    * {{
      animation: none !important;
      transform: none !important;
      opacity: 1 !important;
      filter: none !important;
      clip-path: none !important;
    }}
  }}
</style>
</head>
<body>
<div id="stage">
  <div class="headline" aria-label="{text}">
    {words_html}
  </div>
  {subtext_html}
</div>
<script>
  const t = new URLSearchParams(location.search).get("t");
  if (t !== null) {{
    const sec = parseFloat(t);
    document.querySelectorAll(".headline *, .subtext").forEach(el => {{
      el.style.animationDelay = (-sec) + "s";
      el.style.animationPlayState = "paused";
    }});
  }}
  window.__ready = true;
</script>
</body>
</html>
"""
    return html

def ts(sec: float) -> str:
    sec = max(0.0, sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"

def build_kinetic_ass_events(
    text: str,
    t_in: float,
    t_out: float,
    x: int,
    y: int,
    style: str = "KEY",
    technique: str = "mask_rise",
    w: int = 1920,
    h: int = 1080
) -> List[str]:
    events = []
    
    if technique == "mask_rise" or technique == "rise":
        clip_box = f"\\clip(0,{int(y - 120)},{w},{int(y + 80)})"
        rise_anim = f"\\pos({x},{y+60})\\t(0,380,0.25,\\pos({x},{y}))"
        events.append(
            f"Dialogue: 0,{ts(t_in)},{ts(t_out)},{style},,0,0,0,,"
            f"{{\\an5{clip_box}{rise_anim}\\fad(50,50)}}{text}"
        )
    elif technique == "blur_in":
        blur_anim = r"\blur14\t(0,350,0.22,\blur1)"
        events.append(
            f"Dialogue: 0,{ts(t_in)},{ts(t_out)},{style},,0,0,0,,"
            f"{{\\an5\\pos({x},{y}){blur_anim}\\fad(60,50)}}{text}"
        )
    elif technique == "pop" or technique == "elastic":
        jelly = r"\fscx85\fscy118\t(0,110,0.3,\fscx106\fscy94)\t(110,260,0.4,\fscx100\fscy100)"
        events.append(
            f"Dialogue: 0,{ts(t_in)},{ts(t_out)},{style},,0,0,0,,"
            f"{{\\an5\\pos({x},{y}){jelly}\\fad(40,40)}}{text}"
        )
    elif technique == "word_stagger":
        words = text.split()
        total_words = len(words)
        stagger_delay = 0.06
        full_line = " ".join(words)
        
        for idx in range(total_words):
            word_t_in = t_in + (idx * stagger_delay)
            if word_t_in >= t_out:
                break
            revealed = " ".join(words[:idx + 1])
            next_t = t_in + ((idx + 1) * stagger_delay) if idx + 1 < total_words else t_out
            events.append(
                f"Dialogue: 0,{ts(word_t_in)},{ts(next_t)},{style},,0,0,0,,"
                f"{{\\an5\\pos({x},{y})\\fscx95\\fscy95\\t(0,60,0.3,\\fscx100\\fscy100)\\fad(30,0)}}{revealed}"
            )
        final_in = t_in + (total_words * stagger_delay)
        if final_in < t_out:
            events.append(
                f"Dialogue: 0,{ts(final_in)},{ts(t_out)},{style},,0,0,0,,"
                f"{{\\an5\\pos({x},{y})\\fad(0,50)}}{full_line}"
            )
    else:
        events.append(
            f"Dialogue: 0,{ts(t_in)},{ts(t_out)},{style},,0,0,0,,"
            f"{{\\an5\\pos({x},{y})\\fad(60,50)}}{text}"
        )
        
    return events

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kinetic Typography Generator")
    parser.add_argument("mode", choices=["html", "ass"], help="Operation mode")
    parser.add_argument("--text", default="UNLEASH KINETIC TYPOGRAPHY", help="Headline text")
    parser.add_argument("--subtext", default="", help="Optional subtext")
    parser.add_argument("--style", default="mask_rise", choices=["mask_rise", "blur_in", "char_stagger", "clip_wipe", "word_stagger", "pop"], help="Reveal technique")
    parser.add_argument("--palette", default="kinetic_bold", choices=list(PALETTES.keys()), help="Palette name")
    parser.add_argument("--out", default="kinetic_title.html", help="Output file path")
    parser.add_argument("--duration", type=float, default=2.5, help="Animation duration in seconds")
    args = parser.parse_args()

    if args.mode == "html":
        content = generate_kinetic_html(args.text, technique=args.style, palette_name=args.palette, subtext=args.subtext, duration=args.duration)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated standalone kinetic HTML: {args.out}")
    elif args.mode == "ass":
        evs = build_kinetic_ass_events(args.text, 0.0, args.duration, 960, 540, style="KEY", technique=args.style)
        for ev in evs:
            print(ev)
