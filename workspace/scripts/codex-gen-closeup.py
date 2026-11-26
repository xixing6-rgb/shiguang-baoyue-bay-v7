#!/usr/bin/env python3
"""Generate clean studio-background 3D modeling close-ups via local Codex CLI image_gen."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


PROJECT_ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
MANIFEST_PATH = PROJECT_ROOT / "workspace" / "assets" / "3d-modeling-closeups" / "manifest.json"
OUT_DIR = PROJECT_ROOT / "workspace" / "assets" / "3d-modeling-closeups"
LOG_DIR = OUT_DIR / "_logs"
CODEX_GENERATED_ROOT = Path.home() / ".codex" / "generated_images"


def resolve_codex_argv() -> list[str]:
    npm_codex_js = Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
    node_exe = shutil.which("node")
    if npm_codex_js.is_file() and node_exe:
        return [node_exe, str(npm_codex_js)]
    codex_cmd = shutil.which("codex")
    if codex_cmd:
        return [codex_cmd]
    raise FileNotFoundError("Cannot locate codex CLI binary or codex.js")


def build_prompt(asset: dict, style_bible: dict, extra_fix: str | None) -> str:
    cat = asset["category"]
    refs = asset["refs"]
    ref_notes = []
    for idx, rkey in enumerate(refs, start=1):
        if rkey == "characters":
            ref_notes.append(
                f"Image {idx} (STYLE & PROPORTION REFERENCE ONLY): match ONLY the big-headed chibi rounded clay figurine proportions, smooth matte clay finish, minimal dark bead eyes (or horizontal deadpan line eyes for the tabby cat), and soft color palette. IGNORE all held props and tucked/folded arm poses in Image {idx}; you MUST pose the character strictly in a wide open empty-handed 90-degree horizontal T-POSE."
            )
        elif rkey == "paperPet":
            ref_notes.append(
                f"Image {idx} (STYLE REFERENCE ONLY): match ONLY the flat white die-cut 2D hand-drawn doodle cat standee with thick white foam border and tiny white base block; ignore the surrounding plaza and characters."
            )
        else:
            ref_notes.append(
                f"Image {idx} (STYLE & COLOR BIBLE REFERENCE ONLY): match the storybook warm-sun miniature clay and painted wooden toy aesthetic, soft 2-4cm rounded beveled edges, matte roughness, and high-brightness low-saturation pastel palette. Do NOT copy the surrounding terrain, sky, water, or other objects from the reference image."
            )

    if cat == "character":
        framing_spec = (
            "Composition/framing: single isolated full-body character centered cleanly with 15% pure white studio margin around all ears, hats, outstretched horizontal hands/wingtips, feet, and tails (never crop the wide outstretched arms or hands). "
            "Strict symmetrical front-facing standard T-POSE for 3D auto-rigging: standing completely upright facing straight forward toward the camera, BOTH arms (or owl wings) extended straight out horizontally to the left and right at exact 90-degree shoulder level forming a crisp capital-T silhouette, empty open palms facing downward or slightly forward (DO NOT hold books, watering cans, bread, tools, or fishing rods), legs straight and slightly apart on flat imaginary ground."
        )
        lighting_spec = (
            "Lighting/mood: bright even neutral softbox studio daylight illumination with uniform soft diffuse shading so surface albedo is crisp and legible for 3D reconstruction; soft warm slate-lavender ambient bounce (#5A587D, never harsh pure black shadows); no ground cast shadow or tiny ultra-faint ambient occlusion directly under the soles only."
        )
    elif cat == "ugc":
        framing_spec = (
            "Composition/framing: single isolated miniature 2D die-cut cardboard standee object centered cleanly at a gentle 3/4 front product angle with 15% pure white studio margin on all sides, nothing cropped."
        )
        lighting_spec = (
            "Lighting/mood: bright even studio product lighting on pure clean seamless #FFFFFF white backdrop, crisp matte cardboard edge visibility, zero surrounding floor."
        )
    else:
        framing_spec = (
            "Composition/framing: single isolated 3D miniature asset centered cleanly on a 100% seamless pure off-white studio cyclorama (#FFFFFF / #FAF8F5) with 14% generous negative margin on all sides so roof tips, sails, or canopies are never cropped. "
            "Elevated 3/4 orthographic-like product turnaround angle (around 25 degrees downward pitch, 35 degrees yaw) showing front and side depth clearly for AI 3D mesh reconstruction."
        )
        lighting_spec = (
            "Lighting/mood: clean bright even softbox daylight studio illumination for accurate albedo extraction (NO orange sunset tint, NO dark night darkness, NO harsh directional shadows, NO bloom glare); soft muted warm-slate ambient occlusion only, no visible ground plane, no grass patch, no sand base, no sky."
        )

    fix_line = f"\nMandatory revision fix from art director review: {extra_fix.strip()}" if extra_fix else ""

    prompt = f"""Call the built-in `image_gen` tool ONCE right now to generate a single clean 3D modeling asset turnaround close-up image. Do NOT inspect workspace files or run shell commands. After generating, reply briefly with the output path.

Use case: stylized-concept
Asset type: isolated 3D game asset concept render for AI 3D mesh reconstruction
Asset ID & Name: {asset['code']} - {asset['name_en']} ({asset['name_zh']})
Input images guidance:
{chr(10).join('- ' + n for n in ref_notes)}

Primary subject: {asset['subject']}.
Detailed visual & material design: {asset['details']}
Style/medium: Shiguang Town storybook warm-sun miniature diorama style — soft stylized matte clay and painted wooden toy PBR, 2-4cm rounded beveled edges on every plank/stone/wall, zero realistic gritty grain, zero 2D black ink comic outlines (unless explicitly specified as a 2D cardboard cutout).
Color palette: adhere strictly to high-brightness low-saturation storybook pastels — cream-ivory #FFF5E4, honey oak #E4BA8B, toasted wood #9D623E, terracotta tile #B96A59, sage leaf #93C794, mint sea-blue #7CC6E8, warm amber accent #FFD67A, warm slate shadow tint #5A587D (never pure #000000).
Scene/backdrop: 100% pure clean seamless uniform white / ultra-light cream studio background (#FFFFFF or #FAF8F5), completely floating/isolated with NO grass turf, NO sand floor, NO ocean water, NO sky, NO horizon line, NO stone pedestal slab unless explicitly part of the asset itself.
{framing_spec}
{lighting_spec}
Constraints: single isolated asset only; zero text, zero labels, zero dimensions, zero watermarks, zero grid lines, zero borders.{fix_line}
Avoid: {asset['avoid']}, messy grass base, terrain island block, horizon, dark shadows, photorealism, blurry artifacts, cut-off edges, multiple unrelated copies.
"""
    return prompt


def parse_generated_image(stdout_text: str, started_at: float) -> tuple[str | None, Path | None]:
    thread_id = None
    candidate_paths: list[Path] = []

    for line in stdout_text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "thread.started" and ev.get("thread_id"):
            thread_id = ev["thread_id"]
        # Scan serialized event for generated_images png paths
        s = json.dumps(ev, ensure_ascii=False)
        for m in re.findall(r"[A-Za-z]:[/\\\\][^\"'\s]+?generated_images[/\\\\][^\"'\s]+?\.png", s):
            p = Path(m.replace("\\\\", "\\"))
            if p.is_file():
                candidate_paths.append(p)

    if thread_id:
        tdir = CODEX_GENERATED_ROOT / thread_id
        if tdir.is_dir():
            pngs = sorted(
                [p for p in tdir.glob("*.png") if p.stat().st_mtime >= started_at - 5],
                key=lambda p: p.stat().st_mtime,
            )
            if pngs:
                return thread_id, pngs[-1]
            all_pngs = sorted(tdir.glob("*.png"), key=lambda p: p.stat().st_mtime)
            if all_pngs:
                return thread_id, all_pngs[-1]

    if candidate_paths:
        return thread_id, candidate_paths[-1]

    return thread_id, None


def generate_one(asset: dict, style_bible: dict, force: bool, extra_fix: str | None) -> tuple[str, bool, str]:
    aid = asset["id"]
    out_path = OUT_DIR / f"{aid}.png"
    if out_path.is_file() and not force and not extra_fix:
        return aid, True, f"SKIP (already exists: {out_path.name})"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    codex_argv = resolve_codex_argv()
    ref_map = style_bible["baseReferences"]
    ref_files = []
    for rkey in asset["refs"]:
        rp = (PROJECT_ROOT / ref_map[rkey]).resolve()
        if not rp.is_file():
            return aid, False, f"Missing reference image: {rp}"
        ref_files.append(str(rp))

    cmd = codex_argv + [
        "exec",
        "-c", "mcp_servers={}",
        "--enable", "image_generation",
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "-s", "read-only",
    ]
    for rf in ref_files:
        cmd.extend(["-i", rf])
    cmd.append("-")

    prompt = build_prompt(asset, style_bible, extra_fix)
    started_at = time.time()
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            cwd=str(PROJECT_ROOT),
            timeout=240,
        )
    except subprocess.TimeoutExpired:
        return aid, False, "TIMEOUT after 240s"

    log_file = LOG_DIR / f"{aid}.log"
    log_file.write_text(
        f"RETURN CODE: {proc.returncode}\n\n=== PROMPT ===\n{prompt}\n\n=== STDOUT ===\n{proc.stdout}\n\n=== STDERR ===\n{proc.stderr}\n",
        encoding="utf-8",
    )

    if proc.returncode != 0:
        return aid, False, f"codex exec failed rc={proc.returncode}; see {log_file}"

    thread_id, img_path = parse_generated_image(proc.stdout, started_at)
    if img_path is None or not img_path.is_file():
        return aid, False, f"No image found for thread={thread_id}; see {log_file}"

    shutil.copy2(img_path, out_path)
    return aid, True, f"OK ({img_path.name} -> {out_path.name}, {out_path.stat().st_size} B, thread={thread_id})"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate clean close-up references via Codex image_gen")
    parser.add_argument("--id", action="append", help="Specific asset ID(s) to generate")
    parser.add_argument("--batch", choices=["A", "B", "C", "D", "ALL"], help="Batch to generate")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output PNGs")
    parser.add_argument("--extra-fix", default=None, help="Additional revision note appended to prompt")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers inside this invocation")
    args = parser.parse_args()

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assets = data["assets"]
    style_bible = data["styleBible"]

    selected = []
    if args.id:
        wanted = set(args.id)
        selected = [a for a in assets if a["id"] in wanted]
        missing = wanted - {a["id"] for a in selected}
        if missing:
            print(f"Unknown asset IDs: {sorted(missing)}", file=sys.stderr)
            return 2
    elif args.batch:
        if args.batch == "ALL":
            selected = assets
        else:
            selected = [a for a in assets if a["batch"] == args.batch]
    else:
        parser.error("Provide --id or --batch")

    print(f"Queueing {len(selected)} asset(s) with workers={args.workers}...")
    failures = 0
    if args.workers <= 1 or len(selected) <= 1:
        for asset in selected:
            aid, ok, msg = generate_one(asset, style_bible, args.force, args.extra_fix)
            print(f"[{ 'PASS' if ok else 'FAIL' }] {aid}: {msg}", flush=True)
            if not ok:
                failures += 1
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {
                pool.submit(generate_one, asset, style_bible, args.force, args.extra_fix): asset["id"]
                for asset in selected
            }
            for fut in as_completed(futs):
                aid, ok, msg = fut.result()
                print(f"[{ 'PASS' if ok else 'FAIL' }] {aid}: {msg}", flush=True)
                if not ok:
                    failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
