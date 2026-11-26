"""Download free CC0/royalty-free Mixkit audio MP3s and stage into wprefab assets/audio."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
LOCAL_AUDIO_DIR = ROOT / "workspace" / "assets" / "audio"
LOCAL_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

PREFAB_AUDIO_ROOT = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects"
    r"\project-9c69f507-5375-4486-83fc-d3f150502390\ai-sessions"
    r"\workspace_024l9gls\wprefabs\shiguang-25d-windwaker\assets\audio"
)

AUDIO_SPECS = [
    {
        "resourceId": "audio-footstep-grass",
        "localName": "grass-step.mp3",
        "url": "https://assets.mixkit.co/active_storage/sfx/1920/1920-preview.mp3",
        "displayName": "草地脚步音效",
        "summary": "踩踏抱月湾草地时播放的轻快草叶脚步声。",
    },
    {
        "resourceId": "audio-footstep-sand",
        "localName": "sand-step.mp3",
        "url": "https://assets.mixkit.co/active_storage/sfx/1494/1494-preview.mp3",
        "displayName": "沙地脚步音效",
        "summary": "踩踏海滩细沙或沙石路径时播放的柔和沙粒脚步声。",
    },
    {
        "resourceId": "audio-footstep-water",
        "localName": "water-step.mp3",
        "url": "https://assets.mixkit.co/active_storage/sfx/1311/1311-preview.mp3",
        "displayName": "水面踩水音效",
        "summary": "涉水踩踏浅滩海水时播放的清亮水花声。",
    },
    {
        "resourceId": "audio-ambient-waves",
        "localName": "sea-waves-loop.mp3",
        "url": "https://assets.mixkit.co/active_storage/sfx/1208/1208-preview.mp3",
        "displayName": "海湾轻浪环境音",
        "summary": "抱月湾海岸轻柔拍岸的循环海浪环境声。",
    },
]


def is_valid_mp3(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 10000:
        return False
    hdr = path.read_bytes()[:4]
    # ID3 tag or MPEG audio frame sync (0xFF 0xE0..0xFF)
    if hdr[:3] == b"ID3":
        return True
    if len(hdr) >= 2 and hdr[0] == 0xFF and (hdr[1] & 0xE0) == 0xE0:
        return True
    return False


def main() -> None:
    for item in AUDIO_SPECS:
        dest = LOCAL_AUDIO_DIR / item["localName"]
        if not is_valid_mp3(dest):
            cmd = ["curl.exe", "-sL", "--fail", "--max-time", "45", "-o", str(dest), item["url"]]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode != 0:
                raise RuntimeError(f"Download failed for {item['url']}: {proc.stderr}")
        if not is_valid_mp3(dest):
            raise RuntimeError(f"Invalid MP3 header or size for {dest} (size={dest.stat().st_size if dest.exists() else 0}, head={dest.read_bytes()[:8]!r})")
        print(f"[AUDIO OK] {item['localName']:20s} | {dest.stat().st_size:8d} bytes | head={dest.read_bytes()[:4]!r}")

        res_dir = PREFAB_AUDIO_ROOT / item["resourceId"]
        res_dir.mkdir(parents=True, exist_ok=True)
        # Keep only audio.mp3 per resource-generation/SKILL.md
        for old_wav in res_dir.glob("audio.wav"):
            old_wav.unlink()
        shutil.copy2(dest, res_dir / "audio.mp3")
        meta = {
            "schemaVersion": 4,
            "resourceId": item["resourceId"],
            "displayName": item["displayName"],
            "summary": item["summary"],
        }
        (res_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  [STAGED] {res_dir}")


if __name__ == "__main__":
    main()
