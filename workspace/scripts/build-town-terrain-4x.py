"""Build the 4x Shiguang Town crescent double-cape + offshore tidal islet terrain.

Exports:
  - workspace/assets/models/map-shiguang-town-4x.glb (Y-up GLB matching SCAD/Unity mapping)
  - workspace/debug/town-4x-site-plan.png (North-up orthographic site plan)
  - workspace/debug/town-4x-overview.png (35-degree warm afternoon oblique overview)

Usage:
  blender -b --factory-startup -P workspace/scripts/build-town-terrain-4x.py
"""

from __future__ import annotations

import math
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Vector, Euler
from mathutils.geometry import delaunay_2d_cdt


ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
GLB_OUT = ROOT / "workspace" / "assets" / "models" / "map-shiguang-town-4x.glb"
SITE_PLAN_OUT = ROOT / "workspace" / "debug" / "town-4x-site-plan.png"
OVERVIEW_OUT = ROOT / "workspace" / "debug" / "town-4x-overview.png"


def srgb_to_linear(hex_str: str) -> tuple[float, float, float, float]:
    h = hex_str.lstrip("#")
    vals = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in vals]
    return (*lin, 1.0)


def make_mat(name: str, hex_color: str, roughness: float = 0.88, alpha: float = 1.0, emission: float = 0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    col = srgb_to_linear(hex_color)
    m.diffuse_color = (col[0], col[1], col[2], alpha)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    if emission > 0:
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = emission
    if alpha < 1.0:
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else "HASHED"
    return m


def unity_to_blender_2d(pt: tuple[float, float]) -> Vector:
    # Unity (X_u, Z_u) -> Blender (-X_u, -Z_u) so export_yup=True aligns with scene.scad
    return Vector((-pt[0], -pt[1]))


def unity_to_blender_3d(x: float, y: float, z: float) -> Vector:
    return Vector((-x, -z, y))


# === Shared Master Coastline & Tier Polygons (Unity X, Z in meters) ===

MAIN_ISLAND_POLY = [
    (-65.0, -43.5), (-50.5, -44.5), (-40.0, -39.5), (-36.0, -33.5),
    (-32.0, -28.0), (-25.0, -27.4), (-18.0, -27.6), (-10.0, -27.9), (0.0, -28.0),
    (10.0, -27.8), (18.0, -27.6), (25.0, -27.4), (32.0, -28.0),
    (30.5, -33.5), (41.0, -39.5), (54.5, -42.5), (65.0, -41.5),
    (68.0, -32.0), (68.0, -4.0), (68.0, 29.0), (63.5, 41.0),
    (57.5, 53.5), (53.5, 63.5), (44.0, 67.8), (24.0, 68.0),
    (0.0, 68.0), (-24.0, 68.0), (-44.0, 67.8), (-53.5, 63.5),
    (-57.5, 53.5), (-63.5, 41.0), (-68.0, 29.0), (-68.0, -4.0), (-68.0, -32.0),
]

SOUTH_ISLET_POLY = [
    (-30.0, -41.0), (-20.0, -36.5), (-11.0, -35.2), (-5.0, -35.8), (4.0, -35.8),
    (13.5, -38.5), (25.5, -42.0), (29.5, -48.5), (23.0, -53.5), (8.0, -54.0),
    (-14.0, -54.0), (-29.5, -53.0), (-36.5, -47.0),
]


def ensure_ccw_2d(pts: list[Vector]) -> list[Vector]:
    n = len(pts)
    area2 = sum(pts[i].x * pts[(i + 1) % n].y - pts[(i + 1) % n].x * pts[i].y for i in range(n))
    return list(reversed(pts)) if area2 < 0 else pts


def ensure_ccw_tuples(poly: list[tuple[float, float]]) -> list[tuple[float, float]]:
    n = len(poly)
    area2 = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    return list(reversed(poly)) if area2 < 0 else poly


def smooth_coastal_poly(poly: list[tuple[float, float]], pin_indices: set[int] | None = None) -> list[tuple[float, float]]:
    """Gentle corner beveling for organic crescent bay curves while keeping pinned shore points exact."""
    n = len(poly)
    out = []
    for i in range(n):
        p_prev = Vector(poly[(i - 1) % n])
        p_curr = Vector(poly[i])
        p_next = Vector(poly[(i + 1) % n])
        if pin_indices and i in pin_indices:
            out.append((p_curr.x, p_curr.y))
        else:
            a = p_curr.lerp(p_prev, 0.22)
            b = p_curr.lerp(p_next, 0.22)
            out.append((a.x, a.y))
            out.append((b.x, b.y))
    return ensure_ccw_tuples(out)


def rect_poly(x0: float, x1: float, z0: float, z1: float) -> list[tuple[float, float]]:
    return ensure_ccw_tuples([(x0, z0), (x1, z0), (x1, z1), (x0, z1)])


def ellipse_poly(cx: float, cz: float, rx: float, rz: float, n: int = 28) -> list[tuple[float, float]]:
    return ensure_ccw_tuples([(cx + rx * math.cos(math.tau * i / n), cz + rz * math.sin(math.tau * i / n)) for i in range(n)])


def offset_poly(poly: list[tuple[float, float]], dist: float) -> list[tuple[float, float]]:
    """Outward miter offset of a CCW 2D polygon in Unity XZ."""
    poly = ensure_ccw_tuples(poly)
    n = len(poly)
    out = []
    for i in range(n):
        p_prev = Vector(poly[(i - 1) % n])
        p_curr = Vector(poly[i])
        p_next = Vector(poly[(i + 1) % n])
        e1 = (p_curr - p_prev).normalized()
        e2 = (p_next - p_curr).normalized()
        n1 = Vector((e1.y, -e1.x))
        n2 = Vector((e2.y, -e2.x))
        bis = n1 + n2
        if bis.length < 1e-5:
            bis = n1
        else:
            bis.normalize()
        denom = max(bis.dot(n1), 0.72)
        pt = p_curr + bis * (dist / denom)
        out.append((pt.x, pt.y))
    return ensure_ccw_tuples(out)


def ribbon_quads(pts: list[tuple[float, float]], half_w: float) -> list[list[tuple[float, float]]]:
    """Generate clean convex CCW quads along a polyline so delaunay_2d_cdt never drops concave strips."""
    left, right = [], []
    n = len(pts)
    for i in range(n):
        p = Vector(pts[i])
        d = (Vector(pts[min(i + 1, n - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        perp = Vector((-d.y, d.x))
        left.append((p.x + perp.x * half_w, p.y + perp.y * half_w))
        right.append((p.x - perp.x * half_w, p.y - perp.y * half_w))
    return [ensure_ccw_tuples([left[i], right[i], right[i + 1], left[i + 1]]) for i in range(n - 1)]


# Firefly Creek centerline (Unity X, Z)
CREEK_PATH = [
    (-34.0, 36.5), (-25.0, 35.5), (-18.0, 35.0), (-12.0, 34.5),
    (-4.0, 35.4), (4.0, 35.6), (12.0, 35.0), (18.0, 34.8),
    (24.0, 35.4), (30.5, 41.0), (35.5, 44.5),
]


def build_cdt_layer(name: str, poly_specs: list[tuple[list[tuple[float, float]], int, int]],
                    elevations: dict[int, float], materials_list: list, base_y: float = -0.60,
                    compute_area_tags: set[int] | None = None) -> tuple[bpy.types.Object, float]:
    """Triangulate multi-region 2D polygons cleanly with zero z-fighting via delaunay_2d_cdt."""
    pts_2d = []
    face_loops = []
    for poly, _, _ in poly_specs:
        start = len(pts_2d)
        loop_pts = ensure_ccw_2d([unity_to_blender_2d(p) for p in poly])
        pts_2d.extend(loop_pts)
        face_loops.append(list(range(start, len(pts_2d))))

    coords, _, tris, _, _, owners = delaunay_2d_cdt(pts_2d, [], face_loops, 1, 1e-4)

    # Map each triangle to highest-priority owning polygon
    tri_owners = []
    tri_pts = []
    area_sum = 0.0
    for tri, matches in zip(tris, owners):
        if not matches:
            continue
        owner_idx = max(matches, key=lambda idx: poly_specs[idx][2])
        tag = poly_specs[owner_idx][1]
        if tag < 0:  # hole / cutout
            continue
        tri_owners.append((owner_idx, tag))
        tri_pts.append(tri)
        if compute_area_tags is None or tag in compute_area_tags:
            p0, p1, p2 = coords[tri[0]], coords[tri[1]], coords[tri[2]]
            area_sum += 0.5 * abs((p1.x - p0.x) * (p2.y - p0.y) - (p1.y - p0.y) * (p2.x - p0.x))

    # Build clean flat/stepped mesh with distinct top & cliff faces (separate top vertices per tag so cliffs are crisp!)
    bm = bmesh.new()
    top_vert_map: dict[tuple[int, int], bmesh.types.BMVert] = {}
    bot_vert_map: dict[int, bmesh.types.BMVert] = {}

    def get_top_v(coord_idx: int, tag: int) -> bmesh.types.BMVert:
        key = (coord_idx, tag)
        v = top_vert_map.get(key)
        if v is None:
            c = coords[coord_idx]
            v = bm.verts.new((c.x, c.y, elevations[tag]))
            top_vert_map[key] = v
        return v

    def get_bot_v(coord_idx: int) -> bmesh.types.BMVert:
        v = bot_vert_map.get(coord_idx)
        if v is None:
            c = coords[coord_idx]
            v = bm.verts.new((c.x, c.y, base_y))
            bot_vert_map[coord_idx] = v
        return v

    # Edge adjacency to stitch vertical cliff faces between different elevations / outer boundary
    edge_tags: dict[tuple[int, int], list[tuple[int, int, int]]] = {}
    for tri, (_, tag) in zip(tri_pts, tri_owners):
        vs = [get_top_v(i, tag) for i in tri]
        f = bm.faces.new(vs)
        f.material_index = tag
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            ek = (min(a, b), max(a, b))
            edge_tags.setdefault(ek, []).append((a, b, tag))

    cliff_mat_idx = len(elevations)
    for ek, occs in edge_tags.items():
        if len(occs) == 1:
            a, b, tag = occs[0]
            va_top = get_top_v(a, tag)
            vb_top = get_top_v(b, tag)
            va_bot = get_bot_v(a)
            vb_bot = get_bot_v(b)
            f = bm.faces.new((vb_top, va_top, va_bot, vb_bot))
            f.material_index = cliff_mat_idx
        elif len(occs) == 2:
            (a1, b1, t1), (a2, b2, t2) = occs
            if abs(elevations[t1] - elevations[t2]) > 0.01:
                if elevations[t1] > elevations[t2]:
                    hi_a, hi_b, hi_t, lo_t = a1, b1, t1, t2
                else:
                    hi_a, hi_b, hi_t, lo_t = a2, b2, t2, t1
                v_hi_a = get_top_v(hi_a, hi_t)
                v_hi_b = get_top_v(hi_b, hi_t)
                v_lo_a = get_top_v(hi_a, lo_t)
                v_lo_b = get_top_v(hi_b, lo_t)
                f = bm.faces.new((v_hi_b, v_hi_a, v_lo_a, v_lo_b))
                f.material_index = cliff_mat_idx

    bm.normal_update()
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for mat in materials_list:
        mesh.materials.append(mat)
    return obj, area_sum


def add_graded_ramp(name: str, axis: str, pos_ortho: float, width: float,
                    s0: float, y0: float, s1: float, y1: float, mat, thickness: float = 0.36):
    """Add a beveled continuous ramp connecting two elevation tiers along Unity X or Z."""
    hw = width * 0.5
    p0 = Vector((s0, pos_ortho)) if axis == "x" else Vector((pos_ortho, s0))
    p1 = Vector((s1, pos_ortho)) if axis == "x" else Vector((pos_ortho, s1))
    d = (p1 - p0).normalized()
    perp = Vector((-d.y, d.x))

    corners_u = [
        (p0 - perp * hw, y0),
        (p0 + perp * hw, y0),
        (p1 + perp * hw, y1),
        (p1 - perp * hw, y1),
    ]
    verts = []
    for cu, yy in corners_u:
        verts.append(unity_to_blender_3d(cu.x, yy - thickness, cu.y))
    for cu, yy in corners_u:
        verts.append(unity_to_blender_3d(cu.x, yy, cu.y))

    faces = [
        (3, 2, 1, 0),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def add_box(name: str, ux: float, uy: float, uz: float, sx: float, sy: float, sz: float, mat, bevel: float = 0.025):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=unity_to_blender_3d(ux, uy, uz))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (sx, sz, sy)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0:
        b = min(bevel, min(sx, sy, sz) * 0.25)
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = b
        mod.segments = 1
        mod.limit_method = "NONE"
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def add_round_rock(name: str, ux: float, uy: float, uz: float, rx: float, ry: float, rz: float, mat, rot_z: float = 0.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=unity_to_blender_3d(ux, uy, uz))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (rx, rz, ry)
    obj.rotation_euler.z = rot_z
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for f in obj.data.polygons:
        f.use_smooth = True
    obj.data.materials.append(mat)
    return obj


def add_ramp_rails(name: str, axis: str, pos_ortho: float, width: float,
                   s0: float, y0: float, s1: float, y1: float, mat):
    hw = width * 0.5 + 0.10
    steps = 3
    for side in (-1, 1):
        pts = []
        for i in range(steps):
            t = 0.12 + 0.76 * (i / (steps - 1))
            s = s0 + (s1 - s0) * t
            y = y0 + (y1 - y0) * t
            ux = s if axis == "x" else pos_ortho + side * hw
            uz = pos_ortho + side * hw if axis == "x" else s
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.07, depth=0.58,
                                                location=unity_to_blender_3d(ux, y + 0.26, uz))
            post = bpy.context.object
            post.name = f"{name}_post"
            post.data.materials.append(mat)
            pts.append(unity_to_blender_3d(ux, y + 0.52, uz))
        # Handrail bar
        a, b = pts[0], pts[-1]
        delta = b - a
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(a + b) * 0.5)
        bar = bpy.context.object
        bar.name = f"{name}_rail"
        bar.dimensions = (0.10, 0.10, delta.length + 0.18)
        bar.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
        bar.data.materials.append(mat)


def build_terrain_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # PAD Palette Materials
    mat_sand = make_mat("Sand_L0", "#F5E6C8", roughness=0.90)
    mat_tidepool_bed = make_mat("Tidepool_Bed_L_05", "#C9B89A", roughness=0.88)
    mat_quay = make_mat("Boatyard_Quay_L05", "#E4BA8B", roughness=0.84)
    mat_lawn_l1 = make_mat("Cream_Green_L1", "#B7DDA8", roughness=0.89)
    mat_lawn_l2 = make_mat("Sage_Green_L2", "#93C794", roughness=0.88)
    mat_creek_bed = make_mat("Creek_Pebble_Bed", "#89A389", roughness=0.90)
    mat_knoll = make_mat("Moss_Knoll_L25", "#8BC08B", roughness=0.88)
    mat_summit = make_mat("Summit_Meadow_L3", "#85BC88", roughness=0.87)
    mat_cliff = make_mat("Coastal_Limestone_Cliff", "#B9AE9A", roughness=0.91)

    mat_wood_ramp = make_mat("Warm_Honey_Wood", "#C68A53", roughness=0.82)
    mat_stone_ramp = make_mat("Warm_Cobble_Ramp", "#C4B9A6", roughness=0.89)
    mat_toasted_trim = make_mat("Toasted_Wood_Trim", "#9D623E", roughness=0.84)
    mat_reef_rock = make_mat("Offshore_Reef_Stone", "#A69E92", roughness=0.90)

    mat_sea_foam = make_mat("Sea_Foam_Shallow", "#B5DFD7", roughness=0.55)
    mat_sea_mint = make_mat("Sea_Mint_Lagoon", "#7CC6E8", roughness=0.45)
    mat_sea_deep = make_mat("Sea_Deep_Teal", "#529DC2", roughness=0.42)
    mat_creek_water = make_mat("Creek_Clear_Water", "#7CD1E8", roughness=0.25, alpha=0.82)

    # === 1. Walkable Tier Polygons (tag 0..7) ===
    # Tags:
    #   0 = L0 Sand (+0.20)
    #   1 = L-0.5 Tidepool Bed (-0.15)
    #   2 = L0.5 Boatyard Quay (+1.00)
    #   3 = S-L1 South Islet Theater (+1.40)
    #   4 = L1 Main Living Tier (+1.80)
    #   5 = L2 Uplands & Valley (+3.60)
    #   6 = Creek Bed (+3.10)
    #   7 = L2.5 Knoll (+4.20)
    #   8 = L3 Dual Summits (+5.40)
    elevations = {
        0: 0.20,
        1: -0.15,
        2: 1.00,
        3: 1.40,
        4: 1.80,
        5: 3.60,
        6: 3.10,
        7: 4.20,
        8: 5.40,
    }
    tier_mats = [
        mat_sand,
        mat_tidepool_bed,
        mat_quay,
        mat_lawn_l1,
        mat_lawn_l1,
        mat_lawn_l2,
        mat_creek_bed,
        mat_knoll,
        mat_summit,
        mat_cliff,
    ]

    main_coast = smooth_coastal_poly(MAIN_ISLAND_POLY, pin_indices={3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13})
    south_islet = smooth_coastal_poly(SOUTH_ISLET_POLY, pin_indices={1, 5})

    poly_specs = [
        # Base L0 land silhouettes
        (main_coast, 0, 10),
        (south_islet, 0, 10),
        # L-0.5 East Tidepool basin
        (ellipse_poly(36.0, -26.0, 5.8, 4.4, 24), 1, 20),
        # L0.5 Boatyard Quay
        (rect_poly(46.0, 62.0, -22.5, -12.5), 2, 25),
        # S-L1 South Islet Theater
        (rect_poly(-11.5, 6.5, -49.5, -40.5), 3, 30),
        # L1 Zone 0 (exact 64x28) + Zone W + Zone E
        (rect_poly(-32.0, 32.0, -14.0, 14.0), 4, 40),
        (rect_poly(-44.5, -32.0, -19.0, 12.0), 4, 40),
        (rect_poly(-64.0, -44.5, -10.0, 12.0), 4, 40),
        (rect_poly(32.0, 64.5, -11.0, 11.5), 4, 40),
        # L2 Zone 0 crest (exact -30..+30, 14..28) + Zone W/E/N extensions
        (rect_poly(-30.0, 30.0, 14.0, 28.0), 5, 50),
        (rect_poly(-54.0, -44.5, -26.0, -10.0), 5, 50),  # Zone W F21 terrace
        (rect_poly(-44.5, -42.5, -26.5, -20.5), 5, 50),  # Ramp 07 east landing apron
        (rect_poly(-63.5, -30.0, 12.0, 32.0), 5, 50),    # Zone W NW cottages
        (rect_poly(30.0, 61.5, 11.5, 32.0), 5, 50),      # Zone E camellia terrace
        (rect_poly(-52.5, 52.5, 28.0, 61.5), 5, 50),     # Zone N valley & highlands
        # Carved Firefly Creek channel (+3.10) cutting cleanly through Zone N L2
        *[(q, 6, 60) for q in ribbon_quads(CREEK_PATH, 1.85)],
        # L2.5 Secret Tree Hollow Knoll (+4.20)
        (ellipse_poly(-36.0, 46.0, 5.6, 5.0, 20), 7, 70),
        # L3 Dual Summits (+5.40)
        (rect_poly(-63.0, -51.0, -31.5, -19.5), 8, 80),  # West Lighthouse cliff
        (rect_poly(-10.0, 10.0, 51.0, 65.0), 8, 80),     # North Camphor Summit
    ]

    terrain_obj, walkable_land_area = build_cdt_layer(
        "Walkable_Terrain_4x",
        poly_specs,
        elevations,
        tier_mats,
        base_y=-0.65,
        compute_area_tags={0, 1, 2, 3, 4, 5, 6, 7, 8},
    )
    # Apply subtle 3cm bevel to soften harsh terrace edges (limit by angle so top flats stay crisp)
    bpy.context.view_layer.objects.active = terrain_obj
    mod = terrain_obj.modifiers.new("Soft_Terrace_Bevel", "BEVEL")
    mod.width = 0.035
    mod.segments = 1
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(35.0)
    mod.use_clamp_overlap = True
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # === 2. Continuous 184m x 168m Three-Band Crescent Sea ===
    outer_sea_rect = rect_poly(-92.0, 92.0, -80.0, 88.0)
    inner_lagoon_poly = ensure_ccw_tuples([
        (-45.0, -42.0), (-36.0, -32.0), (-20.0, -26.5), (20.0, -26.5),
        (35.0, -32.0), (45.0, -42.0), (26.0, -46.0), (-28.0, -46.0),
    ])
    sea_specs = [
        (outer_sea_rect, 2, 10),
        (inner_lagoon_poly, 1, 18),
        (offset_poly(main_coast, 5.4), 1, 20),
        (offset_poly(south_islet, 5.4), 1, 20),
        (offset_poly(main_coast, 1.3), 0, 30),
        (offset_poly(south_islet, 1.3), 0, 30),
        (main_coast, -1, 40),
        (south_islet, -1, 40),
    ]
    sea_elevs = {0: -0.02, 1: -0.04, 2: -0.06}
    sea_obj, _ = build_cdt_layer(
        "Crescent_Bay_Sea_4x",
        sea_specs,
        sea_elevs,
        [mat_sea_foam, mat_sea_mint, mat_sea_deep, mat_sea_deep],
        base_y=-0.45,
    )

    # Creek water ribbon (+3.32) & Tidepool water patch (+0.02)
    creek_specs = [(q, 0, 10) for q in ribbon_quads(CREEK_PATH, 1.25)]
    creek_water_obj, _ = build_cdt_layer("Firefly_Creek_Water", creek_specs, {0: 3.32}, [mat_creek_water, mat_creek_water], base_y=3.10)
    tide_specs = [(ellipse_poly(36.0, -26.0, 4.7, 3.6, 24), 0, 10)]
    tide_water_obj, _ = build_cdt_layer("Tidepool_Water", tide_specs, {0: 0.02}, [mat_creek_water, mat_creek_water], base_y=-0.14)

    # === 3. Gentle Tapered Foreshore Apron (L0 +0.20 -> -0.18 into foam band) ===
    shore_skirt_specs = [
        (offset_poly(main_coast, 1.2), 0, 10),
        (offset_poly(south_islet, 1.2), 0, 10),
        (main_coast, -1, 20),
        (south_islet, -1, 20),
    ]
    build_cdt_layer("Beach_Foreshore_Rim", shore_skirt_specs, {0: 0.04}, [mat_sand, mat_sand], base_y=-0.45)

    # === 4. All 18 Walkable Ramps (all <= 18.0 deg) ===
    ramps = [
        # Zone 0 retained ramps (SE extended to -19.40 and NW to 8.10 so all <= 17.5 deg)
        ("Ramp_01_Zone0_SW", "z", -6.0, 4.4, -19.40, 0.20, -14.00, 1.80, mat_wood_ramp, True),
        ("Ramp_02_Zone0_SE", "z", 10.0, 4.4, -19.40, 0.20, -14.00, 1.80, mat_wood_ramp, True),
        ("Ramp_03_Zone0_NW", "z", -16.0, 4.0, 8.10, 1.80, 14.00, 3.60, mat_stone_ramp, False),
        ("Ramp_04_Zone0_NE", "z", 16.0, 4.2, 8.10, 1.80, 14.00, 3.60, mat_lawn_l2, False),
        # Zone W ramps
        ("Ramp_05_W_Coast_A", "z", -35.5, 3.6, -24.50, 0.20, -19.00, 1.80, mat_wood_ramp, True),
        ("Ramp_06_W_Corridor_B", "x", -14.0, 3.4, -38.50, 1.80, -44.50, 3.60, mat_stone_ramp, True),
        ("Ramp_07_W_Lighthouse_C", "x", -24.0, 3.4, -44.50, 3.60, -51.00, 5.40, mat_stone_ramp, True),
        ("Ramp_08_W_PostNorth_D", "z", -35.5, 3.4, 5.50, 1.80, 12.00, 3.60, mat_stone_ramp, False),
        ("Ramp_09_W_OuterNorth_E", "z", -53.5, 3.0, 5.50, 1.80, 12.00, 3.60, mat_lawn_l2, False),
        # Zone E ramps (Ramp 10 & 11b meet East L1 cleanly at Z=-11.00)
        ("Ramp_10_E_TideToMarket_D", "z", 36.0, 3.6, -17.00, 0.20, -11.00, 1.80, mat_wood_ramp, True),
        ("Ramp_11a_E_Quay_L0", "x", -21.5, 3.2, 43.00, 0.20, 46.00, 1.00, mat_wood_ramp, True),
        ("Ramp_11b_E_Quay_L1", "z", 49.0, 3.2, -14.00, 1.00, -11.00, 1.80, mat_wood_ramp, True),
        ("Ramp_12_E_Terrace_A", "z", 40.0, 3.4, 5.50, 1.80, 11.50, 3.60, mat_lawn_l2, False),
        # Zone N ramps
        ("Ramp_13_N_Summit_W", "x", 54.5, 3.4, -17.00, 3.60, -10.00, 5.40, mat_stone_ramp, True),
        ("Ramp_14_N_Summit_E", "x", 54.5, 3.4, 17.00, 3.60, 10.00, 5.40, mat_stone_ramp, True),
        ("Ramp_15_N_Knoll", "x", 44.0, 2.8, -27.20, 3.60, -31.50, 4.20, mat_knoll, False),
        # Zone E Tidepool gentle gravel slopes (starting cleanly at pool rim -21.6 / +41.8)
        ("Ramp_16a_Tidepool_N", "z", 36.0, 3.4, -21.60, 0.20, -24.60, -0.15, mat_tidepool_bed, False),
        ("Ramp_16b_Tidepool_E", "x", -26.0, 3.4, 41.80, 0.20, 38.80, -0.15, mat_tidepool_bed, False),
        # Zone S Islet amphitheater slopes (Ramp 17a meets S-L1 cleanly at Z=-40.50)
        ("Ramp_17a_South_N", "z", -5.0, 3.0, -35.80, 0.20, -40.50, 1.40, mat_lawn_l1, False),
        ("Ramp_17b_South_W", "x", -44.5, 3.0, -16.50, 0.20, -11.50, 1.40, mat_lawn_l1, False),
        ("Ramp_17c_South_E", "x", -44.5, 3.0, 11.50, 0.20, 6.50, 1.40, mat_lawn_l1, False),
    ]
    for rname, axis, ortho, w, s0, y0, s1, y1, rmat, has_rails in ramps:
        add_graded_ramp(rname, axis, ortho, w, s0, y0, s1, y1, rmat)
        if has_rails:
            add_ramp_rails(rname, axis, ortho, w, s0, y0, s1, y1, mat_toasted_trim)

    # === 5. Retaining Curbs (Zone 0 + Expanded Edges, breaking at ramp openings) ===
    # Zone 0 L1 wood retaining wall along Z=-14
    add_box("Zone0_L1_Retain_W", -20.1, 1.01, -13.7, 23.8, 1.62, 0.45, mat_toasted_trim)
    add_box("Zone0_L1_Retain_M", 2.0, 1.01, -13.7, 11.6, 1.62, 0.45, mat_toasted_trim)
    add_box("Zone0_L1_Retain_E", 22.1, 1.01, -13.7, 19.8, 1.62, 0.45, mat_toasted_trim)
    # Zone 0 L2 stone retaining wall along Z=+14
    add_box("Zone0_L2_Retain_W", -24.0, 2.71, 14.2, 12.0, 1.82, 0.45, mat_stone_ramp)
    add_box("Zone0_L2_Retain_M", 0.0, 2.71, 14.2, 27.8, 1.82, 0.45, mat_stone_ramp)
    add_box("Zone0_L2_Retain_E", 24.0, 2.71, 14.2, 12.0, 1.82, 0.45, mat_stone_ramp)

    # === 6. Offshore Distant Sea Stacks & Reef Clusters (184m x 168m sea ring) ===
    offshore_reefs = [
        (-76, -36, 2.4, 1.5, 2.1, 0.4),
        (-74, -40, 1.6, 1.0, 1.4, 1.1),
        (76, -34, 2.5, 1.6, 2.2, -0.5),
        (73, -39, 1.5, 0.9, 1.3, 0.8),
        (-42, -62, 2.0, 1.2, 1.8, 0.2),
        (36, -61, 2.1, 1.3, 1.7, 1.5),
        (-62, 68, 2.6, 1.7, 2.2, 0.7),
        (60, 68, 2.5, 1.6, 2.0, -0.3),
        (-80, 12, 2.2, 1.4, 1.9, 1.2),
        (80, 10, 2.3, 1.4, 2.0, 0.5),
    ]
    for idx, (rx_u, rz_u, sx, sy, sz, rotz) in enumerate(offshore_reefs):
        add_round_rock(f"Offshore_Reef_{idx:02d}", rx_u, 0.15, rz_u, sx, sy, sz, mat_reef_rock, rotz)

    # Compute & print area verification
    total_with_bridges = walkable_land_area + (16.28 * 2.8 + 17.72 * 2.6)
    print(f"TERRAIN_AREA_M2 land_only={walkable_land_area:.1f}, with_crossings={total_with_bridges:.1f}, ratio={total_with_bridges/3584:.4f}x")

    # Export GLB (without cameras/lights)
    GLB_OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=str(GLB_OUT),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )
    print(f"Exported terrain GLB: {GLB_OUT} ({GLB_OUT.stat().st_size} bytes)")
    return total_with_bridges


def setup_daylight_and_render():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1400
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.12

    # Warm Storybook Sky Background
    world = bpy.data.worlds.new("Storybook_Day")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = srgb_to_linear("#D6EEF7")
    bg.inputs["Strength"].default_value = 0.85

    # Warm Afternoon Sun Light
    sun_data = bpy.data.lights.new("Afternoon_Sun", type="SUN")
    sun_data.energy = 2.6
    sun_data.color = srgb_to_linear("#FFF1D6")[:3]
    sun_data.angle = math.radians(12.0)
    sun_obj = bpy.data.objects.new("Afternoon_Sun", sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = Euler((math.radians(48), math.radians(15), math.radians(32)), "XYZ")

    # Soft lavender-blue bounce fill from opposite side (warm slate tint, never pure black)
    fill_data = bpy.data.lights.new("Sky_Fill", type="SUN")
    fill_data.energy = 0.75
    fill_data.color = srgb_to_linear("#C7D6F5")[:3]
    fill_obj = bpy.data.objects.new("Sky_Fill", fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = Euler((math.radians(-50), math.radians(-20), math.radians(190)), "XYZ")

    # 1. Orthographic Site Plan (North +Z_u = -Y_b UP, East +X_u = -X_b RIGHT)
    SITE_PLAN_OUT.parent.mkdir(parents=True, exist_ok=True)
    cam_top_data = bpy.data.cameras.new("Cam_SitePlan")
    cam_top_data.type = "ORTHO"
    cam_top_data.ortho_scale = 178.0
    cam_top_data.clip_end = 500.0
    cam_top = bpy.data.objects.new("Cam_SitePlan", cam_top_data)
    bpy.context.collection.objects.link(cam_top)
    cam_top.location = Vector((0.0, -4.0, 140.0))
    # Looking straight down -Z_b, rotated 180 deg around Z so -Y_b (North) is UP and -X_b (East) is RIGHT
    cam_top.rotation_euler = Euler((0.0, 0.0, math.pi), "XYZ")
    scene.camera = cam_top
    scene.render.filepath = str(SITE_PLAN_OUT)
    bpy.ops.render.render(write_still=True)

    # Add wide outer horizon ocean plane strictly for perspective overview framing (after GLB export)
    horizon_mat = bpy.data.materials.get("Sea_Deep_Teal") or make_mat("Horizon_Sea_Fade", "#529DC2", roughness=0.42)
    bpy.ops.mesh.primitive_plane_add(size=1200.0, location=(0.0, 0.0, -0.065))
    horizon = bpy.context.object
    horizon.name = "Horizon_Ocean_RenderOnly"
    horizon.data.materials.append(horizon_mat)

    # 2. 35-deg Oblique Overview from South looking North-East/North
    # South is +Y_b, North is -Y_b, West is +X_b, East is -X_b
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    cam_ob_data = bpy.data.cameras.new("Cam_Overview")
    cam_ob_data.type = "PERSP"
    cam_ob_data.lens = 36.0
    cam_ob_data.clip_end = 600.0
    cam_ob = bpy.data.objects.new("Cam_Overview", cam_ob_data)
    bpy.context.collection.objects.link(cam_ob)
    cam_pos = Vector((28.0, 148.0, 108.0))
    target = Vector((0.0, -4.0, 2.0))
    cam_ob.location = cam_pos
    cam_ob.rotation_euler = (target - cam_pos).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_ob
    scene.render.filepath = str(OVERVIEW_OUT)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build_terrain_scene()
    setup_daylight_and_render()
