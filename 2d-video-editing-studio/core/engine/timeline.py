# -*- coding: utf-8 -*-
"""timeline.py: word timings (WORDS.tsv), cue resolution and caption phrasing.

Cue syntax (used by EDIT.json "at"/"until"):
   12.4        absolute seconds
   @05         start of VO line 05
   @05+0.4     ... shifted
   राणा         first spoken word CONTAINING "राणा", searched forward from the previous cue
   राणा+0.3     same, shifted by +0.3 s (negative leads)
   w:1906      a spoken word that is itself a number
"""
import csv, os, re

PUNCT = re.compile(r"[।॥?,.!\"'“”‘’:;—–\-…()\[\]]")


class Timeline:
    """lead: visuals fire this many seconds BEFORE their word (editors cut slightly ahead of the
    sound so the eye arrives with the ear; 2 frames at 24 fps by default)."""
    def __init__(self, words_tsv="WORDS.tsv", lead=0.08):
        self.words = []  # (line, start, end, raw, clean)
        self.estimated_lines = set()
        self.lead = lead
        if os.path.exists(words_tsv):
            with open(words_tsv, encoding="utf-8") as f:
                for r in csv.DictReader(f, delimiter="\t"):
                    clean = PUNCT.sub("", r["word"])
                    self.words.append((r["line"], float(r["start"]), float(r["end"]), r["word"], clean))
                    if r.get("src", "estimate") != "cartesia":
                        self.estimated_lines.add(r["line"])
        self.ptr = 0

    def lines(self):
        out = {}
        for w in self.words:
            a = out.setdefault(w[0], [w[1], w[2]])
            a[0], a[1] = min(a[0], w[1]), max(a[1], w[2])
        return out

    def end(self):
        return self.words[-1][2] if self.words else 0.0

    def resolve(self, cue, default=None, advance=True):
        if cue in (None, "", "-"):
            return default
        if isinstance(cue, (int, float)):
            return float(cue)
        cue = str(cue).strip()
        shift = 0.0
        m = re.match(r"^(.*?)([+-]\d+(?:\.\d+)?)$", cue)
        if m and m.group(1) and not re.fullmatch(r"-?\d+(\.\d+)?", cue):
            cue, shift = m.group(1), float(m.group(2))
        if re.fullmatch(r"\d+(\.\d+)?", cue):
            return float(cue) + shift
        if cue.startswith("@"):
            for k, w in enumerate(self.words):
                if w[0] == cue[1:]:
                    if advance:
                        self.ptr = k
                    return max(0.0, w[1] + shift - self.lead)
            raise SystemExit(f"cue {cue!r}: no VO line with that id")
        target = PUNCT.sub("", cue[2:] if cue.startswith("w:") else cue)
        order = list(range(self.ptr, len(self.words))) + list(range(0, self.ptr))
        for k in order:
            if target and target in self.words[k][4]:
                if advance:
                    self.ptr = k
                return max(0.0, self.words[k][1] + shift - self.lead)
        raise SystemExit(f"cue {cue!r} not found in the voiceover words")

    def phrases(self, max_chars=34, max_words=6, min_gap=0.35):
        """Group words into caption phrases: break on punctuation, pauses, line ends, length."""
        out, cur = [], []
        for i, w in enumerate(self.words):
            cur.append(w)
            nxt = self.words[i + 1] if i + 1 < len(self.words) else None
            text_len = sum(len(x[4]) + 1 for x in cur)
            brk = (nxt is None or nxt[0] != w[0] or nxt[1] - w[2] > min_gap
                   or re.search(r"[।?!,…—]$", w[3]) or len(cur) >= max_words or text_len >= max_chars)
            if brk:
                out.append({"words": [(x[3].strip(), x[1], x[2]) for x in cur],
                            "start": cur[0][1], "end": cur[-1][2]})
                cur = []
        for a, b in zip(out, out[1:]):  # hold each phrase until the next one (max 0.6 s of air)
            a["hold"] = min(b["start"], a["end"] + 0.6)
        if out:
            out[-1]["hold"] = out[-1]["end"] + 1.0
        return out
