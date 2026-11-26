"""Produce the landmark orchard as a static, original set of three fruit varieties."""

from math import cos, pi, sin, tau
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def surface(name, color, roughness=0.78):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Roughness"].default_value = roughness
    return mat


def finish(obj, name, mat):
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def cone(name, a, b, bottom, top, mat, vertices=9):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=bottom, radius2=top,
                                    depth=(b - a).length, location=(a + b) / 2)
    obj = finish(bpy.context.object, name, mat)
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return obj


def sphere(name, point, scale, mat, small=False):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=8 if small else 12, ring_count=5 if small else 8, location=point
    )
    obj = finish(bpy.context.object, name, mat)
    obj.scale = scale
    for face in obj.data.polygons:
        face.use_smooth = not small
    return obj


def box(name, point, scale, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=point)
    obj = finish(bpy.context.object, name, mat)
    obj.scale = scale
    return obj


def tree(label, x, z, size, bark, leaf, light_leaf, fruit, profile, turn):
    y = -z
    canopy = (x, y, 2.30 * size)
    cone(f"{label} trunk", (x, y, 0), canopy, 0.26 * size, 0.12 * size, bark)
    lobes = (
        (-0.57, -0.24, 2.21, 0.86),
        (0.53, 0.26, 2.32, 0.83),
        (0.0, 0.0, 2.83, 1.03),
    )
    for index, (dx, dy, height, radius) in enumerate(lobes):
        cx = x + dx * size
        cy = y + dy * size
        cz = height * size
        if index < 2:
            cone(f"{label} branch", (x, y, 1.40 * size), (cx, cy, cz), 0.115 * size, 0.055 * size, bark)
        sphere(f"{label} foliage", (cx, cy, cz), (radius * size, radius * 0.92 * size, radius * 0.79 * size),
               leaf if index < 2 else light_leaf)
    for index in range(7):
        angle = turn + index * tau / 7
        radius = (0.82 + (0.15 if index % 3 == 0 else 0.0)) * size
        fx = x + cos(angle) * radius
        fy = y + sin(angle) * radius
        fz = (2.12 + 0.17 * (index % 4)) * size
        sphere(f"{label} fruit", (fx, fy, fz), tuple(s * size for s in profile), fruit, small=True)
        cone(f"{label} stem", (fx, fy, fz + profile[2] * size * 0.7),
             (fx + 0.03 * size, fy, fz + (profile[2] + 0.05) * size), 0.016, 0.011, bark, vertices=6)


def main(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bark = surface("Orchard chestnut", (0.35, 0.18, 0.082))
    leaf = surface("Apple leaf", (0.20, 0.42, 0.17))
    light_leaf = surface("Sunlit orchard green", (0.35, 0.56, 0.24))
    pear_leaf = surface("Pear olive", (0.37, 0.49, 0.16))
    plum_leaf = surface("Plum green", (0.20, 0.39, 0.24))
    red = surface("Coral apple", (0.76, 0.17, 0.11), 0.50)
    gold = surface("Honey pear", (0.84, 0.56, 0.13), 0.56)
    plum = surface("Violet plum", (0.42, 0.22, 0.54), 0.55)
    cream = surface("Orchard sign limewash", (0.88, 0.76, 0.52))
    # Each variety has a distinct row and color. The through path runs south of the tree crowns.
    for variety, px, positions, greens, fruit, shape in (
        ("Apple", -5.0, [(0.0, 0.38, 0.95), (1.06, 3.37, 1.04)], (leaf, light_leaf), red, (0.19, 0.19, 0.18)),
        ("Pear", 0.0, [(0.0, 0.50, 1.00), (0.68, 3.36, 0.90)], (pear_leaf, light_leaf), gold, (0.16, 0.155, 0.235)),
        ("Plum", 4.55, [(0.0, 0.57, 0.93), (1.09, 3.19, 1.02)], (plum_leaf, leaf), plum, (0.17, 0.16, 0.19)),
    ):
        for index, (dx, z, scale) in enumerate(positions):
            tree(variety, px + dx, z, scale, bark, *greens, fruit, shape, index * pi / 6)
    # A low sign is behind the walking route and faces the plaza below.
    for x in (-3.43, -2.57):
        cone("Orchard sign post", (x, 0.80, 0), (x, 0.80, 1.06), 0.075, 0.067, bark, vertices=8)
    box("Orchard sign frame", (-3.0, 0.80, 0.91), (1.13, 0.10, 0.47), bark)
    box("Orchard sign face", (-3.0, 0.856, 0.91), (1.01, 0.02, 0.35), cream)
    for offset, paint in zip((-0.31, 0, 0.31), (red, gold, plum)):
        sphere("Sign fruit emblem", (-3.0 + offset, 0.884, 0.91), (0.085, 0.028, 0.105), paint, small=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_yup=True)


if __name__ == "__main__":
    main(Path(sys.argv[sys.argv.index("--") + 1]))
