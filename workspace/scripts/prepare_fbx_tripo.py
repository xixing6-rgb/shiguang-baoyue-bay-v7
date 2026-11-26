"""Convert and optimize a local Tripo FBX model to a scene-ready GLB."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector


def import_fbx_meshes(path: Path) -> list:
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.fbx(filepath=str(path))
    return [
        obj for obj in bpy.context.scene.objects
        if obj not in before and obj.type == "MESH"
    ]


def select_meshes(objects: list) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def prepare_fbx_model(path: Path, name: str, height: float, triangles: int, texture_px: int):
    objects = import_fbx_meshes(path)
    if not objects:
        raise ValueError(f"No meshes found in {path}")
    select_meshes(objects)
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(objects) > 1:
        bpy.ops.object.join()
    model = bpy.context.view_layer.objects.active
    model.name = name

    corners = [Vector(point) for point in model.bound_box]
    low = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
    if high.z <= low.z:
        raise ValueError(f"Model has no vertical extent: {path}")
    origin = Vector(((high.x + low.x) / 2, (high.y + low.y) / 2, low.z))
    scale = Matrix.Scale(height / (high.z - low.z), 4)
    model.data.transform(scale @ Matrix.Translation(-origin))

    mesh = model.data
    mesh.calc_loop_triangles()
    original = len(mesh.loop_triangles)
    if original > triangles:
        modifier = model.modifiers.new("Tripo reduction", "DECIMATE")
        modifier.ratio = triangles / original
        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    mesh = model.data
    mesh.calc_loop_triangles()
    reduced = len(mesh.loop_triangles)
    if reduced <= 0 or reduced > triangles * 1.05:
        raise ValueError(f"Unexpected triangle count: {original} -> {reduced}")
    print(f"{name}: {original} -> {reduced} triangles")

    for img in bpy.data.images:
        if img.size[0] == 0 and img.filepath:
            candidate = path.parent / Path(img.filepath).name
            if not candidate.exists():
                for fbm in path.parent.glob("*.fbm"):
                    sub = fbm / Path(img.filepath).name
                    if sub.exists():
                        candidate = sub
                        break
            if candidate.exists():
                img.filepath = str(candidate)
                img.reload()
        w, h = img.size
        if w > 0 and h > 0:
            if max(w, h) > texture_px:
                factor = texture_px / max(w, h)
                img.scale(max(1, round(w * factor)), max(1, round(h * factor)))
            img.pack()
    return model


def export_glb(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        export_yup=True,
        use_selection=True,
        export_image_format="JPEG",
        export_jpeg_quality=90,
        export_materials="EXPORT",
    )
    print(f"{path}: {path.stat().st_size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--height", type=float, required=True)
    parser.add_argument("--triangles", type=int, required=True)
    parser.add_argument("--texture", type=int, default=1024)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

    bpy.ops.wm.read_factory_settings(use_empty=True)
    model = prepare_fbx_model(args.source, args.output.stem, args.height, args.triangles, args.texture)
    select_meshes([model])
    export_glb(args.output)


if __name__ == "__main__":
    main()
