r"""Assemble multi-part Tripo GLBs in Blender 5.3 with clean pivots for Lua interaction.

Usage:
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b --python workspace/scripts/assemble_multipart_models.py -- --test-flag-only
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b --python workspace/scripts/assemble_multipart_models.py -- --spec workspace/data/multipart_assembly_spec.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_and_join_part(glb_path: Path, name: str, target_tris: int, texture_px: int = 1024):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    meshes = [o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"]
    if not meshes:
        raise ValueError(f"No mesh objects imported from {glb_path}")
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name

    # Clean up unused empties created by glTF import
    for o in list(bpy.context.scene.objects):
        if o not in before and o != obj and o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)

    mesh = obj.data
    mesh.calc_loop_triangles()
    orig = len(mesh.loop_triangles)
    if orig > target_tris:
        mod = obj.modifiers.new("PartDecimate", "DECIMATE")
        mod.ratio = target_tris / orig
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mesh = obj.data
        mesh.calc_loop_triangles()
    print(f"  [PART] {name}: {orig} -> {len(mesh.loop_triangles)} tris")

    for img in bpy.data.images:
        w, h = img.size
        if w > 0 and h > 0:
            if max(w, h) > texture_px:
                factor = texture_px / max(w, h)
                img.scale(max(1, round(w * factor)), max(1, round(h * factor)))
            img.pack()
    return obj


def bbox_bounds(obj) -> tuple[Vector, Vector]:
    vertices = [vertex.co for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[i] for point in vertices) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in vertices) for i in range(3)))
    return low, high


def mesh_surface(obj) -> BVHTree:
    return BVHTree.FromPolygons(
        [vertex.co for vertex in obj.data.vertices],
        [tuple(face.vertices) for face in obj.data.polygons],
    )


def normalize_part_origin_bottom_center(obj, height: float | None = None, width: float | None = None) -> Vector:
    low, high = bbox_bounds(obj)
    ext = high - low
    if ext.z <= 1e-5:
        raise ValueError(f"Zero height for {obj.name}")
    scale_factor = 1.0
    if height is not None:
        scale_factor = height / ext.z
    elif width is not None:
        scale_factor = width / max(ext.x, ext.y, 1e-5)
    origin = Vector(((low.x + high.x) * 0.5, (low.y + high.y) * 0.5, low.z))
    obj.data.transform(Matrix.Scale(scale_factor, 4) @ Matrix.Translation(-origin))
    _, new_high = bbox_bounds(obj)
    return new_high


def normalize_part_origin_center(obj, span: float, axis: str = "x") -> tuple[Vector, Vector]:
    low, high = bbox_bounds(obj)
    ext = high - low
    ref = ext.x if axis == "x" else (ext.y if axis == "y" else ext.z)
    scale_factor = span / max(ref, 1e-5)
    center = (low + high) * 0.5
    obj.data.transform(Matrix.Scale(scale_factor, 4) @ Matrix.Translation(-center))
    return bbox_bounds(obj)


def normalize_part_origin_top_center(obj, height: float) -> tuple[Vector, Vector]:
    low, high = bbox_bounds(obj)
    ext = high - low
    scale_factor = height / max(ext.z, 1e-5)
    top_center = Vector(((low.x + high.x) * 0.5, (low.y + high.y) * 0.5, high.z))
    obj.data.transform(Matrix.Scale(scale_factor, 4) @ Matrix.Translation(-top_center))
    return bbox_bounds(obj)


def create_pixel_flag_cloth(name: str = "FlagClothPivot", width: float = 0.95, height: float = 0.95):
    """Build a gently waved flag mesh with origin at pole attachment edge and exact [0,1]x[0,1] UVs."""
    bm = bmesh.new()
    nx, ny = 8, 8
    verts = []
    for iy in range(ny + 1):
        row = []
        v = iy / ny
        z = (v - 1.0) * height  # hangs downward from z=0 top crossbar
        for ix in range(nx + 1):
            u = ix / nx
            x = u * width
            # Gentle sinusoidal ripple increasing away from the pole (u=0 stays pinned)
            y = 0.045 * math.sin(u * math.pi * 1.5) * u
            row.append(bm.verts.new((x, y, z)))
        verts.append(row)

    uv_layer = bm.loops.layers.uv.new("UVMap")
    for iy in range(ny):
        for ix in range(nx):
            v00 = verts[iy][ix]
            v10 = verts[iy][ix + 1]
            v11 = verts[iy + 1][ix + 1]
            v01 = verts[iy + 1][ix]
            face = bm.faces.new((v00, v10, v11, v01))
            uvs = [
                (ix / nx, iy / ny),
                ((ix + 1) / nx, iy / ny),
                ((ix + 1) / nx, (iy + 1) / ny),
                (ix / nx, (iy + 1) / ny),
            ]
            for loop, uv in zip(face.loops, uvs):
                loop[uv_layer].uv = uv

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    mat = bpy.data.materials.new("FlagClothMat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.996, 0.961, 0.894, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.85
    mat.use_backface_culling = False
    mesh.materials.append(mat)

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def export_hierarchy(objects: list, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=str(out_path),
        export_format="GLB",
        export_yup=True,
        use_selection=True,
        export_image_format="JPEG",
        export_jpeg_quality=90,
        export_materials="EXPORT",
    )
    print(f"[EXPORT] {out_path} ({out_path.stat().st_size} bytes)")


def assemble_f15(spec: dict, out_path: Path) -> None:
    clear_scene()
    tower = import_and_join_part(Path(spec["tower"]), "F15_Tower", 14000)
    t_high = normalize_part_origin_bottom_center(tower, height=8.5)
    blades = import_and_join_part(Path(spec["blades"]), "F15_BladesPivot", 6000)
    normalize_part_origin_center(blades, span=4.6, axis="x")
    hub_band = [
        vertex.co for vertex in tower.data.vertices
        if t_high.z * 0.62 <= vertex.co.z <= t_high.z * 0.72
    ]
    hub_radius = max(point.xy.length for point in hub_band)
    hub_tips = [point for point in hub_band if point.xy.length >= hub_radius - 0.12]
    hub = sum(hub_tips, Vector()) / len(hub_tips)
    outward = Vector((hub.x, hub.y, 0)).normalized()
    blades.location = hub + outward * 0.28
    blades.rotation_euler.z = math.atan2(outward.y, outward.x) + math.pi / 2
    export_hierarchy([tower, blades], out_path)


def assemble_f14(spec: dict, out_path: Path) -> None:
    clear_scene()
    pergola = import_and_join_part(Path(spec["pergola"]), "F14_Pergola", 10000)
    p_high = normalize_part_origin_bottom_center(pergola, height=3.2)
    swing = import_and_join_part(Path(spec["swing"]), "F14_SwingPivot", 5000)
    normalize_part_origin_top_center(swing, height=1.65)
    swing.location = (0.0, 0.0, p_high.z * 0.72)
    export_hierarchy([pergola, swing], out_path)


def assemble_f17(spec: dict, out_path: Path) -> None:
    clear_scene()
    tree = import_and_join_part(Path(spec["tree"]), "F17_Tree", 10000)
    t_high = normalize_part_origin_bottom_center(tree, height=4.4)
    peach = import_and_join_part(Path(spec["fruit"]), "F17_Fruit_1", 800)
    normalize_part_origin_top_center(peach, height=0.44)

    t_low, _ = bbox_bounds(tree)
    canopy = mesh_surface(tree)
    offsets = [
        (-0.82, t_high.z * 0.59),
        (0.76, t_high.z * 0.69),
        (0.05, t_high.z * 0.80),
    ]
    fruits = []
    for idx, (x, z) in enumerate(offsets, 1):
        branch, _, _, _ = canopy.ray_cast((x, t_low.y - 1.0, z), (0, 1, 0))
        if branch is None:
            raise ValueError(f"No canopy surface for fruit {idx}")
        if idx == 1:
            inst = peach
        else:
            inst = peach.copy()
            inst.data = peach.data
            inst.name = f"F17_Fruit_{idx}"
            bpy.context.collection.objects.link(inst)
        inst.location = branch + Vector((0, -0.08, 0))
        fruits.append(inst)
    export_hierarchy([tree, *fruits], out_path)


def assemble_f06(spec: dict, out_path: Path) -> None:
    clear_scene()
    planter = import_and_join_part(Path(spec["planter"]), "F06_Planter", 6000)
    p_high = normalize_part_origin_bottom_center(planter, width=6.0)
    flower = import_and_join_part(Path(spec["flower"]), "F06_Slot_1", 700, texture_px=512)
    normalize_part_origin_bottom_center(flower, height=0.58)

    xs = [-1.8, -0.6, 0.6, 1.8]
    ys = [-1.05, 0.0, 1.05]
    planter_surface = mesh_surface(planter)
    slots = []
    idx = 1
    for y in ys:
        for x in xs:
            soil, _, _, _ = planter_surface.ray_cast((x, y, p_high.z + 1.0), (0, 0, -1))
            if soil is None:
                raise ValueError(f"No soil surface under flower slot {idx}")
            if idx == 1:
                inst = flower
            else:
                inst = flower.copy()
                inst.data = flower.data
                inst.name = f"F06_Slot_{idx}"
                bpy.context.collection.objects.link(inst)
            inst.location = (x, y, soil.z - 0.025)
            inst.rotation_euler.z = math.radians((idx * 37) % 360)
            slots.append(inst)
            idx += 1
    export_hierarchy([planter, *slots], out_path)


def assemble_f07(spec: dict, out_path: Path) -> None:
    clear_scene()
    pole = import_and_join_part(Path(spec["pole"]), "F07_Pole", 5000)
    p_high = normalize_part_origin_bottom_center(pole, height=4.2)
    flag = create_pixel_flag_cloth("FlagClothPivot", width=1.05, height=1.05)
    flag.location = (0.08, 0.0, p_high.z * 0.87)
    export_hierarchy([pole, flag], out_path)


def assemble_f16(spec: dict, out_path: Path) -> None:
    clear_scene()
    gazebo = import_and_join_part(Path(spec["gazebo"]), "F16_Gazebo", 10000)
    g_high = normalize_part_origin_bottom_center(gazebo, height=3.5)
    g_low, _ = bbox_bounds(gazebo)
    scope = import_and_join_part(Path(spec["telescope"]), "F16_TelescopePivot", 4000)
    normalize_part_origin_bottom_center(scope, height=1.25)
    scope.location = (0.95, g_low.y * 0.45, g_high.z * 0.14)
    export_hierarchy([gazebo, scope], out_path)


def assemble_p04(spec: dict, out_path: Path) -> None:
    clear_scene()
    post = import_and_join_part(Path(spec["post"]), "P04_Post", 4000)
    p_high = normalize_part_origin_bottom_center(post, height=2.1)
    chime = import_and_join_part(Path(spec["chime"]), "P04_ChimePivot_1", 1500, texture_px=512)
    normalize_part_origin_top_center(chime, height=0.68)

    stem_points = [vertex.co for vertex in post.data.vertices if 0.3 <= vertex.co.z <= 1.0]
    stem = sum(stem_points, Vector()) / len(stem_points)
    arm_tip = max(
        (vertex.co for vertex in post.data.vertices if vertex.co.z >= p_high.z * 0.7),
        key=lambda point: (point.xy - stem.xy).length_squared,
    )
    arm_surface = mesh_surface(post)
    chimes = []
    for idx, fraction in enumerate((0.3, 0.55, 0.8), 1):
        xy = stem.lerp(arm_tip, fraction)
        socket, _, _, _ = arm_surface.ray_cast((xy.x, xy.y, p_high.z * 0.65), (0, 0, 1))
        if socket is None:
            raise ValueError(f"No windchime arm surface for strand {idx}")
        if idx == 1:
            inst = chime
        else:
            inst = chime.copy()
            inst.data = chime.data
            inst.name = f"P04_ChimePivot_{idx}"
            bpy.context.collection.objects.link(inst)
        inst.location = socket
        chimes.append(inst)
    export_hierarchy([post, *chimes], out_path)


def assemble_f42(spec: dict, out_path: Path) -> None:
    clear_scene()
    sign = import_and_join_part(Path(spec["signpost"]), "F42_Signpost", 5000)
    normalize_part_origin_bottom_center(sign, height=2.3)
    sign.location = (-0.55, 0.0, 0.0)
    bike = import_and_join_part(Path(spec["bicycle"]), "F42_Bicycle", 7000)
    normalize_part_origin_bottom_center(bike, height=1.15)
    bike.location = (0.55, 0.05, 0.0)
    export_hierarchy([sign, bike], out_path)


ASSEMBLERS = {
    "F15": assemble_f15,
    "F14": assemble_f14,
    "F17": assemble_f17,
    "F06": assemble_f06,
    "F07": assemble_f07,
    "F16": assemble_f16,
    "P04": assemble_p04,
    "F42": assemble_f42,
}


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-flag-only", action="store_true")
    parser.add_argument("--spec", type=Path)
    args = parser.parse_args(argv)

    if args.test_flag_only:
        clear_scene()
        flag = create_pixel_flag_cloth("FlagClothPivot", width=1.05, height=1.05)
        tmp_out = Path(os.environ.get("TEMP", "/tmp")) / "test-flag-uv.glb"
        export_hierarchy([flag], tmp_out)
        return

    if not args.spec:
        parser.error("Provide --spec <json> or --test-flag-only")

    spec_data = json.loads(args.spec.read_text(encoding="utf-8"))
    for item in spec_data["items"]:
        kind = item["asset"]
        fn = ASSEMBLERS[kind]
        print(f"=== Assembling {kind} -> {item['output']} ===")
        fn(item["parts"], Path(item["output"]))


if __name__ == "__main__":
    main()
