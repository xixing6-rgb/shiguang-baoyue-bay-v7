"""Build the sea-breeze café and landing dock as separate Y-up GLB assets.

Run with Blender: blender --background --factory-startup --python this_file.py -- output_directory
Local -Y is the public frontage, which becomes +Z in the exported asset.
"""

import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


MATERIALS = {
    "Honey timber": ("C68A53", 0.77),
    "Pale timber": ("E4BA8B", 0.78),
    "Toasted timber": ("8D593E", 0.8),
    "Painted cream": ("FFF5E4", 0.68),
    "Sea-blue canvas": ("7CC6E8", 0.92),
    "Cream canvas": ("FFF2D9", 0.95),
    "Sea glass": ("579BAA", 0.55),
    "Terracotta enamel": ("B96A59", 0.68),
    "Warm amber": ("FFD67A", 0.58),
    "Twine": ("E7CF9E", 0.95),
    "Leaf green": ("93C794", 0.83),
    "Warm slate": ("5A587D", 0.81),
}


def to_linear(component):
    component /= 255.0
    if component <= 0.04045:
        return component / 12.92
    return ((component + 0.055) / 1.055) ** 2.4


def material(name):
    stored = bpy.data.materials.get(name)
    if stored:
        return stored
    srgb, roughness = MATERIALS[name]
    rgb = tuple(to_linear(int(srgb[index:index + 2], 16)) for index in (0, 2, 4))
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*rgb, 1.0)
    result.use_nodes = True
    surface = result.node_tree.nodes.get("Principled BSDF")
    surface.inputs["Base Color"].default_value = result.diffuse_color
    surface.inputs["Roughness"].default_value = roughness
    return result


def finish(obj, name, surface, bevel=0.02):
    obj.name = name
    obj.data.materials.append(material(surface))
    if bevel:
        modifier = obj.modifiers.new("Soft edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def box(name, position, size, surface, bevel=0.02, tilt=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.rotation_euler.x = tilt
    return finish(obj, name, surface, bevel)


def beam(name, start, end, thickness, surface):
    start, end = Vector(start), Vector(end)
    direction = end - start
    obj = box(name, (start + end) * 0.5, (thickness, thickness, direction.length), surface)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def round_piece(name, position, lower_radius, upper_radius, height, surface, sides=10):
    bpy.ops.mesh.primitive_cone_add(
        vertices=sides, radius1=lower_radius, radius2=upper_radius, depth=height, location=position
    )
    return finish(bpy.context.object, name, surface, 0.012)


def lantern(x, y, base):
    box("Lantern foot", (x, y, base + 0.035), (0.30, 0.28, 0.07), "Toasted timber")
    box("Amber lantern", (x, y, base + 0.20), (0.20, 0.19, 0.28), "Warm amber", 0.025)
    for dx in (-0.104, 0.104):
        for dy in (-0.10, 0.10):
            box("Lantern frame", (x + dx, y + dy, base + 0.19), (0.028, 0.028, 0.30), "Toasted timber", 0.005)
    box("Lantern cap", (x, y, base + 0.36), (0.30, 0.28, 0.075), "Toasted timber")


def make_cafe():
    box("Counter platform", (0, 0.22, 0.10), (4.12, 2.84, 0.20), "Honey timber", 0.038)
    for index in range(12):
        box("Platform plank", (0, -1.06 + index * 0.224, 0.209), (4.02, 0.215, 0.032), "Pale timber", 0.006)
    for x in (-1.88, 1.88):
        for y in (-0.92, 1.34):
            box("Chamfered oak upright", (x, y, 1.46), (0.24, 0.24, 2.58), "Honey timber", 0.035)
    box("Rear counter wall", (0, 1.39, 0.70), (3.82, 0.16, 0.98), "Painted cream")
    for x in (-1.88, 1.88):
        box("Side counter wall", (x, 0.28, 0.70), (0.17, 2.14, 0.98), "Painted cream")
        beam("Eave brace", (x, -0.91, 2.16), (x, -0.44, 2.67), 0.12, "Pale timber")
    box("Front panel", (-0.36, -0.88, 0.72), (3.01, 0.16, 1.03), "Honey timber")
    for index in range(11):
        x = -1.70 + index * 0.27
        surface = "Pale timber" if index % 3 == 0 else "Honey timber"
        box("Front counter slat", (x, -0.977, 0.70), (0.248, 0.065, 0.93), surface, 0.012)
    box("Service counter", (-0.35, -0.92, 1.25), (3.20, 0.65, 0.14), "Pale timber", 0.038)
    box("Rear shelf", (0.47, 1.20, 1.39), (2.56, 0.36, 0.095), "Pale timber")
    box("Café name board", (0, -1.075, 2.73), (1.26, 0.12, 0.31), "Sea glass", 0.04)
    box("Board trim", (0, -1.078, 2.88), (1.34, 0.15, 0.065), "Pale timber")
    box("Cup logo", (-0.04, -1.143, 2.73), (0.32, 0.022, 0.145), "Painted cream", 0.024)
    box("Cup logo handle", (0.163, -1.143, 2.75), (0.10, 0.025, 0.06), "Painted cream", 0.012)

    ridge, eave, rise = 0.26, 1.93, 0.68
    for index in range(8):
        x = -2.05 + index * 0.585
        surface = "Sea-blue canvas" if index % 2 == 0 else "Cream canvas"
        for sign in (-1, 1):
            run = eave + sign * -ridge
            center = ridge + sign * run / 2
            box("Striped canvas roof", (x, center, 3.14), (0.587, math.hypot(run, rise), 0.105),
                surface, 0.016, -sign * math.atan2(rise, run))
            box("Awning curtain", (x, sign * eave, 2.69), (0.58, 0.105, 0.255), surface, 0.042)

    for x, surface in ((-1.25, "Sea glass"), (-0.73, "Terracotta enamel")):
        round_piece("Coffee cup", (x, -1.02, 1.40), 0.070, 0.096, 0.17, surface)
        round_piece("Cream lid", (x, -1.02, 1.491), 0.102, 0.096, 0.026, "Painted cream")
    for x in (-2.18, 2.16):
        round_piece("Terracotta herb pot", (x, -1.45, 0.16), 0.16, 0.21, 0.32, "Terracotta enamel")
        round_piece("Herb leaves", (x, -1.45, 0.385), 0.24, 0.075, 0.29, "Leaf green")


def make_dock():
    for index in range(20):
        x = -2.755 + 0.29 * index
        length = 3.46 if index <= 2 or index >= 17 else 3.70
        surface = ("Pale timber", "Honey timber", "Pale timber")[index % 3]
        box("Deck boards", (x, 0.38, 0.20), (0.278, length, 0.11), surface, 0.014)
    for x in (-2.53, 0, 2.53):
        box("Deck support", (x, 0.42, 0.10), (0.26, 3.78, 0.20), "Toasted timber", 0.025)
    for row in range(6):
        y = -1.54 - row * 0.171
        height = 0.247 - row * 0.038
        box("Landing ramp riser", (0, y, height / 2), (3.12, 0.174, height), "Honey timber", 0.012)
    for x in (-2.62, 2.62):
        for y in (-0.98, 0.38, 1.81):
            round_piece("Timber piling", (x, y, 0.43), 0.19, 0.17, 0.86, "Honey timber")
            round_piece("Piling cap", (x, y, 0.853), 0.206, 0.195, 0.10, "Pale timber")
        for start, end in ((-0.98, 0.38), (0.38, 1.81)):
            points = ((x, start, 0.63), (x, (start + end) / 2, 0.52), (x, end, 0.63))
            for index in range(2):
                beam("Rope rail", points[index], points[index + 1], 0.035, "Twine")
        box("Gate post", (x, 0.02, 1.50), (0.28, 0.30, 3.00), "Honey timber", 0.037)
        beam("Gate brace", (x, 0.02, 2.30), (x * 0.76, 0.02, 2.83), 0.18, "Pale timber")
        box("Lantern shelf", (x * 0.87, 0.02, 1.86), (0.79, 0.25, 0.12), "Honey timber")
        lantern(x * 0.79, 0.02, 1.92)
    box("Arrival gate beam", (0, 0.02, 2.93), (5.86, 0.36, 0.39), "Honey timber", 0.042)
    box("Gate sign", (0, -0.17, 2.76), (1.44, 0.12, 0.40), "Sea glass", 0.045)
    box("Gate sign trim", (0, -0.177, 2.96), (1.53, 0.15, 0.081), "Pale timber")
    for x in (-0.31, 0.05, 0.41):
        box("Wave sign inlay", (x, -0.239, 2.76), (0.28, 0.021, 0.052), "Painted cream", 0.012,
            math.radians(12))
    for x in (-1.52, 1.52):
        box("Dock cleat base", (x, 1.78, 0.28), (0.16, 0.10, 0.07), "Warm slate")
        box("Dock cleat", (x, 1.78, 0.33), (0.35, 0.09, 0.055), "Warm slate")


def export_model(name, build_model, output_dir):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    build_model()
    material_groups = {}
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            material_groups.setdefault(obj.data.materials[0].name, []).append(obj)
    for surface, members in material_groups.items():
        bpy.ops.object.select_all(action="DESELECT")
        for member in members:
            member.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        if len(members) > 1:
            bpy.ops.object.join()
        bpy.context.object.name = surface
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.export_scene.gltf(filepath=str(output_dir / name), export_format="GLB", export_yup=True,
                              export_cameras=False, export_lights=False)


if __name__ == "__main__":
    if "--" not in sys.argv:
        raise SystemExit("Pass the GLB output directory after Blender's -- separator.")
    output = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    export_model("cafe-kiosk.glb", make_cafe, output)
    export_model("arrival-dock.glb", make_dock, output)
