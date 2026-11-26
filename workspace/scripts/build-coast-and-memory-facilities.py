"""Build the beach discovery strip and the pet-and-memory lookout.

Run Blender in the background with this script and an export directory after --.
"""

import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def material(name, hex_color, roughness=0.83):
    channels = [channel / 255 for channel in bytes.fromhex(hex_color)]
    color = tuple(
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ) + (1.0,)
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


def mesh_object(name, vertices, faces, finishes):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for finish in finishes:
        mesh.materials.append(finish)
    return obj


def ellipsoid(name, center, radii, finish):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    obj.data.materials.append(finish)
    return obj


def tapered_segment(name, start, end, radius_start, radius_end, finish, sides=9):
    first, last = Vector(start), Vector(end)
    delta = last - first
    bpy.ops.mesh.primitive_cone_add(
        vertices=sides,
        radius1=radius_start,
        radius2=radius_end,
        depth=delta.length,
        location=(first + last) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(finish)
    return obj


def scallop(name, x, y, scale, heading, finish, stripe):
    step_count = 14
    cusp = (x, y, 0.018)
    middle = (x + 0.17 * scale * math.cos(heading), y + 0.17 * scale * math.sin(heading), 0.225 * scale)
    vertices = [cusp, middle]
    for index in range(step_count + 1):
        angle = heading + math.radians(63 * (2 * index / step_count - 1))
        radius = (0.59 + 0.047 * (index % 2)) * scale
        vertices.append((x + radius * math.cos(angle), y + radius * math.sin(angle), 0.037 + 0.055 * scale * (index % 2)))
    faces = [(1, 2 + index, 3 + index) for index in range(step_count)]
    faces += [(0, 3 + index, 2 + index) for index in range(step_count)]
    faces += [(0, 2, 1), (0, 1, step_count + 2)]
    obj = mesh_object(name, vertices, faces, (finish, stripe))
    for index in range(0, step_count, 4):
        obj.data.polygons[index].material_index = 1


def bottle(x, y, angle, turquoise, seam, cork):
    start = Vector((x, y, 0.15))
    axis = Vector((math.cos(angle), math.sin(angle), 0.21)).normalized()
    center = lambda distance: start + axis * distance
    for name, a, b, r0, r1, finish in (
        ("Bottle body", 0.0, 0.42, 0.14, 0.14, turquoise),
        ("Bottle shoulder", 0.42, 0.52, 0.14, 0.063, turquoise),
        ("Bottle neck", 0.52, 0.62, 0.063, 0.06, turquoise),
        ("Bottle lip", 0.60, 0.64, 0.074, 0.074, seam),
        ("Bottle stopper", 0.63, 0.68, 0.048, 0.044, cork),
        ("Roll of paper", 0.13, 0.315, 0.055, 0.055, seam),
    ):
        lift = Vector((0, 0, 0.117 if name == "Roll of paper" else 0))
        tapered_segment(name, center(a) + lift, center(b) + lift, r0, r1, finish, 12)


def beach_discovery():
    coral = material("Coral shell", "E3A78D")
    cream = material("Shell stripe", "F7E2BF")
    blush = material("Pink shell", "EAB5B3")
    beige = material("Shell stone", "DDD2B1")
    pale_wood = material("Sunbleached wood", "AE8865")
    dark_wood = material("Weathered grain", "9A775B")
    sea_glass = material("Sea glass green", "6EAFA2", 0.34)
    mint = material("Bottle label", "BDDACE")

    anchors = (
        (-5.1, 1.21, 0.76, 0.47, coral),
        (-4.5, 1.36, 0.72, 2.00, blush),
        (-4.0, 2.05, 0.57, 2.42, cream),
        (-2.0, -1.83, 0.62, -0.68, coral),
        (-1.45, -1.73, 0.50, -1.20, blush),
        (0.75, 1.12, 0.88, -0.30, coral),
        (1.25, 1.30, 0.57, 1.35, cream),
        (3.45, -1.72, 0.71, 0.61, blush),
        (4.38, 1.34, 0.73, 1.27, blush),
        (4.93, 1.23, 1.12, 1.82, coral),
        (5.35, 1.65, 0.49, 3.32, cream),
    )
    for index, (x, y, scale, angle, finish) in enumerate(anchors, 1):
        scallop(f"Scallop shell {index:02d}", x, y, scale, angle, finish, cream)

    for index, (x, y, scale) in enumerate(((-4.94, 2.1, 0.82), (-3.70, 1.27, 0.86), (-1.02, -1.66, 0.70), (2.8, 1.64, 1.0), (5.57, 1.31, 0.79)), 1):
        ellipsoid(f"Beach pebble {index}", (x, y, 0.06 * scale), (0.16 * scale, 0.12 * scale, 0.06 * scale), beige)

    tapered_segment("Driftwood branch", (-2.82, 1.78, 0.13), (-1.13, 1.98, 0.20), 0.13, 0.06, pale_wood, 8)
    tapered_segment("Forked branch", (-2.12, 1.86, 0.18), (-1.82, 2.32, 0.26), 0.074, 0.033, dark_wood, 7)
    bottle(-0.64, 1.12, 0.36, sea_glass, mint, dark_wood)
    bottle(4.25, 1.81, 2.97, sea_glass, mint, dark_wood)

    box("Beach trail sign post", (-5.33, 1.64, 0.38), (0.10, 0.11, 0.76), dark_wood)
    box("Beach trail sign", (-5.33, 1.63, 0.61), (0.65, 0.12, 0.31), pale_wood)
    ellipsoid("Shell emblem on trail sign", (-5.33, 1.556, 0.62), (0.133, 0.018, 0.093), cream)


def footprint(name, polygon, bottom, top, top_finish, edge_finish):
    count = len(polygon)
    vertices = [(x, y, z) for z in (bottom, top) for x, y in polygon]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        after = (index + 1) % count
        faces.append((index, after, after + count, index + count))
    obj = mesh_object(name, vertices, faces, (top_finish, edge_finish))
    for index in range(2, len(faces)):
        obj.data.polygons[index].material_index = 1


def cutout(name, outline, x, y, z, fill, border, size=1.0):
    depth = 0.073
    def panel(title, path, front, thickness, finish):
        count = len(path)
        vertices = [(x + horizontal * size, front + offset, z + vertical * size) for offset in (0, thickness) for horizontal, vertical in path]
        faces = [tuple(range(count)), tuple(reversed(range(count, count * 2)))]
        for index in range(count):
            after = (index + 1) % count
            faces.append((after, index, index + count, after + count))
        return mesh_object(title, vertices, faces, (finish,))
    panel(f"{name} cream outline", outline, y, depth, border)
    inset = [(horizontal * 0.89, 0.88 * (vertical - 0.82) + 0.82) for horizontal, vertical in outline]
    panel(f"{name} painted face", inset, y - 0.009, 0.014, fill)


def memory_corner():
    cream = material("Paper-cut cream outline", "FFF0D7")
    rose = material("Peach pet print", "D99272")
    sage = material("Pear pet print", "A6B66E")
    plum = material("Hand painted ink", "72504E")
    peach = material("Blush print", "EBA6A0")
    timber = material("Pet stand cedar", "AB7A53")
    tile = material("Warm lookout paving", "DCC5A6")
    edge = material("Paving border", "BCA587")
    stone = material("Memory stone lavender slate", "88869C")
    moon = material("Brass memory emblem", "EBBD79")
    moss = material("Moss green", "8C9D67")

    outline = [(-2.84, -1.27), (-2.39, -2.06), (-0.90, -2.53), (1.17, -2.48),
               (2.42, -1.79), (2.93, -0.56), (2.67, 1.21), (1.60, 2.26),
               (-0.08, 2.63), (-1.86, 1.93), (-2.77, 0.66)]
    footprint("Lookout paving", outline, 0, 0.078, tile, edge)

    rock = ellipsoid("Time stone lower base", (1.24, 0.91, 0.22), (0.71, 0.64, 0.17), edge)
    rock.rotation_euler.z = 0.14
    ring = [(-0.55, -0.36, 0.22), (0.52, -0.36, 0.22), (0.63, 0.29, 0.23),
            (-0.44, 0.36, 0.22), (-0.45, -0.34, 1.37), (0.46, -0.31, 1.46),
            (0.36, 0.24, 1.36), (-0.31, 0.29, 1.52)]
    vertices = [(1.24 + x, 0.91 + y, z) for x, y, z in ring]
    mesh_object("Time stone", vertices, ((3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5),
                                        (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)), (stone,))
    tapered_segment("Time stone clock plaque", (1.23, 0.574, 1.01), (1.23, 0.535, 1.01), 0.258, 0.258, moon, 20)
    for name, last in (("Clock hand hour", (1.23, 0.514, 1.15)), ("Clock hand minute", (1.36, 0.514, 0.96))):
        tapered_segment(name, (1.23, 0.514, 1.01), last, 0.014, 0.014, plum, 8)
    for i, (x, y, s) in enumerate(((0.62, 0.66, 0.47), (1.62, 1.63, 0.67), (1.9, 1.06, 0.51)), 1):
        ellipsoid(f"Moss cushion {i}", (x, y, 0.135), (s * 0.32, s * 0.25, 0.076), moss)

    pet_outline = [(-0.52, 0.03), (-0.65, 0.16), (-0.64, 0.43), (-0.45, 0.65),
                   (-0.65, 0.87), (-0.74, 1.18), (-0.67, 1.59), (-0.50, 1.68),
                   (-0.30, 1.41), (0.26, 1.40), (0.45, 1.70), (0.65, 1.60),
                   (0.72, 1.24), (0.62, 0.91), (0.43, 0.70), (0.64, 0.55),
                   (0.84, 0.69), (0.89, 0.53), (0.74, 0.27), (0.52, 0.20),
                   (0.45, 0.02), (0.13, 0), (0.01, 0.10), (-0.12, 0.0)]
    pet_outline.reverse()
    for name, x, y, size, fill in (("Pebblecat", -1.07, 0.74, 1.09, rose), ("Sprout", -0.12, 1.03, 0.63, sage)):
        base_z = 0.17
        box(f"{name} standing base", (x, y + 0.06, 0.132), (1.18 * size, 0.49 * size, 0.11), timber)
        cutout(name, pet_outline, x, y, base_z, fill, cream, size)
        for eye_x in (-0.25, 0.25):
            ellipsoid(f"{name} eye", (x + eye_x * size, y - 0.028, base_z + 1.13 * size), (0.046 * size, 0.019, 0.060 * size), plum)
            ellipsoid(f"{name} cheek", (x + eye_x * 1.55 * size, y - 0.025, base_z + 1.02 * size), (0.087 * size, 0.013, 0.049 * size), peach)
        ellipsoid(f"{name} nose", (x, y - 0.034, base_z + 1.00 * size), (0.057 * size, 0.021, 0.043 * size), plum)
        for spot_x, spot_y in ((-0.19, 0.57), (0.16, 0.45)):
            ellipsoid(f"{name} print mark", (x + spot_x * size, y - 0.021, base_z + spot_y * size), (0.097 * size, 0.013, 0.074 * size), cream)


def main():
    output = Path(sys.argv[sys.argv.index("--") + 1])
    output.mkdir(parents=True, exist_ok=True)
    for filename, build in (("beach-discovery", beach_discovery), ("memory-corner", memory_corner)):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        build()
        bpy.ops.export_scene.gltf(filepath=str(output / f"{filename}.glb"), export_format="GLB", export_yup=True)


if __name__ == "__main__":
    main()

