# Registers a folder as an Obsidian vault so "obsidian://open?vault=<name>" can open it.
# Usage: obsidian_register.py <vault folder>. Config path override: OBSIDIAN_CONFIG (tests).
import json, os, secrets, sys, time

vault = os.path.abspath(sys.argv[1])
if os.environ.get("OBSIDIAN_CONFIG"):
    cfg_path = os.environ["OBSIDIAN_CONFIG"]
elif os.name == "nt":
    cfg_path = os.path.join(os.environ["APPDATA"], "obsidian", "obsidian.json")
else:
    cfg_path = os.path.expanduser("~/Library/Application Support/obsidian/obsidian.json")

cfg = {}
if os.path.exists(cfg_path):
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
vaults = cfg.setdefault("vaults", {})
same = [k for k, v in vaults.items() if os.path.normcase(os.path.abspath(v.get("path", ""))) == os.path.normcase(vault)]
for v in vaults.values():
    v.pop("open", None)
key = same[0] if same else secrets.token_hex(8)
vaults[key] = {"path": vault, "ts": int(time.time() * 1000), "open": True}
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f)
print("Obsidian: folder registered")
