# -*- coding: utf-8 -*-
"""dedupe_guard.py: Bulletproof Universal Asset Registry & Anti-Duplication Engine.

Enforces ZERO duplicate generation across Google Flow, DeepX Bridge, and all studio pipelines.
Checks:
  Tier 1: Keyed cutout in elements/cut/<name>.png
  Tier 2: Raw render in elements/raw/<name>.* (case-insensitive, size > 1024)
  Tier 3: Auto-harvest from Chrome Downloads / project folders
  Tier 4: Project flow_manifest.json (done, dup, inflight)
  Tier 5: elements/registry.json
"""
import glob
import hashlib
import json
import os
import re
import shutil
import time

RAW_DIR = "elements/raw"
CUT_DIR = "elements/cut"
MANIFEST_PATH = "flow_manifest.json"
REGISTRY_PATH = "elements/registry.json"


def resolve_asset_name(item):
    """Cleanly extracts the asset name from a row dict, string, or id."""
    if isinstance(item, dict):
        return str(item.get("name") or item.get("id") or "").strip()
    return str(item).strip()


def get_manifest():
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("jobs", {})
        except Exception:
            return {}
    return {}


def save_manifest(jobs):
    tmp = MANIFEST_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"jobs": jobs}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, MANIFEST_PATH)


def get_registry():
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_registry(reg):
    os.makedirs(os.path.dirname(REGISTRY_PATH) or ".", exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)


def get_download_candidates():
    project_folder = re.sub(r"[^A-Za-z0-9_-]+", "_", os.path.basename(os.getcwd())).strip("_").lower() or "voxdoc"
    dl_base = os.path.expanduser("~/Downloads")
    candidates = [
        dl_base,
        os.path.join(dl_base, project_folder),
        os.path.join(dl_base, f"{project_folder}_props"),
        os.path.join(dl_base, "deepx_renders"),
        os.path.join(dl_base, "deepx_renders", project_folder),
    ]
    if os.environ.get("FLOW_DOWNLOADS"):
        candidates.insert(0, os.environ["FLOW_DOWNLOADS"])
    try:
        candidates.extend(glob.glob(os.path.join(dl_base, "*", "")))
    except Exception:
        pass
    return [os.path.abspath(c) for c in candidates if os.path.isdir(c)]


def harvest_single_asset(name):
    """Searches download folders for any file matching name or name (1).* and copies to elements/raw."""
    os.makedirs(RAW_DIR, exist_ok=True)
    exts = (".png", ".webp", ".jpg", ".jpeg", ".PNG", ".WEBP", ".JPG", ".JPEG")
    candidates = get_download_candidates()
    escaped_name = re.escape(name)
    pat = re.compile(rf"^{escaped_name}(?:\s*\(\d+\))?(?:_\d+)?\.(?:png|webp|jpg|jpeg)$", re.IGNORECASE)

    for dl in candidates:
        if not os.path.exists(dl):
            continue
        try:
            for fname in os.listdir(dl):
                if pat.match(fname):
                    src = os.path.join(dl, fname)
                    if os.path.isfile(src) and os.path.getsize(src) > 1024:
                        dst = os.path.join(RAW_DIR, f"{name}.png")
                        try:
                            from PIL import Image
                            im = Image.open(src).convert("RGB")
                            im.save(dst, "PNG")
                            mark_asset_completed(name, file_path=dst)
                            return dst
                        except Exception:
                            shutil.copy2(src, dst)
                            mark_asset_completed(name, file_path=dst)
                            return dst
        except Exception:
            continue
    return None


def is_asset_ready(asset_item, auto_harvest=True):
    """Comprehensive multi-tier readiness check."""
    name = resolve_asset_name(asset_item)
    if not name:
        return "MISSING"

    # Tier 1: Keyed transparent cutouts
    cut_file = os.path.join(CUT_DIR, f"{name}.png")
    if os.path.exists(cut_file) and os.path.getsize(cut_file) > 1024:
        return "KEYED_READY"

    # Tier 2: Raw images
    for ext in (".png", ".webp", ".jpg", ".jpeg", ".PNG", ".WEBP", ".JPG", ".JPEG"):
        raw_file = os.path.join(RAW_DIR, f"{name}{ext}")
        if os.path.exists(raw_file) and os.path.getsize(raw_file) > 1024:
            return "RAW_EXISTS"

    # Tier 3: Auto-harvest from Chrome Downloads
    if auto_harvest:
        harvested = harvest_single_asset(name)
        if harvested and os.path.exists(harvested) and os.path.getsize(harvested) > 1024:
            return "HARVESTED_READY"

    # Tier 4: Manifest check
    man = get_manifest()
    if name in man:
        st = man[name].get("status")
        fpath = man[name].get("file")
        if st in ("done", "dup") and fpath and os.path.exists(fpath) and os.path.getsize(fpath) > 1024:
            return "MANIFEST_READY"
        if st == "inflight":
            t_sent = man[name].get("t", 0)
            if time.time() - t_sent < 300:
                return "IN_FLIGHT"

    # Tier 5: Registry check
    reg = get_registry()
    if name in reg and reg[name].get("status") in ("QUEUED", "DISPATCHED"):
        t_sent = reg[name].get("t", 0)
        if time.time() - t_sent < 300:
            return "IN_FLIGHT"

    return "MISSING"


def register_dispatched(asset_item, prompt, job_id=None):
    """Registers an asset as in-flight in both manifest and registry."""
    name = resolve_asset_name(asset_item)
    now = int(time.time())
    h = hashlib.sha1(prompt.strip().encode("utf-8")).hexdigest()[:16]

    # Save to manifest
    man = get_manifest()
    entry = man.setdefault(name, {})
    entry.update({"status": "inflight", "hash": h, "job": job_id, "t": now, "prompt": prompt[:120]})
    save_manifest(man)

    # Save to registry
    reg = get_registry()
    reg[name] = {"status": "DISPATCHED", "prompt_hash": h, "job": job_id, "t": now, "prompt": prompt[:120]}
    save_registry(reg)


def mark_asset_completed(asset_item, file_path=None):
    """Marks an asset as done in both manifest and registry."""
    name = resolve_asset_name(asset_item)
    now = int(time.time())
    actual_file = file_path
    if not actual_file:
        cut = os.path.join(CUT_DIR, f"{name}.png")
        if os.path.exists(cut):
            actual_file = cut
        else:
            for ext in (".png", ".webp", ".jpg", ".jpeg"):
                p = os.path.join(RAW_DIR, f"{name}{ext}")
                if os.path.exists(p):
                    actual_file = p
                    break

    man = get_manifest()
    entry = man.setdefault(name, {})
    entry.update({"status": "done", "file": actual_file, "t": now})
    save_manifest(man)

    reg = get_registry()
    entry_r = reg.setdefault(name, {})
    entry_r.update({"status": "COMPLETED", "file": actual_file, "t": now})
    save_registry(reg)


def get_pending_assets(elements_rows, auto_harvest=True):
    """Returns only assets that are truly MISSING. Skips any ready or in-flight asset."""
    pending = []
    for r in elements_rows:
        name = resolve_asset_name(r)
        state = is_asset_ready(r, auto_harvest=auto_harvest)
        if state == "MISSING":
            pending.append(r)
        else:
            print(f"  [✓] {name}: Skipped (status: {state})")
    return pending
