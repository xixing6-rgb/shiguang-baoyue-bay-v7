"""Inspect main scene roots, replace old Wind-Waker roots with v6, and start runtime."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
PROJ_DIR = Path(r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390")
INSTANCE = "1c381f36-58c3-4989-ace4-e89020e8035e"
CLEAN_ENV = {k: v for k, v in os.environ.items() if "PROXY" not in k.upper()}

V6_WPREFAB_URI = (
    "hamlet-ugc/aigc_editor/dev/unity/"
    "MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/"
    "irati3cto8gvzch7.wprefab"
)


def run_cli(args: list[str], allow_fail: bool = False) -> dict:
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
    if (proc.returncode != 0 or not data or not data.get("ok")) and not allow_fail:
        raise RuntimeError(f"CLI failed ({' '.join(args[:5])}): {raw}")
    return data or {"ok": False, "raw": raw}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--deploy", action="store_true")
    args = ap.parse_args()

    rt = run_cli(["douyin-world", "runtime", "status", "--instance", INSTANCE, "--json"], allow_fail=True)
    print("runtime status:", rt, flush=True)

    if args.inspect and not args.deploy:
        return

    # Stop runtime if running
    if rt.get("data", {}).get("status") not in (None, "not_started", "stopped"):
        stop_res = run_cli(["douyin-world", "runtime", "stop", "--instance", INSTANCE, "--json"])
        print("runtime stop:", stop_res, flush=True)

    # Remove previous delivered root (-167362314)
    old_ids = ["-167362314"]
    for rid in old_ids:
        rem = run_cli([
            "douyin-world", "scene", "remove", rid,
            "--instance", INSTANCE, "--timeout-ms", "120000", "--json",
        ], allow_fail=True)
        print(f"scene remove {rid}:", rem, flush=True)

    # Import v6 WPrefab at anchored transform
    imp = run_cli([
        "douyin-world", "scene", "import", "--uri", V6_WPREFAB_URI,
        "--position", "115,79.35,86",
        "--request-id", "shiguang-25d-v6-import",
        "--instance", INSTANCE,
        "--timeout-ms", "180000", "--json",
    ])
    print("scene import v6:", json.dumps(imp, ensure_ascii=False), flush=True)

    # Start runtime preview
    st = run_cli([
        "douyin-world", "runtime", "start",
        "--instance", INSTANCE, "--wait", "60", "--json",
    ])
    print("runtime start:", json.dumps(st, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
