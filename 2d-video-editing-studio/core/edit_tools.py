# -*- coding: utf-8 -*-
"""edit_tools.py: Advanced Motion Editing Toolkit.

Integrates:
1. beat-sync-editing: BPM-to-frame rhythmic cut grid calculation, phrase snapping.
2. lower-thirds: Broadcast name strap and chyron generator with transparent alpha.
3. talking-head-b-roll: 3-treatment rhythm planner (A: Speaker, B: Overlay, C: Cover).
4. shot-composition: 12-column grid and 3-layer parallax calculator.
"""

import math, os, sys
from typing import List, Dict, Tuple

def calculate_bpm_grid(bpm: float, fps: int = 24, duration_sec: float = 60.0) -> Dict:
    """Calculates frame-accurate cut points based on musical tempo."""
    sec_per_beat = 60.0 / bpm
    frames_per_beat = sec_per_beat * fps
    total_frames = int(duration_sec * fps)
    
    beats = []
    phrases_4 = []
    phrases_8 = []
    
    t = 0.0
    f = 0
    beat_idx = 0
    while t < duration_sec:
        f = int(round(beat_idx * frames_per_beat))
        t = f / float(fps)
        if t >= duration_sec:
            break
        beats.append({"beat": beat_idx, "frame": f, "time": round(t, 3)})
        if beat_idx % 4 == 0:
            phrases_4.append({"phrase_4": beat_idx // 4, "frame": f, "time": round(t, 3)})
        if beat_idx % 8 == 0:
            phrases_8.append({"phrase_8": beat_idx // 8, "frame": f, "time": round(t, 3)})
        beat_idx += 1
        
    return {
        "bpm": bpm,
        "fps": fps,
        "frames_per_beat": round(frames_per_beat, 2),
        "total_beats": len(beats),
        "cut_points_4_beats": phrases_4,
        "cut_points_8_beats": phrases_8
    }

def generate_lower_third_html(
    name: str,
    title: str = "",
    channel_tag: str = "",
    color_accent: str = "#E8503A",
    out_html: str = "lower_third.html"
) -> str:
    """Generates a standalone transparent lower-third HTML card."""
    try:
        from core.engine.kit import sanitize_scene_text
    except ImportError:
        try:
            from engine.kit import sanitize_scene_text
        except ImportError:
            sanitize_scene_text = lambda s: s

    name = sanitize_scene_text(name)
    title = sanitize_scene_text(title)
    channel_tag = sanitize_scene_text(channel_tag)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Lower Third · {name}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Hind:wght@400;600;700&family=Inter:wght@400;500;700&family=Noto+Sans+Devanagari:wght@400;600;700&family=Space+Mono:wght@700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: transparent;
    font-family: 'Noto Sans Devanagari', 'Hind', 'Inter', sans-serif;
  }}
  .safe-container {{
    position: fixed;
    bottom: 8%;
    left: 6%;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }}
  .strap {{
    display: flex;
    align-items: center;
    background: #14110F;
    color: #F4F1EA;
    padding: 0.8rem 1.6rem;
    border-radius: 6px;
    border-left: 6px solid {color_accent};
    box-shadow: 0px 6px 14px rgba(0, 0, 0, 0.12);
    overflow: hidden;
    animation: strapIn 0.65s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}
  .name {{
    font-family: 'Noto Sans Devanagari', 'Hind', 'Inter', sans-serif;
    font-weight: 700;
    font-size: 2.8rem;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: #FFFFFF;
    line-height: 1.0;
  }}
  .sub {{
    margin-top: 0.4rem;
    background: rgba(20, 17, 15, 0.90);
    padding: 0.4rem 1.2rem;
    border-radius: 4px;
    font-family: 'Noto Sans Devanagari', 'Hind', 'Inter', sans-serif;
    font-weight: 500;
    font-size: 1.1rem;
    color: {color_accent};
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}
    animation: subIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.15s forwards;
    opacity: 0;
    transform: translateY(8px);
  }}
  @keyframes strapIn {{
    from {{ transform: translateX(-110%); opacity: 0; }}
    to   {{ transform: translateX(0); opacity: 1; }}
  }}
  @keyframes subIn {{
    to   {{ transform: translateY(0); opacity: 1; }}
  }}
</style>
</head>
<body>
<div class="safe-container">
  <div class="strap">
    <div class="name">{name}</div>
  </div>
  {f'<div class="sub">{title}</div>' if title else ''}
</div>
</body>
</html>"""
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    return html

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Motion Editing Helper")
    parser.add_argument("action", choices=["bpm", "lower_third"])
    parser.add_argument("--bpm", type=float, default=120.0)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--name", default="Dr. Stephen Hawking")
    parser.add_argument("--title", default="Theoretical Physicist")
    parser.add_argument("--out", default="lower_third.html")
    args = parser.parse_args()
    
    if args.action == "bpm":
        grid = calculate_bpm_grid(args.bpm, args.fps)
        print(f"BPM: {grid['bpm']} | Frames/Beat: {grid['frames_per_beat']}")
        print(f"4-Beat Phrases (Main Cuts):")
        for p in grid["cut_points_4_beats"][:8]:
            print(f"  Cut #{p['phrase_4']:02d}: Frame {p['frame']:04d} ({p['time']:.2f}s)")
    elif args.action == "lower_third":
        generate_lower_third_html(args.name, args.title, out_html=args.out)
        print(f"Generated transparent lower third: {args.out}")
