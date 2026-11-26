"""Assemble the v7 character layout and UI on the existing Wind Waker WPrefab."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stage_v6_local import INSTANCE, LUA_DIR, PREFAB, ROOT, WS, run_cli, write_prefab_script

DATA = ROOT / "workspace" / "data"
EXPORT = ROOT / "workspace" / "exports" / "shiguang-25d-windwaker-v7.wprefab"
CHARACTER_NODES = {
    "C01": "NPC_Amu",
    "C02": "NPC_Mianmian",
    "C03": "NPC_C03_Aju",
    "C04": "NPC_C04_Naibao_Unrigged",
    "C05": "NPC_C05_Moyu",
    "C07": "NPC_C07_Tuantuan_Unrigged",
    "C09": "NPC_C09_Rongrong_Unrigged",
}

ASSEMBLE = """
const nodes = await scene.nodes.query({ parent: "n1", depth: 1 }, { limit: 200 });
const byName = new Map(nodes.items.map(node => [node.name, node]));

function required(name) {
  const node = byName.get(name);
  if (!node) throw new Error("Missing author node: " + name);
  return node;
}

async function place(root, cfg) {
  const halfYaw = cfg.yawDeg * Math.PI / 360;
  await scene.transforms.set({
    nodes: [root],
    value: {
      position: { x: cfg.x, y: cfg.y, z: cfg.z },
      rotation: { x: 0, y: Math.sin(halfYaw), z: 0, w: Math.cos(halfYaw) },
      scale: { x: cfg.scale, y: cfg.scale, z: cfg.scale },
    },
    space: "world",
    scope: "subtree",
  });
}

for (const [name, cfg] of Object.entries(input.movedProps)) {
  await place(required(name).handle, cfg);
}

const installed = [];
for (const npc of input.characters) {
  const old = byName.get(npc.name);
  let root;
  if (old) {
    const result = await scene.assets.replaceModel({
      root: old.handle, replacement: npc.uri, name: npc.name,
    });
    root = result.root;
  } else {
    const result = await scene.assets.instantiateModel({
      resource: npc.uri, parent: "n1", name: npc.name,
    });
    root = result.root;
  }
  await place(root, npc.placement);
  if (!npc.rigged) {
    await scene.assets.instantiateModel({
      resource: input.markerUri, parent: root, name: "UnriggedMarker_" + npc.id,
    });
  }
  const colliders = await scene.nodes.query(
    { subtree: root, hasComponent: "physicsColliderData" },
    { limit: 100 },
  );
  if (colliders.items.length) {
    await scene.components.set({
      nodes: colliders.items.map(node => node.handle),
      type: "physicsColliderData",
      values: { enableCollision: false, enableRigidBody: false },
    });
  }
  installed.push({ id: npc.id, name: npc.name, root, rigged: npc.rigged });
}

const uiRoot = required("ui-dialogue-25d").handle;
await scene.components.set({
  nodes: [uiRoot],
  type: "aigcModelData",
  values: { meshRefId: input.uiUri },
});
return { characters: installed, uiRoot, diagnostics: await scene.document.validate() };
"""


def load_json(filename):
    return json.loads((DATA / filename).read_text(encoding="utf-8"))


def author(action, *args):
    return run_cli([
        "douyin-world", "authoring", "prefab", action, PREFAB, *args,
        "--workspace-id", WS, "--instance", INSTANCE, "--json",
    ])["data"]


def main():
    uris = load_json("windwaker_asset_uris.json")
    previous = load_json("windwaker_clean_layout_v6.json")
    layout = load_json("windwaker_clean_layout_v7.json")
    audit = load_json("character_rig_audit.json")
    characters = []
    for npc in audit["characters"]:
        name = CHARACTER_NODES[npc["id"]]
        asset = "model-npc-" + Path(npc["glbPath"]).stem.lower()
        characters.append({
            "id": npc["id"], "name": name, "rigged": npc["rigged"],
            "placement": layout[name], "uri": uris[asset],
        })

    transform_fields = ("x", "y", "z", "yawDeg", "scale")
    moved_props = {
        name: cfg for name, cfg in layout.items()
        if name in previous and cfg["category"] != "npc"
        and any(cfg[field] != previous[name][field] for field in transform_fields)
    }
    payload = {
        "characters": characters, "movedProps": moved_props,
        "markerUri": uris["model-marker-unrigged-badge"], "uiUri": uris["ui-dialogue-25d"],
    }
    for filename in ("camera-25d-controller.lua", "dialogue-25d-ui.lua", "surface-audio-controller.lua"):
        write_prefab_script(f"scripts/{filename}", LUA_DIR / filename)

    revision = author("read", "context.capabilities")["revision"]
    with tempfile.TemporaryDirectory(prefix="shiguang-v7-") as temp:
        operation = Path(temp) / "assemble.js"
        operation.write_text(f"const input = {json.dumps(payload)};\n" + ASSEMBLE, encoding="utf-8")
        assembled = author("execute", "--revision", revision, "--file", str(operation))
    print("[ASSEMBLED]", json.dumps(assembled["result"], ensure_ascii=False), flush=True)
    diagnostics = author("validate")
    print("[VALIDATE]", diagnostics, flush=True)
    if diagnostics.get("items") or diagnostics.get("warnings") or diagnostics.get("result", {}).get("items"):
        raise RuntimeError("Prefab validation reported issues")
    print("[BUILD]", author("build", "--timeout-ms", "180000"), flush=True)
    print("[EXPORT]", author("export", "--out", str(EXPORT), "--timeout-ms", "120000"), flush=True)


if __name__ == "__main__":
    main()
