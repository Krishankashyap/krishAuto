# -*- coding: utf-8 -*-
"""voice.py: LINES.tsv -> VO.wav + VO.tsv + WORDS.tsv with EXACT word timings.

Sync is what makes an edit feel professional: a visual that lands 0.3 s after its word
reads as sloppy. So word times are never guessed here:

  * every line is synthesised through Cartesia's SSE endpoint with `add_timestamps`,
    which returns the true start/end of every spoken word (measured: the old
    syllable-weight estimate drifted up to 0.41 s = 10 frames)
  * leading silence is trimmed and the timestamps are shifted by exactly the trimmed amount
  * lines are joined with each line's `gap`; all times are absolute in VO.wav
  * WORDS.tsv gets a `src` column: `cartesia` (exact) or `estimate` (fallback only if the
    API returned no timestamps -- `studio.py check` warns about any estimated line)

usage:  CARTESIA_API_KEY=sk_car_... python core/voice.py [--voice anuj] [--lang hi] [--speed 1.0] [--force]
Per-line results are cached in vo_parts/ (audio + timestamps), so re-runs only fetch missing lines.
"""
import argparse, base64, csv, json, os, re, subprocess, sys, time, urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartesia_tts import resolve_emotions, resolve_voice_id, API_VERSION, BASE_URL  # noqa: E402

SR = 44100


def synth_line(text, voice_id, lang, emotion, key, model="sonic-3.6"):
    """Returns (float32 mono audio, [(word, start, end), ...]) for one line."""
    vd = {"mode": "id", "id": voice_id}
    em = resolve_emotions(emotion)
    if em:
        vd["__experimental_controls"] = {"emotion": em}
    payload = {"model_id": model, "transcript": text.strip(), "voice": vd, "language": lang,
               "output_format": {"container": "raw", "encoding": "pcm_f32le", "sample_rate": SR},
               "add_timestamps": True}
    req = urllib.request.Request(f"{BASE_URL}/tts/sse", data=json.dumps(payload).encode(), headers={
        "X-API-Key": key, "Cartesia-Version": API_VERSION, "Content-Type": "application/json"})
    raw = urllib.request.urlopen(req, timeout=90).read().decode("utf-8")
    audio, words = bytearray(), []
    for line in raw.splitlines():
        if not line.startswith("data:"):
            continue
        ev = json.loads(line[5:])
        if ev.get("type") == "error":
            raise RuntimeError(ev.get("error") or ev)
        if ev.get("data"):
            audio += base64.b64decode(ev["data"])
        wt = ev.get("word_timestamps")
        if wt:
            words += list(zip(wt["words"], wt["start"], wt["end"]))
    return np.frombuffer(bytes(audio), np.float32), words


def trim_bounds(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return 0, len(a)
    return max(0, idx[0] - int(0.02 * SR)), min(len(a), idx[-1] + int(0.08 * SR))


def estimate(text, dur):
    toks = text.split()
    wts = [max(1, len(re.sub(r"[^\w]", "", w))) + 1.5 for w in toks]
    out, c = [], 0.0
    for w, wt in zip(toks, wts):
        d = dur * wt / sum(wts)
        out.append((w, c, c + d))
        c += d
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="anuj")
    ap.add_argument("--lang", default="hi")
    ap.add_argument("--emotion", default="neutral")
    ap.add_argument("--key", default=os.environ.get("CARTESIA_API_KEY"))
    ap.add_argument("--speed", type=float, default=1.0, help="tempo factor applied after synthesis (0.9-1.1)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--jobs", type=int, default=2, help="parallel requests (2 is safe on the free tier)")
    a = ap.parse_args()
    if not a.key:
        sys.exit("Set CARTESIA_API_KEY or pass --key (free key: play.cartesia.ai -> API Keys)")
    rows = list(csv.DictReader(open("LINES.tsv", encoding="utf-8"), delimiter="\t"))
    os.makedirs("vo_parts", exist_ok=True)
    vid = resolve_voice_id(a.voice, a.key)
    def fetch(r):
        pa, pj = f"vo_parts/{r['id']}.f32", f"vo_parts/{r['id']}.json"
        if os.path.exists(pa) and os.path.exists(pj) and not a.force:
            return None
        for attempt in range(5):
            try:
                audio, words = synth_line(r["text"], vid, a.lang, a.emotion, a.key)
                open(pa, "wb").write(audio.tobytes())
                json.dump({"text": r["text"], "words": words}, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
                print(f"  ✓ line {r['id']}  {len(audio) / SR:.1f}s  {len(words)} timed words", flush=True)
                return None
            except Exception as ex:                       # rate limit / network: back off and retry
                print(f"  retry line {r['id']}: {ex}", flush=True)
                time.sleep(2 * (attempt + 1))
        return r["id"]

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max(1, a.jobs)) as pool:      # 2 requests at a time: ~2x faster, below the free-tier limit
        failed = [x for x in pool.map(fetch, rows) if x]
    if failed:
        sys.exit(f"line(s) {', '.join(failed)} failed 5 times -- check the key / quota, then re-run (finished lines are cached)")

    out, vo, words, t, est_lines = [], [], [], 0.0, []
    for r in rows:
        x = np.fromfile(f"vo_parts/{r['id']}.f32", np.float32)
        meta = json.load(open(f"vo_parts/{r['id']}.json", encoding="utf-8"))
        s, e = trim_bounds(x)
        x = x[s:e]
        off = s / SR
        d = len(x) / SR
        vo.append((r["id"], t, t + d, r["text"]))
        timed = meta["words"]
        src = "cartesia"
        if not timed or meta.get("text") != r["text"]:
            timed, src = estimate(r["text"], d), "estimate"
            est_lines.append(r["id"])
            off = 0.0
        for i, (w, ws, we) in enumerate(timed):
            ws = min(max(0.0, ws - off), d)
            we = min(max(ws, we - off), d)
            words.append((r["id"], i, t + ws, t + we, w, src))
        gap = float(r.get("gap") or 0.35)
        out += [x, np.zeros(int(gap * SR), np.float32)]
        t += d + gap
    audio = np.concatenate(out)
    audio = audio / max(1e-6, float(np.abs(audio).max())) * 0.89
    import soundfile as sf
    sf.write("VO.wav", audio, SR, subtype="PCM_16")
    if abs(a.speed - 1.0) > 1e-3:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "VO.wav", "-filter:a", f"atempo={a.speed}", "_vo.wav"], check=True)
        os.replace("_vo.wav", "VO.wav")
        vo = [(i, s / a.speed, e / a.speed, x) for i, s, e, x in vo]
        words = [(l, i, s / a.speed, e / a.speed, w, src) for l, i, s, e, w, src in words]
        t /= a.speed
    with open("VO.tsv", "w", encoding="utf-8") as f:
        f.write("id\tstart\tend\ttext\n" + "".join(f"{i}\t{s:.3f}\t{e:.3f}\t{x}\n" for i, s, e, x in vo))
    with open("WORDS.tsv", "w", encoding="utf-8") as f:
        f.write("line\tword_idx\tstart\tend\tword\tsrc\n" +
                "".join(f"{l}\t{i}\t{s:.3f}\t{e:.3f}\t{w}\t{src}\n" for l, i, s, e, w, src in words))
    print(f"✓ VO.wav {t:.1f}s · {len(vo)} lines · {len(words)} words · "
          + ("all word times exact (Cartesia timestamps)" if not est_lines else f"⚠ estimated timing on lines {', '.join(est_lines)}"))


if __name__ == "__main__":
    main()
