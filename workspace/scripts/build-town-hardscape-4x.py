"""Export the 4x Shiguang Town single-layer hardscape road network & audit route continuity.

Inherits the zero-z-fighting single-layer delaunay_2d_cdt paving method from
build-town-hardscape.py, preserves Zone 0 inner town loop verbatim, expands into
the 385m Crescent Coastal-Mountain Outer Loop + 4 Secondary District Loops +
bridges/ramps/stepping-stones/slides, and verifies >= 12 routes via BVH raycasts
against map-shiguang-town-4x.glb + bridge decks.

Outputs:
  - workspace/assets/models/town-hardscape-4x.glb
  - workspace/debug/route-audit-4x.json

Usage:
  blender -b --factory-startup --python-exit-code 1 -P workspace/scripts/build-town-hardscape-4x.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt


ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
TERRAIN_GLB = ROOT / "workspace" / "assets" / "models" / "map-shiguang-town-4x.glb"
HARDSCAPE_OUT = ROOT / "workspace" / "assets" / "models" / "town-hardscape-4x.glb"
AUDIT_OUT = ROOT / "workspace" / "debug" / "route-audit-4x.json"

PAVING_LIFT = 0.115
SLOPE_PAVING_LIFT = 0.002


def material(name: str, color: tuple[float, float, float], roughness: float = 0.91):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1.0)
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = value.diffuse_color
    bsdf.inputs["Roughness"].default_value = roughness
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


def plaza_faces(center, materials, radii=(3.10, 3.28, 4.49, 4.66), rank=250):
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
            faces.append(((start[strip], start[strip + 1], end[strip + 1], end[strip]), tone, rank))
    return faces


def build_pavement(name, source, ground_y, materials):
    outlines = []
    source_faces = []
    for outline, _, _ in source:
        start = len(outlines)
        outlines.extend(outline)
        source_faces.append(list(range(start, len(outlines))))

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
    return obj


def build_sloped_ribbon(name: str, pts_3d: list[tuple[float, float, float]], width: float,
                        surface_idx: int, border_idx: int, materials, lift: float = SLOPE_PAVING_LIFT):
    """Build a continuous single-layer 3D paved ribbon along graded ramps, bridges, and slides."""
    hw = width * 0.5
    ew = min(0.14, width * 0.13)
    offsets = (hw, hw - ew, -hw + ew, -hw)

    verts = []
    faces = []
    tones = []

    n = len(pts_3d)
    sections_top = []
    sections_bot = []
    for i, (ux, uy, uz) in enumerate(pts_3d):
        p_prev = Vector((pts_3d[max(i - 1, 0)][0], pts_3d[max(i - 1, 0)][2]))
        p_next = Vector((pts_3d[min(i + 1, n - 1)][0], pts_3d[min(i + 1, n - 1)][2]))
        d = (p_next - p_prev)
        if d.length < 1e-6:
            d = Vector((1.0, 0.0))
        d.normalize()
        side = Vector((-d.y, d.x))
        row_t = []
        row_b = []
        for off in offsets:
            cx = ux + side.x * off
            cz = uz + side.y * off
            idx_t = len(verts)
            verts.append((-cx, -cz, uy + lift))
            idx_b = len(verts)
            verts.append((-cx, -cz, uy - 0.04))
            row_t.append(idx_t)
            row_b.append(idx_b)
        sections_top.append(row_t)
        sections_bot.append(row_b)

    for i in range(n - 1):
        a, b = sections_top[i], sections_top[i + 1]
        ab, bb = sections_bot[i], sections_bot[i + 1]
        for j, tone in enumerate((border_idx, surface_idx, border_idx)):
            faces.append((a[j + 1], a[j], b[j], b[j + 1]))
            tones.append(tone)
        # Side fascias
        faces.append((a[0], ab[0], bb[0], b[0]))
        tones.append(4)
        faces.append((ab[3], a[3], b[3], bb[3]))
        tones.append(4)

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for m in materials:
        mesh.materials.append(m)
    for poly, idx in zip(mesh.polygons, tones):
        poly.material_index = idx
    return obj


def sample_arch_pts(p0_xz: tuple[float, float], p1_xz: tuple[float, float], y_base: float,
                    rise: float, steps: int = 16) -> list[tuple[float, float, float]]:
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 2.0 * t - 1.0
        x = p0_xz[0] + (p1_xz[0] - p0_xz[0]) * t
        z = p0_xz[1] + (p1_xz[1] - p0_xz[1]) * t
        y = y_base + rise * (1.0 - u * u)
        pts.append((x, y, z))
    return pts


def sample_ramp_pts(p0: tuple[float, float, float], p1: tuple[float, float, float], steps: int = 8):
    return [
        (
            p0[0] + (p1[0] - p0[0]) * (i / steps),
            p0[1] + (p1[1] - p0[1]) * (i / steps),
            p0[2] + (p1[2] - p0[2]) * (i / steps),
        )
        for i in range(steps + 1)
    ]


def build_hardscape():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = (
        material("Warm limestone", (0.66, 0.55, 0.40)),       # 0
        material("Limestone pale inset", (0.79, 0.69, 0.52)), # 1
        material("Wheat sandstone", (0.70, 0.61, 0.45)),      # 2
        material("Terracotta edging", (0.47, 0.31, 0.22)),    # 3
        material("Sandstone fascia", (0.56, 0.43, 0.31)),     # 4
        material("Shore weathered stone", (0.63, 0.51, 0.36)),# 5
        material("Crest muted limestone", (0.64, 0.58, 0.44)),# 6
        material("Honey bridge plank", (0.72, 0.48, 0.26)),   # 7
        material("Basalt stepping pad", (0.44, 0.43, 0.45)),  # 8
    )

    # === 1. L0 Shore Walk (Zone 0 + Zone W + Zone E + Zone S) ===
    coast = (
        # Zone 0 exact v1 coast paths
        ([(-20.2, -18.8), (-17.9, -18.55), (-13.5, -18.65), (-10.2, -19.25),
          (-7.8, -20.2), (-4.5, -20.15), (-1.4, -19.25), (2.8, -18.6),
          (6.4, -18.85), (8.2, -19.59), (11.9, -19.59), (13.0, -19.4)], 1.8, 5, 0, 30),
        ([(-6.0, -19.40), (-6.0, -19.77), (-6.0, -20.36)], 2.18, 2, 0, 35),
        ([(10.0, -18.80), (10.0, -19.17), (10.0, -19.75)], 2.14, 2, 0, 35),
        # Zone W L0 extension: F03 west -> W-Ramp-A toe -> F24 campfire -> F37 West Arch Bridgehead
        ([(-20.2, -18.8), (-28.0, -21.0), (-34.0, -24.0), (-35.5, -24.5)], 1.9, 5, 0, 30),
        ([(-35.5, -24.5), (-37.5, -28.0), (-41.5, -30.5), (-39.0, -32.8), (-36.0, -33.5)], 2.0, 5, 0, 32),
        # Zone E L0 extension: F02 east -> E-Ramp-D toe -> Tidepool N entry -> Quay L0 toe -> Lightship -> F38 East Stepping Stones
        ([(13.0, -19.4), (24.0, -18.2), (33.0, -17.3), (36.0, -17.0)], 1.9, 5, 0, 30),
        ([(36.0, -17.0), (36.0, -21.6)], 2.0, 5, 0, 32),
        ([(36.0, -17.0), (41.0, -19.5), (43.0, -21.5)], 2.0, 5, 0, 32),
        ([(43.0, -21.5), (43.0, -25.0), (46.5, -26.5), (49.5, -30.5), (43.0, -32.5), (34.5, -33.0), (30.5, -33.5)], 2.1, 5, 0, 33),
        ([(41.8, -26.0), (43.0, -26.0), (46.5, -26.5)], 1.8, 5, 0, 30),
        # Zone S Islet perimeter L0 loop
        ([(-20.0, -36.5), (-12.5, -36.0), (-5.0, -35.8), (5.0, -36.5), (13.5, -38.5)], 2.2, 5, 0, 36),
        ([(13.5, -38.5), (17.0, -41.5), (16.5, -44.5), (14.0, -47.0), (10.0, -47.0)], 2.0, 5, 0, 34),
        ([(10.0, -47.0), (9.5, -51.0), (2.0, -51.0), (-8.0, -51.0), (-15.5, -48.5), (-16.5, -44.5), (-19.5, -40.5), (-20.0, -36.5)], 2.0, 5, 0, 34),
    )

    # === 2. L-0.5 East Tidepool Basin Pad (-0.15) ===
    tidepool_pad = (
        ([(36.0, -24.6), (36.0, -26.0), (38.8, -26.0)], 1.8, 8, 0, 20),
    )

    # === 3. L0.5 Boatyard Quay (1.00) ===
    quay_pad = (
        ([(46.0, -21.5), (49.0, -19.0), (49.0, -14.0)], 2.2, 7, 3, 30),
        ([(49.0, -19.0), (52.5, -18.5)], 2.0, 7, 0, 28),
    )

    # === 4. S-L1 South Islet Echo Amphitheater (1.40) ===
    south_l1 = (
        ([(-5.0, -40.5), (-2.0, -42.5), (6.5, -44.5)], 2.2, 0, 3, 35),
        ([(-11.5, -44.5), (-6.0, -44.5), (-2.0, -42.5)], 2.2, 0, 3, 35),
    )

    # === 5. L1 Town Loop + West & East Wings (1.80) ===
    town = (
        # Zone 0 exact v1 paths
        ([(-19.4, 4.0), (-17.2, 2.7), (-12.0, 2.35), (-6.0, 2.5), (0.0, 2.75),
          (6.6, 2.7), (9.3, 1.85), (10.1, 1.15)], 2.35, 0, 3, 40),
        ([(-19.35, -5.8), (-18.7, -3.3), (-19.0, 0.8), (-19.4, 4.0), (-19.7, 7.6),
          (-19.8, 10.7), (-20.8, 11.0)], 1.76, 2, 0, 30),
        ([(-21.7, 4.0), (-20.5, 4.0), (-19.4, 4.0)], 1.32, 1, 0, 16),
        ([(-17.2, 2.7), (-16.2, 4.9), (-16.0, 7.3), (-16.0, 8.40)], 1.45, 2, 0, 25),
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
        # Zone 0 F42a Bike stop spur
        ([(6.0, 2.7), (6.0, 4.0)], 1.5, 1, 0, 25),
        # Zone W L1 network (between F13a Z>=1.8 and F14 Z<=-3.8)
        ([(-19.0, -1.0), (-26.5, -1.0), (-34.0, -2.5), (-35.5, -3.5)], 2.3, 0, 3, 42),
        ([(-35.5, -3.5), (-40.0, -0.5), (-44.0, 0.0)], 2.1, 0, 3, 42),
        ([(-35.5, -3.5), (-38.0, -6.5), (-38.0, -11.5), (-38.5, -14.0)], 2.0, 2, 3, 38),
        ([(-38.0, -11.5), (-35.5, -15.5), (-35.5, -19.0)], 2.0, 2, 3, 38),
        ([(-35.5, -3.5), (-35.5, 5.5)], 2.0, 2, 3, 36),
        ([(-44.0, 0.0), (-50.5, 0.0), (-53.5, 2.5), (-53.5, 5.5)], 1.9, 2, 0, 34),
        ([(-35.5, 5.5), (-34.5, 7.5)], 2.0, 1, 0, 30),  # F35W slide landing pad
        # Zone E L1 network
        ([(21.1, -4.0), (29.0, -4.0), (36.5, -4.0), (40.0, -1.0)], 2.3, 0, 3, 42),
        ([(40.0, -1.0), (40.0, 5.5)], 2.1, 0, 3, 40),
        ([(40.0, 5.5), (37.0, 8.0)], 2.0, 1, 0, 30),  # F35E slide landing pad
        ([(40.0, 5.0), (48.0, 4.5), (53.5, 4.0)], 1.8, 2, 0, 34),
        ([(44.0, -4.0), (48.5, -6.5), (49.0, -11.0)], 2.0, 2, 3, 38),
        ([(40.5, -7.5), (36.5, -9.0), (36.0, -11.0)], 2.0, 2, 3, 38),
    )

    # === 6. L2 Crest + West/East/North Highlands (3.60) ===
    crest = (
        # Zone 0 exact v1 crest
        ([(-16.0, 14.00), (-16.0, 15.10), (-14.1, 16.10), (-10.75, 16.77),
          (-6.4, 16.10), (-3.75, 15.1), (-1.0, 14.96), (3.2, 15.42), (7.55, 16.03),
          (11.5, 16.39), (15.93, 16.62), (18.45, 16.74), (20.05, 17.03)], 1.62, 6, 0, 30),
        ([(-12.0, 16.55), (-12.0, 17.6)], 1.34, 2, 0, 24),
        ([(-2.0, 15.0), (-2.05, 16.17)], 1.45, 2, 0, 24),
        ([(12.1, 16.42), (12.65, 17.37), (13.35, 17.87)], 1.34, 2, 0, 24),
        ([(16.0, 14.00), (16.0, 15.05), (15.93, 16.62)], 1.58, 2, 0, 24),
        # Zone W South L2 (F21 & Lighthouse Approach with apron at -43.5,-24.0)
        ([(-44.5, -14.0), (-49.5, -14.0), (-46.5, -19.0), (-46.5, -21.2), (-43.5, -21.2), (-43.5, -24.0), (-44.5, -24.0)], 2.1, 6, 3, 38),
        # Zone W NW L2 (F23a/b & link to Zone 0 / Zone N)
        ([(-16.0, 16.77), (-25.0, 16.5), (-35.5, 16.5), (-35.5, 12.0)], 1.9, 6, 0, 34),
        ([(-35.5, 16.5), (-48.0, 16.5), (-53.5, 15.0), (-53.5, 12.0)], 1.85, 6, 0, 34),
        ([(-53.5, 15.0), (-56.5, 13.0)], 1.6, 2, 0, 28),
        ([(-35.5, 16.5), (-34.0, 26.0), (-28.0, 31.0), (-12.0, 31.5)], 1.9, 6, 0, 36),
        # Zone E L2 (F29 Camellia Terrace & F30a Studio & link to Zone 0 / Zone N)
        ([(20.05, 17.03), (32.0, 17.0), (40.0, 14.5), (40.0, 11.5)], 1.9, 6, 0, 34),
        ([(40.0, 14.5), (45.0, 14.5), (48.0, 14.0)], 1.8, 2, 0, 32),
        ([(40.0, 14.5), (41.5, 20.5), (34.0, 27.0), (24.0, 31.0), (18.0, 32.1)], 1.9, 6, 0, 36),
        # Zone N South Creek Bank
        ([(-12.0, 17.6), (-12.0, 26.0), (-12.0, 31.8)], 1.9, 6, 3, 36),
        ([(16.0, 16.62), (18.0, 25.0), (18.0, 32.1)], 1.9, 6, 3, 36),
        ([(-12.0, 31.4), (3.0, 31.0), (18.0, 31.4)], 1.8, 6, 0, 32),
        # Zone N North Creek Bank (F31 Library, F33 Watermill, F36 Knoll approach, N-Ramp-W/E toes)
        ([(-12.0, 37.2), (-16.0, 37.8), (-23.0, 38.5), (-23.5, 44.0), (-27.2, 44.0)], 1.9, 6, 3, 36),
        ([(-23.5, 44.0), (-19.0, 49.0), (-17.0, 54.5)], 2.0, 6, 3, 38),
        ([(18.0, 37.5), (25.0, 38.5), (21.0, 46.5), (17.0, 54.5)], 2.0, 6, 3, 38),
        ([(-19.0, 49.0), (0.0, 48.5), (21.0, 46.5)], 1.9, 6, 0, 34),
    )

    # === 7. L2.5 Knoll (4.20) & L3 Dual Summits (5.40) ===
    knoll_l25 = (
        ([(-30.87, 44.0), (-34.5, 45.2)], 1.8, 2, 0, 30),
    )
    summit_l3 = (
        ([(-51.0, -24.0), (-53.5, -24.0)], 2.4, 1, 3, 40),
        ([(-10.0, 54.5), (-5.5, 52.2), (0.0, 52.0), (5.5, 52.2), (10.0, 54.5)], 2.3, 1, 3, 42),
        ([(-10.0, 54.5), (-15.5, 52.0)], 1.8, 2, 0, 35),
        ([(10.0, 54.5), (15.5, 52.0)], 1.8, 2, 0, 35),
    )

    tiers = (
        ("L-0.5 Tidepool Path", -0.15, tidepool_pad),
        ("L0 Crescent Shore Walk", 0.20, coast),
        ("L0.5 Boatyard Quay Walk", 1.00, quay_pad),
        ("S-L1 Islet Echo Terrace", 1.40, south_l1),
        ("L1 Town Loop and Wings", 1.80, town),
        ("L2 Highlands and Creek Banks", 3.60, crest),
        ("L2.5 Tree Hollow Knoll Walk", 4.20, knoll_l25),
        ("L3 Dual Scenic Summits", 5.40, summit_l3),
    )
    for name, elevation, routes in tiers:
        surface = [face for args in routes for face in path_faces(*args)]
        if elevation == 1.80:
            surface.extend(plaza_faces((14.0, -1.0), (1, 0, 2, 3)))
            surface.extend(plaza_faces((44.0, -4.0), (1, 0, 2, 3), radii=(3.6, 3.8, 5.1, 5.35), rank=240))
        build_pavement(name, surface, elevation, materials)

    # === 8. Continuous Sloped Ribbons on Ramps, Bridges, Stepping Stones & Slides ===
    sloped_ribbons = [
        ("Ribbon_R01_Zone0_SW", sample_ramp_pts((-6.0, 0.20, -19.40), (-6.0, 1.80, -14.00)), 2.18, 7, 3),
        ("Ribbon_R02_Zone0_SE", sample_ramp_pts((10.0, 0.20, -19.40), (10.0, 1.80, -14.00)), 2.14, 7, 3),
        ("Ribbon_R03_Zone0_NW", sample_ramp_pts((-16.0, 1.80, 8.10), (-16.0, 3.60, 14.00)), 1.65, 0, 3),
        ("Ribbon_R04_Zone0_NE", sample_ramp_pts((16.0, 1.80, 8.10), (16.0, 3.60, 14.00)), 1.65, 2, 0),
        ("Ribbon_R05_W_Coast", sample_ramp_pts((-35.5, 0.20, -24.50), (-35.5, 1.80, -19.00)), 2.0, 7, 3),
        ("Ribbon_R06_W_Corridor", sample_ramp_pts((-38.50, 1.80, -14.0), (-44.50, 3.60, -14.0)), 2.1, 0, 3),
        ("Ribbon_R07_W_Lighthouse", sample_ramp_pts((-44.50, 3.60, -24.0), (-51.00, 5.40, -24.0)), 2.2, 0, 3),
        ("Ribbon_R08_W_PostNorth", sample_ramp_pts((-35.5, 1.80, 5.50), (-35.5, 3.60, 12.00)), 1.9, 0, 0),
        ("Ribbon_R09_W_OuterNorth", sample_ramp_pts((-53.5, 1.80, 5.50), (-53.5, 3.60, 12.00)), 1.8, 2, 0),
        ("Ribbon_R10_E_TideMarket", sample_ramp_pts((36.0, 0.20, -17.00), (36.0, 1.80, -11.00)), 2.0, 7, 3),
        ("Ribbon_R11a_E_QuayL0", sample_ramp_pts((43.00, 0.20, -21.5), (46.00, 1.00, -21.5)), 2.0, 7, 3),
        ("Ribbon_R11b_E_QuayL1", sample_ramp_pts((49.0, 1.00, -14.00), (49.0, 1.80, -11.00)), 2.0, 7, 3),
        ("Ribbon_R12_E_Terrace", sample_ramp_pts((40.0, 1.80, 5.50), (40.0, 3.60, 11.50)), 2.0, 2, 0),
        ("Ribbon_R13_N_SummitW", sample_ramp_pts((-17.00, 3.60, 54.5), (-10.00, 5.40, 54.5)), 2.1, 0, 3),
        ("Ribbon_R14_N_SummitE", sample_ramp_pts((17.00, 3.60, 54.5), (10.00, 5.40, 54.5)), 2.1, 0, 3),
        ("Ribbon_R15_N_Knoll", sample_ramp_pts((-27.20, 3.60, 44.0), (-31.50, 4.20, 44.0)), 1.8, 2, 0),
        ("Ribbon_R16a_TidepoolN", sample_ramp_pts((36.0, 0.20, -21.60), (36.0, -0.15, -24.60)), 1.8, 8, 0),
        ("Ribbon_R16b_TidepoolE", sample_ramp_pts((41.80, 0.20, -26.0), (38.80, -0.15, -26.0)), 1.8, 8, 0),
        ("Ribbon_R17a_SouthN", sample_ramp_pts((-5.0, 0.20, -35.80), (-5.0, 1.40, -40.50)), 2.0, 2, 0),
        ("Ribbon_R17b_SouthW", sample_ramp_pts((-16.50, 0.20, -44.5), (-11.50, 1.40, -44.5)), 2.0, 2, 0),
        ("Ribbon_R17c_SouthE", sample_ramp_pts((11.50, 0.20, -44.5), (6.50, 1.40, -44.5)), 2.0, 2, 0),
        ("Ribbon_F32a_CreekBridgeW", sample_arch_pts((-12.0, 31.8), (-12.0, 37.2), 3.60, 0.38, 10), 2.3, 7, 3),
        ("Ribbon_F32b_CreekBridgeE", sample_arch_pts((18.0, 32.1), (18.0, 37.5), 3.60, 0.38, 10), 2.3, 7, 3),
        ("Ribbon_F37_SeaArchBridge", sample_arch_pts((-36.0, -33.5), (-20.0, -36.5), 0.20, 0.95, 18), 2.5, 7, 3),
        ("Ribbon_F38_TidalStepping", sample_arch_pts((30.5, -33.5), (13.5, -38.5), 0.20, 0.04, 14), 2.3, 8, 5),
    ]

    # Fast slides F35W and F35E (stay >= +3.62m above L2 on trestles, then descend L2->L1 across Z=12.0/11.5 at <=17 deg)
    slide_w_pts = [
        (-15.5, 5.40, 52.0), (-21.0, 5.05, 47.0), (-26.0, 4.65, 41.5),
        (-26.5, 4.35, 35.0), (-30.0, 4.00, 25.0), (-32.5, 3.65, 12.0), (-34.5, 1.80, 5.5),
    ]
    slide_e_pts = [
        (15.5, 5.40, 52.0), (18.5, 5.05, 46.0), (20.5, 4.72, 41.0),
        (27.0, 4.40, 35.5), (32.5, 3.98, 23.0), (36.0, 3.65, 11.5), (37.0, 1.80, 5.5),
    ]
    sloped_ribbons.append(("Ribbon_F35W_Slide", slide_w_pts, 1.85, 7, 3))
    sloped_ribbons.append(("Ribbon_F35E_Slide", slide_e_pts, 1.85, 7, 3))

    ribbon_objs = []
    for rname, rpts, rw, rsurf, rbord in sloped_ribbons:
        ribbon_objs.append(build_sloped_ribbon(rname, rpts, rw, rsurf, rbord, materials))

    # Export town-hardscape-4x.glb
    HARDSCAPE_OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=str(HARDSCAPE_OUT),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )
    print(f"Exported hardscape GLB: {HARDSCAPE_OUT} ({HARDSCAPE_OUT.stat().st_size} bytes)")
    return ribbon_objs, slide_w_pts, slide_e_pts


def audit_routes(ribbon_objs, slide_w_pts, slide_e_pts):
    """Load map-shiguang-town-4x.glb and raycast all >= 12 primary/secondary/shortcut routes."""
    # Keep bridge/slide ribbon objects + import walkable terrain mesh for true combined BVH audit
    pre_objs = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(TERRAIN_GLB))
    imported_objs = [o for o in bpy.data.objects if o not in pre_objs and o.type == "MESH"]

    # Build separate BVHs: ground+bridges for walking routes, and slides for slide shortcuts
    bm_walk = bmesh.new()
    bm_slide = bmesh.new()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in list(imported_objs) + list(ribbon_objs):
        if obj.name.startswith(("Crescent_Bay_Sea", "Firefly_Creek_Water", "Tidepool_Water", "Offshore_Reef")):
            continue
        eval_obj = obj.evaluated_get(depsgraph)
        me = eval_obj.to_mesh()
        me.transform(obj.matrix_world)
        if "Slide" in obj.name:
            bm_slide.from_mesh(me)
        else:
            bm_walk.from_mesh(me)
        eval_obj.to_mesh_clear()

    bvh_walk = BVHTree.FromBMesh(bm_walk)
    bvh_slide = BVHTree.FromBMesh(bm_slide)
    bm_walk.free()
    bm_slide.free()

    def ray_y(ux: float, uz: float, expect_y: float, is_slide: bool = False) -> float | None:
        tree = bvh_slide if is_slide else bvh_walk
        origin = Vector((-ux, -uz, expect_y + 1.8))
        loc, _, _, _ = tree.ray_cast(origin, Vector((0.0, 0.0, -1.0)), 25.0)
        if loc is not None:
            return loc.z
        origin2 = Vector((-ux, -uz, 30.0))
        loc2, _, _, _ = tree.ray_cast(origin2, Vector((0.0, 0.0, -1.0)), 60.0)
        return loc2.z if loc2 is not None else None

    def make_arch_wp(p0, p1, y_base, rise, n=12):
        return [(p0[0] + (p1[0] - p0[0]) * (i / n), y_base + rise * (1 - (2 * (i / n) - 1) ** 2), p0[1] + (p1[1] - p0[1]) * (i / n))
                for i in range(n + 1)]

    routes = {
        "01-main-route-v1": [
            (-6.0, 0.20, -22.0), (-6.0, 0.20, -19.40), (-6.0, 1.80, -14.00), (-6.0, 1.80, -10.50),
            (-16.0, 1.80, -10.50), (-16.0, 1.80, 8.10), (-16.0, 3.60, 14.00), (-12.0, 3.60, 16.50),
        ],
        "02-inner-town-loop": [
            (-6.0, 0.20, -20.2), (-6.0, 0.20, -19.4), (-6.0, 1.80, -14.0), (-5.5, 1.80, -4.9),
            (-4.8, 1.80, 2.45), (6.6, 1.80, 2.7), (10.1, 1.80, 1.15), (10.0, 1.80, -14.0),
            (10.0, 0.20, -19.40), (-6.0, 0.20, -20.2),
        ],
        "03-outer-coastal-loop-385m": [
            (-51.0, 5.40, -24.0), (-44.5, 3.60, -24.0), (-43.5, 3.60, -24.0), (-43.5, 3.60, -21.2),
            (-46.5, 3.60, -21.2), (-46.5, 3.60, -19.0), (-49.5, 3.60, -14.0), (-44.5, 3.60, -14.0),
            (-38.5, 1.80, -14.0), (-35.5, 1.80, -19.0), (-35.5, 0.20, -24.5), (-36.0, 0.20, -33.5),
            *make_arch_wp((-36.0, -33.5), (-20.0, -36.5), 0.20, 0.95, 16),
            (-16.5, 0.20, -44.5), (-11.5, 1.40, -44.5), (6.5, 1.40, -44.5), (11.5, 0.20, -44.5),
            (13.5, 0.20, -38.5), *make_arch_wp((13.5, -38.5), (30.5, -33.5), 0.20, 0.04, 12),
            (49.5, 0.20, -30.5), (43.0, 0.20, -25.0), (43.0, 0.20, -21.5), (46.0, 1.00, -21.5),
            (49.0, 1.00, -14.0), (49.0, 1.80, -11.0), (44.0, 1.80, -4.0), (40.0, 1.80, 5.5),
            (40.0, 3.60, 11.5), (40.0, 3.60, 14.5), (24.0, 3.60, 31.0), (18.0, 3.60, 32.1),
            *make_arch_wp((18.0, 32.1), (18.0, 37.5), 3.60, 0.38, 10),
            (21.0, 3.60, 46.5), (17.0, 3.60, 54.5), (10.0, 5.40, 54.5), (0.0, 5.40, 52.0),
            (-10.0, 5.40, 54.5), (-17.0, 3.60, 54.5), (-19.0, 3.60, 49.0), (-12.0, 3.60, 37.2),
            *make_arch_wp((-12.0, 37.2), (-12.0, 31.8), 3.60, 0.38, 10),
            (-28.0, 3.60, 31.0), (-35.5, 3.60, 16.5), (-48.0, 3.60, 16.5), (-53.5, 3.60, 12.0),
            (-53.5, 1.80, 5.5), (-44.0, 1.80, 0.0), (-35.5, 1.80, -3.5), (-38.0, 1.80, -14.0),
            (-38.5, 1.80, -14.0),
        ],
        "04-west-cape-loop": [
            (-34.0, 1.80, -3.5), (-35.5, 1.80, 5.5), (-35.5, 3.60, 12.0), (-48.0, 3.60, 16.5),
            (-53.5, 3.60, 12.0), (-53.5, 1.80, 5.5), (-44.0, 1.80, 0.0), (-38.0, 1.80, -11.5),
            (-35.5, 1.80, -19.0), (-35.5, 0.20, -24.5), (-42.0, 0.20, -30.0),
        ],
        "05-east-bay-loop": [
            (40.0, 1.80, -1.0), (49.0, 1.80, -11.0), (49.0, 1.00, -14.0), (49.0, 1.00, -21.5),
            (46.0, 1.00, -21.5), (43.0, 0.20, -21.5), (43.0, 0.20, -25.0), (48.0, 0.20, -29.0),
            (43.0, 0.20, -26.0), (41.8, 0.20, -26.0), (38.8, -0.15, -26.0), (36.0, -0.15, -24.6),
            (36.0, 0.20, -21.6), (36.0, 0.20, -17.0), (36.0, 1.80, -11.0), (40.0, 1.80, -1.0),
        ],
        "06-north-valley-loop": [
            (-12.0, 3.60, 31.8), *make_arch_wp((-12.0, 31.8), (-12.0, 37.2), 3.60, 0.38, 10),
            (-19.0, 3.60, 49.0), (-17.0, 3.60, 54.5), (-10.0, 5.40, 54.5), (10.0, 5.40, 54.5),
            (17.0, 3.60, 54.5), (21.0, 3.60, 46.5), (18.0, 3.60, 37.5),
            *make_arch_wp((18.0, 37.5), (18.0, 32.1), 3.60, 0.38, 10),
            (-12.0, 3.60, 31.8),
        ],
        "07-south-islet-loop": [
            (-20.0, 0.20, -36.5), (-5.0, 0.20, -35.8), (-5.0, 1.40, -40.5), (6.5, 1.40, -44.5),
            (11.5, 0.20, -44.5), (13.5, 0.20, -38.5), (16.5, 0.20, -44.5), (10.0, 0.20, -47.0),
            (9.5, 0.20, -51.0), (2.0, 0.20, -51.0), (-8.0, 0.20, -51.0), (-15.5, 0.20, -48.5),
            (-16.5, 0.20, -44.5), (-20.0, 0.20, -36.5),
        ],
        "08-east-west-promenade": [
            (-50.5, 1.80, 0.0), (-44.0, 1.80, 0.0), (-34.0, 1.80, -2.5), (-19.0, 1.80, -1.0),
            (-17.2, 1.80, 2.7), (6.6, 1.80, 2.7), (20.4, 1.80, 2.35), (21.1, 1.80, -4.0),
            (40.0, 1.80, -1.0), (53.5, 1.80, 4.0),
        ],
        "09-west-lighthouse-ascent": [
            (-35.5, 1.80, -19.0), (-38.0, 1.80, -14.0), (-38.5, 1.80, -14.0), (-44.5, 3.60, -14.0),
            (-49.5, 3.60, -14.0), (-46.5, 3.60, -19.0), (-46.5, 3.60, -21.2), (-43.5, 3.60, -21.2),
            (-43.5, 3.60, -24.0), (-44.5, 3.60, -24.0), (-51.0, 5.40, -24.0), (-53.5, 5.40, -24.0),
        ],
        "10-east-camellia-ascent": [
            (21.1, 1.80, -4.0), (40.0, 1.80, -1.0), (40.0, 1.80, 5.5), (40.0, 3.60, 11.5),
            (40.0, 3.60, 14.5), (48.0, 3.60, 14.0), (41.5, 3.60, 20.5),
        ],
        "11-tidepool-dip-route": [
            (33.0, 0.20, -17.3), (36.0, 0.20, -21.6), (36.0, -0.15, -24.6), (36.0, -0.15, -26.0),
            (38.8, -0.15, -26.0), (41.8, 0.20, -26.0), (46.5, 0.20, -26.5),
        ],
        "12-knoll-secret-route": [
            (-16.0, 3.60, 37.8), (-23.0, 3.60, 38.5), (-23.5, 3.60, 44.0),
            (-27.2, 3.60, 44.0), (-31.50, 4.20, 44.0), (-34.5, 4.20, 45.2),
        ],
        "13-west-slide-shortcut": slide_w_pts,
        "14-east-slide-shortcut": slide_e_pts,
        "15-creek-bridges-twin": [
            (-12.0, 3.60, 17.6), (-12.0, 3.60, 31.8),
            *make_arch_wp((-12.0, 31.8), (-12.0, 37.2), 3.60, 0.38, 10),
            (-19.0, 3.60, 49.0), (21.0, 3.60, 46.5), (18.0, 3.60, 37.5),
            *make_arch_wp((18.0, 37.5), (18.0, 32.1), 3.60, 0.38, 10),
            (16.0, 3.60, 16.62),
        ],
    }

    report_routes = []
    total_samples = 0
    global_max_slope = 0.0
    total_issues = 0
    sample_step = 0.40

    for rname, wps in routes.items():
        is_slide = "slide" in rname
        dense_pts = []
        route_len = 0.0
        for i in range(len(wps) - 1):
            p0, p1 = Vector(wps[i]), Vector(wps[i + 1])
            seg_len = (Vector((p1.x - p0.x, p1.z - p0.z))).length
            route_len += seg_len
            n_sub = max(1, int(math.ceil(seg_len / sample_step)))
            for k in range(n_sub):
                t = k / n_sub
                dense_pts.append((p0.x + (p1.x - p0.x) * t, p0.y + (p1.y - p0.y) * t, p0.z + (p1.z - p0.z) * t))
        dense_pts.append(wps[-1])

        hit_ys = []
        issues = []
        max_slope = 0.0
        max_step = 0.0
        min_y = 1e9
        max_y = -1e9

        for idx, (ux, ey, uz) in enumerate(dense_pts):
            hy = ray_y(ux, uz, ey, is_slide=is_slide)
            if hy is None:
                issues.append({"sampleIdx": idx, "pos": [round(ux, 2), round(uz, 2)], "type": "missing_ground_hit"})
                hit_ys.append(ey)
                continue
            if is_slide:
                # Verify slide stays above terrain below
                ground_below = ray_y(ux, uz, ey, is_slide=False)
                if ground_below is not None and hy < ground_below - 0.02:
                    issues.append({
                        "sampleIdx": idx,
                        "pos": [round(ux, 2), round(uz, 2)],
                        "type": "slide_clipped_below_ground",
                        "slideY": round(hy, 3),
                        "groundY": round(ground_below, 3),
                    })
            diff = abs(hy - ey)
            if diff > 0.24:
                issues.append({
                    "sampleIdx": idx,
                    "pos": [round(ux, 2), round(uz, 2)],
                    "type": "elevation_mismatch",
                    "rayY": round(hy, 3),
                    "expectedY": round(ey, 3),
                })
            hit_ys.append(hy)
            min_y = min(min_y, hy)
            max_y = max(max_y, hy)
            if idx > 0:
                px, _, pz = dense_pts[idx - 1]
                py = hit_ys[idx - 1]
                ds = math.hypot(ux - px, uz - pz)
                dy = abs(hy - py)
                max_step = max(max_step, dy)
                if ds > 1e-4:
                    slope = math.degrees(math.atan2(dy, ds))
                    max_slope = max(max_slope, slope)
                    if slope > 18.5:
                        issues.append({
                            "sampleIdx": idx,
                            "pos": [round(ux, 2), round(uz, 2)],
                            "type": "slope_exceeds_limit",
                            "slopeDeg": round(slope, 2),
                        })
                    if dy > 0.26:
                        issues.append({
                            "sampleIdx": idx,
                            "pos": [round(ux, 2), round(uz, 2)],
                            "type": "step_height_exceeds_limit",
                            "stepM": round(dy, 3),
                        })

        total_samples += len(dense_pts)
        global_max_slope = max(global_max_slope, max_slope)
        total_issues += len(issues)
        report_routes.append({
            "id": rname,
            "lengthM": round(route_len, 2),
            "sampleCount": len(dense_pts),
            "minY": round(min_y, 3),
            "maxY": round(max_y, 3),
            "maxStepM": round(max_step, 3),
            "maxSlopeDeg": round(max_slope, 2),
            "issueCount": len(issues),
            "issues": issues,
        })

    audit = {
        "schemaVersion": 1,
        "terrainGlb": str(TERRAIN_GLB.relative_to(ROOT)).replace("\\", "/"),
        "hardscapeGlb": str(HARDSCAPE_OUT.relative_to(ROOT)).replace("\\", "/"),
        "sampleSpacingM": sample_step,
        "maxAllowedSlopeDeg": 18.5,
        "routeCount": len(report_routes),
        "totalSamples": total_samples,
        "maxSlopeDeg": round(global_max_slope, 2),
        "issueCount": total_issues,
        "passed": (total_issues == 0 and global_max_slope <= 18.5),
        "routes": report_routes,
    }
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ROUTE_AUDIT: routes={audit['routeCount']}, samples={total_samples}, maxSlopeDeg={audit['maxSlopeDeg']}, issueCount={total_issues}, passed={audit['passed']}")
    if not audit["passed"]:
        raise RuntimeError(f"Route audit failed with {total_issues} issues and maxSlopeDeg={audit['maxSlopeDeg']}")


if __name__ == "__main__":
    ribbons, sw, se = build_hardscape()
    audit_routes(ribbons, sw, se)
