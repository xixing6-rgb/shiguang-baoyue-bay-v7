"""Generate crisp transparent-background animated portrait frame sequences for demo NPCs (Amu & Mianmian).

Uses border flood-fill + chroma-aware anti-aliased edge feathering so pale cream fur on Mianmian
stays intact while pure-white studio backdrop is cleanly removed.
Generates 6 looping frames for C01 (阿木) and 4 looping frames for C02 (绵绵).
"""

from __future__ import annotations

import math
import shutil
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
WPREFAB_UIS = (
    Path(
        r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
        r"\ai-sessions\workspace_024l9gls\wprefabs\shiguang-25d-windwaker\assets\uis\ui-dialogue-25d\images"
    )
)
WS_UI_IMAGES = ROOT / "workspace" / "assets" / "ui-dialogue-25d" / "images"

SRC_AMU = ROOT / "图片" / "03-居民标准TPose-C01-C09" / "C01-眼镜棕熊·阿木.png"
SRC_MIAN = ROOT / "图片" / "03-居民标准TPose-C01-C09" / "C02-垂耳白兔·绵绵.png"

TARGET_W, TARGET_H = 280, 360


def extract_clean_cutout(img_path: Path, bg_tol: float = 16.0, chroma_tol: float = 10.0) -> Image.Image:
    im = Image.open(img_path).convert("RGBA")
    arr = np.array(im, dtype=np.float32)
    h, w, _ = arr.shape
    rgb = arr[:, :, :3]

    # Sample top-left & top-right corner as background color
    corners = np.vstack([rgb[0:6, 0:6].reshape(-1, 3), rgb[0:6, w - 6 : w].reshape(-1, 3)])
    bg_rgb = np.median(corners, axis=0)

    dist = np.linalg.norm(rgb - bg_rgb, axis=2)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)

    # Strict near-white background candidate: low color distance AND low saturation
    is_bg_cand = (dist <= bg_tol) & (chroma <= chroma_tol)

    # 4-connected BFS flood fill starting from all border pixels matching candidate
    bg_mask = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_bg_cand[y, x] and not bg_mask[y, x]:
                bg_mask[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if is_bg_cand[y, x] and not bg_mask[y, x]:
                bg_mask[y, x] = True
                q.append((y, x))

    while q:
        cy, cx = q.popleft()
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w and not bg_mask[ny, nx] and is_bg_cand[ny, nx]:
                bg_mask[ny, nx] = True
                q.append((ny, nx))

    alpha = np.where(bg_mask, 0.0, 255.0).astype(np.float32)

    # Soft feather 1-pixel fringe touching bg_mask where luminance is close to background
    fringe = np.zeros((h, w), dtype=bool)
    fringe[1:, :] |= bg_mask[:-1, :]
    fringe[:-1, :] |= bg_mask[1:, :]
    fringe[:, 1:] |= bg_mask[:, :-1]
    fringe[:, :-1] |= bg_mask[:, 1:]
    fringe &= ~bg_mask

    # Linearly ramp alpha on near-white boundary pixels to prevent jagged halo
    ramp = np.clip((dist - (bg_tol * 0.6)) / (bg_tol * 1.4), 0.15, 1.0) * 255.0
    alpha = np.where(fringe & (dist < bg_tol * 2.0) & (chroma < chroma_tol * 1.8), ramp, alpha)

    # Un-premultiply bright halo on fringe slightly toward neighbor non-fringe pixels by clamping high white mix
    out = arr.copy()
    out[:, :, 3] = np.clip(alpha, 0, 255)
    cutout = Image.fromarray(out.astype(np.uint8), mode="RGBA")

    # Tight bbox crop with slight padding
    alpha_mask = out[:, :, 3] > 20
    ys, xs = np.where(alpha_mask)
    assert len(xs) > 100 and len(ys) > 100, f"Cutout empty for {img_path}"
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    cropped = cutout.crop((x0, y0, x1, y1))

    # Resize to fit comfortably inside portrait card (margin for animation motion)
    max_w = TARGET_W - 28
    max_h = TARGET_H - 36
    scale = min(max_w / cropped.width, max_h / cropped.height)
    nw = max(1, int(round(cropped.width * scale)))
    nh = max(1, int(round(cropped.height * scale)))
    return cropped.resize((nw, nh), Image.Resampling.LANCZOS)


def make_loop_frames(base_sprite: Image.Image, prefix: str, count: int, out_dirs: list[Path], nod_deg: float, bob_px: float):
    sw, sh = base_sprite.size
    for idx in range(count):
        phase = 2.0 * math.pi * (idx / float(count))
        dy = math.sin(phase) * bob_px
        ang = math.sin(phase + 0.6) * nod_deg
        sx_scale = 1.0 + 0.015 * math.cos(phase)
        sy_scale = 1.0 - 0.018 * math.sin(phase)

        tw = max(1, int(round(sw * sx_scale)))
        th = max(1, int(round(sh * sy_scale)))
        warped = base_sprite.resize((tw, th), Image.Resampling.BICUBIC)
        warped = warped.rotate(ang, resample=Image.Resampling.BICUBIC, expand=True)

        canvas = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
        paste_x = (TARGET_W - warped.width) // 2
        # Anchor near bottom of portrait card so feet stay grounded while head breathes
        paste_y = int(round(TARGET_H - 12 - warped.height + dy))
        canvas.alpha_composite(warped, (paste_x, max(2, paste_y)))

        fname = f"{prefix}Frame{idx + 1:02d}.png"
        for d in out_dirs:
            d.mkdir(parents=True, exist_ok=True)
            canvas.save(d / fname, format="PNG")
    print(f"[PORTRAIT OK] {prefix}: {count} frames ({TARGET_W}x{TARGET_H})")


def main():
    amu_sprite = extract_clean_cutout(SRC_AMU, bg_tol=20.0, chroma_tol=12.0)
    mian_sprite = extract_clean_cutout(SRC_MIAN, bg_tol=14.0, chroma_tol=8.0)

    out_dirs = [WPREFAB_UIS, WS_UI_IMAGES]
    make_loop_frames(amu_sprite, "amu", 6, out_dirs, nod_deg=2.2, bob_px=5.5)
    make_loop_frames(mian_sprite, "mianmian", 4, out_dirs, nod_deg=3.0, bob_px=6.5)


if __name__ == "__main__":
    main()
