"""cues.tsv + VO.wav -> mix.wav   (Vox-style documentary mix)

    python scripts/mix.py cues.tsv --vo VO.wav --lines VO.tsv --words WORDS.tsv --out mix.wav
    python scripts/mix.py --selfcheck

cues.tsv columns (tab separated):
    label    any name. The row labelled "bed" is the music bed: it gets ducked by
             every SFX and by the voice, and it gets the optional --dip
    kind     loop | one       loop = repeat the file for `dur` seconds
    file     path relative to the kit folder (sfx/..., music/...) or absolute
    at       WHEN it starts. One of:
               12.4         seconds
               @05          the start of VO line 05
               भारत         the first spoken word containing "भारत", searched
                            forward from the previous word cue, so cues stay in
                            script order
               भारत+0.3     the same word, shifted by +0.3 s (use -0.1 to lead)
               w:1906       a word that is itself a number (a bare number means seconds)
    dur      loop length in seconds, or "all" (until the end). Ignored for "one"
    gain_db  level of this sound, e.g. -18
    fade_in  seconds
    fade_out seconds

Word cues are the point: change the voice, re-run align.py, and every click
still lands on its word. No retiming.

One-shots are placed PEAK on the cue, not file-start on the cue: a page turn
whose loudest moment is 0.3 s in would otherwise land 7 frames late.
Except sounds that run WITH an animation starting on the word (counters, odometer
rolls, scoreboard flips: ROLLING below). Those START on the cue: peak-aligned, an
odometer roll peaking 0.76 s in began before the counter was even on screen.

Levels: every file in CATALOG.tsv (built by scripts/index_sfx.py) carries a
level_offset. mix.py adds it to the cue's gain_db, so the gains in SKILL.md
mean the same thing for any sound, from any pack, at any original loudness.
Files that are not in the catalog are used exactly as they are. Run index_sfx.py
after adding sounds.

Mix chain:
- Each voice is first brought to -22 LUFS. Without this, a loud narrator (one
  measured -17 LUFS) made the final loudnorm pull the whole mix down, and the
  music and SFX sank about 5 dB.
- The bed ducks under SFX, and everything ducks under the voice
  (sidechaincompress).
- Final loudness is -14 LUFS with a -1.5 dBTP ceiling, the YouTube target.
"""
import argparse, csv, os, re, subprocess, sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLLING = re.compile(r"(?i)/Numbers/|counter|counting|odometer|ticking")   # start on the cue, not peak



def start_time(t, peak, file):
    """When a one-shot starts: its peak on the cue, but rolling sounds start on it."""
    return t if ROLLING.search(file.replace("\\", "/")) else max(0.0, t - peak)


def tsv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def clean(w):
    return re.sub(r"[।?,.!\"'“”‘’:;]", "", w)


class Resolver:
    """Turns an `at` value into seconds."""

    def __init__(self, lines=None, words=None):
        self.lines = {r["id"]: float(r["start"]) for r in lines or []}
        self.words = [(float(r["start"]), clean(r["word"])) for r in words or []]
        self.pos = 0

    def __call__(self, at):
        at = at.strip()
        m = re.fullmatch(r"(.+?)([+-]\d+(?:\.\d+)?)?", at)
        base, off = m.group(1), float(m.group(2) or 0)
        if not base.startswith("w:"):
            try:
                return max(0.0, float(base) + off)
            except ValueError:
                pass
        if base.startswith("w:"):
            base = base[2:]
        elif base.startswith("@"):
            lid = base[1:]
            if lid in self.lines:
                return max(0.0, self.lines[lid] + off)
            # Graceful numeric fallback if line ID exceeds VO.tsv
            try:
                num = int(lid)
                numeric_keys = sorted([int(k) for k in self.lines if k.isdigit()])
                if numeric_keys:
                    closest = min(numeric_keys, key=lambda x: abs(x - num))
                    return max(0.0, self.lines[f"{closest:02d}"] + off)
            except Exception:
                pass
            if self.words:
                return max(0.0, self.words[-1][0] + off)
            return max(0.0, off)
        # Search forward from self.pos
        for k in range(self.pos, len(self.words)):
            if base in self.words[k][1]:
                self.pos = k
                return max(0.0, self.words[k][0] + off)
        # Search across all words if not found forward
        for k in range(0, len(self.words)):
            if base in self.words[k][1]:
                self.pos = k
                return max(0.0, self.words[k][0] + off)
        if os.environ.get("MIX_STRICT") == "1":
            raise SystemExit(f"cue {at!r}: word not found after word #{self.pos} "
                             f"(pass --words WORDS.tsv, keep cues in script order)")
        print(f"warning: cue {at!r}: word not found after word #{self.pos} -> fallback")
        if self.words:
            idx = min(self.pos, len(self.words) - 1)
            return max(0.0, self.words[idx][0] + off)
        return max(0.0, off)


def catalog():
    """file -> (peak seconds, level offset dB), from CATALOG.tsv (index_sfx.py)."""
    for cand in [os.path.join(KIT, "CATALOG.tsv"),
                 os.path.join(KIT, "audio", "CATALOG.tsv"),
                 os.path.join(KIT, "skills", "vox-doc-sound", "CATALOG.tsv")]:
        if os.path.exists(cand):
            return {r["file"]: (float(r["peak"] or 0), float(r.get("level_offset") or 0)) for r in tsv(cand)}
    return {}


def media_len(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip())


def build(cues, vo, out, dur, dip):
    cmd, parts, sfx = ["ffmpeg", "-y", "-loglevel", "error"], [], []
    labels = [c["label"] for c in cues]
    for i, c in enumerate(cues):
        path = c["file"]
        if not os.path.isabs(path):
            found = False
            for cand in [os.path.join(KIT, path),
                         os.path.join(KIT, "audio", path),
                         os.path.join(KIT, "skills", "vox-doc-sound", path)]:
                if os.path.exists(cand):
                    path = cand
                    found = True
                    break
            if not found:
                base = os.path.basename(path)
                for search_root in [os.path.join(KIT, "audio"),
                                    os.path.join(KIT, "skills", "vox-doc-sound")]:
                    if os.path.exists(search_root):
                        for root, _, files in os.walk(search_root):
                            if base in files:
                                path = os.path.join(root, base)
                                found = True
                                break
                    if found:
                        break
            if not found:
                path = os.path.join(KIT, path)
        assert os.path.exists(path), f"cue {c['label']}: file missing {path}"
        gain, fi, fo = float(c["gain_db"]), float(c["fade_in"] or 0), float(c["fade_out"] or 0)
        if c["kind"] == "loop":
            d = dur - c["t"] if c["dur"] in ("all", "") else float(c["dur"])
            cmd += ["-stream_loop", "-1", "-i", path]
            f = [f"atrim=0:{d:.3f}", "asetpts=N/SR/TB"]
            if fi:
                f.append(f"afade=t=in:st=0:d={fi}")
            if fo:
                f.append(f"afade=t=out:st={max(0, d - fo):.3f}:d={fo}")
        else:
            cmd += ["-i", path]
            f = []
        f += ["aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo", f"volume={gain}dB"]
        if c["label"] == "bed" and dip is not None:
            # a held breath: a smooth dip in the bed, not a step
            f.append(f"volume='1-0.62*exp(-pow((t-{dip})/0.85,2))':eval=frame")
        if c["t"] > 0:
            f.append(f"adelay={int(c['t'] * 1000)}:all=1")
        parts.append(f"[{i}:a]" + ",".join(f) + f"[a{i}]")
        if c["label"] != "bed":
            sfx.append(f"[a{i}]")

    n = len(cues)
    if "bed" in labels and sfx:
        bed = f"[a{labels.index('bed')}]"
        parts.append("".join(sfx) + f"amix=inputs={len(sfx)}:normalize=0:dropout_transition=0:duration=longest[sfx]")
        parts.append("[sfx]asplit=2[sfxmix][key]")
        parts.append(f"{bed}[key]sidechaincompress=threshold=0.04:ratio=4:attack=25:release=450[duck]")
        parts.append("[duck][sfxmix]amix=inputs=2:normalize=0:dropout_transition=0:duration=longest[world]")
    else:
        parts.append("".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0:dropout_transition=0:duration=longest[world]")

    tail = f"apad=whole_dur={dur:.3f},atrim=0:{dur:.3f},loudnorm=I=-14:TP=-1.5:LRA=11[out]"
    if vo:
        cmd += ["-i", vo]
        parts.append(f"[{n}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                     "loudnorm=I=-22:TP=-2:LRA=11,aresample=48000,volume=2dB,asplit=2[vomix][vokey]")
        parts.append(f"[world]apad=whole_dur={dur:.3f},atrim=0:{dur:.3f}[world_pad]")
        parts.append("[world_pad][vokey]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=380[wd]")
        parts.append(f"[vomix][wd]amix=inputs=2:normalize=0:dropout_transition=0:duration=longest,{tail}")

    else:
        parts.append(f"[world]{tail}")
    r = subprocess.run(cmd + ["-filter_complex", ";".join(parts), "-map", "[out]",
                              "-c:a", "pcm_s16le", "-ar", "48000", out])
    if r.returncode:
        sys.exit("ffmpeg failed")
    print(f"wrote {out}  ({dur:.2f}s, {n} cues{', with voice' if vo else ''})")


def selfcheck():
    lines = [{"id": "01", "start": "0.0"}, {"id": "02", "start": "4.5"}]
    words = [{"start": "0.1", "word": "भारत"}, {"start": "1.0", "word": "1906"},
             {"start": "5.0", "word": "1906।"}]
    r = Resolver(lines, words)
    assert r("12.5") == 12.5 and r("@02") == 4.5 and r("@02-0.2") == 4.3
    assert r("1906") == 1906.0           # a bare number is seconds
    assert r("w:1906") == 1.0
    assert r("w:1906+0.3") == 1.3        # same word again: the search does not skip ahead
    r.pos += 1
    assert r("w:1906") == 5.0            # punctuation is ignored
    assert Resolver(lines, words)("भारत-0.05") == 0.05
    try:
        os.environ["MIX_STRICT"] = "1"
        r("नहींमिला")
        raise AssertionError("missing word must fail")
    except SystemExit:
        pass
    finally:
        os.environ.pop("MIX_STRICT", None)
    assert start_time(5.0, 0.3, "sfx/StableAudio/Paper/page_turn_a.mp3") == 4.7          # peak on the word
    assert start_time(5.0, 0.762, "sfx/StableAudio/Numbers/b5_odometer_roll_a.mp3") == 5.0  # counter: starts on it
    assert start_time(5.0, 1.258, "sfx\\StableAudio\\Data\\b3_money_counter_a.mp3") == 5.0
    print("selfcheck ok")


def auto_generate_cues(out_path="cues.tsv", edit_file="EDIT.json", lines_file="VO.tsv", words_file="WORDS.tsv", style=None):
    """Automatically generates cues.tsv with matching background music bed and foley SFX:
    - Analyzes EDIT.json (or VO.tsv) to detect video style and timeline structure
    - Selects fitting background music bed from audio/music/
    - Adds ducked transition whooshes/sweeps at scene transitions
    - Adds paper slides / pops for cutout asset entrances
    - Adds odometer rolls for number counters / stats
    - Adds stamp press SFX for stamps / seals
    - Adds pin drops for maps and callouts
    """
    import json
    spec = {}
    if os.path.exists(edit_file):
        try:
            with open(edit_file, encoding="utf-8") as f:
                spec = json.load(f)
        except Exception:
            pass

    st = (style or spec.get("style", "documentary")).lower()

    # Select background music bed
    if any(k in st for k in ("noir", "crime", "suspense")):
        bed = "audio/music/crime_and_suspense/mystery_ambient.mp3"
    elif any(k in st for k in ("tech", "box", "editorial")):
        bed = "audio/music/tech_and_corporate/tech_modern.mp3"
    elif any(k in st for k in ("stickman", "cute", "fast", "action")):
        bed = "audio/music/epic_and_action/Energetic_Drum_Background_Music_NO_COPYRIGHT_Action_Drums_Background.mp3"
    else:
        bed = "audio/music/documentary_and_history/ES_Desert Whispers - Tellsonic.mp3"

    rows = []
    # 1. Background Music Bed (ducked under VO and SFX)
    rows.append({
        "label": "bed",
        "kind": "loop",
        "file": bed,
        "at": "0.0",
        "dur": "all",
        "gain_db": "-20",
        "fade_in": "1.0",
        "fade_out": "2.0"
    })

    # 2. Build Foley Cues from scenes / items or lines
    scenes = spec.get("scenes", [])
    if scenes:
        for i, sc in enumerate(scenes):
            sc_cue = sc.get("at") or sc.get("cue") or f"@{i+1:02d}"
            # Transition sound on scene entrance
            if i == 0:
                rows.append({
                    "label": "intro_subdrop",
                    "kind": "one",
                    "file": "audio/sfx/transition/b2_sub_drop_a.mp3",
                    "at": sc_cue,
                    "dur": "",
                    "gain_db": "-16",
                    "fade_in": "0",
                    "fade_out": "0"
                })
            else:
                sfx_trans = (
                    "audio/sfx/transition/b4_sweep_up_h.mp3",
                    "audio/sfx/transition/b4_riser_short_g.mp3",
                    "audio/sfx/transition/b4_shimmer_g.mp3"
                )[i % 3]
                rows.append({
                    "label": f"trans_{i+1:02d}",
                    "kind": "one",
                    "file": sfx_trans,
                    "at": sc_cue,
                    "dur": "",
                    "gain_db": "-18",
                    "fade_in": "0",
                    "fade_out": "0"
                })

            for item in sc.get("items", []):
                t = item.get("type", "")
                at = item.get("cue") or item.get("at") or sc_cue
                if t in ("asset", "cutout"):
                    rows.append({
                        "label": f"cut_{len(rows):02d}",
                        "kind": "one",
                        "file": "audio/sfx/paper/b3_cutout_slide_a.mp3",
                        "at": at,
                        "dur": "",
                        "gain_db": "-16",
                        "fade_in": "0",
                        "fade_out": "0"
                    })
                elif t in ("photo", "polaroid", "card"):
                    rows.append({
                        "label": f"photo_{len(rows):02d}",
                        "kind": "one",
                        "file": "audio/sfx/paper/b3_photo_drop_a.mp3",
                        "at": at,
                        "dur": "",
                        "gain_db": "-15",
                        "fade_in": "0",
                        "fade_out": "0"
                    })
                elif t in ("counter", "numeral", "chart"):
                    rows.append({
                        "label": f"counter_{len(rows):02d}",
                        "kind": "one",
                        "file": "audio/sfx/ui/b5_odometer_roll_a.mp3",
                        "at": at,
                        "dur": "",
                        "gain_db": "-16",
                        "fade_in": "0",
                        "fade_out": "0"
                    })
                elif t in ("stamp", "seal"):
                    rows.append({
                        "label": f"stamp_{len(rows):02d}",
                        "kind": "one",
                        "file": "audio/sfx/paper/b4_stamp_press_j.mp3",
                        "at": at,
                        "dur": "",
                        "gain_db": "-14",
                        "fade_in": "0",
                        "fade_out": "0"
                    })
                elif t in ("callout", "pin"):
                    rows.append({
                        "label": f"pin_{len(rows):02d}",
                        "kind": "one",
                        "file": "audio/sfx/map/drop_001.ogg",
                        "at": at,
                        "dur": "",
                        "gain_db": "-15",
                        "fade_in": "0",
                        "fade_out": "0"
                    })
                elif t in ("note", "sticky", "tag"):
                    rows.append({
                        "label": f"note_{len(rows):02d}",
                        "kind": "one",
                        "file": "audio/sfx/paper/b4_postit_flip_a.mp3",
                        "at": at,
                        "dur": "",
                        "gain_db": "-16",
                        "fade_in": "0",
                        "fade_out": "0"
                    })
    elif os.path.exists(lines_file):
        lines = tsv(lines_file)
        for i, l in enumerate(lines):
            cid = l.get("id", f"{i+1:02d}")
            if i == 0:
                rows.append({
                    "label": "intro_subdrop",
                    "kind": "one",
                    "file": "audio/sfx/transition/b2_sub_drop_a.mp3",
                    "at": f"@{cid}",
                    "dur": "",
                    "gain_db": "-16",
                    "fade_in": "0",
                    "fade_out": "0"
                })
            else:
                sfx = ("audio/sfx/transition/b4_sweep_up_h.mp3", "audio/sfx/paper/b3_cutout_slide_a.mp3")[i % 2]
                rows.append({
                    "label": f"sfx_{cid}",
                    "kind": "one",
                    "file": sfx,
                    "at": f"@{cid}",
                    "dur": "",
                    "gain_db": "-18",
                    "fade_in": "0",
                    "fade_out": "0"
                })

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "kind", "file", "at", "dur", "gain_db", "fade_in", "fade_out"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Auto-generated sound design cues -> {out_path} ({len(rows)} cues with ducked BGM and Foley SFX)")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cues", nargs="?")
    ap.add_argument("--vo", help="narration wav")
    ap.add_argument("--lines", help="VO.tsv (id, start, dur, text) for @NN cues")
    ap.add_argument("--words", help="WORDS.tsv from align.py, for word cues")
    ap.add_argument("--out", default="mix.wav")
    ap.add_argument("--dur", type=float, help="mix length (default: voice + 1.0 s)")
    ap.add_argument("--dip", help="seconds or a cue: dip the bed here for a held breath")
    ap.add_argument("--autocues", action="store_true", help="auto-generate cues.tsv from EDIT.json or VO.tsv")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    if a.autocues or (not a.cues and not os.path.exists("cues.tsv")):
        cues_path = a.cues or "cues.tsv"
        auto_generate_cues(out_path=cues_path, lines_file=a.lines or "VO.tsv", words_file=a.words or "WORDS.tsv")
        if a.autocues and not a.vo:
            return
    cues_file = a.cues or "cues.tsv"
    if not os.path.exists(cues_file):
        auto_generate_cues(out_path=cues_file, lines_file=a.lines or "VO.tsv", words_file=a.words or "WORDS.tsv")
    res = Resolver(tsv(a.lines) if a.lines else None, tsv(a.words) if a.words else None)
    cues = tsv(cues_file)
    cat = catalog()
    for c in cues:
        c["t"] = res(c["at"])
        peak, offset = cat.get(c["file"].replace("\\", "/"), (0.0, 0.0))
        c["gain_db"] = str(float(c["gain_db"]) + offset)    # kit-standard level, whatever the file
        if c["kind"] == "one":
            c["t"] = start_time(c["t"], peak, c["file"])
    dur = a.dur or ((media_len(a.vo) + 1.0) if a.vo else max(c["t"] for c in cues) + 5)
    dip = Resolver(tsv(a.lines) if a.lines else None, tsv(a.words) if a.words else None)(a.dip) \
        if a.dip else None
    build(cues, a.vo, a.out, dur, dip)


if __name__ == "__main__":
    main()
