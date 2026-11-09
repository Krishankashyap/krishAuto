# 📱 Deepesh Mobile Studio — v2 engine

> **New in v2:** slot-based layouts (nothing overlaps), real Devanagari typography with karaoke captions, five style packs
> (noir · cinematic · documentary · sticker · box), camera moves and transitions, parallel rendering, a structured prompt
> engine (one detailed master prompt per visual beat), exact Cartesia word-timestamp sync, and paced Google Flow
> generation (one prompt at a time,1.5 s apart, stops on "unusual activity"). Start with **ENGINE_V2.md**, and run `python studio.py selftest` once on each machine.

```bash
python studio.py new ~/videos/my_video && cd ~/videos/my_video
python studio.py voice && python studio.py plan && python studio.py prompts && python studio.py generate && python studio.py key
python studio.py check && python studio.py sheet && python studio.py render
```

---

## 🧩 Install as an AntiGem Plugin

You can install **2D Video Editing Studio** directly inside the **AntiGem** app:

1. Open **AntiGem**.
2. Go to **Settings → Custom AutoKrish Plugins → Repositories**.
3. Add this repository:
   ```
   Dipeshkrydv/2d-video-editing-skill
   ```
   *(or `https://github.com/Dipeshkrydv/2d-video-editing-skill`)*
4. Browse the repository plugins and click **Install** on **2D Video Editing Studio**.
5. All 26 autonomous skills, styles, fonts, and engines will be installed instantly with automatic updates!

---

## 🌟 Key Features & Innovations

### 1. 📱 Android Mobile First (Termux Optimized)
- **1-Command Mobile Setup (`setup_mobile.sh`)**: Automatically configures FFmpeg, Python, Pillow, NumPy, and SoundFile with zero bloat.
- **Turnkey CLI Pipeline (`mobile_run.py`)**: Run speech alignment, audio mixing, and video rendering with a single command.
- **Android Low Memory Killer (LMK) Protection**: Throttles memory footprint (<150 MB peak RAM) and clamps workers to prevent Termux crashes on mobile phones.
- **Mobile Safe-Zone Guard (1080x1920)**: Automatically keeps all kinetic text, forensic stamps, and graphic callouts inside safe areas—clear of camera notches, status bars, and TikTok/Reels UI buttons.

### 2. 🍌 Mandatory Google Flow Asset Engine & Bridge Protocol
- **Exclusive Cloud Visual Engine**: Generates isolated character cutouts, stickmen, scene illustrations, and props via Google Flow (`🍌 Nano Banana 2.1` / `🍌 Nano Banana Pro` / `Imagen 3`) on solid `#FF00FF` magenta with lossless alpha unmixing.
- **Disconnection Alert Law**: Before generating assets, the system verifies the DeepX Flow Bridge connection (`deepx_status`). If disconnected, it safely pauses and prompts you to connect Google Flow rather than producing crude local dummy shapes.

### 3. ⏱️ 0.000s Audio-Visual Attack Sync Engine
- **Physical Dead-Air Stripping (`core/strict_sync.py`)**: Automatically strips leading digital silence down to audio sample 0, locking **Audio Sample 0 (0.000s)** directly to **Video Frame 0**.
- **Acoustic Activity Detection**: Isolates vocal bursts and breath pauses with FFmpeg `silencedetect`, preventing words from drifting into silent pauses.
- **Instant Frame 0 Opacity**: In-animations attack immediately at `opacity = 1.0` on the onset frame without laggy opacity fade-ins.

### 4. 🎨 Editorial Kinetic Typography & Curated Display Fonts
- **Variable Font Fix**: Bundles curated static bold typography (`Anton-Regular.ttf`, `Khand-Bold.ttf`, `Baloo2-ExtraBold.ttf`, `LiberationSans-Bold.ttf`, `Aquawax-Black.ttf`), eliminating variable font hairline rendering bugs.
- **Dynamic Text Auto-Fitting**: Intelligent multi-line word wrapping and font scaling guarantee zero text clipping across any screen resolution.
- **Gradient Headline Reveals**: Fiery red-orange, royal purple, electric cyan, sunset, and gold gradient typography with dual-tier drop shadows.
- **Tactile Forensic Elements**: Distressed classified evidence stamps with auto-scaling ink borders, realistic pushpinned gradient cards, and animated analog clocks with sweep sectors.

---

## 🚀 Quick Start Guide

### Option A: Turnkey Setup on Android Phone (Termux)
1. Extract the package on your phone:
   ```bash
   termux-setup-storage
   cd ~/storage/shared/Download
   unzip "deepesh mobile studio.zip" -d deepesh_mobile_studio
   cd deepesh_mobile_studio
   ```
2. Run the automated installer:
   ```bash
   sh setup_mobile.sh
   ```
3. Run the full mobile video production pipeline:
   ```bash
   python3 mobile_run.py
   ```
4. Preview the resulting video directly in your gallery:
   ```bash
   termux-open master.mp4
   ```

---

### Option B: Desktop / Standard CLI Workflow
1. **Prerequisites**: Ensure `ffmpeg` and Python 3.10+ are installed.
2. **Align Spoken Words to Audio**:
   ```bash
   python3 core/strict_sync.py --vo VO.wav --lines LINES.tsv --words-out WORDS.tsv --vo-out VO.tsv
   ```
3. **Verify Plan & Layout**:
   ```bash
   python3 core/render.py selfcheck
   python3 core/render.py plan
   ```
4. **Render Video Shots**:
   ```bash
   python3 core/render.py shots
   ```
5. **Mix Ducked Broadcast Audio (-14 LUFS)**:
   ```bash
   python3 core/mix.py cues.tsv --vo VO.wav --words WORDS.tsv --lines VO.tsv --out mix.wav
   ```
6. **Assemble Final Master Video**:
   ```bash
   python3 core/render.py master
   ```

---

## 📁 Directory Architecture

```
deepesh_mobile_studio/
├── README.md               # Complete documentation and quickstart
├── MOBILE_GUIDE.md         # Dedicated Android Termux optimization guide
├── SETUP.md                # System packages and installation guide
├── AGENT.md                # Full autonomous production director laws
├── SKILL.md                # Agent skill manifest & tool reference
├── mobile_run.py           # Turnkey 1-command mobile video generator
├── setup_mobile.sh         # Termux automated package installer
├── master.mp4              # Verified full-length assembled master video
├── VO.wav                  # Master voiceover track
├── LINES.tsv               # Spoken script lines with scene IDs
├── WORDS.tsv               # 0ms aligned word timing database
├── SCENES.tsv              # Visual shot choreographies and compositions
├── cues.tsv                # Sound design, SFX, and ducking cue sheet
├── ELEMENTS.tsv            # Google Flow prompt registry
├── labels.ass              # Substation Alpha kinetic typography subtitles
├── core/                   # Core animation, typography, and sync engine
│   ├── strict_sync.py      # Sample-0 dead air trimming and speech alignment
│   ├── render.py           # Video compositor, clocks, stamps, and layout engine
│   ├── motion_mix.py       # Pinned cards, gradients, and font resolver
│   ├── kinetic_text.py     # Subtitle generator and baseline mask animator
│   ├── mix.py              # Broadcast audio ducking and SFX mixer
│   ├── key.py              # Magenta chroma-keying with alpha edge recovery
│   └── trends.py           # Real-time multi-platform trend scanner
├── fonts/                  # Curated static bold fonts (Anton, Khand, Baloo2, etc.)
├── audio/                  # Broadcast Foley SFX and royalty-free music beds
├── templates/              # Starter project templates
└── shots/                  # Rendered shot clips
```

---

## 📄 License & Credits
Built for high-retention video creators by Deepesh. Free and open for personal and commercial production.
