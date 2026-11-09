#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/stress_test.py -- production stress test for the v3 engine (characters, stages, variety, kickers, stamps).

    python scripts/stress_test.py            builds a throw-away project in a temp folder and runs every edge case:
                                             real pose files with missing poses, two actors + long Hindi bubble,
                                             character in a layout without a cast slot, narrow / opaque / keyed stage
                                             layers, 8 stage scenes (memory LRU), every stamp + kicker design with
                                             Hindi and over-long text, 16:9 + 9:16, determinism across workers,
                                             cache exactness, and a full 1080p multi-worker render with audio sync.
Exit code 1 if anything fails. Run it after changing the engine (takes ~4 min on a phone).
"""
import os, sys, tempfile, shutil, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_tmp = tempfile.mkdtemp(prefix="dstudio_stress_")
subprocess.run([sys.executable, os.path.join(ROOT, "studio.py"), "new", _tmp], check=True, capture_output=True)
os.chdir(_tmp)
import json, traceback, time
sys.path.insert(0, os.path.join(ROOT, "core"))
sys.path.insert(0, os.path.join(ROOT, "core", "engine"))
import selftest as st
import numpy as np
from PIL import Image

P = os.getcwd()
RES = []


def case(name, fn):
    t0 = time.time()
    try:
        msg = fn() or ""
        RES.append((name, True)); print(f"PASS {name:52} {time.time()-t0:5.1f}s {msg}", flush=True)
    except BaseException as e:                       # SystemExit too: a crash in production is a crash here
        RES.append((name, False)); print(f"FAIL {name:52} {type(e).__name__}: {e}", flush=True)
        traceback.print_exc(limit=3)


# ---------------------------------------------------------------- assets
st.make_voice(P, 40.0)
st.make_images(P)
import character
cut = os.path.join(P, "elements", "cut")
# real-ish pose files: different canvas sizes + padding (like keyed Flow output), some poses missing
for k, pose in enumerate(["idle", "talk", "blink", "point", "wow", "think", "happy", "point_talk"]):
    im = character.placeholder_pose(pose.replace("_talk", "") if pose != "point_talk" else "point")
    canvas = Image.new("RGBA", (im.width + 80 + k * 13, im.height + 120 + k * 7), (0, 0, 0, 0))
    canvas.paste(im, (40 + k * 5, 60), im)
    canvas = canvas.resize((int(canvas.width * (0.7 + 0.1 * (k % 3))), int(canvas.height * (0.7 + 0.1 * (k % 3)))))
    canvas.save(os.path.join(cut, f"ravi_{pose}.png"))
# mira: placeholder (no files). ravi: real files without walk poses -> fallback path
raw = os.path.join(P, "elements", "raw")
Image.new("RGB", (900, 500), (120, 180, 235)).save(os.path.join(raw, "sky_small.jpg"))            # narrower than frame
strip = Image.new("RGBA", (1600, 400), (0, 0, 0, 0))
from PIL import ImageDraw
ImageDraw.Draw(strip).polygon([(0, 400), (0, 220), (300, 80), (700, 260), (1100, 60), (1600, 240), (1600, 400)], fill=(90, 120, 160, 255))
strip.save(os.path.join(cut, "hills_strip.png"))
fg = Image.new("RGBA", (800, 300), (0, 0, 0, 0))
ImageDraw.Draw(fg).ellipse([100, 120, 400, 300], fill=(40, 120, 50, 255))
fg.save(os.path.join(cut, "bush_fg.png"))

H = "नेपाल बहुत सुंदर देश है और यहाँ के पहाड़ दुनिया में सबसे ऊँचे हैं, सच में!"


def edit(aspect, style="toon"):
    sc = []
    t = 0.0
    def add(d, dur=2.6):
        nonlocal t
        d["at"] = round(t, 2); sc.append(d); t += dur
    add({"layout": "stage", "items": [{"type": "kicker", "text": "नेपाल // यात्रा", "design": "index"},
        {"type": "character", "cast": "mira"}]})                                            # no actions at all
    add({"layout": "stage", "stage": {"layers": [{"src": "sky_small", "depth": 0.03, "drift": 9},
        {"src": "hills_strip", "depth": 0.3, "h": 0.4}], "fg": [{"src": "bush_fg", "depth": 1.4, "h": 0.25}],
        "particles": "snow", "palette": "night"},
        "items": [{"type": "character", "cast": "ravi", "x": 0.2, "from": "left", "talk": False,
                   "actions": [{"at": t + 0.8, "do": "walk", "to": 1.5}, {"at": t + 1.4, "do": "talk", "until": t + 2.2},
                               {"at": t + 1.6, "do": "point"}]}]}, 3.0)
    add({"layout": "stage", "stage": {"layers": [{"src": "hills_strip", "depth": 0.4}], "particles": "fireflies"},   # no sky given
        "items": [{"type": "character", "cast": "mira", "x": 0.25, "enter": "run_in", "until": t + 2.4, "exit": "run_out",
                   "actions": [{"at": t + 0.9, "do": "say", "text": H}]},
                  {"type": "character", "cast": "ravi", "x": 0.75, "enter": "pop", "slot": "cast",
                   "actions": [{"at": t + 1.0, "do": "react", "pose": "wow"}, {"at": t + 1.5, "do": "nod"}, {"at": t + 1.8, "do": "shake"}]}]})
    add({"layout": "hero", "bg": "bg_a", "items": [{"type": "character", "cast": "ravi", "enter": "fade",
        "actions": [{"at": t + 0.5, "do": "walk", "to": 0.5}, {"at": t + 0.7, "do": "look", "dir": "left"}]}]})  # no cast slot, zero walk
    add({"layout": "presenter", "bg": "paper", "items": [{"type": "kicker", "text": "A VERY LONG CASE FILE TAG #BUR-2018 // DELHI // SANT NAGAR HOUSE 137 // EVIDENCE"},
        {"type": "title", "text": "*104* साल"}, {"type": "asset", "name": "cut_a", "slot": "left"},
        {"type": "character", "cast": "ravi", "enter": "rise", "until": t + 2.2, "exit": "pop",
         "actions": [{"at": t + 0.6, "do": "point", "until": t + 1.6}, {"at": t + 1.0, "do": "hop"}]}]})
    add({"layout": "presenter_l", "bg": "bg_b", "items": [{"type": "character", "cast": "mira", "enter": "none"},
        {"type": "stamp", "text": "रहस्य", "design": "seal"}]})
    for i, (des, txt, col) in enumerate([("rubber", "बंद केस", "#C62828"), ("tape", "NO BREAK-IN AT ALL TONIGHT", [30, 30, 30]),
                                         ("scrawl", "सबसे अहम", "accent"), ("tab", "FILE 2018/BUR", None), ("foo", "UNKNOWN", "red"),
                                         (None, "AUTO ONE", None), (None, "AUTO TWO", None), ("rubber", "OVER BUDGET", None)]):
        d = {"type": "stamp", "text": txt}
        if des: d["design"] = des
        if col is not None: d["color"] = col
        add({"layout": ["hero", "hero_r", "focus", "board", "clean"][i % 5], "bg": ["bg_a", "dark", "paper", "grid"][i % 4],
             "items": [{"type": "kicker", "text": ["CASE FILE", "सवाल", "BIG QUESTION"][i % 3],
                        **({"design": ["bar", "chip", "bracket", "rule", "index"][i % 5], "size": 40 + i * 3} if i % 2 else {})},
                       {"type": "asset", "name": "cut_b"}, d]}, 1.4)
    for i in range(5):                                                                      # many stage scenes (LRU)
        add({"layout": "stage", "transition": "fade", "stage": {"palette": ["day", "dusk", "night"][i % 3], "particles": ["petals", "dust", "none"][i % 3]},
             "items": [{"type": "character", "cast": "mira", "x": 0.3, "actions": [{"at": t + 0.4, "do": "walk", "to": 0.9}]}]}, 1.3)
    add({"layout": "clean", "bg": "bg_a", "items": []}, 1.0)                                # empty scene
    return {"style": style, "aspect": aspect, "scenes": sc, "cast": {"ravi": {"scale": {"wow": 1.05}}}}, t


import render
for aspect in ("16:9", "9:16"):
    e_json, dur = edit(aspect)
    name = f"E_{aspect.replace(':', '')}.json"
    json.dump(e_json, open(name, "w"), ensure_ascii=False, indent=1)

    def chk(name=name):
        e = render.Engine(name, 0.5)
        assert len(e.scenes) == len(json.load(open(name))["scenes"])
        return f"{len(e.scenes)} scenes, {len(e.warnings)} warnings: " + " | ".join(w[:60] for w in e.warnings[:4])
    case(f"[{aspect}] plan/check every edge case", chk)

    def frames(name=name, dur=dur):
        e = render.Engine(name, 0.5)
        bad = []
        n = 0
        for t in np.arange(0.0, dur + 0.5, 1 / 12):
            fr = e.frame(float(t)); n += 1
            if fr.size != (e.W, e.H) or fr.mode != "RGB":
                bad.append(t)
        assert not bad, bad[:5]
        return f"{n} frames drawn at 12 fps across the whole edit (incl. every transition)"
    case(f"[{aspect}] draw every 1/12 s, no crash", frames)

    def determinism(name=name):
        a, b = render.Engine(name, 0.4), render.Engine(name, 0.4)
        ts = [0.5, 3.3, 6.7, 9.1, 12.4, 25.0, 31.0]
        for t in reversed(ts):                       # b renders in a different ORDER (as a different worker would)
            b.frame(t)
        diff = [t for t in ts if not np.array_equal(np.asarray(a.frame(t)), np.asarray(b.frame(t)))]
        assert not diff, f"workers would disagree at {diff}"
        return "two engines, different render order -> identical frames (chunks join seamlessly)"
    case(f"[{aspect}] determinism across workers", determinism)

    def cache_exact(name=name, dur=dur):
        render.Engine.NO_CACHE = False
        fast = render.Engine(name, 0.4)
        render.Engine.NO_CACHE = True
        slow = render.Engine(name, 0.4)
        bad = []
        for t in np.arange(0.1, dur, 0.37):
            render.Engine.NO_CACHE = False; f1 = np.asarray(fast.frame(float(t)))
            render.Engine.NO_CACHE = True; f2 = np.asarray(slow.frame(float(t)))
            if not np.array_equal(f1, f2):
                bad.append(round(float(t), 2))
        render.Engine.NO_CACHE = False
        assert not bad, f"cache differs at {bad[:6]}"
        return "frame caches pixel-exact with characters + stages"
    case(f"[{aspect}] caches exact with characters", cache_exact)


def lru():
    e = render.Engine("E_169.json", 0.5)
    stages = [s for s in e.scenes if s.get("_stage") is not None]
    for s in stages:
        e.frame(s["t0"] + 0.5)
    live = sum(1 for s in stages if s["_stage"].layers is not None)
    assert live <= 2, f"{live} stages hold pixels"
    return f"{len(stages)} stage scenes, {live} loaded at once"
case("stage memory stays bounded (LRU)", lru)


def variety_respect():
    e = render.Engine("E_169.json", 0.5)
    fams = [d.get("_family") for sc in json.load(open("E_169.json"))["scenes"] for d in sc["items"] if d["type"] == "stamp"]
    rep = e.variety
    assert rep["used"].get("rubber", 0) >= 2 and any("OVER BUDGET" in w for w in e.warnings), "explicit over-budget rubber must be warned"
    return f"families {rep['emphasis']}; over-budget warned"
case("variety: explicit designs respected + warned", variety_respect)


def full_render():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "core", "engine", "render.py"), "video", "--edit", "E_169.json",
                        "--out", "stress.mp4", "--to", "30"], capture_output=True, text=True, timeout=1500)
    assert r.returncode == 0, r.stdout[-400:] + r.stderr[-800:]
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration,nb_frames,width,height",
                          "-of", "json", "stress.mp4"], capture_output=True, text=True).stdout
    s = json.loads(out)["streams"]
    v = [x for x in s if x["codec_type"] == "video"][0]; a = [x for x in s if x["codec_type"] == "audio"][0]
    assert (int(v["width"]), int(v["height"])) == (1920, 1080)
    assert abs(float(v["duration"]) - 30) < 0.15 and abs(float(a["duration"]) - float(v["duration"])) < 0.12, (v["duration"], a["duration"])
    return f"1080p 30 s, video {float(v['duration']):.2f}s / audio {float(a['duration']):.2f}s, {v['nb_frames']} frames"
case("full 1080p multi-worker render + audio sync", full_render)

print(f"\n{sum(ok for _, ok in RES)}/{len(RES)} passed")
shutil.rmtree(_tmp, ignore_errors=True)
sys.exit(0 if all(ok for _, ok in RES) else 1)
