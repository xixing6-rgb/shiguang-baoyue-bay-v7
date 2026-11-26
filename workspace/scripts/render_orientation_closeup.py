"""Render a 4x4 close-up orientation sheet for smaller/ambiguous props and towers."""
from __future__ import annotations
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
TRIPO_DIR = ROOT / "workspace" / "assets" / "models" / "tripo-optimized"
OUT_PNG = ROOT / "workspace" / "debug" / "model-orientation-closeup.png"

MODELS = [
    "F15-windmill-tower.glb",
    "F22-west-cape-lighthouse.glb",
    "F14-swing-pavilion.glb",
    "F16-sunset-overlook.glb",
    "F05-coffee-terrace.glb",
    "F08-chalkboard.glb",
    "F10-retro-vending.glb",
    "F11-plaza-benches.glb",
    "F02-fishing-pier.glb",
    "F42-postal-bike-stop.glb",
    "P01-clay-street-lamp.glb",
    "P02-vintage-mailbox.glb",
    "P03-wooden-signpost.glb",
    "P04-shell-windchime-post.glb",
    "P05-bakery-food-cart.glb",
    "U01-paper-pet-standee.glb",
]


def make_mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Emission Color"].default_value = rgba
    bsdf.inputs["Emission Strength"].default_value = 0.55
    return m


def unity_to_blender(ux, uy, uz):
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

    cols = 4
    spacing = 6.5

    for idx, fname in enumerate(MODELS):
        glb = TRIPO_DIR / fname
        if not glb.exists():
            continue
        r = idx // cols
        c = idx % cols
        ux = (c - (cols - 1) * 0.5) * spacing
        uz = -r * spacing
        center_b = unity_to_blender(ux, 0.0, uz)

        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(glb))
        new_objs = [o for o in bpy.context.scene.objects if o not in before]
        sc = 1.0
        if "F22" in fname:
            sc = 0.45
        elif "F15" in fname:
            sc = 0.50
        elif "F02" in fname:
            sc = 0.75
        elif fname.startswith(("P01", "P02", "P03", "P04", "U01", "F08", "F11", "F42")):
            sc = 1.5
        for o in new_objs:
            if o.parent is None:
                o.scale = (o.scale.x * sc, o.scale.y * sc, o.scale.z * sc)
                o.location += center_b

        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=2.1, depth=0.04, location=center_b + Vector((0, 0, -0.025)))
        bpy.context.object.data.materials.append(mat_pad)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=center_b + unity_to_blender(1.3, 0.05, 0.0))
        bx = bpy.context.object
        bx.dimensions = (1.3, 0.14, 0.08)
        bx.data.materials.append(mat_red)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=center_b + unity_to_blender(0.0, 0.05, 1.3))
        bz = bpy.context.object
        bz.dimensions = (0.14, 1.3, 0.08)
        bz.data.materials.append(mat_blue)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=center_b + unity_to_blender(0.0, 0.12, -1.7))
        bpy.context.object.data.materials.append(mat_yel)

    cam_data = bpy.data.cameras.new("IsoCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 34.0
    cam_data.clip_end = 500.0
    cam = bpy.data.objects.new("IsoCam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    tgt = unity_to_blender(0.0, 1.0, -9.75)
    eye = unity_to_blender(-24.0, 26.0, -33.75)
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()

    scene.render.filepath = str(OUT_PNG)
    bpy.ops.render.render(write_still=True)
    print(f"[CLOSEUP] Saved {OUT_PNG}")


if __name__ == "__main__":
    main()
