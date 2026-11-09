# -*- coding: utf-8 -*-
"""mobile_config.py: Mobile-Responsive Architecture & Low-RAM Android Engine.

Provides unified screen geometry, safe-zone bounding checks (TikTok/Reels/Shorts UI),
responsive typography scaling, portable font discovery (Android /system/fonts, Termux, local),
and memory-safe worker/thread clamps for mobile devices.
"""

import os
import shutil
import sys
from typing import Tuple, Dict, Any, Optional

def is_mobile() -> bool:
    """Detects whether running on an Android / Termux or mobile environment."""
    if os.environ.get("IS_MOBILE") in ("1", "true", "True"):
        return True
    if os.environ.get("ANDROID_ROOT") or os.environ.get("ANDROID_DATA"):
        return True
    if os.path.exists("/data/data/com.termux"):
        return True
    if os.environ.get("TERMUX_VERSION"):
        return True
    return False

def get_aspect_ratio() -> str:
    """Resolves aspect ratio: mobile defaults to 9:16, desktop defaults to 16:9."""
    if os.environ.get("VOX_ASPECT"):
        return os.environ["VOX_ASPECT"]
    if os.environ.get("VOX_VERTICAL") == "1":
        return "9:16"
    if is_mobile():
        return "9:16"
    return "16:9"

def get_dimensions(aspect: Optional[str] = None) -> Tuple[int, int]:
    """Returns (W, H) for the given aspect ratio."""
    asp = aspect or get_aspect_ratio()
    if asp == "9:16":
        return 1080, 1920
    elif asp == "1:1":
        return 1080, 1080
    elif asp == "4:5":
        return 1080, 1350
    return 1920, 1080

class MobileSafeZone:
    """
    Mobile UI Safe Zone Manager.
    Guarantees text, forensic stamps, and hero elements never render
    underneath phone camera cutouts, top status bars, or social video UI
    overlays (Reels/TikTok/Shorts sound buttons, like columns, caption marquees).
    """
    def __init__(self, width: int = 1080, height: int = 1920, aspect: str = "9:16"):
        self.w = width
        self.h = height
        self.aspect = aspect
        self.is_vertical = (height > width)
        
        if self.is_vertical:
            # 9:16 Mobile Vertical Safe Margins (px)
            self.top = 160        # Status bar, notch, search, audio tag
            self.bottom = 300     # Caption text, account handle, audio marquee
            self.right = 130      # Like, comment, share, bookmark action rail
            self.left = 40        # Left margin padding
        else:
            # 16:9 Desktop / Landscape Safe Margins
            self.top = 60
            self.bottom = 100
            self.right = 60
            self.left = 60

        self.safe_w = self.w - self.left - self.right
        self.safe_h = self.h - self.top - self.bottom
        self.center_x = self.left + self.safe_w // 2
        self.center_y = self.top + self.safe_h // 2

    def clamp_x(self, x: float, half_w: float = 0.0) -> float:
        min_x = self.left + half_w
        max_x = (self.w - self.right) - half_w
        return max(min_x, min(max_x, x))

    def clamp_y(self, y: float, half_h: float = 0.0) -> float:
        min_y = self.top + half_h
        max_y = (self.h - self.bottom) - half_h
        return max(min_y, min(max_y, y))

    def clamp_box(self, cx: float, cy: float, w: float, h: float) -> Tuple[float, float, float, float]:
        clamped_x = self.clamp_x(cx, w / 2)
        clamped_y = self.clamp_y(cy, h / 2)
        return clamped_x, clamped_y, w, h

def get_responsive_scale(width: int, height: int) -> float:
    """Returns scaling multiplier for badges, typography, and props."""
    if height > width:
        # Vertical 9:16 phone screen
        return 1.30
    return 1.00

def get_safe_workers(requested: Optional[int] = None) -> int:
    """Returns safe parallel worker process count to prevent mobile OOM kills."""
    if requested is not None and requested > 0:
        return requested
    mobile = is_mobile()
    cpus = os.cpu_count() or 2
    if mobile:
        # On Android Termux: never exceed 1 worker (or 2 on high-core chipsets) to prevent lmkd SIGKILL
        return 1 if cpus <= 6 else 2
    else:
        return max(1, min(2, cpus // 2) if cpus <= 4 else min(4, cpus - 1))

def get_ffmpeg_threads() -> str:
    """Returns optimal FFmpeg thread count for current device."""
    mobile = is_mobile()
    cpus = os.cpu_count() or 2
    if mobile:
        return "2" if cpus >= 4 else "1"
    return "1" if cpus <= 4 else "2"

def resolve_font_path(font_name: str = "bold") -> str:
    """
    Portably searches for TrueType fonts across:
    1. Local package fonts/ folder
    2. Android /system/fonts/ (Roboto, NotoSans)
    3. Termux $PREFIX/share/fonts/
    4. Desktop Linux /usr/share/fonts/
    """
    candidates = []
    
    # 1. Project local fonts
    proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(proj_root, "fonts")
    if os.path.exists(fonts_dir):
        for root, _, files in os.walk(fonts_dir):
            for f in files:
                if f.endswith((".ttf", ".otf", ".TTF")):
                    candidates.append(os.path.join(root, f))
    
    # 2. Android system fonts
    android_fonts = [
        "/system/fonts/Roboto-Bold.ttf",
        "/system/fonts/Roboto-Medium.ttf",
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/NotoSansDevanagari-Bold.ttf",
        "/system/fonts/NotoSans-Bold.ttf"
    ]
    candidates.extend([f for f in android_fonts if os.path.exists(f)])
    
    # 3. Termux fonts
    termux_prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    termux_font_dir = os.path.join(termux_prefix, "share/fonts")
    if os.path.exists(termux_font_dir):
        for root, _, files in os.walk(termux_font_dir):
            for f in files:
                if f.endswith((".ttf", ".otf")):
                    candidates.append(os.path.join(root, f))

    # 4. Standard Linux fonts
    linux_fonts = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
    ]
    candidates.extend([f for f in linux_fonts if os.path.exists(f)])

    target = font_name.lower()
    for c in candidates:
        bname = os.path.basename(c).lower()
        if target in bname:
            return c
            
    # Default fallback to first found font or empty
    return candidates[0] if candidates else ""
