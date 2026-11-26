r"""Decimate and normalize selected 55MB+ Tripo FBX models into lightweight Wind-Waker-ready GLBs (<1.5 MB).

Usage:
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b --factory-startup -P workspace/scripts/decimate_tripo_assets.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
TRIPO_ROOT = ROOT / "图片" / "模型"
OUT_DIR = ROOT / "workspace" / "assets" / "models" / "tripo-optimized"
PREVIEW_PNG = ROOT / "workspace" / "debug" / "tripo-optimized-preview.png"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ASSETS = [
    # (folder_name, fbx_name, out_id, target_height_m, target_faces, max_tex_px)
    ("F22-西岬旧灯塔", "F22-西岬旧灯塔.fbx", "F22-west-cape-lighthouse", 11.0, 5500, 1024),
    ("F09-中心心愿喷泉", "F09-中心心愿喷泉.fbx", "F09-wish-fountain", 2.2, 5200, 1024),
    ("E01-海风歪颈三团圆蓬松树", "E01-海风歪颈三团圆蓬松树.fbx", "E01-coastal-pine-tree", 4.6, 3200, 768),
    ("E02-北麓柔金奶油枫树", "E02-北麓柔金奶油枫树.fbx", "E02-autumn-maple-tree", 5.0, 3200, 768),
    ("P01-暖陶木质矮路灯", "P01-暖陶木质矮路灯.fbx", "P01-clay-street-lamp", 1.9, 2200, 512),
    ("P02-歪斜复古薄荷绿海风邮筒", "P02-歪斜复古薄荷绿海风邮筒.fbx", "P02-vintage-mailbox", 1.35, 2200, 512),
    ("P03-手绘微倾木质指路牌", "P03-手绘微倾木质指路牌.fbx", "P03-wooden-signpost", 1.75, 2200, 512),
    ("P05-海风烤包木推车", "P05-海风烤包木推车.fbx", "P05-bakery-food-cart", 1.9, 3400, 768),
]


def world_mesh_bounds(objs):
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for obj in objs:
        if obj.type != "MESH":
            continue
        mw = obj.matrix_world
        for corner in obj.bound_box:
            wc = mw @ Vector(corner)
            mins.x = min(mins.x, wc.x)
            mins.y = min(mins.y, wc.y)
            mins.z = min(mins.z, wc.z)
            maxs.x = max(maxs.x, wc.x)
            maxs.y = max(maxs.y, wc.y)
            maxs.z = max(maxs.z, wc.z)
    return mins, maxs


def process_one(folder: str, fbx_name: str, out_id: str, target_h: float, target_faces: int, max_tex: int) -> Path:
    fbx_path = TRIPO_ROOT / folder / fbx_name
    assert fbx_path.exists(), f"Missing FBX: {fbx_path}"

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    assert meshes, f"No mesh in {fbx_path}"

    # Remove empty/non-mesh helper nodes after baking world transform
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = out_id

    for o in list(bpy.context.scene.objects):
        if o != obj:
            bpy.data.objects.remove(o, do_unlink=True)

    # Decimate high-poly Tripo geometry cleanly before final exact bottom-center normalization
    poly_cnt = len(obj.data.polygons)
    if poly_cnt > target_faces:
        mod = obj.modifiers.new("Decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = max(0.01, min(1.0, target_faces / float(poly_cnt)))
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)

    # Normalize scale to target height and bake bottom-center directly at vertex origin (0, 0, 0)
    from mathutils import Matrix
    verts = [v.co for v in obj.data.vertices]
    mins = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
    maxs = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
    cur_h = max(maxs.z - mins.z, 1e-4)
    scale_f = target_h / cur_h
    origin = Vector((0.5 * (mins.x + maxs.x), 0.5 * (mins.y + maxs.y), mins.z))
    obj.data.transform(Matrix.Scale(scale_f, 4) @ Matrix.Translation(-origin))
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    min_z_after = min(v.co.z for v in obj.data.vertices)
    assert abs(min_z_after) < 1e-4, f"{out_id} min_z_after={min_z_after}"

    for f in obj.data.polygons:
        f.use_smooth = True

    # Soften materials for Wind Waker cohesion & downscale oversized textures
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = 0.85
            if "Specular IOR Level" in bsdf.inputs:
                bsdf.inputs["Specular IOR Level"].default_value = 0.14
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = 0.0

    has_transparency = False
    for img in bpy.data.images:
        if img.size[0] > 0 and img.size[1] > 0:
            w, h = img.size[0], img.size[1]
            if max(w, h) > max_tex:
                scale_tex = max_tex / float(max(w, h))
                nw = max(64, int(round(w * scale_tex)))
                nh = max(64, int(round(h * scale_tex)))
                img.scale(nw, nh)
            if img.channels >= 4 and len(img.pixels) > 0:
                arr = np.empty(len(img.pixels), dtype=np.float32)
                img.pixels.foreach_get(arr)
                if float(arr[3::4].min()) < 0.99:
                    has_transparency = True
            img.pack()

    img_fmt = "AUTO" if has_transparency else "JPEG"
    out_glb = OUT_DIR / f"{out_id}.glb"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=str(out_glb),
        export_format="GLB",
        export_yup=True,
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
        export_image_format=img_fmt,
        export_jpeg_quality=86,
    )
    final_faces = len(obj.data.polygons)
    size_kb = out_glb.stat().st_size / 1024.0
    print(f"[TRIPO OK] {out_id:26s} | {poly_cnt:6d} -> {final_faces:5d} tris | {size_kb:7.1f} KB")
    return out_glb


def render_contact_preview(glbs: list[Path]):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 640

    world = bpy.data.worlds.new("Studio")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.94, 0.96, 0.98, 1.0)
    bg.inputs[1].default_value = 1.1

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 20))
    sun = bpy.context.object
    sun.data.energy = 2.4
    sun.rotation_euler = (math.radians(45), math.radians(12), math.radians(-30))

    spacing = 7.5
    for idx, glb in enumerate(glbs):
        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(glb))
        new_objs = [o for o in bpy.context.scene.objects if o not in before]
        col_x = (idx - (len(glbs) - 1) * 0.5) * spacing
        for o in new_objs:
            if o.parent is None:
                o.location.x += col_x

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 38.0
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    eye = Vector((0.0, -34.0, 11.5))
    tgt = Vector((0.0, 0.0, 2.2))
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()

    scene.render.filepath = str(PREVIEW_PNG)
    bpy.ops.render.render(write_still=True)
    print(f"[PREVIEW] Saved {PREVIEW_PNG}")


def main():
    glbs = []
    for item in ASSETS:
        glbs.append(process_one(*item))
    render_contact_preview(glbs)


if __name__ == "__main__":
    main()
