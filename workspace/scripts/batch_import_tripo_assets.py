"""Batch-import optimized Tripo & assembled multi-part GLBs into shiguang-25d-windwaker.

Reads workspace/data/tripo_batch_manifest.json, imports every existing GLB into the
authoring workspace, patches nodeMergeBlacklist from workspace/data/multipart_blacklists.json,
checks & archives each model, computes exact terrain Y via build_windwaker_terrain.sample_height,
and executes Scene SDK placement/replacement inside shiguang-25d-windwaker.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
sys.path.insert(0, str(ROOT / "workspace" / "scripts"))
from build_windwaker_terrain import sample_height
from verify_multipart_glbs import inspect_glb

MANIFEST_PATH = ROOT / "workspace" / "data" / "tripo_batch_manifest.json"
ASSET_URIS_PATH = ROOT / "workspace" / "data" / "windwaker_asset_uris.json"
BLACKLISTS_PATH = ROOT / "workspace" / "data" / "multipart_blacklists.json"

PREFAB = "shiguang-25d-windwaker"
WS_ID = "workspace_024l9gls"
DEFAULT_INSTANCE = "993d993d-fe6a-44b0-87f9-9c6d2f95ef69"
PREFAB_MODELS_DIR = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
    rf"\ai-sessions\{WS_ID}\wprefabs\{PREFAB}\assets\models"
)


def run_dw(args: list[str], instance: str) -> dict:
    cmd = ["douyin-world", "authoring", *args, "--workspace-id", WS_ID, "--instance", instance, "--timeout-ms", "180000", "--json"]
    proc = subprocess.run(subprocess.list2cmdline(cmd), shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    raw = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if proc.returncode != 0:
        raise RuntimeError(f"CLI failed ({proc.returncode}): {' '.join(args)}\n{raw[:1000]}")
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("{"):
            return json.loads(s)
    return json.loads(raw)


def patch_farm_blacklist(meta_path: Path) -> None:
    m = json.loads(meta_path.read_text(encoding="utf-8"))
    bl = []
    suffixes = ["SoilDry", "SoilWet", "Stage1_Sprout", "Stage2_Growing", "Stage3_Radish", "Stage3_Berry", "Stage3_Sunflower"]
    for i in range(1, 9):
        bl.append(f"Plot_{i}")
        for s in suffixes:
            bl.append(f"Plot_{i}/P{i}_{s}")
    m["nodeMergeBlacklist"] = bl
    meta_path.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", default=DEFAULT_INSTANCE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    uris = json.loads(ASSET_URIS_PATH.read_text(encoding="utf-8")) if ASSET_URIS_PATH.exists() else {}
    blacklists = {}

    import_queue = []
    farm_v5 = ROOT / "workspace/assets/models/tripo-optimized/farm-garden-v5.glb"
    if farm_v5.exists():
        import_queue.append(("model-farm-garden-tripo", farm_v5, "farm", None))

    for item in manifest["batch1_submitted_refs"]:
        if item.get("resourceId"):
            p = ROOT / item["output"]
            if p.exists():
                import_queue.append((item["resourceId"], p, "whole", item))

    for item in manifest["batch2_multipart_and_priority"]["multipart_assets"]:
        p = ROOT / item["output"]
        if p.exists():
            import_queue.append((item["resourceId"], p, "multipart", item))

    for item in manifest["batch2_multipart_and_priority"]["whole_models"]:
        p = ROOT / item["output"]
        if p.exists():
            import_queue.append((item["resourceId"], p, "whole", item))

    print(f"Found {len(import_queue)} ready GLBs for import/update.")
    if args.dry_run:
        for rid, p, kind, _ in import_queue:
            print(f"  [DRY-RUN] {rid} ({kind}) <- {p}")
        return

    for rid, glb_path, kind, _ in import_queue:
        run_dw(["resource", "model", "import", rid, "--glb", str(glb_path), "--prefab", PREFAB], args.instance)
        meta_path = PREFAB_MODELS_DIR / rid / "meta.json"
        if kind == "farm" and meta_path.exists():
            patch_farm_blacklist(meta_path)
        elif kind == "multipart" and meta_path.exists():
            info = inspect_glb(glb_path, strip_root=False)
            blacklists[rid] = info["blacklist"]
            m = json.loads(meta_path.read_text(encoding="utf-8"))
            m["nodeMergeBlacklist"] = info["blacklist"]
            meta_path.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")

        run_dw(["resource", "model", "check", rid, "--prefab", PREFAB], args.instance)
        arch = run_dw(["resource", "archive", rid, "--kind", "model", "--prefab", PREFAB], args.instance)
        uri = arch.get("data", {}).get("uri") or arch.get("uri")
        if uri:
            uris[rid] = uri
            print(f"[ARCHIVED] {rid} -> {uri}")

    ASSET_URIS_PATH.write_text(json.dumps(uris, indent=2, ensure_ascii=False), encoding="utf-8")
    if blacklists:
        BLACKLISTS_PATH.write_text(json.dumps(blacklists, indent=2, ensure_ascii=False), encoding="utf-8")

    # Build Scene SDK placement payload with exact terrain heights
    sdk_items = []
    for rid, _, _, item in import_queue:
        if not item or rid not in uris:
            continue
        if item.get("replaceExisting"):
            sdk_items.append({"op": "replace", "targetName": item["replaceExisting"], "uri": uris[rid]})
        for pl in item.get("placements", []):
            y = sample_height(pl["x"], pl["z"])
            sdk_items.append({
                "op": "place",
                "name": pl["name"],
                "uri": uris[rid],
                "pos": {"x": pl["x"], "y": round(y, 3), "z": pl["z"]},
                "yaw": pl.get("yaw", 0.0),
                "collision": pl.get("collision", True),
            })

    if "model-farm-garden-tripo" in uris and farm_v5.exists():
        sdk_items.insert(0, {"op": "replaceFarm", "targetName": "FarmGarden", "uri": uris["model-farm-garden-tripo"]})

    sdk_source = f"""const ITEMS = {json.dumps(sdk_items, ensure_ascii=False)};
const farmMatches = await scene.nodes.query({{name:{{equals:"FarmGarden"}}}},{{fields:["handle","parent"],limit:3}});
if (farmMatches.items.length !== 1) throw new Error("Expected exactly one FarmGarden");
const parentRoot = farmMatches.items[0].parent;
const out = [];
for (const item of ITEMS) {{
  if (item.op === "replaceFarm") {{
    const oldFarm = farmMatches.items[0];
    const saved = await scene.scripts.bindings([oldFarm.handle]);
    const farmScript = saved.items.find(b => b.filePath === "scripts/farming-plot-system.lua" && b.enabled && !b.readonly);
    if (!farmScript) throw new Error("Missing farm script binding");
    const rep = await scene.assets.replaceModel({{root:oldFarm.handle,replacement:item.uri,name:"FarmGarden"}});
    await scene.scripts.bind({{nodes:[rep.root],script:farmScript.script,params:farmScript.params}});
    out.push({{op:"replaceFarm",root:rep.root}});
  }} else if (item.op === "replace") {{
    const m = await scene.nodes.query({{name:{{equals:item.targetName}}}},{{fields:["handle"],limit:3}});
    if (m.items.length === 1) {{
      const rep = await scene.assets.replaceModel({{root:m.items[0].handle,replacement:item.uri,name:item.targetName}});
      out.push({{op:"replace",name:item.targetName,root:rep.root}});
    }}
  }} else if (item.op === "place") {{
    const existing = await scene.nodes.query({{name:{{equals:item.name}}}},{{fields:["handle"],limit:3}});
    let targetRoot = null;
    if (existing.items.length === 1) {{
      const rep = await scene.assets.replaceModel({{root:existing.items[0].handle,replacement:item.uri,name:item.name}});
      targetRoot = rep.root;
    }} else if (existing.items.length === 0) {{
      const inst = await scene.assets.instantiateModel({{resource:item.uri,parent:parentRoot,name:item.name}});
      targetRoot = inst.root;
    }} else {{
      throw new Error("Multiple matches for " + item.name);
    }}
    const half = item.yaw * Math.PI / 360;
    await scene.transforms.set({{
      nodes:[targetRoot],space:"local",scope:"subtree",
      value:{{position:item.pos,rotation:{{x:0,y:Math.sin(half),z:0,w:Math.cos(half)}},scale:{{x:1,y:1,z:1}}}}
    }});
    if (item.collision === false) {{
      const cols = await scene.nodes.query({{subtree:targetRoot,hasComponent:"physicsColliderData"}},{{fields:["handle"],limit:50}});
      if (cols.items.length) {{
        await scene.components.set({{nodes:cols.items.map(n=>n.handle),type:"physicsColliderData",values:{{enableCollision:false,enableRigidBody:false}}}});
      }}
    }}
    out.push({{op:"place",name:item.name,root:targetRoot}});
  }}
}}
return {{updated:out,diagnostics:await scene.document.validate()}};
"""
    sdk_file = ROOT / "workspace" / "scripts" / "generated_batch_place.js"
    sdk_file.write_text(sdk_source, encoding="utf-8")
    cap = run_dw(["prefab", "read", PREFAB, "context.capabilities"], args.instance)
    rev = cap["data"]["revision"]
    exec_res = run_dw(["prefab", "execute", PREFAB, "--file", str(sdk_file), "--revision", rev], args.instance)
    print("[PREFAB EXECUTE]", json.dumps(exec_res.get("data", {}).get("summary"), ensure_ascii=False))
    val_res = run_dw(["prefab", "validate", PREFAB], args.instance)
    diags = val_res.get("data", {}).get("result", {})
    if diags.get("items") or val_res.get("data", {}).get("warnings"):
        raise RuntimeError(f"Validation diagnostics not empty: {val_res}")
    run_dw(["prefab", "build", PREFAB], args.instance)
    arch_prefab = run_dw(["result", "archive", PREFAB, "--name", "时光小筑2.5D风之杖抱月湾"], args.instance)
    print("[WPREFAB ARCHIVED]", json.dumps(arch_prefab, ensure_ascii=False))


if __name__ == "__main__":
    main()
