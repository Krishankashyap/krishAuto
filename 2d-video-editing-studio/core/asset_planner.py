# -*- coding: utf-8 -*-
"""asset_planner.py: decide HOW MANY images a video needs, of WHAT kind, for WHICH line.

The old planner divided the duration by a constant. A real edit does not work like that:

  * the STYLE decides the density. A Vox collage or a noir documentary changes picture every ~2.5 s and
    needs a dedicated image for most beats; a kinetic-type or stat-card video is mostly typography and
    needs a handful of images. Each style file declares BEAT_S, MIX and MENU (see styles/*.py).
  * the SCRIPT decides where images are NOT needed: a line with a date, a count or a percentage gets a
    text/number beat (giant numeral, counter, chart) instead of a picture.
  * variety is planned, not hoped for: every beat gets a type (scene / asset / reuse / text), scene beats get a
    shot size that never repeats back-to-back, and every image gets an archetype from the style's menu
    (portrait, map, document, tool, symbol, ...) so neighbours are never the same kind of picture.

Output: PLAN.json (machine-readable, used by `studio.py lint`) and PLAN.md (the brief to write SHOTS.json from).

usage:  python studio.py plan [--style noir] [--pace fast|normal|calm|<seconds>]
"""
import argparse, csv, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))
import layouts  # noqa: F401,E402  (registers style layouts before styles are read)
import styles   # noqa: E402

PACE = {"fast": 0.8, "normal": 1.0, "calm": 1.4}          # multipliers on the style's beat length
SIZES = ["wide", "medium", "close", "detail", "medium", "close", "wide", "detail"]
NUM_WORDS = set("""एक दो तीन चार पाँच पांच छह छः सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह पन्द्रह सोलह सत्रह अठारह
उन्नीस बीस तीस चालीस पचास साठ सत्तर अस्सी नब्बे सौ सैकड़ों हज़ार हजार लाख करोड़ करोड़ों प्रतिशत फ़ीसदी""".split())
CLEAN = re.compile(r"[।॥?,.!\"'“”‘’:;—–\-…()\[\]]")


def has_number(text):
    return bool(re.search(r"\d", text)) or any(CLEAN.sub("", w) in NUM_WORDS for w in text.split())


def allocate(durs, total):
    """Beats per line: proportional to duration, with a hard anti-gap guarantee
    (at least 1 visual beat every <= 1.1s, ensuring high-density visual storytelling without dead pauses)."""
    min_counts = [max(1, math.ceil(d / 1.1)) for d in durs]
    raw = [max(float(min_c), d / sum(durs) * total) for d, min_c in zip(durs, min_counts)]
    counts = [int(x) for x in raw]
    remainder = max(0, total - sum(counts))
    if remainder > 0:
        for i in sorted(range(len(raw)), key=lambda i: raw[i] - counts[i], reverse=True)[:remainder]:
            counts[i] += 1
    return counts



def assign_types(counts, lines, mix):
    kinds = [k for k, v in mix.items() if v > 0]
    deficit = {k: 0.0 for k in kinds}
    out = []                                              # list of (line_index, type)
    for li, n in enumerate(counts):
        for j in range(n):
            for k in kinds:
                deficit[k] += mix[k]
            allowed = list(kinds)
            if len(out) < 2 and "reuse" in allowed and len(allowed) > 1:
                allowed.remove("reuse")                    # nothing to re-frame yet
            if len(out) >= 2 and out[-1][1] == out[-2][1] and len(allowed) > 1:
                t = out[-1][1]
                streak = 2
                while streak < len(out) and out[-streak - 1][1] == t:
                    streak += 1
                if not (mix[t] >= 0.55 and streak < 4) and t in allowed:   # a dominant type may run to 4
                    allowed.remove(t)
            pick = max(allowed, key=lambda k: deficit[k])
            deficit[pick] -= 1.0
            out.append((li, pick))
    # a line that states a number / date gets a number beat (counter, giant numeral, chart row) -- but only up to the
    # style's text share (+50% slack), so the number rule can't turn a picture-led style into a text-led one
    if mix.get("text", 0) > 0:
        cap = math.ceil(len(out) * mix["text"] * 1.5)
        have = sum(1 for _, t in out if t == "text")
        spans, pos = [], 0
        for li, n in enumerate(counts):
            spans.append((li, list(range(pos, pos + n))))
            pos += n
        numbered = sorted((x for x in spans if has_number(lines[x[0]]["text"]) and len(x[1]) >= 2
                           and not any(out[i][1] == "text" for i in x[1])),
                          key=lambda x: -sum(1 for w in lines[x[0]]["text"].split() if CLEAN.sub("", w) in NUM_WORDS or re.search(r"\d", w)))
        for li, idx in numbered:
            if have >= cap:
                break
            out[idx[-1]] = (li, "text")
            have += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default=None)
    ap.add_argument("--pace", default="normal", help="fast | normal | calm | seconds per beat")
    a = ap.parse_args()
    if not os.path.exists("VO.tsv"):
        raise SystemExit("plan needs VO.tsv -- run `python studio.py voice` first")
    style = a.style
    for f in ("SHOTS.json", "EDIT.json"):
        if not style and os.path.exists(f):
            style = json.load(open(f, encoding="utf-8")).get("style")
    style = style or "noir"
    plan = styles.plan_for(style)
    lines = list(csv.DictReader(open("VO.tsv", encoding="utf-8"), delimiter="\t"))
    durs = [float(r["end"]) - float(r["start"]) for r in lines]
    dur = float(lines[-1]["end"]) + 1.0
    beat_s = float(a.pace) if re.fullmatch(r"\d+(\.\d+)?", a.pace) else min(1.2, plan["beat_s"] * PACE[a.pace])
    min_total = sum(max(1, math.ceil(d / 1.1)) for d in durs)
    total = max(min_total, math.ceil(dur / beat_s))
    counts = allocate(durs, total)

    typed = assign_types(counts, lines, plan["mix"])
    menu = plan["menu"]
    beats, n_scene, n_asset, last_size = [], 0, 0, None
    for n, (li, t) in enumerate(typed, 1):
        b = {"n": n, "line": lines[li]["id"], "type": t}
        if t == "scene" and menu["scene"]:
            size = SIZES[n_scene % len(SIZES)]
            if size == last_size:
                size = SIZES[(n_scene + 1) % len(SIZES)]
            last_size = size
            b["size"], b["archetype"] = size, menu["scene"][n_scene % len(menu["scene"])]
            n_scene += 1
        elif t == "asset" and menu["asset"]:
            b["archetype"] = menu["asset"][(n_asset * 5 + li) % len(menu["asset"])]       # stride 5: neighbours differ
            n_asset += 1
        elif t in ("scene", "asset"):
            b["type"] = "text"
        if plan.get("accents"):
            b["accent"] = plan["accents"][n % len(plan["accents"])]
        beats.append(b)
    count = {k: sum(1 for b in beats if b["type"] == k) for k in ("scene", "asset", "reuse", "text")}
    images = count["scene"] + count["asset"]
    # Universal Claude Video Director Framework
    act1_end = max(1.0, dur * 0.20)
    act2_end = max(act1_end + 1.0, dur * 0.80)
    sig_beat_time = dur * 0.65

    # Density segments calculation (approx 6-second windows)
    seg_len = 6.0
    n_segs = max(1, math.ceil(dur / seg_len))
    density_rows = []
    for s_idx in range(n_segs):
        t0 = s_idx * seg_len
        t1 = min(dur, (s_idx + 1) * seg_len)
        b_count = sum(1 for b_idx in range(len(beats)) if t0 <= (b_idx * beat_s) < t1)
        density = "HIGH DENSITY (rapid-cut energy)" if b_count >= 4 else ("MEDIUM DENSITY (steady narrative)" if b_count >= 2 else "LOW DENSITY (breathing hold)")
        density_rows.append(f"| {t0:04.1f}s - {t1:04.1f}s | **{density}** | {b_count} visual beat(s) |")

    claude_director = {
        "energy_arc": {
            "act1_hook_end_s": round(act1_end, 1),
            "act2_development_end_s": round(act2_end, 1),
            "signature_hero_beat_s": round(sig_beat_time, 1),
            "act3_resolution_end_s": round(dur, 1)
        },
        "density_segments": n_segs
    }

    json.dump({"style": style, "beat_s": beat_s, "duration": dur, "total_beats": len(beats), "counts": count,
               "images": images, "claude_director": claude_director, "beats": beats},
              open("PLAN.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    gap = float(os.environ.get("FLOW_GUARD_GAP", "1.3"))
    out = [f"# Asset plan — style **{style}** — {dur / 60:.1f} min, {len(lines)} lines", "",
           f"A new visual beat every **{beat_s:.1f} s** → **{len(beats)} beats**. How they are realised:", "",
           "| kind | beats | what it is |", "|---|---|---|",
           f"| **scene** | {count['scene']} | full-frame generated image (wide / medium / close / detail) |",
           f"| **asset** | {count['asset']} | isolated cut-out on magenta (portrait, map, document, prop, ...) |",
           f"| reuse | {count['reuse']} | camera cut / crop of an image you already have: **no new image** |",
           f"| text | {count['text']} | title, number, counter, chart, note: **no image** |", "",
           f"**Images to generate: {images}** (one dedicated prompt each, no two alike).",
           f"Flow time: ~{images * gap / 60:.1f} min to submit at {gap:g} s apart + ~2 min for the last ones to finish.", "",
           "Rules for SHOTS.json: every image shot needs `line`, `cue` (a word spoken in that line), `archetype`, and for "
           "scenes `size`. Run `python studio.py lint` before `prompts`: it rejects duplicates and weak variety.", "",
           "## 🎬 Claude Video Director Blueprint (Universal Production Engine)", "",
           "### 1. Energy Arc (3-Act Narrative Architecture)",
           f"- **Act 1: Attention Hook (00:00 - {act1_end:.1f}s)**: High visual impact, establishes world & emotional stakes immediately. Keep viewer retention peak.",
           f"- **Act 2: Narrative Development & Escalation ({act1_end:.1f}s - {act2_end:.1f}s)**: Deeper evidence, rapid thematic progression. **SIGNATURE HERO VISUAL BEAT** lands around **{sig_beat_time:.1f}s** (maximum visual spectacle/contrast).",
           f"- **Act 3: Climax & Resolution ({act2_end:.1f}s - {dur:.1f}s)**: Emotional/intellectual payoff, decisive closing imagery, energy settles cleanly into final title/callout.", "",
           "### 2. Effects Density & Pacing Map (Contrast Drives Impact)",
           "| Time Window | Density Level | Beats / Technique |",
           "|---|---|---|"] + density_rows + ["",
           "### 3. Director's Motion & Transition Choreography (for `EDIT.json`)",
           "- **Speed Ramps & Zooms**: Use `\"camera\": \"punch_in\"` or `\"zoom_in\"` with Remotion spring physics on key reveals.",
           "- **Transitions**: Connect scenes with directional momentum: `\"transition\": \"whip_left\"`, `\"whip_right\"`, `\"scale_in\"`, or tactile cuts.",
           "- **Emphasis Beats**: At most 2 rubber stamps per video; balance with `seal`, `tape`, `scrawl`, `tab`, or forensic callouts.", "",
           "## Beats per line", "", "| line | sec | beats | plan |", "|---|---|---|---|"]
    byline = {}
    for b in beats:
        byline.setdefault(b["line"], []).append(b)
    for r, d in zip(lines, durs):
        parts = []
        for b in byline.get(r["id"], []):
            s = b["type"]
            if b.get("size"):
                s += f"·{b['size']}"
            if b.get("archetype"):
                s += f"·{b['archetype']}"
            parts.append(s)
        out.append(f"| {r['id']} | {d:.1f} | {len(parts)} | {' ⟶ '.join(parts)} |")
    open("PLAN.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out[:17]))
    print("\nper-line brief: PLAN.md  ·  machine plan: PLAN.json")


if __name__ == "__main__":
    main()
