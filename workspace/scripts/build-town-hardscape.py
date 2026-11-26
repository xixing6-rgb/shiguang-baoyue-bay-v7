"""Export the Shiguang coastal, courtyard, and crest walking routes.

blender -b --factory-startup -P build-town-hardscape.py -- path/to/town-hardscape.glb
Route coordinates are town-local Unity meters, with terrain supplying collision.
"""

from pathlib import Path
import math
import sys

import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt


PAVING_LIFT = 0.115


def material(name, color):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1.0)
    value.use_nodes = True
    shader = value.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = value.diffuse_color
    shader.inputs["Roughness"].default_value = 0.91
    return value


def soften_corners(route):
    points = [Vector(point) for point in route]
    curve = [points[0]]
    for previous, point, following in zip(points, points[1:], points[2:]):
        curve.extend((point.lerp(previous, 0.19), point.lerp(following, 0.19)))
    curve.append(points[-1])
    return curve


def path_faces(route, width, surface, border, rank):
    points = soften_corners(route)
    directions = [(b - a).normalized() for a, b in zip(points, points[1:])]
    half_width = width / 2
    edge_width = min(0.14, width * 0.13)
    sections = []
    for index, point in enumerate(points):
        before = directions[max(index - 1, 0)]
        after = directions[min(index, len(directions) - 1)]
        tangent = (before + after).normalized()
        side = Vector((-tangent.y, tangent.x))
        miter = side / max(side.dot(Vector((-after.y, after.x))), 0.72)
        offsets = (half_width, half_width - edge_width, -half_width + edge_width, -half_width)
        sections.append(tuple(point + miter * offset for offset in offsets))

    faces = []
    for start, end in zip(sections, sections[1:]):
        for index, tone in enumerate((border, surface, border)):
            face_rank = rank + 100 if index == 1 else rank
            faces.append(((start[index], start[index + 1], end[index + 1], end[index]), tone, face_rank))
    return faces


def plaza_faces(center, materials):
    radii = (3.10, 3.28, 4.49, 4.66)
    sectors = []
    for segment in range(36):
        angle = math.tau * segment / 36
        radial = Vector((math.cos(angle), math.sin(angle)))
        sectors.append(tuple(Vector(center) + radial * radius for radius in radii))

    cream, limestone, wheat, clay = materials
    faces = []
    for index, start in enumerate(sectors):
        end = sectors[(index + 1) % len(sectors)]
        accent = (cream, limestone, cream, wheat, cream, limestone)[index % 6]
        for strip, tone in enumerate((clay, accent, clay)):
            faces.append(((start[strip], start[strip + 1], end[strip + 1], end[strip]), tone, 250))
    return faces


def build_pavement(name, source, ground_y, materials):
    outlines = []
    source_faces = []
    for outline, _, _ in source:
        start = len(outlines)
        outlines.extend(outline)
        source_faces.append(list(range(start, len(outlines))))

    # Every tier is triangulated once. At a junction each triangle is assigned
    # the highest-priority paving material that covers it, with no stacked faces.
    coordinates, _, triangles, _, _, owners = delaunay_2d_cdt(outlines, [], source_faces, 1, 0.00002)
    vert_count = len(coordinates)
    top_y = ground_y + PAVING_LIFT
    vertices = [(-point.x, -point.y, top_y) for point in coordinates]
    boundary = {}
    faces = []
    tones = []
    for triangle, matches in zip(triangles, owners):
        if not matches:
            continue
        faces.append(tuple(triangle))
        owner = max(matches, key=lambda index: source[index][2])
        tones.append(source[owner][1])
        for a, b in zip(triangle, triangle[1:] + triangle[:1]):
            edge = tuple(sorted((a, b)))
            if edge in boundary:
                del boundary[edge]
            else:
                boundary[edge] = (a, b)

    # Only the merged exterior perimeter receives a shallow vertical fascia.
    vertices.extend((-point.x, -point.y, ground_y - 0.014) for point in coordinates)
    for a, b in boundary.values():
        faces.append((b, a, a + vert_count, b + vert_count))
        tones.append(4)

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for value in materials:
        mesh.materials.append(value)
    for polygon, index in zip(mesh.polygons, tones):
        polygon.material_index = index


def main(output):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    materials = (
        material("Warm limestone", (0.66, 0.55, 0.40)),
        material("Limestone pale inset", (0.79, 0.69, 0.52)),
        material("Wheat sandstone", (0.70, 0.61, 0.45)),
        material("Terracotta edging", (0.47, 0.31, 0.22)),
        material("Sandstone fascia", (0.56, 0.43, 0.31)),
        material("Shore weathered stone", (0.63, 0.51, 0.36)),
        material("Crest muted limestone", (0.64, 0.58, 0.44)),
    )

    coast = (
        ([(-20.2, -18.8), (-17.9, -18.55), (-13.5, -18.65), (-10.2, -19.25),
          (-7.8, -20.2), (-4.5, -20.15), (-1.4, -19.25), (2.8, -18.6),
          (6.4, -18.85), (8.2, -19.59), (11.9, -19.59), (13.0, -19.4)], 1.8, 5, 0, 30),
        ([(-6.0, -19.40), (-6.0, -19.77), (-6.0, -20.36)], 2.18, 2, 0, 35),
        ([(10.0, -18.80), (10.0, -19.17), (10.0, -19.75)], 2.14, 2, 0, 35),
    )

    town = (
        ([(-19.4, 4.0), (-17.2, 2.7), (-12.0, 2.35), (-6.0, 2.5), (0.0, 2.75),
          (6.6, 2.7), (9.3, 1.85), (10.1, 1.15)], 2.35, 0, 3, 40),
        ([(-19.35, -5.8), (-18.7, -3.3), (-19.0, 0.8), (-19.4, 4.0), (-19.7, 7.6),
          (-19.8, 10.7), (-20.8, 11.0)], 1.76, 2, 0, 30),
        ([(-21.7, 4.0), (-20.5, 4.0), (-19.4, 4.0)], 1.32, 1, 0, 16),
        ([(-17.2, 2.7), (-16.2, 4.9), (-16.0, 7.3), (-16.0, 8.60)], 1.45, 2, 0, 25),
        ([(-6.0, -13.98), (-6.0, -13.25), (-7.65, -12.0), (-8.0, -9.6),
          (-8.0, -7.55), (-6.4, -6.55), (-5.5, -4.9), (-4.9, -2.3), (-4.8, 2.45)], 1.6, 2, 3, 30),
        ([(-19.35, -5.8), (-16.7, -6.15), (-13.1, -6.55), (-10.1, -6.52),
          (-8.0, -7.55)], 1.38, 2, 0, 22),
        ([(-10.1, -6.52), (-10.0, -5.27)], 1.47, 1, 0, 20),
        ([(-7.15, -12.37), (-4.6, -12.8), (-0.9, -12.92), (3.65, -12.94),
          (7.45, -12.62), (10.12, -11.9)], 1.56, 5, 0, 26),
        ([(10.0, -13.98), (10.0, -12.65), (10.32, -10.0), (10.85, -8.15),
          (12.12, -6.65), (13.65, -5.14)], 1.9, 2, 3, 31),
        ([(17.7, 1.55), (19.4, 1.8), (20.38, 2.35)], 1.8, 0, 3, 34),
        ([(20.38, 2.35), (21.5, 3.7), (21.55, 6.55), (21.45, 7.59),
          (21.82, 8.1)], 1.62, 2, 0, 27),
        ([(20.38, 2.35), (20.05, 0.6), (19.85, -1.65), (19.9, -3.45),
          (21.10, -4.0)], 1.64, 2, 0, 26),
        ([(21.55, 6.55), (19.65, 7.22), (17.85, 7.21), (16.6, 7.54),
          (16.0, 8.20)], 1.43, 2, 0, 25),
        ([(16.9, -4.35), (18.0, -4.75), (19.88, -3.9)], 1.37, 2, 0, 22),
    )

    crest = (
        ([(-16.0, 14.04), (-16.0, 15.10), (-14.1, 16.10), (-10.75, 16.77),
          (-6.4, 16.10), (-3.75, 15.1), (-1.0, 14.96), (3.2, 15.42), (7.55, 16.03),
          (11.5, 16.39), (15.93, 16.62), (18.45, 16.74), (20.05, 17.03)], 1.62, 6, 0, 30),
        ([(-12.0, 16.55), (-12.0, 17.6)], 1.34, 2, 0, 24),
        ([(-2.0, 15.0), (-2.05, 16.17)], 1.45, 2, 0, 24),
        ([(12.1, 16.42), (12.65, 17.37), (13.35, 17.87)], 1.34, 2, 0, 24),
        ([(16.0, 14.04), (16.0, 15.05), (15.93, 16.62)], 1.58, 2, 0, 24),
    )

    tiers = (
        ("L0 Shore Walk", 0.20, coast),
        ("L1 Town Loop and Wish Square", 1.80, town),
        ("L2 Crest Walk", 3.60, crest),
    )
    for name, elevation, routes in tiers:
        surface = [face for args in routes for face in path_faces(*args)]
        if elevation == 1.80:
            surface.extend(plaza_faces((14.0, -1.0), (1, 0, 2, 3)))
        build_pavement(name, surface, elevation, materials)

    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", export_yup=True,
                             export_apply=True, use_selection=False)


if __name__ == "__main__":
    output_path = Path(sys.argv[-1]) if "--" in sys.argv else Path("town-hardscape.glb")
    main(output_path)
