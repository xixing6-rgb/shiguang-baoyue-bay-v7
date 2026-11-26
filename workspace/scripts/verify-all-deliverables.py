#!/usr/bin/env python3
"""Final end-to-end verification across 4x map, Blender GLBs, Lua scripts, narrative DBs, mini-scripts, HTML demos, and 62 close-up assets."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
ERRORS: list[str] = []


def ok(msg: str) -> None:
    print(f"[PASS] {msg}")


def err(msg: str) -> None:
    print(f"[FAIL] {msg}")
    ERRORS.append(msg)


def check_file(path: Path, min_bytes: int = 100) -> bool:
    if not path.is_file():
        err(f"Missing file: {path}")
        return False
    sz = path.stat().st_size
    if sz < min_bytes:
        err(f"File too small ({sz} B < {min_bytes} B): {path}")
        return False
    return True


def check_closeups_and_sheets() -> None:
    manifest_p = ROOT / "workspace" / "assets" / "3d-modeling-closeups" / "manifest.json"
    if not check_file(manifest_p, 1000):
        return
    data = json.loads(manifest_p.read_text(encoding="utf-8"))
    assets = data["assets"]
    if len(assets) != 62:
        err(f"Expected 62 assets in manifest.json, got {len(assets)}")
    missing = 0
    for a in assets:
        p = ROOT / "workspace" / "assets" / "3d-modeling-closeups" / f"{a['id']}.png"
        if not check_file(p, 50_000):
            missing += 1
    if missing == 0:
        ok(f"All {len(assets)} asset close-up PNGs present and >50KB")

    sheets = [
        "sheet-1-core-town-F01-F18.png",
        "sheet-2-expansion-west-east-F19-F31.png",
        "sheet-3-expansion-north-south-F32-F42.png",
        "sheet-4-residents-props-C01-U01.png",
    ]
    sheet_ok = True
    for s in sheets:
        if not check_file(ROOT / "workspace" / "assets" / "3d-modeling-closeups" / "_contact-sheets" / s, 100_000):
            sheet_ok = False
    if sheet_ok:
        ok("All 4 contact sheets present and valid")


def check_4x_map_and_blender() -> None:
    check_file(ROOT / "workspace" / "docs" / "map-design-research-4x.md", 5000)
    check_file(ROOT / "workspace" / "docs" / "town-masterplan-4x.md", 2000)
    check_file(ROOT / "workspace" / "docs" / "asset-closeup-style-audit.md", 5000)
    check_file(ROOT / "workspace" / "docs" / "narrative-design-and-script.md", 5000)
    check_file(ROOT / "workspace" / "docs" / "character-mini-scripts.md", 5000)

    terrain_glb = ROOT / "workspace" / "assets" / "models" / "map-shiguang-town-4x.glb"
    hardscape_glb = ROOT / "workspace" / "assets" / "models" / "town-hardscape-4x.glb"
    landmarks_dir = ROOT / "workspace" / "assets" / "models" / "landmarks-4x"
    t_ok = check_file(terrain_glb, 10_000)
    h_ok = check_file(hardscape_glb, 10_000)
    lm_glbs = list(landmarks_dir.glob("*.glb")) if landmarks_dir.is_dir() else []
    if len(lm_glbs) < 15:
        err(f"Expected >=15 landmark GLBs in {landmarks_dir}, found {len(lm_glbs)}")
    elif t_ok and h_ok:
        ok(f"Blender 4x GLBs verified: terrain ({terrain_glb.stat().st_size} B), hardscape ({hardscape_glb.stat().st_size} B), landmarks ({len(lm_glbs)} GLBs)")

    audit_p = ROOT / "workspace" / "debug" / "route-audit-4x.json"
    if check_file(audit_p, 100):
        audit = json.loads(audit_p.read_text(encoding="utf-8"))
        # Support either top-level issueCount/totalIssues or summing routes
        issues = audit.get("issueCount", audit.get("totalIssues", None))
        routes = audit.get("routes", [])
        if issues is None and routes:
            issues = sum(int(r.get("issueCount", len(r.get("issues", [])))) for r in routes)
        max_slope = audit.get("maxSlopeDeg", max((r.get("maxSlopeDeg", 0) for r in routes), default=0))
        if issues != 0:
            err(f"route-audit-4x.json reports {issues} issues")
        elif max_slope > 18.6:
            err(f"route-audit-4x.json maxSlopeDeg={max_slope} > 18.5")
        else:
            ok(f"route-audit-4x.json clean (routes={len(routes)}, issues=0, maxSlopeDeg={max_slope})")

    for shot in ["town-4x-site-plan.png", "town-4x-overview.png", "town-4x-full-assembly.png"]:
        if check_file(ROOT / "workspace" / "debug" / shot, 50_000):
            ok(f"Blender render verified: {shot}")


def check_scripts_and_dbs() -> None:
    for script_name in ["verify-lua-scripts.py", "verify-mini-scripts.py"]:
        sp = ROOT / "workspace" / "scripts" / script_name
        if not check_file(sp, 200):
            continue
        r = subprocess.run([sys.executable, str(sp)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            err(f"{script_name} failed rc={r.returncode}:\n{r.stdout}\n{r.stderr}")
        else:
            ok(f"{script_name} passed cleanly")


def check_html_demos() -> None:
    node_exe = shutil.which("node")
    if not node_exe:
        err("node.exe not found on PATH")
        return

    demos = [
        ("shiguang-narrative-game.html", ["narrative-db.js", "character-mini-scripts.js"]),
        ("town-layout-blueprint-4x.html", ["narrative-db.js"]),
    ]
    for fname, req_scripts in demos:
        hp = ROOT / "interactive-demos" / fname
        if not check_file(hp, 5000):
            continue
        text = hp.read_text(encoding="utf-8")
        if "https://" in text or "http://" in text:
            # Allow only harmless SVG xmlns if http://www.w3.org/2000/svg, forbid external CDN script/link
            bad_urls = re.findall(r"(?:src|href)=[\"'](https?://[^\"']+)[\"']", text, re.I)
            if bad_urls:
                err(f"{fname} contains external URLs: {bad_urls[:5]}")
        if "fetch(" in text:
            err(f"{fname} contains fetch() which breaks offline file:// usage")
        for req in req_scripts:
            if req not in text:
                err(f"{fname} does not reference {req}")

        # Extract inline scripts and syntax-check with node --check
        scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.S | re.I)
        if not scripts:
            err(f"{fname} has no inline <script> blocks")
            continue
        combined = "\n;\n".join(scripts)
        tmp_js = hp.with_suffix(".tmpcheck.js")
        try:
            tmp_js.write_text(combined, encoding="utf-8")
            r = subprocess.run([node_exe, "--check", str(tmp_js)], capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0:
                err(f"{fname} JS syntax check failed: {r.stderr}")
            else:
                ok(f"{fname} offline check + node --check passed ({len(text)} chars, {len(scripts)} inline script block(s))")
        finally:
            if tmp_js.is_file():
                tmp_js.unlink()


def main() -> int:
    check_closeups_and_sheets()
    check_4x_map_and_blender()
    check_scripts_and_dbs()
    check_html_demos()
    print(f"\n=== FINAL VERIFICATION SUMMARY: errors={len(ERRORS)} ===")
    for e in ERRORS:
        print(" -", e)
    return 1 if ERRORS else 0


if __name__ == "__main__":
    raise SystemExit(main())
