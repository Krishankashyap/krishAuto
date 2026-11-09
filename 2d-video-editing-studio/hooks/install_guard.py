#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Install the Flow guard hook into your USER-level Claude Code settings (~/.claude/settings.json), so it applies in
every folder. Works on Windows, macOS, Linux and Termux (install_guard.sh is the Unix-only equivalent).
Existing settings are kept; a backup is written to settings.json.bak. Uses THIS Python's absolute path."""
import json, os, shutil, sys

studio = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
hook = os.path.join(studio, "hooks", "flow_guard_hook.py")
cmd = f'"{sys.executable}" "{hook}"'
path = os.path.expanduser(os.path.join("~", ".claude", "settings.json"))
os.makedirs(os.path.dirname(path), exist_ok=True)
cfg = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
if os.path.exists(path):
    shutil.copy(path, path + ".bak")
proj = json.load(open(os.path.join(studio, ".claude", "settings.json"), encoding="utf-8"))
hooks = cfg.setdefault("hooks", {})
for ev, entries in proj["hooks"].items():
    keep = [e for e in hooks.get(ev, []) if "flow_guard_hook.py" not in json.dumps(e)]
    for e in entries:
        e = json.loads(json.dumps(e))
        for h in e["hooks"]:
            h["command"] = cmd
        keep.append(e)
    hooks[ev] = keep
json.dump(cfg, open(path, "w", encoding="utf-8"), indent=2)
print("Flow guard hook installed in", path)
