#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/fetch_full_audio.py: Desktop Extended Audio Archive Fetcher.

Downloads optional extended 400MB full-fidelity music archive for desktop
workstations while keeping the mobile package featherlight (<15MB).
"""

import os
import sys
import urllib.request
import zipfile

ARCHIVE_URL = "https://github.com/kaomei/vox-audio-archive/releases/download/v1.0/vox_extended_audio.zip"

def main():
    print("=" * 60)
    print("  XDeepFreeVideoGeneration Extended Audio Fetcher")
    print("=" * 60)
    print("Note: The core package already includes essential high-retention")
    print("music beds and the complete SFX sound library for full production.")
    print(f"Target URL: {ARCHIVE_URL}")
    print("\nIf you are on desktop and wish to download the 400MB library,")
    print("ensure you have sufficient bandwidth and run with --confirm.")
    
    if "--confirm" not in sys.argv:
        print("\nAborted. To proceed with desktop download, run:")
        print("    python scripts/fetch_full_audio.py --confirm")
        return

    dest = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audio")
    os.makedirs(dest, exist_ok=True)
    zip_path = os.path.join(dest, "extended_audio.zip")
    print(f"Downloading archive to {zip_path}...")
    try:
        urllib.request.urlretrieve(ARCHIVE_URL, zip_path)
        print("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest)
        os.remove(zip_path)
        print("✓ Successfully installed extended audio library!")
    except Exception as e:
        print(f"Notice: Remote archive unavailable or offline ({e}).")
        print("The standard curated mobile audio pack is ready and active.")

if __name__ == "__main__":
    main()
