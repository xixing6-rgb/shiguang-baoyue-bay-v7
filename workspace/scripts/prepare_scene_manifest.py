"""Build grounded scene placement manifest by sampling windwaker terrain height at every prop (x, z)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
SCRIPTS_DIR = ROOT / "workspace" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_windwaker_terrain import sample_height  # noqa: E402

COTTAGE_URI = (
    "hamlet-ugc/aigc_editor/dev/unity/"
    "MS4wLjABAAAAyvqdmrGLNT202gjmywqj-uY-M27N9cGwNr7K4ldqN2A7wZZqLTIKeW74rX46XC3f/"
    "ptytoyd68l8ke9hv.glb"
)

PREFAB_DIR = Path(
    r"C:\Users\Administrator\AppData\Roaming\AI World Creator\projects\project-9c69f507-5375-4486-83fc-d3f150502390"
    r"\ai-sessions\workspace_024l9gls\wprefabs\shiguang-25d-windwaker"
)


def read_resource_uri(kind_dir: str, res_id: str) -> str:
    rj = PREFAB_DIR / "assets" / kind_dir / res_id / "package" / "resource.json"
    assert rj.exists(), f"Missing archived resource.json: {rj}"
    data = json.loads(rj.read_text(encoding="utf-8"))
    uri = data.get("uri") or data.get("result", {}).get("uri") or data.get("resourceUri")
    assert isinstance(uri, str) and uri.strip(), f"No uri found in {rj}: {data}"
    return uri.strip()


def grounded(x: float, z: float, sink: float = 0.04) -> list[float]:
    y = float(sample_height(x, z)) - sink
    return [round(x, 3), round(y, 3), round(z, 3)]


def main():
    uris = {
        "ui": read_resource_uri("uis", "ui-dialogue-25d"),
        "map_bay": read_resource_uri("models", "model-windwaker-bay"),
        "sea_horizon": read_resource_uri("models", "model-windwaker-sea-horizon"),
        "farm_garden": read_resource_uri("models", "model-farm-garden"),
        "npc_placeholder": read_resource_uri("models", "model-npc-placeholder"),
        "cottage": COTTAGE_URI,
        "f22_lighthouse": read_resource_uri("models", "model-f22-lighthouse"),
        "f09_fountain": read_resource_uri("models", "model-f09-fountain"),
        "e01_pine": read_resource_uri("models", "model-e01-pine"),
        "e02_maple": read_resource_uri("models", "model-e02-maple"),
        "p01_lamp": read_resource_uri("models", "model-p01-lamp"),
        "p02_mailbox": read_resource_uri("models", "model-p02-mailbox"),
        "p03_signpost": read_resource_uri("models", "model-p03-signpost"),
        "p05_bakery": read_resource_uri("models", "model-p05-bakery"),
    }

    placements = [
        {"id": "Cottage_Main", "resKey": "cottage", "pos": grounded(-7.5, 5.5, 0.04), "yawDeg": 180.0, "collision": True},
        {"id": "FarmGarden", "resKey": "farm_garden", "pos": grounded(4.5, 9.0, 0.02), "yawDeg": 0.0, "collision": True, "role": "farm"},
        {"id": "F09_WishFountain", "resKey": "f09_fountain", "pos": grounded(13.5, 1.5, 0.04), "yawDeg": 0.0, "collision": True},
        {"id": "F22_WestLighthouse", "resKey": "f22_lighthouse", "pos": grounded(-54.0, -24.0, 0.05), "yawDeg": 35.0, "collision": True},
        {"id": "P05_BakeryCart", "resKey": "p05_bakery", "pos": grounded(-1.5, 0.2, 0.04), "yawDeg": -160.0, "collision": True},
        {"id": "P02_Mailbox", "resKey": "p02_mailbox", "pos": grounded(-3.8, 4.2, 0.04), "yawDeg": 180.0, "collision": True},
        {"id": "P03_Signpost", "resKey": "p03_signpost", "pos": grounded(2.2, -3.5, 0.04), "yawDeg": 170.0, "collision": True},
        # Cozy coastal lamps along courtyard -> dock -> farm -> paths
        {"id": "P01_Lamp_CourtyardS", "resKey": "p01_lamp", "pos": grounded(-1.8, -5.5, 0.04), "yawDeg": 180.0, "collision": True},
        {"id": "P01_Lamp_Dock", "resKey": "p01_lamp", "pos": grounded(-4.2, -19.0, 0.04), "yawDeg": 165.0, "collision": True},
        {"id": "P01_Lamp_FarmW", "resKey": "p01_lamp", "pos": grounded(-0.6, 8.6, 0.04), "yawDeg": 90.0, "collision": True},
        {"id": "P01_Lamp_BridgeN", "resKey": "p01_lamp", "pos": grounded(-28.0, -20.5, 0.04), "yawDeg": 20.0, "collision": True},
        # NPC Placeholders (until user's full rigged models arrive)
        {"id": "NPC_Amu", "resKey": "npc_placeholder", "pos": grounded(-2.5, 3.6, 0.02), "yawDeg": 165.0, "collision": True, "role": "npc"},
        {"id": "NPC_Mianmian", "resKey": "npc_placeholder", "pos": grounded(9.8, 5.8, 0.02), "yawDeg": -145.0, "collision": True, "role": "npc"},
        # Wind-Waker coastal pines (E01) & warm autumn maples (E02) distributed on scenic bluffs away from paths/farm
        {"id": "E01_Pine_NW1", "resKey": "e01_pine", "pos": grounded(-19.5, 11.0, 0.08), "yawDeg": 18.0, "scale": 1.05, "collision": True},
        {"id": "E01_Pine_NW2", "resKey": "e01_pine", "pos": grounded(-26.0, 4.0, 0.08), "yawDeg": 95.0, "scale": 0.92, "collision": True},
        {"id": "E01_Pine_WestBluff1", "resKey": "e01_pine", "pos": grounded(-46.5, -14.0, 0.08), "yawDeg": -40.0, "scale": 1.10, "collision": True},
        {"id": "E01_Pine_WestBluff2", "resKey": "e01_pine", "pos": grounded(-57.5, -31.5, 0.08), "yawDeg": 65.0, "scale": 0.95, "collision": True},
        {"id": "E01_Pine_EastBluff1", "resKey": "e01_pine", "pos": grounded(36.0, -8.5, 0.08), "yawDeg": -70.0, "scale": 1.08, "collision": True},
        {"id": "E01_Pine_EastBluff2", "resKey": "e01_pine", "pos": grounded(49.0, -18.0, 0.08), "yawDeg": 30.0, "scale": 0.96, "collision": True},
        {"id": "E01_Pine_SouthIslet1", "resKey": "e01_pine", "pos": grounded(-9.5, -47.0, 0.08), "yawDeg": 120.0, "scale": 0.90, "collision": True},
        {"id": "E01_Pine_SouthIslet2", "resKey": "e01_pine", "pos": grounded(8.5, -45.5, 0.08), "yawDeg": -25.0, "scale": 0.95, "collision": True},
        {"id": "E02_Maple_CourtyardN", "resKey": "e02_maple", "pos": grounded(14.5, 14.5, 0.08), "yawDeg": 45.0, "scale": 1.02, "collision": True},
        {"id": "E02_Maple_NorthHill1", "resKey": "e02_maple", "pos": grounded(-12.0, 48.0, 0.08), "yawDeg": -80.0, "scale": 1.12, "collision": True},
        {"id": "E02_Maple_NorthHill2", "resKey": "e02_maple", "pos": grounded(12.5, 49.0, 0.08), "yawDeg": 15.0, "scale": 1.05, "collision": True},
        {"id": "E02_Maple_CreekN", "resKey": "e02_maple", "pos": grounded(-28.0, 32.0, 0.08), "yawDeg": 140.0, "scale": 0.98, "collision": True},
        {"id": "E02_Maple_EastUpland", "resKey": "e02_maple", "pos": grounded(32.0, 26.0, 0.08), "yawDeg": -55.0, "scale": 1.04, "collision": True},
        {"id": "E02_Maple_SouthIslet3", "resKey": "e02_maple", "pos": grounded(-1.5, -51.0, 0.08), "yawDeg": 72.0, "scale": 0.88, "collision": True},
    ]

    manifest = {"uris": uris, "placements": placements}
    out_path = ROOT / "workspace" / "data" / "windwaker_scene_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[MANIFEST OK] {len(placements)} placements saved to {out_path}")

    js_template = """// Auto-generated Scene SDK assembly script for shiguang-25d-windwaker
const MANIFEST = __MANIFEST_JSON__;

function yawQuat(yawDeg) {
  const rad = (yawDeg || 0) * Math.PI / 180.0;
  return { x: 0, y: Math.sin(rad * 0.5), z: 0, w: Math.cos(rad * 0.5) };
}

async function querySubtreeNodes(rootHandle, filterExtra) {
  const items = [];
  let cursor;
  do {
    const page = await scene.nodes.query(
      { subtree: rootHandle, ...(filterExtra || {}) },
      { fields: ["handle", "name", "componentTypes"], limit: 100, ...(cursor ? { cursor } : {}) }
    );
    items.push(...page.items);
    cursor = page.nextCursor;
  } while (cursor);
  return items;
}

async function setNodesCollision(nodes, enabled) {
  const withCol = nodes.filter((n) => n.componentTypes.includes("physicsColliderData")).map((n) => n.handle);
  const withoutCol = nodes.filter((n) => !n.componentTypes.includes("physicsColliderData")).map((n) => n.handle);
  if (withCol.length) {
    await scene.components.set({
      nodes: withCol,
      type: "physicsColliderData",
      values: { enableCollision: enabled, enableRigidBody: false },
    });
  }
  if (enabled && withoutCol.length) {
    await scene.components.add({
      nodes: withoutCol,
      type: "physicsColliderData",
      values: { enableCollision: true, enableRigidBody: false },
    });
  }
}

async function setSubtreeAppearanceInvisible(nodes) {
  const withApp = nodes.filter((n) => n.componentTypes.includes("appearanceData")).map((n) => n.handle);
  const withoutApp = nodes.filter((n) => !n.componentTypes.includes("appearanceData")).map((n) => n.handle);
  if (withApp.length) {
    await scene.components.set({
      nodes: withApp,
      type: "appearanceData",
      values: { transparency: 0, castShadows: false },
    });
  }
  if (withoutApp.length) {
    await scene.components.add({
      nodes: withoutApp,
      type: "appearanceData",
      values: { transparency: 0, castShadows: false },
    });
  }
}

const existingRoots = (await scene.nodes.query({ name: { equals: "时光小筑2.5D风之杖抱月湾" } }, { fields: ["handle"], limit: 10 })).items;
if (existingRoots.length > 0) {
  throw new Error("Root 时光小筑2.5D风之杖抱月湾 already exists; aborting duplicate assembly");
}

const root = await scene.nodes.create({ name: "时光小筑2.5D风之杖抱月湾", parent: null });
await scene.scripts.setScopeRole({ nodes: [root], role: "host" });

// 1. Instantiate Map Terrain (keep collision ON; turn off collision on creek water; make sea boundary invisible)
const mapInst = await scene.assets.instantiateModel({
  resource: MANIFEST.uris.map_bay,
  parent: root,
  name: "Map_WindWaker_Bay",
});
const mapNodes = await querySubtreeNodes(mapInst.root);
const creekNodes = mapNodes.filter((n) => n.name.includes("Firefly_Creek_Water"));
const boundaryNodes = mapNodes.filter((n) => n.name.includes("Invisible_Sea_Boundary"));
if (creekNodes.length) {
  await setNodesCollision(creekNodes, false);
}
if (boundaryNodes.length) {
  await setNodesCollision(boundaryNodes, true);
  await setSubtreeAppearanceInvisible(boundaryNodes);
}

// 2. Instantiate Endless Ocean & Distant Horizon Silhouettes (collision completely OFF)
const seaInst = await scene.assets.instantiateModel({
  resource: MANIFEST.uris.sea_horizon,
  parent: root,
  name: "Env_WindWaker_SeaHorizon",
});
const seaNodes = await querySubtreeNodes(seaInst.root, { hasComponent: "physicsColliderData" });
if (seaNodes.length) {
  await setNodesCollision(seaNodes, false);
}

// 3. Instantiate Props, Landmarks, Farm Garden & NPC Placeholders
let farmRootHandle = null;
const spawned = [];
for (const item of MANIFEST.placements) {
  const resUri = MANIFEST.uris[item.resKey];
  if (!resUri) throw new Error("Missing URI for resKey: " + item.resKey);
  const inst = await scene.assets.instantiateModel({
    resource: resUri,
    parent: root,
    name: item.id,
  });
  const sc = item.scale || 1.0;
  await scene.transforms.set({
    nodes: [inst.root],
    space: "local",
    scope: "subtree",
    value: {
      position: { x: item.pos[0], y: item.pos[1], z: item.pos[2] },
      rotation: yawQuat(item.yawDeg || 0),
      scale: { x: sc, y: sc, z: sc },
    },
  });
  if (item.collision === false) {
    const sub = await querySubtreeNodes(inst.root, { hasComponent: "physicsColliderData" });
    await setNodesCollision(sub, false);
  }
  if (item.role === "farm") {
    farmRootHandle = inst.root;
  }
  spawned.push({ id: item.id, root: inst.root });
}
if (!farmRootHandle) throw new Error("FarmGarden handle not found after instantiation");

// 4. Instantiate Runtime UI
const uiInst = await scene.assets.instantiateUI({
  resource: MANIFEST.uris.ui,
  parent: root,
});

// 5. Register 3 Lua scripts and bind to Host / FarmGarden / UI
const camScript = await scene.scripts.create({ path: "camera-25d-controller.lua" });
const farmScript = await scene.scripts.create({ path: "farming-plot-system.lua" });
const uiScript = await scene.scripts.create({ path: "dialogue-25d-ui.lua" });

await scene.scripts.bind({ nodes: [root], script: camScript.handle, params: {} });
await scene.scripts.bind({ nodes: [farmRootHandle], script: farmScript.handle, params: {} });
await scene.scripts.bind({ nodes: [uiInst.root], script: uiScript.handle, params: {} });

const diagnostics = await scene.document.validate();
return {
  root,
  mapRoot: mapInst.root,
  seaRoot: seaInst.root,
  farmRoot: farmRootHandle,
  uiRoot: uiInst.root,
  spawnedCount: spawned.length,
  scripts: {
    camera: camScript,
    farm: farmScript,
    ui: uiScript,
  },
  diagnostics,
};
"""
    js_out = ROOT / "workspace" / "scripts" / "assemble_windwaker_prefab.js"
    js_out.write_text(js_template.replace("__MANIFEST_JSON__", json.dumps(manifest, indent=2, ensure_ascii=False)), encoding="utf-8")
    print(f"[JS OK] Generated {js_out}")



if __name__ == "__main__":
    main()
