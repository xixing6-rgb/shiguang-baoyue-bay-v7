r"""Render a visual orientation reference sheet for all Wind-Waker GLB models.

Imports each GLB into Blender, marks Unity world axes at yaw=0:
  - RED arrow   : +X_unity (-X_blender)
  - BLUE arrow  : +Z_unity (-Y_blender)
  - YELLOW dot  : -Z_unity (+Y_blender, i.e., facing south when yaw=0)
Renders from Southwest looking Northeast (matching 45-deg axonometric view) so
every model's front face at yaw=0 can be visually verified.

Usage:
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b --factory-startup -P workspace/scripts/render_orientation_sheet.py
"""

from __future__ import annotations

import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
TRIPO_DIR = ROOT / "workspace" / "assets" / "models" / "tripo-optimized"
OUT_PNG = ROOT / "workspace" / "debug" / "model-orientation-sheet.png"

MODELS = [
    "F04-main-cottage.glb",
    "F12-cafe-kiosk.glb",
    "F13a-house-amber.glb",
    "F13b-house-sage.glb",
    "F13c-house-blue.glb",
    "F23-cliff-cottage.glb",
    "F30-studio-cottage.glb",
    "F15-windmill-tower.glb",
    "F22-west-cape-lighthouse.glb",
    "F14-swing-pavilion.glb",
    "F16-sunset-overlook.glb",
    "F05-coffee-terrace.glb",
    "F06-mendel-flowerbed.glb",
    "F07-pixel-flagpole.glb",
    "F08-chalkboard.glb",
    "F09-wish-fountain.glb",
    "F10-retro-vending.glb",
    "F11-plaza-benches.glb",
    "F02-fishing-pier.glb",
    "F03-beach-discovery.glb",
    "F42-postal-bike-stop.glb",
    "P01-clay-street-lamp.glb",
    "P02-vintage-mailbox.glb",
    "P03-wooden-signpost.glb",
    "P04-shell-windchime-post.glb",
    "P05-bakery-food-cart.glb",
    "P06-mini-armillary-sphere.glb",
    "U01-paper-pet-standee.glb",
]


def make_mat(name: str, rgba: tuple[float, float, float, float]):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Emission Color"].default_value = rgba
    bsdf.inputs["Emission Strength"].default_value = 0.55
    return m


def unity_to_blender(ux: float, uy: float, uz: float) -> Vector:
    return Vector((-ux, -uz, uy))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1440

    world = bpy.data.worlds.new("OrientWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.88, 0.92, 0.95, 1.0)
    bg.inputs[1].default_value = 1.1

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
    sun = bpy.context.object
    sun.data.energy = 2.6
    sun.rotation_euler = (math.radians(42), math.radians(15), math.radians(-30))

    mat_red = make_mat("Axis_PosX_Unity", (0.95, 0.15, 0.15, 1.0))
    mat_blue = make_mat("Axis_PosZ_Unity", (0.15, 0.45, 0.95, 1.0))
    mat_yel = make_mat("Axis_NegZ_Unity", (0.95, 0.85, 0.10, 1.0))
    mat_pad = make_mat("Pad_Gray", (0.72, 0.75, 0.78, 1.0))

    cols = 7
    spacing = 9.5

    for idx, fname in enumerate(MODELS):
        glb = TRIPO_DIR / fname
        if not glb.exists():
            print(f"[SKIP] Missing {glb}")
            continue
        r = idx // cols
        c = idx % cols
        # Place in Unity grid so +X goes right and -Z goes down
        ux = (c - (cols - 1) * 0.5) * spacing
        uz = -r * spacing
        center_b = unity_to_blender(ux, 0.0, uz)

        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(glb))
        new_objs = [o for o in bpy.context.scene.objects if o not in before]
        # Scale down tall towers slightly for uniform sheet inspection
        max_dim = 1.0
        for o in new_objs:
            if o.type == "MESH":
                for v in o.bound_box:
                    max_dim = max(max_dim, abs(v[2]) if hasattr(v, "__len__") else 1.0)
        sc = 1.0
        if "F22" in fname:
            sc = 0.55
        elif "F15" in fname:
            sc = 0.65
        for o in new_objs:
            if o.parent is None:
                o.scale = (o.scale.x * sc, o.scale.y * sc, o.scale.z * sc)
                o.location += center_b

        # Base pad
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=2.6, depth=0.05, location=center_b + Vector((0, 0, -0.03)))
        pad = bpy.context.object
        pad.data.materials.append(mat_pad)

        # +X_unity red bar
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=center_b + unity_to_blender(1.6, 0.06, 0.0))
        bx = bpy.context.object
        bx.dimensions = (1.6, 0.18, 0.10)
        bx.data.materials.append(mat_red)

        # +Z_unity blue bar
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=center_b + unity_to_blender(0.0, 0.06, 1.6))
        bz = bpy.context.object
        bz.dimensions = (0.18, 1.6, 0.10)
        bz.data.materials.append(mat_blue)

        # -Z_unity yellow marker (south)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=center_b + unity_to_blender(0.0, 0.14, -2.1))
        ys = bpy.context.object
        ys.data.materials.append(mat_yel)

    cam_data = bpy.data.cameras.new("IsoCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 76.0
    cam_data.clip_end = 500.0
    cam = bpy.data.objects.new("IsoCam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    # Camera looking from Southwest (-X_u, +Y_u, -Z_u) towards center (0, 0, -14.25)
    tgt = unity_to_blender(0.0, 1.2, -14.25)
    eye = unity_to_blender(-32.0, 34.0, -46.25)
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()

    scene.render.filepath = str(OUT_PNG)
    bpy.ops.render.render(write_still=True)
    print(f"[SHEET] Saved {OUT_PNG}")


if __name__ == "__main__":
    main()
