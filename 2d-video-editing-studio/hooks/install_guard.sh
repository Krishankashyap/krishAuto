#!/data/data/com.termux/files/usr/bin/sh
# Install the Flow guard hook into your USER-level Claude Code settings (~/.claude/settings.json)
# so it applies in every folder, not only when Claude Code is started inside this studio.
# Existing settings are kept; a backup is written to ~/.claude/settings.json.bak
STUDIO="$(cd "$(dirname "$0")/.." && pwd)"
python3 - "$STUDIO" <<'PY'
import json, os, sys, shutil
studio = sys.argv[1]
p = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
cfg = json.load(open(p)) if os.path.exists(p) else {}
if os.path.exists(p): shutil.copy(p, p + ".bak")
proj = json.load(open(os.path.join(studio, ".claude", "settings.json")))
hooks = cfg.setdefault("hooks", {})
for ev, entries in proj["hooks"].items():
    lst = [e for e in hooks.get(ev, []) if "flow_guard_hook.py" not in json.dumps(e)]
    for e in entries:
        e = json.loads(json.dumps(e).replace("$CLAUDE_PROJECT_DIR", studio))
        lst.append(e)
    hooks[ev] = lst
json.dump(cfg, open(p, "w"), indent=2)
print("Flow guard hook installed in", p)
PY
