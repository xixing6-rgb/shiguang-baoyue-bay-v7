"""Sequential import -> meta nodeMergeBlacklist patching -> check -> archive for all 12 GLB resources."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
MODELS_DIR = ROOT / "workspace" / "assets" / "models"
TRIPO_DIR = MODELS_DIR / "tripo-optimized"
PREFAB = "shiguang-25d-windwaker"
WS_ID = "workspace_024l9gls"
INSTANCE = "259916cd-7dc2-4a7f-aa09-0bb4bd0ec68f"
PREFAB_MODELS_DIR = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
    rf"\ai-sessions\{WS_ID}\wprefabs\{PREFAB}\assets\models"
)

RESOURCES = [
    ("model-windwaker-bay", MODELS_DIR / "map-windwaker-bay.glb"),
    ("model-windwaker-sea-horizon", MODELS_DIR / "env-windwaker-sea-horizon.glb"),
    ("model-farm-garden", MODELS_DIR / "model-farm-garden.glb"),
    ("model-npc-placeholder", MODELS_DIR / "model-npc-placeholder.glb"),
    ("model-f22-lighthouse", TRIPO_DIR / "F22-west-cape-lighthouse.glb"),
    ("model-f09-fountain", TRIPO_DIR / "F09-wish-fountain.glb"),
    ("model-e01-pine", TRIPO_DIR / "E01-coastal-pine-tree.glb"),
    ("model-e02-maple", TRIPO_DIR / "E02-autumn-maple-tree.glb"),
    ("model-p01-lamp", TRIPO_DIR / "P01-clay-street-lamp.glb"),
    ("model-p02-mailbox", TRIPO_DIR / "P02-vintage-mailbox.glb"),
    ("model-p03-signpost", TRIPO_DIR / "P03-wooden-signpost.glb"),
    ("model-p05-bakery", TRIPO_DIR / "P05-bakery-food-cart.glb"),
]

COMMON_FLAGS = ["--prefab", PREFAB, "--workspace-id", WS_ID, "--instance", INSTANCE, "--timeout-ms", "180000"]


def run_cli(args: list[str]) -> tuple[int, str]:
    cmd = ["douyin-world", "authoring", *args, *COMMON_FLAGS]
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


def patch_meta_blacklists():
    # 1. model-windwaker-bay
    map_meta = PREFAB_MODELS_DIR / "model-windwaker-bay" / "meta.json"
    if map_meta.exists():
        m = json.loads(map_meta.read_text(encoding="utf-8"))
        m["displayName"] = "风之杖抱月湾连续地形"
        m["summary"] = "平滑四倍抱月湾地形 + 西岬拱桥 + 萤火溪流 + 隐形海界围栏"
        m["nodeMergeBlacklist"] = [
            "Invisible_Sea_Boundary_Main",
            "Invisible_Sea_Boundary_South",
            "WindWaker_Bay_Terrain",
            "F37_West_Arch_Bridge",
            "Firefly_Creek_Water",
        ]
        map_meta.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[META PATCHED] model-windwaker-bay nodeMergeBlacklist")

    # 2. model-farm-garden
    farm_meta = PREFAB_MODELS_DIR / "model-farm-garden" / "meta.json"
    if farm_meta.exists():
        f = json.loads(farm_meta.read_text(encoding="utf-8"))
        f["displayName"] = "抱月湾八格小菜园"
        f["summary"] = "8格可交互小菜园，保留每格干土/湿土与3种作物生长阶段独立节点"
        bl = []
        suffixes = [
            "SoilDry",
            "SoilWet",
            "Stage1_Sprout",
            "Stage2_Growing",
            "Stage3_Radish",
            "Stage3_Berry",
            "Stage3_Sunflower",
        ]
        for i in range(1, 9):
            bl.append(f"Plot_{i}")
            for s in suffixes:
                node_name = f"P{i}_{s}"
                bl.append(f"Plot_{i}/{node_name}")
        f["nodeMergeBlacklist"] = bl
        farm_meta.write_text(json.dumps(f, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[META PATCHED] model-farm-garden nodeMergeBlacklist ({len(bl)} entries)")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    uris = {}

    for res_id, glb_path in RESOURCES:
        assert glb_path.exists(), f"Missing GLB: {glb_path}"
        res_dir = PREFAB_MODELS_DIR / res_id
        if mode in ("all", "import"):
            if (res_dir / "meta.json").exists():
                print(f"[SKIP IMPORT] {res_id} already exists")
            else:
                code, out = run_cli(["resource", "model", "import", res_id, "--glb", str(glb_path)])
                print(f"[IMPORT {code}] {res_id}: {out[:240]}")
                if code != 0:
                    sys.exit(code)

    patch_meta_blacklists()

    if mode == "import":
        return

    for res_id, _ in RESOURCES:
        res_dir = PREFAB_MODELS_DIR / res_id
        rj = res_dir / "package" / "resource.json"
        if rj.exists():
            data = json.loads(rj.read_text(encoding="utf-8"))
            existing_uri = data.get("uri") or data.get("result", {}).get("uri")
            if existing_uri:
                uris[res_id] = existing_uri
                print(f"[SKIP ARCHIVE] {res_id} -> {existing_uri}")
                continue

        if mode in ("all", "check"):
            code_c, out_c = run_cli(["resource", "model", "check", res_id])
            print(f"[CHECK {code_c}] {res_id}: {out_c[:240]}")
            if code_c != 0:
                sys.exit(code_c)

        if mode in ("all", "archive"):
            code_a, out_a = run_cli(["resource", "archive", res_id, "--kind", "model"])
            print(f"[ARCHIVE {code_a}] {res_id}: {out_a[:300]}")
            if code_a != 0:
                sys.exit(code_a)
            if rj.exists():
                data = json.loads(rj.read_text(encoding="utf-8"))
                uris[res_id] = data.get("uri") or data.get("result", {}).get("uri")

    (ROOT / "workspace" / "data" / "windwaker_asset_uris.json").write_text(
        json.dumps(uris, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[DONE] Saved {len(uris)} URIs to windwaker_asset_uris.json")


if __name__ == "__main__":
    main()
