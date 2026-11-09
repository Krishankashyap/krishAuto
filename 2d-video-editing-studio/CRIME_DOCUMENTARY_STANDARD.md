# 🔍 Crime Documentary & Investigative Video Production Standard
### The Hybrid Architecture: Full-Bleed Scene Canvases + Isolated Evidence Cutouts + Kinetic Typography

Whenever a user requests a **Crime Documentary, True Crime Investigation, Murder Mystery, Noir Thriller, Police Procedural, or Suspense Case File video**, Antigravity strictly enforces the **Three-Pillar Crime Production Law**:

---

## 🏛️ Pillar 1: Whole Scene Images (WITHOUT Cutout) — Mode A Full-Bleed

- **What it covers**:
  - Establishing environmental shots, crime scenes, rain-slicked asphalt alleys, interrogation rooms, forensic autopsy suites, dimly lit police archive basements, shadowy courtrooms, aerial night cityscapes, CCTV surveillance grids, and archival crime photos.
- **Visual Aesthetic**:
  - **Full-Bleed Edge-to-Edge Frame**: Fills the entire 16:9 Landscape or 9:16 Vertical viewport.
  - **Cinematic Noir Realism**: Chiaroscuro lighting, deep atmospheric shadows, harsh amber streetlights reflecting in wet asphalt, cold steel-blue rim light, authentic 35mm film grain, and subtle smoke/fog haze.
  - **ZERO CUTOUT / ZERO MAGENTA**: Prompts for scene environments must NEVER use `#FF00FF` magenta. The prompt explicitly specifies an immersive, full-frame cinematic digital painting or photographic scene.
  - **Camera Motion**: Slow, continuous Ken Burns camera push-in (`1.0 -> 1.06`) or lateral tracking drift with subtle vignette breathing.

### Mode A Scene Prompt Example:
```text
Dark wet metropolitan alleyway at 3 AM in the pouring rain, yellow police caution tape stretching across aged brick walls, reflections of flashing red and blue police siren lights in pavement puddles, deep noir chiaroscuro shadows, steam rising from asphalt sewer grates, full-bleed edge-to-edge 16:9 cinematic environmental shot, richly detailed atmospheric crime scene filling the entire frame, seamless composition, zero cutout, no magenta, no borders, no frames, masterwork forensic documentary cinematography
```

---

## 🔬 Pillar 2: Cool Forensic Evidence in CUTOUT Style — Mode B Magenta Keying

- **What it covers**:
  - **Physical Weapons & Ballistics**: Bloodied hunting knife, revolver with filed-off serial numbers, spent 9mm brass casing, shattered glass bottle.
  - **Forensic Artifacts**: Yellow acrylic evidence tent marker `#01` or `#04`, transparent plastic evidence bag with barcode label, dusted latent fingerprint cards, forensic chemical test swabs, autopsy toxicology reports.
  - **Investigative Clues**: Taped Polaroid suspect portraits with metal paper clips, vintage micro-cassette tape recorder with spinning spools, classified manila dossier envelope tied with red string, FBI/Interpol investigator credentials, magnifying glass, tarnished handcuffs.
- **Visual Aesthetic**:
  - **Chroma Magenta Isolation**: Generated on solid flat pure chroma magenta `#FF00FF` via Google Flow (`🍌 Nano Banana 2.1` / `🍌 Nano Banana Pro` / `Imagen 3`).
  - **Lossless Alpha Unmixing**: Keyed cleanly via `core/key.py` into transparent PNGs with edge unmixing.
  - **Tactile 3D Compositing**: Layered directly **OVER** the full-bleed scene image with natural soft two-tier shadows (never clipped), spring pop-ins (`back_out`), subtle 3D rotational tilt (-4° to +6°), and metal pushpin effects.

### Mode B Evidence Cutout Prompt Example:
```text
Forensic yellow acrylic evidence tent marker numbered 04 sitting beside a spent 9mm brass bullet casing, dusted with black magnetic fingerprint powder, visible forensic scale measurement grid on the marker, one single isolated object, centred with a generous margin of empty space on all sides, on a solid flat pure chroma magenta background, uniform magenta hex #FF00FF filling the entire background and showing through every gap and opening, object contains zero magenta, hard crisp edges, sharply defined boundary, no drop shadow, no cast shadow, no blur, no text, no frame
```

---

## ⚡ Pillar 3: Cool Kinetic Typography & Forensic Edits

- **Case File Identifiers & Terminal Badges**:
  - High-impact monospaced headers rendered in **Space Mono** or **Courier Prime**:
    - `[CASE FILE #4092-CRIME // EVIDENCE ARCHIVE]`
    - `[DATE: 14 NOV // TIME: 03:42:15 AM // LOCATION: UNCONFIRMED]`
    - `[CLASSIFIED // TOP SECRET // DO NOT DISCLOSE]`
- **Redacted Classified Text Reveals**:
  - Solid black censor blocks (`████████████` or `[REDACTED]`) that slide away with an organic paper slice sound effect, revealing the hidden suspect name or covert location beneath.
- **Distressed Forensic Rubber Stamps (MAX 2 per video, v3)**: reserve them for the reveal and the verdict. Every other
  emphasis beat uses a different design: `seal` (official), `tape` (warning / NO BREAK-IN), `tab` (file / date), `scrawl`
  (the key point circled), a redaction, a counter or a callout. See CREATIVE_DIRECTOR.md.
  - Heavy bass-impact stamps with dynamic camera shake:
    - `EVIDENCE #01`, `CRIME SCENE`, `CONFIDENTIAL`, `PRIME SUSPECT`, `VERIFIED ALIBI`, `COLD CASE`, `CAUSE OF DEATH: UNKNOWN`.
  - Stamped in deep crimson red (`#C62828`) with procedural distressed ink erosion noise and double-line forensic borders.
- **Curated High-Impact Typography**:
  - **Anton-Regular**: Giant blood-red/fiery headline reveals (`THE MURDER WEAPON`, `THE ALIBI CRUMBLES`).
  - **Khand-Bold**: Heavyweight Hindi/Devanagari investigative statements with zero clipping.
  - **Gradient Palettes**: Crimson Blood (`#B71C1C -> #D32F2F`), Noir Cold Cyan (`#00BCD4 -> #0097A7`), or Caution Gold (`#FFD54F -> #FF8F00`).
- **Forensic Pointers & Connector Rules**:
  - Red investigative yarn lines, dashed vector arrows, and crosshair reticles connecting the evidence cutout to points of interest on the full background image.
