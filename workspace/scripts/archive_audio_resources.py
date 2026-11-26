"""Archive the 4 staged audio resources into shiguang-25d-windwaker and record URIs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
URIS_PATH = ROOT / "workspace" / "data" / "windwaker_asset_uris.json"
INSTANCE = "1c381f36-58c3-4989-ace4-e89020e8035e"
WS = "workspace_024l9gls"
PREFAB = "shiguang-25d-windwaker"

AUDIO_IDS = [
    "audio-footstep-grass",
    "audio-footstep-sand",
    "audio-footstep-water",
    "audio-ambient-waves",
]


def main() -> None:
    uris = json.loads(URIS_PATH.read_text(encoding="utf-8"))
    for rid in AUDIO_IDS:
        cmd = [
            "douyin-world", "authoring", "resource", "archive", rid,
            "--kind", "audio", "--prefab", PREFAB,
            "--workspace-id", WS, "--instance", INSTANCE,
            "--timeout-ms", "120000", "--json",
        ]
        proc = subprocess.run(subprocess.list2cmdline(cmd), shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        raw = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        if proc.returncode != 0:
            raise RuntimeError(f"Audio archive failed for {rid}: {raw}")
        data = None
        for line in raw.splitlines():
            s = line.strip()
            if s.startswith("{"):
                data = json.loads(s)
                break
        if not data or not data.get("ok"):
            raise RuntimeError(f"Unexpected response for {rid}: {raw}")
        uri = data.get("data", {}).get("uri") or data.get("uri")
        if not uri:
            raise RuntimeError(f"Missing URI for {rid}: {data}")
        uris[rid] = uri
        print(f"[ARCHIVED AUDIO] {rid} -> {uri}")
    URIS_PATH.write_text(json.dumps(uris, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {URIS_PATH}")


if __name__ == "__main__":
    main()
