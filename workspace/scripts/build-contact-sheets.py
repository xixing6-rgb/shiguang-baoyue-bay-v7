#!/usr/bin/env python3
"""Assemble 4 labeled contact sheets for Art Director QA across all 62 close-up assets."""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
CLOSEUP_DIR = PROJECT_ROOT / "workspace" / "assets" / "3d-modeling-closeups"
MANIFEST_PATH = CLOSEUP_DIR / "manifest.json"
SHEET_DIR = CLOSEUP_DIR / "_contact-sheets"


SHEETS = [
    (
        "sheet-1-core-town-F01-F18.png",
        "Batch A: Core Town F01-F18 (20 Assets)",
        lambda a: a["batch"] == "A",
    ),
    (
        "sheet-2-expansion-west-east-F19-F31.png",
        "Batch B: 4x Expansion West/East/Greenhouse F19-F31 (13 Assets)",
        lambda a: a["batch"] == "B",
    ),
    (
        "sheet-3-expansion-north-south-F32-F42.png",
        "Batch C: 4x Expansion North/South/Ferry F32-F42 (11 Assets)",
        lambda a: a["batch"] == "C",
    ),
    (
        "sheet-4-residents-props-C01-U01.png",
        "Batch D: Residents T-Pose + Props + Flora + 2D Pet C01-U01 (18 Assets)",
        lambda a: a["batch"] == "D",
    ),
]


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for fp in candidates:
        if Path(fp).is_file():
            try:
                return ImageFont.truetype(fp, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def build_sheet(filename: str, title: str, items: list[dict]) -> Path:
    cols = 4
    rows = (len(items) + cols - 1) // cols
    cell_w = 520
    cell_h = 460
    pad = 28
    header_h = 84
    label_h = 54

    canvas_w = pad + cols * (cell_w + pad)
    canvas_h = header_h + pad + rows * (cell_h + pad)
    sheet = Image.new("RGB", (canvas_w, canvas_h), (247, 244, 238))
    draw = ImageDraw.Draw(sheet)

    title_font = load_font(30)
    label_font = load_font(20)
    sub_font = load_font(15)

    draw.rectangle([0, 0, canvas_w, header_h], fill=(236, 229, 217))
    draw.text((pad, 24), title, fill=(65, 58, 78), font=title_font)

    for idx, item in enumerate(items):
        r = idx // cols
        c = idx % cols
        x0 = pad + c * (cell_w + pad)
        y0 = header_h + pad + r * (cell_h + pad)

        # Card container
        draw.rounded_rectangle(
            [x0, y0, x0 + cell_w, y0 + cell_h],
            radius=16,
            fill=(255, 255, 255),
            outline=(214, 206, 192),
            width=2,
        )

        img_path = CLOSEUP_DIR / f"{item['id']}.png"
        thumb_area_w = cell_w - 20
        thumb_area_h = cell_h - label_h - 16
        if img_path.is_file():
            with Image.open(img_path) as im:
                im_rgb = im.convert("RGB")
                im_rgb.thumbnail((thumb_area_w, thumb_area_h), Image.Resampling.LANCZOS)
                tx = x0 + 10 + (thumb_area_w - im_rgb.width) // 2
                ty = y0 + 8 + (thumb_area_h - im_rgb.height) // 2
                sheet.paste(im_rgb, (tx, ty))
        else:
            draw.rectangle(
                [x0 + 20, y0 + 20, x0 + cell_w - 20, y0 + thumb_area_h],
                fill=(254, 226, 226),
                outline=(220, 38, 38),
                width=2,
            )
            draw.text((x0 + 36, y0 + 80), f"MISSING: {item['id']}.png", fill=(185, 28, 28), font=label_font)

        # Label bar
        ly = y0 + cell_h - label_h
        draw.line([x0 + 12, ly, x0 + cell_w - 12, ly], fill=(230, 224, 214), width=1)
        draw.text((x0 + 16, ly + 6), f"{item['id']} | {item['name_zh']}", fill=(54, 48, 68), font=label_font)
        draw.text((x0 + 16, ly + 31), f"{item['category']} · {item['dimensions']}", fill=(120, 114, 130), font=sub_font)

    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SHEET_DIR / filename
    sheet.save(out_path, format="PNG", optimize=True)
    return out_path


def main() -> int:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assets = data["assets"]
    for filename, title, pred in SHEETS:
        subset = [a for a in assets if pred(a)]
        out = build_sheet(filename, title, subset)
        print(f"Built {out} ({len(subset)} items, {out.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
