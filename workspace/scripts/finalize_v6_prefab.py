"""Finalize WPrefab v6: replaceModel for updated GLBs, bind published URIs, validate, build, archive, and export."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
URIS_PATH = ROOT / "workspace" / "data" / "windwaker_asset_uris.json"
LAYOUT_PATH = ROOT / "workspace" / "data" / "windwaker_clean_layout_v6.json"
EXPORT_PATH = ROOT / "workspace" / "exports" / "shiguang-25d-windwaker-v6.wprefab"

INSTANCE = "1c381f36-58c3-4989-ace4-e89020e8035e"
WS = "workspace_024l9gls"
PREFAB = "shiguang-25d-windwaker"
CLEAN_ENV = {k: v for k, v in os.environ.items() if "PROXY" not in k.upper()}

REPLACE_MAP = {
    "Map_WindWaker_Bay": "model-windwaker-bay",
    "Env_WindWaker_SeaHorizon": "model-windwaker-sea-horizon",
    "F09_WishFountain": "model-f09-fountain",
    "F22_WestLighthouse": "model-f22-lighthouse",
    "P05_BakeryCart": "model-p05-bakery",
    "P02_Mailbox": "model-p02-mailbox",
    "P03_Signpost": "model-p03-signpost",
    "P01_Lamp_CourtyardS": "model-p01-lamp",
    "P01_Lamp_Dock": "model-p01-lamp",
    "P01_Lamp_FarmW": "model-p01-lamp",
    "P01_Lamp_BridgeN": "model-p01-lamp",
    "E01_Pine_NW1": "model-e01-pine",
    "E01_Pine_NW2": "model-e01-pine",
    "E01_Pine_WestBluff1": "model-e01-pine",
    "E01_Pine_WestBluff2": "model-e01-pine",
    "E01_Pine_EastBluff1": "model-e01-pine",
    "E01_Pine_EastBluff2": "model-e01-pine",
    "E01_Pine_SouthIslet1": "model-e01-pine",
    "E01_Pine_SouthIslet2": "model-e01-pine",
    "E02_Maple_CourtyardN": "model-e02-maple",
    "E02_Maple_NorthHill1": "model-e02-maple",
    "E02_Maple_NorthHill2": "model-e02-maple",
    "E02_Maple_CreekN": "model-e02-maple",
    "E02_Maple_EastUpland": "model-e02-maple",
    "E02_Maple_SouthIslet3": "model-e02-maple",
}


def run_cli(args: list[str]) -> dict:
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
        raise RuntimeError(f"CLI failed ({' '.join(args[:5])}): {raw}")
    return data


def main() -> None:
    uris = json.loads(URIS_PATH.read_text(encoding="utf-8"))
    layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    repl_uris = {node: uris[rkey] for node, rkey in REPLACE_MAP.items()}

    js_code = f"""
const replUris = {json.dumps(repl_uris)};
const layout = {json.dumps(layout, ensure_ascii=False)};
const audioUris = {{
  GrassSound: {{ uri: {json.dumps(uris["audio-footstep-grass"])} }},
  SandSound: {{ uri: {json.dumps(uris["audio-footstep-sand"])} }},
  WaterSound: {{ uri: {json.dumps(uris["audio-footstep-water"])} }},
  WaveSound: {{ uri: {json.dumps(uris["audio-ambient-waves"])} }},
}};
const effectUris = {{
  WaterRippleEffect: {{ uri: {json.dumps(uris["effect-water-ripple"])} }},
}};

const qTop = await scene.nodes.query({{ parent: "n1", depth: 1 }}, {{ limit: 200 }});
const byName = new Map();
for (const item of qTop.items) byName.set(item.name, item.handle);

const replacedRoots = {{}};
for (const [nodeName, uri] of Object.entries(replUris)) {{
  const h = byName.get(nodeName);
  if (!h) throw new Error("Node not found for replaceModel: " + nodeName);
  const res = await scene.assets.replaceModel({{ root: h, replacement: uri, name: nodeName }});
  const newRoot = res.root || res;
  replacedRoots[nodeName] = newRoot;
  byName.set(nodeName, newRoot);
}}

// Ensure Map_WindWaker_Bay & Env_WindWaker_SeaHorizon transforms and collider/appearance rules
const bayRoot = byName.get("Map_WindWaker_Bay");
const seaRoot = byName.get("Env_WindWaker_SeaHorizon");
await scene.transforms.set({{
  nodes: [bayRoot, seaRoot],
  value: {{ position: {{ x: 0, y: 0, z: 0 }}, rotation: {{ x: 0, y: 0, z: 0, w: 1 }}, scale: {{ x: 1, y: 1, z: 1 }} }},
  space: "world",
  scope: "subtree",
}});

const baySub = await scene.nodes.query({{ subtree: bayRoot }}, {{ limit: 200 }});
let boundaryConfigured = 0;
for (const item of baySub.items) {{
  if (item.name === "Invisible_Sea_Boundary_Main" || item.name === "Invisible_Sea_Boundary_South") {{
    if (item.componentTypes && item.componentTypes.includes("physicsColliderData")) {{
      await scene.components.set({{ nodes: [item.handle], type: "physicsColliderData", values: {{ enableCollision: true }} }});
    }} else {{
      await scene.components.add({{ nodes: [item.handle], type: "physicsColliderData", values: {{ enableCollision: true }} }});
    }}
    if (item.componentTypes && item.componentTypes.includes("appearanceData")) {{
      await scene.components.set({{ nodes: [item.handle], type: "appearanceData", values: {{ transparency: 0, castShadows: false }} }});
    }} else {{
      await scene.components.add({{ nodes: [item.handle], type: "appearanceData", values: {{ transparency: 0, castShadows: false }} }});
    }}
    boundaryConfigured += 1;
  }} else if (item.name === "WindWaker_Bay_Terrain" || item.name === "F37_West_Arch_Bridge") {{
    if (item.componentTypes && item.componentTypes.includes("physicsColliderData")) {{
      await scene.components.set({{ nodes: [item.handle], type: "physicsColliderData", values: {{ enableCollision: true }} }});
    }}
  }}
}}

const seaSub = await scene.nodes.query({{ subtree: seaRoot }}, {{ limit: 250 }});
let seaCollidersDisabled = 0;
for (const item of seaSub.items) {{
  if (item.componentTypes && item.componentTypes.includes("physicsColliderData")) {{
    await scene.components.set({{ nodes: [item.handle], type: "physicsColliderData", values: {{ enableCollision: false }} }});
    seaCollidersDisabled += 1;
  }}
}}

// Re-apply v6 world transforms on all 55 non-farm objects
let relaidCount = 0;
for (const [name, cfg] of Object.entries(layout)) {{
  if (name === "FarmGarden") continue;
  const h = byName.get(name);
  if (!h) throw new Error("Missing node after replaceModel: " + name);
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
  relaidCount += 1;
}}

// Bind published audio & effect URIs onto SurfaceAudioFollower & WaterMotionController
const audioNode = byName.get("SurfaceAudioFollower");
const waterNode = byName.get("WaterMotionController");
if (!audioNode || !waterNode) throw new Error("Missing SurfaceAudioFollower or WaterMotionController");

const bAudio = await scene.scripts.bindings([audioNode], {{ limit: 20 }});
const bWater = await scene.scripts.bindings([waterNode], {{ limit: 20 }});
let audioBinding = null;
let waterBinding = null;
for (const b of bAudio.items) {{
  if (String(b.filePath || "").includes("surface-audio-controller")) audioBinding = b.handle;
}}
for (const b of bWater.items) {{
  if (String(b.filePath || "").includes("water-motion-controller")) waterBinding = b.handle;
}}
if (!audioBinding || !waterBinding) throw new Error("Could not find audio/water script bindings");

await scene.scripts.setParams({{ bindings: [audioBinding], values: audioUris }});
await scene.scripts.setParams({{ bindings: [waterBinding], values: effectUris }});

return {{
  replacedCount: Object.keys(replacedRoots).length,
  boundaryConfigured,
  seaCollidersDisabled,
  relaidCount,
  audioBinding,
  waterBinding,
}};
"""
    tmp_js = ROOT / "workspace" / "scripts" / "_tmp_finalize_v6.js"
    tmp_js.write_text(js_code, encoding="utf-8")
    try:
        exec_res = run_cli([
            "douyin-world", "authoring", "prefab", "execute", PREFAB,
            "--file", str(tmp_js),
            "--workspace-id", WS, "--instance", INSTANCE, "--json",
        ])
    finally:
        tmp_js.unlink(missing_ok=True)
    print("[SDK FINALIZE]", json.dumps(exec_res.get("data", {}).get("result", {}), ensure_ascii=False), flush=True)

    val_res = run_cli([
        "douyin-world", "authoring", "prefab", "validate", PREFAB,
        "--workspace-id", WS, "--instance", INSTANCE, "--json",
    ])
    val_items = val_res.get("data", {}).get("result", {}).get("items", [])
    val_warns = val_res.get("data", {}).get("warnings", [])
    print(f"[VALIDATE] items={len(val_items)}, warnings={len(val_warns)}", flush=True)
    if val_items or val_warns:
        raise RuntimeError(f"Validate returned issues: {val_res}")

    build_res = run_cli([
        "douyin-world", "authoring", "prefab", "build", PREFAB,
        "--workspace-id", WS, "--instance", INSTANCE, "--json",
    ])
    print("[BUILD OK]", json.dumps(build_res.get("data", {}), ensure_ascii=False), flush=True)

    arch_res = run_cli([
        "douyin-world", "authoring", "result", "archive", PREFAB,
        "--workspace-id", WS, "--instance", INSTANCE, "--timeout-ms", "180000", "--json",
    ])
    print("[ARCHIVE RESULT]", json.dumps(arch_res.get("data", {}), ensure_ascii=False), flush=True)

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    exp_res = run_cli([
        "douyin-world", "authoring", "prefab", "export", PREFAB,
        "--out", str(EXPORT_PATH),
        "--workspace-id", WS, "--instance", INSTANCE, "--json",
    ])
    print("[EXPORT OK]", EXPORT_PATH, json.dumps(exp_res.get("data", {}), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
