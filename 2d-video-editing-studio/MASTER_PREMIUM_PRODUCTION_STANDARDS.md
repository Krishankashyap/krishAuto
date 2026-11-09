# 👑 Master Premium Production & Editorial Standard (V4.0)
### The 10 Inviolable Laws of Broadcast-Grade Video, Typography, Overlays & Motion Design

Every video created by Antigravity—whether documentary, stickman explainer, crime thriller, or vertical short—must look like an agency-produced, broadcast-grade masterwork. Every asset, typography layer, animation curve, overlay, and audio transition must strictly adhere to the **10 Inviolable Laws**:

---

## 🏛️ Law 1: 100% Semantic Word-Locked Explanation (Zero Decorative Filler)
- **Direct Literal & Thematic Mapping**: Visuals must never be decorative "eyecandy" or disconnected stock illustrations. Every single image, prop, sticker, diagram, and card must explain, demonstrate, or dramatize the exact words being spoken in the voiceover at that microsecond.
- **Cognitive Clarity**: If the narrator mentions *"Amygdala triggers panic in 3 seconds"*, the screen shows an illuminated brain alarm graphic, an animated analog clock sweeping 3 seconds, and a distressed `"ALARM DISARMED"` stamp.
- **Zero Vague Shapes**: Never draw primitive lines or abstract placeholders when an authentic visual Twin can be generated on Google Flow.

---

## 🎨 Law 2: Organic Word-to-Word Asset Selection & Directorial Intelligence (No Rigid Quotas)
- **Script & Voiceover Driven (Not Compulsory 100 Assets)**: Asset count is never artificially forced to 100 or any arbitrary number. Visual assets are formulated strictly and organically according to the **script, narrative pacing, and word-for-word voiceover**.
- **Senior Editor & Directorial Logic**: Antigravity thinks and directs like an elite Senior Video Editor, Motion Designer, and Lead Content Creator:
  - Select assets with creative intelligence and narrative logic—extracting the underlying metaphor, psychological tension, forensic clue, emotional beat, or visual punchline directly from the voiceover.
  - Never spam meaningless icons or clutter the screen just to hit an arbitrary number.
  - Zero Visual Starvation: Maintain continuous, engaging visual progression where every key spoken phrase is creatively and purposefully illustrated.
- **5-Layer Depth Stacking**: Every scene orchestrates up to 5 clean, uncluttered visual layers:
  - *Layer 1*: Atmospheric Living Canvas (Full-bleed Mode A image or warm `#F8F6EF` paper with Ken Burns drift)
  - *Layer 2*: Secondary Contextual Props & Blueprint Grids
  - *Layer 3*: Primary Hero Subject / Character Cutout on Chroma Key
  - *Layer 4*: Tactile Badges, emphasis marks (max 2 rubber stamps per video; seal / tape / scrawl / tab otherwise) & Pinned Note Cards
  - *Layer 5*: Kinetic Subtitles & Animated Typography

---

## 🔤 Law 3: Premium Editorial Typography & Zero Hairline/Clipping Bugs
- **Heavyweight Static Typography Only**: Strictly banned are thin variable font fallbacks. Antigravity uses curated, high-density static fonts:
  - **Anton-Regular**: Giant headline reveals, forensic rubber stamps, high-impact titles.
  - **Khand-Bold**: Powerful, condensed Devanagari (Hindi) and English investigative statements.
  - **Baloo2-ExtraBold**: Friendly, rounded punchy stickman callouts.
  - **LiberationSans-Bold**: Sharp technical badges and analytical labels.
  - **Aquawax-Black / Space Mono**: Monospaced timecodes, coordinates, and case file IDs.
- **Dynamic Multi-Line Auto-Wrapping & Scaling**: Text strings automatically split across balanced lines with no underscores (`_`). Font size scales down dynamically (`while text_size > max: font_size -= 3`) guaranteeing zero text clipping regardless of screen resolution.
- **Curated Gradient Palettes with Specular Highlights**:
  - *Blood Crimson*: `#B71C1C -> #D32F2F` with top bevel rim light
  - *Fiery Sunset*: `#FF5722 -> #FF9800`
  - *Cyber Cyan*: `#00BCD4 -> #0097A7`
  - *Gold Luxury*: `#FFD54F -> #FF8F00`
  - *Royal Purple*: `#7B1FA2 -> #AB47BC`

---

## 📐 Law 4: Spatial Hierarchy, Composition Grids & 3-Layer Parallax
- **12-Column Grid & Rule of Thirds**: Focal subjects anchor on vertical power points ($x = 0.33$ or $x = 0.67$), leaving the opposite side for typography or secondary props.
- **Mode B Balanced Duets**: When pairing a character/subject with a stamp or card, place the subject at $x = 0.32$ (left) and the stamp/card at $x = 0.72$ (right). Never stack stamps directly on top of the character's face.
- **Camera Breathing & Parallax**: Continuous, subtle Ken Burns push-in (`1.0 -> 1.06`) combined with micro-harmonic organic drift (`dy = 2.4*sin`, `dx = 1.2*cos`) gives every frame a breathing cinematic feel without nervous jitter.

---

## 🛡️ Law 5: Zero-Collision Geometry & Vertical Clearance Enclosure
- **Non-Zero Bounding Boxes**: Every card, stamp, badge, and graphic must declare true geometric bounds in `geometry()` so subtitle and label layout engines can compute clearances.
- **45–55px Subtitle Clearance**: Subtitle labels (`LBL`, `PIN`, `TAG`) rendered below cards, stamps, and graphics must maintain a strict 45–55px vertical buffer. Text never collides or overlaps with graphic borders.

---

## 🌑 Law 6: Natural Soft Shadows (v3) & Physical Skeuomorphism
- **Physical Depth**: every cut-out, card, label and character casts a NATURAL shadow:
  - *Contact tier*: tight and slightly darker, right under the edge where the object touches the surface.
  - *Ambient tier*: wide, soft, lighter, offset in the light direction.
  - Warm near-black tint (`#1A1410`), never pure black; total opacity capped at ~0.5.
  - The canvas is padded by 3.2x the blur radius, so the shadow fades to exactly zero. **A shadow with a hard straight
    edge is a bug** (the v2 "sharp cut" shadow). Use `kit.shadow()`; standing figures also get `kit.ground_shadow()`.
- **Tactile Details**: realistic pushpins, procedural ink wear and bleed on stamps and seals, torn tape ends.

## ⏱️ Law 7: 0.000s Audio-Visual Attack Synchronization (Strict Attack Law)
- **Dead Air Elimination (`core/strict_sync.py`)**: All leading TTS digital silence is physically trimmed down to sample 0. **Audio Sample 0 (first spoken consonant) == Video Frame 0**.
- **Instant Opacity Onset**: All entrance animations (`pop`, `stamp`, `sketch`, `slide`) initiate with `opacity = 1.0` on the exact frame of attack ($t = 0$), completely eliminating sluggish opacity dissolve lag.
- **Acoustic Activity Alignment**: Spoken words are bound strictly within active acoustic bursts via FFmpeg `silencedetect`, preventing words from drifting into silent breath pauses.

---

## 📱 Law 8: Mobile Safe Zones (1080x1920) & Desktop Framing (1920x1080)
- **Mobile Safe Zone Guard**:
  - *Top Margin*: `160px` (clears camera notch, status bar, search header).
  - *Bottom Margin*: `300px` (clears TikTok/Reels caption marquee, account handle, audio track).
  - *Right Margin*: `130px` (clears like, comment, share, bookmark button stack).
  - *Left Margin*: `40px` (edge safety padding).
- All key typography, forensic stamps, and focal action remain locked inside this safe zone.

---

## 🔊 Law 9: Broadcast Audio Engineering (-14 LUFS with Voice Ducking)
- **Voiceover is Supreme**: Voiceover audio is calibrated to broadcast speech loudness.
- **Dynamic Music Ducking (`core/mix.py`)**: Background music tracks duck to $-18\text{dB}$ during active vocal bursts and smoothly ramp back up during natural multi-second narrative pauses.
- **Tactile Foley & SFX**: Every visual event has a dedicated sound counterpart:
  - Stamp slam $\to$ 30Hz sub-bass thud (`boom_sub.wav`).
  - Card entrance $\to$ crisp paper whoosh (`paper_slide.wav`).
  - Clocks $\to$ ticking clock riser (`clock_tick.wav`).
  - Warning/Error $\to$ cinematic tension drone or analog buzz.

---

## 🍌 Law 10: Mandatory Google Flow Asset Engine & Zero Dummy Shapes
- **Exclusive Cloud Visual Engine**: All image cutouts, scene illustrations, characters, and evidence props are generated using Google Flow (`🍌 Nano Banana 2.1` / `🍌 Nano Banana Pro` / `Imagen 3`).
- **Chroma Key Integrity**: Cutouts are generated on flat pure magenta `#FF00FF` and keyed via `core/key.py` with physical alpha edge recovery.
- **Bridge Disconnection Verification**: Always verify `deepx_status` before production. If disconnected, pause and proactively guide the user to connect rather than silently falling back to crude local shapes.

---

## 🎨 Law 11 (v3): Creative Variety, Never a Template
- Every design motif has a per-video budget (rubber stamp ≤ 2, seal ≤ 1, tape / scrawl / tab ≤ 3).
- No two neighbouring beats share an emphasis design, kicker design, layout or entrance.
- Choose the emphasis that MEANS the word (see CREATIVE_DIRECTOR.md §2). Numbers get counters, not stamps.
- Case-file / question tags render ≥ 46 px at 1080p.
- `studio.py check` prints the design-variety report; `core/engine/variety.py` enforces the budget.
