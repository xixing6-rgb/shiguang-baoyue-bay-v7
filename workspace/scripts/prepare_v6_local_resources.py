"""Copy updated v6 GLBs into shiguang-25d-windwaker and run local check + prepare."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
WPREFAB_DIR = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
    r"\ai-sessions\workspace_024l9gls\wprefabs\shiguang-25d-windwaker"
)
MODELS_SRC = ROOT / "workspace" / "assets" / "models"
TRIPO_SRC = MODELS_SRC / "tripo-optimized"

INSTANCE = "1c381f36-58c3-4989-ace4-e89020e8035e"
WS = "workspace_024l9gls"
PREFAB = "shiguang-25d-windwaker"

MODEL_UPDATES = {
    "model-windwaker-bay":         MODELS_SRC / "map-windwaker-bay.glb",
    "model-windwaker-sea-horizon": MODELS_SRC / "env-windwaker-sea-horizon.glb",
    "model-e01-pine":              TRIPO_SRC / "E01-coastal-pine-tree.glb",
    "model-e02-maple":             TRIPO_SRC / "E02-autumn-maple-tree.glb",
    "model-f09-fountain":          TRIPO_SRC / "F09-wish-fountain.glb",
    "model-f22-lighthouse":        TRIPO_SRC / "F22-west-cape-lighthouse.glb",
    "model-p01-lamp":              TRIPO_SRC / "P01-clay-street-lamp.glb",
    "model-p02-mailbox":           TRIPO_SRC / "P02-vintage-mailbox.glb",
    "model-p03-signpost":          TRIPO_SRC / "P03-wooden-signpost.glb",
    "model-p05-bakery":            TRIPO_SRC / "P05-bakery-food-cart.glb",
}

SEA_BLACKLIST = [
    "WindWaker_Lagoon_Shallows",
    "WindWaker_Endless_Ocean",
    "WW_WaveFoam_Inner",
    "WW_WaveFoam_Outer",
    "WW_SeaSparkle_Layer",
]


def run_json(args: list[str]) -> dict:
    proc = subprocess.run(
        subprocess.list2cmdline(args),
        shell=True,
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
        raise RuntimeError(f"Command failed ({' '.join(args[:5])}): {raw}")
    return data


def main() -> None:
    for rid, src in MODEL_UPDATES.items():
        if not src.exists():
            raise FileNotFoundError(f"Missing GLB: {src}")
        dst_dir = WPREFAB_DIR / "assets" / "models" / rid
        topo_glb = dst_dir / "topology" / "model.glb"
        topo_glb.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, topo_glb)

        if rid == "model-windwaker-sea-horizon":
            meta_p = dst_dir / "meta.json"
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
            meta["nodeMergeBlacklist"] = SEA_BLACKLIST
            meta_p.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        elif rid == "model-windwaker-bay":
            meta_p = dst_dir / "meta.json"
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
            meta["nodeMergeBlacklist"] = [
                "Invisible_Sea_Boundary_Main",
                "Invisible_Sea_Boundary_South",
                "WindWaker_Bay_Terrain",
                "F37_West_Arch_Bridge",
            ]
            meta["summary"] = "平滑四倍抱月湾地形 + 西岬拱桥 + 隐形海界围栏"
            meta_p.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

        chk = run_json([
            "douyin-world", "authoring", "resource", "model", "check", rid,
            "--prefab", PREFAB, "--workspace-id", WS, "--instance", INSTANCE, "--json",
        ])
        prep = run_json([
            "douyin-world", "authoring", "resource", "model", "prepare", rid,
            "--prefab", PREFAB, "--workspace-id", WS, "--instance", INSTANCE, "--json",
        ])
        res = prep.get("data", {}).get("result", {})
        if not res.get("path"):
            raise RuntimeError(f"Unexpected prepare result for {rid}: {prep}")
        nodes = res.get("nodeCount", "?")
        print(f"[MODEL PREPARED] {rid:28s} <- {src.name} (nodes={nodes}, pkg={res['path']})")


if __name__ == "__main__":
    main()
