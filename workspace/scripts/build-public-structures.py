"""Build the neighborhood pavilion and hilltop overlook for Shiguang Town."""

from mathutils import Vector
from pathlib import Path
import sys

import bpy


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = 0.86
    return mat


def box(name, center, dimensions, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def beam(name, start, end, width, depth, mat):
    a, b = Vector(start), Vector(end)
    obj = box(name, (a + b) / 2, (width, depth, (b - a).length), mat)
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return obj


def footing(x, y, stone, timber, height):
    box("Stone footing", (x, y, 0.12), (0.37, 0.37, 0.24), stone)
    box("Timber post", (x, y, height / 2 + 0.15), (0.19, 0.19, height), timber)


def deck(width, depth, timber, trim, front_y):
    board_count = round(width / 0.20)
    pitch = width / board_count
    for index in range(board_count):
        x = (index + 0.5) * pitch - width / 2
        box("Deck plank", (x, 0, 0.12), (pitch - 0.006, depth, 0.18), timber)
    box("Entry tread", (0, front_y, 0.045), (1.65, 0.45, 0.09), trim)


def swing_pavilion():
    oak = material("Warm chestnut", (0.39, 0.19, 0.075))
    planks = material("Honey deck", (0.62, 0.36, 0.16))
    stone = material("Sandstone piers", (0.52, 0.45, 0.34))
    sage = material("Sage canvas", (0.34, 0.49, 0.36))
    linen = material("Ivory canvas", (0.89, 0.77, 0.57))
    deck(4.65, 3.85, planks, oak, -2.10)
    for x in (-2.10, 2.10):
        for y in (-1.48, 1.48):
            footing(x, y, stone, oak, 2.63)
            beam("Corner knee brace", (x, y, 2.12), (x * 0.80, y, 2.68), 0.12, 0.12, oak)
        box("Eave crossbar", (x, 0, 2.79), (0.20, 3.44, 0.16), oak)
    box("Back lintel", (0, 1.48, 2.76), (4.46, 0.22, 0.18), oak)
    box("Swing beam", (0, 0.38, 2.73), (4.45, 0.20, 0.22), oak)
    for index in range(9):
        x = (index - 4) * 0.55
        beam("Canopy rafter", (x, -1.76, 2.87), (x, 1.76, 3.02), 0.095, 0.10, oak)
    for index in range(7):
        x = (index - 3) * 0.37
        beam("Striped canopy", (x, -1.73, 2.94), (x, 1.69, 3.085), 0.374, 0.035, sage if index % 2 == 0 else linen)
        box("Canvas valance", (x, -1.74, 2.88), (0.372, 0.035, 0.16), sage if index % 2 == 0 else linen)
    for x in (-0.66, 0.66):
        beam("Swing rope", (x, 0.38, 2.65), (x, 0.22, 0.70), 0.034, 0.034, linen)
    box("Swing seat", (0, 0.21, 0.70), (1.45, 0.41, 0.095), oak)


def sunset_overlook():
    oak = material("Salt-aged timber", (0.30, 0.18, 0.096))
    planks = material("Bleached oak deck", (0.63, 0.44, 0.25))
    stone = material("Sandstone piers", (0.53, 0.46, 0.33))
    blue = material("Sea blue trim", (0.20, 0.40, 0.46))
    roof = material("Tea green shingles", (0.28, 0.37, 0.29))
    deck(4.85, 3.35, planks, oak, -1.85)
    for x in (-2.19, 2.19):
        for y in (-1.35, 1.24):
            footing(x, y, stone, oak, 2.53)
        box("Side guardrail", (x, 0.25, 1.03), (0.12, 2.10, 0.13), blue)
        box("Eave crossbar", (x, 0, 2.68), (0.22, 3.24, 0.19), oak)
        for y in (-0.64, 0.08, 0.80):
            box("Guardrail spindle", (x, y, 0.63), (0.075, 0.075, 0.82), oak)
    box("Bench seat", (0, 1.04, 0.68), (3.3, 0.52, 0.12), planks)
    box("Bench back", (0, 1.35, 0.99), (3.3, 0.09, 0.43), blue)
    for x in (-1.35, 1.35):
        box("Bench leg", (x, 1.02, 0.43), (0.15, 0.43, 0.44), oak)
    for i in range(10):
        x = (i - 4.5) * 0.52
        for outer_y in (-1.76, 1.76):
            beam("Roof panel", (x, outer_y, 2.79), (x, 0, 3.45), 0.523, 0.13, roof)
    box("Ridge cap", (0, 0, 3.46), (5.28, 0.20, 0.17), blue)
    box("Viewer base", (1.14, -0.90, 0.29), (0.41, 0.36, 0.17), stone)
    box("Viewer stand", (1.14, -0.90, 0.80), (0.13, 0.14, 1.00), oak)
    beam("Telescope", (1.14, -0.66, 1.28), (1.14, -1.27, 1.42), 0.25, 0.23, blue)


if __name__ == "__main__":
    output = Path(sys.argv[sys.argv.index("--") + 1])
    output.mkdir(parents=True, exist_ok=True)
    for name, build in (("community-pavilion", swing_pavilion), ("sunset-overlook", sunset_overlook)):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        build()
        bpy.ops.export_scene.gltf(filepath=str(output / (name + ".glb")), export_format="GLB")

