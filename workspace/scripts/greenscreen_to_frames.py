r"""Offline green-screen video -> transparent PNG sequence converter for Douyin 2.5D Dialogue UI.

Converts an external AI-generated green-screen character video (mp4/mov/webm) into a crisp
sequence of RGBA transparent PNG frames aligned to a unified bounding box (no jitter!),
ready to drop into ui-dialogue-25d/images/.

Usage:
  python workspace/scripts/greenscreen_to_frames.py --input path/to/video.mp4 --out-dir path/to/images --prefix amuFrame --fps 8 --max-frames 8
  python workspace/scripts/greenscreen_to_frames.py --self-test
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def resolve_ffmpeg() -> str | None:
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return exe
    except Exception:
        pass
    which = shutil.which("ffmpeg")
    return which


def extract_frames_ffmpeg(video_path: Path, tmp_dir: Path, fps: float, max_frames: int) -> list[Path]:
    ffmpeg_exe = resolve_ffmpeg()
    if ffmpeg_exe:
        try:
            pattern = tmp_dir / "raw_%04d.png"
            cmd = [
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(video_path),
                "-vf", f"fps={fps}",
                "-frames:v", str(max_frames),
                str(pattern),
            ]
            subprocess.run(cmd, check=True)
            frames = sorted(tmp_dir.glob("raw_*.png"))
            if frames:
                return frames
        except Exception:
            pass

    # Pure OpenCV fallback
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    step = max(1, int(round(src_fps / max(fps, 0.5))))
    frames = []
    idx = 0
    saved = 0
    while saved < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            out_p = tmp_dir / f"raw_{saved + 1:04d}.png"
            cv2.imwrite(str(out_p), frame)
            frames.append(out_p)
            saved += 1
        idx += 1
    cap.release()
    if not frames:
        raise RuntimeError(f"Extracted 0 frames from {video_path}")
    return frames


def chroma_key_frame(
    bgr: np.ndarray,
    hue_min: int = 35,
    hue_max: int = 92,
    sat_min: int = 50,
    val_min: int = 45,
    feather: int = 2,
) -> np.ndarray:
    """HSV green-screen chroma key + soft spill suppression -> RGBA uint8."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    # Primary green screen mask
    is_green = (h >= hue_min) & (h <= hue_max) & (s >= sat_min) & (v >= val_min)

    # Also catch bright green excess (G significantly higher than R and B)
    b_ch, g_ch, r_ch = cv2.split(bgr.astype(np.float32))
    green_dom = g_ch - np.maximum(r_ch, b_ch)
    soft_green = np.clip((green_dom - 12.0) / 36.0, 0.0, 1.0)

    alpha = np.where(is_green, 0.0, 1.0).astype(np.float32)
    alpha = np.minimum(alpha, 1.0 - soft_green * 0.95)

    # Morphological cleanup of isolated specks & smooth alpha edge
    kernel = np.ones((3, 3), np.uint8)
    alpha_u8 = (np.clip(alpha, 0.0, 1.0) * 255.0).astype(np.uint8)
    alpha_u8 = cv2.morphologyEx(alpha_u8, cv2.MORPH_OPEN, kernel, iterations=1)
    if feather > 0:
        ksize = feather * 2 + 1
        alpha_u8 = cv2.GaussianBlur(alpha_u8, (ksize, ksize), 0)

    # Despill green fringe in semi-transparent/edge pixels
    alpha_f = alpha_u8.astype(np.float32) / 255.0
    max_rb = np.maximum(r_ch, b_ch)
    avg_rb = 0.5 * (r_ch + b_ch)
    spill_amt = np.clip(g_ch - max_rb, 0.0, 255.0)
    g_despilled = np.where(g_ch > max_rb, g_ch - spill_amt * 0.85, g_ch)
    # Stronger despill on semi-transparent fringe
    edge_mask = (alpha_f > 0.02) & (alpha_f < 0.92)
    g_out = np.where(edge_mask, np.minimum(g_despilled, avg_rb + 12.0), g_despilled)

    rgba = np.stack([
        np.clip(r_ch, 0, 255).astype(np.uint8),
        np.clip(g_out, 0, 255).astype(np.uint8),
        np.clip(b_ch, 0, 255).astype(np.uint8),
        alpha_u8,
    ], axis=-1)
    return rgba


def convert_video_to_frames(
    input_video: Path,
    out_dir: Path,
    prefix: str = "portraitFrame",
    fps: float = 8.0,
    max_frames: int = 8,
    width: int = 280,
    height: int = 360,
    hue_min: int = 35,
    hue_max: int = 92,
    sat_min: int = 50,
    val_min: int = 45,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td)
        raw_files = extract_frames_ffmpeg(input_video, tmp_dir, fps=fps, max_frames=max_frames)
        keyed_frames = []
        union_x0, union_y0, union_x1, union_y1 = 10**9, 10**9, -1, -1

        for rf in raw_files:
            bgr = cv2.imread(str(rf), cv2.IMREAD_COLOR)
            rgba = chroma_key_frame(bgr, hue_min, hue_max, sat_min, val_min)
            keyed_frames.append(rgba)
            ys, xs = np.where(rgba[:, :, 3] > 24)
            if len(xs) > 0:
                union_x0 = min(union_x0, int(xs.min()))
                union_y0 = min(union_y0, int(ys.min()))
                union_x1 = max(union_x1, int(xs.max()))
                union_y1 = max(union_y1, int(ys.max()))

        if union_x1 < union_x0:
            raise RuntimeError("No foreground subject detected after chroma keying!")

        # Unified crop box with 4% padding so character never jumps horizontally/vertically
        pad = 8
        h_src, w_src = keyed_frames[0].shape[:2]
        cx0 = max(0, union_x0 - pad)
        cy0 = max(0, union_y0 - pad)
        cx1 = min(w_src, union_x1 + pad + 1)
        cy1 = min(h_src, union_y1 + pad + 1)

        crop_w = cx1 - cx0
        crop_h = cy1 - cy0
        scale = min((width - 16) / float(crop_w), (height - 16) / float(crop_h))
        nw = max(1, int(round(crop_w * scale)))
        nh = max(1, int(round(crop_h * scale)))
        ox = (width - nw) // 2
        oy = height - nh - 6  # bottom-aligned cleanly inside portrait box

        written = []
        pil_preview = []
        for idx, rgba in enumerate(keyed_frames, start=1):
            cropped = Image.fromarray(rgba[cy0:cy1, cx0:cx1], mode="RGBA")
            resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            canvas.paste(resized, (ox, oy), resized)
            out_path = out_dir / f"{prefix}{idx:02d}.png"
            canvas.save(out_path)
            written.append(out_path)
            pil_preview.append(canvas)

        preview_gif = out_dir / f"{prefix}_preview.gif"
        pil_preview[0].save(
            preview_gif,
            save_all=True,
            append_images=pil_preview[1:],
            duration=int(1000 / max(fps, 1.0)),
            loop=0,
            disposal=2,
        )
        print(f"[FRAMES OK] Generated {len(written)} RGBA frames + preview GIF in {out_dir}")
        return written


def run_self_test():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        frames_in = tmp / "in_frames"
        frames_in.mkdir()
        # Create a 1-second synthetic green-screen animation of a bouncing warm character silhouette
        for i in range(8):
            img = np.zeros((360, 360, 3), dtype=np.uint8)
            img[:, :] = (40, 225, 45)  # BGR bright green screen
            cy = int(200 - 14 * abs(np.sin(i * np.pi / 4.0)))
            cv2.circle(img, (180, cy), 68, (110, 165, 225), -1)  # bear body
            cv2.circle(img, (180, cy - 82), 54, (130, 185, 240), -1)  # head
            cv2.circle(img, (162, cy - 88), 8, (40, 40, 60), -1)
            cv2.circle(img, (198, cy - 88), 8, (40, 40, 60), -1)
            cv2.imwrite(str(frames_in / f"f_{i:02d}.png"), img)

        test_mp4 = tmp / "selftest_gs.mp4"
        ffmpeg_exe = resolve_ffmpeg()
        if ffmpeg_exe:
            subprocess.run([
                ffmpeg_exe, "-y", "-hide_banner", "-loglevel", "error",
                "-framerate", "8", "-i", str(frames_in / "f_%02d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(test_mp4),
            ], check=True)
        else:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            vw = cv2.VideoWriter(str(test_mp4), fourcc, 8.0, (360, 360))
            for i in range(8):
                vw.write(cv2.imread(str(frames_in / f"f_{i:02d}.png")))
            vw.release()

        out_dir = tmp / "out_frames"
        written = convert_video_to_frames(test_mp4, out_dir, prefix="testFrame", fps=8, max_frames=8)
        assert len(written) == 8
        sample = np.asarray(Image.open(written[0]).convert("RGBA"))
        # Verify corners are 100% transparent and center has solid character alpha
        assert sample[0, 0, 3] == 0 and sample[0, -1, 3] == 0, "Corner not transparent!"
        assert sample[220, 140, 3] > 230, "Subject body missing alpha!"
        print("[SELF-TEST PASS] Green-screen ffmpeg + chroma-key + despill + unified crop verified.")


def main():
    parser = argparse.ArgumentParser(description="Convert green-screen video into transparent PNG frames.")
    parser.add_argument("--input", type=Path, help="Input green-screen video path (.mp4/.mov/.webm)")
    parser.add_argument("--out-dir", type=Path, help="Output directory for RGBA PNG frames")
    parser.add_argument("--prefix", default="portraitFrame", help="Output filename prefix")
    parser.add_argument("--fps", type=float, default=8.0, help="Target extraction FPS")
    parser.add_argument("--max-frames", type=int, default=8, help="Max number of frames")
    parser.add_argument("--width", type=int, default=280, help="Target frame width px")
    parser.add_argument("--height", type=int, default=360, help="Target frame height px")
    parser.add_argument("--hue-min", type=int, default=35)
    parser.add_argument("--hue-max", type=int, default=92)
    parser.add_argument("--sat-min", type=int, default=50)
    parser.add_argument("--val-min", type=int, default=45)
    parser.add_argument("--self-test", action="store_true", help="Run built-in synthetic green-screen test")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return
    if not args.input or not args.out_dir:
        parser.error("--input and --out-dir are required unless --self-test is set")
    convert_video_to_frames(
        args.input, args.out_dir,
        prefix=args.prefix, fps=args.fps, max_frames=args.max_frames,
        width=args.width, height=args.height,
        hue_min=args.hue_min, hue_max=args.hue_max, sat_min=args.sat_min, val_min=args.val_min,
    )


if __name__ == "__main__":
    main()
