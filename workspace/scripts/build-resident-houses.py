"""Build three coastal resident house shells, then export metre-scale GLBs.

Usage:
    blender -b --python build-resident-houses.py -- OUTPUT_DIRECTORY
"""

from pathlib import Path
import sys

import bpy
from mathutils import Vector


def srgb_channel(value):
    normalized = value / 255.0
    if normalized <= 0.04045:
        return normalized / 12.92
    return ((normalized + 0.055) / 1.055) ** 2.4


def material(name, rgb, roughness=0.86):
    color = tuple(srgb_channel(channel) for channel in bytes.fromhex(rgb)) + (1.0,)
    result = bpy.data.materials.new(name)
    result.diffuse_color = color
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    return result


def box(name, center, size, finish):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(finish)
    return obj


def beam(name, start, end, width, depth, finish):
    first = Vector(start)
    last = Vector(end)
    axis = last - first
    obj = box(name, (first + last) / 2.0, (width, depth, axis.length), finish)
    obj.rotation_euler = axis.to_track_quat("Z", "Y").to_euler()


def roof(profile, body_height, rise, roof_finish, edge_finish):
    # Blender front is -Y, which becomes +Z in the exported GLB.
    left, right = -2.44, 2.44
    front, back = -1.60, 2.16
    ridge_x = 0.0 if profile != "saltbox" else -0.58
    ridge_front = front if profile != "hip" else front + 0.88
    ridge_back = back if profile != "hip" else back - 0.88
    eaves = body_height - 0.02
    top = eaves + rise
    vertices = [
        (left, front, eaves), (right, front, eaves),
        (right, back, eaves), (left, back, eaves),
        (ridge_x, ridge_front, top), (ridge_x, ridge_back, top),
    ]
    faces = [(3, 2, 1, 0), (0, 4, 5, 3), (4, 1, 2, 5), (0, 1, 4), (3, 5, 2)]
    mesh = bpy.data.meshes.new("Roof mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    roof_object = bpy.data.objects.new("Hip roof" if profile == "hip" else "Pitched roof", mesh)
    bpy.context.collection.objects.link(roof_object)
    mesh.materials.append(roof_finish)
    mesh.materials.append(edge_finish)
    if profile != "hip":
        for polygon_index in (3, 4):
            mesh.polygons[polygon_index].material_index = 1

    for name, start, end in (
        ("West eaves", 0, 3), ("East eaves", 1, 2),
        ("Front left rake", 0, 4), ("Front right rake", 4, 1),
        ("Back left rake", 3, 5), ("Back right rake", 5, 2),
        ("Ridge cap", 4, 5),
    ):
        beam(name, vertices[start], vertices[end], 0.105, 0.12, edge_finish)
    if profile == "hip":
        beam("Front eaves", vertices[0], vertices[1], 0.105, 0.12, edge_finish)
        beam("Back eaves", vertices[3], vertices[2], 0.105, 0.12, edge_finish)


def street_window(name, x, z, width, finishes):
    frame, glazing, sill = finishes
    front_y = -1.394
    box(f"{name} frame", (x, front_y, z), (width, 0.11, 0.82), frame)
    box(f"{name} glazing", (x, front_y - 0.065, z), (width - 0.16, 0.032, 0.65), glazing)
    box(f"{name} mullion", (x, front_y - 0.085, z), (0.053, 0.036, 0.66), frame)
    box(f"{name} transom", (x, front_y - 0.085, z), (width - 0.14, 0.036, 0.053), frame)
    box(f"{name} sill", (x, front_y - 0.09, z - 0.43), (width + 0.12, 0.19, 0.11), sill)


def build_house(profile, wall_color, roof_color, accent_color, height, rise, door_x):
    cream = material("Ivory woodwork", "F7ECD5")
    cedar = material("Honey timber", "A97654")
    foundation = material("Sandstone plinth", "C5A78A")
    glass = material("Amber glass", "EABC72", 0.4)
    wall = material("Colored plaster", wall_color)
    roof_finish = material("Coastal roof", roof_color)
    accent = material("Painted joinery", accent_color)
    face_y = -1.35

    box("Foundation", (0, 0.30, 0.115), (4.47, 3.53, 0.23), foundation)
    box("House shell", (0, 0.30, (height + 0.21) / 2), (4.30, 3.30, height - 0.21), wall)
    for x in (-2.13, 2.13):
        box("Quoin", (x, face_y - 0.034, (height + 0.23) / 2), (0.15, 0.12, height - 0.23), cream)
    box("Front wall cap", (0, face_y - 0.03, height - 0.045), (4.32, 0.12, 0.13), cream)
    box("Facade base trim", (0, face_y - 0.03, 0.32), (4.30, 0.12, 0.14), cream)
    roof(profile, height, rise, roof_finish, cream if profile == "hip" else cedar)

    box("Entrance porch", (door_x, -1.61, 0.13), (1.57, 0.59, 0.26), cedar)
    box("Low step", (door_x, -2.01, 0.066), (1.36, 0.38, 0.132), foundation)
    box("Entrance casing", (door_x, -1.41, 1.24), (1.06, 0.15, 1.99), cream)
    box("Painted door", (door_x, -1.498, 1.205), (0.86, 0.08, 1.76), accent)
    box("Door glazing", (door_x, -1.547, 1.55), (0.50, 0.032, 0.52), glass)
    box("Door mullion", (door_x, -1.56, 1.55), (0.043, 0.035, 0.50), cream)
    box("Door handle", (door_x + 0.30, -1.56, 1.13), (0.077, 0.053, 0.071), cedar)

    street_window("Left window", -1.24 if door_x >= 0 else -1.43, 1.42, 0.83, (cream, glass, cedar))
    street_window("Right window", 1.24 if door_x <= 0 else 1.43, 1.42, 0.83, (cream, glass, cedar))
    for x in (-2.172, 2.172):
        side = "West" if x < 0 else "East"
        inset_x = x - 0.046 if x < 0 else x + 0.046
        box(f"{side} window frame", (x, 0.38, 1.47), (0.095, 1.03, 0.78), cream)
        box(f"{side} window glazing", (inset_x, 0.38, 1.47), (0.035, 0.86, 0.61), glass)
        box(f"{side} mullion", (inset_x, 0.38, 1.47), (0.055, 0.056, 0.67), cream)

    if profile == "gable":
        box("Brick chimney", (1.28, 0.95, height + 0.93), (0.54, 0.58, 1.53), roof_finish)
        box("Chimney cap", (1.28, 0.95, height + 1.69), (0.66, 0.70, 0.13), foundation)
    elif profile == "saltbox":
        box("Covered entry fascia", (door_x, -1.75, 2.32), (1.54, 0.73, 0.12), roof_finish)
        for x in (door_x - 0.65, door_x + 0.65):
            box("Porch support", (x, -1.98, 1.28), (0.10, 0.10, 2.08), cedar)
    else:
        box("Striped coastal canopy", (door_x, -1.77, 2.31), (1.59, 0.74, 0.12), cream)
        for offset in (-0.59, -0.20, 0.20, 0.59):
            box("Blue canopy stripe", (door_x + offset, -1.77, 2.38), (0.20, 0.74, 0.036), accent)


HOUSES = (
    ("resident-amber", "gable", "F1DDC1", "AE624B", "80574D", 2.73, 1.20, 0.0),
    ("resident-sage", "saltbox", "B7C69B", "65765F", "58795B", 3.10, 1.34, -0.27),
    ("resident-blue", "hip", "EDE5CE", "638A9E", "457D94", 2.83, 0.95, 0.21),
)


def main():
    output = Path(sys.argv[sys.argv.index("--") + 1])
    output.mkdir(parents=True, exist_ok=True)
    for filename, *profile in HOUSES:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        build_house(*profile)
        bpy.ops.export_scene.gltf(
            filepath=str(output / f"{filename}.glb"),
            export_format="GLB",
            export_yup=True,
            export_apply=True,
        )


if __name__ == "__main__":
    main()

