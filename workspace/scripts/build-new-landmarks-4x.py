"""Build all 4x Shiguang Town new landmarks (F19-F42 + P01-P06 + E01/E02) as Y-up GLBs
and assemble the entire 4x town (terrain + hardscape + F01-F18 + F19-F42) for final render.

Exports:
  - workspace/assets/models/landmarks-4x/<id>.glb
  - workspace/debug/town-4x-full-assembly.png

Usage:
  blender -b --factory-startup --python-exit-code 1 -P workspace/scripts/build-new-landmarks-4x.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
LANDMARKS_DIR = ROOT / "workspace" / "assets" / "models" / "landmarks-4x"
TERRAIN_GLB = ROOT / "workspace" / "assets" / "models" / "map-shiguang-town-4x.glb"
HARDSCAPE_GLB = ROOT / "workspace" / "assets" / "models" / "town-hardscape-4x.glb"
LAYOUT_JSON = ROOT / "workspace" / "scripts" / "town-building-layout.json"
ASSEMBLY_RENDER_OUT = ROOT / "workspace" / "debug" / "town-4x-full-assembly.png"


# === PAD Palette & Material System ===

PALETTE = {
    "cream_wall": ("#FFF5E4", 0.72, 0.0),
    "ivory_trim": ("#F7ECD5", 0.70, 0.0),
    "mustard_wall": ("#F2D88F", 0.76, 0.0),
    "honey_wood": ("#E4BA8B", 0.78, 0.0),
    "warm_cedar": ("#C68A53", 0.80, 0.0),
    "toasted_wood": ("#9D623E", 0.82, 0.0),
    "dark_bark": ("#7A4E34", 0.86, 0.0),
    "driftwood": ("#D8C3A5", 0.86, 0.0),
    "terracotta": ("#B96A59", 0.72, 0.0),
    "coral_red": ("#D97867", 0.70, 0.0),
    "mint_wood": ("#85C7B3", 0.72, 0.0),
    "sea_blue": ("#7CC6E8", 0.74, 0.0),
    "slate_blue": ("#638A9E", 0.76, 0.0),
    "sage_roof": ("#65765F", 0.78, 0.0),
    "sage_leaf": ("#93C794", 0.84, 0.0),
    "cream_green": ("#B7DDA8", 0.85, 0.0),
    "coastal_pine": ("#7BB59D", 0.84, 0.0),
    "golden_maple": ("#E8C37D", 0.83, 0.0),
    "peach_blossom": ("#F2A8AE", 0.75, 0.0),
    "limestone": ("#C8BFB0", 0.88, 0.0),
    "basalt": ("#686A75", 0.88, 0.0),
    "warm_slate": ("#5A587D", 0.80, 0.0),
    "brass": ("#D8AE5E", 0.35, 0.0),
    "amber_glow": ("#FFD67A", 0.35, 0.85),
    "hearth_fire": ("#FF9E4F", 0.35, 1.15),
    "mint_glass": ("#B5E6DC", 0.22, 0.08),
    "pink_accent": ("#F48FB1", 0.72, 0.0),
    "lemon_accent": ("#F5D76E", 0.74, 0.0),
    "kraft_paper": ("#D4B082", 0.88, 0.0),
    "cream_rope": ("#EFE0C4", 0.90, 0.0),
}


def srgb_to_linear(hex_str: str) -> tuple[float, float, float, float]:
    h = hex_str.lstrip("#")
    vals = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in vals]
    return (*lin, 1.0)


def get_mat(key: str):
    mat = bpy.data.materials.get(key)
    if mat:
        return mat
    hex_col, rough, emit = PALETTE[key]
    col = srgb_to_linear(hex_col)
    mat = bpy.data.materials.new(key)
    alpha = 0.32 if key == "mint_glass" else 1.0
    mat.diffuse_color = (col[0], col[1], col[2], alpha)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = 0.08 if key == "mint_glass" else rough
    bsdf.inputs["Alpha"].default_value = alpha
    if key == "mint_glass" and hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    if key == "brass":
        bsdf.inputs["Metallic"].default_value = 0.75
    if emit > 0:
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = emit
    return mat


def apply_soft_bevel(obj, width: float = 0.028, dims: tuple[float, float, float] | None = None):
    if width <= 0:
        return obj
    if dims is not None:
        width = min(width, min(dims) * 0.26)
    if width < 0.004:
        return obj
    mod = obj.modifiers.new("Bevel24cm", "BEVEL")
    mod.width = width
    mod.segments = 1
    mod.use_clamp_overlap = True
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def box(name: str, pos: tuple[float, float, float], size: tuple[float, float, float],
        mat_key: str, bevel: float = 0.025, rot: tuple[float, float, float] = (0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(get_mat(mat_key))
    apply_soft_bevel(obj, bevel, size)
    if any(rot):
        obj.rotation_euler = rot
    return obj


def cyl(name: str, pos: tuple[float, float, float], radius: float, height: float,
        mat_key: str, sides: int = 12, bevel: float = 0.02, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=height, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(get_mat(mat_key))
    apply_soft_bevel(obj, bevel, (radius * 2, radius * 2, height))
    if any(rot):
        obj.rotation_euler = rot
    for f in obj.data.polygons:
        f.use_smooth = True
    return obj


def cone(name: str, pos: tuple[float, float, float], r1: float, r2: float, height: float,
         mat_key: str, sides: int = 12, bevel: float = 0.018):
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=r1, radius2=r2, depth=height, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(get_mat(mat_key))
    apply_soft_bevel(obj, bevel, (max(r1, r2) * 2, max(r1, r2) * 2, height))
    for f in obj.data.polygons:
        f.use_smooth = True
    return obj


def sphere(name: str, pos: tuple[float, float, float], radii: tuple[float, float, float],
           mat_key: str, subdiv: int = 2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(get_mat(mat_key))
    for f in obj.data.polygons:
        f.use_smooth = True
    return obj


def beam(name: str, p0: tuple[float, float, float], p1: tuple[float, float, float],
         w: float, d: float, mat_key: str, bevel: float = 0.02):
    a, b = Vector(p0), Vector(p1)
    delta = b - a
    if delta.length < 1e-4:
        return None
    obj = box(name, tuple((a + b) * 0.5), (w, d, delta.length), mat_key, bevel=bevel)
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    return obj


def mesh_poly(name: str, verts, faces, mat_keys: list[str], mat_indices: list[int] | None = None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for k in mat_keys:
        mesh.materials.append(get_mat(k))
    if mat_indices:
        for poly, idx in zip(mesh.polygons, mat_indices):
            poly.material_index = idx
    return obj


def gable_roof(name: str, center_xy: tuple[float, float], w: float, d: float,
               eave_z: float, rise: float, roof_mat: str, trim_mat: str = "ivory_trim"):
    cx, cy = center_xy
    hw, hd = w * 0.5, d * 0.5
    verts = [
        (cx - hw, cy - hd, eave_z), (cx + hw, cy - hd, eave_z),
        (cx + hw, cy + hd, eave_z), (cx - hw, cy + hd, eave_z),
        (cx, cy - hd, eave_z + rise), (cx, cy + hd, eave_z + rise),
    ]
    # Note: ridge along Y so gables face -Y and +Y
    faces = [(3, 2, 1, 0), (0, 4, 5, 3), (1, 2, 5, 4), (0, 1, 4), (3, 5, 2)]
    m_idx = [1, 0, 0, 1, 1]
    mesh_poly(name, verts, faces, [roof_mat, trim_mat], m_idx)
    for s, e in ((0, 3), (1, 2), (0, 4), (4, 1), (3, 5), (5, 2), (4, 5)):
        beam(f"{name}_trim", verts[s], verts[e], 0.11, 0.11, trim_mat, bevel=0.015)


def hip_roof(name: str, center_xy: tuple[float, float], w: float, d: float,
             eave_z: float, rise: float, ridge_inset: float, roof_mat: str, trim_mat: str = "ivory_trim"):
    cx, cy = center_xy
    hw, hd = w * 0.5, d * 0.5
    rw = max(0.3, hw - ridge_inset)
    verts = [
        (cx - hw, cy - hd, eave_z), (cx + hw, cy - hd, eave_z),
        (cx + hw, cy + hd, eave_z), (cx - hw, cy + hd, eave_z),
        (cx - rw, cy, eave_z + rise), (cx + rw, cy, eave_z + rise),
    ]
    faces = [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)]
    m_idx = [1, 0, 0, 0, 0]
    mesh_poly(name, verts, faces, [roof_mat, trim_mat], m_idx)
    for s, e in ((0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 5), (2, 5), (3, 4), (4, 5)):
        beam(f"{name}_hip", verts[s], verts[e], 0.10, 0.10, trim_mat, bevel=0.015)


def lantern_unit(pos: tuple[float, float, float], scale: float = 1.0):
    x, y, z = pos
    box("Lantern_Cap", (x, y, z + 0.32 * scale), (0.30 * scale, 0.30 * scale, 0.08 * scale), "toasted_wood")
    box("Lantern_Core", (x, y, z + 0.16 * scale), (0.20 * scale, 0.20 * scale, 0.26 * scale), "amber_glow")
    box("Lantern_Base", (x, y, z + 0.02 * scale), (0.26 * scale, 0.26 * scale, 0.06 * scale), "toasted_wood")


def window_unit(pos: tuple[float, float, float], w: float = 0.85, h: float = 0.82, facing: str = "-y"):
    x, y, z = pos
    if facing in ("-y", "+y"):
        dy = -0.04 if facing == "-y" else 0.04
        box("Win_Frame", (x, y, z), (w, 0.12, h), "ivory_trim")
        box("Win_Glass", (x, y + dy, z), (w - 0.16, 0.04, h - 0.16), "amber_glow", bevel=0.008)
        box("Win_Sill", (x, y + dy * 1.4, z - h * 0.52), (w + 0.12, 0.18, 0.10), "warm_cedar")
    else:
        dx = -0.04 if facing == "-x" else 0.04
        box("Win_Frame", (x, y, z), (0.12, w, h), "ivory_trim")
        box("Win_Glass", (x + dx, y, z), (0.04, w - 0.16, h - 0.16), "amber_glow", bevel=0.008)
        box("Win_Sill", (x + dx * 1.4, y, z - h * 0.52), (0.18, w + 0.12, 0.10), "warm_cedar")


def wind_chime(pos: tuple[float, float, float], mat_key: str = "mint_glass"):
    x, y, z = pos
    cyl("Chime_Cord", (x, y, z - 0.12), 0.012, 0.24, "cream_rope", sides=6, bevel=0.002)
    cyl("Chime_Bell", (x, y, z - 0.28), 0.055, 0.14, mat_key, sides=8, bevel=0.01)


def export_clean_glb(filepath: Path):
    """Join meshes by material for tidy low-drawcall GLBs and export Y-up."""
    material_groups: dict[str, list[bpy.types.Object]] = {}
    for obj in list(bpy.context.scene.objects):
        if obj.type == "MESH" and obj.data.materials:
            key = obj.data.materials[0].name
            if len(obj.data.materials) == 1:
                material_groups.setdefault(key, []).append(obj)

    for key, members in material_groups.items():
        if len(members) <= 1:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        for m in members:
            m.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        bpy.ops.object.join()
        bpy.context.object.name = key

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(filepath),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )


# === Individual Landmark Builders (Local Front = -Y_b, Ground = Z_b = 0) ===

def build_F19_post_office():
    # 9.0 x 7.0 x 5.5m: Wind-Chime Coastal Post Office
    box("Plinth", (0, 0.4, 0.16), (8.6, 5.8, 0.32), "limestone")
    box("Main_Walls", (0, 0.5, 1.75), (8.0, 5.0, 2.9), "cream_wall", bevel=0.04)
    for sx in (-3.95, 3.95):
        for sy in (-1.95, 2.95):
            box("Corner_Post", (sx, sy, 1.75), (0.30, 0.30, 3.0), "honey_wood")
    hip_roof("Post_Roof", (0, 0.5), 8.9, 6.2, 3.18, 1.85, 1.8, "terracotta", "ivory_trim")
    # Cute dormer & envelope weathervane
    box("Dormer", (0, -0.7, 3.85), (1.7, 1.4, 1.1), "cream_wall")
    gable_roof("Dormer_Roof", (0, -0.7), 2.0, 1.6, 4.4, 0.65, "terracotta", "ivory_trim")
    cyl("Vane_Mast", (0, 0.5, 5.25), 0.04, 0.55, "brass", sides=8)
    box("Vane_Envelope", (0.18, 0.5, 5.45), (0.45, 0.06, 0.30), "mint_wood", bevel=0.01)
    # Front timber veranda (-Y)
    box("Veranda_Deck", (0, -2.55, 0.16), (8.4, 1.5, 0.32), "warm_cedar")
    box("Veranda_Step", (0, -3.45, 0.08), (2.8, 0.45, 0.16), "limestone")
    box("Porch_Canopy", (0, -2.55, 2.95), (8.6, 1.7, 0.22), "terracotta")
    for x in (-3.9, -1.5, 1.5, 3.9):
        cyl("Veranda_Post", (x, -3.15, 1.6), 0.11, 2.75, "honey_wood")
    # Mint arched double doors + counter window
    box("Door_Frame", (-0.6, -2.02, 1.35), (1.9, 0.18, 2.2), "ivory_trim")
    box("Mint_Door_L", (-1.02, -2.10, 1.30), (0.82, 0.08, 2.0), "mint_wood")
    box("Mint_Door_R", (-0.18, -2.10, 1.30), (0.82, 0.08, 2.0), "mint_wood")
    window_unit((2.2, -2.00, 1.55), 1.4, 1.0, "-y")
    window_unit((-2.6, -2.00, 1.55), 1.0, 0.9, "-y")
    box("Postcard_Counter", (2.2, -2.35, 0.95), (1.8, 0.48, 0.12), "honey_wood")
    # Wind chimes along veranda eaves & mint postbox
    for idx, x in enumerate((-3.2, -2.4, -1.8, 1.8, 2.6, 3.3)):
        wind_chime((x, -3.22, 2.84), ("mint_glass", "sea_blue", "peach_blossom")[idx % 3])
    cyl("Postbox_Post", (3.6, -3.35, 0.55), 0.09, 0.85, "toasted_wood")
    box("Postbox_Body", (3.6, -3.35, 1.12), (0.46, 0.40, 0.52), "mint_wood", bevel=0.04)
    lantern_unit((-1.7, -3.15, 2.35), 0.9)


def build_F20_mailbox_gallery():
    # 6.0 x 4.0 x 3.2m: Stepped Mailbox Gallery & Parcel Shelter
    box("Deck", (0, 0, 0.12), (5.8, 3.8, 0.24), "warm_cedar")
    for x in (-2.6, 0.0, 2.6):
        box("Back_Post", (x, 1.6, 1.55), (0.20, 0.20, 2.8), "toasted_wood")
    for x in (-2.6, 2.6):
        box("Front_Post", (x, -1.6, 1.35), (0.20, 0.20, 2.4), "toasted_wood")
    box("Slanted_Roof", (0, 0.0, 2.82), (6.1, 4.1, 0.22), "terracotta", rot=(math.radians(10), 0, 0))
    # Stepped cubby wall with 6 pastel mailboxes
    box("Cubby_Rack", (-1.1, 0.7, 1.15), (3.1, 0.75, 2.0), "honey_wood")
    box_colors = ["coral_red", "mint_wood", "lemon_accent", "sea_blue", "peach_blossom", "ivory_trim"]
    for i in range(6):
        col = i % 3
        row = i // 3
        box(f"Mailbox_{i}", (-2.05 + col * 0.95, 0.30, 0.85 + row * 0.72), (0.58, 0.48, 0.45), box_colors[i], bevel=0.04)
    # Parcel bench & kraft boxes + pixel stamp board
    box("Parcel_Bench", (1.65, 0.3, 0.45), (1.8, 0.95, 0.65), "warm_cedar")
    box("Parcel_1", (1.35, 0.3, 0.96), (0.48, 0.42, 0.36), "kraft_paper")
    box("Parcel_2", (1.95, 0.35, 0.92), (0.42, 0.38, 0.30), "kraft_paper")
    box("Stamp_Board", (1.65, 1.45, 1.65), (1.8, 0.12, 1.25), "ivory_trim")
    for si, sk in enumerate(("coral_red", "sea_blue", "sage_leaf", "amber_glow")):
        box(f"Stamp_{si}", (1.1 + (si % 2) * 0.8, 1.36, 1.35 + (si // 2) * 0.5), (0.45, 0.05, 0.38), sk, bevel=0.01)


def build_F21_windchime_corridor():
    # 6.4 x 3.8 x 3.8m: Cape Wind-Chime Pergola Corridor
    box("Boardwalk", (0, 0, 0.12), (6.4, 3.8, 0.24), "warm_cedar")
    for px in (-2.8, -0.95, 0.95, 2.8):
        for py in (-1.55, 1.55):
            cyl("Pergola_Post", (px, py, 1.55), 0.13, 2.8, "honey_wood")
        beam("Arch_Tie", (px, -1.65, 2.95), (px, 1.65, 2.95), 0.18, 0.18, "honey_wood")
        beam("Arch_Peak_L", (px, -1.55, 2.95), (px, 0, 3.45), 0.15, 0.15, "warm_cedar")
        beam("Arch_Peak_R", (px, 1.55, 2.95), (px, 0, 3.45), 0.15, 0.15, "warm_cedar")
    for py in (-1.3, 0.0, 1.3):
        beam("Purlin", (-3.1, py, 3.05 if py != 0 else 3.45), (3.1, py, 3.05 if py != 0 else 3.45), 0.12, 0.12, "toasted_wood")
    # Wind chimes & festive bunting flags
    for idx in range(7):
        x = -2.4 + idx * 0.8
        wind_chime((x, 0.0, 3.35), ("mint_glass", "sea_blue", "peach_blossom")[idx % 3])
        cone(f"Flag_{idx}", (x, -1.55, 2.65), 0.18, 0.02, 0.34, ("coral_red", "lemon_accent", "sea_blue")[idx % 3], sides=4)
    cyl("Signal_Post", (3.0, -1.65, 1.9), 0.08, 3.6, "toasted_wood")
    box("Signal_Flag", (3.42, -1.65, 3.35), (0.75, 0.05, 0.45), "sea_blue", bevel=0.01)


def build_F22_lighthouse():
    # 7.0 x 7.0 x 11.5m: West Cape Storybook Lighthouse
    cyl("Cobble_Plinth", (0, 0, 0.45), 3.2, 0.90, "limestone", sides=18, bevel=0.04)
    cyl("Plinth_Step", (0, -3.2, 0.18), 1.3, 0.36, "limestone", sides=10)
    # Tapered striped tower (cream & terracotta bands)
    bands = [
        (0.90, 2.60, 2.55, 2.25, "cream_wall"),
        (2.60, 4.30, 2.25, 1.98, "terracotta"),
        (4.30, 6.00, 1.98, 1.74, "cream_wall"),
        (6.00, 7.60, 1.74, 1.54, "terracotta"),
        (7.60, 8.60, 1.54, 1.42, "cream_wall"),
    ]
    for z0, z1, r0, r1, mkey in bands:
        cone(f"Tower_{mkey}", (0, 0, (z0 + z1) * 0.5), r0, r1, z1 - z0, mkey, sides=18, bevel=0.02)
    # Entrance door & porthole windows
    box("Door_Case", (0, -2.55, 1.55), (1.15, 0.35, 1.85), "ivory_trim")
    box("Door_Leaf", (0, -2.68, 1.50), (0.85, 0.14, 1.65), "warm_cedar")
    for pz, py in ((3.5, -2.10), (5.2, -1.84), (6.9, -1.62)):
        cyl("Porthole_Ring", (0, py, pz), 0.34, 0.18, "ivory_trim", sides=14, rot=(math.radians(90), 0, 0))
        cyl("Porthole_Glass", (0, py - 0.04, pz), 0.24, 0.16, "amber_glow", sides=14, rot=(math.radians(90), 0, 0))
    # Gallery balcony
    cyl("Gallery_Deck", (0, 0, 8.70), 2.15, 0.24, "warm_cedar", sides=18)
    for i in range(12):
        ang = math.tau * i / 12
        px, py = 1.98 * math.cos(ang), 1.98 * math.sin(ang)
        cyl("Balcony_Post", (px, py, 9.15), 0.06, 0.72, "ivory_trim", sides=8)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.98, minor_radius=0.07, location=(0, 0, 9.48))
    rail = bpy.context.object
    rail.name = "Gallery_Rail"
    rail.data.materials.append(get_mat("ivory_trim"))
    # Glowing amber glass lantern room + terracotta dome cap
    cyl("Lantern_Glass", (0, 0, 9.72), 1.15, 1.35, "amber_glow", sides=14)
    for i in range(6):
        ang = math.tau * i / 6
        box("Lantern_Mullion", (1.16 * math.cos(ang), 1.16 * math.sin(ang), 9.72), (0.10, 0.10, 1.40), "warm_slate")
    cone("Lighthouse_Cap", (0, 0, 10.85), 1.38, 0.18, 1.10, "terracotta", sides=16)
    sphere("Finial", (0, 0, 11.45), (0.20, 0.20, 0.20), "brass", subdiv=1)


def build_F23_cliff_cottage():
    # 5.5 x 4.5 x 4.2m: Northwest Cliff Slate-Blue Pointed Cottage
    box("Plinth", (0, 0.2, 0.14), (4.8, 3.8, 0.28), "limestone")
    box("Walls", (0, 0.2, 1.45), (4.5, 3.5, 2.35), "cream_wall", bevel=0.04)
    for sx in (-2.2, 2.2):
        box("Corner_Beam", (sx, -1.55, 1.45), (0.18, 0.16, 2.35), "honey_wood")
    gable_roof("Cliff_Roof", (0, 0.2), 5.3, 4.2, 2.60, 1.50, "slate_blue", "ivory_trim")
    # Dormer & fish weathervane
    box("Dormer", (-0.8, -0.8, 3.15), (1.1, 1.0, 0.8), "cream_wall")
    gable_roof("Dormer_Cap", (-0.8, -0.8), 1.3, 1.1, 3.52, 0.45, "slate_blue", "ivory_trim")
    cyl("Vane_Post", (0, 0.2, 4.18), 0.035, 0.45, "brass", sides=8)
    box("Fish_Vane", (0.16, 0.2, 4.35), (0.38, 0.04, 0.20), "brass", bevel=0.008)
    # Front porch, mint door & front mailbox
    box("Porch", (0, -1.85, 0.14), (1.7, 0.75, 0.28), "warm_cedar")
    box("Door_Frame", (0, -1.56, 1.18), (1.05, 0.16, 1.85), "ivory_trim")
    box("Door", (0, -1.62, 1.15), (0.85, 0.08, 1.72), "mint_wood")
    window_unit((-1.35, -1.56, 1.45), 0.82, 0.80, "-y")
    window_unit((1.35, -1.56, 1.45), 0.82, 0.80, "-y")
    lantern_unit((0.68, -1.72, 1.65), 0.7)
    cyl("Post_Box_Leg", (-1.75, -2.05, 0.45), 0.07, 0.85, "toasted_wood")
    box("Post_Box", (-1.75, -2.05, 0.95), (0.38, 0.34, 0.38), "coral_red", bevel=0.03)


def build_F24_campfire():
    # 6.0 x 5.0 x 1.4m: Driftwood Beach Campfire Circle
    for i in range(10):
        ang = math.tau * i / 10
        sphere(f"Stone_{i}", (0.92 * math.cos(ang), 0.92 * math.sin(ang), 0.14), (0.24, 0.22, 0.16), "limestone", 1)
    for i in range(4):
        ang = math.tau * i / 4 + 0.3
        cyl(f"Log_{i}", (0.2 * math.cos(ang), 0.2 * math.sin(ang), 0.20), 0.11, 0.95, "toasted_wood", 8,
            rot=(math.radians(65), 0, ang))
    cone("Fire_Outer", (0, 0, 0.45), 0.38, 0.06, 0.72, "hearth_fire", sides=8)
    cone("Fire_Core", (0, 0, 0.38), 0.22, 0.04, 0.48, "amber_glow", sides=8)
    # 3 curved driftwood log benches
    for ang, l_w in ((math.radians(-40), 2.1), (math.radians(80), 2.0), (math.radians(200), 2.1)):
        lx, ly = 2.05 * math.cos(ang), 2.05 * math.sin(ang)
        cyl("Driftwood_Seat", (lx, ly, 0.24), 0.24, l_w, "driftwood", 10, rot=(0, math.radians(90), ang + math.pi * 0.5))
    # Tripod kettle
    for i in range(3):
        a = math.tau * i / 3
        beam("Tripod_Leg", (0.75 * math.cos(a), 0.75 * math.sin(a), 0.0), (0, 0, 1.35), 0.06, 0.06, "toasted_wood", 0.01)
    sphere("Kettle", (0, 0, 0.85), (0.22, 0.22, 0.18), "basalt", 1)


def build_F25_bakery_kiln():
    # 12.0 x 9.5 x 4.2m: Night-Market Brick Bakery Kiln, Stall & Theater Seating
    box("Theater_Deck", (0, -0.4, 0.10), (10.8, 8.2, 0.20), "limestone")
    # Red-brick bread kiln (-2.4, 1.5)
    cyl("Kiln_Plinth", (-2.4, 1.5, 0.45), 1.65, 0.65, "limestone", sides=14)
    sphere("Kiln_Dome", (-2.4, 1.5, 1.15), (1.52, 1.52, 1.35), "terracotta", 2)
    box("Kiln_Mouth", (-2.4, 0.18, 0.92), (0.95, 0.50, 0.78), "terracotta")
    box("Kiln_Hearth_Glow", (-2.4, 0.02, 0.88), (0.62, 0.15, 0.52), "hearth_fire", bevel=0.01)
    cyl("Kiln_Chimney", (-2.4, 1.85, 2.85), 0.34, 1.65, "terracotta", sides=10)
    # Joined honey-wood bakery stall (1.8, 1.2)
    box("Stall_Counter", (1.8, 0.8, 0.68), (4.4, 1.6, 1.0), "honey_wood")
    for x in (-0.2, 3.8):
        for y in (0.1, 1.5):
            box("Stall_Post", (x, y, 1.75), (0.20, 0.20, 3.1), "toasted_wood")
    # Striped cream-and-amber scalloped awning
    for idx in range(7):
        ax = -0.05 + idx * 0.62
        mk = "amber_glow" if idx % 2 == 0 else "ivory_trim"
        box("Awning_Strip", (ax, 0.75, 3.15), (0.60, 2.3, 0.14), mk, rot=(math.radians(16), 0, 0))
    # Golden croissants/buns on trays
    box("Bread_Tray", (1.2, 0.55, 1.24), (1.4, 0.65, 0.08), "warm_cedar")
    for bx in (0.8, 1.2, 1.6):
        sphere("Golden_Bun", (bx, 0.55, 1.36), (0.16, 0.14, 0.11), "golden_maple", 1)
    # String-light poles & glowing amber fairy bulbs across front theater
    for px in (-4.4, 4.4):
        cyl("String_Pole", (px, -3.2, 1.65), 0.11, 3.2, "toasted_wood")
    for i in range(9):
        t = i / 8
        bx = -4.4 + 8.8 * t
        bz = 3.15 - 0.55 * math.sin(math.pi * t)
        sphere(f"Fairy_Bulb_{i}", (bx, -3.2, bz), (0.12, 0.12, 0.12), "amber_glow", 1)
    # Semicircular wooden theater benches facing the kiln/stall
    for ang in (math.radians(-145), math.radians(-110), math.radians(-70), math.radians(-35)):
        bx, by = 3.4 * math.cos(ang), -0.6 + 2.6 * math.sin(ang)
        box("Theater_Bench", (bx, by, 0.38), (1.85, 0.58, 0.34), "warm_cedar", rot=(0, 0, ang + math.pi * 0.5))


def build_F26_boatyard():
    # 10.0 x 8.0 x 5.0m: Coastal Wooden Boatyard Workshop
    box("Boatyard_Deck", (0, 0, 0.14), (9.6, 7.6, 0.28), "warm_cedar")
    for x in (-4.2, 0.0, 4.2):
        for y in (-3.1, 3.1):
            box("Timber_Post", (x, y, 1.95), (0.28, 0.28, 3.6), "toasted_wood")
    gable_roof("Boatyard_Roof", (0, 0), 10.0, 7.8, 3.70, 1.35, "slate_blue", "honey_wood")
    # Half-built wooden dinghy hull on cradles inside
    for cx in (-1.4, 1.4):
        box("Sawhorse", (cx, -0.2, 0.55), (0.35, 1.6, 0.65), "toasted_wood")
    for i in range(6):
        rx = -2.2 + i * 0.88
        w = 1.65 * math.sin(math.pi * (0.15 + 0.7 * i / 5))
        box("Hull_Rib", (rx, -0.2, 1.05), (0.14, w, 0.65), "honey_wood", bevel=0.02)
    box("Keel_Beam", (0, -0.2, 0.85), (4.8, 0.24, 0.24), "warm_cedar")
    # Tool rack & mint paint buckets
    box("Tool_Bench", (-3.2, 2.2, 0.65), (2.4, 0.85, 0.85), "honey_wood")
    cyl("Paint_Bucket", (2.8, 2.1, 0.48), 0.24, 0.42, "mint_wood", sides=10)
    cyl("Rope_Coil", (3.3, -2.1, 0.40), 0.38, 0.26, "cream_rope", sides=12)
    lantern_unit((0, -3.1, 3.05), 1.0)


def build_F27_lightship():
    # 11.0 x 5.0 x 9.5m: Beached "Daylight" Tidal Lightship
    # Wooden chocks under gently tilted plump hull
    for cx in (-2.8, 2.8):
        box("Ship_Chock", (cx, 0, 0.22), (0.55, 2.8, 0.44), "toasted_wood")
    # Plump hull shell (layered cream upper, mint lower, honey-oak gunwales)
    sphere("Hull_Mint", (0, 0, 1.15), (5.2, 2.25, 1.05), "mint_wood", 2)
    sphere("Hull_Cream", (0, 0, 1.52), (5.3, 2.30, 0.62), "cream_wall", 2)
    box("Main_Deck", (0, 0, 1.78), (8.6, 3.5, 0.22), "warm_cedar", bevel=0.04)
    # Bow figure & boarding gangplank on -Y side
    cone("Bowsprit", (-5.2, 0, 2.05), 0.16, 0.06, 2.2, "honey_wood", sides=8)
    beam("Gangplank", (1.2, -1.65, 1.78), (1.8, -3.55, 0.05), 1.05, 0.14, "honey_wood")
    # Cozy deckhouse cabin
    box("Cabin", (1.4, 0, 2.65), (3.4, 2.4, 1.65), "cream_wall", bevel=0.04)
    hip_roof("Cabin_Roof", (1.4, 0), 3.8, 2.8, 3.45, 0.72, 0.65, "terracotta", "ivory_trim")
    cyl("Porthole", (1.4, -1.22, 2.72), 0.26, 0.12, "amber_glow", sides=12, rot=(math.radians(90), 0, 0))
    # Tall beacon mast (9.5m!) with ratlines, brass ship bell & glowing lantern cage
    cyl("Main_Mast", (-0.8, 0, 5.25), 0.22, 7.2, "toasted_wood", sides=12)
    box("Cross_Yard", (-0.8, 0, 6.8), (0.20, 3.1, 0.18), "honey_wood")
    cyl("Mast_Beacon", (-0.8, 0, 8.95), 0.62, 0.88, "amber_glow", sides=12)
    cone("Mast_Cap", (-0.8, 0, 9.52), 0.78, 0.10, 0.55, "terracotta", sides=12)
    cone("Ship_Bell", (-0.4, -0.35, 3.15), 0.22, 0.10, 0.30, "brass", sides=10)


def build_F28_tidepool_rocks():
    # 11.0 x 8.5 x 1.5m: Intertidal Smooth Sandstone Boulders & Starfish/Hermit Crab
    boulders = [
        (-3.6, -2.0, 0.45, 1.35, 1.15, 0.78),
        (-2.4, 2.4, 0.50, 1.45, 1.25, 0.85),
        (2.8, 2.1, 0.42, 1.25, 1.05, 0.72),
        (3.4, -1.8, 0.48, 1.40, 1.15, 0.80),
        (-0.8, 2.9, 0.35, 0.95, 0.85, 0.55),
    ]
    for i, (bx, by, bz, sx, sy, sz) in enumerate(boulders):
        sphere(f"Tidal_Boulder_{i}", (bx, by, bz), (sx, sy, sz), "limestone", 2)
        sphere(f"Boulder_Moss_{i}", (bx, by, bz + sz * 0.45), (sx * 0.78, sy * 0.78, sz * 0.35), "sage_leaf", 1)
    # Coral starfish & cute hermit crab shell
    for sx, sy, mk in ((-1.2, -0.6, "coral_red"), (1.4, 0.8, "peach_blossom"), (0.2, -1.3, "amber_glow")):
        sphere("Starfish", (sx, sy, 0.08), (0.35, 0.35, 0.08), mk, 1)
    cone("Hermit_Shell", (0.8, -0.3, 0.24), 0.26, 0.04, 0.38, "coral_red", sides=10)


def build_F29_kite_terrace():
    # 9.0 x 7.0 x 2.8m: Camellia Terrace Wooden Deck & Kite Stand
    box("Lower_Deck", (0, -0.8, 0.12), (8.4, 4.8, 0.24), "warm_cedar")
    box("Upper_Deck", (0, 1.2, 0.28), (7.6, 2.6, 0.32), "honey_wood")
    # Raised camellia troughs
    for tx in (-2.6, 2.6):
        box("Camellia_Box", (tx, -2.3, 0.42), (2.4, 0.95, 0.55), "toasted_wood")
        for dx in (-0.7, 0.0, 0.7):
            sphere("Camellia_Bush", (tx + dx, -2.3, 0.82), (0.45, 0.42, 0.36), "sage_leaf", 1)
            sphere("Camellia_Bloom", (tx + dx, -2.45, 1.02), (0.14, 0.14, 0.12), "peach_blossom", 1)
    # Wooden bench + upright kite display stand
    box("Bench_Seat", (-1.8, 1.2, 0.72), (2.4, 0.75, 0.14), "honey_wood")
    for px in (1.2, 2.8):
        cyl("Kite_Post", (px, 1.2, 1.45), 0.09, 2.3, "toasted_wood")
    beam("Kite_Bar", (1.0, 1.2, 2.45), (3.0, 1.2, 2.45), 0.12, 0.12, "honey_wood")
    # Two colorful diamond paper kites
    box("Kite_Coral", (1.55, 1.10, 1.85), (0.72, 0.05, 0.72), "coral_red", bevel=0.01, rot=(0, math.radians(45), 0))
    box("Kite_Blue", (2.45, 1.10, 1.80), (0.68, 0.05, 0.68), "sea_blue", bevel=0.01, rot=(0, math.radians(45), 0))


def build_F30_studio_cottage():
    # 5.5 x 4.5 x 4.2m: East-Shore Mustard Craft Studio Cottage with Easel
    box("Plinth", (0, 0.2, 0.14), (4.8, 3.8, 0.28), "limestone")
    box("Walls", (0, 0.2, 1.45), (4.5, 3.5, 2.35), "mustard_wall", bevel=0.04)
    gable_roof("Studio_Roof", (0, 0.2), 5.3, 4.2, 2.60, 1.45, "mint_wood", "ivory_trim")
    # Roof skylight
    box("Skylight_Frame", (0.7, -0.4, 3.45), (1.3, 1.1, 0.18), "ivory_trim", rot=(0, math.radians(28), 0))
    box("Skylight_Glass", (0.72, -0.4, 3.50), (1.05, 0.85, 0.08), "mint_glass", rot=(0, math.radians(28), 0))
    box("Door", (0, -1.58, 1.15), (0.95, 0.12, 1.75), "warm_cedar")
    window_unit((-1.4, -1.56, 1.45), 0.9, 0.82, "-y")
    window_unit((1.4, -1.56, 1.45), 0.9, 0.82, "-y")
    # Outdoor painting easel & paintbrush jar
    beam("Easel_L", (1.65, -2.15, 0.0), (1.85, -1.95, 1.55), 0.08, 0.08, "toasted_wood")
    beam("Easel_R", (2.05, -2.15, 0.0), (1.85, -1.95, 1.55), 0.08, 0.08, "toasted_wood")
    box("Canvas", (1.85, -2.12, 1.10), (0.72, 0.06, 0.58), "cream_wall", bevel=0.01, rot=(math.radians(-12), 0, 0))
    cyl("Brush_Jar", (-1.55, -1.95, 0.28), 0.16, 0.35, "terracotta", sides=10)


def build_F31_memory_greenhouse():
    # 12.0 x 9.0 x 6.2m: Valley Memory Conservatory Greenhouse & Library
    box("Floor", (0, 0, 0.14), (11.6, 8.6, 0.28), "limestone")
    # Low cobblestone dwarf walls with arched opening in front (-Y)
    box("Wall_Back", (0, 4.0, 0.85), (11.2, 0.45, 1.25), "limestone")
    for sx in (-5.4, 5.4):
        box("Wall_Side", (sx, 0, 0.85), (0.45, 8.2, 1.25), "limestone")
    for sx in (-3.6, 3.6):
        box("Wall_Front", (sx, -4.0, 0.85), (3.8, 0.45, 1.25), "limestone")
    # Barrel-vault arched honey-oak structural ribs & translucent mint glass roof
    for y in (-3.8, -1.9, 0.0, 1.9, 3.8):
        for seg in range(10):
            a0 = math.pi * seg / 10
            a1 = math.pi * (seg + 1) / 10
            p0 = (5.4 * math.cos(a0), y, 1.45 + 4.4 * math.sin(a0))
            p1 = (5.4 * math.cos(a1), y, 1.45 + 4.4 * math.sin(a1))
            beam("Vault_Rib", p0, p1, 0.20, 0.20, "ivory_trim")
    # Translucent glass barrel shell
    cyl("Glass_Vault", (0, 0, 2.25), 5.25, 7.8, "mint_glass", sides=16, bevel=0.0, rot=(math.radians(90), 0, 0))
    # Front arched portal & double doors
    box("Portal_Frame", (0, -4.05, 1.75), (2.4, 0.35, 3.0), "honey_wood")
    box("Portal_Door", (0, -4.15, 1.60), (1.85, 0.12, 2.65), "mint_glass")
    # Cozy visible interior bookshelves & warm amber reading lamps!
    for bx in (-3.2, 3.2):
        for by in (-1.2, 1.6):
            box("Bookshelf", (bx, by, 1.25), (0.85, 2.1, 2.1), "warm_cedar")
            box("Books_Row", (bx - 0.1 if bx > 0 else bx + 0.1, by, 1.55), (0.70, 1.85, 0.38), "coral_red", bevel=0.01)
    box("Reading_Table", (0, 0.6, 0.58), (2.2, 1.3, 0.78), "honey_wood")
    lantern_unit((0, 0.6, 0.98), 0.9)
    # Rose planter beds inside
    box("Rose_Bed", (0, 2.9, 0.45), (3.4, 1.1, 0.48), "toasted_wood")
    for rx in (-1.0, 0.0, 1.0):
        sphere("Rose_Crown", (rx, 2.9, 0.85), (0.38, 0.35, 0.28), "sage_leaf", 1)
        sphere("Blue_Rose", (rx, 2.9, 1.08), (0.12, 0.12, 0.10), "sea_blue", 1)
    lantern_unit((-1.4, -4.2, 2.25), 0.9)
    lantern_unit((1.4, -4.2, 2.25), 0.9)


def build_F32_creek_bridge():
    # 2.8 x 5.6 x 2.0m: Firefly Creek Arched Timber Footbridge (matches 5.4m span, 0.38m rise)
    steps = 12
    span = 5.4
    rise = 0.38
    for sx in (-1.35, 1.35):
        box("Abutment", (sx, -span * 0.5, 0.05), (0.45, 0.55, 0.35), "limestone")
        box("Abutment_B", (sx, span * 0.5, 0.05), (0.45, 0.55, 0.35), "limestone")
    for i in range(steps):
        t = (i + 0.5) / steps
        y = -span * 0.5 + span * t
        u = 2.0 * t - 1.0
        z = rise * (1.0 - u * u)
        slope = math.atan2(-4.0 * rise * u / span, 1.0)
        box("Deck_Plank", (0, y, z + 0.04), (2.6, span / steps - 0.03, 0.14), "honey_wood", bevel=0.015, rot=(-slope, 0, 0))
    for sx in (-1.22, 1.22):
        rail_pts = []
        for k in range(5):
            t = k / 4
            y = -span * 0.5 + span * t
            u = 2.0 * t - 1.0
            z = rise * (1.0 - u * u)
            cyl("Rail_Post", (sx, y, z + 0.45), 0.07, 0.82, "toasted_wood", sides=8)
            rail_pts.append((sx, y, z + 0.84))
        for k in range(4):
            beam("Handrail", rail_pts[k], rail_pts[k + 1], 0.11, 0.11, "honey_wood")
    lantern_unit((-1.22, -span * 0.5, 0.88), 0.8)
    lantern_unit((1.22, span * 0.5, 0.88), 0.8)


def build_F33_watermill():
    # 7.0 x 6.0 x 4.8m: Forest Watermill Cottage & Vintage Phonograph Kiosk
    box("Stone_Lower", (0, 0.2, 1.05), (5.2, 4.4, 2.1), "limestone", bevel=0.04)
    box("Timber_Upper", (0, 0.2, 2.65), (5.0, 4.2, 1.2), "cream_wall", bevel=0.04)
    gable_roof("Mill_Roof", (0, 0.2), 5.8, 4.9, 3.22, 1.48, "terracotta", "honey_wood")
    box("Mill_Door", (-0.8, -2.02, 1.05), (0.95, 0.12, 1.75), "warm_cedar")
    window_unit((1.1, -2.02, 1.25), 0.85, 0.80, "-y")
    # Big circular honey-oak paddle waterwheel attached on creek-facing side (local -X -> East +X_u when yaw=180)
    wheel_x = -2.95
    bpy.ops.mesh.primitive_torus_add(major_radius=1.35, minor_radius=0.14, location=(wheel_x, 0.2, 1.35),
                                     rotation=(0, math.radians(90), 0))
    rim = bpy.context.object
    rim.name = "Wheel_Rim"
    rim.data.materials.append(get_mat("warm_cedar"))
    cyl("Wheel_Axle", (-2.65, 0.2, 1.35), 0.22, 0.95, "toasted_wood", rot=(0, math.radians(90), 0))
    for i in range(8):
        ang = math.tau * i / 8
        py = 0.2 + 1.35 * math.cos(ang)
        pz = 1.35 + 1.35 * math.sin(ang)
        beam("Wheel_Spoke", (wheel_x, 0.2, 1.35), (wheel_x, py, pz), 0.12, 0.12, "honey_wood")
        box("Wheel_Paddle", (wheel_x, py, pz), (0.48, 0.28, 0.10), "toasted_wood", rot=(ang, 0, 0))
    # Vintage phonograph kiosk on front porch
    box("Phono_Table", (1.4, -2.45, 0.45), (0.95, 0.85, 0.78), "honey_wood")
    box("Phono_Box", (1.4, -2.45, 0.98), (0.45, 0.45, 0.25), "terracotta")
    cone("Brass_Horn", (1.4, -2.55, 1.35), 0.06, 0.30, 0.42, "brass", sides=12)


def build_F34_camphor_bell():
    # 12.0 x 10.0 x 12.5m: Ancient Camphor Tree, Circular Viewing Deck & Bronze Bell Tower
    # Raised circular chamfered wooden viewing deck
    cyl("Viewing_Deck", (0, 0, 0.24), 4.8, 0.48, "warm_cedar", sides=28, bevel=0.04)
    for i in range(18):
        ang = math.tau * i / 18
        if abs(ang + math.pi * 0.5) < 0.35:  # leave South entrance gap (-Y)
            continue
        cyl("Deck_Post", (4.55 * math.cos(ang), 4.55 * math.sin(ang), 0.88), 0.08, 0.82, "toasted_wood", sides=8)
    bpy.ops.mesh.primitive_torus_add(major_radius=4.55, minor_radius=0.09, location=(0, 0, 1.28))
    dr = bpy.context.object
    dr.name = "Deck_Rail"
    dr.data.materials.append(get_mat("honey_wood"))
    # Majestic ancient camphor trunk & gnarled roots + 5-puff rounded canopy + golden star lanterns
    cone("Camphor_Trunk", (0, 0.4, 3.1), 1.35, 0.85, 5.4, "dark_bark", sides=14)
    for ang in (0.4, 1.8, 3.2, 4.8):
        beam("Camphor_Branch", (0, 0.4, 4.4), (2.4 * math.cos(ang), 0.4 + 2.4 * math.sin(ang), 7.2), 0.55, 0.55, "dark_bark")
    canopies = [
        ((0, 0.4, 9.2), (3.6, 3.4, 2.6), "sage_leaf"),
        ((-2.6, 0.8, 7.8), (2.4, 2.3, 1.9), "cream_green"),
        ((2.6, 0.2, 7.9), (2.5, 2.3, 1.9), "sage_leaf"),
        ((0.0, -1.8, 7.6), (2.2, 2.0, 1.7), "cream_green"),
        ((0.2, 2.4, 8.0), (2.3, 2.2, 1.8), "sage_leaf"),
    ]
    for pos, rad, mk in canopies:
        sphere("Camphor_Canopy", pos, rad, mk, 2)
    for i in range(6):
        ang = math.tau * i / 6
        wind_chime((3.1 * math.cos(ang), 0.4 + 3.1 * math.sin(ang), 6.2), "amber_glow")
    # Adjacent open-frame timber belfry pavilion (+3.6, -1.6) with bronze town bell
    bx, by = 3.8, -1.8
    box("Belfry_Base", (bx, by, 0.24), (2.6, 2.6, 0.48), "limestone")
    for dx in (-0.95, 0.95):
        for dy in (-0.95, 0.95):
            box("Belfry_Post", (bx + dx, by + dy, 2.1), (0.20, 0.20, 3.3), "toasted_wood")
    hip_roof("Belfry_Roof", (bx, by), 3.1, 3.1, 3.72, 1.15, 0.4, "terracotta", "ivory_trim")
    cone("Town_Bronze_Bell", (bx, by, 2.95), 0.55, 0.26, 0.78, "brass", sides=14)


def build_F35_slide_modular():
    # 2.4 x 8.0 x 3.2m: Modular Curved Wooden Slide Chute (standalone asset for manifest)
    pts = [(0, -3.8, 0.05), (0, -2.0, 0.55), (0, 0.0, 1.35), (0, 2.0, 2.25), (0, 3.8, 3.05)]
    build_slide_from_pts("F35_Slide", pts)


def build_slide_from_pts(prefix: str, pts_b: list[tuple[float, float, float]]):
    """Build a smooth rounded wooden trough slide with side curbs, trestle legs & top arch."""
    for i in range(len(pts_b) - 1):
        a, b = Vector(pts_b[i]), Vector(pts_b[i + 1])
        mid = (a + b) * 0.5
        delta = b - a
        pitch = math.atan2(delta.z, math.hypot(delta.x, delta.y))
        yaw = math.atan2(delta.y, delta.x) - math.pi * 0.5
        seg_len = delta.length + 0.08
        box(f"{prefix}_Bed_{i}", tuple(mid), (1.75, seg_len, 0.16), "honey_wood", bevel=0.02, rot=(pitch, 0, yaw))
        perp = Vector((-delta.y, delta.x, 0)).normalized()
        for side in (-0.96, 0.96):
            cp = mid + perp * side + Vector((0, 0, 0.22))
            box(f"{prefix}_Curb_{i}", tuple(cp), (0.18, seg_len, 0.42), "warm_cedar", bevel=0.02, rot=(pitch, 0, yaw))
    # Trestle A-frame legs
    for i, p in enumerate(pts_b):
        if p[2] > 0.35:
            cyl(f"{prefix}_Trestle_L_{i}", (p[0] - 0.75, p[1], p[2] * 0.5), 0.10, p[2], "toasted_wood", 8)
            cyl(f"{prefix}_Trestle_R_{i}", (p[0] + 0.75, p[1], p[2] * 0.5), 0.10, p[2], "toasted_wood", 8)
    # Entrance arch at top & hay cushion at bottom
    top = pts_b[0] if pts_b[0][2] > pts_b[-1][2] else pts_b[-1]
    bot = pts_b[-1] if pts_b[0][2] > pts_b[-1][2] else pts_b[0]
    for sx in (-0.95, 0.95):
        cyl(f"{prefix}_ArchPost", (top[0] + sx, top[1], top[2] + 0.95), 0.10, 1.9, "honey_wood", 8)
    box(f"{prefix}_ArchBeam", (top[0], top[1], top[2] + 1.90), (2.2, 0.24, 0.24), "coral_red")
    box(f"{prefix}_HayPad", (bot[0], bot[1], bot[2] + 0.12), (2.3, 1.6, 0.24), "golden_maple", bevel=0.04)


def build_F36_tree_hollow():
    # 5.0 x 4.5 x 3.5m: Secret Tree-Hollow Nook with Mailbox & Photo Frame
    cone("Stump_Body", (0, 0, 1.45), 1.75, 1.25, 2.9, "dark_bark", sides=14)
    sphere("Stump_Top_Crown", (0.6, 0.4, 2.95), (0.95, 0.85, 0.65), "sage_leaf", 1)
    sphere("Stump_Top_B", (-0.7, 0.5, 2.75), (0.65, 0.60, 0.48), "golden_maple", 1)
    # Arched warm glowing doorway nook (-Y)
    box("Hollow_Trim", (0, -1.25, 1.05), (1.45, 0.45, 1.75), "honey_wood")
    box("Hollow_Glow", (0, -1.42, 0.98), (1.05, 0.16, 1.45), "amber_glow")
    # Photo cards & tiny red secret mailbox
    for px, mk in ((-0.26, "peach_blossom"), (0.24, "sea_blue")):
        box("Photo_Card", (px, -1.52, 1.15), (0.34, 0.04, 0.34), mk, bevel=0.008)
    cyl("Secret_Box_Leg", (-1.35, -1.45, 0.48), 0.07, 0.90, "toasted_wood")
    box("Secret_Box", (-1.35, -1.45, 0.98), (0.40, 0.36, 0.38), "coral_red", bevel=0.03)


def build_F37_sea_arch_bridge():
    # 2.8 x 16.5 x 3.0m: Curved Coastal Wooden Arch Bridge (span 16.28m, rise 0.95m)
    span = 16.28
    rise = 0.95
    steps = 26
    for i in range(steps):
        t = (i + 0.5) / steps
        y = -span * 0.5 + span * t
        u = 2.0 * t - 1.0
        z = rise * (1.0 - u * u)
        slope = math.atan2(-4.0 * rise * u / span, 1.0)
        mk = "honey_wood" if i % 2 == 0 else "warm_cedar"
        box(f"Bridge_Plank_{i}", (0, y, z + 0.04), (2.75, span / steps - 0.04, 0.16), mk, bevel=0.018, rot=(-slope, 0, 0))
    # Submerged wooden pile bents
    for py in (-5.4, -1.8, 1.8, 5.4):
        u = py / (span * 0.5)
        pz = rise * (1.0 - u * u)
        for px in (-1.2, 1.2):
            cyl("Bridge_Piling", (px, py, (pz - 1.2) * 0.5), 0.18, pz + 1.2, "toasted_wood", sides=10)
    # Balustrades & crest/end lantern posts
    for sx in (-1.30, 1.30):
        rail_pts = []
        for k in range(9):
            t = k / 8
            y = -span * 0.5 + span * t
            u = 2.0 * t - 1.0
            z = rise * (1.0 - u * u)
            cyl("Balustrade_Post", (sx, y, z + 0.48), 0.08, 0.88, "toasted_wood", sides=8)
            rail_pts.append((sx, y, z + 0.90))
        for k in range(8):
            beam("Bridge_Rail", rail_pts[k], rail_pts[k + 1], 0.12, 0.12, "honey_wood")
    for ly, lz in ((-span * 0.46, 0.95), (0.0, 1.85), (span * 0.46, 0.95)):
        lantern_unit((-1.30, ly, lz), 0.9)
        lantern_unit((1.30, ly, lz), 0.9)


def build_F38_stepping_stones():
    # 2.6 x 17.8 x 1.2m: East Tidal Flat Basalt Stepping Stones & Mossy Lantern Posts
    span = 17.72
    count = 13
    for i in range(count):
        t = (i + 0.5) / count
        y = -span * 0.5 + span * t
        x = 0.25 * math.sin(i * 1.4)
        cyl(f"Basalt_Pad_{i}", (x, y, -0.04), 0.95, 0.36, "basalt", sides=12, bevel=0.05)
        if i % 3 == 0:
            sphere(f"Moss_Rim_{i}", (x + 0.65, y, 0.02), (0.35, 0.30, 0.14), "sage_leaf", 1)
    # Guide stakes with cream rope & lanterns
    for i, gy in enumerate((-6.5, -2.2, 2.2, 6.5)):
        cyl("Guide_Stake", (-1.18, gy, 0.48), 0.09, 1.1, "toasted_wood", sides=8)
        if i in (0, 3):
            lantern_unit((-1.18, gy, 1.02), 0.75)
    beam("Rope_A", (-1.18, -6.5, 0.85), (-1.18, -2.2, 0.85), 0.04, 0.04, "cream_rope", 0.005)
    beam("Rope_B", (-1.18, -2.2, 0.85), (-1.18, 2.2, 0.85), 0.04, 0.04, "cream_rope", 0.005)
    beam("Rope_C", (-1.18, 2.2, 0.85), (-1.18, 6.5, 0.85), 0.04, 0.04, "cream_rope", 0.005)


def build_F39_echo_amphitheater():
    # 10.0 x 9.0 x 6.5m: Tidal Echo Driftwood Amphitheater Arch
    cyl("Stage_Step_1", (0, 0, 0.14), 4.6, 0.28, "warm_cedar", sides=24)
    cyl("Stage_Step_2", (0, 0.6, 0.34), 3.4, 0.28, "honey_wood", sides=24)
    # Grand curving sun-bleached driftwood arch gateway
    n_arch = 16
    prev_p = None
    for i in range(n_arch + 1):
        ang = math.pi * i / n_arch
        px = 3.65 * math.cos(ang)
        pz = 0.25 + 5.75 * math.sin(ang)
        py = 0.8 + 0.35 * math.sin(ang * 2)
        p = (px, py, pz)
        if prev_p is not None:
            r = 0.34 - 0.10 * math.sin(ang)
            beam(f"Drift_Arch_{i}", prev_p, p, r * 2, r * 2, "driftwood", bevel=0.04)
            if 2 <= i <= n_arch - 2 and i % 2 == 0:
                wind_chime((px, py, pz - 0.25), ("mint_glass", "peach_blossom", "sea_blue")[i % 3])
        prev_p = p
    # Music stands & sconces
    for sx in (-1.4, 1.4):
        cyl("Stand_Pole", (sx, -1.6, 0.72), 0.05, 0.95, "toasted_wood", 8)
        box("Stand_Desk", (sx, -1.6, 1.18), (0.55, 0.38, 0.06), "honey_wood", rot=(math.radians(25), 0, 0))
    lantern_unit((-3.7, 0.4, 0.45), 1.0)
    lantern_unit((3.7, 0.4, 0.45), 1.0)


def build_F40_ferry_dock():
    # 5.0 x 4.5 x 2.2m: South Islet North Ferry Pier + Moored Cream-and-Mint Rowboat
    box("Pier_Deck", (0, 0.4, 0.20), (3.6, 3.8, 0.18), "honey_wood")
    for sx in (-1.6, 1.6):
        for sy in (-1.2, 0.4, 1.9):
            cyl("Pier_Post", (sx, sy, 0.45), 0.15, 1.15, "toasted_wood", sides=10)
    lantern_unit((-1.6, 1.9, 1.02), 0.9)
    # Plump wooden ferry rowboat moored at +Y (bay side)
    bx, by, bz = 2.2, 2.35, 0.05
    sphere("Boat_Hull_Mint", (bx, by, bz + 0.18), (0.80, 1.75, 0.42), "mint_wood", 2)
    sphere("Boat_Hull_Cream", (bx, by, bz + 0.38), (0.82, 1.78, 0.22), "cream_wall", 2)
    box("Boat_Bench_A", (bx, by - 0.45, bz + 0.56), (1.15, 0.32, 0.08), "warm_cedar")
    box("Boat_Bench_B", (bx, by + 0.45, bz + 0.56), (1.15, 0.32, 0.08), "warm_cedar")
    beam("Oar_L", (bx - 0.75, by - 0.8, bz + 0.62), (bx - 0.95, by + 0.9, bz + 0.45), 0.06, 0.06, "honey_wood")
    beam("Oar_R", (bx + 0.75, by - 0.8, bz + 0.62), (bx + 0.95, by + 0.9, bz + 0.45), 0.06, 0.06, "honey_wood")
    cyl("Bow_Lantern_Pole", (bx, by + 1.55, bz + 0.78), 0.05, 0.65, "toasted_wood", 8)
    lantern_unit((bx, by + 1.55, bz + 1.08), 0.65)


def build_F41_mini_book_booth():
    # 2.5 x 2.0 x 2.6m: Miniature Coastal Drift-Book Phonebooth
    box("Base", (0, 0, 0.10), (2.2, 1.8, 0.20), "limestone")
    box("Booth_Body", (0, 0, 1.15), (1.35, 1.25, 1.95), "mint_wood", bevel=0.04)
    box("Door_Frame", (0, -0.62, 1.12), (0.98, 0.08, 1.65), "cream_wall")
    box("Glass_Pane", (0, -0.66, 1.22), (0.72, 0.04, 1.22), "mint_glass", bevel=0.008)
    for sz, mk in ((0.85, "coral_red"), (1.35, "sea_blue")):
        box("Book_Row", (0, -0.35, sz), (0.95, 0.35, 0.28), mk, bevel=0.01)
    hip_roof("Booth_Cap", (0, 0), 1.65, 1.55, 2.10, 0.48, 0.25, "terracotta", "ivory_trim")
    lantern_unit((0, -0.3, 1.68), 0.55)


def build_F42_postal_bike_stop():
    # 2.4 x 1.2 x 2.3m: Vintage Mint Postman Bicycle & Enamel Waypoint Signpost
    # Signpost at X = -0.65
    cyl("Sign_Base", (-0.65, 0, 0.08), 0.26, 0.16, "limestone", 10)
    cyl("Sign_Pole", (-0.65, 0, 1.05), 0.06, 1.85, "toasted_wood", 8)
    cyl("Sign_Medallion", (-0.65, -0.04, 1.95), 0.36, 0.10, "mint_wood", 16, rot=(math.radians(90), 0, 0))
    box("Envelope_Icon", (-0.65, -0.10, 1.95), (0.36, 0.04, 0.24), "cream_wall", bevel=0.01)
    lantern_unit((-0.25, 0, 1.62), 0.6)
    # Vintage mint postman bicycle at X = +0.45
    for wx in (-0.05, 0.95):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.30, minor_radius=0.06, location=(wx, 0, 0.34),
                                         rotation=(math.radians(90), 0, 0))
        w = bpy.context.object
        w.name = "Bike_Wheel"
        w.data.materials.append(get_mat("cream_wall"))
    beam("Frame_Main", (-0.05, 0, 0.34), (0.85, 0, 0.72), 0.06, 0.06, "mint_wood")
    beam("Frame_Fork", (0.95, 0, 0.34), (0.75, 0, 0.92), 0.06, 0.06, "mint_wood")
    box("Saddle", (0.28, 0, 0.85), (0.26, 0.18, 0.08), "toasted_wood")
    box("Wicker_Basket", (0.86, 0, 0.88), (0.32, 0.36, 0.26), "honey_wood")
    box("Letters", (0.86, 0, 1.02), (0.22, 0.24, 0.08), "cream_wall", bevel=0.008)


# === Trees (E01 / E02) & Micro Affordances (P01-P06) ===

def build_tree_3puff(name_prefix: str, canopy_mat: str, accent_mat: str, height: float = 4.8):
    s = height / 4.8
    cone(f"{name_prefix}_Trunk", (0, 0, 1.15 * s), 0.26 * s, 0.14 * s, 2.3 * s, "dark_bark", 10)
    lobes = [(-0.55 * s, -0.2 * s, 2.5 * s, 0.92 * s), (0.55 * s, 0.25 * s, 2.6 * s, 0.88 * s), (0, 0, 3.35 * s, 1.12 * s)]
    for i, (lx, ly, lz, r) in enumerate(lobes):
        sphere(f"{name_prefix}_Puff_{i}", (lx, ly, lz), (r, r * 0.94, r * 0.82), canopy_mat if i < 2 else accent_mat, 2)


def build_P01_lamp():
    cyl("Lamp_Foot", (0, 0, 0.08), 0.22, 0.16, "limestone", 10)
    cyl("Lamp_Post", (0, 0, 0.82), 0.07, 1.45, "toasted_wood", 8)
    lantern_unit((0, 0, 1.48), 0.85)


def build_P02_tilted_mailbox():
    cyl("Post", (0, 0, 0.45), 0.06, 0.90, "toasted_wood", 8)
    box("Box", (0, 0, 0.98), (0.42, 0.38, 0.44), "mint_wood", bevel=0.04, rot=(0, math.radians(5), 0))
    box("Flag", (0.24, 0, 1.05), (0.05, 0.14, 0.22), "coral_red", bevel=0.005)


def build_P03_signpost():
    cyl("Post", (0, 0, 0.78), 0.08, 1.56, "toasted_wood", 8)
    box("Arrow_A", (0.15, 0, 1.35), (0.72, 0.08, 0.22), "honey_wood", bevel=0.015, rot=(0, math.radians(6), 0))
    box("Arrow_B", (-0.15, 0, 1.02), (0.68, 0.08, 0.22), "ivory_trim", bevel=0.015, rot=(0, math.radians(-5), 0))


def build_P04_chime_post():
    cyl("Post", (0, 0, 0.92), 0.08, 1.84, "driftwood", 8)
    beam("Cross", (-0.42, 0, 1.72), (0.42, 0, 1.78), 0.09, 0.09, "driftwood")
    wind_chime((-0.25, 0, 1.72), "peach_blossom")
    wind_chime((0.25, 0, 1.75), "mint_glass")


def build_P06_armillary():
    cyl("Plinth", (0, 0, 0.35), 0.36, 0.70, "limestone", 12)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.34, minor_radius=0.04, location=(0, 0, 1.08),
                                     rotation=(math.radians(35), 0, 0))
    bpy.context.object.data.materials.append(get_mat("brass"))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.28, minor_radius=0.035, location=(0, 0, 1.08),
                                     rotation=(0, math.radians(55), 0))
    bpy.context.object.data.materials.append(get_mat("brass"))
    sphere("Globe", (0, 0, 1.08), (0.14, 0.14, 0.14), "sea_blue", 1)


LANDMARK_BUILDERS = {
    "F19-windchime-post-office": build_F19_post_office,
    "F20-mailbox-gallery": build_F20_mailbox_gallery,
    "F21-windchime-corridor": build_F21_windchime_corridor,
    "F22-west-cape-lighthouse": build_F22_lighthouse,
    "F23-cliff-cottage": build_F23_cliff_cottage,
    "F24-driftwood-campfire": build_F24_campfire,
    "F25-bakery-kiln-stall": build_F25_bakery_kiln,
    "F26-old-boatyard": build_F26_boatyard,
    "F27-daylight-lightship": build_F27_lightship,
    "F28-tidepool-rocks": build_F28_tidepool_rocks,
    "F29-kite-terrace-bench": build_F29_kite_terrace,
    "F30-studio-cottage": build_F30_studio_cottage,
    "F31-memory-greenhouse": build_F31_memory_greenhouse,
    "F32-creek-arch-bridge": build_F32_creek_bridge,
    "F33-forest-watermill": build_F33_watermill,
    "F34-camphor-bell-pavilion": build_F34_camphor_bell,
    "F35-timber-slide": build_F35_slide_modular,
    "F36-tree-hollow-postbox": build_F36_tree_hollow,
    "F37-sea-arch-bridge": build_F37_sea_arch_bridge,
    "F38-tidal-stepping-stones": build_F38_stepping_stones,
    "F39-echo-amphitheater-arch": build_F39_echo_amphitheater,
    "F40-ferry-dock-rowboat": build_F40_ferry_dock,
    "F41-mini-book-booth": build_F41_mini_book_booth,
    "F42-postal-bike-stop": build_F42_postal_bike_stop,
    "P01-clay-street-lamp": build_P01_lamp,
    "P02-vintage-mailbox": build_P02_tilted_mailbox,
    "P03-wooden-signpost": build_P03_signpost,
    "P04-shell-windchime-post": build_P04_chime_post,
    "P06-mini-armillary-sphere": build_P06_armillary,
    "E01-coastal-pine-tree": lambda: build_tree_3puff("Pine", "coastal_pine", "sage_leaf", 4.6),
    "E02-autumn-maple-tree": lambda: build_tree_3puff("Maple", "golden_maple", "coral_red", 5.0),
}


def generate_all_landmark_glbs():
    LANDMARKS_DIR.mkdir(parents=True, exist_ok=True)
    for lid, builder in LANDMARK_BUILDERS.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        builder()
        out_path = LANDMARKS_DIR / f"{lid}.glb"
        export_clean_glb(out_path)
        print(f"Exported {out_path.name} ({out_path.stat().st_size} B)")


def import_glb_as_collection(glb_path: Path, col_name: str) -> list[bpy.types.Object]:
    pre = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    objs = [o for o in bpy.data.objects if o not in pre and o.type == "MESH"]
    col = bpy.data.collections.new(col_name)
    bpy.context.scene.collection.children.link(col)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    return objs


def place_asset_instance(template_objs: list[bpy.types.Object], name: str,
                         ux: float, uy: float, uz: float, yaw_deg: float, scale: float = 1.0):
    """Instantiate a GLB asset into Blender Town World: (-X_u, -Z_u, Y_u) with rot_z = -yaw_deg."""
    parent = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(parent)
    parent.location = Vector((-ux, -uz, uy))
    parent.rotation_euler = Euler((0.0, 0.0, -math.radians(yaw_deg)), "XYZ")
    parent.scale = Vector((scale, scale, scale))
    for src in template_objs:
        inst = bpy.data.objects.new(f"{name}_{src.name}", src.data)
        inst.matrix_local = src.matrix_world.copy()
        inst.parent = parent
        bpy.context.scene.collection.objects.link(inst)
    return parent


def assemble_and_render():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Load 4x Terrain & Hardscape (both already in Blender Town coords (-X_u, -Z_u, Y_u))
    bpy.ops.import_scene.gltf(filepath=str(TERRAIN_GLB))
    bpy.ops.import_scene.gltf(filepath=str(HARDSCAPE_GLB))
    # Hide collision/audit-only ribbons where full 3D landmark meshes (F32/F35/F37/F38) sit
    for o in bpy.data.objects:
        if any(tag in o.name for tag in ("Ribbon_F32", "Ribbon_F35", "Ribbon_F37", "Ribbon_F38")):
            o.hide_render = True
            o.hide_viewport = True

    # Add wide outer horizon ocean plane strictly for render backdrop framing
    horizon_mat = bpy.data.materials.get("Sea_Deep_Teal") or get_mat("sea_blue")
    bpy.ops.mesh.primitive_plane_add(size=1200.0, location=(0.0, 0.0, -0.065))
    h_obj = bpy.context.object
    h_obj.name = "Horizon_Ocean_RenderOnly"
    h_obj.data.materials.append(horizon_mat)

    # 2. Load & Place all F01-F42 instances from town-building-layout.json
    items = json.loads(LAYOUT_JSON.read_text(encoding="utf-8"))
    template_cache: dict[str, list[bpy.types.Object]] = {}
    hidden_stash = bpy.data.collections.new("_Templates")
    bpy.context.scene.collection.children.link(hidden_stash)
    hidden_stash.hide_render = True
    hidden_stash.hide_viewport = True

    def get_template(rel_path: str) -> list[bpy.types.Object]:
        if rel_path in template_cache:
            return template_cache[rel_path]
        abs_path = ROOT / rel_path
        pre = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(abs_path))
        objs = [o for o in bpy.data.objects if o not in pre and o.type == "MESH"]
        for o in objs:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            hidden_stash.objects.link(o)
        template_cache[rel_path] = objs
        return objs

    for item in items:
        fac = item.get("facility", "")
        iid = item["id"]
        if iid == "model-town-promenade-4x":
            continue  # hardscape already loaded directly at origin
        if fac in ("F35W", "F35E"):
            continue  # built below as exact full-span terrain-fitted chutes
        rel = item["modelPath"]
        tmpl = get_template(rel)
        ux, uy, uz = item["position"]
        # F02 fishing-pier has pilings down to -0.75 in local GLB (see prefab.json pos.y=0.646)
        if fac == "F02":
            uy = 0.646
        scale = float(item.get("prefabScale", 1.0))
        place_asset_instance(tmpl, f"{fac}_{iid}", ux, uy, uz, float(item.get("yaw", 0.0)), scale)

    # 3. Build exact full-span curved trestle slides F35W & F35E matching terrain/audit
    slide_w_u = [
        (-15.5, 5.40, 52.0), (-21.0, 5.05, 47.0), (-26.0, 4.65, 41.5),
        (-26.5, 4.35, 35.0), (-30.0, 4.00, 25.0), (-32.5, 3.65, 12.0), (-34.5, 1.80, 5.5),
    ]
    slide_e_u = [
        (15.5, 5.40, 52.0), (18.5, 5.05, 46.0), (20.5, 4.72, 41.0),
        (27.0, 4.40, 35.5), (32.5, 3.98, 23.0), (36.0, 3.65, 11.5), (37.0, 1.80, 5.5),
    ]
    build_slide_from_pts("F35W_Full", [(-x, -z, y) for x, y, z in slide_w_u])
    build_slide_from_pts("F35E_Full", [(-x, -z, y) for x, y, z in slide_e_u])

    # 4. Scatter Partitioned Trees (E01 Coastal Pines / E02 Golden Maples) & P01-P06 Micro Props
    pine_tmpl = get_template("workspace/assets/models/landmarks-4x/E01-coastal-pine-tree.glb")
    maple_tmpl = get_template("workspace/assets/models/landmarks-4x/E02-autumn-maple-tree.glb")
    lamp_tmpl = get_template("workspace/assets/models/landmarks-4x/P01-clay-street-lamp.glb")
    mbox_tmpl = get_template("workspace/assets/models/landmarks-4x/P02-vintage-mailbox.glb")
    sign_tmpl = get_template("workspace/assets/models/landmarks-4x/P03-wooden-signpost.glb")
    chime_tmpl = get_template("workspace/assets/models/landmarks-4x/P04-shell-windchime-post.glb")
    arm_tmpl = get_template("workspace/assets/models/landmarks-4x/P06-mini-armillary-sphere.glb")

    pine_locs = [
        (-61, 3.6, 26, 25, 0.95), (-60, 1.8, -4, 70, 0.90), (-53, 0.2, -37, 140, 0.85),
        (-25, 0.2, -46, 40, 0.85), (20, 0.2, -49, 110, 0.88), (58, 0.2, -37, 200, 0.90),
        (59, 3.6, 23, 30, 0.92), (-46, 3.6, -10, 15, 0.82),
    ]
    for idx, (ux, uy, uz, yaw, sc) in enumerate(pine_locs):
        place_asset_instance(pine_tmpl, f"E01_Pine_{idx}", ux, uy, uz, yaw, sc)

    maple_locs = [
        (-45, 3.6, 54, 15, 1.05), (-32, 3.6, 56, 85, 0.95), (-22, 3.6, 56, 140, 1.0),
        (22, 3.6, 56, 45, 1.02), (35, 3.6, 54, 110, 1.05), (46, 3.6, 48, 20, 0.95),
        (44, 3.6, 36, 175, 0.92), (-44, 3.6, 32, 60, 0.94),
    ]
    for idx, (ux, uy, uz, yaw, sc) in enumerate(maple_locs):
        place_asset_instance(maple_tmpl, f"E02_Maple_{idx}", ux, uy, uz, yaw, sc)

    micro_placements = [
        (lamp_tmpl, "P01", [(-30, 1.8, 2), (-44, 1.8, -2), (-46, 3.6, -16), (32, 1.8, -3),
                            (50, 1.8, -9), (43, 3.6, 12), (-20, 3.6, 34), (22, 3.6, 35),
                            (-8, 5.4, 52), (8, 5.4, 52), (-10, 1.4, -41), (6, 1.4, -41)]),
        (mbox_tmpl, "P02", [(-36, 1.8, 1.5), (-46, 3.6, 16), (-35, 4.2, 44.5), (38, 1.8, 2.5)]),
        (sign_tmpl, "P03", [(-31, 1.8, -1.5), (-37, 0.2, -27), (31, 1.8, -3.5), (33, 0.2, -30),
                            (-13, 3.6, 29), (17, 3.6, 29), (-18, 0.2, -37)]),
        (chime_tmpl, "P04", [(-40, 0.2, -32), (-52, 3.6, -12), (-10, 1.4, -43), (6, 1.4, -43), (16, 0.2, -39)]),
        (arm_tmpl, "P06", [(-53, 5.4, -22), (-4, 5.4, 54), (4, 5.4, 54)]),
    ]
    for tmpl, code, coords in micro_placements:
        for idx, (ux, uy, uz) in enumerate(coords):
            place_asset_instance(tmpl, f"{code}_{idx}", ux, uy, uz, (idx * 37) % 360, 1.0)

    # Fix packed texture nodes in imported v1 GLBs that fail Blender memory image decode (avoid magenta faces)
    for mat in bpy.data.materials:
        if not mat.node_tree:
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if not bsdf:
            continue
        for link in list(bsdf.inputs["Base Color"].links):
            node = link.from_node
            if node.type == "TEX_IMAGE":
                img = node.image
                if img is None or img.size[0] == 0:
                    mat.node_tree.links.remove(link)
                    if "flag" in mat.name.lower() or "banner" in mat.name.lower():
                        bsdf.inputs["Base Color"].default_value = srgb_to_linear("#7CC6E8")
                    else:
                        bsdf.inputs["Base Color"].default_value = srgb_to_linear("#46455E")

    # 5. Afternoon Clear-Sky Storybook Daylight & High-Res Bird's-Eye Render
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 2200
    scene.render.resolution_y = 1500
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.08

    world = bpy.data.worlds.new("Afternoon_ClearSky")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = srgb_to_linear("#CBEAF7")
    bg.inputs["Strength"].default_value = 0.82

    sun_data = bpy.data.lights.new("Afternoon_Sun", type="SUN")
    sun_data.energy = 2.75
    sun_data.color = srgb_to_linear("#FFF3DE")[:3]
    sun_data.angle = math.radians(10.0)
    sun = bpy.data.objects.new("Afternoon_Sun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = Euler((math.radians(44), math.radians(16), math.radians(34)), "XYZ")

    fill_data = bpy.data.lights.new("Sky_Fill", type="SUN")
    fill_data.energy = 0.80
    fill_data.color = srgb_to_linear("#D6E4FF")[:3]
    fill = bpy.data.objects.new("Sky_Fill", fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.rotation_euler = Euler((math.radians(-48), math.radians(-22), math.radians(195)), "XYZ")

    # 35-deg Panoramic Bird's-Eye Camera from South-West looking North-East across full 136x122 island
    cam_data = bpy.data.cameras.new("Cam_FullAssembly")
    cam_data.type = "PERSP"
    cam_data.lens = 35.0
    cam_data.clip_end = 700.0
    cam = bpy.data.objects.new("Cam_FullAssembly", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam_pos = Vector((36.0, 142.0, 102.0))
    target = Vector((0.0, -3.0, 3.0))
    cam.location = cam_pos
    cam.rotation_euler = (target - cam_pos).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam

    ASSEMBLY_RENDER_OUT.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(ASSEMBLY_RENDER_OUT)
    bpy.ops.render.render(write_still=True)
    print(f"Rendered full assembly: {ASSEMBLY_RENDER_OUT} ({ASSEMBLY_RENDER_OUT.stat().st_size} B)")


if __name__ == "__main__":
    generate_all_landmark_glbs()
    assemble_and_render()
