# -*- coding: utf-8 -*-
"""character.py -- Character-Based 2D Storytelling Mode (v3, optional).

A cute, consistent 2D cartoon character who LIVES inside the documentary: walks into a scene, talks to camera
with lip-flaps locked to the real voiceover words, points at the evidence, reacts, looks around, walks through a
parallax world while the camera tracks them. Everything else in the edit keeps its normal style -- the character
appears only in the scenes that ask for it.

HOW THE CHARACTER IS BUILT (no rigging, no morphing -- a pose library, like TV cut-out animation)
  One master image of the character + a set of POSES generated on Google Flow with the master as reference
  (same face, hair, outfit, colours, proportions), keyed to transparent PNGs:
      elements/cut/<cast>_<pose>.png        e.g. mira_idle.png, mira_talk.png, mira_walk1.png ...
  core poses   idle  talk  blink  walk1 walk2 (walk3 walk4)  point  wow  think  happy
  optional     run1 run2  wave  sad  look  hold  shrug  <pose>_talk (mouth-open version of any pose)
  Missing poses fall back gracefully: talk -> idle with a jaw-bob, walk -> idle with a puppet bob, run -> walk.

ON SCREEN (EDIT.json item)
  {"type": "character", "cast": "mira", "at": "नेपाल", "until": "@09",
   "enter": "walk_in",            walk_in (default) | run_in | pop | rise | fade | none
   "from": "right",               side the walk-in starts from (default: the far side)
   "x": 0.5,                      resting spot inside the cast slot (0 = left edge, 1 = right edge)
   "height": 0.96,                fraction of the cast slot height
   "talk": true,                  lip-flap on every spoken word while visible (false = silent actor)
   "exit": "walk_out",            walk_out | run_out | fade | pop  (used when the item has "until")
   "actions": [
      {"at": "सुंदर", "do": "point"},                         any pose name: holds 1.6 s (or "until") then idle
      {"at": "पहाड़", "do": "walk", "to": 0.8},              walk / run to an x (camera tracks on stages)
      {"at": "वाह",  "do": "react", "pose": "wow"},          pose + a little hop
      {"at": "देखो", "do": "look", "dir": "left"},           turn to face a side
      {"at": "नेपाल", "do": "say", "text": "नेपाल बहुत सुंदर है!", "until": "@08"},   speech bubble
      {"at": "हाँ",  "do": "nod"}, {"at": "नहीं", "do": "shake"}, {"at": "...", "do": "hop"},
      {"at": "...", "do": "talk", "until": "..."}, {"at": "...", "do": "quiet", "until": "..."}]}

  Layouts with a "cast" slot: presenter / presenter_l (documentary beat + host beside it) and stage (full
  character scene). Any other layout gets a default zone with a warning.

STAGE SCENES (parallax world + camera tracking)
  {"layout": "stage", "stage": {
      "layers": [{"src": "nepal_sky", "depth": 0.04, "drift": 8},     depth 0 = infinitely far, 1 = the ground
                 {"src": "nepal_himalaya", "depth": 0.18},
                 {"src": "nepal_village", "depth": 0.55},
                 {"src": "nepal_path", "depth": 1.0}],
      "fg": [{"src": "rhododendron_fg", "depth": 1.45}],              drawn IN FRONT of the character
      "track": "mira",            camera follows this character's walk (critically damped, never jerky)
      "particles": "petals",      petals | snow | dust | fireflies | none   (ambient life)
      "palette": "day"}}          procedural fallback look when a layer image is missing: day | dusk | night
  Layer images are wide strips keyed on magenta (sky can be a plain full image); they are mirror-tiled so the
  world never runs out while walking. A missing layer is replaced by a soft procedural one (with a warning) so
  previews always work -- the real video should use Flow-generated layers.
"""
import math, zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import kit

CORE_POSES = ["idle", "talk", "blink", "walk1", "walk2", "point", "wow", "think", "happy"]
EXTRA_POSES = ["walk3", "walk4", "run1", "run2", "wave", "sad", "look", "hold", "shrug"]
ALL_POSES = CORE_POSES + EXTRA_POSES
HOLD = 1.6               # a gesture pose holds this long, then the character relaxes back to idle
WALK_SPEED = 0.30        # slot-widths per second
RUN_SPEED = 0.62


# ====================================================================== cast
class Cast:
    def __init__(self, name, cfg, find_image, warnings):
        self.name = name
        self.cfg = cfg or {}
        self.faces = self.cfg.get("faces", "right")          # which way the drawn art looks
        self.files = {}
        explicit = self.cfg.get("poses", {})
        for pose in ALL_POSES + [p for p in explicit if p not in ALL_POSES]:
            src = explicit.get(pose, f"{name}_{pose}")
            p = find_image(src)
            if p:
                self.files[pose] = p
        for pose in list(explicit) + ALL_POSES:            # "<pose>_talk" mouth-open variants
            p = find_image(f"{name}_{pose}_talk")
            if p:
                self.files[f"{pose}_talk"] = p
        self.placeholder = "idle" not in self.files
        if self.placeholder:
            warnings.append(f"character {name!r}: no art found (elements/cut/{name}_idle.png ...) -> drawing a "
                            f"placeholder toon. Generate the pose set: SHOTS.json kind 'character' (see CHARACTER_MODE.md)")
        else:
            miss = [p for p in CORE_POSES if p not in self.files]
            if miss:
                warnings.append(f"character {name!r}: missing poses {', '.join(miss)} -> fallbacks used "
                                f"(generate them for natural motion)")
        self._img = {}
        self._feet = {}

    def has(self, pose):
        return self.placeholder and pose in ("idle", "talk", "blink", "walk1", "walk2", "point", "wow", "think", "happy") \
            or pose in self.files

    def image(self, pose):
        """Trimmed RGBA pose, normalised: every pose has the same body height (feet to top), unless the cast
        config gives a per-pose 'scale' (e.g. arms-up poses: {"scale": {"wow": 1.12}})."""
        if pose in self._img:
            return self._img[pose]
        if self.placeholder:
            im = placeholder_pose(pose, seed=zlib.crc32(self.name.encode()))
        else:
            im = kit.trim(Image.open(self.files[pose]).convert("RGBA"))
        ref_h = 1000
        k = ref_h * float(self.cfg.get("scale", {}).get(pose, 1.0)) / im.height
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        self._img[pose] = im
        a = np.asarray(im.getchannel("A")) > 90                       # feet anchor: centre of the bottom band
        rows = np.where(a.any(axis=1))[0]
        band = a[max(0, rows[-1] - int(im.height * 0.06)):rows[-1] + 1] if len(rows) else a
        cols = np.where(band.any(axis=0))[0]
        self._feet[pose] = float(cols.mean()) if len(cols) else im.width / 2
        return im

    def feet_x(self, pose):
        self.image(pose)
        return self._feet[pose]


def load_cast(spec, find_image, warnings):
    cast = {}
    names = set((spec.get("cast") or {}).keys())
    for sc in spec.get("scenes", []):
        for d in sc.get("items", []):
            if d.get("type") == "character":
                names.add(d.get("cast", "hero"))
    for n in sorted(names):
        cast[n] = Cast(n, (spec.get("cast") or {}).get(n), find_image, warnings)
    return cast


def placeholder_pose(pose, seed=1):
    """Stand-in toon (preview / self-test only): rounded head, big eyes, simple body. Clearly a placeholder."""
    W, H = 520, 1000
    S2 = 2
    im = Image.new("RGBA", (W * S2, H * S2), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    s = lambda v: int(v * S2)
    skin, shirt, pants, hair, ink = (247, 205, 170), (64, 132, 222), (52, 58, 84), (54, 38, 32), (28, 24, 30)
    lw = s(9)
    leg_a, leg_b = {"walk1": (-60, 40), "walk2": (40, -60), "walk3": (-20, 10), "walk4": (10, -20),
                    "run1": (-90, 70), "run2": (70, -90)}.get(pose, (-28, 28))
    for off in (leg_a, leg_b):                                  # legs + shoes
        g.line([(s(260), s(700)), (s(260 + off), s(950))], fill=pants + (255,), width=s(62))
        g.ellipse([s(260 + off - 52), s(930), s(260 + off + 52), s(985)], fill=ink + (255,))
    g.rounded_rectangle([s(150), s(430), s(370), s(730)], s(70), fill=shirt + (255,), outline=ink + (255,), width=lw)
    arm_up = pose in ("wow", "happy", "wave")
    if pose == "point":
        g.line([(s(350), s(500)), (s(500), s(420))], fill=shirt + (255,), width=s(50))
        g.ellipse([s(480), s(395), s(530), s(445)], fill=skin + (255,))
    elif arm_up:
        for sx in (-1, 1):
            g.line([(s(260 + sx * 95), s(480)), (s(260 + sx * 190), s(330))], fill=shirt + (255,), width=s(48))
            g.ellipse([s(260 + sx * 190 - 26), s(300), s(260 + sx * 190 + 26), s(352)], fill=skin + (255,))
    elif pose == "think":
        g.line([(s(330), s(500)), (s(300), s(390))], fill=shirt + (255,), width=s(46))
        g.ellipse([s(275), s(360), s(325), s(410)], fill=skin + (255,))
    g.ellipse([s(110), s(60), s(410), s(450)], fill=skin + (255,), outline=ink + (255,), width=lw)   # head
    g.chord([s(100), s(40), s(420), s(300)], 180, 360, fill=hair + (255,))
    eye_y = 250
    for ex in (215, 305):
        if pose == "blink":
            g.line([(s(ex - 26), s(eye_y)), (s(ex + 26), s(eye_y))], fill=ink + (255,), width=lw)
        else:
            r = 34 if pose == "wow" else 28
            g.ellipse([s(ex - r), s(eye_y - r), s(ex + r), s(eye_y + r)], fill=(255, 255, 255, 255), outline=ink + (255,), width=s(5))
            g.ellipse([s(ex - 12 + 8), s(eye_y - 14), s(ex + 12 + 8), s(eye_y + 14)], fill=ink + (255,))
    if pose in ("talk", "wow"):
        g.ellipse([s(232), s(330), s(292), s(385 if pose == "wow" else 372)], fill=(150, 40, 50, 255), outline=ink + (255,), width=s(5))
    else:
        g.arc([s(225), s(300), s(300), s(360)], 20, 160, fill=ink + (255,), width=s(7))
    g.ellipse([s(150), s(300), s(190), s(330)], fill=(240, 140, 140, 150))
    g.ellipse([s(330), s(300), s(370), s(330)], fill=(240, 140, 140, 150))
    return kit.trim(im.resize((W, H), Image.LANCZOS))


# ====================================================================== helpers
def spring_scale(dt):
    """Squash -> stretch -> settle after a pose change (anticipation + overshoot, 12 principles)."""
    if dt < 0 or dt > 0.5:
        return 1.0, 1.0
    amp = 0.075 * math.exp(-dt * 11) * math.cos(dt * 26)
    return 1 + amp * 0.55, 1 - amp


def ease_io(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


# ====================================================================== the on-screen character
class CharacterItem:
    type = "character"

    def __init__(self, d, sc, eng):
        self.d, self.sc, self.e = d, sc, eng
        self.look = sc.get("look", eng.look)
        self.slot, self.rect = None, None
        self.t_in = self.t_out = 0.0
        self.exit = False
        self.cast = eng.cast.get(d.get("cast", "hero"))
        self.bbox = None
        self._cache = {}

    # -- item interface used by the engine
    def z(self):
        return self.d.get("z", 1)

    def alive(self, t):
        return self.t_in <= t < self.t_out

    def settled_at(self):
        return float("inf")          # a living character never stops moving (breath, blinks)

    # -- timeline
    def resolve(self):
        """Resolve every action cue, then build the position track (walk segments) and the pose events."""
        e, d = self.e, self.d
        x, y, w, h = self.rect
        if d.get("until") and self.t_out > self.sc["t1"]:   # an exit after the cut would never be seen
            e.warnings.append(f"scene {self.sc['id']}: character {d.get('cast')!r} 'until' is after the scene ends -> "
                              f"its exit now finishes at the cut ({self.sc['t1']:.2f}s)")
            self.t_out = self.sc["t1"]
        self.px_h = h * float(d.get("height", d.get("_height", 0.96)))
        idle = self.cast.image("idle")
        self.px_w = idle.width * self.px_h / idle.height
        rest = float(d.get("x", 0.5))
        edge = (self.px_w * 0.55 + 8) / w                 # keep the whole body inside the frame when standing still
        lo, hi = (edge - x / w), (e.W - x) / w - edge
        if lo < hi:
            rest = min(max(rest, lo), hi)
        self._clamp = (lo, hi) if lo < hi else None
        foot = x + rest * w                           # enter from the frame edge NEAREST the resting spot,
        frm = d.get("from") or ("left" if foot < e.W / 2 else "right")   # so the walk never crosses the text
        off_l = (-x - self.px_w * 0.7) / w            # fully off-screen, in slot units
        off_r = (e.W - x + self.px_w * 0.7) / w
        enter = d.get("enter", "walk_in")
        self.enter = enter
        segs, poses = [], []                          # (t0, t1, x0, x1, gait)
        cur_x, t_cur = rest, self.t_in
        if enter in ("walk_in", "run_in"):
            start = off_l if frm == "left" else off_r
            spd = RUN_SPEED if enter == "run_in" else WALK_SPEED
            dur = min(2.6, max(0.6, abs(rest - start) * w / e.W / spd * 1.0))
            segs.append((self.t_in, self.t_in + dur, start, rest, "run" if enter == "run_in" else "walk"))
            t_cur = self.t_in + dur
        self.facing0 = "left" if (segs and segs[0][3] < segs[0][2]) else ("right" if segs else
                                                                          ("right" if rest < 0.5 else "left"))
        self.facings = []                             # (t, dir)
        self.hops, self.nods, self.shakes, self.bubbles = [], [], [], []
        self.quiet, self.talks = [], []
        for a in d.get("actions", []):
            ta = e.sub_time(a.get("at"), t_cur, self.t_in)
            tu = e.sub_time(a.get("until"), None, ta) if a.get("until") else None
            do = a.get("do", "pose")
            if do in ("walk", "run"):
                to = float(a.get("to", rest))
                if self._clamp and self.sc.get("stage") is None:
                    to = min(max(to, self._clamp[0]), self._clamp[1])   # off a stage: never walk out of frame by accident
                spd = RUN_SPEED if do == "run" else WALK_SPEED
                x0 = segs[-1][3] if segs else rest
                t0 = max(ta, segs[-1][1] if segs else ta)
                dur = float(a.get("dur", abs(to - x0) * w / e.W / spd + 0.05))
                segs.append((t0, t0 + max(0.3, dur), x0, to, do))
            elif do == "look":
                self.facings.append((ta, a.get("dir", "left")))
            elif do in ("react", "hop", "jump"):
                self.hops.append(ta)
                if do == "react":
                    poses.append((ta, tu or ta + HOLD, a.get("pose", "wow")))
            elif do == "nod":
                self.nods.append(ta)
            elif do == "shake":
                self.shakes.append(ta)
            elif do == "say":
                self.bubbles.append((ta, tu or ta + max(1.8, len(a.get("text", "")) * 0.07), a.get("text", "")))
            elif do == "talk":
                self.talks.append((ta, tu or ta + 2.0))
            elif do == "quiet":
                self.quiet.append((ta, tu or ta + 2.0))
            else:                                       # any pose name
                pz = a.get("pose", do)
                if pz not in ALL_POSES and pz not in self.cast.files and do not in ("pose", "gesture"):
                    e.warnings.append(f"scene {self.sc['id']}: character action {do!r} is not a known action or pose "
                                      f"(actions: walk run look react hop jump nod shake say talk quiet; poses: {', '.join(ALL_POSES)})")
                elif not self.cast.has(pz):
                    e.warnings.append(f"scene {self.sc['id']}: {d.get('cast')!r} has no {pz!r} pose image -> shows idle "
                                      f"(generate {d.get('cast')}_{pz})")
                poses.append((ta, tu or ta + float(a.get("hold", HOLD)), pz))
        if d.get("until"):
            ex = d.get("exit", "walk_out" if enter in ("walk_in", "run_in") else "fade")
            self.exit_kind = ex
            if ex in ("walk_out", "run_out"):
                x0 = segs[-1][3] if segs else rest
                to = off_r if x0 >= 0.5 else off_l
                spd = RUN_SPEED if ex == "run_out" else WALK_SPEED
                dur = min(2.4, max(0.6, abs(to - x0) * w / e.W / spd))
                t0 = max(self.t_out - dur, segs[-1][1] if segs else self.t_in)
                segs.append((t0, t0 + dur, x0, to, "run" if ex == "run_out" else "walk"))
                self.t_out = max(self.t_out, t0 + dur)
        else:
            self.exit_kind = None
        self.segs, self.poses = segs, sorted(poses)
        self.rest = rest
        talk_on = d.get("talk", True)
        words = [(s, en) for (_, s, en, _, _) in e.tl.words if self.t_in - 0.05 <= s < self.t_out]
        if talk_on is False:
            words = [(s, en) for s, en in words if any(a <= s < b for a, b in self.talks)]
        self.words = [(s, en) for s, en in words if not any(a <= s < b for a, b in self.quiet)]
        sd = zlib.crc32(f"{d.get('cast')}{self.t_in:.2f}".encode())
        rng = np.random.default_rng(sd)
        self.blinks, tb = [], self.t_in + 0.8
        while tb < self.t_out:
            self.blinks.append(tb)
            tb += rng.uniform(2.3, 4.6)
        self.camx = None                               # filled by the stage camera if tracked

    # -- state at time t
    def x_at(self, t):
        x = self.rest
        for t0, t1, x0, x1, _ in self.segs:
            if t < t0:
                return x
            x = x0 + (x1 - x0) * ease_io((t - t0) / max(1e-3, t1 - t0)) if t < t1 else x1
        return x

    def moving(self, t):
        for t0, t1, x0, x1, g in self.segs:
            if t0 <= t < t1:
                return g, (t - t0), (1 if x1 > x0 else -1)
        return None, 0.0, 0

    def facing(self, t):
        """Walking: the way they walk. Standing: towards the frame centre (where the story is), unless a
        'look' action given after the last walk says otherwise."""
        g, _, sgn = self.moving(t)
        if g:
            return "right" if sgn > 0 else "left"
        last_move = max([t1 for t0, t1, *_ in self.segs if t1 <= t] or [self.t_in])
        f = None
        for tl, dr in self.facings:
            if last_move <= tl <= t:
                f = dr
        if f:
            return f
        return "right" if self.screen_x(t) < self.e.W * 0.5 else "left"

    def speaking(self, t):
        for s, en in self.words:
            if s <= t < en:
                return int((t - s) * 9.0) % 2 == 0          # ~9 Hz flap, open on the attack
        return False

    def base_pose(self, t):
        pose, since = "idle", self.t_in
        for t0, t1, p in self.poses:
            if t0 <= t < t1:
                pose, since = p, t0
        if pose != "idle":
            return pose, since
        for t0, t1, _ in self.poses:                        # relaxed back to idle at t1
            if t1 <= t:
                since = max(since, t1)
        return pose, since

    def pick(self, t):
        """(pose image name, change time) for frame t."""
        c = self.cast
        g, dt, _ = self.moving(t)
        if g:
            frames = [p for p in ((["run1", "run2"] if g == "run" and c.has("run1") else
                                   ["walk1", "walk2", "walk3", "walk4"])) if c.has(p)]
            if frames:
                rate = 11.0 if g == "run" else 7.5
                return frames[int(dt * rate) % len(frames)], None
            return "idle", None
        pose, since = self.base_pose(t)
        if not c.has(pose):
            pose = "idle"
        if self.speaking(t):
            if c.has(f"{pose}_talk"):
                return f"{pose}_talk", since
            if pose == "idle" and c.has("talk"):
                return "talk", since
        if pose == "idle" and c.has("blink") and any(0 <= t - b < 0.11 for b in self.blinks):
            return "blink", since
        return pose, since

    # -- drawing
    def sprite(self, pose, flip, h):
        key = (pose, flip, int(h))
        sp = self._cache.get(key)
        if sp is None:
            if len(self._cache) > 40:
                self._cache.clear()
            im = self.cast.image(pose)
            k = h / 1000.0
            sp = im.resize((max(1, int(im.width * k)), max(1, int(h))), Image.LANCZOS)
            if flip:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            self._cache[key] = sp
        return sp

    def screen_x(self, t):
        x, y, w, h = self.rect
        cam = self.camx(t) if self.camx else 0.0
        return x + (self.x_at(t) - cam) * w

    def draw(self, cv, t, ox=0, oy=0):
        if not self.alive(t):
            return
        S = self.e.S
        x, y, w, h = self.rect
        pose, since = self.pick(t)
        face = self.facing(t)
        flip = face != self.cast.faces
        H = self.px_h
        sx = sy = 1.0
        op = 1.0
        dy = 0.0
        g, gdt, _ = self.moving(t)
        if g:                                            # walk bob + slight squash at each footfall
            ph = gdt * (11.0 if g == "run" else 7.5) * math.pi
            dy -= abs(math.sin(ph)) * H * (0.03 if g == "run" else 0.018)
            sy *= 1 - 0.012 * abs(math.cos(ph))
        else:                                            # breathing (anchored at the feet)
            br = math.sin(2 * math.pi * (t - self.t_in) / 3.4)
            sy *= 1 + 0.009 * br
            sx *= 1 - 0.004 * br
            if not self.cast.has("talk") and self.speaking(t):
                sy *= 1.012                              # jaw-bob fallback
        if since is not None:
            a, b = spring_scale(t - since)
            sx, sy = sx * a, sy * b
        for th in self.hops:
            q = (t - th) / 0.38
            if 0 <= q < 1:
                dy -= math.sin(math.pi * q) * H * 0.07
        for tn in self.nods:
            q = (t - tn) / 0.6
            if 0 <= q < 1:
                dy += abs(math.sin(q * math.pi * 2)) * H * 0.012
        shake_dx = 0.0
        for ts in self.shakes:
            q = (t - ts) / 0.6
            if 0 <= q < 1:
                shake_dx = math.sin(q * math.pi * 4) * H * 0.012 * (1 - q)
        ent = self.enter
        dt_in = t - self.t_in
        if ent == "pop" and dt_in < 0.5:
            k = kit.ease_out_back(kit.clamp(dt_in / 0.42))
            sx, sy, op = sx * (0.4 + 0.6 * k), sy * (0.4 + 0.6 * k), kit.clamp(dt_in / 0.1)
        elif ent == "rise" and dt_in < 0.6:
            dy += (1 - kit.ease_out_expo(kit.clamp(dt_in / 0.55))) * H * 0.25
            op = kit.clamp(dt_in / 0.2)
        elif ent == "fade":
            op = kit.clamp(dt_in / 0.4)
        if self.exit_kind in ("fade", "pop") and t > self.t_out - 0.4:
            q = kit.clamp((self.t_out - t) / 0.4)
            op *= q
            if self.exit_kind == "pop":
                sx, sy = sx * (0.5 + 0.5 * q), sy * (0.5 + 0.5 * q)
        sp = self.sprite(pose, flip, H)
        if abs(sx - 1) > 1e-3 or abs(sy - 1) > 1e-3:
            sp = sp.resize((max(1, int(sp.width * sx)), max(1, int(sp.height * sy))), Image.BILINEAR)
        feet_rel = self.cast.feet_x(pose) / self.cast.image(pose).width
        if flip:
            feet_rel = 1 - feet_rel
        fx = self.screen_x(t) + ox + shake_dx
        fy = y + h + oy                                   # the ground line = bottom of the cast slot
        px, py = fx - sp.width * feet_rel, fy - sp.height + dy
        # soft ground shadow: shrinks and fades while the feet leave the ground
        lift = kit.clamp(-dy / (H * 0.08))
        gs = self._shadow(int(self.px_w * 0.62 * (1 - 0.25 * lift)), int(H * 0.06), 0.36 * (1 - 0.5 * lift) * op)
        cv.paste(gs, (int(fx - gs.width / 2), int(fy - gs.height / 2)), gs)
        sp = kit.with_alpha(sp, op)
        cv.paste(sp, (int(px), int(py)), sp)
        self.bbox = (px, py, sp.width, sp.height)
        self._bub = (px, py, sp.width, face)            # bubbles are drawn later, above every actor (draw_bubbles)

    def draw_bubbles(self, cv, t):
        if not self.alive(t) or getattr(self, "_bub", None) is None:
            return
        px, py, sw, face = self._bub
        for tb0, tb1, text in self.bubbles:
            if tb0 <= t < tb1:
                self._bubble(cv, t, tb0, tb1, text, px, py, sw, face)

    def _shadow(self, w, h, alpha):
        key = ("sh", w // 4, h // 2, int(alpha * 20))
        s = self._cache.get(key)
        if s is None:
            s = self._cache[key] = kit.ground_shadow(w, h, alpha)
        return s

    def _bubble(self, cv, t, t0, t1, text, px, py, sw, face):
        e, S = self.e, self.e.S
        key = ("bubble", text)
        b = self._cache.get(key)
        if b is None:
            txt, _ = kit.text_block(text, "round", 42 * S * (1.15 if e.aspect == "9:16" else 1), (28, 26, 32),
                                    e.W * (0.30 if e.aspect == "16:9" else 0.62), max_lines=3, align="center")
            txt = kit.trim(txt)
            pw, ph = int(34 * S), int(24 * S)
            W, H = txt.width + pw * 2, txt.height + ph * 2
            body = kit.rounded(W, H, int(min(H, W) * 0.42), (255, 255, 255, 250), outline=(28, 26, 32, 255),
                               width=max(3, int(4 * S)))
            body.alpha_composite(txt, (pw, ph))
            b = self._cache[key] = kit.shadow(body, blur=int(10 * S), dy=int(6 * S), alpha=0.28)
        head_x = px + sw * (0.62 if face == "right" else 0.38)
        to_right = head_x < e.W * 0.55
        if e.aspect == "9:16":                            # narrow frame: no room beside the head -> centred above it
            bx, by = head_x - b.width / 2, py - b.height - 18 * S
        else:
            bx = head_x + (40 * S if to_right else -40 * S - b.width)
            by = py - b.height * 0.55
        bx = min(max(bx, e.W * 0.02), e.W * 0.98 - b.width)
        by = min(max(by, e.H * 0.03), e.H * 0.70 - b.height)
        k = kit.ease_out_back(kit.clamp((t - t0) / 0.32))
        op = kit.clamp((t - t0) / 0.1) * kit.clamp((t1 - t) / 0.2)
        g = ImageDraw.Draw(cv)
        tail_base = ((min(max(head_x, bx + b.width * 0.2), bx + b.width * 0.8), by + b.height * 0.7) if e.aspect == "9:16"
                     else (bx + (b.width * 0.25 if to_right else b.width * 0.75), by + b.height * 0.78))
        if op > 0.5:                                      # tail pointing at the speaker's head
            hx, hy = head_x, py + 30 * S
            g.polygon([(tail_base[0] - 16 * S, tail_base[1] - 8 * S), (tail_base[0] + 16 * S, tail_base[1] - 8 * S),
                       (hx + (tail_base[0] - hx) * 0.35, hy + (tail_base[1] - hy) * 0.35)],
                      fill=(255, 255, 255), outline=(28, 26, 32))
        sp = b if k >= 0.999 else b.resize((max(1, int(b.width * k)), max(1, int(b.height * k))), Image.BILINEAR)
        sp = kit.with_alpha(sp, op)
        cv.paste(sp, (int(bx + (b.width - sp.width) / 2), int(by + (b.height - sp.height) / 2)), sp)


# ====================================================================== stage: parallax world + tracking camera
PALETTES = {
    "day": {"sky": ((122, 186, 238), (214, 236, 250)), "far": (150, 178, 206), "snow": (246, 249, 252),
            "mid": (110, 170, 108), "near": (86, 146, 84), "ground": (196, 164, 116), "sun": (255, 236, 170)},
    "dusk": {"sky": ((246, 156, 112), (255, 214, 160)), "far": (150, 120, 150), "snow": (255, 226, 214),
             "mid": (120, 112, 120), "near": (92, 86, 98), "ground": (150, 112, 92), "sun": (255, 210, 140)},
    "night": {"sky": ((18, 26, 58), (52, 66, 112)), "far": (44, 54, 92), "snow": (190, 204, 236),
              "mid": (34, 52, 66), "near": (26, 40, 52), "ground": (48, 46, 58), "sun": (240, 240, 220)},
}


def _ridge(Wp, H, base, amp, rough, seed, peaks=False):
    rng = np.random.default_rng(seed)
    n = np.zeros(Wp, np.float32)
    for octv, a in ((1, 1.0), (2, 0.5), (4, 0.25), (8, 0.12)):
        k = max(2, int(Wp / (rough / octv)))
        pts = rng.random(k + 3).astype(np.float32)
        pts[-3:] = pts[:3]                               # wrap so the strip tiles seamlessly
        n += a * np.interp(np.linspace(0, k, Wp, endpoint=False), np.arange(k + 3), pts)
    n = n / 1.87
    if peaks:
        n = n ** 1.8
    return (base - n * amp).astype(np.float32)


def procedural_layer(kind, W, H, palette, seed, ground=None):
    """Soft flat-vector stand-in layer (preview only), 3 frames wide, seamless."""
    P = PALETTES.get(palette, PALETTES["day"])
    Wp = W * 3
    if kind == "sky":
        top, bot = np.array(P["sky"][0], np.float32), np.array(P["sky"][1], np.float32)
        tt = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        img = np.broadcast_to(top * (1 - tt) + bot * tt, (H, Wp, 3)).copy()
        im = Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")
        g = ImageDraw.Draw(im, "RGBA")                   # blend clouds INTO the sky (keeps the sky fully opaque)
        r = int(H * 0.07)
        g.ellipse([int(W * 0.75) - r, int(H * 0.16) - r, int(W * 0.75) + r, int(H * 0.16) + r], fill=P["sun"] + (255,))
        rng = np.random.default_rng(seed)
        for _ in range(9):                                # soft clouds
            cx, cy = rng.uniform(0, Wp), rng.uniform(H * 0.08, H * 0.35)
            for k in range(4):
                rr = rng.uniform(H * 0.035, H * 0.06)
                g.ellipse([cx + k * rr * 0.9 - rr, cy - rr * (0.7 if k % 3 else 1.0), cx + k * rr * 0.9 + rr, cy + rr * 0.6],
                          fill=(255, 255, 255, 215))
        return im.filter(ImageFilter.GaussianBlur(1.2))
    yy = np.arange(H, dtype=np.float32)[:, None]
    gy = ground if ground else H * 0.86              # the line the character's feet stand on
    if kind == "far":
        ridge = _ridge(Wp, H, H * 0.62, H * 0.40, W * 0.55, seed, peaks=True)
        col = np.array(P["far"], np.float32)
        snow = (yy < ridge[None, :] + H * 0.07) & (ridge[None, :] < H * 0.40)
    elif kind == "mid":
        ridge = _ridge(Wp, H, gy - H * 0.13, H * 0.16, W * 0.45, seed)
        col = np.array(P["mid"], np.float32)
        snow = None
    elif kind == "near":
        ridge = _ridge(Wp, H, gy - H * 0.05, H * 0.10, W * 0.3, seed)
        col = np.array(P["near"], np.float32)
        snow = None
    else:  # ground
        ridge = np.full(Wp, gy - H * 0.035, np.float32) + np.sin(np.linspace(0, 6 * math.pi, Wp, endpoint=False)) * H * 0.006
        col = np.array(P["ground"], np.float32)
        snow = None
    a = np.clip((yy - ridge[None, :]) * 1.5 + 0.5, 0, 1)            # anti-aliased skyline
    shade = 1 - 0.18 * np.clip((yy - ridge[None, :]) / (H * 0.3), 0, 1)
    rgb = np.broadcast_to(col, (H, Wp, 3)) * shade[..., None]
    if snow is not None:
        rgb = np.where(snow[..., None], np.array(P["snow"], np.float32), rgb)
    rng = np.random.default_rng(seed + 5)
    rgb = rgb + rng.normal(0, 2.2, (H, Wp, 1)).astype(np.float32)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8), "RGBA")


_LIVE = []                                   # stages whose layer pixels are currently loaded (LRU, max 2)


class Stage:
    """Built once per scene per worker: pre-scaled, mirror-tiled layers + the tracking camera path."""

    def __init__(self, eng, sc, find_image):
        self.e, self.sc = eng, sc
        cfg = sc["stage"] or {}
        self.cfg = cfg
        W, H = eng.W, eng.H
        pal = cfg.get("palette", "day")
        cast_r = eng.slots.get(sc["layout"], {}).get("cast")
        gy = eng.px(cast_r)[1] + eng.px(cast_r)[3] if cast_r else H * 0.86
        seed = zlib.crc32(str(sc["id"]).encode())
        defaults = [{"src": None, "depth": 0.03, "kind": "sky", "drift": 6}, {"src": None, "depth": 0.15, "kind": "far"},
                    {"src": None, "depth": 0.45, "kind": "mid"}, {"src": None, "depth": 0.75, "kind": "near"},
                    {"src": None, "depth": 1.0, "kind": "ground"}]
        self._spec = (cfg.get("layers") or defaults, cfg.get("fg") or [], pal, seed, gy, find_image)
        for L in list(self._spec[0]) + list(self._spec[1]):          # cheap existence check now, pixels later
            if L.get("src") and not find_image(L["src"]):
                eng.warnings.append(f"scene {sc['id']}: stage layer {L['src']!r} missing -> soft procedural stand-in")
        self.layers = self.fg = None                                   # built lazily (see _ensure)
        self.particles = cfg.get("particles", "none")
        self.cam = None

    def _ensure(self):
        """Load + scale + tile the layers on first draw. Only the 2 most recently used stages keep their pixels
        (a transition needs 2): a long video with many stage scenes stays inside phone memory."""
        if self.layers is not None:
            if self in _LIVE:
                _LIVE.remove(self)
            _LIVE.append(self)
            return
        groups, fgs, pal, seed, gy, find_image = self._spec
        W, H = self.e.W, self.e.H
        self.layers, self.fg = [], []
        for group, out in ((groups, self.layers), (fgs, self.fg)):
            for k, L in enumerate(group):
                p = find_image(L["src"]) if L.get("src") else None
                if p:
                    im = Image.open(p).convert("RGBA")
                    if k == 0 and out is self.layers and im.getchannel("A").getextrema()[0] == 255:
                        hh = H                                    # opaque back layer: cover the frame height
                    else:
                        hh = int(H * float(L.get("h", 0.6 if out is self.layers else 0.35)))
                    im = im.resize((max(1, int(im.width * hh / im.height)), hh), Image.LANCZOS)
                    if im.width < W * 2:                          # mirror-tile so walking never runs out of world
                        tile = Image.new("RGBA", (im.width * 2, hh))
                        tile.paste(im, (0, 0))
                        tile.paste(im.transpose(Image.FLIP_LEFT_RIGHT), (im.width, 0))
                        im = tile
                    ytop = int(H * float(L["y"])) if "y" in L else H - hh
                else:
                    kind = L.get("kind") or ("sky" if k == 0 and out is self.layers else ("far", "mid", "near", "ground")[min(3, max(0, k - 1))])
                    im, ytop = procedural_layer(kind, W, H, pal, seed + k, gy), 0
                bb = im.getchannel("A").getbbox()               # drop fully transparent rows: same pixels, less work
                if bb and (bb[1] > 0 or bb[3] < im.height):
                    im, ytop = im.crop((0, bb[1], im.width, bb[3])), ytop + bb[1]
                out.append({"im": im, "depth": float(L.get("depth", 0.5)), "drift": float(L.get("drift", 0)), "y": ytop})
        first = self.layers[0] if self.layers else None
        if first is None or not (first["y"] == 0 and first["im"].height >= H and first["im"].getchannel("A").getextrema()[0] == 255):
            # no opaque full-frame back layer (e.g. only keyed strips were given): add a soft sky, never black
            self.layers.insert(0, {"im": procedural_layer("sky", W, H, pal, seed), "depth": 0.03, "drift": 6.0, "y": 0})
        _LIVE.append(self)
        while len(_LIVE) > 2:
            old = _LIVE.pop(0)
            old.layers = old.fg = None

    def track(self, item):
        """Critically damped follow of the tracked character's walk (computed from the scene start, so every
        render chunk gets the identical camera)."""
        fps = 48.0
        t0, t1 = self.sc["t0"], self.sc["t1"] + 0.5
        n = int((t1 - t0) * fps) + 2
        ts = t0 + np.arange(n) / fps
        target = np.array([item.x_at(t) - item.rest for t in ts], np.float32)
        lead = float(self.cfg.get("lead", 0.12))
        target = target + np.array([item.moving(t)[2] * lead for t in ts], np.float32)
        w = float(self.cfg.get("stiffness", 3.2))
        pos, vel = float(target[0]), 0.0
        out = np.empty(n, np.float32)
        dt = 1 / fps
        for i in range(n):
            acc = w * w * (target[i] - pos) - 2 * w * vel
            vel += acc * dt
            pos += vel * dt
            out[i] = pos
        self.cam = (t0, fps, out)
        item.camx = self.cam_at

    def cam_at(self, t):
        if self.cam is None:
            return 0.0
        t0, fps, arr = self.cam
        i = (t - t0) * fps
        i0 = int(min(max(0, math.floor(i)), len(arr) - 2))
        f = min(1.0, max(0.0, i - i0))
        return float(arr[i0] * (1 - f) + arr[i0 + 1] * f)

    def _paste_layer(self, cv, L, t, slot_w, opaque=False):
        """Only the visible W-wide window of a (wide, tiled) layer is composited -- never the whole strip
        (compositing the full 3x-wide layer made stage scenes ~6x slower). Opaque layers are pasted, not blended."""
        im = L["im"]
        if "rgb" not in L:                                      # opaque sky: keep an RGB copy for plain pasting
            L["rgb"] = im.convert("RGB") if opaque or im.getchannel("A").getextrema()[0] == 255 else None
        off = self.cam_at(t) * slot_w * L["depth"] - L["drift"] * self.e.S * (t - self.sc["t0"])
        x0 = (-int(off)) % im.width                             # source column shown at screen x = 0
        W = self.e.W
        src = L["rgb"] or im
        x, sx = 0, x0
        while x < W:                                            # at most 2 pieces (wrap-around)
            w = min(W - x, im.width - sx)
            piece = src.crop((sx, 0, sx + w, im.height))
            if L["rgb"] is not None:
                cv.paste(piece, (x, L["y"]))
            elif cv.mode == "RGB":                              # blend straight onto the RGB frame (no convert)
                cv.paste(piece, (x, L["y"]), piece)
            else:
                cv.alpha_composite(piece, (x, L["y"]))
            x += w
            sx = 0

    def background(self, t, slot_w):
        self._ensure()
        cv = Image.new("RGB", (self.e.W, self.e.H), (0, 0, 0))
        for k, L in enumerate(self.layers):
            self._paste_layer(cv, L, t, slot_w, opaque=(k == 0 and L["y"] == 0 and L["im"].height >= self.e.H))
        return cv

    def foreground(self, cv, t, slot_w):
        self._ensure()
        if not self.fg and self.particles in (None, "none"):
            return
        for L in self.fg:
            self._paste_layer(cv, L, t, slot_w)
        if self.particles not in (None, "none"):
            self._particles(cv, t)

    def _particles(self, layer, t):
        W, H, S = self.e.W, self.e.H, self.e.S
        kind = self.particles
        rng = np.random.default_rng(zlib.crc32(f"p{self.sc['id']}".encode()))
        n = {"snow": 70, "petals": 26, "dust": 40, "fireflies": 22}.get(kind, 0)
        g = ImageDraw.Draw(layer, "RGBA")                       # blends translucent particles onto RGB directly
        cam = self.cam_at(t) * W * 0.5
        for i in range(n):
            x0, y0, sp, ph = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.5, 1.4), rng.uniform(0, 6.28)
            if kind == "fireflies":
                x = (x0 + math.sin(t * 0.7 * sp + ph) * 40 * S - cam * 0.6) % W
                y = y0 * 0.7 + H * 0.2 + math.cos(t * 0.9 * sp + ph) * 30 * S
                a = int(120 + 120 * math.sin(t * 3 * sp + ph) ** 2)
                r = 4 * S
                g.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 150, a))
                continue
            fall = {"snow": 60, "petals": 70, "dust": 8}[kind] * sp * S
            x = (x0 + math.sin(t * sp + ph) * 30 * S + t * 18 * S * sp - cam) % W
            y = (y0 + t * fall) % H
            if kind == "snow":
                r = 3.2 * S * sp
                g.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 200))
            elif kind == "petals":
                r = 7 * S * sp
                g.ellipse([x - r, y - r * 0.55, x + r, y + r * 0.55], fill=(238, 120, 150, 215))
            else:
                r = 2.2 * S * sp
                g.ellipse([x - r, y - r, x + r, y + r], fill=(255, 238, 200, 90))
