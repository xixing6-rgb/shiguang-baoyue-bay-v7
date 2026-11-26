r"""Build smooth Wind-Waker-style 4x Shiguang crescent bay terrain + 1400m pseudo-infinite sea horizon.

Replaces harsh 1.8m vertical cliff blocks and narrow disconnected ramps with:
1. A single continuous organic heightfield mesh (all slopes <= 12.5 deg, zero steps/gaps).
2. A crisp 2048x2048 painterly Wind Waker terrain albedo texture (grass swirls, warm sand,
   gentle winding footpaths, soft ochre slope bands).
3. Seamless West Wooden Arch Bridge & East Tidal Stone Causeway connecting to South Islet.
4. A 1400m x 1400m pseudo-infinite Wind Waker ocean with crisp coastal foam & 14 distant islands.
5. An invisible shoreline safety collar mesh ('Invisible_Sea_Boundary') hidden at runtime by Lua.

Usage:
  python workspace/scripts/build_windwaker_terrain.py --prep
  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b --factory-startup -P workspace/scripts/build_windwaker_terrain.py -- --blender
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

IN_BLENDER = "--blender" in sys.argv
if IN_BLENDER:
    import bpy
    import bmesh
    from mathutils import Vector
else:
    from PIL import Image

ROOT = Path(r"C:\Users\Administrator\Desktop\抖音")
MODELS_DIR = ROOT / "workspace" / "assets" / "models"
DATA_DIR = ROOT / "workspace" / "data"
DEBUG_DIR = ROOT / "workspace" / "debug"

TERRAIN_GLB = MODELS_DIR / "map-windwaker-bay.glb"
SEA_GLB = MODELS_DIR / "env-windwaker-sea-horizon.glb"
TERRAIN_TEX_PATH = MODELS_DIR / "windwaker_terrain_albedo.png"
LAGOON_TEX_PATH = MODELS_DIR / "windwaker_lagoon_albedo.png"
OCEAN_TEX_PATH = MODELS_DIR / "windwaker_ocean_albedo.png"
HEIGHTS_JSON = DATA_DIR / "windwaker_terrain_heights.json"
OVERVIEW_PNG = DEBUG_DIR / "windwaker-bay-overview.png"
PREVIEW_25D_PNG = DEBUG_DIR / "windwaker-bay-25d-preview.png"

for d in (MODELS_DIR, DATA_DIR, DEBUG_DIR):
    d.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# 1. Coastline & SDF Geometry (Unity XZ coordinates in meters)
# ==============================================================================

MAIN_ISLAND_RAW = [
    (-65.0, -43.5), (-50.5, -44.5), (-40.0, -39.5), (-36.0, -33.5),
    (-32.0, -28.0), (-25.0, -27.4), (-18.0, -27.6), (-10.0, -27.9), (0.0, -28.0),
    (10.0, -27.8), (18.0, -27.6), (25.0, -27.4), (32.0, -28.0),
    (30.5, -33.5), (41.0, -39.5), (54.5, -42.5), (65.0, -41.5),
    (68.0, -32.0), (68.0, -4.0), (68.0, 29.0), (63.5, 41.0),
    (57.5, 53.5), (53.5, 63.5), (44.0, 67.8), (24.0, 68.0),
    (0.0, 68.0), (-24.0, 68.0), (-44.0, 67.8), (-53.5, 63.5),
    (-57.5, 53.5), (-63.5, 41.0), (-68.0, 29.0), (-68.0, -4.0), (-68.0, -32.0),
]

SOUTH_ISLET_RAW = [
    (-30.0, -41.0), (-20.0, -36.5), (-11.0, -35.2), (-5.0, -35.8), (4.0, -35.8),
    (13.5, -38.5), (25.5, -42.0), (29.5, -48.5), (23.0, -53.5), (8.0, -54.0),
    (-14.0, -54.0), (-29.5, -53.0), (-36.5, -47.0),
]


def chaikin_smooth_closed(poly: list[tuple[float, float]], iterations: int = 2) -> np.ndarray:
    pts = np.asarray(poly, dtype=np.float64)
    for _ in range(iterations):
        nxt = np.roll(pts, -1, axis=0)
        q = 0.75 * pts + 0.25 * nxt
        r = 0.25 * pts + 0.75 * nxt
        pts = np.empty((len(pts) * 2, 2), dtype=np.float64)
        pts[0::2] = q
        pts[1::2] = r
    return pts


MAIN_POLY = chaikin_smooth_closed(MAIN_ISLAND_RAW, iterations=2)
SOUTH_POLY = chaikin_smooth_closed(SOUTH_ISLET_RAW, iterations=2)

# Path polylines (Unity X, Z) connecting all regions smoothly
ROAD_PATHS = [
    # Core Zone 0 courtyard & plaza loop + dock link
    [(-6.0, -22.0), (-6.0, -14.0), (-2.0, -7.0), (4.7, 2.6), (13.5, 1.5), (19.0, 4.5), (12.0, 12.0), (-2.0, 14.0), (-11.0, 6.0), (-7.5, 1.5), (-2.0, -7.0)],
    # Farm border path loop around (4.5, 9.0)
    [(4.7, 2.6), (4.5, 5.2), (-1.2, 5.2), (-1.2, 12.8), (10.2, 12.8), (10.2, 5.2), (4.5, 5.2)],
    # Dock to West Cape -> Lighthouse gate -> West Bridge -> South Islet -> East Causeway -> East Bay
    [(-6.0, -21.0), (-18.0, -19.5), (-31.0, -21.0), (-38.0, -27.0), (-45.0, -26.0), (-48.5, -24.5)],
    [(-38.0, -27.0), (-36.0, -33.5), (-28.0, -35.0), (-20.0, -36.5), (-11.0, -41.5), (-2.0, -45.0), (8.0, -43.5), (13.5, -38.5), (22.0, -36.0), (30.5, -33.5), (42.0, -27.0), (52.0, -30.0)],
    # West & East inland loops to North highlands
    [(-11.0, 6.0), (-25.0, 4.0), (-44.0, 3.0), (-48.0, -12.0), (-45.0, -26.0)],
    [(-44.0, 3.0), (-48.0, 20.0), (-36.0, 42.0), (-16.0, 42.0), (0.0, 56.0), (26.0, 42.0), (46.0, 20.0), (44.0, -4.0), (34.0, -15.0), (42.0, -27.0)],
    [(13.5, 1.5), (26.0, 1.0), (44.0, -4.0)],
    [(-2.0, 14.0), (-12.0, 22.0), (-16.0, 42.0)],
    [(12.0, 12.0), (16.0, 22.0), (26.0, 42.0)],
]

CREEK_PATH = [
    (-34.0, 36.5), (-25.0, 35.5), (-18.0, 35.0), (-12.0, 34.5),
    (-4.0, 35.4), (4.0, 35.6), (12.0, 35.0), (18.0, 34.8),
    (24.0, 35.4), (30.5, 41.0), (35.5, 44.5),
]

EAST_CAUSEWAY_A = (30.5, -33.5)
EAST_CAUSEWAY_B = (13.5, -38.5)
WEST_BRIDGE_A = (-36.0, -33.5)
WEST_BRIDGE_B = (-20.0, -36.5)


def poly_sdf_vec(x: np.ndarray, z: np.ndarray, poly: np.ndarray) -> np.ndarray:
    """Vectorized 2D signed distance to closed polygon (negative inside, positive outside)."""
    px = poly[:, 0]
    pz = poly[:, 1]
    qx = np.roll(px, -1)
    qz = np.roll(pz, -1)
    ex = qx - px
    ez = qz - pz
    ee = np.maximum(ex * ex + ez * ez, 1e-12)

    # Reshape for broadcasting: (H, W, 1) vs (N,)
    xf = x[..., None]
    zf = z[..., None]

    wx = xf - px
    wz = zf - pz
    t = np.clip((wx * ex + wz * ez) / ee, 0.0, 1.0)
    bx = wx - ex * t
    bz = wz - ez * t
    dist2 = np.min(bx * bx + bz * bz, axis=-1)
    d = np.sqrt(dist2)

    # Winding / ray-cast inside test
    cond1 = (pz > zf) != (qz > zf)
    x_int = (qx - px) * (zf - pz) / np.where(np.abs(qz - pz) > 1e-12, (qz - pz), 1e-12) + px
    inside = np.sum(cond1 & (xf < x_int), axis=-1) % 2 == 1
    return np.where(inside, -d, d)


def seg_dist_vec(x: np.ndarray, z: np.ndarray, a: tuple[float, float], b: tuple[float, float]) -> np.ndarray:
    ax, az = a
    bx, bz = b
    ex, ez = bx - ax, bz - az
    ee = max(ex * ex + ez * ez, 1e-12)
    t = np.clip(((x - ax) * ex + (z - az) * ez) / ee, 0.0, 1.0)
    dx = x - (ax + ex * t)
    dz = z - (az + ez * t)
    return np.sqrt(dx * dx + dz * dz)


def polyline_dist_vec(x: np.ndarray, z: np.ndarray, pts: list[tuple[float, float]]) -> np.ndarray:
    best = np.full_like(x, 1e9, dtype=np.float64)
    for i in range(len(pts) - 1):
        d = seg_dist_vec(x, z, pts[i], pts[i + 1])
        best = np.minimum(best, d)
    return best


def sd_rounded_box_vec(x: np.ndarray, z: np.ndarray, cx: float, cz: float, hx: float, hz: float, r: float) -> np.ndarray:
    qx = np.abs(x - cx) - (hx - r)
    qz = np.abs(z - cz) - (hz - r)
    out = np.sqrt(np.maximum(qx, 0.0) ** 2 + np.maximum(qz, 0.0) ** 2)
    inside = np.minimum(np.maximum(qx, qz), 0.0)
    return out + inside - r


def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smin(a: np.ndarray, b: np.ndarray, k: float = 4.0) -> np.ndarray:
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def compute_terrain_fields(x: np.ndarray, z: np.ndarray):
    """Evaluate continuous SDFs and organic Wind-Waker heightfield (Unity meters)."""
    d_main = poly_sdf_vec(x, z, MAIN_POLY)
    d_south = poly_sdf_vec(x, z, SOUTH_POLY)
    d_causeway = seg_dist_vec(x, z, EAST_CAUSEWAY_A, EAST_CAUSEWAY_B) - 2.1
    d_wbridge = seg_dist_vec(x, z, WEST_BRIDGE_A, WEST_BRIDGE_B) - 1.9

    d_land = np.minimum(d_main, d_south)

    # Organic gentle rolling elevation tiers (ZERO vertical cliffs, all slopes <= 11.5 deg)
    # L1 mask (+1.15m): Zone 0 plaza/cottage/farm (keeps Z=-8..+12 flat) + West Post Office + East Market
    d_l1_core = sd_rounded_box_vec(x, z, 0.0, 1.5, 31.0, 17.0, 6.5)
    d_l1_west = sd_rounded_box_vec(x, z, -48.0, -3.5, 16.0, 17.5, 7.0)
    d_l1_east = sd_rounded_box_vec(x, z, 44.0, 0.0, 18.0, 12.0, 5.0)
    d_l1 = smin(smin(d_l1_core, d_l1_west, 6.0), d_l1_east, 6.0)

    # L2 mask (+2.15m): North Valley & Highlands + East Terrace + West NW/Ridge
    d_l2_north = sd_rounded_box_vec(x, z, 0.0, 44.0, 53.0, 19.5, 8.0)
    d_l2_east = sd_rounded_box_vec(x, z, 46.0, 21.0, 15.0, 10.5, 5.0)
    d_l2_nw = sd_rounded_box_vec(x, z, -47.0, 20.0, 15.0, 10.0, 5.0)
    d_l2_wcor = sd_rounded_box_vec(x, z, -53.5, -14.5, 9.0, 9.0, 5.0)
    d_l2 = smin(smin(d_l2_north, d_l2_east, 6.0), smin(d_l2_nw, d_l2_wcor, 6.0), 6.0)

    # L3 hill masks: West Lighthouse hill (+2.75m, wide 5.2m flat summit apron) & North Camphor summit (+3.10m)
    r_w_hill = np.sqrt((x + 56.0) ** 2 + (z + 25.0) ** 2) - 5.2
    r_n_hill = np.sqrt(((x - 0.0) / 1.20) ** 2 + ((z - 55.0) / 0.90) ** 2) - 4.5

    # Ensure L1 and L2 stay safely away from shore (so coastline stays gentle L0 sandy beach!)
    shore_guard_l1 = smoothstep(-0.5, -13.5, d_main)
    shore_guard_l2 = smoothstep(-5.5, -16.5, d_main)
    shore_guard_l3_w = smoothstep(-0.5, -10.5, d_main)
    shore_guard_l3_n = smoothstep(-1.5, -10.5, d_main)

    w_l1 = smoothstep(6.5, -6.5, d_l1) * shore_guard_l1
    w_l2 = smoothstep(7.0, -7.0, d_l2) * shore_guard_l2

    # Base island elevation from L0 (+0.25) -> L1 (+1.15) -> L2 (+2.15)
    h_main = 0.25 + 0.90 * w_l1 + 1.00 * w_l2

    # Blend L3 hills smoothly on top of local terrain
    w_w_hill = smoothstep(23.5, 0.0, r_w_hill) * shore_guard_l3_w
    w_n_hill = smoothstep(14.5, 0.0, r_n_hill) * shore_guard_l3_n
    h_main = h_main * (1.0 - w_w_hill) + 2.75 * w_w_hill
    h_main = h_main * (1.0 - w_n_hill) + 3.10 * w_n_hill
    w_l3 = np.maximum(w_w_hill, w_n_hill)

    # Creek ribbon removed per v6 spec: keep continuous walkable meadow without creek depression
    d_creek = np.full_like(x, 1e9, dtype=np.float64)

    # South Islet smooth organic dome (+0.25 shore -> +0.95 amphitheater crest)
    r_south = np.sqrt(((x + 2.0) / 1.45) ** 2 + ((z + 45.0) / 0.85) ** 2) - 4.5
    h_south = 0.25 + 0.70 * smoothstep(9.0, 0.0, r_south) * smoothstep(-0.5, -5.5, d_south)

    # Select main vs south islet land height cleanly
    h_land_only = np.where(d_main <= d_south, h_main, h_south)

    # Smooth sandy foreshore tapering gently into shallow turquoise lagoon (-0.52m offshore)
    shore_slope = smoothstep(-2.2, 4.4, d_land)
    h_island_and_shoal = h_land_only * (1.0 - shore_slope) + (-0.52) * shore_slope

    # East Tidal Causeway: wide, smooth basalt stepping shoal at +0.28m connecting East Cape & South Islet
    w_causeway = smoothstep(1.2, -0.8, d_causeway)
    h_final = np.maximum(h_island_and_shoal, -0.52 + (0.28 - (-0.52)) * w_causeway)

    # Path SDF across all roads
    d_road = np.full_like(x, 1e9, dtype=np.float64)
    for rpts in ROAD_PATHS:
        d_road = np.minimum(d_road, polyline_dist_vec(x, z, rpts))

    return {
        "h": h_final,
        "d_main": d_main,
        "d_south": d_south,
        "d_land": d_land,
        "d_causeway": d_causeway,
        "d_wbridge": d_wbridge,
        "d_road": d_road,
        "d_creek": d_creek,
        "w_l1": w_l1,
        "w_l2": w_l2,
        "w_l3": w_l3,
    }


def sample_height(ux: float, uz: float) -> float:
    x = np.array([[ux]], dtype=np.float64)
    z = np.array([[uz]], dtype=np.float64)
    return float(compute_terrain_fields(x, z)["h"][0, 0])


# ==============================================================================
# 2. Route Slope & Continuity Audit (Hard Gate <= 12.5 deg)
# ==============================================================================

def verify_routes_and_save_heights() -> dict:
    routes = [
        ("Dock_to_Courtyard_Spawn", [(-6.0, -22.0), (-6.0, -14.0), (0.0, -6.0), (4.74, 2.64)]),
        ("Courtyard_to_Farm", [(4.74, 2.64), (4.5, 9.0)]),
        ("Courtyard_to_Fountain", [(4.74, 2.64), (13.5, 1.5)]),
        ("Courtyard_to_Cottage", [(4.74, 2.64), (-7.5, 4.0)]),
        ("Courtyard_to_North_Uplands", [(4.74, 2.64), (-2.0, 14.0), (-12.0, 26.0), (-16.0, 42.0)]),
        ("North_Uplands_to_Summit_L3", [(-16.0, 42.0), (-6.0, 50.0), (0.0, 56.0)]),
        ("North_Creek_Crossing", [(-12.0, 28.0), (-12.0, 35.0), (-12.0, 42.0)]),
        ("West_Cape_to_Lighthouse_L3", [(-30.0, -22.0), (-42.0, -25.0), (-54.0, -24.0)]),
        ("West_Post_to_South_Beach", [(-44.0, 3.0), (-44.0, -14.0), (-36.0, -33.5)]),
        ("East_Causeway_to_South_Islet", [(30.5, -33.5), (22.0, -36.0), (13.5, -38.5), (4.0, -42.0), (-2.0, -45.0)]),
        ("East_Bay_to_Terrace", [(44.0, -24.0), (44.0, -4.0), (46.0, 18.0)]),
        ("West_Plaza_to_East_Plaza", [(-44.0, 3.0), (-10.0, 3.0), (20.0, 2.0), (44.0, -2.0)]),
    ]
    max_slope_all = 0.0
    max_step_all = 0.0
    audit = []
    for name, pts in routes:
        max_sl = 0.0
        max_dh = 0.0
        samples = 0
        for i in range(len(pts) - 1):
            ax, az = pts[i]
            bx, bz = pts[i + 1]
            dist = math.hypot(bx - ax, bz - az)
            n = max(int(dist / 0.5), 10)
            xs = np.linspace(ax, bx, n)
            zs = np.linspace(az, bz, n)
            hs = compute_terrain_fields(xs, zs)["h"]
            ds = dist / (n - 1)
            for k in range(n - 1):
                dh = abs(float(hs[k + 1] - hs[k]))
                sl = math.degrees(math.atan2(dh, ds))
                max_sl = max(max_sl, sl)
                max_dh = max(max_dh, dh)
                samples += 1
        max_slope_all = max(max_slope_all, max_sl)
        max_step_all = max(max_step_all, max_dh)
        audit.append({"route": name, "samples": samples, "maxSlopeDeg": round(max_sl, 2), "maxStepM": round(max_dh, 3)})
        print(f"  [ROUTE] {name:30s} maxSlope={max_sl:5.2f} deg, maxStep={max_dh:.3f} m")
    assert max_slope_all <= 12.5, f"Max route slope too steep: {max_slope_all:.2f} deg"

    # Landmark placement table
    anchors = {
        "spawn_courtyard": (4.74, 2.64),
        "F04_main_cottage": (-7.5, 5.5),
        "FarmGarden_8plots": (4.5, 9.0),
        "F09_wish_fountain": (13.5, 1.5),
        "F22_west_lighthouse": (-54.0, -24.0),
        "P05_bakery_cart": (-1.5, 0.2),
        "NPC_Amu": (-2.5, 3.6),
        "NPC_Mianmian": (9.8, 5.8),
        "F01_dock": (-6.0, -22.0),
        "F34_north_summit": (0.0, 56.0),
        "F39_south_islet": (-2.0, -45.0),
    }
    heights_out = {
        "meta": {
            "maxRouteSlopeDeg": round(max_slope_all, 2),
            "maxStepM": round(max_step_all, 3),
            "recommendedWorldImportPos": [115.0, 79.35, 86.0],
        },
        "routeAudit": audit,
        "anchors": {
            k: {"x": vx, "y": round(sample_height(vx, vz), 4), "z": vz}
            for k, (vx, vz) in anchors.items()
        },
    }
    HEIGHTS_JSON.write_text(json.dumps(heights_out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[AUDIT PASS] 12 routes verified: maxSlope={max_slope_all:.2f} deg (<=12.5), maxStep={max_step_all:.3f} m")
    return heights_out


# ==============================================================================
# 3. Wind-Waker Procedural Painterly Textures (Numpy + PIL)
# ==============================================================================

def value_noise_2d(h: int, w: int, grid_size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    g = rng.random((grid_size + 1, grid_size + 1), dtype=np.float64)
    img = Image.fromarray((g * 255.0).astype(np.uint8), mode="L").resize((w, h), Image.Resampling.BICUBIC)
    return np.asarray(img, dtype=np.float64) / 255.0


def hex_rgb(hex_str: str) -> np.ndarray:
    s = hex_str.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def generate_textures(bounds_x: tuple[float, float], bounds_z: tuple[float, float]):
    """Generate Wind Waker terrain, lagoon foam, and endless ocean textures."""
    x0, x1 = bounds_x
    z0, z1 = bounds_z
    res = 2048

    xs = np.linspace(x0, x1, res)
    zs = np.linspace(z1, z0, res)  # top row (v=1) corresponds to +Z north
    xx, zz = np.meshgrid(xs, zs)

    fields = compute_terrain_fields(xx, zz)
    hh = fields["h"]
    d_land = fields["d_land"]
    d_causeway = fields["d_causeway"]
    d_road = fields["d_road"]
    d_creek = fields["d_creek"]
    w_l2 = fields["w_l2"]
    w_l3 = fields["w_l3"]

    # Finite-difference normal & slope
    dx = (x1 - x0) / res
    dz = (z1 - z0) / res
    dhdx = np.gradient(hh, dx, axis=1)
    dhdz = np.gradient(hh, -dz, axis=0)
    slope = np.sqrt(dhdx ** 2 + dhdz ** 2)

    # Low-noise Wind Waker grass swirls
    n_swirl = value_noise_2d(res, res, 24, 101) * 0.65 + value_noise_2d(res, res, 56, 202) * 0.35
    n_detail = value_noise_2d(res, res, 140, 303)

    # Color palette (Wind Waker Outset Island crisp sunlit tones)
    c_grass_main = hex_rgb("#88D86A")
    c_grass_sun = hex_rgb("#A6EB82")
    c_grass_hi = hex_rgb("#73C462")
    c_grass_rich = hex_rgb("#65B658")

    c_sand_warm = hex_rgb("#F7E4B4")
    c_sand_wet = hex_rgb("#E1C386")
    c_earth_slope = hex_rgb("#C9B084")
    c_earth_band = hex_rgb("#B99D71")
    c_road = hex_rgb("#EFE0B7")
    c_road_edge = hex_rgb("#C8DC84")
    c_causeway = hex_rgb("#8B959C")
    c_creek_bed = hex_rgb("#7AB59E")

    # Base grass with soft Wind Waker cel-painted bands
    swirl_band = smoothstep(0.38, 0.68, n_swirl)
    grass = c_grass_main[None, None, :] * (1.0 - swirl_band[..., None]) + c_grass_sun[None, None, :] * swirl_band[..., None]
    upland_w = np.clip(0.55 * w_l2 + 0.85 * w_l3, 0.0, 1.0)
    grass_hi = c_grass_hi[None, None, :] * (1.0 - 0.5 * swirl_band[..., None]) + c_grass_rich[None, None, :] * (0.5 * swirl_band[..., None])
    grass = grass * (1.0 - upland_w[..., None]) + grass_hi * upland_w[..., None]

    # Subtle hillside warm sandy-earth tint only on steeper slopes (never harsh grey!)
    slope_mask = smoothstep(0.11, 0.22, slope) * smoothstep(0.35, 0.75, hh)
    strata = 0.5 + 0.5 * np.sin(hh * 11.0 + n_swirl * 3.0)
    earth = c_earth_slope[None, None, :] * (1.0 - 0.45 * strata[..., None]) + c_earth_band[None, None, :] * (0.45 * strata[..., None])
    col = grass * (1.0 - 0.62 * slope_mask[..., None]) + earth * (0.62 * slope_mask[..., None])

    # Winding cream-sandstone paths with soft grassy feather
    road_outer = smoothstep(1.95, 1.20, d_road)
    road_inner = smoothstep(1.30, 0.65, d_road)
    col = col * (1.0 - road_outer[..., None]) + c_road_edge[None, None, :] * road_outer[..., None]
    speck = 0.96 + 0.06 * n_detail
    col = col * (1.0 - road_inner[..., None]) + (c_road[None, None, :] * speck[..., None]) * road_inner[..., None]

    # Beach sand blend (shore & low elevation)
    sand_mask = np.maximum(smoothstep(-3.8, -0.5, d_land), smoothstep(0.62, 0.34, hh))
    wet_mask = smoothstep(-0.3, 2.2, d_land)
    sand = c_sand_warm[None, None, :] * (1.0 - wet_mask[..., None]) + c_sand_wet[None, None, :] * wet_mask[..., None]
    col = col * (1.0 - sand_mask[..., None]) + sand * sand_mask[..., None]

    # East Tidal Stone Causeway tint
    cw_mask = smoothstep(0.5, -0.5, d_causeway)
    col = col * (1.0 - cw_mask[..., None]) + (c_causeway[None, None, :] * (0.94 + 0.12 * n_detail[..., None])) * cw_mask[..., None]

    # Gentle directional sun shading baked very subtly (+-6%) for soft Wind Waker relief
    nx, ny, nz = -dhdx, np.ones_like(hh), -dhdz
    nlen = np.sqrt(nx * nx + ny * ny + nz * nz)
    sun = np.array([-0.42, 0.80, -0.42], dtype=np.float64)
    sun /= np.linalg.norm(sun)
    ndotl = (nx * sun[0] + ny * sun[1] + nz * sun[2]) / nlen
    shade = 0.93 + 0.11 * np.clip(ndotl, 0.0, 1.0)
    col = np.clip(col * shade[..., None], 0.0, 1.0)

    Image.fromarray((col * 255.0).astype(np.uint8), mode="RGB").save(TERRAIN_TEX_PATH)
    print(f"[TEX] Saved terrain albedo {TERRAIN_TEX_PATH} ({res}x{res})")

    # 2. Lagoon & Coastal Foam Texture ([-110, +110] -> 2048x2048)
    lx0, lx1 = -110.0, 110.0
    lxs = np.linspace(lx0, lx1, res)
    lzs = np.linspace(lx1, lx0, res)
    lxx, lzz = np.meshgrid(lxs, lzs)
    lf = compute_terrain_fields(lxx, lzz)
    ld_shore = np.minimum(lf["d_land"], lf["d_causeway"])

    ln_wave = value_noise_2d(res, res, 48, 404)
    c_foam = hex_rgb("#F2FEFD")
    c_shallow = hex_rgb("#68E0E4")
    c_mid_teal = hex_rgb("#3BB8DF")
    c_ww_blue = hex_rgb("#2C9AD8")

    # Scalloped foam right around shore (d in [-0.4, +1.5m])
    wobble = (ln_wave - 0.5) * 0.85
    d_wob = ld_shore + wobble
    foam_band = smoothstep(-0.5, 0.1, d_wob) * (1.0 - smoothstep(0.65, 1.45, d_wob))
    foam_outer_ring = smoothstep(2.2, 2.7, d_wob) * (1.0 - smoothstep(2.9, 3.5, d_wob)) * 0.55
    shallow_w = smoothstep(1.2, 11.0, ld_shore)
    mid_w = smoothstep(9.0, 28.0, ld_shore)

    water = c_shallow[None, None, :] * (1.0 - shallow_w[..., None]) + c_mid_teal[None, None, :] * shallow_w[..., None]
    water = water * (1.0 - mid_w[..., None]) + c_ww_blue[None, None, :] * mid_w[..., None]

    # Subtle Wind Waker sea curl highlights
    curl = smoothstep(0.76, 0.84, value_noise_2d(res, res, 72, 505)) * 0.22 * smoothstep(4.0, 14.0, ld_shore) * (1.0 - smoothstep(45.0, 75.0, ld_shore))
    foam_total = np.clip(foam_band + foam_outer_ring + curl, 0.0, 1.0)
    water = water * (1.0 - foam_total[..., None]) + c_foam[None, None, :] * foam_total[..., None]

    Image.fromarray((np.clip(water, 0.0, 1.0) * 255.0).astype(np.uint8), mode="RGB").save(LAGOON_TEX_PATH)
    print(f"[TEX] Saved lagoon foam albedo {LAGOON_TEX_PATH} ({res}x{res})")

    # 3. Endless Horizon Ocean Texture ([-720, +720] -> 1024x1024)
    ores = 1024
    oxs = np.linspace(-720.0, 720.0, ores)
    ozs = np.linspace(720.0, -720.0, ores)
    oxx, ozz = np.meshgrid(oxs, ozs)
    rr = np.sqrt(oxx ** 2 + ozz ** 2)
    c_deep = hex_rgb("#268EC9")
    c_fog_sky = hex_rgb("#96D8F4")

    w_deep = smoothstep(110.0, 260.0, rr)
    w_horizon = smoothstep(320.0, 690.0, rr)
    on_curl = smoothstep(0.79, 0.86, value_noise_2d(ores, ores, 96, 606)) * 0.16 * (1.0 - w_horizon)
    ocean = c_ww_blue[None, None, :] * (1.0 - w_deep[..., None]) + c_deep[None, None, :] * w_deep[..., None]
    ocean = ocean * (1.0 - on_curl[..., None]) + c_foam[None, None, :] * on_curl[..., None]
    ocean = ocean * (1.0 - w_horizon[..., None]) + c_fog_sky[None, None, :] * w_horizon[..., None]

    Image.fromarray((np.clip(ocean, 0.0, 1.0) * 255.0).astype(np.uint8), mode="RGB").save(OCEAN_TEX_PATH)
    print(f"[TEX] Saved horizon ocean albedo {OCEAN_TEX_PATH} ({ores}x{ores})")


# ==============================================================================
# 4. Blender Mesh Construction & Export
# ==============================================================================

def unity_to_blender_pos(ux: float, uy: float, uz: float) -> Vector:
    return Vector((-ux, -uz, uy))


def make_textured_mat(name: str, tex_path: Path, roughness: float = 0.88, emission_strength: float = 0.12):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.15

    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(tex_path))
    tex.extension = "EXTEND"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if emission_strength > 0:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return m


def make_flat_mat(name: str, hex_col: str, roughness: float = 0.85, alpha: float = 1.0, emission: float = 0.08):
    s = hex_col.lstrip("#")
    rgb = [int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    col = (*lin, 1.0)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    if emission > 0:
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = emission
    if alpha < 1.0:
        m.blend_method = "BLEND"
    return m


def build_continuous_terrain_mesh(bounds_x: tuple[float, float], bounds_z: tuple[float, float], step: float = 1.0):
    x0, x1 = bounds_x
    z0, z1 = bounds_z
    nx = int(round((x1 - x0) / step)) + 1
    nz = int(round((z1 - z0) / step)) + 1

    xs = np.linspace(x0, x1, nx)
    zs = np.linspace(z0, z1, nz)
    xx, zz = np.meshgrid(xs, zs)
    fields = compute_terrain_fields(xx, zz)
    hh = fields["h"]
    d_shore = np.minimum(fields["d_land"], fields["d_causeway"])

    # Keep only triangles within 5.5m of shore/causeway so the mesh edges cleanly underwater
    keep_pt = d_shore <= 5.5

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    vert_grid = {}
    for j in range(nz):
        for i in range(nx):
            # Include vertex if it or any neighbor is kept
            if (keep_pt[j, i] or
                (i > 0 and keep_pt[j, i - 1]) or (i + 1 < nx and keep_pt[j, i + 1]) or
                (j > 0 and keep_pt[j - 1, i]) or (j + 1 < nz and keep_pt[j + 1, i])):
                ux = float(xx[j, i])
                uz = float(zz[j, i])
                uy = float(hh[j, i])
                v = bm.verts.new(unity_to_blender_pos(ux, uy, uz))
                vert_grid[(j, i)] = (v, (ux - x0) / (x1 - x0), (uz - z0) / (z1 - z0))

    for j in range(nz - 1):
        for i in range(nx - 1):
            if not (keep_pt[j, i] or keep_pt[j + 1, i] or keep_pt[j, i + 1] or keep_pt[j + 1, i + 1]):
                continue
            keys = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            if not all(k in vert_grid for k in keys):
                continue
            # Unity (X right, Z forward) -> Blender (-X, -Z, Y): ensure upward normal (+Z_b)
            # With unity_to_blender (-ux, -uz, uy), increasing i gives (-1,0,0) and increasing j gives (0,-1,0)
            # (-1,0,0) x (0,-1,0) = (0,0,+1), so (j,i) -> (j,i+1) -> (j+1,i+1) -> (j+1,i) yields +Z normal in Blender
            ord_keys = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            vs = [vert_grid[k][0] for k in ord_keys]
            try:
                f = bm.faces.new(vs)
                f.smooth = True
                for loop, k in zip(f.loops, ord_keys):
                    loop[uv_layer].uv = (vert_grid[k][1], vert_grid[k][2])
            except ValueError:
                pass

    bm.normal_update()
    flipped_cnt = 0
    for f in bm.faces:
        if f.normal.z < 0.0:
            f.normal_flip()
            flipped_cnt += 1
    bm.normal_update()
    if flipped_cnt:
        print(f"[WARN] Flipped {flipped_cnt} downward terrain faces to +Z")
    assert all(f.normal.z > 0.0 for f in bm.faces), "WindWaker_Bay_Terrain has non-upward face normals!"
    mesh = bpy.data.meshes.new("WindWaker_Bay_Terrain")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("WindWaker_Bay_Terrain", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(make_textured_mat("WW_Terrain_Mat", TERRAIN_TEX_PATH, roughness=0.90, emission_strength=0.14))
    return obj


def build_west_arch_bridge():
    """Smooth wide flush-entry wooden arch bridge between (-36,-33.5) and (-20,-36.5)."""
    ax, az = WEST_BRIDGE_A
    bx, bz = WEST_BRIDGE_B
    dx, dz = bx - ax, bz - az
    length = math.hypot(dx, dz)
    dir_v = Vector((dx / length, dz / length))
    perp_v = Vector((-dir_v.y, dir_v.x))
    half_w = 1.90  # 3.8m walkable width!

    # Extend 1.8m inland at both ends with smooth sine arch from +0.23m up to +1.00m
    n_seg = 24
    bm = bmesh.new()
    left_top, right_top, left_bot, right_bot = [], [], [], []
    for i in range(n_seg + 1):
        u = i / n_seg
        s = -1.8 + (length + 3.6) * u
        cx = ax + dir_v.x * s
        cz = az + dir_v.y * s
        if 0.0 <= s <= length:
            t_span = s / length
            deck_y = 0.23 + 0.78 * (math.sin(math.pi * t_span) ** 1.35)
        else:
            deck_y = 0.22  # tucked smoothly flush under sandy shore (+0.25m)
        for sign, top_list, bot_list in ((-1, left_top, left_bot), (1, right_top, right_bot)):
            ux = cx + perp_v.x * half_w * sign
            uz = cz + perp_v.y * half_w * sign
            top_list.append(bm.verts.new(unity_to_blender_pos(ux, deck_y, uz)))
            bot_list.append(bm.verts.new(unity_to_blender_pos(ux, deck_y - 0.32, uz)))

    for i in range(n_seg):
        for quad in (
            (left_top[i], left_top[i + 1], right_top[i + 1], right_top[i]),
            (right_bot[i], right_bot[i + 1], left_bot[i + 1], left_bot[i]),
            (left_bot[i], left_bot[i + 1], left_top[i + 1], left_top[i]),
            (right_top[i], right_top[i + 1], right_bot[i + 1], right_bot[i]),
        ):
            f = bm.faces.new(quad)
            f.smooth = True
    bm.faces.new((left_bot[0], left_top[0], right_top[0], right_bot[0]))
    bm.faces.new((right_bot[-1], right_top[-1], left_top[-1], left_bot[-1]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    mesh = bpy.data.meshes.new("F37_West_Arch_Bridge")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("F37_West_Arch_Bridge", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(make_flat_mat("WW_Bridge_Wood", "#D59A5E", roughness=0.82))

    # Decorative low side rails strictly outside walkable 3.8m deck (at half_w + 0.14m)
    rail_mat = make_flat_mat("WW_Bridge_Rail", "#A86E3E", roughness=0.84)
    for side in (-1, 1):
        rail_pts = []
        for k in range(5):
            t_span = 0.08 + 0.84 * (k / 4.0)
            s = length * t_span
            cx = ax + dir_v.x * s + perp_v.x * (half_w + 0.14) * side
            cz = az + dir_v.y * s + perp_v.y * (half_w + 0.14) * side
            dy = 0.23 + 0.78 * (math.sin(math.pi * t_span) ** 1.35)
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.09, depth=0.68,
                                                location=unity_to_blender_pos(cx, dy + 0.28, cz))
            post = bpy.context.object
            post.name = f"Bridge_Post_{side}_{k}"
            post.data.materials.append(rail_mat)
            rail_pts.append(unity_to_blender_pos(cx, dy + 0.56, cz))
        for k in range(4):
            a, b = rail_pts[k], rail_pts[k + 1]
            delta = b - a
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(a + b) * 0.5)
            bar = bpy.context.object
            bar.name = f"Bridge_Rail_{side}_{k}"
            bar.dimensions = (0.11, 0.11, delta.length + 0.08)
            bar.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
            bar.data.materials.append(rail_mat)


def build_creek_water_ribbon():
    """Translucent turquoise Wind-Waker stream ribbon in North Firefly Creek."""
    bm = bmesh.new()
    half_w = 1.65
    left_v, right_v = [], []
    for i, (ux, uz) in enumerate(CREEK_PATH):
        p = Vector((ux, uz))
        p_prev = Vector(CREEK_PATH[max(0, i - 1)])
        p_next = Vector(CREEK_PATH[min(len(CREEK_PATH) - 1, i + 1)])
        d = (p_next - p_prev).normalized()
        perp = Vector((-d.y, d.x))
        for sign, lst in ((-1, left_v), (1, right_v)):
            qx = ux + perp.x * half_w * sign
            qz = uz + perp.y * half_w * sign
            lst.append(bm.verts.new(unity_to_blender_pos(qx, 2.08, qz)))
    for i in range(len(CREEK_PATH) - 1):
        f = bm.faces.new((left_v[i], left_v[i + 1], right_v[i + 1], right_v[i]))
        f.smooth = True
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0.0:
            f.normal_flip()
    bm.normal_update()
    assert all(f.normal.z > 0.0 for f in bm.faces), "Firefly_Creek_Water has non-upward face normals!"
    mesh = bpy.data.meshes.new("Firefly_Creek_Water")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Firefly_Creek_Water", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(make_flat_mat("WW_Creek_Water", "#5EDBE4", roughness=0.25, alpha=0.82, emission=0.18))


def build_invisible_sea_boundary():
    """Smooth offshore perimeter collar (hidden at runtime by Lua) so players cannot wade off-map."""
    # Trace outer perimeter where d_shore == 3.2m on a coarse grid via marching-ish radial rays or polygon offset?
    # Cleanest reliable method: sample contour around main_coast & south_islet at +3.0m offset, skipping bridge & causeway corridors!
    def build_contour_wall(poly_pts: np.ndarray, name: str, offset_m: float = 3.0):
        n = len(poly_pts)
        segments = []
        for i in range(n):
            p0 = poly_pts[i]
            p1 = poly_pts[(i + 1) % n]
            t = np.array([p1[0] - p0[0], p1[1] - p0[1]])
            ln = np.linalg.norm(t)
            if ln < 1e-4:
                continue
            t /= ln
            # Outward normal for CCW polygon in XZ: (tz, -tx) -> verify sign via SDF
            nrm = np.array([t[1], -t[0]])
            mid = 0.5 * (p0 + p1)
            test_pt = mid + nrm * 0.5
            # Check if outside (d > 0)
            d_test = float(poly_sdf_vec(np.array([test_pt[0]]), np.array([test_pt[1]]), poly_pts)[0])
            if d_test < 0:
                nrm = -nrm
            out_pt = mid + nrm * offset_m
            # Skip bridge & causeway openings
            dc = float(seg_dist_vec(np.array([out_pt[0]]), np.array([out_pt[1]]), EAST_CAUSEWAY_A, EAST_CAUSEWAY_B)[0])
            dw = float(seg_dist_vec(np.array([out_pt[0]]), np.array([out_pt[1]]), WEST_BRIDGE_A, WEST_BRIDGE_B)[0])
            if dc < 3.4 or dw < 3.2:
                continue
            p0_out = p0 + nrm * offset_m
            p1_out = p1 + nrm * offset_m
            segments.append((p0_out, p1_out, nrm))

        bm = bmesh.new()
        for a, b, nrm in segments:
            va0 = bm.verts.new(unity_to_blender_pos(float(a[0]), -0.6, float(a[1])))
            va1 = bm.verts.new(unity_to_blender_pos(float(a[0]), 2.8, float(a[1])))
            vb1 = bm.verts.new(unity_to_blender_pos(float(b[0]), 2.8, float(b[1])))
            vb0 = bm.verts.new(unity_to_blender_pos(float(b[0]), -0.6, float(b[1])))
            bm.faces.new((va0, vb0, vb1, va1))

            # Separate outer back face with distinct vertices for double-sided collision
            a_b = a + nrm * 0.25
            b_b = b + nrm * 0.25
            va0_b = bm.verts.new(unity_to_blender_pos(float(a_b[0]), -0.6, float(a_b[1])))
            va1_b = bm.verts.new(unity_to_blender_pos(float(a_b[0]), 2.8, float(a_b[1])))
            vb1_b = bm.verts.new(unity_to_blender_pos(float(b_b[0]), 2.8, float(b_b[1])))
            vb0_b = bm.verts.new(unity_to_blender_pos(float(b_b[0]), -0.6, float(b_b[1])))
            bm.faces.new((vb0_b, va0_b, va1_b, vb1_b))
        bm.normal_update()
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(make_flat_mat(f"{name}_Mat", "#68E0E4", alpha=0.05, emission=0.0))

    build_contour_wall(MAIN_POLY, "Invisible_Sea_Boundary_Main", offset_m=2.8)
    build_contour_wall(SOUTH_POLY, "Invisible_Sea_Boundary_South", offset_m=2.8)


def build_sea_and_horizon_islands():
    """Export 1400m x 1400m pseudo-infinite Wind Waker sea + 14 distant silhouette islands."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Inner Lagoon & Coastal Foam Plane ([-110, +110], Y=+0.02)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    lx0, lx1 = -110.0, 110.0
    l_n = 44
    xs = np.linspace(lx0, lx1, l_n + 1)
    zs = np.linspace(lx0, lx1, l_n + 1)
    grid = {}
    for j, uz in enumerate(zs):
        for i, ux in enumerate(xs):
            v = bm.verts.new(unity_to_blender_pos(float(ux), 0.02, float(uz)))
            grid[(j, i)] = (v, (ux - lx0) / (lx1 - lx0), (uz - lx0) / (lx1 - lx0))
    for j in range(l_n):
        for i in range(l_n):
            ord_k = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            f = bm.faces.new([grid[k][0] for k in ord_k])
            for loop, k in zip(f.loops, ord_k):
                loop[uv_layer].uv = (grid[k][1], grid[k][2])
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0.0:
            f.normal_flip()
    bm.normal_update()
    assert all(f.normal.z > 0.0 for f in bm.faces), "WindWaker_Lagoon_Shallows has non-upward face normals!"
    mesh = bpy.data.meshes.new("WindWaker_Lagoon_Shallows")
    bm.to_mesh(mesh)
    bm.free()
    lagoon_obj = bpy.data.objects.new("WindWaker_Lagoon_Shallows", mesh)
    bpy.context.collection.objects.link(lagoon_obj)
    lagoon_obj.data.materials.append(make_textured_mat("WW_Lagoon_Mat", LAGOON_TEX_PATH, roughness=0.35, emission_strength=0.22))

    # 2. Endless Outer Ocean Disk (R = 720m -> 1440m diameter, Y=0.00)
    bm2 = bmesh.new()
    uv2 = bm2.loops.layers.uv.new("UVMap")
    ox0, ox1 = -720.0, 720.0
    o_n = 36
    oxs = np.linspace(ox0, ox1, o_n + 1)
    ozs = np.linspace(ox0, ox1, o_n + 1)
    ogrid = {}
    for j, uz in enumerate(ozs):
        for i, ux in enumerate(oxs):
            v = bm2.verts.new(unity_to_blender_pos(float(ux), 0.00, float(uz)))
            ogrid[(j, i)] = (v, (ux - ox0) / (ox1 - ox0), (uz - ox0) / (ox1 - ox0))
    for j in range(o_n):
        for i in range(o_n):
            ord_k = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            f = bm2.faces.new([ogrid[k][0] for k in ord_k])
            for loop, k in zip(f.loops, ord_k):
                loop[uv2].uv = (ogrid[k][1], ogrid[k][2])
    bm2.normal_update()
    for f in bm2.faces:
        if f.normal.z < 0.0:
            f.normal_flip()
    bm2.normal_update()
    assert all(f.normal.z > 0.0 for f in bm2.faces), "WindWaker_Endless_Ocean has non-upward face normals!"
    omesh = bpy.data.meshes.new("WindWaker_Endless_Ocean")
    bm2.to_mesh(omesh)
    bm2.free()
    ocean_obj = bpy.data.objects.new("WindWaker_Endless_Ocean", omesh)
    bpy.context.collection.objects.link(ocean_obj)
    ocean_obj.data.materials.append(make_textured_mat("WW_Ocean_Mat", OCEAN_TEX_PATH, roughness=0.40, emission_strength=0.24))

    # 3. 14 Distant Wind-Waker Silhouette Islands & Sea Stacks (R = 185m .. 420m)
    mat_isle_green = make_flat_mat("WW_Distant_Isle_Green", "#6CB99E", roughness=0.90, emission=0.14)
    mat_isle_sand = make_flat_mat("WW_Distant_Isle_Sand", "#D8D6A8", roughness=0.92, emission=0.12)
    mat_isle_foam = make_flat_mat("WW_Distant_Isle_Foam", "#DCFAF8", roughness=0.60, emission=0.25)

    distant_specs = [
        # (ux, uz, rx, ry, rz, yaw_deg, twin_peak)
        (-220, 180, 26, 15, 22, 20, True),
        (-95, 255, 34, 22, 26, -15, True),
        (85, 270, 38, 25, 28, 30, True),
        (235, 195, 28, 17, 22, -25, False),
        (295, 45, 24, 14, 20, 12, True),
        (260, -145, 22, 13, 18, 40, False),
        (145, -245, 26, 16, 20, -18, True),
        (-25, -265, 20, 11, 16, 8, False),
        (-185, -220, 24, 14, 19, -32, True),
        (-290, -85, 28, 16, 22, 25, False),
        (-310, 80, 30, 18, 24, -10, True),
        (30, 390, 52, 34, 38, 15, True),
        (-280, 330, 45, 28, 34, -22, True),
        (330, 310, 48, 30, 36, 18, False),
    ]
    for idx, (ux, uz, rx, ry, rz, yaw_d, twin) in enumerate(distant_specs):
        # Soft foam collar
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=1.0, depth=0.16, location=unity_to_blender_pos(ux, 0.08, uz))
        foam = bpy.context.object
        foam.name = f"Horizon_Isle_{idx:02d}_Foam"
        foam.scale = (rx * 1.18, rz * 1.18, 1.0)
        foam.rotation_euler.z = math.radians(-yaw_d)
        foam.data.materials.append(mat_isle_foam)

        # Sandy shoal skirt
        bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=10, radius=1.0, location=unity_to_blender_pos(ux, -0.2, uz))
        shoal = bpy.context.object
        shoal.name = f"Horizon_Isle_{idx:02d}_Sand"
        shoal.scale = (rx * 1.04, rz * 1.04, ry * 0.35)
        shoal.rotation_euler.z = math.radians(-yaw_d)
        for f in shoal.data.polygons:
            f.use_smooth = True
        shoal.data.materials.append(mat_isle_sand)

        # Rounded lush peak
        bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=12, radius=1.0, location=unity_to_blender_pos(ux, 0.2, uz))
        peak = bpy.context.object
        peak.name = f"Horizon_Isle_{idx:02d}_Peak"
        peak.scale = (rx * 0.82, rz * 0.82, ry)
        peak.rotation_euler.z = math.radians(-yaw_d)
        for f in peak.data.polygons:
            f.use_smooth = True
        peak.data.materials.append(mat_isle_green)

        if twin:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=1.0,
                                                 location=unity_to_blender_pos(ux + rx * 0.45, 0.1, uz + rz * 0.22))
            p2 = bpy.context.object
            p2.name = f"Horizon_Isle_{idx:02d}_Peak2"
            p2.scale = (rx * 0.55, rz * 0.55, ry * 0.72)
            for f in p2.data.polygons:
                f.use_smooth = True
            p2.data.materials.append(mat_isle_green)

    # 4. Animated Coastal Wave Foam Bands & Sea Sparkle Layer (preserved in nodeMergeBlacklist)
    def build_foam_ring_mesh(obj_name: str, off_in: float, off_out: float, y_pos: float, mat_name: str, hex_col: str, alpha: float, emission: float):
        bm_f = bmesh.new()
        for poly_pts, other_poly in ((MAIN_POLY, SOUTH_POLY), (SOUTH_POLY, MAIN_POLY)):
            n_pts = len(poly_pts)
            edge_nrms = []
            for i in range(n_pts):
                p0 = poly_pts[i]
                p1 = poly_pts[(i + 1) % n_pts]
                t = np.array([p1[0] - p0[0], p1[1] - p0[1]])
                ln = max(float(np.linalg.norm(t)), 1e-6)
                t /= ln
                nrm = np.array([t[1], -t[0]])
                mid = 0.5 * (p0 + p1)
                test_pt = mid + nrm * 0.5
                if float(poly_sdf_vec(np.array([test_pt[0]]), np.array([test_pt[1]]), poly_pts)[0]) < 0:
                    nrm = -nrm
                edge_nrms.append(nrm)

            verts_in, verts_out = [], []
            for i in range(n_pts):
                vn = edge_nrms[(i - 1) % n_pts] + edge_nrms[i]
                vln = max(float(np.linalg.norm(vn)), 1e-6)
                vn /= vln
                pi = poly_pts[i]
                pin = pi + vn * off_in
                pout = pi + vn * off_out
                verts_in.append(bm_f.verts.new(unity_to_blender_pos(float(pin[0]), y_pos, float(pin[1]))))
                verts_out.append(bm_f.verts.new(unity_to_blender_pos(float(pout[0]), y_pos, float(pout[1]))))

            for i in range(n_pts):
                j = (i + 1) % n_pts
                mid = 0.5 * (poly_pts[i] + poly_pts[j]) + edge_nrms[i] * ((off_in + off_out) * 0.5)
                dc = float(seg_dist_vec(np.array([mid[0]]), np.array([mid[1]]), EAST_CAUSEWAY_A, EAST_CAUSEWAY_B)[0])
                dw = float(seg_dist_vec(np.array([mid[0]]), np.array([mid[1]]), WEST_BRIDGE_A, WEST_BRIDGE_B)[0])
                do = float(poly_sdf_vec(np.array([mid[0]]), np.array([mid[1]]), other_poly)[0])
                if dc < 2.6 or dw < 2.4 or do < 0.8:
                    continue
                f = bm_f.faces.new((verts_in[i], verts_in[j], verts_out[j], verts_out[i]))
                f.smooth = True

        bm_f.normal_update()
        for f in bm_f.faces:
            if f.normal.z < 0.0:
                f.normal_flip()
        bm_f.normal_update()
        assert all(f.normal.z > 0.0 for f in bm_f.faces), f"{obj_name} has non-upward face normals!"
        m_f = bpy.data.meshes.new(obj_name)
        bm_f.to_mesh(m_f)
        bm_f.free()
        o_f = bpy.data.objects.new(obj_name, m_f)
        bpy.context.collection.objects.link(o_f)
        o_f.data.materials.append(make_flat_mat(mat_name, hex_col, roughness=0.30, alpha=alpha, emission=emission))

    build_foam_ring_mesh("WW_WaveFoam_Inner", 0.25, 1.45, 0.042, "WW_Wave_Foam_Inner_Mat", "#F2FFFF", 0.88, 0.26)
    build_foam_ring_mesh("WW_WaveFoam_Outer", 2.30, 3.30, 0.035, "WW_Wave_Foam_Outer_Mat", "#ADEFF8", 0.72, 0.22)

    # Sea Sparkle Layer: 44 Wind-Waker crescent/diamond surface glints in d_shore in [6m, 60m]
    rng_sp = np.random.default_rng(20261126)
    bm_sp = bmesh.new()
    placed_sp = 0
    for attempt in range(400):
        if placed_sp >= 44:
            break
        ang = float(rng_sp.uniform(0.0, 2.0 * math.pi))
        rad = float(rng_sp.uniform(38.0, 118.0))
        sx = rad * math.cos(ang)
        sz = rad * math.sin(ang)
        sf = compute_terrain_fields(np.array([[sx]]), np.array([[sz]]))
        ds = float(np.minimum(sf["d_land"], sf["d_causeway"])[0, 0])
        dw = float(sf["d_wbridge"][0, 0])
        if 6.0 <= ds <= 60.0 and dw > 3.5:
            # Sleek Wind-Waker elongated diamond-wave highlight
            w_len = float(rng_sp.uniform(2.2, 4.4))
            w_wid = float(rng_sp.uniform(0.38, 0.65))
            yaw_sp = ang + math.pi * 0.5 + float(rng_sp.uniform(-0.25, 0.25))
            cs, sn = math.cos(yaw_sp), math.sin(yaw_sp)
            pts_local = [(-w_len, 0.0), (0.0, w_wid), (w_len, 0.0), (0.0, -w_wid * 0.35)]
            vs = []
            for lx, lz in pts_local:
                wx = sx + lx * cs - lz * sn
                wz = sz + lx * sn + lz * cs
                vs.append(bm_sp.verts.new(unity_to_blender_pos(wx, 0.030, wz)))
            f = bm_sp.faces.new(vs)
            f.smooth = True
            placed_sp += 1

    bm_sp.normal_update()
    for f in bm_sp.faces:
        if f.normal.z < 0.0:
            f.normal_flip()
    bm_sp.normal_update()
    assert all(f.normal.z > 0.0 for f in bm_sp.faces), "WW_SeaSparkle_Layer has non-upward face normals!"
    m_sp = bpy.data.meshes.new("WW_SeaSparkle_Layer")
    bm_sp.to_mesh(m_sp)
    bm_sp.free()
    o_sp = bpy.data.objects.new("WW_SeaSparkle_Layer", m_sp)
    bpy.context.collection.objects.link(o_sp)
    o_sp.data.materials.append(make_flat_mat("WW_Sea_Sparkle_Mat", "#E8FFFF", roughness=0.25, alpha=0.78, emission=0.28))
    print(f"[SEA] Added WW_WaveFoam_Inner, WW_WaveFoam_Outer, WW_SeaSparkle_Layer ({placed_sp} glints)")

    bpy.ops.export_scene.gltf(
        filepath=str(SEA_GLB),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_materials="EXPORT",
    )
    print(f"[EXPORT] Sea & Horizon GLB: {SEA_GLB} ({SEA_GLB.stat().st_size / 1024:.1f} KB)")


def render_preview_images(heights_data: dict):
    """Render Cycles/EEVEE overview and 2.5D perspective preview for visual inspection."""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    world = bpy.data.worlds.new("WW_Sky")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.48, 0.80, 0.96, 1.0)
    bg.inputs[1].default_value = 0.95

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
    sun = bpy.context.object
    sun.data.energy = 2.6
    sun.data.color = (1.0, 0.95, 0.85)
    sun.rotation_euler = (math.radians(48), math.radians(15), math.radians(-35))

    # Add temporary sea mesh into preview scene so render shows endless ocean!
    bpy.ops.import_scene.gltf(filepath=str(SEA_GLB))

    # Hide invisible collision collar during preview rendering
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("Invisible_Sea_Boundary"):
            obj.hide_render = True
            obj.hide_viewport = True

    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.clip_end = 1500.0
    cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    def point_cam(eye_u: tuple[float, float, float], target_u: tuple[float, float, float], lens: float):
        cam_data.lens = lens
        eye_b = unity_to_blender_pos(*eye_u)
        tgt_b = unity_to_blender_pos(*target_u)
        cam_obj.location = eye_b
        cam_obj.rotation_euler = (tgt_b - eye_b).to_track_quat("-Z", "Y").to_euler()

    # 1. Bay overview
    point_cam((0.0, 82.0, -108.0), (0.0, 1.5, 6.0), 28.0)
    scene.render.filepath = str(OVERVIEW_PNG)
    bpy.ops.render.render(write_still=True)

    # 2. 2.5D spawn perspective (looking north across plaza/farm towards hills & endless ocean)
    sp = heights_data["anchors"]["spawn_courtyard"]
    point_cam((sp["x"], sp["y"] + 10.2, sp["z"] - 12.8), (sp["x"], sp["y"] + 1.2, sp["z"] + 1.5), 32.0)
    scene.render.filepath = str(PREVIEW_25D_PNG)
    bpy.ops.render.render(write_still=True)
    print(f"[RENDER] Previews saved: {OVERVIEW_PNG}, {PREVIEW_25D_PNG}")


def main():
    bounds_x = (-76.0, 76.0)
    bounds_z = (-60.0, 74.0)

    if not IN_BLENDER:
        verify_routes_and_save_heights()
        generate_textures(bounds_x, bounds_z)
        return

    heights_data = json.loads(HEIGHTS_JSON.read_text(encoding="utf-8"))

    # Build Terrain GLB (creek water ribbon removed per v6 spec)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build_continuous_terrain_mesh(bounds_x, bounds_z, step=1.0)
    build_west_arch_bridge()
    build_invisible_sea_boundary()

    bpy.ops.export_scene.gltf(
        filepath=str(TERRAIN_GLB),
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_materials="EXPORT",
    )
    print(f"[EXPORT] Terrain GLB: {TERRAIN_GLB} ({TERRAIN_GLB.stat().st_size / 1024:.1f} KB)")

    # Build Sea & Horizon GLB
    build_sea_and_horizon_islands()

    # Re-open terrain + sea for preview renders
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(TERRAIN_GLB))
    render_preview_images(heights_data)


if __name__ == "__main__":
    main()
