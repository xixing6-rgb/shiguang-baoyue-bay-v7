"""Execute v4.1 WPrefab update (P06 + U01), build, archive, and swap into live scene."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
INSTANCE = "993d993d-fe6a-44b0-87f9-9c6d2f95ef69"
WS = "workspace_024l9gls"
PREFAB = "shiguang-25d-windwaker"
URIS_PATH = ROOT / "workspace" / "data" / "windwaker_asset_uris.json"
RECEIPT_PATH = ROOT / "workspace" / "data" / "windwaker_delivery_receipt.json"
SDK_JS = ROOT / "workspace" / "scripts" / "add_p06_u01_to_prefab.js"


def run_dw(args: list[str], timeout_ms: int = 180000, allow_fail: bool = False) -> tuple[int, dict | str]:
    cmd = ["douyin-world", *args, "--instance", INSTANCE, "--timeout-ms", str(timeout_ms), "--json"]
    p = subprocess.run(subprocess.list2cmdline(cmd), shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    raw = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
    print(f"[CMD exit={p.returncode}] {' '.join(args[:4])} -> {raw[:400]}")
    if p.returncode != 0 and not allow_fail:
        raise RuntimeError(f"CLI failed: {' '.join(args)}\n{raw}")
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("{"):
            try:
                return p.returncode, json.loads(s)
            except Exception:
                pass
    return p.returncode, raw


def main() -> None:
    # 1. Update windwaker_asset_uris.json with all archived Tripo URIs
    uris = json.loads(URIS_PATH.read_text(encoding="utf-8"))
    prefab_models = Path(
        r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
        rf"\ai-sessions\{WS}\wprefabs\{PREFAB}\assets\models"
    )
    for mid in ("model-farm-garden-tripo", "model-f03-tripo", "model-f23-tripo", "model-p06-tripo", "model-u01-tripo"):
        rj = prefab_models / mid / "package" / "resource.json"
        if rj.exists():
            d = json.loads(rj.read_text(encoding="utf-8"))
            u = d.get("uri") or d.get("result", {}).get("uri")
            if u:
                uris[mid] = u
    URIS_PATH.write_text(json.dumps(uris, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Execute SDK script to place P06 & U01
    _, cap = run_dw(["authoring", "prefab", "read", PREFAB, "context.capabilities", "--workspace-id", WS])
    rev = cap["data"]["revision"]
    _, ex = run_dw(["authoring", "prefab", "execute", PREFAB, "--file", str(SDK_JS), "--revision", rev, "--workspace-id", WS])
    print("[EXECUTE SUMMARY]", ex["data"].get("summary"))

    _, val = run_dw(["authoring", "prefab", "validate", PREFAB, "--workspace-id", WS])
    res = val["data"]["result"]
    if res.get("items") or val["data"].get("warnings"):
        raise RuntimeError(f"Validation failed: {val}")

    run_dw(["authoring", "prefab", "build", PREFAB, "--workspace-id", WS])
    _, arch = run_dw(["authoring", "result", "archive", PREFAB, "--workspace-id", WS, "--name", "时光小筑2.5D风之杖抱月湾"])
    new_uri = arch["data"]["uri"]
    print(f"[NEW WPREFAB URI] {new_uri}")

    # 3. Swap into live scene
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    old_root = str(receipt.get("lastRootId") or "-1577082918")
    rc_rm, out_rm = run_dw(["scene", "remove", old_root, "--request-id", "shiguang-25d-v41-remove-old"], timeout_ms=120000, allow_fail=True)
    if rc_rm != 0:
        msg = json.dumps(out_rm, ensure_ascii=False)
        if "找不到" not in msg and "not found" not in msg.lower():
            raise RuntimeError(f"Remove failed: {msg}")

    rc_imp, out_imp = run_dw(
        [
            "scene", "import",
            "--uri", new_uri,
            "--position", "115,79.35,86",
            "--name", "时光小筑2.5D风之杖抱月湾",
            "--request-id", "shiguang-25d-v41-import",
        ],
        timeout_ms=240000,
        allow_fail=True,
    )
    if rc_imp != 0:
        _, out_imp = run_dw(["scene", "cancel", "shiguang-25d-v41-import"], timeout_ms=60000)

    receipt["wprefabUri"] = new_uri
    receipt["sceneImport"] = out_imp
    roots = out_imp.get("data", {}).get("rootIDs") or []
    if roots:
        receipt["lastRootId"] = str(roots[0])
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[DELIVERED V4.1]", json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
