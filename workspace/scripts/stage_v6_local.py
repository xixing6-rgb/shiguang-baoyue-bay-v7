"""Stage v6 layout transforms, invisible material voxels, and Lua scripts locally into shiguang-25d-windwaker."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
WPREFAB_DIR = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
    r"\ai-sessions\workspace_024l9gls\wprefabs\shiguang-25d-windwaker"
)
LAYOUT_JSON = ROOT / "workspace" / "data" / "windwaker_clean_layout_v6.json"
VOXELS_JSON = ROOT / "workspace" / "data" / "windwaker_material_voxels.json"
LUA_DIR = ROOT / "workspace" / "scripts" / "lua-25d"

INSTANCE = "1c381f36-58c3-4989-ace4-e89020e8035e"
WS = "workspace_024l9gls"
PREFAB = "shiguang-25d-windwaker"

NEW_SCRIPTS = [
    "terrain-material-trigger.lua",
    "surface-audio-controller.lua",
    "water-motion-controller.lua",
]
ALL_SCRIPTS = ["camera-25d-controller.lua"] + NEW_SCRIPTS


def run_cli(args: list[str]) -> dict:
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
        raise RuntimeError(f"CLI failed ({' '.join(args[:5])}): {raw}")
    return data


def read_header_lines(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8")
    headers = []
    script_id = ""
    for line in text.splitlines()[:5]:
        if line.startswith("---@id ") or line.startswith("---@referenceName "):
            headers.append(line)
            if line.startswith("---@id "):
                script_id = line.split(" ", 1)[1].strip()
    if len(headers) < 2 or not script_id:
        raise RuntimeError(f"Missing ---@id / ---@referenceName header in {path}")
    return script_id, headers


def write_prefab_script(rel_path: str, local_src: Path) -> str:
    target = WPREFAB_DIR / rel_path
    script_id, headers = read_header_lines(target)
    body = local_src.read_text(encoding="utf-8")
    # Strip any accidental id/referenceName headers in local_src
    clean_lines = [
        ln for ln in body.splitlines()
        if not ln.startswith("---@id ") and not ln.startswith("---@referenceName ")
    ]
    merged = "\n".join(headers + clean_lines) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False, encoding="utf-8", newline="\n") as tf:
        tf.write(merged)
        tmp_path = Path(tf.name)
    try:
        run_cli([
            "douyin-world", "authoring", "prefab", "files", "write", str(tmp_path),
            "--prefab", PREFAB, "--path", rel_path,
            "--workspace-id", WS, "--instance", INSTANCE, "--json",
        ])
    finally:
        tmp_path.unlink(missing_ok=True)
    return script_id


def exec_sdk(js_code: str, label: str) -> dict:
    tmp_js = ROOT / "workspace" / "scripts" / f"_tmp_{label}.js"
    tmp_js.write_text(js_code, encoding="utf-8")
    try:
        return run_cli([
            "douyin-world", "authoring", "prefab", "execute", PREFAB,
            "--file", str(tmp_js),
            "--workspace-id", WS, "--instance", INSTANCE, "--json",
        ])
    finally:
        tmp_js.unlink(missing_ok=True)


def main() -> None:
    layout = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    voxels = json.loads(VOXELS_JSON.read_text(encoding="utf-8"))

    # Phase 1: Ensure new script files exist (create only missing ones)
    missing = [s for s in NEW_SCRIPTS if not (WPREFAB_DIR / "scripts" / s).exists()]
    if missing:
        code_scripts = f"""
const toCreate = {json.dumps(missing)};
const created = {{}};
for (const p of toCreate) {{
  created[p] = await scene.scripts.create({{ path: p }});
}}
return {{ created }};
"""
        res1 = exec_sdk(code_scripts, "create_scripts")
        print("[PHASE 1] Created scripts:", list(res1["data"].get("result", {}).get("created", {}).keys()))
    else:
        print("[PHASE 1] All 3 new scripts already exist")

    # Phase 2: Write full Lua contents preserving @id / @referenceName headers
    script_ids = {}
    for s in ALL_SCRIPTS:
        sid = write_prefab_script(f"scripts/{s}", LUA_DIR / s)
        script_ids[s] = sid
        print(f"[PHASE 2] Wrote scripts/{s} (id={sid})")

    # Phase 3: Apply v6 layout transforms + create/rebuild SurfaceMaterialVoxels + SurfaceAudioFollower + WaterMotionController
    code_scene = f"""
const layout = {json.dumps(layout, ensure_ascii=False)};
const voxelNodes = {json.dumps(voxels["nodes"], ensure_ascii=False)};
const scriptIds = {json.dumps(script_ids)};

const qRes = await scene.nodes.query({{ parent: "n1", depth: 1 }}, {{ limit: 200 }});
const byName = new Map();
for (const item of qRes.items) {{
  byName.set(item.name, item.handle);
}}

// Remove stale helper roots if present for idempotency
const toRemove = [];
for (const oldName of ["SurfaceMaterialVoxels", "SurfaceAudioFollower", "WaterMotionController"]) {{
  if (byName.has(oldName)) toRemove.push(byName.get(oldName));
}}
if (toRemove.length > 0) {{
  await scene.nodes.remove({{ nodes: toRemove }});
}}

// Apply clean v6 transforms (preserve FarmGarden fixed position & sub-plots)
let movedCount = 0;
for (const [name, cfg] of Object.entries(layout)) {{
  if (name === "FarmGarden") continue;
  const h = byName.get(name);
  if (!h) throw new Error("Missing expected node in prefab: " + name);
  const rad = (cfg.yawDeg * Math.PI) / 180.0;
  const rot = {{ x: 0, y: Math.sin(rad * 0.5), z: 0, w: Math.cos(rad * 0.5) }};
  const sc = cfg.scale ?? 1.0;
  await scene.transforms.set({{
    nodes: [h],
    value: {{
      position: {{ x: cfg.x, y: cfg.y, z: cfg.z }},
      rotation: rot,
      scale: {{ x: sc, y: sc, z: sc }},
    }},
    space: "world",
    scope: "subtree",
  }});
  movedCount += 1;
}}

// Create SurfaceMaterialVoxels group + 26 invisible triggerData child nodes
const voxelRootRes = await scene.nodes.create({{ name: "SurfaceMaterialVoxels", parent: "n1" }});
const voxelRoot = voxelRootRes.handle || voxelRootRes;
for (const v of voxelNodes) {{
  const cRes = await scene.nodes.create({{ name: v.name, parent: voxelRoot }});
  const vh = cRes.handle || cRes;
  await scene.components.add({{ nodes: [vh], type: "triggerData", values: v.triggers }});
  await scene.scripts.bind({{
    nodes: [vh],
    script: scriptIds["terrain-material-trigger.lua"],
    params: {{ MaterialId: v.material }},
  }});
}}

// Create Resource-scoped controller nodes for surface audio & water motion
await scene.scripts.setScopeRole({{ nodes: ["n1"], role: "host" }});
const audioRes = await scene.nodes.create({{ name: "SurfaceAudioFollower", parent: "n1" }});
const audioNode = audioRes.handle || audioRes;
const waterRes = await scene.nodes.create({{ name: "WaterMotionController", parent: "n1" }});
const waterNode = waterRes.handle || waterRes;
await scene.scripts.setScopeRole({{ nodes: [audioNode, waterNode], role: "resource" }});
await scene.scripts.bind({{ nodes: [audioNode], script: scriptIds["surface-audio-controller.lua"], params: {{}} }});
await scene.scripts.bind({{ nodes: [waterNode], script: scriptIds["water-motion-controller.lua"], params: {{}} }});

return {{
  movedCount,
  voxelRoot,
  voxelNodeCount: voxelNodes.length,
  audioNode,
  waterNode,
}};
"""
    res3 = exec_sdk(code_scene, "apply_v6_scene")
    print("[PHASE 3] SDK staged:", json.dumps(res3.get("data", {}).get("result", {}), ensure_ascii=False))


if __name__ == "__main__":
    main()
