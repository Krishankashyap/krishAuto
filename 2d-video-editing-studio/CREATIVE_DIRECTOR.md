# CREATIVE_DIRECTOR.md — how to THINK about design (v3)

> Read this before writing any EDIT.json. It replaces "add a red stamp to every scene" with real editorial judgement.
> The engine enforces the hard limits automatically (`core/engine/variety.py`), but a great video comes from the
> agent planning variety on purpose, not from the engine cleaning up after it.

---

## 1. The problem v3 fixes

Real complaints from finished videos:

| what the viewer saw | why it hurts |
|---|---|
| CASE CLOSED · VERIFIED · NO STRUGGLE · MASS CASUALTY · UNSOLVED: **the same red rubber stamp 5-6 times** in one video | a motif repeated that often stops meaning "important" and starts meaning "template". Engagement drops every time it reappears |
| sticker / prop shadows with a **hard straight cut edge** | the blur was clipped by the sprite canvas. It reads as cheap cut-and-paste, not a real object on a surface |
| `CASE FILE #BUR-2018 // DELHI`, `BIG QUESTION` tags at **30 px** | a great font nobody can read on a phone is wasted |
| every scene built from the same recipe | the viewer's brain predicts the next frame and tunes out |

## 2. The five laws of creative variety

1. **Every design motif has a budget per video.** Repetition is allowed only as a deliberate *system* (chapter
   tags, captions), never as a crutch.

   | motif | max per video | notes |
   |---|---|---|
   | rubber stamp (slam + shake) | **2**, at least 3 scenes apart | the loudest hit. Save it for the reveal and the verdict |
   | seal (oval notary seal) | 1 | official / legal / sealed beats |
   | tape (label tape strip) | 3 | warnings, "NO BREAK-IN", facts that interrupt |
   | scrawl (handwritten word + pen loop) | 3 | an editor circling the point. Great on paper styles |
   | tab (manila index tab) | 3 | archival facts, dates, file references |
   | burst doodle / accent ticks | **2**, at least 3 scenes apart | radiating action burst ticks. Strict max 2 per video (never blanketed) |
   | circle / underline doodle accent | **2** | hand-drawn marker loop or squiggle accent |
   | same keyword box design | twice in a row: never | the engine rotates the style's `boxes` |
   | same entrance animation | 3 in a row: never | rise / pop / drop / slide / snap / fade |
   | same layout | back to back: never (except `clean`) | `check` warns |
   | same transition | the engine rotates the style's vocabulary | override per scene only with intent |

2. **No neighbours look alike.** Two consecutive emphasis beats, kickers, layouts or entrances never share a design.
3. **Emphasis is earned.** Before adding a stamp, ask: *is this the single most important word of the scene?* If
   not, use a keyword, a callout, a counter, a redaction, an arrow, or nothing. Silence is a design choice.
4. **Pick the emphasis that MEANS the word, not the first one you remember.**

   | the narration says... | best emphasis |
   |---|---|
   | a verdict / a reveal ("UNSOLVED", "GUILTY") | `rubber` stamp (max 2) or `redact` reveal |
   | an official status ("SEALED", "APPROVED", "OFFICIAL") | `seal` |
   | an interruption / a warning ("NO BREAK-IN", "DANGER") | `tape` |
   | the key idea of an explainer ("7 रंग", "ज़ोन 2") | `scrawl`, `keyword` marker, or `counter` |
   | a file / date / record ("FILE 2018/BUR") | `tab` or `kicker` |
   | a number | `counter`, `bigtext`, `chart`. Never a stamp |

5. **Physical things look physical.** Natural soft shadows (contact + ambient, warm-tinted, never clipped), a slight
   tilt on paper, a ground shadow under anything standing. No hard-edged shadow shapes, ever.

## 3. How the engine helps (and how to steer it)

`studio.py check` prints a **design variety** report:

```
design variety: emphasis rubber 2/2, seal 1/1, tape 1/3, scrawl 1/3, tab 1/3 · kickers 3 designs · transitions 4 kinds
   ↻ scene 02: stamp 'VERIFIED' re-designed as tab (rubber-stamp budget / no repeats)
```

* A `stamp` item WITHOUT `"design"` is a request for emphasis: the engine picks the family (style taste, budget,
  no neighbour repeats).
* `"design": "rubber" | "seal" | "tape" | "scrawl" | "tab"` forces a family. It still counts against the budget and
  `check` warns if you overspend.
* Kickers rotate through the style's tag designs (`bar`, `chip`, `bracket`, `rule`, `index`). The `index` design
  shows a running chapter number. Force one with `"design"` on the kicker, or a size with `"size"` (px at 1080p,
  default 46).
* `"variety": {"auto": false}` at the top of EDIT.json turns the automatic re-design off (report only).
  `"variety": {"budget": {"rubber": 1}}` tightens a budget.

## 4. A director's checklist for every scene (do this in your head before writing JSON)

1. **What is the ONE idea of this scene?** Everything on screen serves it.
2. **What did the previous two scenes look like?** Layout, colour block, emphasis, entrance. Choose something else.
3. **Which beat type fits the words?** Picture, number, comparison, list, map, quote, character moment, silence.
4. **Is there a human moment?** If the line is an explanation, an invitation ("चलो देखते हैं..."), or a reaction
   ("सोचिए...", "हैरानी की बात..."), consider the **character** (CHARACTER_MODE.md) instead of another stamp.
5. **Where does the eye go first, second and third?** Title → visual → emphasis. Never three things fighting.
6. **Is anything repeated from 30 seconds ago?** If yes, change it unless it is the video's deliberate system.

## 5. Before → after (same narration)

Before (v2: what made the video feel cheap):
```json
{"layout": "hero", "items": [{"type": "kicker", "text": "CASE FILE"}, {"type": "title", "text": "दरवाज़ा खुला था"},
  {"type": "asset", "name": "door"}, {"type": "stamp", "text": "NO BREAK-IN"}]}
{"layout": "hero", "items": [{"type": "kicker", "text": "CASE FILE"}, {"type": "title", "text": "11 लाशें"},
  {"type": "asset", "name": "mesh"}, {"type": "stamp", "text": "MASS CASUALTY"}]}
```
After (v3: same facts, three different design ideas):
```json
{"layout": "hero", "items": [{"type": "kicker", "text": "SANT NAGAR // HOUSE NO. 137"},
  {"type": "title", "text": "दरवाज़ा *खुला* था"}, {"type": "asset", "name": "door"},
  {"type": "stamp", "text": "NO BREAK-IN", "design": "tape"}]}
{"layout": "focus", "items": [{"type": "kicker", "text": "THE INNER HALL"},
  {"type": "photo", "src": "mesh", "slot": "center"},
  {"type": "counter", "from": 0, "to": 11, "slot": "r1"},
  {"type": "callout", "text": "लोहे का जाल", "point": [0.5, 0.3], "slot": "l1"}]}
{"layout": "presenter", "items": [{"type": "title", "text": "हर रात का *हिसाब*"},
  {"type": "asset", "name": "diary", "slot": "left"},
  {"type": "character", "cast": "host", "actions": [{"at": "हिसाब", "do": "point"}]}]}
```
