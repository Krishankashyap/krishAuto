# Setup & System Prerequisites — Deepesh Mobile Studio

## 1. System Packages (Linux / macOS / WSL)
Ensure ffmpeg and font utilities are installed:
```bash
sudo apt update && sudo apt install -y ffmpeg fonts-noto-core fonts-noto-ui-core
```

## 2. Android Phone (Termux) Automated Setup
On Android Termux, simply run:
```bash
sh setup_mobile.sh
```
This automatically installs `ffmpeg`, `python3`, `clang`, `libjpeg-turbo`, `freetype`, `pillow`, `numpy`, and `soundfile`.

## 3. Python Dependencies
Install required Python libraries:
```bash
pip install --upgrade pip
pip install pillow numpy scipy soundfile faster-whisper
```

## 4. Google Flow Bridge Connection
Verify DeepX Flow Bridge MCP connection:
- Ensure Google Chrome (or Kiwi Browser on Android) is running with `flow.google.com` open.
- The DeepX bridge listens on `ws://127.0.0.1:8792/ws`.
- Check status via the `deepx_status` tool.

## 5. Engine Verification Check
Run self-check on the core engine components:
```bash
python3 core/render.py selfcheck
python3 core/mix.py --selfcheck
python3 core/cutout.py --demo
python3 core/key.py --demo
```
