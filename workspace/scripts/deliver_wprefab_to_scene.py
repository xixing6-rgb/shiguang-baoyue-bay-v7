"""Build, archive shiguang-25d-windwaker WPrefab, patch Wind-Waker environment, and swap into live scene."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
ENV_PATCH = ROOT / "workspace" / "data" / "windwaker_env_patch.json"
DELIVER_JSON = ROOT / "workspace" / "data" / "windwaker_delivery_receipt.json"
PREFAB = "shiguang-25d-windwaker"
WS_ID = "workspace_024l9gls"
INSTANCE = "259916cd-7dc2-4a7f-aa09-0bb4bd0ec68f"
OLD_ROOT_ID = "-1355719423"
IMPORT_POS = "115,79.35,86"
IMPORT_REQ_ID = "shiguang-25d-v3-import"


def run_dw(args: list[str]) -> tuple[int, str]:
    cmd = ["douyin-world", *args, "--instance", INSTANCE, "--timeout-ms", "180000"]
    proc = subprocess.run(
        subprocess.list2cmdline(cmd),
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, out.strip()


def extract_json_payload(raw: str) -> dict:
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("{"):
            try:
                return json.loads(s)
            except Exception:
                pass
    return json.loads(raw)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    receipt = json.loads(DELIVER_JSON.read_text(encoding="utf-8")) if DELIVER_JSON.exists() else {}

    if mode in ("all", "build"):
        c1, o1 = run_dw(["authoring", "prefab", "build", PREFAB, "--workspace-id", WS_ID, "--json"])
        print(f"[BUILD {c1}] {o1[:400]}")
        if c1 != 0:
            sys.exit(c1)

        c2, o2 = run_dw(
            ["authoring", "result", "archive", PREFAB, "--workspace-id", WS_ID, "--name", "时光小筑2.5D风之杖抱月湾", "--json"]
        )
        print(f"[ARCHIVE {c2}] {o2[:500]}")
        if c2 != 0:
            sys.exit(c2)
        parsed = extract_json_payload(o2)
        uri = parsed.get("data", {}).get("uri") or parsed.get("uri")
        assert uri, f"Missing archived WPrefab URI in: {o2}"
        receipt["wprefabUri"] = uri
        DELIVER_JSON.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[WPREFAB URI] {uri}")

    if mode in ("all", "scene"):
        uri = receipt.get("wprefabUri")
        assert uri, "Run build mode first to produce wprefabUri"

        c_env, o_env = run_dw(["scene", "environment", "set", "--file", str(ENV_PATCH), "--json"])
        print(f"[ENV SET {c_env}] {o_env[:350]}")
        if c_env != 0:
            sys.exit(c_env)

        remove_id = str(receipt.get("lastRootId") or OLD_ROOT_ID)
        c_rm, o_rm = run_dw(["scene", "remove", remove_id, "--json"])
        print(f"[SCENE REMOVE {remove_id} -> {c_rm}] {o_rm[:350]}")
        # Note: if already removed on retry, don't crash blindly; check error text
        if c_rm != 0 and "找不到" not in o_rm and "not found" not in o_rm.lower():
            sys.exit(c_rm)

        c_imp, o_imp = run_dw(
            [
                "scene",
                "import",
                "--uri",
                uri,
                "--position",
                IMPORT_POS,
                "--name",
                "时光小筑2.5D风之杖抱月湾",
                "--request-id",
                IMPORT_REQ_ID,
                "--json",
            ]
        )
        print(f"[SCENE IMPORT {c_imp}] {o_imp[:500]}")
        if c_imp != 0:
            sys.exit(c_imp)
        imp_data = extract_json_payload(o_imp)
        receipt["sceneImport"] = imp_data
        roots = imp_data.get("data", {}).get("rootIDs") or imp_data.get("rootIDs") or []
        if roots:
            receipt["lastRootId"] = str(roots[0])
        DELIVER_JSON.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
