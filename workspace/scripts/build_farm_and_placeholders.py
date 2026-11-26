r"""Build 8-plot Wind-Waker Farm Garden GLB (with named plot/stage nodes) and NPC Placeholder GLB.

Plot hierarchy in model-farm-garden.glb (protected by meta.json nodeMergeBlacklist):
  Plot_1 .. Plot_8
    SoilDry
    SoilWet
    Stage1_Sprout
    Stage2_Growing
    Stage3_Radish
    Stage3_Berry
    Stage3_Sunflower

Usage:
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b --factory-startup -P workspace/scripts/build_farm_and_placeholders.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
MODELS_DIR = ROOT / "workspace" / "assets" / "models"
DEBUG_DIR = ROOT / "workspace" / "debug"
FARM_GLB = MODELS_DIR / "model-farm-garden.glb"
NPC_PH_GLB = MODELS_DIR / "model-npc-placeholder.glb"
FARM_PREVIEW = DEBUG_DIR / "farm-garden-preview.png"


def srgb_col(hex_str: str):
    s = hex_str.lstrip("#")
    vals = [int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in vals) + (1.0,)


def make_mat(name: str, hex_str: str, roughness: float = 0.85, emission: float = 0.05):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    col = srgb_col(hex_str)
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.14
    if emission > 0:
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = emission
    return m


def add_box(name: str, parent, loc, dims, mat, bevel: float = 0.03):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = min(bevel, min(dims) * 0.22)
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for f in obj.data.polygons:
        f.use_smooth = True
    obj.data.materials.append(mat)
    if parent is not None:
        obj.parent = parent
    return obj


def add_sphere(name: str, parent, loc, scale, mat, segs: int = 12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=8, radius=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for f in obj.data.polygons:
        f.use_smooth = True
    obj.data.materials.append(mat)
    if parent is not None:
        obj.parent = parent
    return obj


def add_cyl(name: str, parent, loc, rad: float, depth: float, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=rad, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    for f in obj.data.polygons:
        f.use_smooth = True
    obj.data.materials.append(mat)
    if parent is not None:
        obj.parent = parent
    return obj


def join_parts_as(name: str, parts: list[bpy.types.Object], parent) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    res = bpy.context.view_layer.objects.active
    res.name = name
    if parent is not None:
        res.parent = parent
    return res


def build_farm_garden():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    mat_wood = make_mat("WW_Farm_Wood", "#D89E63", 0.84)
    mat_wood_dark = make_mat("WW_Farm_Wood_Dark", "#A87042", 0.86)
    mat_soil_dry = make_mat("WW_Soil_Dry", "#C69D71", 0.92)
    mat_soil_wet = make_mat("WW_Soil_Wet", "#795234", 0.72)
    mat_leaf = make_mat("WW_Sprout_Green", "#65CA55", 0.82)
    mat_leaf_bright = make_mat("WW_Leaf_Bright", "#8BE66B", 0.80)
    mat_radish = make_mat("WW_Radish_Coral", "#F26D63", 0.78)
    mat_radish_tip = make_mat("WW_Radish_Cream", "#FFF3DC", 0.82)
    mat_berry = make_mat("WW_Berry_Pink", "#FF5C8D", 0.74)
    mat_sunflower = make_mat("WW_Sunflower_Gold", "#FFD147", 0.76, emission=0.10)
    mat_sun_center = make_mat("WW_Sunflower_Brown", "#6D4428", 0.88)
    mat_sign = make_mat("WW_Sign_Cream", "#F7E9CA", 0.86)
    mat_bucket = make_mat("WW_Bucket_Mint", "#6AC8DF", 0.55)

    # Outer fence & base props (can be merged together by AWC optimizer)
    decor_root = bpy.data.objects.new("FarmDecor", None)
    bpy.context.collection.objects.link(decor_root)

    # Low open-front picket perimeter (4.6m half-width X, 2.7m half-depth Y in Blender)
    # Leave wide 3.2m front opening on South (-Z_u -> +Y_b) and North (+Z_u -> -Y_b)
    # In Blender: X_b = -X_u, Y_b = -Z_u, Z_b = Y_u
    fence_segments = [
        ((-4.5, 0.0), (-4.5, 2.55)),
        ((4.5, 0.0), (4.5, 2.55)),
        ((-4.5, 0.0), (-4.5, -2.55)),
        ((4.5, 0.0), (4.5, -2.55)),
        ((-4.5, -2.55), (-1.9, -2.55)),
        ((1.9, -2.55), (4.5, -2.55)),
        ((-4.5, 2.55), (-1.9, 2.55)),
        ((1.9, 2.55), (4.5, 2.55)),
    ]
    post_positions = [
        (-4.5, -2.55), (-3.2, -2.55), (-1.9, -2.55),
        (1.9, -2.55), (3.2, -2.55), (4.5, -2.55),
        (-4.5, 2.55), (-3.2, 2.55), (-1.9, 2.55),
        (1.9, 2.55), (3.2, 2.55), (4.5, 2.55),
        (-4.5, -0.9), (-4.5, 0.9), (4.5, -0.9), (4.5, 0.9),
    ]
    for idx, (px, py) in enumerate(post_positions):
        add_box(f"FencePost_{idx}", decor_root, (px, py, 0.34), (0.16, 0.16, 0.68), mat_wood_dark, 0.03)
    for idx, ((ax, ay), (bx, by)) in enumerate(fence_segments):
        mx, my = 0.5 * (ax + bx), 0.5 * (ay + by)
        dx, dy = abs(bx - ax) + 0.14, abs(by - ay) + 0.14
        add_box(f"FenceRailTop_{idx}", decor_root, (mx, my, 0.52), (dx, dy, 0.10), mat_wood, 0.02)
        add_box(f"FenceRailBot_{idx}", decor_root, (mx, my, 0.24), (dx, dy, 0.10), mat_wood, 0.02)

    # Cozy Farm Signpost & Watering Can on front-left corner
    add_box("SignPost", decor_root, (-3.6, 2.25, 0.45), (0.12, 0.12, 0.90), mat_wood_dark, 0.02)
    add_box("SignBoard", decor_root, (-3.6, 2.25, 0.82), (0.90, 0.09, 0.46), mat_sign, 0.025)
    add_cyl("WaterBucket", decor_root, (3.75, 2.15, 0.22), 0.22, 0.44, mat_bucket)

    # 8 Individual Plots (2 rows x 4 cols)
    # Row 1 (South, closer to spawn): Y_b = +1.15 (Z_u = -1.15)
    # Row 2 (North): Y_b = -1.15 (Z_u = +1.15)
    # Cols (West to East): X_u = -3.0, -1.0, +1.0, +3.0 -> X_b = +3.0, +1.0, -1.0, -3.0
    plot_idx = 0
    for row_zu in (-1.15, 1.15):
        for col_xu in (-3.0, -1.0, 1.0, 3.0):
            plot_idx += 1
            px = -col_xu
            py = -row_zu

            plot_empty = bpy.data.objects.new(f"Plot_{plot_idx}", None)
            plot_empty.location = (px, py, 0.0)
            bpy.context.collection.objects.link(plot_empty)

            # Wooden border frame (under SoilDry)
            add_box(f"BedFrame_{plot_idx}", decor_root, (px, py, 0.07), (1.68, 1.68, 0.14), mat_wood_dark, 0.03)

            # SoilDry & SoilWet (kept cleanly separable with globally unique node names)
            add_box(f"P{plot_idx}_SoilDry", plot_empty, (0.0, 0.0, 0.11), (1.46, 1.46, 0.10), mat_soil_dry, 0.03)
            add_box(f"P{plot_idx}_SoilWet", plot_empty, (0.0, 0.0, 0.12), (1.44, 1.44, 0.10), mat_soil_wet, 0.03)

            # Stage1_Sprout (4 tiny cute sprouts)
            s1_parts = []
            for ox, oy in ((-0.35, -0.35), (0.35, -0.35), (-0.35, 0.35), (0.35, 0.35)):
                s1_parts.append(add_cyl("s1_stem", None, (ox, oy, 0.23), 0.03, 0.14, mat_leaf))
                s1_parts.append(add_sphere("s1_l1", None, (ox + 0.06, oy, 0.30), (0.09, 0.05, 0.03), mat_leaf_bright))
                s1_parts.append(add_sphere("s1_l2", None, (ox - 0.06, oy, 0.30), (0.09, 0.05, 0.03), mat_leaf_bright))
            join_parts_as(f"P{plot_idx}_Stage1_Sprout", s1_parts, plot_empty)

            # Stage2_Growing (4 lush leafy tufts)
            s2_parts = []
            for ox, oy in ((-0.36, -0.36), (0.36, -0.36), (-0.36, 0.36), (0.36, 0.36)):
                s2_parts.append(add_sphere("s2_a", None, (ox, oy, 0.31), (0.20, 0.20, 0.16), mat_leaf))
                s2_parts.append(add_sphere("s2_b", None, (ox + 0.06, oy - 0.05, 0.42), (0.14, 0.14, 0.12), mat_leaf_bright))
            join_parts_as(f"P{plot_idx}_Stage2_Growing", s2_parts, plot_empty)

            # Stage3_Radish (plump coral-red & cream radishes peeking out with tall leaves)
            s3r_parts = []
            for ox, oy in ((-0.36, -0.36), (0.36, -0.36), (-0.36, 0.36), (0.36, 0.36)):
                s3r_parts.append(add_sphere("rad_body", None, (ox, oy, 0.29), (0.17, 0.17, 0.19), mat_radish))
                s3r_parts.append(add_sphere("rad_tip", None, (ox, oy, 0.21), (0.12, 0.12, 0.10), mat_radish_tip))
                for ang in (0, 2.1, 4.2):
                    lx = ox + math.cos(ang) * 0.10
                    ly = oy + math.sin(ang) * 0.10
                    s3r_parts.append(add_sphere("rad_lf", None, (lx, ly, 0.52), (0.10, 0.15, 0.16), mat_leaf_bright))
            join_parts_as(f"P{plot_idx}_Stage3_Radish", s3r_parts, plot_empty)

            # Stage3_Berry (lush bushes studded with plump pink strawberries)
            s3b_parts = []
            for ox, oy in ((-0.36, -0.36), (0.36, -0.36), (-0.36, 0.36), (0.36, 0.36)):
                s3b_parts.append(add_sphere("br_bush", None, (ox, oy, 0.36), (0.25, 0.25, 0.21), mat_leaf))
                for bx, by, bz in ((0.18, 0.10, 0.40), (-0.16, 0.12, 0.38), (0.04, -0.18, 0.43)):
                    s3b_parts.append(add_sphere("br_fruit", None, (ox + bx, oy + by, bz), (0.08, 0.08, 0.10), mat_berry))
            join_parts_as(f"P{plot_idx}_Stage3_Berry", s3b_parts, plot_empty)

            # Stage3_Sunflower (tall cheerful golden sunflowers facing South +Y_b)
            s3s_parts = []
            for ox, oy in ((-0.35, -0.35), (0.35, -0.35), (-0.35, 0.35), (0.35, 0.35)):
                s3s_parts.append(add_cyl("sf_stem", None, (ox, oy, 0.46), 0.045, 0.62, mat_leaf))
                s3s_parts.append(add_sphere("sf_petals", None, (ox, oy + 0.02, 0.80), (0.22, 0.08, 0.22), mat_sunflower))
                s3s_parts.append(add_sphere("sf_core", None, (ox, oy + 0.08, 0.80), (0.11, 0.06, 0.11), mat_sun_center))
            join_parts_as(f"P{plot_idx}_Stage3_Sunflower", s3s_parts, plot_empty)

    bpy.ops.export_scene.gltf(
        filepath=str(FARM_GLB),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_materials="EXPORT",
    )
    print(f"[EXPORT] Farm GLB: {FARM_GLB} ({FARM_GLB.stat().st_size / 1024:.1f} KB)")

    # Quick render preview
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 600
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 15))
    bpy.context.object.data.energy = 2.6
    bpy.context.object.rotation_euler = (math.radians(45), 0, math.radians(-30))
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    cam.location = Vector((0, 9.5, 6.2))
    cam.rotation_euler = (Vector((0, 0, 0.3)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(FARM_PREVIEW)
    bpy.ops.render.render(write_still=True)


def build_npc_placeholder():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mat_wood = make_mat("WW_PH_Wood", "#D8A26A", 0.84)
    mat_cream = make_mat("WW_PH_Cream", "#FFF4DF", 0.78, emission=0.14)
    mat_mint = make_mat("WW_PH_Mint", "#6FD8C4", 0.70, emission=0.20)

    # Cozy rounded wooden stump pedestal + floating friendly pill/head silhouette (height ~1.55m)
    add_cyl("Pedestal_Base", None, (0, 0, 0.12), 0.52, 0.24, mat_wood)
    add_cyl("Body_Pillar", None, (0, 0, 0.65), 0.28, 0.82, mat_cream)
    add_sphere("Head_Dome", None, (0, 0, 1.25), (0.34, 0.34, 0.32), mat_cream)
    add_sphere("Talk_Orb_Marker", None, (0, 0, 1.72), (0.14, 0.14, 0.14), mat_mint)

    bpy.ops.export_scene.gltf(
        filepath=str(NPC_PH_GLB),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_materials="EXPORT",
    )
    print(f"[EXPORT] NPC Placeholder GLB: {NPC_PH_GLB} ({NPC_PH_GLB.stat().st_size / 1024:.1f} KB)")


def main():
    build_farm_garden()
    build_npc_placeholder()


if __name__ == "__main__":
    main()
