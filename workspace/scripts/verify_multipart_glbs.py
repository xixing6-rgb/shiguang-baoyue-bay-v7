"""Inspect GLB node trees, verify multi-part hierarchy, and emit nodeMergeBlacklist JSON."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


def read_glb_json(glb_path: Path) -> dict:
    with glb_path.open("rb") as f:
        magic, version, total_len = struct.unpack("<III", f.read(12))
        if magic != 0x46546C67 or version != 2:
            raise ValueError(f"Not a glTF 2.0 binary GLB: {glb_path}")
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        if chunk_type != 0x4E4F534A:
            raise ValueError(f"First GLB chunk is not JSON: {glb_path}")
        raw = f.read(chunk_len).decode("utf-8")
    return json.loads(raw)


def collect_node_paths(gltf: dict) -> list[dict]:
    nodes = gltf.get("nodes", [])
    scenes = gltf.get("scenes", [])
    roots = scenes[0].get("nodes", []) if scenes else []
    if not roots and nodes:
        child_set = {c for n in nodes for c in n.get("children", [])}
        roots = [i for i in range(len(nodes)) if i not in child_set]

    records: list[dict] = []

    def walk(idx: int, prefix: str) -> None:
        node = nodes[idx]
        name = node.get("name") or f"Node_{idx}"
        path = f"{prefix}/{name}" if prefix else name
        has_mesh = "mesh" in node
        mesh_tris = 0
        if has_mesh:
            mesh = gltf["meshes"][node["mesh"]]
            for prim in mesh.get("primitives", []):
                if "indices" in prim:
                    acc = gltf["accessors"][prim["indices"]]
                    mesh_tris += acc.get("count", 0) // 3
                elif "POSITION" in prim.get("attributes", {}):
                    acc = gltf["accessors"][prim["attributes"]["POSITION"]]
                    mesh_tris += acc.get("count", 0) // 3
        records.append({
            "index": idx,
            "name": name,
            "path": path,
            "hasMesh": has_mesh,
            "triangles": mesh_tris,
            "translation": node.get("translation"),
            "children": len(node.get("children", [])),
        })
        for c in node.get("children", []):
            walk(c, path)

    for r in roots:
        walk(r, "")
    return records


def build_blacklist(records: list[dict], strip_root: bool = False) -> list[str]:
    """Return nodeMergeBlacklist relative paths preserving all interactive sub-nodes."""
    if len(records) <= 1:
        return []
    paths = [r["path"] for r in records]
    if strip_root and "/" in paths[0]:
        pass
    if strip_root:
        root_prefix = paths[0] + "/"
        trimmed = [p[len(root_prefix):] for p in paths if p.startswith(root_prefix)]
        if trimmed:
            return trimmed
    return paths


def inspect_glb(glb_path: Path, strip_root: bool = False) -> dict:
    gltf = read_glb_json(glb_path)
    records = collect_node_paths(gltf)
    uv_bounds = []
    if gltf.get("accessors"):
        # Check TEXCOORD_0 bounds when present
        for mesh in gltf.get("meshes", []):
            for prim in mesh.get("primitives", []):
                tc_idx = prim.get("attributes", {}).get("TEXCOORD_0")
                if tc_idx is not None:
                    acc = gltf["accessors"][tc_idx]
                    uv_bounds.append({
                        "mesh": mesh.get("name"),
                        "min": acc.get("min"),
                        "max": acc.get("max"),
                    })
    return {
        "file": str(glb_path),
        "sizeBytes": glb_path.stat().st_size,
        "materials": len(gltf.get("materials", [])),
        "images": len(gltf.get("images", [])),
        "totalTriangles": sum(r["triangles"] for r in records),
        "nodes": records,
        "blacklist": build_blacklist(records, strip_root=strip_root),
        "uvBounds": uv_bounds,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("glbs", nargs="+", type=Path)
    parser.add_argument("--strip-root", action="store_true", help="Strip top-level container name when exporting blacklist")
    parser.add_argument("--output-json", type=Path, help="Optional path to write multipart_blacklists.json")
    args = parser.parse_args()

    out = {}
    for p in args.glbs:
        info = inspect_glb(p, strip_root=args.strip_root)
        print(f"=== {p.name} ({info['sizeBytes']} bytes, {info['totalTriangles']} tris, mats={info['materials']}, imgs={info['images']}) ===")
        for n in info["nodes"]:
            print(f"  - {n['path']} [mesh={n['hasMesh']}, tris={n['triangles']}]")
        out[p.stem] = {
            "file": str(p),
            "totalTriangles": info["totalTriangles"],
            "nodeMergeBlacklist": info["blacklist"],
            "uvBounds": info["uvBounds"],
        }

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote blacklist report -> {args.output_json}")


if __name__ == "__main__":
    main()
