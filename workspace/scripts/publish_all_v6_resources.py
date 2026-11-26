"""Publish effect, 4 audio clips, and 10 prepared models for v6 and update windwaker_asset_uris.json."""
from __future__ import annotations

import json
import os
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

MODEL_IDS = [
    "model-windwaker-bay",
    "model-windwaker-sea-horizon",
    "model-e01-pine",
    "model-e02-maple",
    "model-f09-fountain",
    "model-f22-lighthouse",
    "model-p01-lamp",
    "model-p02-mailbox",
    "model-p03-signpost",
    "model-p05-bakery",
]

CLEAN_ENV = {k: v for k, v in os.environ.items() if "PROXY" not in k.upper()}


def run_json(args: list[str]) -> dict:
    proc = subprocess.run(
        subprocess.list2cmdline(args),
        shell=True,
        env=CLEAN_ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    data = None
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("{"):
            data = json.loads(s)
            break
    if proc.returncode != 0 or not data or not data.get("ok"):
        raise RuntimeError(f"CLI failed ({' '.join(args[:6])}): {raw}")
    return data


def main() -> None:
    uris = json.loads(URIS_PATH.read_text(encoding="utf-8"))
    # Already published in verification step:
    uris["effect-water-ripple"] = (
        "hamlet-ugc/aigc_editor/dev/unity/"
        "MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/"
        "eod4qbx91mkr84s2.wprefab"
    )

    for aid in AUDIO_IDS:
        res = run_json([
            "douyin-world", "authoring", "resource", "archive", aid,
            "--kind", "audio", "--prefab", PREFAB,
            "--workspace-id", WS, "--instance", INSTANCE,
            "--timeout-ms", "180000", "--json",
        ])
        uri = res.get("data", {}).get("uri")
        if not uri:
            raise RuntimeError(f"Missing URI for audio {aid}: {res}")
        uris[aid] = uri
        print(f"[PUBLISHED AUDIO] {aid:24s} -> {uri[-32:]}", flush=True)

    for mid in MODEL_IDS:
        res = run_json([
            "douyin-world", "authoring", "resource", "publish", mid,
            "--kind", "model", "--prefab", PREFAB,
            "--workspace-id", WS, "--instance", INSTANCE,
            "--timeout-ms", "180000", "--json",
        ])
        uri = res.get("data", {}).get("uri")
        if not uri:
            raise RuntimeError(f"Missing URI for model {mid}: {res}")
        uris[mid] = uri
        print(f"[PUBLISHED MODEL] {mid:28s} -> {uri[-32:]}", flush=True)

    URIS_PATH.write_text(json.dumps(uris, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ALL URIS SAVED] {URIS_PATH}", flush=True)


if __name__ == "__main__":
    main()
