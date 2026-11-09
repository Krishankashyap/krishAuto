#!/bin/sh
# setup_mobile.sh — 1-Command Automated Setup for Android (Termux) & Linux/macOS
# Sets up ffmpeg, python, dependencies, rules, hooks, and skills with zero bloat.

set -e

echo "===================================================================="
echo "  🚀 DEEPESH MOBILE STUDIO (v3) — UNIVERSAL MOBILE & DESKTOP INSTALLER"
echo "===================================================================="

STUDIO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$STUDIO_DIR"

# 1. Check if running in Termux vs Non-Termux
if [ -d "/data/data/com.termux" ]; then
    echo "✓ Detected Termux environment on Android."
    echo "Updating Termux packages..."
    pkg update -y
    echo "Installing core dependencies (ffmpeg, python, clang, libjpeg-turbo, freetype)..."
    pkg install -y ffmpeg python clang libjpeg-turbo freetype
else
    echo "✓ Linux / Desktop environment detected."
    mkdir -p "$HOME/.local/bin"
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) export PATH="$HOME/.local/bin:$PATH" ;;
    esac
fi

# 2. Install lightweight Python dependencies
echo "Installing lightweight Python dependencies..."
python3 -m pip install --upgrade pip --break-system-packages 2>/dev/null || python3 -m pip install --upgrade pip 2>/dev/null || true
python3 -m pip install --break-system-packages pillow numpy scipy soundfile faster-whisper opencv-python-headless static_ffmpeg 2>/dev/null || python3 -m pip install pillow numpy scipy soundfile faster-whisper opencv-python-headless static_ffmpeg 2>/dev/null || true

# 3. Ensure native ffmpeg and ffprobe are available
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
    echo "Fetching static ffmpeg & ffprobe binaries..."
    python3 -c "import static_ffmpeg; static_ffmpeg.add_paths()" || true
    FF_BIN="$(python3 -c "import static_ffmpeg, shutil; static_ffmpeg.add_paths(); print(shutil.which('ffmpeg') or '')")"
    FP_BIN="$(python3 -c "import static_ffmpeg, shutil; static_ffmpeg.add_paths(); print(shutil.which('ffprobe') or '')")"
    if [ -n "$FF_BIN" ] && [ -f "$FF_BIN" ]; then
        ln -sf "$FF_BIN" "$HOME/.local/bin/ffmpeg"
    fi
    if [ -n "$FP_BIN" ] && [ -f "$FP_BIN" ]; then
        ln -sf "$FP_BIN" "$HOME/.local/bin/ffprobe"
    fi
fi

# 4. Register Gemini & Claude Directorial Rules into Workspace & System
echo "Registering Conversational Intake Rules & Agent Directives..."
for rule_file in GEMINI.md AGENTS.md AGENT.md SKILL.md CLAUDE.md CREATIVE_DIRECTOR.md; do
    if [ -f "$STUDIO_DIR/$rule_file" ] && [ ! -f "$PWD/$rule_file" ]; then
        cp "$STUDIO_DIR/$rule_file" "$PWD/$rule_file"
    fi
done

# Register rules into Gemini / Antigravity global rule paths if directory exists
if [ -d "$HOME/.gemini" ]; then
    mkdir -p "$HOME/.gemini/antigravity"
    mkdir -p "$HOME/.gemini/config/plugins/deepx-flow/rules"
    mkdir -p "$HOME/.gemini/config/rules"
    cp "$STUDIO_DIR/GEMINI.md" "$HOME/.gemini/config/plugins/deepx-flow/rules/GEMINI.md" 2>/dev/null || true
    cp "$STUDIO_DIR/AGENTS.md" "$HOME/.gemini/config/plugins/deepx-flow/rules/AGENTS.md" 2>/dev/null || true
    cp "$STUDIO_DIR/GEMINI.md" "$HOME/.gemini/config/rules/GEMINI.md" 2>/dev/null || true
    echo "✓ Registered 7-Step Conversational Intake Rules into ~/.gemini"
fi

# 5. Register Skills into Gemini Skills Directory
if [ -d "$HOME/.gemini/config" ]; then
    mkdir -p "$HOME/.gemini/config/skills/xdeepfreevideogeneration"
    mkdir -p "$HOME/.gemini/config/skills/claude-video-prompt-builder"
    cp "$STUDIO_DIR/SKILL.md" "$HOME/.gemini/config/skills/xdeepfreevideogeneration/SKILL.md" 2>/dev/null || true
    if [ -d "$STUDIO_DIR/skills/claude-video-prompt-builder" ]; then
        cp -r "$STUDIO_DIR/skills/claude-video-prompt-builder/"* "$HOME/.gemini/config/skills/claude-video-prompt-builder/" 2>/dev/null || true
    fi
    echo "✓ Registered skills (xdeepfreevideogeneration, claude-video-prompt-builder) into ~/.gemini/config/skills"
fi

# 6. Install Flow Guard Hook for Claude Code & Antigravity
if [ -f "$STUDIO_DIR/hooks/install_guard.py" ]; then
    echo "Installing Flow Guard hook to prevent unusual-activity stops..."
    python3 "$STUDIO_DIR/hooks/install_guard.py" || true
fi

# 7. Run self-checks
echo "\nRunning engine selfcheck & feature test suite..."
python3 "$STUDIO_DIR/scripts/test_all_features.py"
python3 "$STUDIO_DIR/studio.py" selftest --quick

echo "\n===================================================================="
echo "🎉 SETUP COMPLETE! Deepesh Mobile Studio v3 is 100% operational."
echo "   All 7-Step Conversational Intake Rules are active."
echo "   To start: python3 mobile_run.py OR python3 studio.py new <path>"
echo "===================================================================="
