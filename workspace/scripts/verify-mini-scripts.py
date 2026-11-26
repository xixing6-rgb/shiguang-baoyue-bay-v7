#!/usr/bin/env python3
"""Verify character-mini-scripts.json and .js against platform & animation constraints."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import shutil


ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
JSON_PATH = ROOT / "workspace" / "data" / "character-mini-scripts.json"
JS_PATH = ROOT / "workspace" / "data" / "character-mini-scripts.js"

ALLOWED_ACTIONS = {
    "walk", "run", "greet", "wave", "sit", "clap", "cheer", "dance", "photo", "water_bend",
    "turn_to_player", "hop_bounce", "nod_tilt", "hover_bob", "door_open", "pivot_spin", "paper_pet_squash",
}
ALLOWED_BUBBLES = {"none", "bubble_yellow", "bubble_orange", "bubble_pink", "bubble_purple"}
ALLOWED_FX = {"none", "fx_heart", "fx_sparkle", "fx_petal", "fx_ripple", "fx_firefly"}
ALLOWED_SFX = {"voice_soft", "voice_mech"}


def check_line(line: dict, ctx: str, errors: list[str], lengths: list[int]) -> None:
    text = line.get("text", "")
    lengths.append(len(text))
    if not (10 <= len(text) <= 36):
        errors.append(f"{ctx}: line length {len(text)} out of [10,36]: {text!r}")
    if line.get("action") not in ALLOWED_ACTIONS:
        errors.append(f"{ctx}: invalid action {line.get('action')!r}")
    if line.get("bubble") not in ALLOWED_BUBBLES:
        errors.append(f"{ctx}: invalid bubble {line.get('bubble')!r}")
    if line.get("fx") not in ALLOWED_FX:
        errors.append(f"{ctx}: invalid fx {line.get('fx')!r}")
    if line.get("sfx") not in ALLOWED_SFX:
        errors.append(f"{ctx}: invalid sfx {line.get('sfx')!r}")


def main() -> int:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    chars = data["characters"]
    duos = data["duoEncounters"]
    errors: list[str] = []
    lengths: list[int] = []
    episode_count = 0

    if len(chars) != 9:
        errors.append(f"Expected 9 characters, got {len(chars)}")

    for c in chars:
        cid = c["id"]
        scripts = c["scripts"]
        if len(scripts) != 3:
            errors.append(f"{cid}: expected 3 stage scripts, got {len(scripts)}")
        for ep in scripts:
            episode_count += 1
            sid = ep["scriptId"]
            for i, ln in enumerate(ep["lines"], 1):
                check_line(ln, f"{sid}.lines[{i}]", errors, lengths)
            choice = ep.get("choice", {})
            opts = choice.get("options", [])
            if len(opts) != 2:
                errors.append(f"{sid}: expected 2 choice options, got {len(opts)}")
            for oi, opt in enumerate(opts, 1):
                lbl = opt.get("label", "")
                if len(lbl) > 14:
                    errors.append(f"{sid}.opt[{oi}] label too long ({len(lbl)}): {lbl!r}")
                if opt.get("affectionDelta", 0) <= 0:
                    errors.append(f"{sid}.opt[{oi}] non-positive affectionDelta")
                for ri, rln in enumerate(opt.get("replyLines", []), 1):
                    check_line(rln, f"{sid}.opt[{oi}].reply[{ri}]", errors, lengths)

    if len(duos) != 3:
        errors.append(f"Expected 3 duo encounters, got {len(duos)}")
    for d in duos:
        did = d["scriptId"]
        for i, ln in enumerate(d["lines"], 1):
            check_line(ln, f"{did}.lines[{i}]", errors, lengths)
        for oi, opt in enumerate(d.get("choice", {}).get("options", []), 1):
            if len(opt.get("label", "")) > 14:
                errors.append(f"{did}.opt[{oi}] label too long")
            for ri, rln in enumerate(opt.get("replyLines", []), 1):
                check_line(rln, f"{did}.opt[{oi}].reply[{ri}]", errors, lengths)

    # Check JS loadable via Node
    node_exe = shutil.which("node")
    if node_exe:
        probe = (
            "const fs = require('fs'); const vm = require('vm');"
            f"const code = fs.readFileSync({json.dumps(str(JS_PATH))}, 'utf8');"
            "const sandbox = { window: {} }; vm.runInNewContext(code, sandbox);"
            "const d = sandbox.window.SHIGUANG_MINI_SCRIPTS;"
            "if (!d || d.characters.length !== 9 || d.duoEncounters.length !== 3) process.exit(2);"
            "console.log('NODE_MINI_JS_OK', d.characters.length, d.duoEncounters.length);"
        )
        res = subprocess.run([node_exe, "-e", probe], capture_output=True, text=True, encoding="utf-8")
        print(res.stdout.strip())
        if res.returncode != 0:
            errors.append(f"Node eval failed: {res.stderr}")

    print(f"Characters={len(chars)}, PersonalEpisodes={episode_count}, DuoEncounters={len(duos)}, TotalLines={len(lengths)}, LineLen=[{min(lengths)}..{max(lengths)}]")
    print(f"Errors={len(errors)}")
    for e in errors[:20]:
        print("  ERR:", e)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
